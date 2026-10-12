# O2C Leakage Detection — Data Dictionary

**Author:** Manikanta Engalligi  
**Step:** 2 of 8 — document grain, columns, and quality  
**Status:** Dictionary only. Raw files were not changed.

Sources and merge keys are locked in `docs/01_data_lock.md`.

---

## 1. How to read this dictionary

| Term | Meaning |
|---|---|
| **Grain** | What one row represents |
| **Primary key** | The field that uniquely identifies a row, or the case it belongs to |
| **Join key** | The field used to combine two files |
| **Nulls** | Empty values in the source. These are quality notes, not fixes |

Delimiter for both QPR files: **semicolon (`;`)**.  
Delimiter for ECB: **comma (`,`)**.  
Text encoding: UTF-8.

---

## 2. File A — process event log

**File:** `data/raw/OTC_Events_900k.csv`  
**Source:** QPR ProcessAnalyzer sample event logs  
**Grain:** one row = one activity that happened on one sales order  
**Rows:** 900,113  
**Columns:** 5  
**Primary / join key:** `Sales Order ID`  
**Distinct sales orders:** 91,746

This is the **fact** table for stage times, variants, and leak flags.

| Column | Type in source | Nulls | Distinct (approx.) | Meaning | Used later for |
|---|---|---|---|---|---|
| `Sales Order ID` | text | 0 | 91,746 | Case ID. Same ID as in the case file | Merge 1 |
| `Activity` | text | 0 | 16 | Process step name | Stage map, leak flags |
| `Timestamp` | datetime `YYYY-MM-DD HH:MM:SS.mmm` | 0 | many | When the activity happened | Waiting time, DSO-style days |
| `Automation` | text | 192,484 | 3 filled values | Manual / automatic flag. Empty on some events | Optional quality / automation view |
| `CreatedBy` | text | 192,484 | 473 | User who posted the event. Empty when Automation is empty | Optional owner / resource view |

`Automation` and `CreatedBy` share the same 192,484 empty rows. That is a source gap, not a join problem. The three required process-mining fields (`Sales Order ID`, `Activity`, `Timestamp`) have **no nulls**.

### Activity list (all 16)

| Activity | Event count | Role in this project |
|---|---|---|
| Create Invoice | 121,645 | Billing. Can repeat |
| Invoice Due Date | 104,800 | Contractual due point |
| Receive Purchase Order | 91,746 | Upstream demand |
| Create Sales Order | 91,746 | Order exists |
| Create Delivery | 89,081 | Fulfilment start |
| Create Shipment | 87,898 | Fulfilment |
| Confirmed Delivery Date | 87,684 | Promise date. Closest to “order confirmation” |
| Issue Goods | 86,030 | Delivered. Start of billing-lag clock |
| Clear Invoice | 84,825 | Cash applied / invoice cleared |
| Change Net Price in Sales Order | 19,397 | Commercial rework |
| Deactivate Billing Block | 10,181 | Billing hold released |
| Deactivate Delivery Block | 6,869 | Delivery / credit-style hold released |
| Reject Sales Order | 6,182 | Stop / dispute-like path |
| Change Manual Price in Sales Order | 5,727 | Commercial rework |
| Change Material in Sales Order | 4,169 | Order change / mismatch risk |
| Cancel Sales Order Rejection | 2,133 | Rejection reversed |

Event date range: **2021-12-15** to **2024-10-28**.

---

## 3. File B — sales order / customer header

**File:** `data/raw/OTC_Cases_92k.csv`  
**Source:** QPR ProcessAnalyzer sample case attributes  
**Grain:** one row = one sales order  
**Rows:** 91,746  
**Columns:** 18  
**Primary / join key:** `Sales Order ID`  
**Join to File A:** `Sales Order ID` = `Sales Order ID` (100% match)

This is the **dimension / commercial header**. Filters for segment and region come from here.

