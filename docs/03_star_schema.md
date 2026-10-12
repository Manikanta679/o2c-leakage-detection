# O2C Leakage Detection — Star Schema

**Author:** Manikanta Engalligi  
**Step:** 3 of 8 — design facts, dimensions, and keys  
**Status:** Model design only. No tables loaded. Raw files unchanged.

This is the standard finance-ops shape: process facts at event grain, commercial facts at order grain, and shared dimensions for customer, geography, calendar, and FX.

---

## 1. Why two facts

Power BI and DSO metrics cannot sit on the event log alone.

| Fact | Grain | Question it answers |
|---|---|---|
| `fact_event` | one activity on one sales order | What happened, in what order, how long between steps |
| `fact_order` | one sales order | Value, segment, region, leak flags, days-to-cash, cash locked |

`fact_order` is the table the dashboard will use for KPIs.  
`fact_event` is the table used to **build** stage dates and leak flags, and later for process-path views.

They connect through `sales_order_id`.

---

## 2. Model picture

```text
                         dim_calendar
                              |
                              | event_date / invoice_date
                              |
dim_activity ---- fact_event ---- fact_order ---- dim_customer
                              |        |
                              |        +---- dim_geography
                              |        +---- dim_sales_org
                              |        +---- dim_payment_term
                              |        +---- dim_delivery_block
                              |        +---- dim_product
                              |        +---- dim_order_type
                              |
                         dim_fx_rate
                    (date + currency → EUR)
```

No snowflake of 20 tables. Extra source fields that are not needed on the dashboard stay off the model.

---

## 3. Fact tables

### 3.1 `fact_event`

**Source:** `OTC_Events_900k.csv`  
**Grain:** one row = one activity  
**Expected rows:** 900,113  
**Primary key:** surrogate `event_id` (row number in load). Business key = `sales_order_id` + `activity` + `timestamp` (not always unique if the same activity repeats).

| Column | From | Notes |
|---|---|---|
| `event_id` | generated | Integer, unique |
| `sales_order_id` | `Sales Order ID` | Join to `fact_order` |
| `activity` | `Activity` | Also join to `dim_activity` |
| `event_ts` | `Timestamp` | Full timestamp |
| `event_date` | date part of `Timestamp` | Join to `dim_calendar` and FX |
| `automation` | `Automation` | May be empty |
| `created_by` | `CreatedBy` | May be empty |

**Do not put** order value on this table. Value lives once on `fact_order`, or it will be double-counted.

### 3.2 `fact_order`

**Source:** `OTC_Cases_92k.csv` plus stage dates derived later from `fact_event`  
**Grain:** one row = one sales order  
**Expected rows:** 91,746  
**Primary key:** `sales_order_id`

| Column | From | Notes |
|---|---|---|
| `sales_order_id` | `Sales Order ID` | PK / join to events |
| `order_value` | `SO: Value` | Source amount, not yet EUR |
| `customer_id` | parsed from `SO: Customer` | Join `dim_customer` |
| `customer_country` | `SO: Customer Country` | Join `dim_geography` |
| `sales_org` | `SO: Sales Org` | Join `dim_sales_org` |
| `company_code` | `SO: Company Code` | Kept as attribute |
| `business_area` | `SO: Business Area` | Join `dim_product` |
| `material_group` | `SO: Material Group` | Join `dim_product` |
| `item_category` | `SO: Item Category` | Attribute |
| `customer_group` | `SO: Customer Group` | External / internal |
| `order_type` | `SO: Type` | Join `dim_order_type` |
| `payment_term` | `SO: Payment term` | Join `dim_payment_term` |
| `delivery_block` | `SO: Delivery Block` | Join `dim_delivery_block` |
| `kpi_on_time_delivery` | `KPI: On Time Delivery` | Source flag |
| `kpi_paid_on_time` | `KPI: Paid On Time` | Source flag |
| `kpi_price_changed` | `KPI: Price Changed` | Source flag |
| `kpi_material_changed` | `KPI: Material Changed` | Source flag |

**Derived later (Step 4–5, not loaded now):**

| Column | Meaning |
|---|---|
| `ts_create_sales_order` | First `Create Sales Order` |
| `ts_confirmed_delivery` | First `Confirmed Delivery Date` |
| `ts_issue_goods` | First `Issue Goods` |
| `ts_create_invoice` | First `Create Invoice` |
| `ts_invoice_due` | First `Invoice Due Date` |
| `ts_clear_invoice` | Last `Clear Invoice` |
| `ts_deactivate_billing_block` | First billing-block release |
| `ts_deactivate_delivery_block` | First delivery-block release |
| `flag_billing_lag` | Goods issued, invoice late or missing |
| `flag_dispute_rework` | Price / material change or reject loop |
| `flag_credit_hold` | Delivery block / credit-style hold |
| `days_goods_to_invoice` | Billing lag days |
| `days_invoice_to_cash` | Invoice to clear |
| `days_confirm_to_cash` | Confirmation to cash |
| `days_best_possible` | From payment terms |
| `currency` | Mapped from sales org |
| `order_value_eur` | `order_value` ÷ ECB rate (or ×, depending on quote) |

`SO: RowNumber` does **not** enter the model.

---

## 4. Dimension tables

### 4.1 `dim_customer`

| Column | From |
|---|---|
| `customer_id` | Numeric suffix in `SO: Customer` (e.g. `0021915612`) |
| `customer_name` | Name part of `SO: Customer` |
| `customer_group` | `SO: Customer Group` |

Grain: one customer. About 2,671 IDs.  
If the suffix is missing on a row, `customer_id` = full source string.

### 4.2 `dim_geography`

| Column | From / rule |
|---|---|
| `customer_country` | `SO: Customer Country` |
| `region` | Mapped in Step 4: EMEA / AMER / APAC |

