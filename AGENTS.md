# AGENTS.md

## Project Overview

Sales ETL pipeline using:

- Apache Airflow 2.8.1
- PostgreSQL
- Docker Compose
- Python 3.11

Pipeline flow:

EML files
-> extract email metadata
-> extract PDF attachments
-> parse sales orders
-> insert into PostgreSQL

## Important Architecture Rules

- `customer` rows MUST exist before inserting `sales_order`
- DAGs live in `airflow/dags/`
- Shared business logic lives in `src/`
- Never place business logic directly inside DAG files
- DAG files should orchestrate only
- NEVER overwrite the given init_scripts.


## Folder Structure

project/
├── airflow/dags/
├── src/
├── init-scripts/
├── maildata/
│   ├── incoming/
│   ├── processed/
│   └── failed/
├── processing/temp_pdfs/

## Docker Services

- airflow-webserver
- airflow-scheduler
- airflow-init
- postgres-airflow
- postgres_dataexp

## Airflow Notes

- Airflow metadata DB is `postgres-airflow`
- Business data DB is `postgres_dataexp`
- Always run:
  `docker compose up airflow-init`
  before starting scheduler/webserver

## Coding Rules

- Use logging instead of print
- Use transactions carefully
- Roll back failed inserts
- Move failed emails to `maildata/failed`
- Move successful emails to `maildata/processed`

## Database Rules

Insertion order:

1. customer
2. sales_order
3. order_line

Foreign keys must always be satisfied.

## Common Problems

### after docker compose up -d, always have to manually add a user for Airflow.
docker compose exec airflow-webserver airflow users create \
  --username airflow \
  --password airflow \
  --firstname admin \
  --lastname admin \
  --role Admin \
  --email admin@example.com

### If you want to rerun the pipeline because of any reason, move emails back to incoming
mv maildata/failed/*.eml maildata/incoming 
mv maildata/processed/*.eml maildata/incoming 

### FK constraint failures

If:

```text
sales_order_customer_code_fkey

