#!/usr/bin/env python3
"""
RFM Analysis, Cohort Retention, Pareto, and Scatter Analysis
Comprehensive customer analytics for Insurance Dataset
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")
OUTPUT_PATH = Path("/home/huynnz/GetAJob/DataExplorer/EDA/output")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

plt.rcParams["figure.figsize"] = (12, 8)
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12


def load_data():
    don_hang = pd.read_csv(DATA_PATH / "Đơn hàng.csv")
    khach_hang = pd.read_csv(DATA_PATH / "Khách hàng.csv")
    hop_dong = pd.read_csv(DATA_PATH / "Hợp đồng.csv")
    goi_sp = pd.read_csv(DATA_PATH / "Gói Sản Phẩm.csv")

    return don_hang, khach_hang, hop_dong, goi_sp


def preprocess_orders(don_hang):
    df = don_hang.copy()
    df["NGAY_KY_HD"] = pd.to_datetime(df["NGAY_KY_HD"], errors="coerce")
    df["NGAY_HIEU_LUC"] = pd.to_datetime(df["NGAY_HIEU_LUC"], errors="coerce")
    df["NGAY_HET_HAN"] = pd.to_datetime(df["NGAY_HET_HAN"], errors="coerce")

    df["GIA_TIEN"] = pd.to_numeric(df["GIA_TIEN"], errors="coerce").fillna(0)
    df["PHIBH"] = pd.to_numeric(df["PHIBH"], errors="coerce").fillna(0)
    df["GIA_BH"] = pd.to_numeric(df["GIA_BH"], errors="coerce").fillna(0)

    df["COHORT_MONTH"] = df["NGAY_KY_HD"].dt.to_period("M")
    df["YEAR_MONTH"] = df["NGAY_KY_HD"].dt.to_period("M")
    df["MONTH"] = df["NGAY_KY_HD"].dt.month
    df["YEAR"] = df["NGAY_KY_HD"].dt.year

    return df


def calculate_rfm(df, reference_date=None):
    if reference_date is None:
        reference_date = df["NGAY_KY_HD"].max() + timedelta(days=1)

    rfm = (
        df.groupby("MA_KH")
        .agg(
            {
                "NGAY_KY_HD": lambda x: (reference_date - x.max()).days,
                "MA_DON": "count",
                "PHIBH": "sum",
            }
        )
        .reset_index()
    )

    rfm.columns = ["MA_KH", "Recency", "Frequency", "Monetary"]

    rfm["R_Score"] = pd.qcut(
        rfm["Recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop"
    )
    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
        duplicates="drop",
    )
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
        duplicates="drop",
    )

    rfm["R_Score"] = rfm["R_Score"].astype(int)
    rfm["F_Score"] = rfm["F_Score"].astype(int)
    rfm["M_Score"] = rfm["M_Score"].astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )
    rfm["RFM_Total"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    rfm["Segment"] = vectorized_segment_customer(rfm)

    return rfm


def vectorized_segment_customer(rfm):
    """Vectorized RFM segmentation using numpy.select for performance."""
    r = rfm["R_Score"]
    f = rfm["F_Score"]
    m = rfm["M_Score"]

    conditions = [
        (r >= 4) & (f >= 4) & (m >= 4),
        (r >= 4) & (f >= 3) & (m >= 3),
        (r >= 4) & (f <= 2) & (m <= 2),
        (r >= 3) & (f >= 3) & (m >= 3),
        (r >= 3) & (f <= 2) & (m >= 4),
        (r <= 2) & (f >= 4) & (m >= 4),
        (r <= 2) & (f <= 2) & (m <= 2),
        (r <= 2) & (f >= 3) & (m >= 3),
        (r == 3) & (f <= 2) & (m <= 2),
    ]
    choices = [
        "Champions",
        "Loyal Customers",
        "New Customers",
        "Potential Loyalists",
        "Big Spenders (New)",
        "At Risk",
        "Lost",
        "Need Attention",
        "About to Sleep",
    ]
    return np.select(conditions, choices, default="Others")


def generate_vip_list(rfm, khach_hang, top_n=100):
    vip_candidates = rfm[
        (rfm["Segment"].isin(["Champions", "Loyal Customers", "Potential Loyalists"]))
        | (rfm["Monetary"] >= rfm["Monetary"].quantile(0.95))
    ].copy()

    vip_list = vip_candidates.merge(khach_hang, on="MA_KH", how="left")

    if "TUOI" in vip_list.columns:
        age_bins = [0, 25, 35, 45, 55, 100]
        age_labels = ["18-25", "26-35", "36-45", "46-55", "55+"]
        vip_list["Age_Group"] = pd.cut(
            vip_list["TUOI"], bins=age_bins, labels=age_labels
        )

    vip_list = vip_list.sort_values("Monetary", ascending=False)

    vip_list["VIP_Tier"] = np.select(
        [
            vip_list["RFM_Total"] >= 14,
            vip_list["RFM_Total"] >= 11,
            vip_list["RFM_Total"] >= 8,
        ],
        ["Platinum", "Gold", "Silver"],
        default="Bronze",
    )

    return vip_list.head(top_n)


def create_cohort_matrix(df):
    """
    Create cohort retention and renewal matrices.

    Note: Renewals appearing in Month 1 indicate data truncation - customers whose
    first recorded order is a renewal had prior history that was not migrated.
    """
    df_cohort = df[df["NGAY_KY_HD"].notna()].copy()

    # 1. Map the first order date to every row for the customer (vectorized)
    df_cohort["FirstOrderDate"] = df_cohort.groupby("MA_KH")["NGAY_KY_HD"].transform(
        "min"
    )

    # 2. Extract Cohort Month for the index
    df_cohort["CohortMonth"] = df_cohort["FirstOrderDate"].dt.to_period("M")

    # 3. Calculate Index using native datetime attributes (cleaner and faster)
    df_cohort["CohortIndex"] = (
        (df_cohort["NGAY_KY_HD"].dt.year - df_cohort["FirstOrderDate"].dt.year) * 12
        + (df_cohort["NGAY_KY_HD"].dt.month - df_cohort["FirstOrderDate"].dt.month)
        + 1
    )

    # Flag renewal orders
    df_cohort["IsRenewal"] = df_cohort["LOAI_HD"] == "Tái tục"

    # Retention: any customer who made a purchase in that month
    cohort_data = (
        df_cohort.groupby(["CohortMonth", "CohortIndex"])["MA_KH"]
        .nunique()
        .reset_index()
    )
    cohort_data.columns = ["CohortMonth", "CohortIndex", "Customers"]

    cohort_pivot = cohort_data.pivot(
        index="CohortMonth", columns="CohortIndex", values="Customers"
    )

    # Use explicit column selection for cohort size (column 1 = first month)
    if 1 in cohort_pivot.columns:
        cohort_size = cohort_pivot[1]
    else:
        # Fallback: use first available column
        cohort_size = cohort_pivot.iloc[:, 0]

    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100

    # Renewal: only customers who renewed (Tái tục) in that month
    renewal_data = (
        df_cohort[df_cohort["IsRenewal"]]
        .groupby(["CohortMonth", "CohortIndex"])["MA_KH"]
        .nunique()
        .reset_index()
    )
    renewal_data.columns = ["CohortMonth", "CohortIndex", "Renewals"]

    renewal_pivot = renewal_data.pivot(
        index="CohortMonth", columns="CohortIndex", values="Renewals"
    )
    renewal_pivot = renewal_pivot.reindex(
        index=retention_matrix.index, columns=retention_matrix.columns, fill_value=0
    )

    renewal_rate_matrix = renewal_pivot.divide(cohort_size, axis=0) * 100

    return retention_matrix, cohort_pivot, renewal_rate_matrix, renewal_pivot


def create_pareto_chart(df, top_n=20):
    revenue_by_customer = (
        df.groupby("MA_KH")["PHIBH"].sum().sort_values(ascending=False)
    )

    cumulative_pct = revenue_by_customer.cumsum() / revenue_by_customer.sum() * 100

    pareto_data = pd.DataFrame(
        {
            "MA_KH": revenue_by_customer.index[:top_n],
            "Revenue": revenue_by_customer.values[:top_n],
            "Cumulative_Pct": cumulative_pct.values[:top_n],
        }
    )

    return pareto_data, revenue_by_customer


def create_volume_margin_scatter(df, khach_hang):
    df["Margin"] = df["PHIBH"]
    df["Volume"] = df["GIA_TIEN"]

    customer_metrics = (
        df.groupby("MA_KH")
        .agg(
            {
                "Margin": "sum",
                "Volume": "sum",
                "MA_DON": "count",
                "CTY": "last",
            }
        )
        .reset_index()
    )

    customer_metrics.columns = [
        "MA_KH",
        "Total_Margin",
        "Total_Volume",
        "Order_Count",
        "Company",
    ]
    customer_metrics["Avg_Margin"] = (
        customer_metrics["Total_Margin"] / customer_metrics["Order_Count"]
    )
    customer_metrics["Avg_Volume"] = (
        customer_metrics["Total_Volume"] / customer_metrics["Order_Count"]
    )

    scatter_data = customer_metrics.merge(
        khach_hang[["MA_KH", "XHKH", "TUOI", "GIOI_TINH"]], on="MA_KH", how="left"
    )

    return scatter_data


def create_feature_table(rfm, khach_hang, don_hang):
    feature_agg = don_hang.groupby("MA_KH").agg(
        {
            "MA_DON": "count",
            "PHIBH": ["sum", "mean", "std"],
            "GIA_TIEN": ["sum", "mean"],
            "NGAY_KY_HD": ["min", "max"],
            "THOI_HAN_THANG": "mean",
            "CTY": "last",
            "MA_GSP": "nunique",
            "MA_KENHBANCHITIET": "nunique",
            "MA_NV": "nunique",
        }
    )

    feature_agg.columns = ["_".join(col).strip() for col in feature_agg.columns.values]
    feature_agg = feature_agg.reset_index()

    feature_table = rfm.merge(khach_hang, on="MA_KH", how="left").merge(
        feature_agg, on="MA_KH", how="left"
    )

    feature_table["Customer_Tenure_Days"] = (
        feature_table["NGAY_KY_HD_max"] - feature_table["NGAY_KY_HD_min"]
    ).dt.days.fillna(0)

    feature_table["Days_Since_First_Order"] = (
        don_hang["NGAY_KY_HD"].max() - feature_table["NGAY_KY_HD_min"]
    ).dt.days.fillna(0)

    feature_table["Days_Since_Last_Order"] = feature_table["Recency"]

    for col in feature_table.select_dtypes(include=[np.number]).columns:
        if feature_table[col].isna().any():
            feature_table[col] = feature_table[col].fillna(0)

    return feature_table


def print_rfm_summary(rfm):
    print("\n" + "=" * 80)
    print("RFM SEGMENTS SUMMARY")
    print("=" * 80)

    segment_summary = (
        rfm.groupby("Segment")
        .agg(
            {
                "MA_KH": "count",
                "Recency": "mean",
                "Frequency": "mean",
                "Monetary": ["mean", "sum"],
            }
        )
        .round(2)
    )

    segment_summary.columns = [
        "Customer_Count",
        "Avg_Recency",
        "Avg_Frequency",
        "Avg_Monetary",
        "Total_Revenue",
    ]
    segment_summary["Pct_Customers"] = (
        segment_summary["Customer_Count"]
        / segment_summary["Customer_Count"].sum()
        * 100
    ).round(2)
    segment_summary["Pct_Revenue"] = (
        segment_summary["Total_Revenue"] / segment_summary["Total_Revenue"].sum() * 100
    ).round(2)
    segment_summary = segment_summary.sort_values("Total_Revenue", ascending=False)

    print(segment_summary.to_string())
    print(f"\nTotal unique customers: {rfm['MA_KH'].nunique():,}")
    print(f"Total revenue: {rfm['Monetary'].sum():,.0f} VND")

    return segment_summary


def print_vip_summary(vip_list):
    print("\n" + "=" * 80)
    print("VIP CUSTOMERS LIST (Top 20)")
    print("=" * 80)

    display_cols = [
        "MA_KH",
        "RFM_Score",
        "RFM_Total",
        "Segment",
        "VIP_Tier",
        "Monetary",
        "Recency",
        "Frequency",
    ]
    if "TUOI" in vip_list.columns:
        display_cols.append("TUOI")
    if "XHKH" in vip_list.columns:
        display_cols.append("XHKH")

    print(vip_list[display_cols].head(20).to_string(index=False))

    print(f"\nVIP Tier Distribution:")
    print(vip_list["VIP_Tier"].value_counts())


def print_cohort_summary(retention_matrix, renewal_rate_matrix=None):
    print("\n" + "=" * 80)
    print("COHORT RETENTION MATRIX (Based on First NEW Contract)")
    print("=" * 80)

    print(f"\nCohorts available: {len(retention_matrix)}")
    print(f"Max cohort index: {retention_matrix.shape[1]}")

    print("\nRetention rates for first 10 cohorts (first 12 months):")
    print("(Percentage of customers from cohort who made ANY purchase in that month)")
    display_matrix = retention_matrix.iloc[:10, :12]
    print(display_matrix.round(1).fillna("-").to_string())

    if renewal_rate_matrix is not None:
        print("\n" + "=" * 80)
        print("RENEWAL RATE MATRIX (Tái tục)")
        print("=" * 80)
        print("\nRenewal rates for first 10 cohorts (first 12 months):")
        print("(Percentage of customers from cohort who RENEWED in that month)")
        display_renewal = renewal_rate_matrix.iloc[:10, :12]
        print(display_renewal.round(1).fillna("-").to_string())

        print("\n" + "-" * 60)
        print("KEY INSIGHTS:")
        print("-" * 60)
        avg_month2_retention = retention_matrix.iloc[:, 1].mean()
        avg_month2_renewal = renewal_rate_matrix.iloc[:, 1].mean()
        print(f"  - Avg Month-2 Retention: {avg_month2_retention:.1f}%")
        print(f"  - Avg Month-2 Renewal Rate: {avg_month2_renewal:.1f}%")

        if retention_matrix.shape[1] >= 13:
            month_12_renewals = (
                renewal_rate_matrix.iloc[:, 12]
                if renewal_rate_matrix.shape[1] > 12
                else renewal_rate_matrix.iloc[:, -1]
            )
            valid_12 = month_12_renewals.dropna()
            if len(valid_12) > 0:
                print(f"  - Avg Month-12 (1 Year) Renewal Rate: {valid_12.mean():.1f}%")


def print_pareto_summary(pareto_data, all_revenue):
    print("\n" + "=" * 80)
    print("PARETO ANALYSIS (80/20 Rule)")
    print("=" * 80)

    total_customers = len(all_revenue)
    total_revenue = all_revenue.sum()

    customers_80_pct = (all_revenue.cumsum() <= total_revenue * 0.8).sum() + 1

    print(f"\nTotal customers: {total_customers:,}")
    print(f"Total revenue: {total_revenue:,.0f} VND")
    print(
        f"\n80% of revenue comes from {customers_80_pct:,} customers ({customers_80_pct / total_customers * 100:.1f}% of customers)"
    )

    print(f"\nTop 10 Customers by Revenue:")
    print(pareto_data.head(10).to_string(index=False))


def print_scatter_summary(scatter_data):
    print("\n" + "=" * 80)
    print("VOLUME VS MARGIN SCATTER ANALYSIS")
    print("=" * 80)

    print(f"\nTotal customers analyzed: {len(scatter_data):,}")
    print(
        f"\nMarg.| Correlation: Volume vs Total Margin: {scatter_data['Total_Volume'].corr(scatter_data['Total_Margin']):.4f}"
    )

    print(f"\nStatistics by Tier:")
    tier_stats = (
        scatter_data.groupby("XHKH")
        .agg(
            {
                "Total_Volume": "mean",
                "Total_Margin": "mean",
                "Order_Count": "mean",
                "MA_KH": "count",
            }
        )
        .round(0)
    )
    tier_stats.columns = ["Avg_Volume", "Avg_Margin", "Avg_Orders", "Count"]
    print(tier_stats.to_string())


def print_feature_summary(feature_table):
    print("\n" + "=" * 80)
    print("FEATURE TABLE SUMMARY")
    print("=" * 80)

    print(f"\nTotal features: {len(feature_table.columns)}")
    print(f"Total customers: {len(feature_table):,}")

    orders_col = "MA_DON_count" if "MA_DON_count" in feature_table.columns else "count"
    products_col = (
        "MA_GSP_nunique" if "MA_GSP_nunique" in feature_table.columns else "products"
    )

    print(f"\nKey Feature Statistics:")
    print(f"  - Average orders per customer: {feature_table[orders_col].mean():.2f}")
    print(
        f"  - Average customer tenure: {feature_table['Customer_Tenure_Days'].mean():.0f} days"
    )
    print(
        f"  - Average products per customer: {feature_table[products_col].mean():.2f}"
    )

    print(f"\nRFM Distribution:")
    print(
        f"  - Recency: min={feature_table['Recency'].min()}, max={feature_table['Recency'].max()}, mean={feature_table['Recency'].mean():.1f}"
    )
    print(
        f"  - Frequency: min={feature_table['Frequency'].min()}, max={feature_table['Frequency'].max()}, mean={feature_table['Frequency'].mean():.1f}"
    )
    print(
        f"  - Monetary: min={feature_table['Monetary'].min():,.0f}, max={feature_table['Monetary'].max():,.0f}, mean={feature_table['Monetary'].mean():,.0f}"
    )


def save_outputs(
    rfm,
    vip_list,
    retention_matrix,
    cohort_pivot,
    renewal_rate_matrix,
    renewal_pivot,
    pareto_data,
    scatter_data,
    feature_table,
):
    rfm.to_csv(OUTPUT_PATH / "rfm_segments.csv", index=False)
    vip_list.to_csv(OUTPUT_PATH / "vip_customers.csv", index=False)
    retention_matrix.to_csv(OUTPUT_PATH / "cohort_retention_matrix.csv")
    cohort_pivot.to_csv(OUTPUT_PATH / "cohort_pivot.csv")
    renewal_rate_matrix.to_csv(OUTPUT_PATH / "renewal_rate_matrix.csv")
    renewal_pivot.to_csv(OUTPUT_PATH / "renewal_pivot.csv")
    pareto_data.to_csv(OUTPUT_PATH / "pareto_analysis.csv", index=False)
    scatter_data.to_csv(OUTPUT_PATH / "volume_margin_scatter.csv", index=False)
    feature_table.to_csv(OUTPUT_PATH / "feature_table.csv", index=False)

    print(f"\nAll outputs saved to: {OUTPUT_PATH}")


def create_visualizations(
    rfm,
    vip_list,
    retention_matrix,
    renewal_rate_matrix,
    pareto_data,
    scatter_data,
    max_cohorts=15,
    max_months=12,
):
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    ax1 = axes[0, 0]
    segment_counts = rfm["Segment"].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(segment_counts)))
    ax1.barh(segment_counts.index, segment_counts.values, color=colors)
    ax1.set_xlabel("Number of Customers")
    ax1.set_title("RFM Segments Distribution")
    for i, v in enumerate(segment_counts.values):
        ax1.text(v + 50, i, f"{v:,}", va="center", fontsize=9)

    ax2 = axes[0, 1]
    vip_tier_counts = vip_list["VIP_Tier"].value_counts()
    tier_order = ["Platinum", "Gold", "Silver", "Bronze"]
    tier_counts = [vip_tier_counts.get(t, 0) for t in tier_order]
    tier_colors = ["#E5E4E2", "#FFD700", "#C0C0C0", "#CD7F32"]
    bars = ax2.bar(tier_order, tier_counts, color=tier_colors)
    ax2.set_ylabel("Number of VIP Customers")
    ax2.set_title("VIP Customer Tiers")
    for bar in bars:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
        )

    # Dynamic heatmap sizing
    n_cohorts = min(max_cohorts, len(retention_matrix))
    n_months = min(max_months, retention_matrix.shape[1])

    ax3 = axes[0, 2]
    try:
        sns.heatmap(
            retention_matrix.iloc[:n_cohorts, :n_months],
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            ax=ax3,
            cbar_kws={"label": "Retention %"},
        )
        ax3.set_title("Cohort Retention Heatmap (Any Purchase)")
        ax3.set_xlabel("Cohort Index (Months)")
        ax3.set_ylabel("Cohort Month")
    except Exception as e:
        ax3.text(0.5, 0.5, f"Heatmap error: {str(e)}", ha="center", va="center")

    ax4 = axes[1, 0]
    x_pos = np.arange(len(pareto_data))
    ax4.bar(
        x_pos, pareto_data["Revenue"], color="steelblue", alpha=0.7, label="Revenue"
    )
    ax4_twin = ax4.twinx()
    ax4_twin.plot(
        x_pos, pareto_data["Cumulative_Pct"], "r-o", markersize=4, label="Cumulative %"
    )
    ax4_twin.axhline(y=80, color="red", linestyle="--", alpha=0.5)
    ax4.set_xlabel("Customer Rank")
    ax4.set_ylabel("Revenue (VND)", color="steelblue")
    ax4_twin.set_ylabel("Cumulative %", color="red")
    ax4.set_title("Pareto Analysis (Top 20 Customers)")
    ax4.set_xticks(x_pos[::2])
    ax4.legend(loc="upper left")
    ax4_twin.legend(loc="center right")

    ax5 = axes[1, 1]
    scatter_colors = {
        "Đồng": "#CD7F32",
        "Bạc": "#C0C0C0",
        "Vàng": "#FFD700",
        "Bạch kim": "#E5E4E2",
        "Kim cương": "#B9F2FF",
    }
    for tier, color in scatter_colors.items():
        tier_data = scatter_data[scatter_data["XHKH"] == tier]
        if len(tier_data) > 0:
            ax5.scatter(
                tier_data["Total_Volume"] / 1e6,
                tier_data["Total_Margin"] / 1e6,
                c=color,
                label=tier,
                alpha=0.5,
                s=20,
            )
    ax5.set_xlabel("Total Volume (Million VND)")
    ax5.set_ylabel("Total Margin (Million VND)")
    ax5.set_title("Volume vs Margin by Customer Tier")
    ax5.legend(title="Tier", loc="upper right")
    ax5.set_xlim(0, scatter_data["Total_Volume"].quantile(0.95) / 1e6)
    ax5.set_ylim(0, scatter_data["Total_Margin"].quantile(0.95) / 1e6)

    ax6 = axes[1, 2]
    try:
        sns.heatmap(
            renewal_rate_matrix.iloc[:n_cohorts, :n_months],
            annot=True,
            fmt=".1f",
            cmap="YlGn",
            ax=ax6,
            cbar_kws={"label": "Renewal %"},
        )
        ax6.set_title("Renewal Rate Heatmap (Tái tục)")
        ax6.set_xlabel("Cohort Index (Months)")
        ax6.set_ylabel("Cohort Month")
    except Exception as e:
        ax6.text(0.5, 0.5, f"Heatmap error: {str(e)}", ha="center", va="center")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH / "rfm_cohort_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Visualization saved to: {OUTPUT_PATH / 'rfm_cohort_analysis.png'}")


def main():
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - RFM & COHORT ANALYSIS")
    print("=" * 80)

    print("\nLoading data...")
    don_hang, khach_hang, hop_dong, goi_sp = load_data()
    print(f"  - Orders: {len(don_hang):,} records")
    print(f"  - Customers: {len(khach_hang):,} records")
    print(f"  - Contracts: {len(hop_dong):,} records")
    print(f"  - Products: {len(goi_sp)} types")

    print("\nPreprocessing orders...")
    don_hang_processed = preprocess_orders(don_hang)

    print("\nCalculating RFM...")
    rfm = calculate_rfm(don_hang_processed)
    print(f"RFM analysis complete: {len(rfm):,} customers segmented")

    print("\nGenerating VIP list...")
    vip_list = generate_vip_list(rfm, khach_hang)

    print("\nCreating cohort retention matrix...")
    retention_matrix, cohort_pivot, renewal_rate_matrix, renewal_pivot = (
        create_cohort_matrix(don_hang_processed)
    )

    print("\nRunning Pareto analysis...")
    pareto_data, all_revenue = create_pareto_chart(don_hang_processed)

    print("\nCreating volume vs margin scatter data...")
    scatter_data = create_volume_margin_scatter(don_hang_processed, khach_hang)

    print("\nGenerating feature table...")
    feature_table = create_feature_table(rfm, khach_hang, don_hang_processed)

    print_rfm_summary(rfm)
    print_vip_summary(vip_list)
    print_cohort_summary(retention_matrix, renewal_rate_matrix)
    print_pareto_summary(pareto_data, all_revenue)
    print_scatter_summary(scatter_data)
    print_feature_summary(feature_table)

    print("\nSaving outputs...")
    save_outputs(
        rfm,
        vip_list,
        retention_matrix,
        cohort_pivot,
        renewal_rate_matrix,
        renewal_pivot,
        pareto_data,
        scatter_data,
        feature_table,
    )

    print("\nCreating visualizations...")
    create_visualizations(
        rfm, vip_list, retention_matrix, renewal_rate_matrix, pareto_data, scatter_data
    )

    print("\n" + "=" * 80)
    print("RFM & COHORT ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  - {OUTPUT_PATH / 'rfm_segments.csv'}")
    print(f"  - {OUTPUT_PATH / 'vip_customers.csv'}")
    print(f"  - {OUTPUT_PATH / 'cohort_retention_matrix.csv'}")
    print(f"  - {OUTPUT_PATH / 'renewal_rate_matrix.csv'}")
    print(f"  - {OUTPUT_PATH / 'pareto_analysis.csv'}")
    print(f"  - {OUTPUT_PATH / 'volume_margin_scatter.csv'}")
    print(f"  - {OUTPUT_PATH / 'feature_table.csv'}")
    print(f"  - {OUTPUT_PATH / 'rfm_cohort_analysis.png'}")


if __name__ == "__main__":
    main()