Grain: one country. About 45 countries.  
This is the dashboard **region** slicer.

Planned region map (applied in Step 4, not now):

- **AMER:** USA, United States, Mexico, …  
- **APAC:** China, India, Malaysia, Australia, South Korea, …  
- **EMEA:** United Kingdom, Germany, and remaining Europe / Middle East / Africa countries in the file  

### 4.3 `dim_sales_org`

| Column | From / rule |
|---|---|
| `sales_org` | `SO: Sales Org` |
| `currency` | ISO code mapped in Step 4 (GBP, EUR, USD, …) |
| `is_eur_area` | Yes if currency = EUR |

This dimension is the **bridge to ECB**. There is no currency on the raw order.

### 4.4 `dim_payment_term`

| Column | From / rule |
|---|---|
| `payment_term` | `SO: Payment term` |
| `term_days` | Parsed integer (30, 45, 60, 90, 0 for cash in advance / free of charge) |
| `term_method` | `from_invoice` / `end_of_month` / `cash_in_advance` / `free` |

Used for **best possible DSO**.

### 4.5 `dim_delivery_block`

| Column | From / rule |
|---|---|
| `delivery_block` | `SO: Delivery Block` |
| `is_hold` | 0 if `No block`, else 1 |
| `hold_class` | `credit` / `compliance` / `service` / `other` / `none` |

`Credit Limit` and `Block for Compliance` are the credit-style holds.  
`Customer Service Block` and others are operational holds. They are not all “credit”, and the model will not pretend they are.

### 4.6 `dim_product`

| Column | From |
|---|---|
| `business_area` | `SO: Business Area` |
| `material_group` | `SO: Material Group` |

Used as a composite slicer, not as a true product master.

### 4.7 `dim_order_type`

| Column | From |
|---|---|
| `order_type` | `SO: Type` |

Normal Order / Restocking / Sample order.

### 4.8 `dim_activity`

| Column | From / rule |
|---|---|
| `activity` | Event `Activity` |
| `stage_group` | `order` / `hold` / `fulfilment` / `billing` / `cash` / `rework` |
| `is_happy_path` | Yes for the standard sequence only |

Happy-path activities: Receive Purchase Order → Create Sales Order → Create Delivery → Create Shipment → Confirmed Delivery Date → Issue Goods → Create Invoice → Invoice Due Date → Clear Invoice.

### 4.9 `dim_calendar`

| Column | Rule |
|---|---|
| `date` | One day from 2021-12-01 through 2024-12-31, plus ECB history as needed |
| `year`, `quarter`, `month`, `month_name` | Standard |
| `is_weekend` | Sat / Sun |
| `is_ecb_day` | Date exists in ECB file |

One date table only. Both facts use it.

### 4.10 `dim_fx_rate`

**Source:** `eurofxref-hist.csv` (unpivoted)

| Column | Meaning |
|---|---|
| `rate_date` | ECB `Date` |
| `currency` | USD, GBP, INR, … |
| `eur_per_unit` | `1 / published_rate` when the file is “units per EUR” |
| `units_per_eur` | Published ECB value |

Grain: one currency on one date.  
Join: `fact_order.invoice_or_event_date` + `dim_sales_org.currency` → `dim_fx_rate`.

EUR-area orgs: rate = 1, no lookup required.

---

## 5. Relationships

| From | To | Key | Type |
|---|---|---|---|
| `fact_event` | `fact_order` | `sales_order_id` | many → one |
| `fact_event` | `dim_activity` | `activity` | many → one |
| `fact_event` | `dim_calendar` | `event_date` | many → one |
| `fact_order` | `dim_customer` | `customer_id` | many → one |
| `fact_order` | `dim_geography` | `customer_country` | many → one |
| `fact_order` | `dim_sales_org` | `sales_org` | many → one |
| `fact_order` | `dim_payment_term` | `payment_term` | many → one |
| `fact_order` | `dim_delivery_block` | `delivery_block` | many → one |
| `fact_order` | `dim_product` | `business_area` + `material_group` | many → one |
| `fact_order` | `dim_order_type` | `order_type` | many → one |
| `fact_order` | `dim_calendar` | invoice / event date (later) | many → one |
| `dim_sales_org` + date | `dim_fx_rate` | `currency` + `date` | lookup |

Power BI will use the same keys. SQL will create them first so the model is not built by clicking in Power Query only.

---

## 6. Leak flags — planned mapping (calculated in Step 4, not now)

| Leak | Order-level rule (draft) |
|---|---|
| **Billing lag** | `Issue Goods` exists AND (`Create Invoice` missing OR invoice timestamp is after goods issue by more than a set threshold, default 1 day). Also true if `Deactivate Billing Block` exists |
| **Dispute / rework** | Price change KPI = Yes OR material change KPI = Yes OR activities include reject / price / material change |
| **Hold / credit-style** | Delivery block ≠ `No block` OR `Deactivate Delivery Block` exists. Credit class only when block reason is Credit Limit or Compliance |

An order can have more than one flag. Ranking will use cash impact, not flag count.

---

## 7. What is in vs out

**In the model**

- Event fact, order fact  
- Customer, geography, sales org / currency, payment terms, blocks, product, order type, activity, calendar, FX  

**Out of the model**

- `SO: RowNumber`  
- ECB blank trailing column  
- Rejected SAP Extended demo files  
- Celonis as a data source  

---

## 8. What this step does not do

- No SQLite tables created  
- No leak days calculated  
- No Power BI relationships  
- No git commit unless requested  

## Next step

Step 4 — SQL: load raw files into a local SQLite database, build these tables, and apply the two joins (`Sales Order ID`, then date + currency).
