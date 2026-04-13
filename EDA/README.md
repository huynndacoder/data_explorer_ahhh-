# Insurance Data Explorer - EDA Documentation

## Dataset Overview

This dataset contains insurance company data in Vietnamese, including customer information, contracts, orders, employees, branches, vehicles, and sales channels.

### Data Files Summary

| File | Records | Description |
|------|---------|-------------|
| Khách hàng.csv | ~400,000 | Customer demographics (age, gender, occupation, tier) |
| Hợp đồng.csv | ~150,000 | Contract information (customer, product) |
| Đơn hàng.csv | ~189,779 | Order details (dates, prices, channels) |
| Thông tin xe cơ giới.csv | ~64,487 | Vehicle insurance details |
| KPI.csv | ~8,705 | KPI metrics by product/channel |
| Nhân viên.csv | 600 | Employee names, ages, phone numbers |
| Mã nhân viên.csv | 1,122 | Employee mappings to branches/departments |
| Xe cơ giới.csv | 263 | Vehicle model definitions |
| Gói Sản Phẩm.csv | 21 | Insurance product packages |
| Kênh bán chi tiết.csv | 97 | Detailed sales channels |
| Phòng ban.csv | 68 | Department definitions |
| Chi nhánh.csv | 22 | Branch offices |
| Others | - | Reference tables (ages, occupations, etc.) |

### Dimension Tables

- **Companies (Công ty)**: 2 insurance companies (TQP, MGV)
- **Insurance Types (Bảo Hiểm)**: 2 types (Personal/Con người, Vehicle/Xe cơ giới)
- **Product Groups (Nhóm sản phẩm)**: 9 groups
- **Product Packages (Gói Sản Phẩm)**: 21 packages
- **Vehicle Brands (Hãng Xe)**: 51 brands
- **Vehicle Types (Loại xe cơ giới)**: 36 types
- **Sales Channels (Kênh Bán)**: 7 main channel types
- **Detailed Channels (Kênh bán chi tiết)**: 97 specific channels
- **Branches (Chi nhánh)**: 22 branch offices
- **Departments (Phòng ban)**: 68 departments
- **Occupations (Nghề nghiệp)**: 32 occupation types
- **Customer Tiers (Xếp hạng khách hàng)**: 5 tiers (Đồng, Bạc, Vàng, Bạch kim, Kim cương)

### Fact Tables

1. **Khách hàng (Customers)**: Customer demographics and tier information
2. **Hợp đồng (Contracts)**: Links customers to product packages
3. **Đơn hàng (Orders)**: Detailed transaction information including dates, prices, employees, channels
4. **Thông tin xe cơ giới (Vehicle Info)**: Vehicle insurance contract details
5. **KPI**: Monthly KPI metrics by product and channel

## EDA Scripts

### 01_data_overview.py
- Overview of all data tables
- Basic statistics (rows, columns, memory usage)
- Dimension table analysis
- Hierarchical relationship analysis

### 02_customer_analysis.py
- Customer demographics analysis
- Age distribution
- Gender distribution
- Occupation analysis
- Customer tier analysis
- Age-tier relationship

### 03_contract_order_analysis.py
- Contract overview and statistics
- Product distribution analysis
- Order patterns and dates
- Revenue analysis by company
- Sales channel performance
- Employee sales performance
- Time series analysis
- KPI analysis

### 04_vehicle_analysis.py
- Vehicle model overview
- Brand analysis
- Vehicle type analysis
- Manufacturing year trends
- Price distribution analysis
- Vehicle insurance patterns

### 05_employee_branch_analysis.py
- Employee demographics
- Branch distribution
- Department structure
- Employee mappings
- Sales performance by employee
- Company comparison
- Branch performance comparison

### 06_product_channel_analysis.py
- Product package analysis
- Product group hierarchy
- Sales channel overview
- Channel performance analysis
- KPI by product and channel
- Product-channel combinations
- Contract duration patterns

### 07_rfm_cohort_analysis.py
- RFM (Recency, Frequency, Monetary) customer segmentation
- Cohort retention matrix analysis
- Renewal rate matrix (Tái tục tracking)
- Pareto 80/20 analysis
- Volume vs Margin scatter analysis
- VIP customer identification
- Feature table generation for ML

## RFM Segmentation Methodology

### Segment Definitions

