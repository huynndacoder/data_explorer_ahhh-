#!/usr/bin/env python3
"""
Contract & Order Analysis - Insurance Dataset EDA
Detailed analysis of contracts, orders, and revenue patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_transaction_data():
    """Load transaction-related data."""
    hop_dong = pd.read_csv(DATA_PATH / "Hợp đồng.csv")
    don_hang = pd.read_csv(DATA_PATH / "Đơn hàng.csv")
    kpi = pd.read_csv(DATA_PATH / "KPI.csv")
    goi_sp = pd.read_csv(DATA_PATH / "Gói Sản Phẩm.csv")
    kenh_ban = pd.read_csv(DATA_PATH / "Kênh bán chi tiết.csv")

    return hop_dong, don_hang, kpi, goi_sp, kenh_ban


def contract_overview(hop_dong):
    """Basic contract statistics."""
    print("\n" + "=" * 80)
    print("CONTRACT OVERVIEW")
    print("=" * 80)
    print(f"Total contracts: {len(hop_dong):,}")
    print(f"Unique customers: {hop_dong['MA_KH'].nunique():,}")
    print(f"Unique products: {hop_dong['MA_GSP'].nunique()}")

    contracts_per_customer = hop_dong.groupby("MA_KH").size()
    print(f"\nContracts per customer:")
    print(f"  - Min: {contracts_per_customer.min()}")
    print(f"  - Max: {contracts_per_customer.max()}")
    print(f"  - Mean: {contracts_per_customer.mean():.2f}")
    print(f"  - Median: {contracts_per_customer.median()}")

    customer_counts = contracts_per_customer.value_counts().sort_index()
    print(f"\nDistribution of contracts per customer:")
    for num_contracts, count in customer_counts.head(10).items():
        print(
            f"  {num_contracts} contract(s): {count:,} customers ({count / len(contracts_per_customer) * 100:.1f}%)"
        )


def product_analysis(hop_dong, goi_sp):
    """Analyze product distribution in contracts."""
    print("\n" + "=" * 80)
    print("PRODUCT DISTRIBUTION IN CONTRACTS")
    print("=" * 80)

    product_counts = hop_dong["MA_GSP"].value_counts()

    print("\nTop 10 most popular products:")
    for prod_id, count in product_counts.head(10).items():
        product_name = goi_sp[goi_sp["MA_GOISANPHAM"] == prod_id][
            "TENGOISANPHAM"
        ].values
        name = product_name[0] if len(product_name) > 0 else "Unknown"
        pct = count / len(hop_dong) * 100
        print(f"  {prod_id} ({name}): {count:,} contracts ({pct:.2f}%)")

    print(f"\nBottom 5 least popular products:")
    for prod_id, count in product_counts.tail(5).items():
        product_name = goi_sp[goi_sp["MA_GOISANPHAM"] == prod_id][
            "TENGOISANPHAM"
        ].values
        name = product_name[0] if len(product_name) > 0 else "Unknown"
        pct = count / len(hop_dong) * 100
        print(f"  {prod_id} ({name}): {count:,} contracts ({pct:.4f}%)")

    return product_counts


def order_analysis(don_hang):
    """Analyze order patterns."""
    print("\n" + "=" * 80)
    print("ORDER ANALYSIS")
    print("=" * 80)

    print(f"Total orders: {len(don_hang):,}")

    don_hang["NGAY_KY_HD"] = pd.to_datetime(don_hang["NGAY_KY_HD"], errors="coerce")

    print(f"\nDate range of orders:")
    print(f"  - Earliest: {don_hang['NGAY_KY_HD'].min()}")
    print(f"  - Latest: {don_hang['NGAY_KY_HD'].max()}")

    print(f"\nContract types:")
    type_counts = don_hang["LOAI_HD"].value_counts()
    for type_name, count in type_counts.items():
        pct = count / len(don_hang) * 100
        print(f"  {type_name}: {count:,} ({pct:.1f}%)")

    print(f"\nContract duration (months):")
    duration_stats = don_hang["THOI_HAN_THANG"].describe()
    print(duration_stats)


def revenue_analysis(don_hang):
    """Analyze revenue patterns."""
    print("\n" + "=" * 80)
    print("REVENUE ANALYSIS")
    print("=" * 80)

    total_revenue = don_hang["GIA_TIEN"].sum()
    total_insurance_fee = don_hang["GIA_BH"].sum()

    print(f"Total contract value: {total_revenue:,.0f} VND")
    print(f"Total insurance fee: {total_insurance_fee:,.0f} VND")
    print(f"Average contract value: {don_hang['GIA_TIEN'].mean():,.0f} VND")
    print(f"Median contract value: {don_hang['GIA_TIEN'].median():,.0f} VND")
    print(f"Average insurance fee: {don_hang['GIA_BH'].mean():,.0f} VND")

    revenue_by_company = don_hang.groupby("CTY")["GIA_TIEN"].agg(
        ["sum", "mean", "count"]
    )
    print(f"\nRevenue by company:")
    for company, row in revenue_by_company.iterrows():
        print(f"  {company}:")
        print(f"    - Total: {row['sum']:,.0f} VND")
        print(f"    - Average: {row['mean']:,.0f} VND")
        print(f"    - Contracts: {row['count']:,}")

    return revenue_by_company


def sales_channel_analysis(don_hang, kenh_ban):
    """Analyze sales by channel."""
    print("\n" + "=" * 80)
    print("SALES CHANNEL ANALYSIS")
    print("=" * 80)

    channel_sales = (
        don_hang.groupby("MA_KENHBANCHITIET")
        .agg({"GIA_TIEN": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "contract_count"})
    )

    channel_sales = channel_sales.sort_values("GIA_TIEN", ascending=False)

    print("\nTop 10 sales channels by revenue:")
    for channel_id, row in channel_sales.head(10).iterrows():
        channel_name = kenh_ban[kenh_ban["MA_KENHBANCHITIET"] == channel_id][
            "TENKENHBANCHITIET"
        ].values
        name = channel_name[0] if len(channel_name) > 0 else "Unknown"
        print(f"  {channel_id} ({name}):")
        print(f"    - Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"    - Contracts: {row['contract_count']:,}")

    channel_type_map = kenh_ban.set_index("MA_KENHBANCHITIET")["MA_KENHBAN"].to_dict()
    don_hang["channel_type"] = don_hang["MA_KENHBANCHITIET"].map(channel_type_map)

    type_sales = (
        don_hang.groupby("channel_type")
        .agg({"GIA_TIEN": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "contract_count"})
    )

    print("\nSales by channel type:")
    print(type_sales)

    return channel_sales


def employee_performance(don_hang):
    """Analyze employee performance."""
    print("\n" + "=" * 80)
    print("EMPLOYEE PERFORMANCE")
    print("=" * 80)

    employee_stats = don_hang.groupby("MA_NV").agg(
        {"GIA_TIEN": ["sum", "mean"], "MA_HD": "count"}
    )
    employee_stats.columns = ["total_revenue", "avg_revenue", "contract_count"]
    employee_stats = employee_stats.sort_values("total_revenue", ascending=False)

    print("\nTop 10 employees by total revenue:")
    for i, (emp_id, row) in enumerate(employee_stats.head(10).iterrows(), 1):
        print(f"  {i}. {emp_id}:")
        print(f"     - Total Revenue: {row['total_revenue']:,.0f} VND")
        print(f"     - Avg Revenue: {row['avg_revenue']:,.0f} VND")
        print(f"     - Contracts: {row['contract_count']:,}")

    print(f"\nEmployee statistics:")
    print(f"  - Total employees with sales: {len(employee_stats):,}")
    print(
        f"  - Average revenue per employee: {employee_stats['total_revenue'].mean():,.0f} VND"
    )
    print(
        f"  - Median contracts per employee: {employee_stats['contract_count'].median():.0f}"
    )

    return employee_stats


def time_series_analysis(don_hang):
    """Analyze orders over time."""
    print("\n" + "=" * 80)
    print("TIME SERIES ANALYSIS")
    print("=" * 80)

    don_hang["NGAY_KY_HD"] = pd.to_datetime(don_hang["NGAY_KY_HD"], errors="coerce")
    don_hang["year_month"] = don_hang["NGAY_KY_HD"].dt.to_period("M")

    monthly_stats = (
        don_hang.groupby("year_month")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "contract_count"})
    )

    print("\nMonthly Order Statistics (first 12 months):")
    for period, row in monthly_stats.head(12).iterrows():
        print(f"  {period}:")
        print(f"    - Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"    - Insurance Fee: {row['GIA_BH']:,.0f} VND")
        print(f"    - Contracts: {row['contract_count']:,}")

    return monthly_stats


def kpi_analysis(kpi):
    """Analyze KPI data."""
    print("\n" + "=" * 80)
    print("KPI ANALYSIS")
    print("=" * 80)

    print(f"Total KPI records: {len(kpi):,}")
    print(f"\nTime range: {kpi['THANGNAM'].min()} to {kpi['THANGNAM'].max()}")

    print(f"\nKPI by sales channel:")
    kpi_by_channel = kpi.groupby("MA_KENHBAN").agg({"SLHD": "sum", "DOANH_THU": "sum"})
    print(kpi_by_channel)

    print(f"\nKPI by product:")
    kpi_by_product = (
        kpi.groupby("MA_GOISANPHAM")
        .agg({"SLHD": "sum", "DOANH_THU": "sum"})
        .sort_values("DOANH_THU", ascending=False)
    )
    print(kpi_by_product.head(10))

    return kpi_by_channel, kpi_by_product


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - CONTRACT & ORDER ANALYSIS")
    print("=" * 80)

    hop_dong, don_hang, kpi, goi_sp, kenh_ban = load_transaction_data()

    print(f"\nLoaded {len(hop_dong):,} contract records")
    print(f"Loaded {len(don_hang):,} order records")
    print(f"Loaded {len(kpi):,} KPI records")

    contract_overview(hop_dong)
    product_analysis(hop_dong, goi_sp)
    order_analysis(don_hang)
    revenue_analysis(don_hang)
    sales_channel_analysis(don_hang, kenh_ban)
    employee_performance(don_hang)
    time_series_analysis(don_hang)
    kpi_analysis(kpi)

    print("\n" + "=" * 80)
    print("Contract and order analysis complete!")
    print("=" * 80)
