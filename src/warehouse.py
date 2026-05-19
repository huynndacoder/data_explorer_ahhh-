import psycopg2


DB_CONFIG = {
    "host": "postgres_dataexp",
    "database": "weather",
    "user": "admin",
    "password": "admin",
    "port": "5432",
}


def refresh_fact_sales():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO tnbike, public;")

            cur.execute(
                """
                CREATE TEMP TABLE fact_sales_new AS
                SELECT
                    so.order_date,
                    so.fiscal_year,
                    so.fiscal_quarter,
                    so.fiscal_month,
                    EXTRACT(WEEK FROM so.order_date)::SMALLINT AS week_of_year,
                    so.so_number,
                    so.order_id,
                    ol.line_id,
                    c.customer_code,
                    c.customer_name,

                    -- Keep old integer province_id for fact_sales schema compatibility.
                    -- Clean province_name and region come from Silver geography.
                    c.province_id AS province_id,
                    COALESCE(sp.province_name, 'UNKNOWN') AS province_name,
                    COALESCE(sp.region, 'UNKNOWN') AS region,

                    pr.product_code,
                    pr.product_name,
                    pr.color,
                    pr.line_id AS line_id_fk,
                    pl.line_name,
                    pg.group_code,
                    pg.group_name,
                    ol.quantity,
                    ol.unit_price,
                    ol.line_total
                FROM tnbike.order_line ol
                JOIN tnbike.sales_order so
                    ON ol.order_id = so.order_id
                LEFT JOIN tnbike.customer c
                    ON so.customer_code = c.customer_code
                LEFT JOIN tnbike.silver_customer_geo scg
                    ON c.customer_code = scg.customer_code
                LEFT JOIN tnbike.silver_province sp
                    ON scg.province_code = sp.province_code
                LEFT JOIN tnbike.product pr
                    ON ol.product_code = pr.product_code
                LEFT JOIN tnbike.product_line pl
                    ON pr.line_id = pl.line_id
                LEFT JOIN tnbike.product_group pg
                    ON pl.group_code = pg.group_code
                """
            )

            cur.execute("TRUNCATE tnbike.fact_sales;")

            cur.execute(
                """
                INSERT INTO tnbike.fact_sales (
                    order_date,
                    fiscal_year,
                    fiscal_quarter,
                    fiscal_month,
                    week_of_year,
                    so_number,
                    order_id,
                    line_id,
                    customer_code,
                    customer_name,
                    province_id,
                    province_name,
                    region,
                    product_code,
                    product_name,
                    color,
                    line_id_fk,
                    line_name,
                    group_code,
                    group_name,
                    quantity,
                    unit_price,
                    line_total
                )
                SELECT
                    order_date,
                    fiscal_year,
                    fiscal_quarter,
                    fiscal_month,
                    week_of_year,
                    so_number,
                    order_id,
                    line_id,
                    customer_code,
                    customer_name,
                    province_id,
                    province_name,
                    region,
                    product_code,
                    product_name,
                    color,
                    line_id_fk,
                    line_name,
                    group_code,
                    group_name,
                    quantity,
                    unit_price,
                    line_total
                FROM fact_sales_new;
                """
            )

            cur.execute("DROP TABLE fact_sales_new;")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def refresh_gold_fact_sales():
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO tnbike, public;")

            cur.execute("TRUNCATE tnbike.gold_fact_sales;")

            cur.execute(
                """
                INSERT INTO tnbike.gold_fact_sales (
                    order_date,
                    fiscal_year,
                    fiscal_quarter,
                    fiscal_month,
                    week_of_year,

                    so_number,
                    order_id,
                    line_id,

                    customer_code,
                    customer_name,

                    legacy_province_id,
                    legacy_province_name,
                    legacy_region,

                    silver_province_code,
                    silver_province_name,
                    silver_province_type,
                    silver_region,
                    geo_match_method,
                    geo_confidence,

                    product_code,
                    product_name,
                    color,
                    line_id_fk,
                    line_name,
                    group_code,
                    group_name,

                    quantity,
                    unit_price,
                    line_total
                )
                SELECT
                    so.order_date,
                    so.fiscal_year,
                    so.fiscal_quarter,
                    so.fiscal_month,
                    EXTRACT(WEEK FROM so.order_date)::SMALLINT AS week_of_year,

                    so.so_number,
                    so.order_id,
                    ol.line_id,

                    c.customer_code,
                    c.customer_name,

                    legacy_p.province_id AS legacy_province_id,
                    legacy_p.province_name AS legacy_province_name,
                    legacy_p.region AS legacy_region,

                    sp.province_code AS silver_province_code,
                    sp.province_name AS silver_province_name,
                    sp.province_type AS silver_province_type,
                    sp.region AS silver_region,
                    scg.match_method AS geo_match_method,
                    scg.confidence AS geo_confidence,

                    pr.product_code,
                    pr.product_name,
                    pr.color,
                    pr.line_id AS line_id_fk,
                    pl.line_name,
                    pg.group_code,
                    pg.group_name,

                    ol.quantity,
                    ol.unit_price,
                    ol.line_total
                FROM tnbike.order_line ol
                JOIN tnbike.sales_order so
                    ON ol.order_id = so.order_id
                LEFT JOIN tnbike.customer c
                    ON so.customer_code = c.customer_code
                LEFT JOIN tnbike.province legacy_p
                    ON c.province_id = legacy_p.province_id
                LEFT JOIN tnbike.silver_customer_geo scg
                    ON c.customer_code = scg.customer_code
                LEFT JOIN tnbike.silver_province sp
                    ON scg.province_code = sp.province_code
                LEFT JOIN tnbike.product pr
                    ON ol.product_code = pr.product_code
                LEFT JOIN tnbike.product_line pl
                    ON pr.line_id = pl.line_id
                LEFT JOIN tnbike.product_group pg
                    ON pl.group_code = pg.group_code
                """
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()