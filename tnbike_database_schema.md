**THỐNG NHẤT BIKE · DATA EXPLORER 2026**

**Tài liệu Database**

_Schema · Từ điển dữ liệu · ERD · Hướng dẫn import_

Database: tnbike_db · Schema: tnbike · PostgreSQL 14+

Dữ liệu: Q1/2025 → T2/2026 · 17.031 dòng giao dịch · 702 đại lý · 247 SKU

_Phiên bản 1.0 · Tháng 1/2026_

# **1\. Tổng quan database**

Database tnbike_db được thiết kế để lưu trữ và phân tích dữ liệu bán hàng của Thống Nhất Bike theo mô hình star schema gọn nhẹ - phù hợp cho cả OLTP (ghi nhận giao dịch từ Sales Order Agent) lẫn OLAP (analytics dashboard, ML forecasting).

Dữ liệu gốc: file Tnbike_Bán_hàng_Q1_2025_Q1_2026_Enriched.xlsx đã được làm giàu (ẩn danh hóa địa chỉ, bổ sung Mã KH / Tên KH / MST / Số chứng từ / Ký hiệu HĐ). Import phạm vi 2025-01-01 → 2026-02-28.

## **1.1 Danh sách bảng và views**

| **Tên**             | **Loại**    | **Số dòng import** | **Mô tả ngắn**                                        |
| ------------------- | ----------- | ------------------ | ----------------------------------------------------- |
| product_group       | Dimension   | 5                  | Nhóm SP cấp 1: CITYBIKE_P, KIDBIKE_1/2, SPORTBIKE_S/A |
| product_line        | Dimension   | 77                 | Dòng xe cấp 3: GN 06-27, New 26, MTB 20-04...         |
| product             | Dimension   | 247                | SKU: mã hàng + tên đầy đủ + màu sắc                   |
| product_price       | History     | 1.016              | Lịch sử giá list theo thời kỳ                         |
| province            | Dimension   | 75                 | Tỉnh/thành phố + vùng địa lý                          |
| customer            | Dimension   | 702                | Đại lý: mã, tên, MST, địa chỉ, tỉnh                   |
| sales_order         | Fact/Header | 1.627              | Đầu phiếu chứng từ bán hàng                           |
| order_line          | Fact/Detail | 17.031             | Dòng hàng hóa: SKU × qty × giá                        |
| fact_sales          | Fact/Flat   | 17.031             | Bảng fact phẳng denormalized cho analytics            |
| v_monthly_by_group  | View        | -                  | Doanh số tháng × nhóm SP cấp 1                        |
| v_customer_period   | View        | -                  | Tổng hợp khách hàng theo quý (RFM base)               |
| v_sku_monthly       | View        | -                  | Doanh số SKU × màu × tháng                            |
| v_customer_activity | View        | -                  | Hoạt động tổng hợp đại lý (churn detection)           |

## **1.2 Entity Relationship - sơ đồ quan hệ**

product_group (1) ──< (N) product_line (1) ──< (N) product

│

product_price (lịch sử giá)

province (1) ──< (N) customer (1) ──< (N) sales_order (1) ──< (N) order_line

│

product

fact_sales ← JOIN của: order_line × sales_order × customer × product × product_line × product_group × province

# **2\. Từ điển dữ liệu - chi tiết từng bảng**

## **2.1 product_group - Nhóm sản phẩm cấp 1**

Bảng tra cứu 5 nhóm sản phẩm cấp cao nhất. Là gốc của cây phân cấp sản phẩm 3 cấp.

