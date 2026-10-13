# Order-to-Cash Leakage — Decision Brief

**Author:** Manikanta Engalligi  
**Scope:** Order confirmation → cash collection  
**Data:** QPR O2C event log (91,746 orders, 900,113 events) joined to ECB euro FX rates  
**Snapshot:** 2024-10-28  
**Cost of capital (assumption):** 6%

---

## Question

Where does cash stick between confirmation and collection, who owns the fix, and how much cash could be released?

---

## Headline

| | |
|---|---|
| Orders | 91,746 |
| Order value (EUR) | €652.9m |
| Weighted actual DSO (paid invoices) | 44.1 days |
| Weighted contractual terms | 54.5 days |

Company-average DSO looks **better** than terms. Leakage sits in the **late, blocked, and disputed** cases, not in the average.

---

## Top three leakage points

Ranked by **cash locked** (`value × extra days / 365`). Orders can sit in more than one leak; do not add the four cash figures as unique euros.

### 1. Collection lag after payment terms

| | |
|---|---|
| **Owner** | AR Collections Lead |
| **Orders** | 56,046 |
| **Value involved** | €388.8m |
| **Cash locked** | **€96.9m** |
| **Interest @ 6%** | €5.8m per year |

Invoices paid later than contracted terms, or still open past terms. This is the main cash lever. Concentrated in **EMEA** and **external customers**. Largest business area: **Power Tools**.

**Action:** Prioritise overdue open AR and chronic late payers in EMEA / Power Tools. Align collections with actual terms, not with the healthy company-average DSO.

### 2. Dispute / rework loops

| | |
|---|---|
| **Owner** | AR Dispute Manager (Sales contributing) |
| **Orders** | 22,474 (24.5% of orders) |
| **Value involved** | €178.4m |
| **Cash locked** | **€4.5m** |

Price changes, material changes, and order rejects. Volume is high; extra days versus clean peers are the cash cost.

**Action:** Cut invoice errors (price, material) at order entry. Give Sales a named SLA with AR on open disputes.

### 3. Holds (delivery / credit-style)

| | |
|---|---|
| **Owner** | Credit Manager / Order Management |
| **Orders** | 6,482 |
| **Value involved** | €46.7m |
| **Cash locked** | **€1.9m** |

Holds add about 7–8 days versus orders with no hold. **True credit-limit / compliance blocks are almost none** (4 orders). Most holds are operational (customer service, political, unconfirmed).

**Action:** Do not treat every hold as a credit failure. Clear operational blocks faster. Keep credit checks as a control.

---

## Also on the dashboard (not top-3 cash)

**Billing lag** — 18,915 orders, €128m flagged, only **€1.1m** cash locked. Many cases, few extra days (~2 when late). Owner: **Billing / Order-to-Invoice Lead**. Watch unbilled goods issue; it is not the main cash programme.

---

## Cash-acceleration case

If **collection extra days versus terms** were cut to zero:

- Expected cash released ≈ **€97m**  
- Annual interest avoided @ 6% ≈ **€5.8m**

This is a **scenario**, not a forecast. It assumes no loss of sales and no change in credit risk.

A 10-day cut on the same late/open book is a more realistic programme target; scale linearly from the €97m full-gap figure.

---

## Where it sits

| Cut | Finding |
|---|---|
| Region | **EMEA** holds most value and most collection cash |
| Segment | **External** customers (~€94m collection cash vs ~€3m internal) |
| Area | **Power Tools**, then Agriculture, Building Materials |

---

## Method (one line)

Celonis-style process stages from the event log; SQL joins on `Sales Order ID` and on `date + currency` to ECB rates; Power BI for segment / region cut.

---

## Limits

Sample / training-style O2C data, not a live SAP extract. Amounts treated as sales-org currency, then converted to EUR. Classic accounting DSO (AR stock ÷ credit sales) was not used; invoice-to-cash and cash-locked days were used instead.
