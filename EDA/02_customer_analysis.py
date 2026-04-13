#!/usr/bin/env python3
"""
Customer Analysis - Insurance Dataset EDA
Detailed analysis of customer demographics and behavior
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")
OUTPUT_PATH = Path("/home/huynnz/GetAJob/DataExplorer/EDA/output")


def setup_output_dir():
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def load_customer_data():
    """Load customer and related reference data."""
    khach_hang = pd.read_csv(DATA_PATH / "Khách hàng.csv")
    nghe_nghiep = pd.read_csv(DATA_PATH / "Nghề nghiệp.csv")
    do_tuoi = pd.read_csv(DATA_PATH / "Độ tuổi.csv")
    xep_hang = pd.read_csv(DATA_PATH / "Xếp hạng khách hạng.csv")

    return khach_hang, nghe_nghiep, do_tuoi, xep_hang


def basic_customer_stats(df):
    """Calculate basic customer statistics."""
    print("\n" + "=" * 80)
    print("CUSTOMER BASIC STATISTICS")
    print("=" * 80)
    print(f"Total customers: {len(df):,}")
    print(f"\nUnique values:")
    print(f"  - Unique ages: {df['TUOI'].nunique()}")
    print(f"  - Unique occupations: {df['NGHENGHIEP'].nunique()}")
    print(f"  - Customer tiers: {df['XHKH'].nunique()}")

    print(f"\nAge Statistics:")
    print(f"  - Min age: {df['TUOI'].min()}")
    print(f"  - Max age: {df['TUOI'].max()}")
    print(f"  - Mean age: {df['TUOI'].mean():.1f}")
    print(f"  - Median age: {df['TUOI'].median():.1f}")
    print(f"  - Std dev: {df['TUOI'].std():.1f}")


def gender_distribution(df):
    """Analyze gender distribution."""
    print("\n" + "=" * 80)
    print("GENDER DISTRIBUTION")
    print("=" * 80)
    gender_counts = df["GIOI_TINH"].value_counts()
    gender_pct = df["GIOI_TINH"].value_counts(normalize=True) * 100

    print(f"Male: {gender_counts.get('Nam', 0):,} ({gender_pct.get('Nam', 0):.1f}%)")
    print(f"Female: {gender_counts.get('Nữ', 0):,} ({gender_pct.get('Nữ', 0):.1f}%)")

    return gender_counts


def age_distribution(df):
    """Analyze age distribution."""
    print("\n" + "=" * 80)
    print("AGE DISTRIBUTION")
    print("=" * 80)
    age_bins = [0, 18, 23, 30, 40, 50, 55, 100]
    age_labels = ["Under 18", "18-23", "23-30", "30-40", "40-50", "50-55", "55+"]

    df["age_group"] = pd.cut(df["TUOI"], bins=age_bins, labels=age_labels)
    age_dist = df["age_group"].value_counts().sort_index()

    print(age_dist)

    age_stats = df.groupby("age_group")["TUOI"].agg(["mean", "std", "count"])
    print(f"\nAge statistics by group:")
    print(age_stats)

    return age_dist


def occupation_analysis(df, nghe_nghiep_df):
    """Analyze customer occupation distribution."""
    print("\n" + "=" * 80)
    print("OCCUPATION ANALYSIS")
    print("=" * 80)
    occ_counts = df["NGHENGHIEP"].value_counts()

    print(f"\nTop 10 occupations by customer count:")
    for occ, count in occ_counts.head(10).items():
        pct = count / len(df) * 100
        print(f"  {occ}: {count:,} ({pct:.2f}%)")

    print(f"\nBottom 5 occupations:")
    for occ, count in occ_counts.tail(5).items():
        pct = count / len(df) * 100
        print(f"  {occ}: {count:,} ({pct:.2f}%)")

    occupation_by_gender = pd.crosstab(df["NGHENGHIEP"], df["GIOI_TINH"])
    print(f"\nOccupation distribution by gender (top 10):")
    print(occupation_by_gender.loc[occ_counts.head(10).index])

    return occ_counts


def customer_tier_analysis(df):
    """Analyze customer tier distribution."""
    print("\n" + "=" * 80)
    print("CUSTOMER TIER ANALYSIS")
    print("=" * 80)
    tier_counts = df["XHKH"].value_counts()
    tier_order = ["Đồng", "Bạc", "Vàng", "Bạch kim", "Kim cương"]

    print("Customer distribution by tier:")
    for tier in tier_order:
        if tier in tier_counts:
            count = tier_counts[tier]
            pct = count / len(df) * 100
            print(f"  {tier}: {count:,} ({pct:.2f}%)")

    tier_by_gender = pd.crosstab(df["XHKH"], df["GIOI_TINH"], normalize="index") * 100
    print(f"\nGender distribution within each tier:")
    print(tier_by_gender)

    avg_age_by_tier = df.groupby("XHKH")["TUOI"].agg(["mean", "median", "std"])
    print(f"\nAverage age by tier:")
    print(avg_age_by_tier)

    return tier_counts


def age_tier_relationship(df):
    """Analyze relationship between age and customer tier."""
    print("\n" + "=" * 80)
    print("AGE-TIER RELATIONSHIP")
    print("=" * 80)
    age_bins = [0, 18, 23, 30, 40, 50, 55, 100]
    age_labels = ["Under 18", "18-23", "23-30", "30-40", "40-50", "50-55", "55+"]
    df["age_group"] = pd.cut(df["TUOI"], bins=age_bins, labels=age_labels)

    tier_order = ["Đồng", "Bạc", "Vàng", "Bạch kim", "Kim cương"]

    cross_tab = pd.crosstab(df["age_group"], df["XHKH"], normalize="index") * 100

    print("\nTier distribution within each age group (%):")
    for tier in tier_order:
        if tier in cross_tab.columns:
            print(f"\n{tier}:")
            print(cross_tab[tier])

    return cross_tab


def demographic_summary(df):
    """Create comprehensive demographic summary."""
    print("\n" + "=" * 80)
    print("DEMOGRAPHIC SUMMARY")
    print("=" * 80)

    summary_stats = {
        "Total Customers": len(df),
        "Male Customers": (df["GIOI_TINH"] == "Nam").sum(),
        "Female Customers": (df["GIOI_TINH"] == "Nữ").sum(),
        "Average Age": df["TUOI"].mean(),
        "Median Age": df["TUOI"].median(),
        "Age Std Dev": df["TUOI"].std(),
        "Most Common Occupation": df["NGHENGHIEP"].mode()[0],
        "Most Common Tier": df["XHKH"].mode()[0],
    }

    for key, value in summary_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        elif isinstance(value, (int, float)):
            print(f"  {key}: {value:,}")
        else:
            print(f"  {key}: {value}")

    return summary_stats


def create_customer_profile_segments(df):
    """Create customer profile segments."""
    print("\n" + "=" * 80)
    print("CUSTOMER SEGMENTATION")
    print("=" * 80)

    age_bins = [0, 25, 35, 45, 55, 100]
    age_labels = [
        "Young (18-25)",
        "Young Adult (26-35)",
        "Middle Age (36-45)",
        "Senior (46-55)",
        "Elderly (55+)",
    ]
    df["age_segment"] = pd.cut(df["TUOI"], bins=age_bins, labels=age_labels)

    high_tier = ["Vàng", "Bạch kim", "Kim cương"]
    df["tier_level"] = df["XHKH"].apply(lambda x: "High" if x in high_tier else "Low")

    segment_cross = pd.crosstab(df["age_segment"], df["tier_level"], margins=True)
    print("\nCustomer segments (Age vs Tier Level):")
    print(segment_cross)

    return segment_cross


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - CUSTOMER ANALYSIS")
    print("=" * 80)

    setup_output_dir()

    khach_hang, nghe_nghiep, do_tuoi, xep_hang = load_customer_data()

    print(f"\nLoaded {len(khach_hang):,} customer records")
    print(f"Loaded {len(nghe_nghiep)} occupation types")
    print(f"Loaded {len(do_tuoi)} age mapping records")
    print(f"Loaded {len(xep_hang)} customer tier definitions")

    basic_customer_stats(khach_hang)
    gender_distribution(khach_hang)
    age_distribution(khach_hang)
    occupation_analysis(khach_hang, nghe_nghiep)
    customer_tier_analysis(khach_hang)
    age_tier_relationship(khach_hang)
    demographic_summary(khach_hang)
    create_customer_profile_segments(khach_hang)

    print("\n" + "=" * 80)
    print("Customer analysis complete!")
    print("=" * 80)
