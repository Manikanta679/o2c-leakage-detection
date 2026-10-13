-- O2C Leakage Detection
-- Author: Manikanta Engalligi
--
-- vw_o2c_case_timeline
-- One row = one sales order.
-- Columns follow the happy path:
--   Create Sales Order
--   -> Confirmed Delivery Date
--   -> Issue Goods
--   -> Create Invoice
--   -> Invoice Due Date
--   -> Clear Invoice
-- Extra columns capture holds and rework (not the happy path).

DROP VIEW IF EXISTS vw_o2c_case_timeline;

CREATE VIEW vw_o2c_case_timeline AS
SELECT
    o.sales_order_id,

    -- Happy-path timestamps (left-to-right O2C flow)
    o.ts_create_sales_order,
    o.ts_confirmed_delivery,
    o.ts_issue_goods,
    o.ts_create_invoice,
    o.ts_invoice_due,
    o.ts_clear_invoice,

    -- Waiting time between stages (days)
    CASE
        WHEN o.ts_create_sales_order IS NOT NULL
         AND o.ts_confirmed_delivery IS NOT NULL
        THEN julianday(substr(o.ts_confirmed_delivery, 1, 10))
           - julianday(substr(o.ts_create_sales_order, 1, 10))
    END AS days_order_to_confirm,
    o.days_goods_to_invoice,
    o.days_invoice_to_cash,
    o.days_confirm_to_cash,
    o.days_best_possible,

    -- Exception path
    o.ts_deactivate_delivery_block,
    o.ts_deactivate_billing_block,
    o.rework_event_count,
    o.invoice_event_count,
    o.flag_billing_lag,
    o.flag_dispute_rework,
    o.flag_hold,
    o.flag_credit_hold,

    -- Commercial grain for the same case
    o.order_value_eur,
    o.currency,
    o.customer_id,
    o.customer_country,
    o.sales_org,
    o.customer_group,
    o.business_area,
    o.payment_term,
    o.delivery_block
FROM fact_order o;
