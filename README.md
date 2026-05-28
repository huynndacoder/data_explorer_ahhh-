# DataExplorer — Email-to-Warehouse ETL Pipeline

Pipeline xử lý đơn hàng tự động cho **Công ty xe đạp Thống Nhất** trong cuộc thi Data Explorers 2026. Hệ thống nhận email đặt hàng từ đại lý (`.eml` có đính kèm PDF), trích xuất dữ liệu đơn hàng, kiểm tra hợp lệ và nạp vào PostgreSQL theo schema được cung cấp.

Project áp dụng **Medallion Architecture** để tách rõ các lớp dữ liệu: lớp **Bronze/Source** lưu dữ liệu giao dịch theo schema gốc, lớp **Silver** thực hiện làm sạch và làm giàu dữ liệu khách hàng, sản phẩm, địa lý, và lớp **Gold** tổng hợp, tạo các bảng fact phục vụ phân tích. Thiết kế này giữ nguyên khả năng tương thích với yêu cầu ban tổ chức, đồng thời bổ sung các lớp dữ liệu sạch hơn cho báo cáo và BI.
## Mục tiêu

Tự động xử lý toàn bộ đơn hàng tháng 3/2026 từ email/PDF và ghi dữ liệu hợp lệ vào database.

Đầu ra chính:

- `email_log`: ghi nhận trạng thái xử lý từng email
- `sales_order`: đầu đơn hàng
- `order_line`: dòng hàng hóa
- `fact_sales`: bảng fact phẳng theo schema gốc
- `silver_province`, `silver_customer_geo`: lớp địa lý đã qua làm sạch và chuẩn hóa
- `gold_fact_sales`: bảng fact nâng cao dùng địa lý legacy + Silver song song

## Tech Stack

- Apache Airflow 2.8.1
- PostgreSQL 13 / Debezium PostgreSQL image
- Python 3.11
- Docker Compose
- `pdfplumber`
- `psycopg2-binary`

## Triển khaipipeline Pipeline

### Yêu cầu

- Docker
- Docker Compose

### Khởi động

```bash
docker compose up -d
```

Các service chính:

| Service | Mô tả |
|---|---|
| `postgres-airflow` | Metadata database cho Airflow |
| `postgres_dataexp` | PostgreSQL nghiệp vụ, schema `tnbike` |
| `airflow-webserver` | Giao diện web của Airflow |
| `airflow-scheduler` | Thực thi DAG, lên lịch cho pipeline |
| `airflow-init` | Chạy migration Airflow DB và tạo user |

### Tài khoản mặc định

| Dịch vụ | User | Password |
|---|---|---|
| Airflow Web UI | `airflow` | `airflow` |
| PostgreSQL nghiệp vụ | `admin` | `admin` |
| PostgreSQL Airflow | `airflow` | `airflow` |

### Reset toàn bộ database

Khi muốn chạy lại từ đầu và chạy lại toàn bộ init scripts:

```bash
docker compose down -v
docker compose up --build -d
```

Lưu ý: `down -v` sẽ xóa Docker volumes, bao gồm dữ liệu PostgreSQL hiện tại.

## Cách chạy pipeline

1. Nếu chạy lần đầu, giải nén tất cả file `.eml` vào:

```text
maildata/incoming/
```

   **Nếu khởi động lại pipeline thì chạy lệnh sau ở terminal:**

```bash
 mv maildata/processed/*.eml maildata/incoming/ && mv maildata/failed/*.eml maildata/incoming 
```

2. Mở Airflow UI:

```text
http://localhost:8085
```

3. Trigger DAG bằng cách click vào biểu tượng nút Play ở Actions:

```text
email_order_pipeline
```

Hoặc trigger bằng CLI:

```bash
docker exec -it dataexplorer-airflow-scheduler-1 airflow dags trigger email_order_pipeline
```

Sau khi xử lý, email sẽ được chuyển tới:

```text
maildata/processed/  # nếu email xử lý thành công
maildata/failed/     # nếu email xử lý thất bại
```

Log của quá trình trích xuất dữ liệu từ email sẽ được lưu vào bảng:

```text
tnbike.email_log
```

4. 


## Kiến trúc hệ thống
![Pipeline Architecture](docs/images/pipeline-architecture.svg)
## Luồng DAG

**DAG ID:** `email_order_pipeline`  
**Kích hoạt:** thủ công  
**Song song:** tối đa 8 mapped tasks

| # | Task | Mô tả |
|---|---|---|
| 1 | `list_eml_files` | Quét thư mục `maildata/incoming/` để lấy danh sách email |
| 2 | `process_single_email` | Mapped task: mỗi email một task. Parse email/PDF, validate, load DB, ghi log, route file |
| 3 | `summarize_results` | Tổng hợp số lượng thành công/thất bại và phân loại lỗi |
| 4 | `run_silver_layer` | Chạy các bước làm sạch/làm giàu dữ liệu |
| 5 | `refresh_fact_sales` | Làm mới bảng `fact_sales` theo schema legacy |
| 6 | `refresh_gold_fact_sales` | Làm mới bảng `gold_fact_sales` dùng geography Silver |

