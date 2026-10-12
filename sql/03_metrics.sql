-- O2C Leakage Detection — Step 5 metrics
-- Author: Manikanta Engalligi
-- Snapshot date is the last event date in the log: 2024-10-28

DROP TABLE IF EXISTS mart_order_kpi;
CREATE TABLE mart_order_kpi AS
WITH snap AS (
    SELECT '2024-10-28' AS snapshot_date
),
peers AS (
    SELECT
        SUM(CASE WHEN flag_hold = 0 AND days_confirm_to_cash IS NOT NULL
                 THEN days_confirm_to_cash * order_value_eur END)
        / SUM(CASE WHEN flag_hold = 0 AND days_confirm_to_cash IS NOT NULL
                   THEN order_value_eur END) AS hold_peer_cycle_days,
        SUM(CASE WHEN flag_dispute_rework = 0 AND days_invoice_to_cash IS NOT NULL
                 THEN days_invoice_to_cash * order_value_eur END)
        / SUM(CASE WHEN flag_dispute_rework = 0 AND days_invoice_to_cash IS NOT NULL
                   THEN order_value_eur END) AS dispute_peer_dso_days
    FROM fact_order
)
SELECT
    o.sales_order_id,
    o.order_value_eur,
    o.currency,
    o.customer_id,
    o.customer_country,
    g.region,
    o.sales_org,
    o.customer_group,
    o.business_area,
    o.order_type,
    o.payment_term,
    o.delivery_block,
    o.days_best_possible,
    o.days_goods_to_invoice,
    o.days_invoice_to_cash,
    o.days_confirm_to_cash,
    o.flag_billing_lag,
    o.flag_dispute_rework,
    o.flag_hold,
    o.flag_credit_hold,
    o.invoice_event_count,
    CASE
        WHEN o.ts_issue_goods IS NOT NULL AND o.ts_create_invoice IS NULL THEN 1
        ELSE 0
    END AS is_unbilled_delivered,
    CASE
        WHEN o.ts_create_invoice IS NOT NULL AND o.ts_clear_invoice IS NULL THEN 1
        ELSE 0
    END AS is_open_ar,
    CASE
        WHEN o.days_invoice_to_cash IS NOT NULL
         AND o.days_invoice_to_cash > o.days_best_possible THEN 1
        ELSE 0
    END AS is_late_vs_terms,
    CASE
        WHEN o.days_invoice_to_cash IS NOT NULL
        THEN o.days_invoice_to_cash - o.days_best_possible
        ELSE NULL
    END AS days_vs_terms,
    -- Billing cash: extra days after goods issue, or days still unbilled to snapshot
    CASE
        WHEN o.ts_issue_goods IS NOT NULL AND o.ts_create_invoice IS NULL THEN
            o.order_value_eur
            * MAX(julianday((SELECT snapshot_date FROM snap))
                  - julianday(substr(o.ts_issue_goods, 1, 10)), 0)
            / 365.0
        WHEN o.days_goods_to_invoice IS NOT NULL AND o.days_goods_to_invoice > 0 THEN
            o.order_value_eur * o.days_goods_to_invoice / 365.0
        ELSE 0
    END AS cash_billing_eur,
    -- Hold cash: extra confirm-to-cash days versus non-hold peers
    CASE
        WHEN o.flag_hold = 1 AND o.days_confirm_to_cash IS NOT NULL
         AND o.days_confirm_to_cash > (SELECT hold_peer_cycle_days FROM peers)
        THEN o.order_value_eur
             * (o.days_confirm_to_cash - (SELECT hold_peer_cycle_days FROM peers))
             / 365.0
        ELSE 0
    END AS cash_hold_eur,
    -- Dispute cash: extra invoice-to-cash days versus clean peers (zero if faster)
    CASE
        WHEN o.flag_dispute_rework = 1 AND o.days_invoice_to_cash IS NOT NULL
         AND o.days_invoice_to_cash > (SELECT dispute_peer_dso_days FROM peers)
        THEN o.order_value_eur
             * (o.days_invoice_to_cash - (SELECT dispute_peer_dso_days FROM peers))
             / 365.0
        ELSE 0
    END AS cash_dispute_eur,
    -- Collection cash: paid later than contractual terms, or still open past terms
    CASE
        WHEN o.days_invoice_to_cash IS NOT NULL
         AND o.days_invoice_to_cash > o.days_best_possible
        THEN o.order_value_eur
             * (o.days_invoice_to_cash - o.days_best_possible)
             / 365.0
        WHEN o.ts_create_invoice IS NOT NULL
         AND o.ts_clear_invoice IS NULL
         AND (julianday((SELECT snapshot_date FROM snap))
              - julianday(substr(o.ts_create_invoice, 1, 10))) > o.days_best_possible
        THEN o.order_value_eur
             * ((julianday((SELECT snapshot_date FROM snap))
                 - julianday(substr(o.ts_create_invoice, 1, 10)))
                - o.days_best_possible)
             / 365.0
        ELSE 0
    END AS cash_collection_eur
