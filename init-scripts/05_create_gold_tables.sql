CREATE TABLE IF NOT EXISTS tnbike.gold_fact_sales (
    order_date DATE,
    fiscal_year SMALLINT,
    fiscal_quarter SMALLINT,
    fiscal_month SMALLINT,
    week_of_year SMALLINT,

    so_number VARCHAR(20),
    order_id INTEGER,
    line_id INTEGER,

    customer_code VARCHAR(20),
    customer_name VARCHAR(200),

    legacy_province_id INTEGER,
    legacy_province_name VARCHAR(100),
    legacy_region VARCHAR(50),

    silver_province_code VARCHAR(2),
    silver_province_name VARCHAR(100),
    silver_province_type VARCHAR(30),
    silver_region VARCHAR(50),
    geo_match_method VARCHAR(50),
    geo_confidence VARCHAR(20),

    product_code VARCHAR(20),
    product_name VARCHAR(200),
    color VARCHAR(60),
    line_id_fk INTEGER,
    line_name VARCHAR(100),
    group_code VARCHAR(30),
    group_name VARCHAR(100),

    quantity NUMERIC(10,2),
    unit_price NUMERIC(15,2),
    line_total NUMERIC(15,2)
);

CREATE INDEX IF NOT EXISTS idx_gold_fact_year_month
ON tnbike.gold_fact_sales(fiscal_year, fiscal_month);

CREATE INDEX IF NOT EXISTS idx_gold_fact_customer
ON tnbike.gold_fact_sales(customer_code);

CREATE INDEX IF NOT EXISTS idx_gold_fact_group
ON tnbike.gold_fact_sales(group_code);

CREATE INDEX IF NOT EXISTS idx_gold_fact_silver_province
ON tnbike.gold_fact_sales(silver_province_code);

CREATE INDEX IF NOT EXISTS idx_gold_fact_legacy_province
ON tnbike.gold_fact_sales(legacy_province_id);