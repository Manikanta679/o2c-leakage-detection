"""Build docs/O2C_Leakage_Brief.pdf — Author: Manikanta Engalligi."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT = Path(r"C:\Users\Manikanta\Desktop\Masters Projects\O2C Leakage\docs\O2C_Leakage_Brief.pdf")
NAVY = HexColor("#0B1F3A")
TEAL = HexColor("#1F6F8B")
GOLD = HexColor("#C4A35A")
GRAY = HexColor("#4A5568")
LINE = HexColor("#D6DDE5")
LIGHT = HexColor("#F4F7FA")


def header(c, page, total=5):
    w, h = A4
    c.setFillColor(NAVY)
    c.rect(0, h - 18 * mm, w, 18 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Times-Bold", 10)
    c.drawString(18 * mm, h - 11 * mm, "O2C Leakage Detection  |  Decision brief")
    c.setFont("Times-Roman", 9)
    c.drawRightString(w - 18 * mm, h - 11 * mm, "Manikanta Engalligi")
    c.setFillColor(GRAY)
    c.setFont("Times-Roman", 8)
    c.drawString(18 * mm, 10 * mm, "Confidential for portfolio use  |  Sample O2C data + ECB FX  |  Snapshot 2024-10-28")
    c.drawRightString(w - 18 * mm, 10 * mm, f"{page} / {total}")


def section(c, x, y, title):
    c.setFillColor(TEAL)
    c.rect(x, y - 1, 6, 10, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 13)
    c.drawString(x + 12, y, title)
    return y - 8 * mm


def body(c, x, y, text, size=10, leading=13, width=175 * mm):
    c.setFillColor(GRAY)
    c.setFont("Times-Roman", size)
    words = text.split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, "Times-Roman", size) > width:
            c.drawString(x, y, line)
            y -= leading
            line = w
        else:
            line = test
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def kpi_box(c, x, y, w, h, label, value):
    c.setFillColor(LIGHT)
    c.setStrokeColor(LINE)
    c.roundRect(x, y - h, w, h, 3, fill=1, stroke=1)
    c.setFillColor(GRAY)
    c.setFont("Times-Roman", 8)
    c.drawString(x + 4 * mm, y - 6 * mm, label)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(x + 4 * mm, y - 13 * mm, value)


def leak_row(c, y, rank, name, owner, cash, orders):
    x = 18 * mm
    c.setFillColor(LIGHT if rank % 2 else white)
    c.rect(x, y - 14 * mm, 174 * mm, 14 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.circle(x + 6 * mm, y - 7 * mm, 4, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 9)
    c.drawCentredString(x + 6 * mm, y - 8.5 * mm, str(rank))
    c.setFont("Times-Bold", 10)
    c.drawString(x + 14 * mm, y - 6 * mm, name)
    c.setFont("Times-Roman", 8)
    c.setFillColor(GRAY)
    c.drawString(x + 14 * mm, y - 11 * mm, owner)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 11)
    c.drawRightString(x + 170 * mm, y - 6 * mm, cash)
    c.setFont("Times-Roman", 8)
    c.setFillColor(GRAY)
    c.drawRightString(x + 170 * mm, y - 11 * mm, orders)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=A4)
    w, h = A4
    x = 18 * mm

    # Page 1 — cover + question
    header(c, 1)
    y = h - 32 * mm
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 22)
    c.drawString(x, y, "Where does revenue leak")
    y -= 8 * mm
    c.drawString(x, y, "between confirmation and cash?")
    y -= 10 * mm
    c.setFont("Times-Italic", 11)
    c.setFillColor(TEAL)
    c.drawString(x, y, "Working-capital diagnostic  ·  Order-to-Cash  ·  SQL + Power BI")
    y -= 12 * mm
    kpi_box(c, x, y, 42 * mm, 18 * mm, "Orders", "91,746")
    kpi_box(c, x + 44 * mm, y, 42 * mm, 18 * mm, "Order value (EUR)", "€652.9m")
    kpi_box(c, x + 88 * mm, y, 42 * mm, 18 * mm, "Actual DSO", "44.1 days")
    kpi_box(c, x + 132 * mm, y, 42 * mm, 18 * mm, "Contract terms", "54.5 days")
    y -= 28 * mm
    y = section(c, x, y, "The question")
    y = body(
        c, x, y,
        "Average DSO looks healthy: paid invoices clear in 44 days against 54 days of contractual terms. "
        "The leak is not the average. It is the late, blocked, and disputed cases. "
        "This brief names the top three leakage points, a process owner for each, and the cash-acceleration case.",
    )
    y -= 3 * mm
    y = section(c, x, y, "Top three leakage points (by cash locked)")
    y -= 2 * mm
    leak_row(c, y, 1, "Collection lag after payment terms", "Owner: AR Collections Lead", "€96.9m", "56,046 orders  ·  €388.8m involved")
    y -= 16 * mm
    leak_row(c, y, 2, "Dispute / rework loops", "Owner: AR Dispute Manager (Sales contributing)", "€4.5m", "22,474 orders  ·  €178.4m involved")
    y -= 16 * mm
    leak_row(c, y, 3, "Holds (delivery / credit-style)", "Owner: Credit Manager / Order Management", "€1.9m", "6,482 orders  ·  mostly operational, not credit limit")
    y -= 22 * mm
    y = section(c, x, y, "Cash-acceleration case")
    y = body(
        c, x, y,
        "If extra days versus payment terms were cut to zero, expected cash released is about €97 million. "
        "At a 6% cost of capital that is about €5.8 million of annual interest. This is a scenario, not a forecast. "
        "A 10-day cut on the same late/open book is a more realistic programme target.",
    )
    y -= 2 * mm
    y = body(
        c, x, y,
        "Formula: cash locked = order value (EUR) × extra days / 365. Extra days are defined per leak "
        "(late vs terms; dispute vs clean peers; hold vs no-hold peers; goods-issue to invoice).",
        size=9,
    )
    c.showPage()

    # Page 2 — actions + cuts
    header(c, 2)
    y = h - 32 * mm
    y = section(c, x, y, "What to do")
    items = [
        ("1  Collections", "Work overdue open AR and chronic late payers first in EMEA and Power Tools. Do not manage to the healthy company-average DSO."),
        ("2  Disputes", "Stop invoice errors at order entry (price, material). Give Sales a named SLA with AR on open dispute loops."),
        ("3  Holds", "Do not treat every hold as a credit failure. True credit-limit blocks are almost none (4 orders). Clear operational blocks faster; keep credit as a control."),
        ("Billing (watch)", "18,915 orders and €128m flagged, but only €1.1m cash locked — extra days are short. Owner: Billing / Order-to-Invoice Lead."),
    ]
    for title, text in items:
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 11)
        c.drawString(x, y, title)
        y -= 5 * mm
        y = body(c, x, y, text, size=10)
        y -= 3 * mm
    y = section(c, x, y, "Where it sits")
    y = body(c, x, y, "Region: EMEA holds most value and most collection cash. AMER next. APAC is smaller in value but slower on invoice-to-cash.")
    y = body(c, x, y, "Segment: External customers (~€94m collection cash) versus internal (~€3m).")
    y = body(c, x, y, "Business area: Power Tools, then Agriculture, then Building Materials.")
    y -= 4 * mm
    y = section(c, x, y, "O2C path in SQL (vw_o2c_case_timeline)")
    y = body(
        c, x, y,
        "One row per sales order. Columns read left to right as the process: Create Sales Order → Confirmed Delivery Date → Issue Goods → Create Invoice → Invoice Due Date → Clear Invoice. "
        "Holding and rework dates sit beside the happy path so missing next documents stay visible. Query: sql/04_o2c_timeline.sql.",
    )
    c.setFillColor(NAVY)
    c.setFont("Courier", 8)
    lines = [
        "SELECT sales_order_id, ts_create_sales_order, ts_confirmed_delivery,",
        "       ts_issue_goods, ts_create_invoice, ts_invoice_due, ts_clear_invoice",
        "FROM vw_o2c_case_timeline;",
    ]
    y -= 2 * mm
    c.setFillColor(LIGHT)
    c.rect(x, y - 18 * mm, 174 * mm, 20 * mm, fill=1, stroke=0)
    c.setFillColor(NAVY)
    ty = y - 6 * mm
    for line in lines:
        c.drawString(x + 4 * mm, ty, line)
        ty -= 4 * mm
    c.showPage()

    # Page 3 — dashboard map (stands in + instructions for PBI export)
    header(c, 3)
    y = h - 32 * mm
    y = section(c, x, y, "Power BI report — four pages")
    y = body(
        c, x, y,
        "File: powerbi/O2C_Leakage.pbix. Export a visual pack from Power BI Desktop: File → Export → Export to PDF "
        "(or Print → Microsoft Print to PDF). Combine with this brief for applications.",
    )
    y -= 3 * mm
    pages = [
        ("1  Executive", "KPIs (orders, €653m, DSO 44 vs terms 54). Bar of cash locked by leak. Owner table. Cash by region. Slicers do not move the company snapshot; they move the region chart."),
        ("2  Process", "Events by stage group (fulfilment largest, hold smallest). Average days: goods→invoice ~0, invoice→cash ~46, confirm→cash ~41. Happy-path share vs extra steps."),
        ("3  Leakage", "Order counts on flags. Cash by leak. Delivery-block reasons (No block dominates; credit limit is rare). Collection cash by business area (Power Tools)."),
        ("4  Segment & region", "Matrix region × customer group. Collection cash by area and region. Customer ranking by collection cash locked."),
    ]
    for title, text in pages:
        c.setFillColor(TEAL)
        c.rect(x, y - 1, 4, 9, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 11)
        c.drawString(x + 8, y, title)
        y -= 5 * mm
        y = body(c, x, y, text, size=10)
        y -= 4 * mm
    y = section(c, x, y, "Method")
    y = body(c, x, y, "Celonis Academy trained the process vocabulary (case, activity, timestamp, variant, waiting time). Analysis data is not a Celonis extract.")
    y = body(c, x, y, "Sources: QPR Order-to-Cash event log and case attributes; ECB euro reference rates. Joins: Sales Order ID (91,746/91,746); date + sales-org currency to ECB.")
    y = body(c, x, y, "Python loads files into SQLite. Star schema, leak flags, and DSO marts are SQL (sql/02_build_star.sql, sql/03_metrics.sql).")
    y -= 3 * mm
    y = section(c, x, y, "Limits")
    y = body(c, x, y, "Public sample process data, not a live SAP client extract. Amounts treated as sales-org currency then converted to EUR. Classic AR-stock DSO is not used. Leak cash figures can overlap — do not add them as unique euros.")
    c.showPage()

    # Page 4 — how to rebuild
    header(c, 4)
    y = h - 32 * mm
    y = section(c, x, y, "Rebuild locally")
    steps = [
        "1. Clone the repo. Download OTC_Events_900k.csv, OTC_Cases_92k.csv, and ECB eurofxref-hist.csv into data/raw/ (URLs in README).",
        "2. python sql/01_load_and_build.py",
        "3. In DB Browser, run sql/03_metrics.sql and sql/04_o2c_timeline.sql if you rebuilt only part of the pipeline.",
        "4. Open powerbi/O2C_Leakage.pbix in Power BI Desktop.",
        "5. Optional: File → Export → PDF for the four report pages; keep this PDF as the narrative.",
    ]
    for s in steps:
        y = body(c, x, y, s, size=10)
        y -= 2 * mm
    y -= 2 * mm
    y = section(c, x, y, "Credit")
    y = body(c, x, y, "Author of analysis, SQL model, Power BI structure, and this brief: Manikanta Engalligi.")
    y = body(c, x, y, "Event log samples: QPR ProcessAnalyzer. FX: European Central Bank. Process-intelligence training: Celonis Academy.")
    c.showPage()

    # Page 5 — empty template note for PBI print
    header(c, 5)
    y = h - 32 * mm
    y = section(c, x, y, "Attach Power BI pages here")
    y = body(
        c, x, y,
        "Print or export the four pages from Power BI Desktop and keep them behind this brief, in this order: Executive, Process, Leakage, Segment & region. "
        "Do not add extra decoration. The charts already carry the SI story: cash first, then process, then cut by segment and region.",
    )
    y -= 6 * mm
    for name in ("Executive", "Process", "Leakage", "Segment & region"):
        c.setStrokeColor(LINE)
        c.setFillColor(LIGHT)
        c.roundRect(x, y - 28 * mm, 174 * mm, 26 * mm, 3, fill=1, stroke=1)
        c.setFillColor(GRAY)
        c.setFont("Times-Italic", 10)
        c.drawCentredString(w / 2, y - 15 * mm, f"Power BI page — {name}  (export from O2C_Leakage.pbix)")
        y -= 32 * mm
    c.save()
    print("Wrote", OUT, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    build()