| **Tên cột**     | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                                                   |
| --------------- | ---------------- | ------------ | --------------------------------------------------------------------------- |
| **group_code**  | VARCHAR(30)      | NOT NULL     | PK. Mã nhóm: CITYBIKE_P / KIDBIKE_1 / KIDBIKE_2 / SPORTBIKE_S / SPORTBIKE_A |
| **group_name**  | VARCHAR(100)     | NOT NULL     | Tên hiển thị: Xe phổ thông / Xe trẻ em nhóm 1...                            |
| **description** | TEXT             | NULL         | Mô tả danh mục sản phẩm                                                     |
| **created_at**  | TIMESTAMPTZ      | NOT NULL     | Thời điểm tạo. Default NOW()                                                |

5 giá trị cố định: CITYBIKE_P · KIDBIKE_1 · KIDBIKE_2 · SPORTBIKE_S · SPORTBIKE_A

## **2.2 product_line - Dòng sản phẩm cấp 3**

77 dòng xe, mỗi dòng thuộc một nhóm cấp 1. Ví dụ: 'Xe GN 06-27' thuộc CITYBIKE_P.

| **Tên cột**    | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                            |
| -------------- | ---------------- | ------------ | ---------------------------------------------------- |
| **line_id**    | SERIAL           | NOT NULL     | PK tự tăng                                           |
| **line_name**  | VARCHAR(100)     | NOT NULL     | Tên dòng xe: Xe GN 06-27, Xe New 26, Xe MTB 20-04... |
| **group_code** | VARCHAR(30)      | NOT NULL     | FK → product_group.group_code                        |
| **created_at** | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                        |

## **2.3 product - SKU sản phẩm**

247 SKU - mỗi SKU là một mã hàng cụ thể, tương ứng với một màu sắc/biến thể. Đây là hạt nhân của chiều sản phẩm.

| **Tên cột**      | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                              |
| ---------------- | ---------------- | ------------ | ------------------------------------------------------ |
| **product_code** | VARCHAR(20)      | NOT NULL     | PK. Mã hàng ERP: 000214004000000, 1030010000080000...  |
| **product_name** | VARCHAR(200)     | NOT NULL     | Tên đầy đủ: Xe đạp Thống Nhất GN 06-27 2.0 Cam         |
| **line_id**      | INTEGER          | NULL         | FK → product_line. NULL nếu SKU chưa map vào danh mục. |
| **color**        | VARCHAR(60)      | NULL         | Màu sắc trích từ tên: Đen, Cam, Xanh mint, Café/nâu... |
| **unit**         | VARCHAR(20)      | NOT NULL     | Đơn vị tính. Default 'Chiếc'                           |
| **is_active**    | BOOLEAN          | NOT NULL     | Default TRUE. FALSE = SKU đã ngừng bán                 |
| **created_at**   | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                          |

72/247 SKU không map được vào danh mục cấp 3 (line_id = NULL) do tên sản phẩm khác nhẹ hoặc là SKU mới chưa có trong catalogue. Các SKU này vẫn có đầy đủ dữ liệu giao dịch.

## **2.4 product_price - Lịch sử giá**

Lưu lịch sử biến động đơn giá theo thời gian. 196/247 SKU có nhiều hơn một mức giá trong kỳ - đây là giá thực tế giao dịch, không phải giá niêm yết cố định.

| **Tên cột**        | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                              |
| ------------------ | ---------------- | ------------ | -------------------------------------- |
| **price_id**       | SERIAL           | NOT NULL     | PK tự tăng                             |
| **product_code**   | VARCHAR(20)      | NOT NULL     | FK → product.product_code              |
| **unit_price**     | NUMERIC(15,2)    | NOT NULL     | Đơn giá (VND). CHECK > 0               |
| **effective_from** | DATE             | NOT NULL     | Ngày bắt đầu áp dụng giá               |
| **effective_to**   | DATE             | NULL         | Ngày kết thúc. NULL = giá đang áp dụng |
| **created_at**     | TIMESTAMPTZ      | NOT NULL     | Default NOW()                          |

Lưu ý: order_line.unit_price là giá thực tế tại thời điểm giao dịch, có thể khác với product_price tại cùng thời điểm (do chiết khấu thương mại).

