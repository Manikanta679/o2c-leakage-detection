-- O2C Leakage Detection — Step 4 star-schema build
-- Author: Manikanta Engalligi
-- Reads raw_event, raw_case, raw_fx and the mapping tables.

DROP TABLE IF EXISTS dim_activity;
CREATE TABLE dim_activity (
    activity TEXT PRIMARY KEY,
    stage_group TEXT NOT NULL,
    is_happy_path INTEGER NOT NULL
);

INSERT INTO dim_activity (activity, stage_group, is_happy_path) VALUES
    ('Receive Purchase Order', 'order', 1),
    ('Create Sales Order', 'order', 1),
    ('Create Delivery', 'fulfilment', 1),
    ('Create Shipment', 'fulfilment', 1),
    ('Confirmed Delivery Date', 'fulfilment', 1),
    ('Issue Goods', 'fulfilment', 1),
    ('Create Invoice', 'billing', 1),
    ('Invoice Due Date', 'cash', 1),
    ('Clear Invoice', 'cash', 1),
    ('Deactivate Delivery Block', 'hold', 0),
    ('Deactivate Billing Block', 'hold', 0),
    ('Change Net Price in Sales Order', 'rework', 0),
    ('Change Manual Price in Sales Order', 'rework', 0),
    ('Change Material in Sales Order', 'rework', 0),
    ('Reject Sales Order', 'rework', 0),
    ('Cancel Sales Order Rejection', 'rework', 0);

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT,
    customer_group TEXT
);

INSERT INTO dim_customer (customer_id, customer_name, customer_group)
SELECT
    customer_id,
    MIN(customer_name),
    MIN(customer_group)
FROM raw_case
GROUP BY customer_id;

DROP TABLE IF EXISTS dim_geography;
CREATE TABLE dim_geography (
    customer_country TEXT PRIMARY KEY,
    region TEXT NOT NULL
);

INSERT INTO dim_geography (customer_country, region)
SELECT customer_country, region
FROM map_region;

DROP TABLE IF EXISTS dim_sales_org;
CREATE TABLE dim_sales_org (
    sales_org TEXT PRIMARY KEY,
    currency TEXT NOT NULL,
    is_eur_area INTEGER NOT NULL
);

INSERT INTO dim_sales_org (sales_org, currency, is_eur_area)
SELECT sales_org, currency, is_eur_area
FROM map_sales_org_currency;

DROP TABLE IF EXISTS dim_payment_term;
CREATE TABLE dim_payment_term (
    payment_term TEXT PRIMARY KEY,
    term_days INTEGER NOT NULL,
    term_method TEXT NOT NULL
);

INSERT INTO dim_payment_term (payment_term, term_days, term_method) VALUES
    ('30 days from date of invoice', 30, 'from_invoice'),
    ('45 days from date of invoice', 45, 'from_invoice'),
    ('60 days from date of invoice', 60, 'from_invoice'),
    ('90 days from date of invoice', 90, 'from_invoice'),
    ('30 days end of month', 30, 'end_of_month'),
    ('45 days end of month', 45, 'end_of_month'),
    ('60 days end of month', 60, 'end_of_month'),
    ('90 days end of month', 90, 'end_of_month'),
    ('Cash in advance', 0, 'cash_in_advance'),
    ('Free of charge', 0, 'free');

DROP TABLE IF EXISTS dim_delivery_block;
CREATE TABLE dim_delivery_block (
    delivery_block TEXT PRIMARY KEY,
    is_hold INTEGER NOT NULL,
    hold_class TEXT NOT NULL
);

INSERT INTO dim_delivery_block (delivery_block, is_hold, hold_class) VALUES
    ('No block', 0, 'none'),
    ('Credit Limit', 1, 'credit'),
    ('Block for Compliance', 1, 'compliance'),
    ('Customer Service Block', 1, 'service'),
    ('Political Reasons', 1, 'other'),
    ('Unconfirmed Block', 1, 'other'),
    ('Incoterm', 1, 'other'),
    ('Sales Control', 1, 'other'),
    ('Pre-Sample Needed', 1, 'other'),
    ('Change in Quantity', 1, 'other');

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    business_area TEXT NOT NULL,
    material_group TEXT NOT NULL,
    PRIMARY KEY (business_area, material_group)
);

