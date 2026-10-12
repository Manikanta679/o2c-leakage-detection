# O2C Leakage Detection — Data Lock

**Author:** Manikanta Engalligi  
**Step:** 1 of 8 — lock sources, size, and merge keys  
**Status:** Locked. No cleaning or dashboard work in this step.

## Decision

Use the large QPR Order-to-Cash pair as the process and commercial facts. Use official ECB euro reference rates for EUR reporting.

Do not use Celonis Academy as a file source. Celonis is the process-intelligence method, not the extract.

Do not use the smaller SAP Extended demo (about 10k cases). It is too small and too generic for this project.

## Locked files

Location: `data/raw`

| File | Source | Role | Size | Grain |
|---|---|---|---|---|
| `OTC_Events_900k.csv` | QPR ProcessAnalyzer sample event logs | Process fact | 900,113 events | one row = one activity on a sales order |
| `OTC_Cases_92k.csv` | QPR ProcessAnalyzer sample case attributes | Commercial / customer dimension | 91,746 orders | one row = one sales order |
| `eurofxref-hist.csv` | European Central Bank, eurofxref historical ZIP | FX dimension | 7,111 daily rate rows (1999-01-04 to 2026-10-09) | one row = one calendar day |

Provenance archive kept next to the CSV: `eurofxref-hist.zip`.

Inspected and rejected files are in `data/raw/_inspected_not_used`. They are not part of the model.

## Why this pair is large enough

- **900,113** process events  
- **91,746** sales orders  
- **€702.7m** order value (source amount field `SO: Value`)  
- Date span in the event log: **2021-12-15 to 2024-10-28**  
- **45** customer countries  
- **16** sales organisations  
- Activities cover confirmation, delivery block, goods issue, billing block, invoice, due date, and invoice clearing  

That is enough to isolate billing lag, block/hold delay, and cash delay by segment and region.

## Merge keys

### Merge 1 — required (process to commercial header)

| Left | Right | Key |
|---|---|---|
| `OTC_Events_900k.csv`.`Sales Order ID` | `OTC_Cases_92k.csv`.`Sales Order ID` | `Sales Order ID` |

Coverage checked: **91,746 / 91,746 = 100%**. No event-only orders. No header-only orders.

This is the standard process-mining join: event log to case attributes.

### Merge 2 — reporting currency (date + currency)

The O2C files have **no native currency column**. Amounts sit in `SO: Value`.

EUR conversion will use a documented mapping in the next modelling step:

1. Map `SO: Sales Org` (and where needed `SO: Company Code`) to an ISO currency.  
2. Take the invoice or event date.  
3. Join ECB rates on **`Date` + currency code**.

| Left | Right | Key |
|---|---|---|
| derived `event_date` + derived `currency` | `eurofxref-hist.csv`.`Date` + currency column (USD, GBP, …) | `Date` + `Currency` |

EUR-area sales orgs will use rate = 1. Weekend / holiday dates will use the last available ECB working-day rate. That rule will be written when the calendar table is built.

## Fields that support the three leaks

From the event log (`Activity`):

- **Billing lag:** `Issue Goods` → `Create Invoice`; also `Deactivate Billing Block`  
- **Dispute / rework loops:** `Change Net Price in Sales Order`, `Change Manual Price in Sales Order`, `Change Material in Sales Order`, `Reject Sales Order`, `Cancel Sales Order Rejection`  
- **Holds / blocks:** `Deactivate Delivery Block`; case field `SO: Delivery Block` (includes Credit Limit, Compliance, Customer Service)  
- **Cash cycle:** `Invoice Due Date`, `Clear Invoice`

From the case header:

- Segment: `SO: Customer Group`, `SO: Business Area`, `SO: Type`  
- Region: `SO: Customer Country`, `SO: Sales Org`  
- Terms: `SO: Payment term`  
- Value: `SO: Value`  
- Outcome flags already in source: `KPI: Paid On Time`, `KPI: On Time Delivery`

## What this step does not do

- No SQL transforms  
- No leak flags yet  
- No Power BI  
- No git commit unless requested  

## Next step

Step 2 — write the data dictionary (every kept column, grain, and source) and leave the raw files unchanged.