## **2.5 province - Tỉnh / Thành phố**

75 tỉnh/thành phố phân chia theo 3 vùng địa lý. Được suy ra từ địa chỉ khách hàng.

| **Tên cột**       | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                             |
| ----------------- | ---------------- | ------------ | ----------------------------------------------------- |
| **province_id**   | SERIAL           | NOT NULL     | PK tự tăng                                            |
| **province_name** | VARCHAR(100)     | NOT NULL     | Tên tỉnh/thành: Hà Nội, TP. Hồ Chí Minh, Thanh Hóa... |
| **region**        | VARCHAR(50)      | NULL         | Vùng: Miền Bắc / Miền Trung / Miền Nam                |
| **created_at**    | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                         |

## **2.6 customer - Khách hàng / Đại lý**

702 khách hàng. Chủ yếu là B2B: công ty TNHH, cửa hàng xe đạp, hộ kinh doanh. Dữ liệu đã được ẩn danh hóa.

| **Tên cột**       | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                             |
| ----------------- | ---------------- | ------------ | ----------------------------------------------------- |
| **customer_code** | VARCHAR(20)      | NOT NULL     | PK. Mã khách hàng giả lập: KH-00001 → KH-00702        |
| **customer_name** | VARCHAR(200)     | NOT NULL     | Tên doanh nghiệp giả lập (stable per address cluster) |
| **tax_code**      | VARCHAR(15)      | NULL         | MST 10 số giả lập (stable per customer_code)          |
| **address**       | TEXT             | NULL         | Địa chỉ đã ẩn danh: bỏ số nhà, giữ đường/phường/quận  |
| **province_id**   | INTEGER          | NULL         | FK → province. Trích xuất từ address.                 |
| **customer_tier** | VARCHAR(20)      | NOT NULL     | Phân tầng: STANDARD / KEY / VIP. Default 'STANDARD'   |
| **is_active**     | BOOLEAN          | NOT NULL     | Default TRUE                                          |
| **created_at**    | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                         |
| **updated_at**    | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                         |

Phân tầng customer_tier chưa có giá trị thực - tất cả mặc định STANDARD. Sinh viên có thể phân tầng dựa trên kết quả RFM analysis (Module 2) rồi UPDATE lại.

## **2.7 sales_order - Phiếu bán hàng (header)**

1.627 phiếu. Mỗi phiếu tương ứng một giao dịch với một khách hàng, có thể gồm nhiều dòng hàng hóa. Các cột fiscal_year, fiscal_month, fiscal_quarter là computed columns - tự tính từ order_date.

| **Tên cột**        | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                                       |
| ------------------ | ---------------- | ------------ | --------------------------------------------------------------- |
| **order_id**       | SERIAL           | NOT NULL     | PK tự tăng                                                      |
| **so_number**      | VARCHAR(20)      | NOT NULL     | UNIQUE. Số chứng từ: BH25.XXXX / BH26.XXXX                      |
| **invoice_symbol** | VARCHAR(15)      | NULL         | Ký hiệu hóa đơn: C25TTN / C26TTN                                |
| **invoice_number** | VARCHAR(20)      | NULL         | Số hóa đơn gốc từ ERP (không unique giữa các ngày)              |
| **order_date**     | DATE             | NOT NULL     | Ngày chứng từ (= Ngày hóa đơn trong data gốc)                   |
| **customer_code**  | VARCHAR(20)      | NOT NULL     | FK → customer.customer_code                                     |
| **total_amount**   | NUMERIC(15,2)    | NULL         | Tổng doanh số. Auto-update qua trigger khi thêm/sửa order_line. |
| **total_quantity** | INTEGER          | NULL         | Tổng số lượng. Auto-update qua trigger.                         |
| **line_count**     | INTEGER          | NULL         | Số dòng hàng hóa. Auto-update qua trigger.                      |
| **fiscal_year**    | SMALLINT         | NOT NULL     | GENERATED: EXTRACT(YEAR FROM order_date)                        |
| **fiscal_month**   | SMALLINT         | NOT NULL     | GENERATED: EXTRACT(MONTH FROM order_date)                       |
| **fiscal_quarter** | SMALLINT         | NOT NULL     | GENERATED: EXTRACT(QUARTER FROM order_date)                     |
| **created_at**     | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                                   |