INSERT INTO dim_product (business_area, material_group)
SELECT DISTINCT business_area, material_group
FROM raw_case;

DROP TABLE IF EXISTS dim_order_type;
CREATE TABLE dim_order_type (
    order_type TEXT PRIMARY KEY
);

INSERT INTO dim_order_type (order_type)
SELECT DISTINCT order_type FROM raw_case;

DROP TABLE IF EXISTS dim_calendar;
CREATE TABLE dim_calendar (
    date TEXT PRIMARY KEY,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name TEXT,
    is_weekend INTEGER,
    is_ecb_day INTEGER
);

INSERT INTO dim_calendar (date, year, quarter, month, month_name, is_weekend, is_ecb_day)
SELECT
    c.date,
    c.year,
    c.quarter,
    c.month,
    c.month_name,
    c.is_weekend,
    CASE WHEN fx.rate_date IS NULL THEN 0 ELSE 1 END
FROM map_calendar c
LEFT JOIN (
    SELECT DISTINCT rate_date FROM raw_fx
) fx
    ON fx.rate_date = c.date;

DROP TABLE IF EXISTS dim_fx_rate;
CREATE TABLE dim_fx_rate (
    rate_date TEXT NOT NULL,
    currency TEXT NOT NULL,
    units_per_eur REAL NOT NULL,
    eur_per_unit REAL NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

INSERT INTO dim_fx_rate (rate_date, currency, units_per_eur, eur_per_unit)
SELECT
    rate_date,
    currency,
    units_per_eur,
    1.0 / units_per_eur
FROM raw_fx;

DROP TABLE IF EXISTS fact_event;
CREATE TABLE fact_event (
    event_id INTEGER PRIMARY KEY,
    sales_order_id TEXT NOT NULL,
    activity TEXT NOT NULL,
    event_ts TEXT NOT NULL,
    event_date TEXT NOT NULL,
    automation TEXT,
    created_by TEXT
);

INSERT INTO fact_event (
    sales_order_id, activity, event_ts, event_date, automation, created_by
)
SELECT
    sales_order_id,
    activity,
    event_ts,
    substr(event_ts, 1, 10),
    automation,
    created_by
FROM raw_event;

CREATE INDEX idx_fact_event_order ON fact_event (sales_order_id);
CREATE INDEX idx_fact_event_activity ON fact_event (activity);
CREATE INDEX idx_fact_event_date ON fact_event (event_date);

DROP TABLE IF EXISTS order_stage;
CREATE TABLE order_stage AS
SELECT
    sales_order_id,
    MIN(CASE WHEN activity = 'Create Sales Order' THEN event_ts END) AS ts_create_sales_order,
    MIN(CASE WHEN activity = 'Confirmed Delivery Date' THEN event_ts END) AS ts_confirmed_delivery,
    MIN(CASE WHEN activity = 'Issue Goods' THEN event_ts END) AS ts_issue_goods,
    MIN(CASE WHEN activity = 'Create Invoice' THEN event_ts END) AS ts_create_invoice,
    MIN(CASE WHEN activity = 'Invoice Due Date' THEN event_ts END) AS ts_invoice_due,
    MAX(CASE WHEN activity = 'Clear Invoice' THEN event_ts END) AS ts_clear_invoice,
    MIN(CASE WHEN activity = 'Deactivate Billing Block' THEN event_ts END) AS ts_deactivate_billing_block,
    MIN(CASE WHEN activity = 'Deactivate Delivery Block' THEN event_ts END) AS ts_deactivate_delivery_block,
    SUM(CASE WHEN activity IN (
            'Change Net Price in Sales Order',
            'Change Manual Price in Sales Order',
            'Change Material in Sales Order',
            'Reject Sales Order',
            'Cancel Sales Order Rejection'
        ) THEN 1 ELSE 0 END) AS rework_event_count,
    SUM(CASE WHEN activity = 'Create Invoice' THEN 1 ELSE 0 END) AS invoice_event_count
FROM fact_event
GROUP BY sales_order_id;

DROP TABLE IF EXISTS fact_order;
CREATE TABLE fact_order AS
SELECT
    c.sales_order_id,
    c.order_value,
    c.customer_id,
    c.customer_country,
    c.sales_org,
    c.company_code,
    c.business_area,
    c.material_group,
    c.item_category,
    c.customer_group,
    c.order_type,
    c.payment_term,
    c.delivery_block,
    c.kpi_on_time_delivery,
    c.kpi_paid_on_time,
    c.kpi_price_changed,
    c.kpi_material_changed,
    s.ts_create_sales_order,
    s.ts_confirmed_delivery,
    s.ts_issue_goods,
    s.ts_create_invoice,
    s.ts_invoice_due,
    s.ts_clear_invoice,
    s.ts_deactivate_billing_block,
    s.ts_deactivate_delivery_block,
    s.rework_event_count,
    s.invoice_event_count,
    so.currency,
    CASE
        WHEN s.ts_create_invoice IS NOT NULL THEN substr(s.ts_create_invoice, 1, 10)
        WHEN s.ts_create_sales_order IS NOT NULL THEN substr(s.ts_create_sales_order, 1, 10)
        ELSE NULL
    END AS fx_date,
    CASE
        WHEN s.ts_issue_goods IS NOT NULL
         AND (
                s.ts_create_invoice IS NULL
                OR julianday(substr(s.ts_create_invoice, 1, 10))
                   - julianday(substr(s.ts_issue_goods, 1, 10)) >= 1
                OR s.ts_deactivate_billing_block IS NOT NULL
             )
        THEN 1 ELSE 0
    END AS flag_billing_lag,
    CASE
        WHEN c.kpi_price_changed = 'Yes'
          OR c.kpi_material_changed = 'Yes'
          OR s.rework_event_count > 0
        THEN 1 ELSE 0
    END AS flag_dispute_rework,
    CASE
        WHEN c.delivery_block <> 'No block'
          OR s.ts_deactivate_delivery_block IS NOT NULL
        THEN 1 ELSE 0
    END AS flag_hold,
    CASE
        WHEN c.delivery_block IN ('Credit Limit', 'Block for Compliance')
        THEN 1 ELSE 0
    END AS flag_credit_hold,
    CASE
        WHEN s.ts_issue_goods IS NOT NULL AND s.ts_create_invoice IS NOT NULL
        THEN julianday(substr(s.ts_create_invoice, 1, 10))
           - julianday(substr(s.ts_issue_goods, 1, 10))
        ELSE NULL
    END AS days_goods_to_invoice,
    CASE
        WHEN s.ts_create_invoice IS NOT NULL AND s.ts_clear_invoice IS NOT NULL
        THEN julianday(substr(s.ts_clear_invoice, 1, 10))
           - julianday(substr(s.ts_create_invoice, 1, 10))
        ELSE NULL
    END AS days_invoice_to_cash,
    CASE
        WHEN s.ts_confirmed_delivery IS NOT NULL AND s.ts_clear_invoice IS NOT NULL
        THEN julianday(substr(s.ts_clear_invoice, 1, 10))
           - julianday(substr(s.ts_confirmed_delivery, 1, 10))
        ELSE NULL
    END AS days_confirm_to_cash,
    pt.term_days AS days_best_possible,
    CAST(NULL AS REAL) AS units_per_eur,
    CAST(NULL AS REAL) AS order_value_eur
FROM raw_case c
INNER JOIN order_stage s
    ON s.sales_order_id = c.sales_order_id
INNER JOIN dim_sales_org so
    ON so.sales_org = c.sales_org
INNER JOIN dim_payment_term pt
    ON pt.payment_term = c.payment_term;

CREATE UNIQUE INDEX idx_fact_order_id ON fact_order (sales_order_id);
CREATE INDEX idx_fact_order_country ON fact_order (customer_country);
CREATE INDEX idx_fact_order_org ON fact_order (sales_org);
CREATE INDEX idx_fact_order_customer ON fact_order (customer_id);
