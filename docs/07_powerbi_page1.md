# O2C Leakage Detection — Power BI Page 1 (Executive)

**Author:** Manikanta Engalligi  
**Step:** 7 of 8 — first report page only  
**File:** `powerbi/O2C_Leakage.pbix`

This page answers: how much cash is stuck, which leak is largest, who owns it.

Headline KPIs come from `mart_headline` (company snapshot).  
Leak ranking comes from `mart_leak_impact`.  
Region / segment charts come from `mart_order_kpi_full` so slicers work.

---

## Layout (top to bottom)

1. Title  
2. Four KPI cards  
3. Horizontal bar: cash locked by leak  
4. Table: leak, owner, orders, cash  
5. Two slicers: Region, Customer group  
6. Clustered bar: cash collection vs billing vs hold vs dispute, by region  

---

## Measures (create these once)

Table: `mart_order_kpi_full`

| Name | Formula |
|---|---|
| Orders | `COUNTROWS('mart_order_kpi_full')` |
| Order Value EUR | `SUM('mart_order_kpi_full'[order_value_eur])` |
| Cash Billing EUR | `SUM('mart_order_kpi_full'[cash_billing_eur])` |
| Cash Dispute EUR | `SUM('mart_order_kpi_full'[cash_dispute_eur])` |
| Cash Hold EUR | `SUM('mart_order_kpi_full'[cash_hold_eur])` |
| Cash Collection EUR | `SUM('mart_order_kpi_full'[cash_collection_eur])` |

Do not create measures on `mart_headline`. Use its columns on the KPI cards only.

---

## Expected numbers (no slicer)

| Card | Approx. |
|---|---|
| Orders | 91,746 |
| Order value | €652.9m |
| Actual DSO | 44.1 days |
| Best possible DSO | 54.5 days |

Largest bar: **Collection lag after terms** ≈ €96.9m.

---

## Next page (not now)

Page 2 — Process. Page 3 — Leakage deep dive. Page 4 — Segment and region.
