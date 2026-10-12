# O2C Leakage Detection — SQL Build

**Author:** Manikanta Engalligi  
**Step:** 4 of 8 — load raw files, build the star schema, apply both joins  
**Status:** Local SQLite database created. No Power BI.

## Database

`data/clean/o2c_leakage.db`

Scripts:

- `sql/01_load_and_build.py` — load CSVs and run the model  
- `sql/02_build_star.sql` — star-schema SQL  

## Joins applied

| Merge | Key | Result |
|---|---|---|
| 1. Events to orders | `sales_order_id` | 900,113 events, 91,746 orders, **0 unmatched** |
| 2. Order to ECB FX | `fx_date` + `currency` | **91,746 / 91,746** orders have `order_value_eur` |

`fx_date` is the invoice date, or the sales-order create date if no invoice exists.  
Weekend / holiday dates use the last ECB rate on or before that date.  
EUR sales orgs use rate = 1.

Assumption, documented: `SO: Value` is in the **sales-org currency**.

## Tables built

Facts: `fact_event`, `fact_order`  
Dimensions: `dim_activity`, `dim_customer`, `dim_geography`, `dim_sales_org`, `dim_payment_term`, `dim_delivery_block`, `dim_product`, `dim_order_type`, `dim_calendar`, `dim_fx_rate`

## First leak counts (order grain)

These are flags only. Cash impact is Step 5.

| Flag | Orders | Share of 91,746 |
|---|---|---|
| Billing lag | 18,915 | 20.6% |
| Dispute / rework | 22,474 | 24.5% |
| Any hold (delivery block or unblock event) | 6,482 | 7.1% |
| Credit-class hold (Credit Limit or Compliance) | 4 | ~0.0% |

True credit-limit blocks are rare in this sample. Most holds are operational (customer service, political, unconfirmed). The dashboard must not label every hold as a credit hold.

## What this step does not do

- No DSO ranking or cash-locked table  
- No Power BI  
- No git commit unless requested  

## Next step

Step 5 — DSO-style metrics and cash impact by leak, segment, and region.
