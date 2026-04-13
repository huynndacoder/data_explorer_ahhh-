#!/usr/bin/env python3
"""
Employee & Branch Analysis - Insurance Dataset EDA
Analysis of employees, branches, departments, and organizational structure
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_employee_data():
    """Load employee-related data."""
    nhan_vien = pd.read_csv(DATA_PATH / "Nhân viên.csv")
    ma_nv = pd.read_csv(DATA_PATH / "Mã nhân viên.csv")
    chi_nhanh = pd.read_csv(DATA_PATH / "Chi nhánh.csv")
    cong_ty = pd.read_csv(DATA_PATH / "Công ty.csv")
    phong_ban = pd.read_csv(DATA_PATH / "Phòng ban.csv")
    don_hang = pd.read_csv(DATA_PATH / "Đơn hàng.csv")

    return nhan_vien, ma_nv, chi_nhanh, cong_ty, phong_ban, don_hang


def employee_overview(nhan_vien):
    """Basic employee statistics."""
    print("\n" + "=" * 80)
    print("EMPLOYEE OVERVIEW")
    print("=" * 80)

    print(f"Total employees: {len(nhan_vien):,}")

    print(f"\nAge statistics:")
    print(f"  - Min age: {nhan_vien['TUOI'].min():.0f}")
    print(f"  - Max age: {nhan_vien['TUOI'].max():.0f}")
    print(f"  - Mean age: {nhan_vien['TUOI'].mean():.1f}")
    print(f"  - Median age: {nhan_vien['TUOI'].median():.0f}")

    age_bins = [20, 25, 30, 35, 40, 45, 50, 60]
    age_labels = ["20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"]
    nhan_vien["age_group"] = pd.cut(nhan_vien["TUOI"], bins=age_bins, labels=age_labels)

    print(f"\nAge distribution:")
    age_dist = nhan_vien["age_group"].value_counts().sort_index()
    for group, count in age_dist.items():
        pct = count / len(nhan_vien) * 100
        print(f"  {group}: {count} ({pct:.1f}%)")

    return nhan_vien["TUOI"].describe()


def branch_analysis(chi_nhanh, cong_ty):
    """Analyze branch distribution."""
    print("\n" + "=" * 80)
    print("BRANCH ANALYSIS")
    print("=" * 80)

    print(f"Total branches: {len(chi_nhanh):,}")

    branches_by_company = chi_nhanh.groupby("MA_CONGTY").size()

    print(f"\nBranches by company:")
    for company_id, count in branches_by_company.items():
        company_name = cong_ty[cong_ty["MA_CONGTY"] == company_id]["TEN_CONGTY"].values
        name = company_name[0] if len(company_name) > 0 else "Unknown"
        print(f"  {company_id} ({name}): {count} branches")

    branches_by_location = chi_nhanh["TEN_CN"].value_counts()

    print(f"\nBranches by location (top 10):")
    for location, count in branches_by_location.head(10).items():
        print(f"  {location}: {count}")

    return branches_by_company


def department_analysis(phong_ban):
    """Analyze department structure."""
    print("\n" + "=" * 80)
    print("DEPARTMENT ANALYSIS")
    print("=" * 80)

    print(f"Total departments: {len(phong_ban):,}")

    departments_by_branch = phong_ban.groupby("MA_CN").size()

    print(f"\nDepartments per branch (top 10):")
    for branch, count in departments_by_branch.head(10).items():
        print(f"  {branch}: {count} departments")

    departments_by_type = (
        phong_ban["TEN_PHONGBAN"].str.extract(r"(\w+)")[0].value_counts()
    )

    print(f"\nDepartment types:")
    for dept_type, count in departments_by_type.head(10).items():
        print(f"  {dept_type}: {count}")

    xcg_depts = phong_ban[
        phong_ban["TEN_PHONGBAN"].str.contains("Xe cơ giới", na=False)
    ]
    cn_depts = phong_ban[phong_ban["TEN_PHONGBAN"].str.contains("Con người", na=False)]

    print(f"\nBy business line:")
    print(f"  Vehicle insurance (Xe cơ giới): {len(xcg_depts)} departments")
    print(f"  Personal insurance (Con người): {len(cn_depts)} departments")

    return departments_by_branch


def employee_mapping_analysis(ma_nv):
    """Analyze employee mapping to branches."""
    print("\n" + "=" * 80)
    print("EMPLOYEE MAPPING ANALYSIS")
    print("=" * 80)

    print(f"Total employee mappings: {len(ma_nv):,}")

    employees_by_company = ma_nv.groupby("MA_CONGTY").size()

    print(f"\nEmployees by company:")
    for company, count in employees_by_company.items():
        print(f"  {company}: {count:,} employees")

    employees_by_branch = ma_nv.groupby("MA_CN").size().sort_values(ascending=False)

    print(f"\nTop 10 branches by employee count:")
    for branch, count in employees_by_branch.head(10).items():
        print(f"  {branch}: {count:,} employees")

    employees_by_dept_type = ma_nv["MA_PB"].str.extract(r"-(\w+)$")[0].value_counts()

    print(f"\nEmployees by department type:")
    for dept_type, count in employees_by_dept_type.items():
        print(f"  {dept_type}: {count:,} employees")

    return employees_by_branch


def sales_performance_by_employee(don_hang, nhan_vien):
    """Analyze sales performance by employee."""
    print("\n" + "=" * 80)
    print("EMPLOYEE SALES PERFORMANCE")
    print("=" * 80)

    sales_by_emp = (
        don_hang.groupby("MA_NV")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )

    sales_by_emp = sales_by_emp.sort_values("GIA_TIEN", ascending=False)

    print(f"\nEmployees with sales: {len(sales_by_emp):,}")
    print(f"Total revenue: {sales_by_emp['GIA_TIEN'].sum():,.0f} VND")

    print(f"\nTop 20 employees by total revenue:")
    for i, (emp_id, row) in enumerate(sales_by_emp.head(20).iterrows(), 1):
        emp_name = nhan_vien[
            nhan_vien["MA_GOCNV"] == emp_id[:5] if len(emp_id) > 5 else emp_id
        ]["HO_TEN"].values
        name = emp_name[0] if len(emp_name) > 0 else "Unknown"
        print(f"  {i}. {emp_id} ({name}):")
        print(f"     Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"     Contracts: {row['num_contracts']:,}")

    print(f"\nPerformance statistics:")
    print(f"  Average revenue per employee: {sales_by_emp['GIA_TIEN'].mean():,.0f} VND")
    print(f"  Median revenue: {sales_by_emp['GIA_TIEN'].median():,.0f} VND")
    print(
        f"  Average contracts per employee: {sales_by_emp['num_contracts'].mean():.1f}"
    )

    return sales_by_emp


def company_comparison(don_hang, ma_nv):
    """Compare sales between companies."""
    print("\n" + "=" * 80)
    print("COMPANY COMPARISON")
    print("=" * 80)

    emp_company_map = ma_nv.set_index("MA_NV")["MA_CONGTY"].to_dict()
    don_hang["company"] = don_hang["MA_NV"].map(emp_company_map)

    company_sales = (
        don_hang.groupby("company")
        .agg({"GIA_TIEN": "sum", "GIA_BH": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )

    print("\nSales by company:")
    for company, row in company_sales.iterrows():
        print(f"\n{company}:")
        print(f"  Total Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"  Total Insurance Fee: {row['GIA_BH']:,.0f} VND")
        print(f"  Total Contracts: {row['num_contracts']:,}")

    employees_per_company = don_hang.groupby("company")["MA_NV"].nunique()
    print("\nActive employees by company:")
    for company, count in employees_per_company.items():
        avg_revenue = company_sales.loc[company, "GIA_TIEN"] / count
        print(f"  {company}: {count:,} employees, avg {avg_revenue:,.0f} VND/employee")

    return company_sales


def branch_performance(don_hang, ma_nv):
    """Analyze performance by branch."""
    print("\n" + "=" * 80)
    print("BRANCH PERFORMANCE")
    print("=" * 80)

    emp_branch_map = ma_nv.set_index("MA_NV")["MA_CN"].to_dict()
    don_hang["branch"] = don_hang["MA_NV"].map(emp_branch_map)

    branch_sales = (
        don_hang.groupby("branch")
        .agg({"GIA_TIEN": "sum", "MA_HD": "count"})
        .rename(columns={"MA_HD": "num_contracts"})
    )
    branch_sales = branch_sales.sort_values("GIA_TIEN", ascending=False)

    print("\nTop 15 branches by revenue:")
    for branch, row in branch_sales.head(15).iterrows():
        print(f"  {branch}:")
        print(f"    Revenue: {row['GIA_TIEN']:,.0f} VND")
        print(f"    Contracts: {row['num_contracts']:,}")

    return branch_sales


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - EMPLOYEE & BRANCH ANALYSIS")
    print("=" * 80)

    nhan_vien, ma_nv, chi_nhanh, cong_ty, phong_ban, don_hang = load_employee_data()

    print(f"\nLoaded {len(nhan_vien)} employee records")
    print(f"Loaded {len(ma_nv)} employee mappings")
    print(f"Loaded {len(chi_nhanh)} branches")
    print(f"Loaded {len(phong_ban)} departments")

    employee_overview(nhan_vien)
    branch_analysis(chi_nhanh, cong_ty)
    department_analysis(phong_ban)
    employee_mapping_analysis(ma_nv)
    sales_performance_by_employee(don_hang, nhan_vien)
    company_comparison(don_hang, ma_nv)
    branch_performance(don_hang, ma_nv)

    print("\n" + "=" * 80)
    print("Employee and branch analysis complete!")
    print("=" * 80)