FROM fact_order o
JOIN dim_geography g
    ON g.customer_country = o.customer_country;

DROP TABLE IF EXISTS mart_leak_impact;
CREATE TABLE mart_leak_impact AS
SELECT
    1 AS rank_hint,
    'Billing lag' AS leak_name,
    'Billing / Order-to-Invoice Lead' AS process_owner,
    SUM(flag_billing_lag) AS orders_flagged,
    ROUND(SUM(CASE WHEN flag_billing_lag = 1 THEN order_value_eur ELSE 0 END), 2) AS value_flagged_eur,
    ROUND(SUM(cash_billing_eur), 2) AS cash_locked_eur,
    ROUND(SUM(cash_billing_eur) * 0.06, 2) AS annual_interest_eur_at_6pct
FROM mart_order_kpi
UNION ALL
SELECT
    2,
    'Dispute / rework loops',
    'AR Dispute Manager (Sales contributing)',
    SUM(flag_dispute_rework),
    ROUND(SUM(CASE WHEN flag_dispute_rework = 1 THEN order_value_eur ELSE 0 END), 2),
    ROUND(SUM(cash_dispute_eur), 2),
    ROUND(SUM(cash_dispute_eur) * 0.06, 2)
FROM mart_order_kpi
UNION ALL
SELECT
    3,
    'Holds (delivery / credit-style)',
    'Credit Manager / Order Management',
    SUM(flag_hold),
    ROUND(SUM(CASE WHEN flag_hold = 1 THEN order_value_eur ELSE 0 END), 2),
    ROUND(SUM(cash_hold_eur), 2),
    ROUND(SUM(cash_hold_eur) * 0.06, 2)
FROM mart_order_kpi
UNION ALL
SELECT
    4,
    'Collection lag after terms',
    'AR Collections Lead',
    SUM(CASE WHEN cash_collection_eur > 0 THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN cash_collection_eur > 0 THEN order_value_eur ELSE 0 END), 2),
    ROUND(SUM(cash_collection_eur), 2),
    ROUND(SUM(cash_collection_eur) * 0.06, 2)
FROM mart_order_kpi;

DROP TABLE IF EXISTS mart_segment_region;
CREATE TABLE mart_segment_region AS
SELECT
    region,
    customer_group,
    business_area,
    COUNT(*) AS orders,
    ROUND(SUM(order_value_eur), 2) AS order_value_eur,
    ROUND(AVG(days_invoice_to_cash), 2) AS avg_days_invoice_to_cash,
    ROUND(
        SUM(CASE WHEN days_invoice_to_cash IS NOT NULL THEN days_invoice_to_cash * order_value_eur END)
        / NULLIF(SUM(CASE WHEN days_invoice_to_cash IS NOT NULL THEN order_value_eur END), 0)
    , 2) AS weighted_days_invoice_to_cash,
    ROUND(AVG(days_best_possible), 2) AS avg_best_possible_days,
    SUM(flag_billing_lag) AS billing_lag_orders,
    SUM(flag_dispute_rework) AS dispute_orders,
    SUM(flag_hold) AS hold_orders,
    ROUND(SUM(cash_billing_eur), 2) AS cash_billing_eur,
    ROUND(SUM(cash_dispute_eur), 2) AS cash_dispute_eur,
    ROUND(SUM(cash_hold_eur), 2) AS cash_hold_eur,
    ROUND(SUM(cash_collection_eur), 2) AS cash_collection_eur
FROM mart_order_kpi
GROUP BY region, customer_group, business_area;

DROP TABLE IF EXISTS mart_headline;
CREATE TABLE mart_headline AS
SELECT
    COUNT(*) AS orders,
    ROUND(SUM(order_value_eur), 2) AS order_value_eur,
    SUM(CASE WHEN days_invoice_to_cash IS NOT NULL THEN 1 ELSE 0 END) AS orders_with_cash,
    ROUND(
        SUM(CASE WHEN days_invoice_to_cash IS NOT NULL THEN days_invoice_to_cash * order_value_eur END)
        / SUM(CASE WHEN days_invoice_to_cash IS NOT NULL THEN order_value_eur END)
    , 2) AS weighted_actual_dso,
    ROUND(
        SUM(days_best_possible * order_value_eur) / SUM(order_value_eur)
    , 2) AS weighted_best_possible_dso,
    ROUND(SUM(cash_billing_eur), 2) AS cash_billing_eur,
    ROUND(SUM(cash_dispute_eur), 2) AS cash_dispute_eur,
    ROUND(SUM(cash_hold_eur), 2) AS cash_hold_eur,
    ROUND(SUM(cash_collection_eur), 2) AS cash_collection_eur,
    0.06 AS cost_of_capital
FROM mart_order_kpi;
