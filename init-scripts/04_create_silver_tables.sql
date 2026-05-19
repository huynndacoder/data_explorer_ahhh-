CREATE TABLE IF NOT EXISTS tnbike.silver_province (
    province_code VARCHAR(2) PRIMARY KEY,
    province_name VARCHAR(100) NOT NULL UNIQUE,
    province_type VARCHAR(30) NOT NULL,
    region VARCHAR(50) NOT NULL,
    source VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tnbike.silver_customer_geo (
    customer_code VARCHAR(20) PRIMARY KEY
        REFERENCES tnbike.customer(customer_code),

    province_code VARCHAR(2) NOT NULL
        REFERENCES tnbike.silver_province(province_code),

    source_address TEXT,
    legacy_province_id INTEGER,
    legacy_province_name VARCHAR(100),

    matched_text VARCHAR(100),
    match_method VARCHAR(50) NOT NULL,
    confidence VARCHAR(20) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_silver_customer_geo_province
ON tnbike.silver_customer_geo(province_code);