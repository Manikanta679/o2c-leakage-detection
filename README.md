# Order-to-Cash (O2C) Leakage Detection

**Author:** Manikanta Engalligi  
**Role this proves:** finance–ops analyst (SQL + process mining method + Power BI)

Where does cash stick between **order confirmation** and **cash collection**?  
This project maps the O2C path, flags billing lag, dispute/rework, holds, and collection after terms, then quantifies **DSO-style days** and **cash locked** by customer segment and region.

Celonis Academy = **how to read a process** (case, activity, timestamp, variants).  
The numbers in this repo = **QPR O2C logs + ECB FX rates**, modelled in **SQL**, shown in **Power BI**.

---

## Quick facts

| | |
|---|---|
| Orders | 91,746 |
| Events | 900,113 |
| Order value | €652.9m (ECB-converted) |
| Main join | `Sales Order ID` (100% match) |
| Second join | invoice/order **date** + **currency** → ECB rate |
| Top cash leak | Collection after terms ≈ **€96.9m** |
| Then | Dispute / rework ≈ €4.5m; holds ≈ €1.9m |
| Dashboard | `powerbi/O2C_Leakage.pbix` (4 pages) |
| Decision page | `docs/08_executive_brief.md` and `docs/O2C_Leakage_Brief.pdf` |

---

## Repository map

```text
O2C Leakage/
├── README.md                 ← you are here
├── docs/                     ← method, dictionary, brief, PDF
├── sql/                      ← load + star schema + metrics + O2C timeline view
├── powerbi/
│   ├── O2C_Leakage.pbix      ← open this in Power BI Desktop
│   └── model/                ← CSVs for the model (optional reload)
└── data/
    ├── raw/                  ← CSVs you download (not in Git — too large)
    └── clean/                ← o2c_leakage.db after you run SQL (not in Git)
```

| File | Why it exists |
|---|---|
| `docs/01_data_lock.md` | Sources, size, merge keys |
| `docs/02_data_dictionary.md` | Every column |
| `docs/03_star_schema.md` | Facts and dimensions |
| `docs/05_metrics.md` | DSO and cash formulas |
| `docs/08_executive_brief.md` | Top 3 leaks, owner, cash case |
| `docs/O2C_Leakage_Brief.pdf` | Same story, for applications |
| `sql/01_load_and_build.py` | Loads CSVs into SQLite, runs SQL, applies FX |
| `sql/02_build_star.sql` | Star schema + leak flags |
| `sql/03_metrics.sql` | Cash / DSO marts |
| `sql/04_o2c_timeline.sql` | **`vw_o2c_case_timeline`** — one row per order, O2C dates left to right |

---

## O2C flow (what the SQL follows)

Happy path (one case = one sales order):

```text
Create Sales Order
        → Confirmed Delivery Date
                → Issue Goods
                        → Create Invoice
                                → Invoice Due Date
                                        → Clear Invoice
```

Exceptions (leakage):

- **Billing lag** — goods issued, invoice late or missing  
- **Dispute / rework** — price/material change, reject  
- **Hold** — delivery block or unblock event  
- **Collection lag** — cash after contractual terms  

That sequence is a **view** you can query:

```sql
SELECT
    sales_order_id,
    ts_create_sales_order,
    ts_confirmed_delivery,
    ts_issue_goods,
    ts_create_invoice,
    ts_invoice_due,
    ts_clear_invoice,
    days_goods_to_invoice,
    days_invoice_to_cash,
    days_confirm_to_cash
FROM vw_o2c_case_timeline
LIMIT 20;
```

Open `data/clean/o2c_leakage.db` in **DB Browser for SQLite** → **Execute SQL** → paste the query.

---

## How to run (from scratch)

### 1. Tools

- Python 3  
- [DB Browser for SQLite](https://sqlitebrowser.org) (optional, to inspect)  
- [Power BI Desktop](https://apps.microsoft.com/detail/9ntxr16hnw1t) (Windows)

### 2. Download data into `data/raw/`

| File | From |
|---|---|
| `OTC_Events_900k.csv` | [QPR sample event logs](https://files.qpr.com/releases/PASampleFiles/csv/OTC_Events_900k.csv) |
| `OTC_Cases_92k.csv` | [QPR case attributes](https://files.qpr.com/releases/PASampleFiles/csv/OTC_Cases_92k.csv) |
| `eurofxref-hist.csv` | Unzip [ECB eurofxref-hist.zip](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip) |

Page that lists the QPR files: [Sample Eventlog Files](https://wiki.onqpr.com/pa/index.php/Sample_Eventlog_Files).

### 3. Build the database

From the `O2C Leakage` folder:

```powershell
python sql/01_load_and_build.py
```

Then in DB Browser, open `data/clean/o2c_leakage.db` and run:

- `sql/03_metrics.sql`  
- `sql/04_o2c_timeline.sql`

(If you re-run the Python loader, run the two SQL files again.)

### 4. Open the dashboard

Open `powerbi/O2C_Leakage.pbix`.

Pages:

1. **Executive** — KPIs, leak ranking, owners, cash by region  
2. **Process** — stage mix, average days, happy path vs extra steps  
3. **Leakage** — flags, holds by reason, cash by business area  
4. **Segment & region** — region × customer group, top customers  

If Power BI asks to refresh CSVs, point it at `powerbi/model/` (re-export from SQLite if those files are missing).

---

## How to read the result (one minute)

1. Company-average DSO (**44 days**) is **better** than terms (**54 days**). Do not stop there.  
2. Cash is stuck in **late / open after terms** (~€97m equivalent).  
3. Owner: **AR Collections**. Then disputes (Sales + AR), then operational holds (not fake “credit crisis”).  
4. Cut: **EMEA**, **external customers**, **Power Tools**.

Full write-up: `docs/08_executive_brief.md`.

---

## Skills shown

- SQL joins (order / event / payment-style clearing dates)  
- Left/inner joins so **missing next documents** stay visible  
- DSO-style metrics and cash locked (`value × extra days / 365`)  
- Second dataset merge (ECB on date + currency)  
- Power BI star model and four-page ops–finance dashboard  
- Process-intelligence vocabulary from Celonis (without claiming a Celonis extract)

---

## Limits (honest)

- Public sample O2C data, not a live SAP company extract.  
- `SO: Value` has no currency in the source; sales org is mapped to ISO currency, then ECB.  
- Classic accounting DSO (AR stock ÷ credit sales) is not used; invoice-to-cash and cash-locked days are used instead.  
- Celonis is the **training method**, not the file source.

---

## License / credit

Analysis and documentation: **Manikanta Engalligi**.  
Raw logs: QPR ProcessAnalyzer samples. FX: European Central Bank.
