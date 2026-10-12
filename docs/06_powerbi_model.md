# O2C Leakage Detection — Power BI Model

**Author:** Manikanta Engalligi  
**Step:** 6 of 8 — connect data and set relationships  
**Status:** CSV model files are ready. Report pages are Step 7.

Do **not** use Power BI sample data.  
Do **not** connect to SQL Server.  
Do **not** connect to Celonis.

## Files to load

Folder: `C:\Users\Manikanta\Desktop\Masters Projects\O2C Leakage\powerbi\model`

| File | Role in the model |
|---|---|
| `mart_order_kpi.csv` | Main fact. One row = one order. Value, flags, cash, region |
| `fact_event.csv` | Process fact. One row = one activity. Large file (~83 MB) |
| `dim_customer.csv` | Customer |
| `dim_geography.csv` | Country and region |
| `dim_sales_org.csv` | Sales org and currency |
| `dim_payment_term.csv` | Terms and contractual days |
| `dim_delivery_block.csv` | Hold class |
| `dim_activity.csv` | Activity and stage group |
| `dim_calendar.csv` | Date |
| `dim_order_type.csv` | Order type |
| `mart_leak_impact.csv` | Four-row leak ranking |
| `mart_headline.csv` | One-row company KPIs |

## Relationships to create

| From (many) | To (one) | Key |
|---|---|---|
| `mart_order_kpi` | `dim_customer` | `customer_id` |
| `mart_order_kpi` | `dim_geography` | `customer_country` |
| `mart_order_kpi` | `dim_sales_org` | `sales_org` |
| `mart_order_kpi` | `dim_payment_term` | `payment_term` |
| `mart_order_kpi` | `dim_delivery_block` | `delivery_block` |
| `mart_order_kpi` | `dim_order_type` | `order_type` |
| `fact_event` | `mart_order_kpi` | `sales_order_id` |
| `fact_event` | `dim_activity` | `activity` |
| `fact_event` | `dim_calendar` | `event_date` = `date` |

Cardinality: **Many to one**.  
Cross-filter: **Single** (dimension filters the fact).

`mart_leak_impact` and `mart_headline` stay disconnected. They are KPI tables, not part of the star.

## Save as

`C:\Users\Manikanta\Desktop\Masters Projects\O2C Leakage\powerbi\O2C_Leakage.pbix`

## What this step does not do

No report pages. No colours. No titles. That is Step 7.