| Segment | R Score | F Score | M Score | Description |
|---------|---------|---------|---------|-------------|
| Champions | 4-5 | 4-5 | 4-5 | Best customers - bought recently, buy often, spend most |
| Loyal Customers | 4-5 | 3+ | 3+ | Good customers - consistent purchasers |
| Potential Loyalists | 3+ | 3+ | 3+ | Recent customers with good frequency |
| Big Spenders (New) | 3+ | 1-2 | 4+ | New customers with high spending |
| New Customers | 4-5 | 1-2 | 1-2 | Recent first-time buyers |
| At Risk | 1-2 | 4+ | 4+ | Good customers who haven't bought recently |
| Need Attention | 1-2 | 3+ | 3+ | Valuable customers who may churn |
| About to Sleep | 3 | 1-2 | 1-2 | Below average recency, frequency, monetary |
| Lost | 1-2 | 1-2 | 1-2 | Lowest engagement customers |

### VIP Tiers

| Tier | RFM Total Score | Description |
|------|-----------------|-------------|
| Platinum | 14-15 | Top tier VIP customers |
| Gold | 11-13 | High-value customers |
| Silver | 8-10 | Medium-value customers |
| Bronze | 1-7 | Entry-level customers |

### Cohort Analysis Notes

- **Retention Matrix**: Tracks customers who made ANY purchase in subsequent months
- **Renewal Matrix**: Tracks only customers who RENEWED contracts (Tái tục)
- **Data Caveat**: ~14% of Month-1 customers show renewal activity, indicating historical data migration where some customers' first recorded order was a renewal

### Output Files

| File | Description |
|------|-------------|
| `rfm_segments.csv` | Customer RFM scores and segment assignments |
| `vip_customers.csv` | Top 100 VIP customers with tier assignments |
| `cohort_retention_matrix.csv` | Monthly cohort retention rates |
| `renewal_rate_matrix.csv` | Monthly cohort renewal rates |
| `pareto_analysis.csv` | Top customers by revenue contribution |
| `volume_margin_scatter.csv` | Customer volume vs margin data |
| `feature_table.csv` | 30 features per customer for ML |
| `rfm_cohort_analysis.png` | Visualization dashboard |

## Key Insights from Data Structure

### Business Model
- Two insurance companies operate across Vietnam
- Products include both personal insurance (Con người) and vehicle insurance (Xe cơ giới)
- Products are mandatory (bắt buộc) and voluntary (tự nguyện)

### Sales Channels
- **DC**: Direct channel (Văn phòng giao dịch, Website, App, Hotline)
- **AC**: Agency channel (Individual and organizational agents)
- **BC**: Insurance broker channel
- **BA**: Bank channel (Bancassurance)
- **POS**: Garage/Salon channel
- **EC**: E-commerce channel
- **B2B**: Business-to-business channel

### Customer Segmentation
- Tiers based on total insurance value:
  - Đồng (Bronze): < 10 million VND
  - Bạc (Silver): 10-30 million VND
  - Vàng (Gold): 30-100 million VND
  - Bạch kim (Platinum): 100 million - 1 billion VND
  - Kim cương (Diamond): > 1 billion VND

### Organizational Structure
- Each company has headquarters (Hội sở/TCT) and regional branches
- Branches cover major cities: Hà Nội, TP.HCM, Đà Nẵng, Hải Phòng, Cần Thơ, etc.
- Departments are organized by business line (XCG - Vehicle, CN - Personal)

## Running the EDA

```bash
# Install required packages
pip install pandas numpy matplotlib seaborn

# Run all EDA scripts
cd /DataExplorer/EDA
python run_all_eda.py

# Or run individual scripts
python 01_data_overview.py
python 02_customer_analysis.py
python 03_contract_order_analysis.py
python 04_vehicle_analysis.py
python 05_employee_branch_analysis.py
python 06_product_channel_analysis.py
```

## Data Relationships

```
Công ty (Company)1--* Chi nhánh (Branch)
Chi nhánh1--* Phòng ban (Department)
Phòng ban1--* Mã nhân viên (Employee)
Mã nhân viên1--* Đơn hàng (Orders)

Khách hàng (Customer)1--* Hợp đồng (Contract)
Hợp đồng1--* Thông tin xe (Vehicle Info)
Hợp đồng1--* Đơn hàng (Order)

Gói Sản Phẩm (Product) *--1 Nhóm sản phẩm (Product Group)
Nhóm sản phẩm *--1 Bảo Hiểm (Insurance Type)

Kênh bán chi tiết (Channel Detail) *--1 Kênh Bán (Channel Type)
```