## Per-email ETL

```text
.eml
→ parse email metadata
→ extract PDF attachment
→ parse PDF header + order lines
→ validate quantity, unit price, line total
→ ensure product exists
→ resolve/create customer by MST
→ upsert sales_order
→ replace order_line for that order
→ write email_log
→ move email to processed/failed
```

### `extract.py`

- Decode MIME headers
- Extract plain-text email body
- Save PDF attachment to temp folder
- Extract anchor fields:
  - `so_number`
  - `MST`
  - customer name
  - customer address
  - declared total amount
- Parse PDF order lines with `pdfplumber`
- Use regex fallback when table extraction fails

### `validators.py`

- Validate required fields
- Validate `quantity × unit_price ≈ line_total`
- Validate total amount against email anchor
- Ensure product codes exist in `tnbike.product`
- Auto-create missing products as unresolved rows when needed

### `loaders.py`

- Upsert `sales_order`
- Replace `order_line` for idempotent reruns
- Upsert `email_log`
- Resolve customer by MST
- Auto-create customer when MST is valid but not found

### `router.py`

- Move successful `.eml` files to `processed/`
- Move failed `.eml` files to `failed/`
- Clean temporary PDF files

## Error handling

Business/data errors are handled inside each mapped email task. The task returns a status dict and writes to `email_log`.

Typical categories:

| Category | Cause |
|---|---|
| `missing_customer` | Email body does not contain usable MST |
| `missing_product` | PDF parsing failed to extract product codes |
| `line_total_mismatch` | Extracted line totals do not match expected values |
| `unknown` | Other unexpected business/data error |

Infrastructure/code errors should still fail Airflow normally.

## Silver layer

Silver is used for controlled data-quality improvement after ingestion.

### Customer name cleanup

Removes accidental field labels from customer names.

Examples:

```text
Tên : CÔNG TY TNHH PHÚC AN
→ CÔNG TY TNHH PHÚC AN

Đại lý : CỬA HÀNG XE ĐẠP A
→ CỬA HÀNG XE ĐẠP A
```

### Product name enrichment

Some March PDF product codes did not exist in the original product master. These products were initially created as:

```text
UNRESOLVED PRODUCT {product_code}
```

The Silver layer applies manually verified product names for 18 unresolved products.

### Product hierarchy enrichment

Some products had `line_id = NULL`, which caused missing `line_name`, `group_code`, and `group_name` in fact tables.

The Silver layer applies 36 high-confidence mappings:

```text
product_code → product_line.line_id
```

Only products that clearly match an existing product line are mapped. Products whose catalogue lines are absent remain NULL intentionally.

Validated impact:

```text
Before enrichment:
- 5,355 fact rows without product line
- 25.28B VND affected revenue

After enrichment:
- 2,948 fact rows without product line
- 11.53B VND affected revenue
```

### Silver geography

The original `tnbike.province` table is preserved as a legacy/source table. It contains typos, duplicates, old province names, city-level values, and address fragments, so it is not used as the trusted geography layer.

Silver geography adds:

| Table | Purpose |
|---|---|
| `silver_province` | Canonical 34 post-merger province/city units |
| `silver_customer_geo` | Mapping from customer to canonical province code |

Matching priority:

```text
customer.address
→ legacy province name fallback
→ normalized alias lookup
→ silver province code
```

Validated result:

```text
silver_province_count = 34
customer_count = 798
mapped_customer_count = 797
unmatched_customer_count = 1
```

The only unmatched customer has no address and no legacy province evidence, so it is intentionally left unknown.

## Fact tables

### `fact_sales`

`fact_sales` is the required flat fact table following the provided schema. It preserves the original/legacy geography structure from the provided database.

Use this table for compatibility with the organiser schema.

### `gold_fact_sales`

`gold_fact_sales` is the cleaned analytical fact table.

It keeps both geography systems explicitly:

```text
legacy_province_id
legacy_province_name
legacy_region

silver_province_code
silver_province_name
silver_region
geo_match_method
geo_confidence
```

This avoids mixing old surrogate `province_id` values with new canonical province names.

## Database schema

Main database:

```text
Database: weather
Schema: tnbike
Host: postgres_dataexp
Port: 5432
```

Main tables:

| Table | Type | Notes |
|---|---|---|
| `product_group` | Dimension | Product group level |
| `product_line` | Dimension | Product line/catalogue level |
| `product` | Dimension | SKU-level product master |
| `province` | Legacy dimension | Original geography table |
| `customer` | Dimension | Dealer/customer master |
| `sales_order` | Fact header | Order header |
| `order_line` | Fact detail | Order lines |
| `fact_sales` | Fact flat | Required denormalized fact table |
| `gold_fact_sales` | Fact flat | Clean analytics fact table |
| `email_log` | Log | Email processing status |
| `silver_province` | Silver dimension | Canonical geography |
| `silver_customer_geo` | Silver bridge | Customer-to-province mapping |

