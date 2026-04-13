#!/usr/bin/env python3
"""
Data Overview - Insurance Dataset Exploration
Initial data loading, structure analysis, and basic statistics
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_all_data():
    """Load all CSV files from the data directory."""
    data = {}

    files = {
        "bao_hiem": "Bảo Hiểm.csv",
        "chi_nhanh": "Chi nhánh.csv",
        "cong_ty": "Công ty.csv",
        "goi_san_pham": "Gói Sản Phẩm.csv",
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
        filepath = DATA_PATH / filename
        if filepath.exists():
            try:
                data[key] = pd.read_csv(filepath)
                print(
                    f"Loaded {filename}: {data[key].shape[0]} rows, {data[key].shape[1]} columns"
                )
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return data


def display_basic_info(data):
    """Display basic information about each dataset."""
    print("\n" + "=" * 80)
    print("BASIC DATA INFORMATION")
    print("=" * 80)

    for name, df in data.items():
        print(f"\n--- {name.upper()} ---")
        print(f"Shape: {df.shape}")
        print(f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"Columns: {list(df.columns)}")
        print(f"Data types:\n{df.dtypes}")


def data_summary_statistics(data):
    """Generate summary statistics for all datasets."""
    summary = []

    for name, df in data.items():
        summary.append(
            {
                "Table": name,
                "Rows": df.shape[0],
                "Columns": df.shape[1],
                "Missing Values": df.isnull().sum().sum(),
                "Duplicate Rows": df.duplicated().sum(),
                "Memory (MB)": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}",
            }
        )

    summary_df = pd.DataFrame(summary)
    print("\n" + "=" * 80)
    print("DATA SUMMARY")
    print("=" * 80)
    print(summary_df.to_string(index=False))

    return summary_df


def analyze_dimension_tables(data):
    """Analyze dimension/reference tables."""
    print("\n" + "=" * 80)
    print("DIMENSION TABLES ANALYSIS")
    print("=" * 80)
    if "bao_hiem" in data:
        print("\n--- Insurance Types (Bảo Hiểm) ---")
        print(data["bao_hiem"])

    if "cong_ty" in data:
        print("\n--- Companies (Công ty) ---")
        print(data["cong_ty"])

    if "hang_xe" in data:
        print("\n--- Vehicle Brands (Hãng Xe) ---")
        print(f"Total brands: {len(data['hang_xe'])}")
        print(data["hang_xe"].head(10))

    if "nghe_nghiep" in data:
        print("\n--- Occupations (Nghề nghiệp) ---")
        print(f"Total occupations: {len(data['nghe_nghiep'])}")
        print(data["nghe_nghiep"])

    if "xep_hang_kh" in data:
        print("\n--- Customer Tiers (Xếp hạng khách hàng) ---")
        print(data["xep_hang_kh"])


def analyze_dimensional_hierarchy(data):
    """Analyze dimensional hierarchies and relationships."""
    print("\n" + "=" * 80)
    print("DIMENSIONAL HIERARCHY ANALYSIS")
    print("=" * 80)
    if "chi_nhanh" in data and "cong_ty" in data:
        print("\n--- Branches by Company ---")
        branches_by_company = data["chi_nhanh"].groupby("MA_CONGTY").size()
        print(branches_by_company)

    if "phong_ban" in data:
        print("\n--- Departments by Branch ---")
        dept_by_branch = data["phong_ban"].groupby("MA_CN").size()
        print(dept_by_branch.head(10))

    if "kenh_ban_ct" in data and "kenh_ban" in data:
        print("\n--- Sales Channels by Type ---")
        channels_by_type = data["kenh_ban_ct"].groupby("MA_KENHBAN").size()
        print(channels_by_type)

    if "nhom_sp" in data and "bao_hiem" in data:
        print("\n--- Product Groups by Insurance Type ---")
        products_by_type = data["nhom_sp"].groupby("MABH").size()
        print(products_by_type)


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - DATA OVERVIEW")
    print("=" * 80)

    data = load_all_data()

    display_basic_info(data)

    summary = data_summary_statistics(data)

    analyze_dimension_tables(data)

    analyze_dimensional_hierarchy(data)

    print("\n" + "=" * 80)
    print("Data overview complete!")
    print("=" * 80)
