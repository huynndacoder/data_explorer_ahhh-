# Insurance Data Explorer - Complete EDA Report

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Overview](#data-overview)
3. [Customer Analysis](#customer-analysis)
4. [Contract & Order Analysis](#contract--order-analysis)
5. [Vehicle Analysis](#vehicle-analysis)
6. [Employee & Branch Analysis](#employee--branch-analysis)
7. [Product & Channel Analysis](#product--channel-analysis)
8. [RFM & Cohort Analysis](#rfm--cohort-analysis)
9. [Output Files](#output-files)

---

## Executive Summary

### Business Overview

| Metric | Value |
|--------|-------|
| Companies | 2 (TQP, MGV) |
| Branches | 22 locations |
| Departments | 68 |
| Employees | 602 |
| Customers | 400,001 |
| Contracts | 150,494 |
| Orders | 189,778 |

### Revenue Metrics

| Metric | Value |
|--------|-------|
| Total Contract Value | 129.42 trillion VND |
| Total Insurance Fee | 1,456.58 billion VND |
| Average Contract Value | 681,976,861 VND |
| Median Contract Value | 140,000,000 VND |

### Customer Profile

| Metric | Value |
|--------|-------|
| Male | 229,735 (57.4%) |
| Female | 170,266 (42.6%) |
| Average Age | 41.5 years |

**Customer Tier Distribution:**
| Tier | Count | Percentage |
|------|-------|------------|
| Đồng (Bronze) | 75,385 | 18.8% |
| Bạc (Silver) | 108,729 | 27.2% |
| Vàng (Gold) | 105,000 | 26.2% |
| Bạch kim (Platinum) | 61,954 | 15.5% |
| Kim cương (Diamond) | 48,933 | 12.2% |

### Top 5 Products by Revenue

1. GSP01 (Bảo hiểm Bắt buộc Trách nhiệm dân sự xe ô tô): 55.98 trillion VND
2. GSP02 (Bảo hiểm Vật chất xe): 34.86 trillion VND
3. GSP05 (Bảo hiểm Bắt buộc Trách nhiệm dân sự xe mô tô): 17.31 trillion VND
4. GSP04 (Bảo hiểm TNDS của chủ xe đối với hàng hóa): 5.51 trillion VND
5. BHCN.1 (Cơ bản): 4.76 trillion VND

### Key Insights

1. **Customer Segmentation**: 54% are high-tier customers (Vàng, Bạch kim, Kim cương)
2. **Sales Channels**: Direct channel (DC) contributes 55.9% of revenue
3. **Employee Productivity**: Top 10% employees contribute 61.7% of revenue
4. **Vehicle Insurance**: 64,486 contracts across 51 vehicle brands

---

## Data Overview

### Data Files Summary

| File | Records | Columns | Memory |
|------|---------|---------|--------|
| Khách hàng.csv | 400,001 | 5 | 118.86 MB |
| Đơn hàng.csv | 189,778 | 15 | 125.56 MB |
| Hợp đồng.csv | 150,494 | 3 | 25.08 MB |
| Thông tin xe.csv | 64,486 | 4 | 14.64 MB |
| KPI.csv | 8,704 | 6 | 1.58 MB |
| Mã nhân viên.csv | 1,122 | 5 | 0.30 MB |
| Nhân viên.csv | 602 | 4 | 0.10 MB |

### Dimension Tables

- **Insurance Types (Bảo Hiểm)**: 2 types (Con người, Xe cơ giới)
- **Product Groups (Nhóm sản phẩm)**: 9 groups
- **Product Packages (Gói Sản Phẩm)**: 21 packages
- **Vehicle Brands (Hãng Xe)**: 51 brands
- **Sales Channels (Kênh Bán)**: 7 types, 97 detailed channels
- **Branches (Chi nhánh)**: 22 offices

### Data Quality

- **Missing Values**: 4 in Nhân viên table
- **Duplicate Rows**: 682 in KPI table
- **Referential Integrity**: All foreign keys valid

---

## Customer Analysis

### Basic Statistics

- Total customers: 400,001
- Unique ages: 53 (range: 21-74)
- Average age: 41.5 years
- Unique occupations: 33

### Age Distribution

| Age Group | Count | Percentage |
|-----------|-------|------------|
| 18-23 | 482 | 0.1% |
| 23-30 | 77,186 | 19.3% |
| 30-40 | 111,144 | 27.8% |
| 40-50 | 110,643 | 27.7% |
| 50-55 | 55,714 | 13.9% |
| 55+ | 44,832 | 11.2% |

### Top 10 Occupations

| Occupation | Count | Percentage |
|------------|-------|------------|
| Khác | 52,320 | 13.1% |
| Nhân viên văn phòng | 28,354 | 7.1% |
| Giáo viên | 28,260 | 7.1% |
| Kỹ sư | 22,298 |5.6% |
| Quản lý sản xuất | 22,289 | 5.6% |
| Cửa hàng bán lẻ | 22,255 | 5.6% |
| CEO | 22,232 | 5.6% |
| Bác sĩ | 22,226 | 5.6% |
| Kinh doanh tự do | 22,122 | 5.5% |
| Công nhân | 22,104 | 5.5% |

---

## Contract & Order Analysis

### Contract Overview

- Total contracts: 150,494
- Unique customers: 130,099
- Unique products: 21

**Contracts per customer:**
- 1 contract: 111,851 customers (86.0%)
- 2 contracts: 16,308 customers (12.5%)
- 3+ contracts: 1,940 customers (1.5%)

### Order Analysis

- Total orders: 189,778
- Date range: 2023-01-01 to 2025-07-01
- Contract types: Mới (79.3%), Tái tục (20.7%)

### Revenue by Company

| Company | Revenue | Avg per Contract | Contracts |
|---------|---------|------------------|-----------|
| MGV | 63.42 trillion VND | 671.3M VND | 94,478 |
| TQP | 66.00 trillion VND | 692.6M VND | 95,300 |

### Top Sales Channels

| Channel | Revenue | Percentage |
|---------|---------|------------|
| DC (Direct) | 72.34 trillion VND | 55.9% |
| AC (Agency) | 23.85 trillion VND | 18.4% |
| BC (Broker) | 11.36 trillion VND | 8.8% |
| POS (Garage) | 8.22 trillion VND | 6.3% |
| EC (E-commerce) | 5.51 trillion VND | 4.3% |

---

## Vehicle Analysis

### Vehicle Model Overview

- Total models: 263
- Unique brands: 51
- Price range: 15.3M - 7B VND
- Manufacturing years: 2005-2025

### Top Vehicle Brands

| Brand | Models | Avg Price |
|-------|--------|-----------|
| VinFast | 17 | 597.4M VND |
| Honda | 16 | 361.4M VND |
| GasGas | 11 | 54.5M VND |
| Suzuki | 11 | 142.1M VND |
| Benelli | 10 | 53.7M VND |

### Insured Vehicles

- Total insured: 64,486
- Unique contracts: 64,486
- Top type: XCG2B.2 (50+ CC) - 12,487 (19.4%)

---

## Employee & Branch Analysis

### Employee Overview

- Total employees: 602
- Age range: 22-50 years
- Average age: 33.8 years

### Top 5 Employees by Revenue

| Employee ID | Revenue | Contracts |
|-------------|---------|-----------|
| TQP-TCT-XCG001 | 31.08 trillion VND | 21,452 |
| MGV-TCT-XCG001 | 30.00 trillion VND | 20,621 |
| TQP-BD-XCG087 | 267.4 billion VND | 127 |
| TQP-BD-XCG047 | 236.7 billion VND | 132 |
| TQP-QN-XCG228 | 229.0 billion VND | 132 |

### Company Comparison

| Metric | MGV | TQP |
|--------|-----|-----|
| Revenue | 63.59 trillion VND | 65.83 trillion VND |
| Employees | 512 | 510 |
| Avg/Employee | 124.2B VND | 129.1B VND |

---

## Product & Channel Analysis

### Product Groups

| Group | Type | Description |
|-------|------|-------------|
| XCG_BB | Vehicle | Mandatory insurance |
| XCG_TN | Vehicle | Voluntary insurance |
| BHAT | Personal | Health wellness package |
| BHSK | Personal | Comprehensive health |
| BHTN | Personal | Accident insurance |
| BHTNĐ | Personal | Household accident |
| BHHS | Personal | Student insurance |
| BHCN | Personal | High liability |
| BHBT | Personal | Worker compensation |

### ChannelType Breakdown

| Type | Revenue | Contracts |
|------|---------|-----------|
| DC (Direct) | 72.34T VND (55.9%) | 82,188 |
| AC (Agency) | 23.85T VND (18.4%) | 48,452 |
| BC (Broker) | 11.36T VND (8.8%) | 11,398 |
| POS (Garage) | 8.22T VND (6.3%) | 19,289 |
| EC (E-commerce) | 5.51T VND (4.3%) | 12,904 |
| BA (Bank) | 5.27T VND (4.1%) | 12,578 |
| B2B (Business) | 2.89T VND (2.2%) | 2,969 |

### Contract Duration

| Duration | Contracts | Percentage |
|----------|-----------|------------|
| 12 months | 70,041 | 36.9% |
| 24 months | 61,781 | 32.6% |
| 36 months | 57,956 | 30.5% |

---

## RFM & Cohort Analysis

### RFM Segments Summary

| Segment | Customers | %Customers | Revenue | %Revenue |
|---------|-----------|------------|---------|----------|
| Champions | 13,809 | 10.6% | 216.5T VND | 28.1% |
| Big Spenders (New) | 9,767 | 7.5% | 187.0T VND | 24.3% |
| Others | 39,071 | 30.0% | 184.2T VND | 23.9% |
| Potential Loyalists | 10,689 | 8.2% | 73.6T VND | 9.6% |
| At Risk | 5,808 | 4.5% | 39.4T VND | 5.1% |
| Need Attention | 11,766 | 9.0% | 30.3T VND | 3.9% |
| Loyal Customers | 11,568 | 8.9% | 25.6T VND | 3.3% |
| Lost | 12,901 | 9.9% | 6.4T VND | 0.8% |
| New Customers | 8,977 | 6.9% | 4.4T VND | 0.6% |
| About to Sleep | 5,743 | 4.4% | 2.8T VND | 0.4% |

### VIP Customers (Top20)

| Customer | RFM Score | Segment | VIP Tier | Monetary |
|----------|-----------|---------|----------|----------|
| KH029569 | 455 | Champions | Platinum | 315.0M |
| KH032151 | 555 | Champions | Platinum | 315.0M |
| KH036010 | 455 | Champions | Platinum | 294.0M |
| KH028535 | 455 | Champions | Platinum | 294.0M |
| KH026156 | 555 | Champions | Platinum | 247.8M |

### Cohort Retention Matrix

**Key Insights:**
- Avg Month-2 Retention: 1.8%
- Avg Month-2 Renewal Rate: 0.6%
- Avg Month-12 (1 Year) Renewal Rate: 9.6%

**Note:** Low monthly retention is expected for insurance products (annual renewal cycle).

### Pareto Analysis (80/20 Rule)

- Total customers: 130,099
- Total revenue: 770.2 billion VND
- **80% of revenue from 29,759 customers (22.9%)**

### Volume vsMargin Correlation

- Correlation coefficient: 0.465
- Higher tier customers have larger average volume

---

## Output Files

| File | Description |
|------|-------------|
| `rfm_segments.csv` | Customer RFM scores and segments |
| `vip_customers.csv` | Top 100 VIP customers |
| `cohort_retention_matrix.csv` | Monthly retention rates |
| `renewal_rate_matrix.csv` | Monthly renewal rates |
| `pareto_analysis.csv` | Top 20 revenue customers |
| `volume_margin_scatter.csv` | Volume/margin by customer |
| `feature_table.csv` | 30 features per customer |
| `rfm_cohort_analysis.png` | Visualization dashboard |

### Location

All outputs saved to: `/DataExplorer/EDA/output/`

---

## Running the Analysis

```bash
# Activate virtual environment
cd /DataExplorer
source .venv/bin/activate

# Run all EDA scripts
python EDA/run_all_eda.py

# Or run individual scripts
python EDA/00_comprehensive_summary.py
python EDA/01_data_overview.py
python EDA/02_customer_analysis.py
python EDA/03_contract_order_analysis.py
python EDA/04_vehicle_analysis.py
python EDA/05_employee_branch_analysis.py
python EDA/06_product_channel_analysis.py
python EDA/07_rfm_cohort_analysis.py
```

---
