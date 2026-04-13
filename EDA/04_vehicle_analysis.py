#!/usr/bin/env python3
"""
Vehicle Analysis - Insurance Dataset EDA
Detailed analysis of vehicle data and insurance patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/CSVData")


def load_vehicle_data():
    """Load vehicle-related data."""
    xe_co_gioi = pd.read_csv(DATA_PATH / "Xe cơ giới.csv")
    thong_tin_xe = pd.read_csv(DATA_PATH / "Thông tin xe cơ giới.csv")
    loai_xe = pd.read_csv(DATA_PATH / "Loại xe cơ giới.csv")
    hang_xe = pd.read_csv(DATA_PATH / "Hãng Xe.csv")
    hop_dong = pd.read_csv(DATA_PATH / "Hợp đồng.csv")

    return xe_co_gioi, thong_tin_xe, loai_xe, hang_xe, hop_dong


def vehicle_overview(xe_co_gioi):
    """Basic vehicle model statistics."""
    print("\n" + "=" * 80)
    print("VEHICLE MODEL OVERVIEW")
    print("=" * 80)
    print(f"Total vehicle models: {len(xe_co_gioi):,}")
    print(f"Unique brands: {xe_co_gioi['MA_HANG_XE'].nunique()}")
    print(f"Unique vehicle types: {xe_co_gioi['SO_CHO_NGOI'].nunique()}")

    print(f"\nPrice statistics:")
    print(f"  - Min: {xe_co_gioi['GIA_TIEN'].min():,.0f} VND")
    print(f"  - Max: {xe_co_gioi['GIA_TIEN'].max():,.0f} VND")
    print(f"  - Mean: {xe_co_gioi['GIA_TIEN'].mean():,.0f} VND")
    print(f"  - Median: {xe_co_gioi['GIA_TIEN'].median():,.0f} VND")

    print(f"\nManufacturing year range:")
    print(f"  - Oldest: {xe_co_gioi['NAM_SX'].min()}")
    print(f"  - Newest: {xe_co_gioi['NAM_SX'].max()}")

    return xe_co_gioi.describe()


def brand_analysis(xe_co_gioi, hang_xe):
    """Analyze vehicles by brand."""
    print("\n" + "=" * 80)
    print("VEHICLE BRAND ANALYSIS")
    print("=" * 80)

    brand_counts = xe_co_gioi["MA_HANG_XE"].value_counts()
    brand_avg_price = xe_co_gioi.groupby("MA_HANG_XE")["GIA_TIEN"].mean()

    print("\nTop 15 brands by number of models:")
    for brand_id, count in brand_counts.head(15).items():
        brand_name = hang_xe[hang_xe["MA_HANG_XE"] == brand_id]["TEN_HANG_XE"].values
        name = brand_name[0] if len(brand_name) > 0 else "Unknown"
        avg_price = brand_avg_price.get(brand_id, 0)
        print(f"  {brand_id} ({name}): {count} models, avg price {avg_price:,.0f} VND")

    brand_revenue = xe_co_gioi.groupby("MA_HANG_XE").agg(
        {"GIA_TIEN": ["mean", "min", "max"]}
    )

    print("\nTop 10 most expensive brands (by avg price):")
    top_expensive = brand_avg_price.sort_values(ascending=False).head(10)
    for brand_id, price in top_expensive.items():
        brand_name = hang_xe[hang_xe["MA_HANG_XE"] == brand_id]["TEN_HANG_XE"].values
        name = brand_name[0] if len(brand_name) > 0 else "Unknown"
        print(f"  {brand_id} ({name}): {price:,.0f} VND avg")

    return brand_counts


def vehicle_type_analysis(xe_co_gioi, loai_xe):
    """Analyze vehicles by type."""
    print("\n" + "=" * 80)
    print("VEHICLE TYPE ANALYSIS")
    print("=" * 80)

    print(f"\nSeat capacity distribution:")
    seat_dist = xe_co_gioi["SO_CHO_NGOI"].value_counts().sort_index()
    for seats, count in seat_dist.items():
        pct = count / len(xe_co_gioi) * 100
        print(f"  {seats} seats: {count} models ({pct:.1f}%)")

    print(f"\nLoad capacity distribution:")
    load_dist = (
        xe_co_gioi[xe_co_gioi["TRONG_TAI_XE"] > 0]["TRONG_TAI_XE"]
        .value_counts()
        .sort_index()
    )
    print(f"  Vehicles with load capacity: {len(load_dist)} types")
    for load, count in load_dist.items():
        print(f"  {load:,.0f} kg: {count} models")

    xe_co_gioi["vehicle_category"] = xe_co_gioi["SO_CHO_NGOI"].apply(
        lambda x: "2-wheel" if x == 2 else ("4-wheel" if x >= 4 else "Other")
    )

    category_stats = xe_co_gioi.groupby("vehicle_category").agg(
        {"GIA_TIEN": ["count", "mean", "min", "max"]}
    )

    print(f"\nVehicle category statistics:")
    print(category_stats)

    return seat_dist


def year_analysis(xe_co_gioi):
    """Analyze vehicle manufacturing years."""
    print("\n" + "=" * 80)
    print("MANUFACTURING YEAR ANALYSIS")
    print("=" * 80)

    year_counts = xe_co_gioi["NAM_SX"].value_counts().sort_index()

    print("\nVehicles by manufacturing year:")
    for year, count in year_counts.items():
        print(f"  {year}: {count} models")

    price_by_year = xe_co_gioi.groupby("NAM_SX")["GIA_TIEN"].agg(["mean", "min", "max"])

    print("\nPrice trends by year:")
    print(price_by_year)

    brand_diversity_per_year = xe_co_gioi.groupby("NAM_SX")["MA_HANG_XE"].nunique()

    print("\nBrand diversity per year:")
    print(brand_diversity_per_year)

    return year_counts


def vehicle_insurance_analysis(thong_tin_xe, loai_xe):
    """Analyze vehicle insurance patterns."""
    print("\n" + "=" * 80)
    print("VEHICLE INSURANCE ANALYSIS")
    print("=" * 80)

    print(f"Total insured vehicles: {len(thong_tin_xe):,}")

    vehicle_type_counts = thong_tin_xe["MA_LOAIXE"].value_counts()

    print("\nInsured vehicles by type (top 10):")
    for vtx, count in vehicle_type_counts.head(10).items():
        type_name = loai_xe[loai_xe["MA_LOAI_XE"] == vtx]["TEN_LOAI_XE"].values
        name = type_name[0] if len(type_name) > 0 else "Unknown"
        pct = count / len(thong_tin_xe) * 100
        print(f"  {vtx} ({name}): {count:,} ({pct:.2f}%)")

    print(f"\nUnique vehicle models insured: {thong_tin_xe['MA_DONG_XE'].nunique()}")
    print(f"Unique contracts: {thong_tin_xe['MA_HD'].nunique()}")

    contracts_per_vehicle_model = thong_tin_xe.groupby("MA_DONG_XE").size()

    print("\nTop 10 most insured vehicle models:")
    for model_id, count in (
        contracts_per_vehicle_model.sort_values(ascending=False).head(10).items()
    ):
        print(f"  {model_id}: {count:,} contracts")

    return vehicle_type_counts


def model_price_analysis(xe_co_gioi):
    """Analyze price distribution by model."""
    print("\n" + "=" * 80)
    print("MODEL PRICE ANALYSIS")
    print("=" * 80)

    price_bins = [
        0,
        50000000,
        100000000,
        500000000,
        1000000000,
        5000000000,
        float("inf"),
    ]
    price_labels = ["<50M", "50M-100M", "100M-500M", "500M-1B", "1B-5B", ">5B"]

    xe_co_gioi["price_range"] = pd.cut(
        xe_co_gioi["GIA_TIEN"], bins=price_bins, labels=price_labels
    )

    price_dist = xe_co_gioi["price_range"].value_counts()

    print("\nPrice range distribution:")
    for price_range, count in price_dist.items():
        pct = count / len(xe_co_gioi) * 100
        print(f"  {price_range}: {count} models ({pct:.1f}%)")

    luxury_models = xe_co_gioi[xe_co_gioi["GIA_TIEN"] >= 1000000000].sort_values(
        "GIA_TIEN", ascending=False
    )

    print(f"\nLuxury vehicles (>= 1 billion VND): {len(luxury_models)}")
    print("Top 10 most expensive models:")
    for _, row in luxury_models.head(10).iterrows():
        print(
            f"  {row['MA_DONG_XE']}: {row['GIA_TIEN']:,.0f} VND ({row['MA_HANG_XE']})"
        )

    economy_models = xe_co_gioi[xe_co_gioi["GIA_TIEN"] < 50000000].sort_values(
        "GIA_TIEN"
    )

    print(f"\nEconomy vehicles (<50M VND): {len(economy_models)}")
    print("Top 10 cheapest models:")
    for _, row in economy_models.head(10).iterrows():
        print(
            f"  {row['MA_DONG_XE']}: {row['GIA_TIEN']:,.0f} VND ({row['MA_HANG_XE']})"
        )

    return price_dist


def dong_xe_analysis(xe_co_gioi):
    """Analyze vehicle model names."""
    print("\n" + "=" * 80)
    print("VEHICLE MODEL (DONG XE) ANALYSIS")
    print("=" * 80)

    model_counts = xe_co_gioi["TEN_DONG_XE"].value_counts()

    print("\nMost common vehicle model names:")
    for model_name, count in model_counts.head(15).items():
        print(f"  {model_name}: {count}")

    print(f"\nUnique model names: {xe_co_gioi['TEN_DONG_XE'].nunique()}")
    print(f"Total models: {len(xe_co_gioi)}")

    return model_counts


if __name__ == "__main__":
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - VEHICLE ANALYSIS")
    print("=" * 80)

    xe_co_gioi, thong_tin_xe, loai_xe, hang_xe, hop_dong = load_vehicle_data()

    print(f"\nLoaded {len(xe_co_gioi)} vehicle model records")
    print(f"Loaded {len(thong_tin_xe)} insured vehicle records")
    print(f"Loaded {len(loai_xe)} vehicle type definitions")
    print(f"Loaded {len(hang_xe)} vehicle brands")

    vehicle_overview(xe_co_gioi)
    brand_analysis(xe_co_gioi, hang_xe)
    vehicle_type_analysis(xe_co_gioi, loai_xe)
    year_analysis(xe_co_gioi)
    vehicle_insurance_analysis(thong_tin_xe, loai_xe)
    model_price_analysis(xe_co_gioi)
    dong_xe_analysis(xe_co_gioi)

    print("\n" + "=" * 80)
    print("Vehicle analysis complete!")
    print("=" * 80)