The original row counts from the organiser-provided database are documented in:

```text
tnbike_database_schema.md
```

After March 2026 ingestion, row counts will increase.

## Project structure

```text
DataExplorer/
├── airflow/
│   └── dags/
│       └── email_pipeline_dag.py
├── init-scripts/
│   ├── 01_create_tables.sql
│   ├── 02_import_data.sql
│   ├── 03_create_email_log.sql
│   ├── 04_create_silver_tables.sql
│   └── 05_create_gold_tables.sql
├── maildata/
│   ├── incoming/
│   ├── processed/
│   └── failed/
├── src/
│   ├── __init__.py
│   ├── extract.py
│   ├── validators.py
│   ├── loaders.py
│   ├── router.py
│   ├── silver.py
│   └── warehouse.py
├── docker-compose.yml
├── dockerfile.airflow
├── requirements.txt
├── tnbike_database_schema.md
└── README.md
```

## Manual validation

### Email processing status

```sql
SELECT processing_status, COUNT(*)
FROM tnbike.email_log
GROUP BY processing_status
ORDER BY processing_status;
```

### March 2026 orders

```sql
SELECT COUNT(*) AS march_order_count
FROM tnbike.sales_order
WHERE order_date >= DATE '2026-03-01'
  AND order_date < DATE '2026-04-01';
```

### March 2026 order lines

```sql
SELECT COUNT(*) AS march_order_line_count
FROM tnbike.order_line ol
JOIN tnbike.sales_order so
    ON ol.order_id = so.order_id
WHERE so.order_date >= DATE '2026-03-01'
  AND so.order_date < DATE '2026-04-01';
```

### March 2026 fact rows

```sql
SELECT COUNT(*) AS march_fact_rows
FROM tnbike.fact_sales
WHERE order_date >= DATE '2026-03-01'
  AND order_date < DATE '2026-04-01';
```

### Silver geography coverage

```sql
SELECT
    COUNT(*) AS total_customers,
    COUNT(scg.customer_code) AS mapped_customers,
    COUNT(*) - COUNT(scg.customer_code) AS unmatched_customers
FROM tnbike.customer c
LEFT JOIN tnbike.silver_customer_geo scg
    ON c.customer_code = scg.customer_code;
```

### Product hierarchy coverage

```sql
SELECT
    COUNT(*) AS fact_rows_without_product_line,
    SUM(quantity) AS quantity,
    SUM(line_total) AS revenue
FROM tnbike.fact_sales
WHERE line_id_fk IS NULL;
```

### Remaining unmapped product lines

```sql
SELECT
    product_code,
    product_name,
    COUNT(*) AS fact_rows,
    SUM(quantity) AS total_qty,
    SUM(line_total) AS total_revenue
FROM tnbike.fact_sales
WHERE line_id_fk IS NULL
GROUP BY product_code, product_name
ORDER BY total_revenue DESC
LIMIT 30;
```

## Manual Silver test

Run inside Airflow scheduler container:

```bash
docker exec -it dataexplorer-airflow-scheduler-1 bash
cd /opt/airflow
PYTHONPATH=/opt/airflow/src python -c "from silver import run_silver_layer; run_silver_layer()"
```

Expected current result:

```text
unresolved_product_count = 0
silver_province_count = 34
mapped_customer_count = 797
unmatched_customer_count = 1
```

## Development notes

### Airflow user creation

If the Airflow user is missing:

```bash
docker exec -it dataexplorer-airflow-scheduler-1 airflow users create \
  --username airflow \
  --password airflow \
  --firstname admin \
  --lastname admin \
  --role Admin \
  --email admin@example.com
```

Check users:

```bash
docker exec -it dataexplorer-airflow-scheduler-1 airflow users list
```

### Moving processed emails back for reruns

If emails have already been processed and you want to rerun the DAG:

```bash
docker exec -it dataexplorer-airflow-scheduler-1 bash
mv /opt/airflow/maildata/processed/*.eml /opt/airflow/maildata/incoming/
```

## Git notes

Do not commit raw or generated data:

```text
.env
CSVData/
EDA/output/
maildata/incoming/*
maildata/processed/*
maildata/failed/*
pdfdata/
processing/
*.rar
*.pdf
*.log
```

Keep these tracked:

```text
src/
airflow/dags/
init-scripts/
docker-compose.yml
dockerfile.airflow
requirements.txt
README.md
tnbike_database_schema.md
```

## Status

Current status:

```text
Bronze ingestion: functional
Silver enrichment: functional and validated
fact_sales refresh: functional
gold_fact_sales: analytics-ready layer using Silver geography
```

Known remaining data-quality limitations:

```text
- 1 customer cannot be mapped to province because both address and legacy province are NULL.
- Some products remain without product_line because their catalogue lines are absent from the provided product_line table.
- Original province table is preserved as dirty legacy/source geography.
```
