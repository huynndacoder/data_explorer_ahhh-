#!/usr/bin/env python3
"""
Product & Channel Analysis - Insurance Dataset EDA
Analysis of products, sales channels, and their relationships
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_product_data():
    """Load product and channel-related data."""
    goi_sp = pd.read_csv(DATA_PATH / "Gói Sản Phẩm.csv")
    nhom_sp = pd.read_csv(DATA_PATH / "Nhóm sản phẩm.csv")
    bao_hiem = pd.read_csv(DATA_PATH / "Bảo Hiểm.csv")
    kenh_ban = pd.read_csv(DATA_PATH / "Kênh Bán.csv")
    kenh_ban_ct = pd.read_csv(DATA_PATH / "Kênh bán chi tiết.csv")
    kpi = pd.read_csv(DATA_PATH / "KPI.csv")
    don_hang = pd.read_csv(DATA_PATH / "Đơn hàng.csv")
    hop_dong = pd.read_csv(DATA_PATH / "Hợp đồng.csv")

    return goi_sp, nhom_sp, bao_hiem, kenh_ban, kenh_ban_ct, kpi, don_hang, hop_dong


def product_overview(goi_sp, nhom_sp, bao_hiem):
    """Analyze product structure."""
    print("\n" + "=" * 80)
    print("PRODUCT OVERVIEW")
    print("=" * 80)

    print(f"Total product packages: {len(goi_sp)}")
    print(f"Product groups: {len(nhom_sp)}")
    print(f"Insurance types: {len(bao_hiem)}")

    print("\n--- Insurance Types ---")
    print(bao_hiem.to_string(index=False))

    print("\n--- Product Groups ---")
    for _, row in nhom_sp.iterrows():
        print(f"  {row['MA_NHOMSANPHAM']}: {row['NHOMSANPHAM']}")
        print(f"    Description: {row['MOTA_NHOM']}")
        print(f"    Insurance Type: {row['MABH']}")

    print("\n--- Product Packages ---")
    for _, row in goi_sp.iterrows():
        print(f"  {row['MA_GOISANPHAM']}: {row['TENGOISANPHAM']}")
        print(f"    Group: {row['MA_NHOMSANPHAM']}")


def product_sales_analysis(don_hang, goi_sp):
    """Analyze sales by product."""
    print("\n" + "=" * 80)
    print("PRODUCT SALES ANALYSIS")
    print("=" * 80)

    product_sales = (
        don_hang.groupby("MA_GSP")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )
    product_sales = product_sales.sort_values("GIA_TIEN", ascending=False)

    print("\nTop products by revenue:")
    for product_id, row in product_sales.head(15).iterrows():
        product_name = goi_sp[goi_sp["MA_GOISANPHAM"] == product_id][
            "TENGOISANPHAM"
        ].values
        name = product_name[0] if len(product_name) > 0 else "Unknown"
        print(f"  {product_id} ({name}):")
        print(f"    Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"    Insurance Fee: {row['GIA_BH']:,.0f} VND")
        print(f"    Contracts: {row['num_contracts']:,}")

    print(f"\n\nLeast sold products:")
    for product_id, row in product_sales.tail(10).iterrows():
        product_name = goi_sp[goi_sp["MA_GOISANPHAM"] == product_id][
            "TENGOISANPHAM"
        ].values
        name = product_name[0] if len(product_name) > 0 else "Unknown"
        print(f"  {product_id} ({name}): {row['num_contracts']:,} contracts")

    return product_sales


def channel_overview(kenh_ban, kenh_ban_ct):
    """Analyze sales channels."""
    print("\n" + "=" * 80)
    print("SALES CHANNEL OVERVIEW")
    print("=" * 80)

    print(f"Total channel types: {len(kenh_ban)}")
    print(f"Total detailed channels: {len(kenh_ban_ct)}")

    print("\n--- Channel Types ---")
    for _, row in kenh_ban.iterrows():
        channels_of_type = kenh_ban_ct[kenh_ban_ct["MA_KENHBAN"] == row["MA_KENHBAN"]]
        print(
            f"  {row['MA_KENHBAN']} ({row['TENKENHBAN']}): {len(channels_of_type)} channels"
        )

    print("\n--- Channel Details (sample) ---")
    print(kenh_ban_ct.head(20).to_string(index=False))


def channel_sales_analysis(don_hang, kenh_ban, kenh_ban_ct):
    """Analyze sales by channel."""
    print("\n" + "=" * 80)
    print("CHANNEL SALES ANALYSIS")
    print("=" * 80)

    channel_sales = (
        don_hang.groupby("MA_KENHBANCHITIET")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )
    channel_sales = channel_sales.sort_values("GIA_TIEN", ascending=False)

    print("\nTop 20 sales channels by revenue:")
    for i, (channel_id, row) in enumerate(channel_sales.head(20).iterrows(), 1):
        channel_name = kenh_ban_ct[kenh_ban_ct["MA_KENHBANCHITIET"] == channel_id][
            "TENKENHBANCHITIET"
        ].values
        name = channel_name[0] if len(channel_name) > 0 else "Unknown"
        channel_type = kenh_ban_ct[kenh_ban_ct["MA_KENHBANCHITIET"] == channel_id][
            "MA_KENHBAN"
        ].values[0]
        type_name = (
            kenh_ban[kenh_ban["MA_KENHBAN"] == channel_type]["TENKENHBAN"].values[0]
            if channel_type
            else "Unknown"
        )

        print(f"  {i}. {channel_id} ({name})")
        print(f"     Type: {type_name}")
        print(f"     Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"     Contracts: {row['num_contracts']:,}")

    channel_type_map = kenh_ban_ct.set_index("MA_KENHBANCHITIET")[
        "MA_KENHBAN"
    ].to_dict()
    don_hang["channel_type"] = don_hang["MA_KENHBANCHITIET"].map(channel_type_map)

    type_sales = (
        don_hang.groupby("channel_type")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )
    type_sales = type_sales.sort_values("GIA_TIEN", ascending=False)

    print("\n\nSales by channel type:")
    for channel_type, row in type_sales.iterrows():
        type_name = (
            kenh_ban[kenh_ban["MA_KENHBAN"] == channel_type]["TENKENHBAN"].values[0]
            if channel_type
            else "Unknown"
        )
        total_revenue = type_sales["GIA_TIEN"].sum()
        pct = row["GIA_TIEN"] / total_revenue * 100
        print(f"  {channel_type} ({type_name}):")
        print(f"    Revenue: {row['GIA_TIEN']:,.0f} VND ({pct:.1f}%)")
        print(f"    Contracts: {row['num_contracts']:,}")

    return channel_sales


def kpi_analysis(kpi, goi_sp, kenh_ban):
    """Analyze KPI data."""
    print("\n" + "=" * 80)
    print("KPI ANALYSIS")
    print("=" * 80)

    print(f"Total KPI records: {len(kpi):,}")
    print(f"Unique time periods: {kpi['THANGNAM'].nunique()}")

    print(f"\nTime range: {kpi['THANGNAM'].min()} to {kpi['THANGNAM'].max()}")

    kpi_by_product = (
        kpi.groupby("MA_GOISANPHAM")
        .agg({"SLHD": "sum", "DOANH_THU": "sum"})
        .sort_values("DOANH_THU", ascending=False)
    )

    print("\nKPI by product:")
    for product_id, row in kpi_by_product.iterrows():
        product_name = goi_sp[goi_sp["MA_GOISANPHAM"] == product_id][
            "TENGOISANPHAM"
        ].values
        name = product_name[0] if len(product_name) > 0 else "Unknown"
        print(f"  {product_id} ({name}):")
        print(f"    Contracts: {row['SLHD']:,}")
        print(f"    Revenue: {row['DOANH_THU']:,.0f} VND")

    kpi_by_channel = (
        kpi.groupby("MA_KENHBAN")
        .agg({"SLHD": "sum", "DOANH_THU": "sum"})
        .sort_values("DOANH_THU", ascending=False)
    )

    print("\nKPI by channel type:")
    for channel_type, row in kpi_by_channel.iterrows():
        type_name = (
            kenh_ban[kenh_ban["MA_KENHBAN"] == channel_type]["TENKENHBAN"].values[0]
            if channel_type
            else "Unknown"
        )
        print(f"  {channel_type} ({type_name}):")
        print(f"    Contracts: {row['SLHD']:,}")
        print(f"    Revenue: {row['DOANH_THU']:,.0f} VND")

    return kpi_by_product, kpi_by_channel


def product_channel_combo(don_hang, goi_sp, kenh_ban_ct):
    """Analyze product-channel combinations."""
    print("\n" + "=" * 80)
    print("PRODUCT-CHANNEL COMBINATION ANALYSIS")
    print("=" * 80)

    combo = (
        don_hang.groupby(["MA_KENHBANCHITIET", "MA_GSP"])
        .agg({"GIA_TIEN": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )
    combo = combo.sort_values("GIA_TIEN", ascending=False)

    print("\nTop 20 product-channel combinations:")
    for i, ((channel_id, product_id), row) in enumerate(combo.head(20).iterrows(), 1):
        product_name = (
            goi_sp[goi_sp["MA_GOISANPHAM"] == product_id]["TENGOISANPHAM"].values[0]
            if product_id
            else "Unknown"
        )

        print(f"  {i}. {product_id}: {product_name[:40]}...")
        print(
            f"     Revenue: {row['GIA_TIEN']:,.0f} VND, Contracts: {row['num_contracts']:,}"
        )

    return combo


def contract_duration_analysis(don_hang):
    """Analyze contract duration patterns."""
    print("\n" + "=" * 80)
    print("CONTRACT DURATION ANALYSIS")
    print("=" * 80)

    duration_dist = don_hang["THOI_HAN_THANG"].value_counts().sort_index()

    print("\nContract duration distribution:")
    for duration, count in duration_dist.items():
        pct = count / len(don_hang) * 100
        print(f"  {duration} months: {count:,} contracts ({pct:.1f}%)")

    avg_price_by_duration = don_hang.groupby("THOI_HAN_THANG")["GIA_TIEN"].agg(
        ["mean", "median", "std"]
    )

    print("\nAverage price by duration:")
    print(avg_price_by_duration)

    return duration_dist


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - PRODUCT & CHANNEL ANALYSIS")
    print("=" * 80)

    goi_sp, nhom_sp, bao_hiem, kenh_ban, kenh_ban_ct, kpi, don_hang, hop_dong = (
        load_product_data()
    )

    print(f"\nLoaded {len(goi_sp)} product packages")
    print(f"Loaded {len(nhom_sp)} product groups")
    print(f"Loaded {len(kenh_ban)} channel types")
    print(f"Loaded {len(kenh_ban_ct)} detailed channels")
    print(f"Loaded {len(kpi)} KPI records")
    print(f"Loaded {len(don_hang):,} order records")

    product_overview(goi_sp, nhom_sp, bao_hiem)
    product_sales_analysis(don_hang, goi_sp)
    channel_overview(kenh_ban, kenh_ban_ct)
    channel_sales_analysis(don_hang, kenh_ban, kenh_ban_ct)
    kpi_analysis(kpi, goi_sp, kenh_ban)
    product_channel_combo(don_hang, goi_sp, kenh_ban_ct)
    contract_duration_analysis(don_hang)

    print("\n" + "=" * 80)
    print("Product and channel analysis complete!")
    print("=" * 80)