| Column | Type in source | Nulls | Distinct | Meaning | Used later for |
|---|---|---|---|---|---|
| `Sales Order ID` | text | 0 | 91,746 | Same key as the event log | Merge 1 |
| `SO: Business Area` | text | 0 | 8 | Product / industry line (Power Tools, Agriculture, …) | Segment slice |
| `SO: Value` | decimal | 0 | many | Order value. **No currency code in file** | Cash impact, weighted DSO |
| `SO: Company Code` | text | 0 | 15 | Legal entity (e.g. Drystone Deutschland GmbH) | Optional company view; currency hint |
| `SO: Customer` | text | 0 | 2,671 | Customer name plus a numeric suffix | Customer ranking |
| `SO: Customer Country` | text | 0 | 45 | Sold-to country | Region slice |
| `SO: Customer Group` | text | 0 | 2 | External customer / Internal customer | Segment slice |
| `SO: Delivery Block` | text | 0 | 10 | Current / recorded delivery block reason | Hold / credit-style leak |
| `SO: Item Category` | text | 0 | 9 | Item type (mostly Standard Item) | Optional filter |
| `SO: Material Group` | text | 0 | 48 | Product family | Optional filter |
| `SO: Payment term` | text | 0 | 10 | Contractual days (30/45/60/90, EOM, CIA, free) | Best possible DSO |
| `SO: RowNumber` | integer-like text | 0 | 47 | Source row / item helper. Not a business KPI | Ignore for dashboard |
| `SO: Sales Org` | text | 0 | 17 | Selling organisation geography | Region; **currency mapping** |
| `SO: Type` | text | 0 | 3 | Normal Order / Restocking / Sample order | Segment / filter |
| `KPI: On Time Delivery` | text | 0 | 3 | Yes / No / missing goods-issue or confirm date | Fulfilment quality |
| `KPI: Paid On Time` | text | 0 | 3 | Yes / No / invoice not cleared or due missing | Collection quality |
| `KPI: Price Changed` | text | 0 | 2 | Yes / No | Dispute / rework flag |
| `KPI: Material Changed` | text | 0 | 2 | Yes / No | Dispute / rework flag |

Header fields have **no nulls**.

`SO: Value` is a number only. Currency is not stored. EUR conversion stays a later, documented mapping from `SO: Sales Org` (and if needed `SO: Company Code`) plus ECB rates.

---

## 4. File C — ECB euro reference rates

**File:** `data/raw/eurofxref-hist.csv`  
**Source:** European Central Bank, `eurofxref-hist.zip`  
**Grain:** one row = one ECB publication day  
**Rows:** 7,111  
**Join key later:** `Date` + currency column name (USD, GBP, INR, …)  
**Date range:** 1999-01-04 to 2026-10-09  

Rates are **units of foreign currency per 1 EUR**.

| Column | Meaning |
|---|---|
| `Date` | ECB reference date (`YYYY-MM-DD`) |
| `USD`, `GBP`, `JPY`, `CHF`, `CNY`, `INR`, `AUD`, `CAD`, `MXN`, `MYR`, `NOK`, `SEK`, `TRY`, `ZAR`, … | Daily rate vs EUR. `N/A` means the series is missing that day (legacy or holiday currencies) |
| trailing empty column | Source artefact. Ignore |

USD and GBP have no empty cells in this extract. Some older currencies (CYP, EEK, SIT, SKK, …) are `N/A` after they left the published set. That does not affect 2021–2024 O2C dates for the main sales orgs.

Weekend and target-holiday gaps will be filled with the **last available working-day rate** when the calendar is built. Not done in this step.

---

## 5. Keys — restated

| Merge | Left | Right | Key | Coverage |
|---|---|---|---|---|
| 1. Process + header | Event log | Case header | `Sales Order ID` | 91,746 / 91,746 = 100% |
| 2. EUR reporting | Derived `event_date` + derived `currency` | ECB `Date` + currency column | `Date` + `Currency` | Built in the model step, not here |

---

## 6. Quality notes (do not fix yet)

1. `Automation` and `CreatedBy` are empty on 192,484 events. Do not use them as required filters.  
2. Invoice-related activities can repeat (`Create Invoice` count > order count). One order can have more than one invoice event.  
3. Source KPI text values include “missing” states (`Invoice not Cleared or Due Date Missing`). Those are useful, not errors.  
4. `SO: RowNumber` is a technical helper. It will not go on the dashboard.  
5. No native currency field. Do not treat `SO: Value` as EUR until Merge 2 is applied.  
6. ECB file has a blank last column. Ignore it.

---

## 7. What this step does not do

- No column renamed in the raw files  
- No rows deleted  
- No SQL model  
- No Power BI  
- No git commit unless requested  

## Next step

Step 3 — star schema design: facts, dimensions, and which columns move into each table. Still no dashboard.