## **2.8 order_line - Dòng hàng hóa**

17.031 dòng giao dịch. Trung bình 10,5 dòng/phiếu, dao động 1-82 dòng. Đây là bảng chi tiết giao dịch - nền tảng cho mọi phân tích doanh số.

| **Tên cột**      | **Kiểu dữ liệu** | **Nullable** | **Mô tả**                                                      |
| ---------------- | ---------------- | ------------ | -------------------------------------------------------------- |
| **line_id**      | SERIAL           | NOT NULL     | PK tự tăng                                                     |
| **order_id**     | INTEGER          | NOT NULL     | FK → sales_order.order_id. ON DELETE CASCADE                   |
| **so_number**    | VARCHAR(20)      | NOT NULL     | Denormalized từ sales_order.so_number - tối ưu query analytics |
| **product_code** | VARCHAR(20)      | NOT NULL     | FK → product.product_code (Mã hàng)                            |
| **quantity**     | NUMERIC(10,2)    | NOT NULL     | Số lượng bán. CHECK > 0                                        |
| **unit_price**   | NUMERIC(15,2)    | NOT NULL     | Đơn giá thực tế giao dịch (VND, có thể khác product_price)     |
| **line_total**   | NUMERIC(15,2)    | NOT NULL     | Thành tiền = quantity × unit_price (làm tròn VND)              |
| **created_at**   | TIMESTAMPTZ      | NOT NULL     | Default NOW()                                                  |

## **2.9 fact_sales - Bảng fact phẳng (analytics)**

17.031 dòng denormalized - JOIN sẵn toàn bộ dimension vào một bảng. Được sinh tự động từ câu INSERT...SELECT trong 02_import_data.sql. Dùng cho BI dashboard, aggregation, ML feature engineering.

| **Nhóm cột** | **Các cột**                                                                      | **Mục đích**                                   |
| ------------ | -------------------------------------------------------------------------------- | ---------------------------------------------- |
| Thời gian    | order_date, fiscal_year, fiscal_quarter, fiscal_month, week_of_year              | Filter và group theo mọi granularity thời gian |
| Order ref    | so_number, order_id, line_id                                                     | Truy về bảng gốc khi cần                       |
| Khách hàng   | customer_code, customer_name, province_id, province_name, region                 | Phân tích theo đại lý và vùng địa lý           |
| Sản phẩm     | product_code, product_name, color, line_id_fk, line_name, group_code, group_name | Drill-down từ nhóm cấp 1 → dòng → SKU → màu    |
| Measures     | quantity, unit_price, line_total                                                 | 3 measure chính cho mọi aggregation            |

# **3\. Indexes và Views**

## **3.1 Chiến lược indexing**

Tất cả indexes phục vụ các pattern query phổ biến nhất trong analytics:

| **Tên Index**       | **Bảng**    | **Columns**                 | **Phục vụ query**       |
| ------------------- | ----------- | --------------------------- | ----------------------- |
| idx_so_date         | sales_order | order_date                  | Filter theo khoảng ngày |
| idx_so_year_month   | sales_order | fiscal_year, fiscal_month   | GROUP BY tháng/năm      |
| idx_so_year_quarter | sales_order | fiscal_year, fiscal_quarter | GROUP BY quý/năm        |
| idx_so_customer     | sales_order | customer_code               | JOIN và filter theo KH  |
| idx_ol_product      | order_line  | product_code                | Filter theo SKU         |
| idx_fact_year_month | fact_sales  | fiscal_year, fiscal_month   | Aggregation tháng/năm   |
| idx_fact_customer   | fact_sales  | customer_code               | GROUP BY đại lý         |
| idx_fact_group      | fact_sales  | group_code                  | Aggregation nhóm SP     |
| idx_fact_province   | fact_sales  | province_id                 | Phân tích theo vùng     |

