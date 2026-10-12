# O2C Leakage Detection — DSO and Cash Impact

**Author:** Manikanta Engalligi  
**Step:** 5 of 8 — quantify delays and cash  
**Snapshot date:** 2024-10-28 (last event in the log)  
**Cost of capital:** 6% (assumption, for interest only)

Tables: `mart_order_kpi`, `mart_leak_impact`, `mart_segment_region`, `mart_headline`  
SQL: `sql/03_metrics.sql`

---

## 1. Formulas

**Weighted actual DSO**  
Average `invoice date → clear invoice` days, weighted by `order_value_eur`.  
Only orders that were both invoiced and cleared (66,106 orders).

**Weighted best possible DSO**  
Contractual `SO: Payment term` days, weighted by value.  
This is policy, not leakage by itself.

**Days vs terms**  
`days_invoice_to_cash − days_best_possible`  
Positive = paid later than the contract. Negative = paid early.

**Cash locked**  
`order_value_eur × extra_days / 365`

| Leak | Extra days used |
|---|---|
| Billing lag | Days from goods issue to invoice, if > 0. If goods issued and never invoiced: days from goods issue to snapshot |
| Dispute / rework | Invoice-to-cash days above the clean-order peer average. If the order is faster than peers, cash = 0 |
| Holds | Confirm-to-cash days above the no-hold peer average. If faster, cash = 0 |
| Collection after terms | Days above payment terms on cleared invoices, or days past terms on open invoices |

**Interest**  
`cash locked × 6%`

Orders can carry more than one flag. Leak cash figures can overlap. Do not add all four cash numbers and call that unique cash.

`SO: Value` is treated as sales-org currency, then converted to EUR with ECB rates (Step 4).

---

## 2. Headline

| Metric | Value |
|---|---|
| Orders | 91,746 |
| Order value | **€652.9m** |
| Weighted actual DSO (paid invoices) | **44.1 days** |
| Weighted contractual terms | **54.5 days** |

On average, paid invoices are collected **faster** than the contract. A single “actual DSO minus terms” gap would look healthy and would hide the leaks. That is why cash is measured on the late and blocked cases, not on the company average.

---

## 3. Leak ranking by cash locked

| Rank | Leak | Orders flagged | Value flagged | Cash locked | Interest @ 6% | Owner |
|---|---|---|---|---|---|---|
| 1 | Collection lag after terms | 56,046 | €388.8m | **€96.88m** | €5.81m | AR Collections Lead |
| 2 | Dispute / rework loops | 22,474 | €178.4m | **€4.47m** | €0.27m | AR Dispute Manager |
| 3 | Holds (delivery / credit-style) | 6,482 | €46.7m | **€1.93m** | €0.12m | Credit / Order Management |
| 4 | Billing lag | 18,915 | €128.0m | **€1.07m** | €0.06m | Billing / Order-to-Invoice Lead |

### How to read this

**Collection lag** is the large cash problem. About €389m was paid late versus terms, or is still open past terms. That is not one of the three names in the original brief, but the data puts it first. A professional study reports it.

**Dispute / rework** is common (24.5% of orders, €178m). Average DSO on dispute orders is not worse than clean orders. Cash here is only the subset that is slower than clean peers.

**Holds** add about 7–8 days to the cycle versus orders with no hold. True credit-limit / compliance blocks are only 4 orders. Most holds are operational (customer service, political, unconfirmed).

**Billing lag** hits many orders (€128m flagged) but extra days are short (about 2 days when invoice is late). That is why cash locked is smaller than the volume suggests. Unbilled after goods issue is only €1.0m.

---

## 4. By region

| Region | Orders | Value | Collection cash | Dispute cash | Hold cash | Billing cash |
|---|---|---|---|---|---|---|
| EMEA | 70,317 | €513.9m | €73.8m | €3.8m | €1.6m | €0.8m |
| AMER | 15,780 | €118.1m | €18.0m | €0.5m | €0.1m | €0.3m |
| APAC | 5,649 | €20.9m | €5.1m | €0.2m | €0.2m | €0.0m |

EMEA holds most of the value and most of the cash. APAC is small in value but slower on actual DSO (see Step 4 notes).

## 5. By segment

| Segment | Orders | Value | Collection cash | Billing cash |
|---|---|---|---|---|
| External customer | 90,092 | €642.9m | €93.9m | €1.07m |
| Internal customer | 1,654 | €9.9m | €3.0m | €0.00m |

Almost all leakage sits in **external** customers.

Largest business area by collection cash: **Power Tools** (€31.8m), then Agriculture (€17.0m), Building Materials (€11.6m).

---

## 6. Decision draft (for the later brief)

Top three **by cash**:

1. Collection lag after terms — AR Collections Lead — €96.9m cash equivalent  
2. Dispute / rework — AR Dispute Manager — €4.5m extra days versus clean peers, on €178m of orders  
3. Holds — Credit / Order Management — €1.9m, mostly operational holds not credit limits  

Billing remains a **volume** issue (18.9k orders) and stays on the dashboard, but it is not the top cash lever.

If collection extra days were cut to zero, cash acceleration is about **€97m**. At 6% that is about **€5.8m** annual interest. That is a scenario, not a forecast.

---

## 7. What this step does not do

- No Power BI  
- No git commit unless requested  

## Next step

Step 6 — Power BI model only: connect to `o2c_leakage.db` and set relationships. No report pages yet.
