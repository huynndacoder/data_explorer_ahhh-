#!/usr/bin/env python3
"""
Comprehensive Summary Report - Insurance Dataset EDA
Executive summary combining all analysis modules
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_all_data():
    """Load all CSV files."""
    data = {}
    files = {
        "bao_hiem": "Bảo Hiểm.csv",
        "chi_nhanh": "Chi nhánh.csv",
        "cong_ty": "Công ty.csv",
        "goi_sp": "Gói Sản Phẩm.csv",
        "hang_xe": "Hãng Xe.csv",
        "kenh_ban": "Kênh Bán.csv",
        "kenh_ban_ct": "Kênh bán chi tiết.csv",
        "do_tuoi": "Độ tuổi.csv",
        "loai_xe": "Loại xe cơ giới.csv",
        "nghe_nghiep": "Nghề nghiệp.csv",
        "nhom_sp": "Nhóm sản phẩm.csv",
        "phong_ban": "Phòng ban.csv",
        "trang_thai": "Trạng thái đăng ký.csv",
        "xep_hang_kh": "Xếp hạng khách hạng.csv",
        "ma_nv": "Mã nhân viên.csv",
        "nhan_vien": "Nhân viên.csv",
        "xe_co_gioi": "Xe cơ giới.csv",
        "khach_hang": "Khách hàng.csv",
        "hop_dong": "Hợp đồng.csv",
        "don_hang": "Đơn hàng.csv",
        "thong_tin_xe": "Thông tin xe cơ giới.csv",
        "kpi": "KPI.csv",
    }

    for key, filename in files.items():
        try:
            data[key] = pd.read_csv(DATA_PATH / filename)
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")

    return data


def executive_summary(data):
    """Generate executive summary."""
    print("=" * 80)
    print("EXECUTIVE SUMMARY - INSURANCE DATA ANALYSIS")
    print("=" * 80)
    print(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "-" * 40)
    print("BUSINESS OVERVIEW")
    print("-" * 40)

    print(f"\nCompanies: {len(data['cong_ty'])} insurance companies")
    for _, row in data["cong_ty"].iterrows():
        print(f"  - {row['MA_CONGTY']}: {row['TEN_CONGTY']}")

    print(f"\nBranches: {len(data['chi_nhanh'])} locations")
    print(f"Departments: {len(data['phong_ban'])}")
    print(f"Employees: {len(data['nhan_vien'])}")

    print(f"\nCustomers: {len(data['khach_hang']):,}")
    print(f"Contracts: {len(data['hop_dong']):,}")
    print(f"Orders: {len(data['don_hang']):,}")

    print("\n" + "-" * 40)
    print("REVENUE METRICS")
    print("-" * 40)

    total_revenue = data["don_hang"]["GIA_TIEN"].sum()
    total_insurance_fee = data["don_hang"]["GIA_BH"].sum()

    print(f"\nTotal Contract Value: {total_revenue:,.0f} VND")
    print(f"  = {total_revenue / 1e12:.2f} trillion VND")
    print(f"  = {total_revenue / 1e9:.2f} billion VND")

    print(f"\nTotal Insurance Fee: {total_insurance_fee:,.0f} VND")
    print(f"  = {total_insurance_fee / 1e9:.2f} billion VND")

    avg_contract = data["don_hang"]["GIA_TIEN"].mean()
    median_contract = data["don_hang"]["GIA_TIEN"].median()
    print(f"\nAverage Contract Value: {avg_contract:,.0f} VND")
    print(f"Median Contract Value: {median_contract:,.0f} VND")

    print("\n" + "-" * 40)
    print("CUSTOMER PROFILE")
    print("-" * 40)

    gender_dist = data["khach_hang"]["GIOI_TINH"].value_counts()
    print(f"\nGender Distribution:")
    for gender, count in gender_dist.items():
        pct = count / len(data["khach_hang"]) * 100
        print(f"  {gender}: {count:,} ({pct:.1f}%)")

    avg_age = data["khach_hang"]["TUOI"].mean()
    print(f"\nAverage Customer Age: {avg_age:.1f} years")

    tier_dist = data["khach_hang"]["XHKH"].value_counts()
    print(f"\nCustomer Tier Distribution:")
    tier_order = ["Đồng", "Bạc", "Vàng", "Bạch kim", "Kim cương"]
    for tier in tier_order:
        if tier in tier_dist:
            count = tier_dist[tier]
            pct = count / len(data["khach_hang"]) * 100
            print(f"  {tier}: {count:,} ({pct:.1f}%)")

    print("\n" + "-" * 40)
    print("PRODUCT & SALES")
    print("-" * 40)

    print(f"\nInsurance Types: {len(data['bao_hiem'])}")
    print(f"Product Groups: {len(data['nhom_sp'])}")
    print(f"Product Packages: {len(data['goi_sp'])}")

    top_products = (
        data["don_hang"]
        .groupby("MA_GSP")["GIA_TIEN"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    print(f"\nTop 5 Products by Revenue:")
    for prod_id, revenue in top_products.items():
        prod_name = (
            data["goi_sp"][data["goi_sp"]["MA_GOISANPHAM"] == prod_id][
                "TENGOISANPHAM"
            ].values[0]
            if prod_id
            else "Unknown"
        )
        print(f"  {prod_id}: {prod_name[:40]}...")
        print(f"    Revenue: {revenue:,.0f} VND")

    print(
        f"\nSales Channels: {len(data['kenh_ban'])} types, {len(data['kenh_ban_ct'])} detailed channels"
    )
    channel_sales = (
        data["don_hang"]
        .groupby("MA_KENHBANCHITIET")["GIA_TIEN"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    print(f"Top 5 Sales Channels by Revenue:")
    for i, (channel_id, revenue) in enumerate(channel_sales.items(), 1):
        channel_name = data["kenh_ban_ct"][
            data["kenh_ban_ct"]["MA_KENHBANCHITIET"] == channel_id
        ]["TENKENHBANCHITIET"].values
        name = channel_name[0] if len(channel_name) > 0 else "Unknown"
        print(f"  {i}. {name[:50]}...")
        print(f"     Revenue: {revenue:,.0f} VND")

    print("\n" + "-" * 40)
    print("VEHICLE INSURANCE")
    print("-" * 40)

    print(f"\nVehicle Brands: {len(data['hang_xe'])}")
    print(f"Vehicle Models: {len(data['xe_co_gioi'])}")
    print(f"Insured Vehicles: {len(data['thong_tin_xe']):,}")

    print(f"\nPrice Range:")
    print(f"  Min: {data['xe_co_gioi']['GIA_TIEN'].min():,.0f} VND")
    print(f"  Max: {data['xe_co_gioi']['GIA_TIEN'].max():,.0f} VND")
    print(f"  Average: {data['xe_co_gioi']['GIA_TIEN'].mean():,.0f} VND")

    print("\n" + "-" * 40)
    print("EMPLOYEE PERFORMANCE")
    print("-" * 40)

    employee_sales = (
        data["don_hang"]
        .groupby("MA_NV")
        .agg({"GIA_TIEN": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "contracts"})
    )
    employee_sales = employee_sales.sort_values("GIA_TIEN", ascending=False)

    print(f"\nTotal Employees with Sales: {len(employee_sales):,}")
    print(f"Average Revenue per Employee: {employee_sales['GIA_TIEN'].mean():,.0f} VND")
    print(f"Median Contracts per Employee: {employee_sales['contracts'].median():.0f}")

    top_employees = employee_sales.head(5)
    print(f"\nTop 5 Employees by Revenue:")
    for emp_id, row in top_employees.iterrows():
        print(f"  {emp_id}:")
        print(f"    Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"    Contracts: {row['contracts']:,}")

    print("\n" + "-" * 40)
    print("TIME RANGE")
    print("-" * 40)

    data["don_hang"]["NGAY_KY_HD"] = pd.to_datetime(
        data["don_hang"]["NGAY_KY_HD"], errors="coerce"
    )
    min_date = data["don_hang"]["NGAY_KY_HD"].min()
    max_date = data["don_hang"]["NGAY_KY_HD"].max()

    print(
        f"\nOrder Date Range: {min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else 'N/A'} to {max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else 'N/A'}"
    )

    monthly_orders = (
        data["don_hang"]
        .groupby(data["don_hang"]["NGAY_KY_HD"].dt.to_period("M"))["GIA_TIEN"]
        .sum()
    )
    print(f"Months with activity: {len(monthly_orders)}")

    print("\n" + "-" * 40)
    print("KEY INSIGHTS & RECOMMENDATIONS")
    print("-" * 40)

    print("\n1. Customer Segmentation:")
    print("   - Focus on Bạc (Silver) tier customers who represent the majority")
    print("   - Develop strategies to upgrade customers to higher tiers")
    high_tier = data["khach_hang"][
        data["khach_hang"]["XHKH"].isin(["Vàng", "Bạch kim", "Kim cương"])
    ].shape[0]
    print(
        f"   - Current high-tier customers: {high_tier:,} ({high_tier / len(data['khach_hang']) * 100:.1f}%)"
    )

    print("\n2. Sales Channels:")
    direct_channel = data["don_hang"][
        data["don_hang"]["MA_KENHBANCHITIET"].str.startswith("DC", na=False)
    ]["GIA_TIEN"].sum()
    print(
        f"   - Direct channel revenue: {direct_channel:,.0f} VND ({direct_channel / total_revenue * 100:.1f}%)"
    )
    print("   - Consider expanding digital channels for growth")

    print("\n3. Product Strategy:")
    print(f"   - {len(data['goi_sp'])} product packages available")
    print("   - Focus on high-revenue products for cross-selling opportunities")
    print("   - Consider bundling strategies for related products")

    print("\n4. Employee Productivity:")
    top10_pct = employee_sales.head(int(len(employee_sales) * 0.1))["GIA_TIEN"].sum()
    print(
        f"   - Top 10% employees contribute {top10_pct / total_revenue * 100:.1f}% of revenue"
    )
    print("   - Identify and replicate best practices from top performers")

    print("\n5. Vehicle Insurance:")
    vehicle_contracts = data["thong_tin_xe"]["MA_HD"].nunique()
    print(f"   - {vehicle_contracts:,} vehicle insurance contracts")
    print(f"   - {data['xe_co_gioi']['MA_HANG_XE'].nunique()} vehicle brands covered")
    print("   - High-value vehicles represent significant premium opportunity")

    print("\n" + "=" * 80)
    print("END OF EXECUTIVE SUMMARY")
    print("=" * 80)


def data_quality_report(data):
    """Generate data quality report."""
    print("\n" + "=" * 80)
    print("DATA QUALITY REPORT")
    print("=" * 80)

    quality_issues = []

    for table_name, df in data.items():
        missing = df.isnull().sum().sum()
        duplicates = df.duplicated().sum()

        if missing > 0:
            quality_issues.append(f"  {table_name}: {missing} missing values")
        if duplicates > 0:
            quality_issues.append(f"  {table_name}: {duplicates} duplicate rows")

    if quality_issues:
        print("\nData Quality Issues Found:")
        for issue in quality_issues:
            print(issue)
    else:
        print("\nNo significant data quality issues found.")

    print("\n" + "-" * 40)
    print("REFERENTIAL INTEGRITY CHECK")
    print("-" * 40)

    kh_in_orders = set(data["don_hang"]["MA_KH"].unique())
    kh_in_customers = set(data["khach_hang"]["MA_KH"].unique())
    orphan_orders = kh_in_orders - kh_in_customers
    print(f"\nOrders with missing customer references: {len(orphan_orders):,}")

    nv_in_orders = set(data["don_hang"]["MA_NV"].unique())
    nv_in_employee = set(data["ma_nv"]["MA_NV"].unique())
    orphan_employees = nv_in_orders - nv_in_employee
    print(f"Orders with missing employee references: {len(orphan_employees):,}")

    gsp_in_contracts = set(data["hop_dong"]["MA_GSP"].unique())
    gsp_in_products = set(data["goi_sp"]["MA_GOISANPHAM"].unique())
    orphan_products = gsp_in_contracts - gsp_in_products
    print(f"Contracts with missing product references: {len(orphan_products):,}")


if __name__ == "__main__":
    print("\nLoading all data...")
    data = load_all_data()
    print(f"Loaded {len(data)} tables\n")

    executive_summary(data)
    data_quality_report(data)