## **3.2 Views phân tích**

### **v_monthly_by_group**

Doanh số tháng × nhóm sản phẩm cấp 1. Dùng cho trend chart, seasonality, YoY comparison.

- Cột chính: fiscal_year, fiscal_month, group_code, group_name
- Measures: order_count, total_qty, total_revenue, avg_unit_price

### **v_customer_period**

Tổng hợp hoạt động đại lý theo quý. Nền tảng cho RFM analysis và churn detection.

- Cột chính: fiscal_year, fiscal_quarter, customer_code, province_name, region
- Measures: order_count, total_qty, total_revenue, last_order_date, first_order_date

### **v_sku_monthly**

Doanh số SKU × màu sắc theo tháng. Dùng cho color trend analysis và slow-moving SKU detection.

- Cột chính: fiscal_year, fiscal_month, product_code, color, line_name, group_code
- Measures: total_qty, total_revenue, order_count

### **v_customer_activity**

Toàn bộ lịch sử hoạt động mỗi đại lý. Tính days_since_last_order = CURRENT_DATE − max(order_date).

- Dùng để: xác định đại lý inactive (>45 ngày), phân tầng VIP/KEY theo tổng doanh số

# **4\. Hướng dẫn cài đặt và import**

## **4.1 Tạo database và chạy DDL**

\# Bước 1: Tạo database

psql -U postgres -c "CREATE DATABASE tnbike_db ENCODING 'UTF8';"

\# Bước 2: Tạo schema, bảng, views, triggers

psql -U postgres -d tnbike_db -f 01_create_tables.sql

## **4.2 Import dữ liệu**

\# Bước 3: Import toàn bộ dữ liệu (2025-01-01 → 2026-02-28)

psql -U postgres -d tnbike_db -f 02_import_data.sql

Thời gian import ước tính: 30-90 giây tùy tốc độ máy. Cuối file sẽ in bảng kiểm tra row count.

**Kết quả mong đợi sau import:**

product_group | 5

product_line | 77

product | 247

product_price | 1016

province | 75

customer | 702

sales_order | 1627

order_line | 17031

fact_sales | 17031

## **4.3 Query kiểm tra nhanh**

Sau khi import, chạy các query sau để xác nhận dữ liệu đúng:

\-- Tổng doanh số theo năm

SELECT fiscal_year, SUM(line_total) AS revenue, COUNT(\*) AS rows

FROM fact_sales GROUP BY fiscal_year ORDER BY fiscal_year;

\-- Top 5 nhóm SP theo doanh số

SELECT group_name, SUM(line_total) AS revenue

FROM fact_sales GROUP BY group_name ORDER BY revenue DESC LIMIT 5;

\-- Top 10 tỉnh/thành phố

SELECT province_name, region, SUM(line_total) AS revenue

FROM fact_sales GROUP BY province_name, region

ORDER BY revenue DESC LIMIT 10;

\-- Kiểm tra churn signal: đại lý không đặt >60 ngày

SELECT customer_code, customer_name, days_since_last_order

FROM v_customer_activity WHERE days_since_last_order > 60

ORDER BY days_since_last_order DESC;

## **4.4 Kết nối Python**

import psycopg2, pandas as pd

conn = psycopg2.connect(

host='localhost', port=5432, database='tnbike_db',

user='postgres', password='your_password'

)

df = pd.read_sql("SELECT \* FROM fact_sales WHERE fiscal_year = 2025", conn)

**TNBIKE DATABASE · Thống Nhất Bike · Data Explorer 2026**

_9 bảng · 4 views · 1 trigger · PostgreSQL 14+_