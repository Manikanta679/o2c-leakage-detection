"""
O2C Leakage Detection — Step 4
Author: Manikanta Engalligi

Load the three raw files into SQLite and build the star schema.
"""

from __future__ import annotations

import csv
import sqlite3
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(r"C:\Users\Manikanta\Desktop\Masters Projects\O2C Leakage")
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
DB_PATH = CLEAN / "o2c_leakage.db"
SQL_PATH = ROOT / "sql" / "02_build_star.sql"

REGION = {
    "USA": "AMER",
    "Mexico": "AMER",
    "Canada": "AMER",
    "Brazil": "AMER",
    "Colombia": "AMER",
    "China": "APAC",
    "India": "APAC",
    "Malaysia": "APAC",
    "Australia": "APAC",
    "Singapore": "APAC",
    "Indonesia": "APAC",
    "South Korea": "APAC",
    "New Zealand": "APAC",
}

SALES_ORG_CURRENCY = {
    "United Kingdom": "GBP",
    "USA": "USD",
    "United States": "USD",
    "Germany": "EUR",
    "Belgium": "EUR",
    "The Netherlands": "EUR",
    "Italy": "EUR",
    "Ireland": "EUR",
    "Austria": "EUR",
    "France": "EUR",
    "Spain": "EUR",
    "Norway": "NOK",
    "India": "INR",
    "Malaysia": "MYR",
    "Mexico": "MXN",
    "Australia": "AUD",
    "South Korea": "KRW",
}


def region_for(country: str) -> str:
    return REGION.get(country, "EMEA")


def parse_customer(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    if " - " in text:
        name, suffix = text.rsplit(" - ", 1)
        suffix = suffix.strip()
        if suffix.isdigit():
            return suffix, name.strip()
    return text, text


def load_events(con: sqlite3.Connection) -> int:
    con.execute("DROP TABLE IF EXISTS raw_event")
    con.execute(
        """
        CREATE TABLE raw_event (
            sales_order_id TEXT,
            activity TEXT,
            event_ts TEXT,
            automation TEXT,
            created_by TEXT
        )
        """
    )
    path = RAW / "OTC_Events_900k.csv"
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for rec in reader:
            rows.append(
                (
                    rec["Sales Order ID"].strip(),
                    rec["Activity"].strip(),
                    rec["Timestamp"].strip(),
                    rec["Automation"].strip() or None,
                    rec["CreatedBy"].strip() or None,
                )
            )
    con.executemany("INSERT INTO raw_event VALUES (?,?,?,?,?)", rows)
    return len(rows)


def load_cases(con: sqlite3.Connection) -> int:
    con.execute("DROP TABLE IF EXISTS raw_case")
    con.execute(
        """
        CREATE TABLE raw_case (
            sales_order_id TEXT,
            business_area TEXT,
            order_value REAL,
            company_code TEXT,
            customer_raw TEXT,
            customer_id TEXT,
            customer_name TEXT,
            customer_country TEXT,
            customer_group TEXT,
            delivery_block TEXT,
            item_category TEXT,
            material_group TEXT,
            payment_term TEXT,
            sales_org TEXT,
            order_type TEXT,
            kpi_on_time_delivery TEXT,
            kpi_paid_on_time TEXT,
            kpi_price_changed TEXT,
            kpi_material_changed TEXT
        )
        """
    )
    path = RAW / "OTC_Cases_92k.csv"
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for rec in reader:
            customer_id, customer_name = parse_customer(rec["SO: Customer"])
            rows.append(
                (
                    rec["Sales Order ID"].strip(),
                    rec["SO: Business Area"].strip(),
                    float(rec["SO: Value"]),
                    rec["SO: Company Code"].strip(),
                    rec["SO: Customer"].strip(),
                    customer_id,
                    customer_name,
                    rec["SO: Customer Country"].strip(),
                    rec["SO: Customer Group"].strip(),
                    rec["SO: Delivery Block"].strip(),
                    rec["SO: Item Category"].strip(),
                    rec["SO: Material Group"].strip(),
                    rec["SO: Payment term"].strip(),
                    rec["SO: Sales Org"].strip(),
                    rec["SO: Type"].strip(),
                    rec["KPI: On Time Delivery"].strip(),
                    rec["KPI: Paid On Time"].strip(),
                    rec["KPI: Price Changed"].strip(),
                    rec["KPI: Material Changed"].strip(),
                )
            )
    con.executemany(
        """
        INSERT INTO raw_case VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    return len(rows)


def load_fx(con: sqlite3.Connection) -> int:
    con.execute("DROP TABLE IF EXISTS raw_fx")
    con.execute(
        """
        CREATE TABLE raw_fx (
            rate_date TEXT,
            currency TEXT,
            units_per_eur REAL
        )
        """
    )
    path = RAW / "eurofxref-hist.csv"
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for rec in reader:
            rate_date = (rec.get("Date") or "").strip()
            if not rate_date:
                continue
            for currency, raw_val in rec.items():
                if currency in (None, "", "Date"):
                    continue
                currency = currency.strip()
                if not currency:
                    continue
                val = (raw_val or "").strip()
                if val in ("", "N/A"):
                    continue
                try:
                    rate = float(val)
                except ValueError:
                    continue
                if rate <= 0:
                    continue
                rows.append((rate_date, currency, rate))
    con.executemany("INSERT INTO raw_fx VALUES (?,?,?)", rows)
    return len(rows)


def load_maps(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS map_region")
    con.execute("CREATE TABLE map_region (customer_country TEXT PRIMARY KEY, region TEXT)")
    countries = [
        row[0]
        for row in con.execute(
            "SELECT DISTINCT customer_country FROM raw_case ORDER BY 1"
        )
    ]
    con.executemany(
        "INSERT INTO map_region VALUES (?,?)",
        [(c, region_for(c)) for c in countries],
    )

    con.execute("DROP TABLE IF EXISTS map_sales_org_currency")
    con.execute(
        """
        CREATE TABLE map_sales_org_currency (
            sales_org TEXT PRIMARY KEY,
            currency TEXT,
            is_eur_area INTEGER
        )
        """
    )
    orgs = [row[0] for row in con.execute("SELECT DISTINCT sales_org FROM raw_case ORDER BY 1")]
    mapped = []
    for org in orgs:
        currency = SALES_ORG_CURRENCY[org]
        mapped.append((org, currency, 1 if currency == "EUR" else 0))
    con.executemany("INSERT INTO map_sales_org_currency VALUES (?,?,?)", mapped)

    con.execute("DROP TABLE IF EXISTS map_calendar")
    con.execute(
        """
        CREATE TABLE map_calendar (
            date TEXT PRIMARY KEY,
            year INTEGER,
            quarter INTEGER,
            month INTEGER,
            month_name TEXT,
            is_weekend INTEGER
        )
        """
    )
    start = date(2021, 12, 1)
    end = date(2024, 12, 31)
    cal = []
    day = start
    names = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
    while day <= end:
        cal.append(
            (
                day.isoformat(),
                day.year,
                (day.month - 1) // 3 + 1,
                day.month,
                names[day.month - 1],
                1 if day.weekday() >= 5 else 0,
            )
        )
        day += timedelta(days=1)
    con.executemany("INSERT INTO map_calendar VALUES (?,?,?,?,?,?)", cal)


def apply_fx(con: sqlite3.Connection) -> None:
    rates: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for rate_date, currency, units in con.execute(
        "SELECT rate_date, currency, units_per_eur FROM dim_fx_rate ORDER BY currency, rate_date"
    ):
        rates[currency].append((rate_date, units))

    updates = []
    for sales_order_id, currency, fx_date, order_value in con.execute(
        "SELECT sales_order_id, currency, fx_date, order_value FROM fact_order"
    ):
        if currency == "EUR":
            updates.append((sales_order_id, 1.0, order_value))
            continue
        series = rates.get(currency, [])
        if not series or not fx_date:
            continue
        dates = [item[0] for item in series]
        idx = bisect_right(dates, fx_date) - 1
        if idx < 0:
            continue
        units = series[idx][1]
        updates.append((sales_order_id, units, order_value / units))

    con.execute("DROP TABLE IF EXISTS tmp_fx")
    con.execute(
        """
        CREATE TABLE tmp_fx (
            sales_order_id TEXT PRIMARY KEY,
            units_per_eur REAL,
            order_value_eur REAL
        )
        """
    )
    con.executemany("INSERT INTO tmp_fx VALUES (?,?,?)", updates)
    con.execute(
        """
        UPDATE fact_order
        SET units_per_eur = t.units_per_eur,
            order_value_eur = t.order_value_eur
        FROM tmp_fx t
        WHERE t.sales_order_id = fact_order.sales_order_id
        """
    )
    con.execute("DROP TABLE tmp_fx")


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")
    started = datetime.now()
    print("Loading events...")
    n_events = load_events(con)
    print(f"  raw_event {n_events:,}")
    print("Loading cases...")
    n_cases = load_cases(con)
    print(f"  raw_case {n_cases:,}")
    print("Loading ECB rates...")
    n_fx = load_fx(con)
    print(f"  raw_fx {n_fx:,}")
    print("Loading maps...")
    load_maps(con)
    con.commit()

    print("Building star schema...")
    sql = SQL_PATH.read_text(encoding="utf-8")
    con.executescript(sql)
    con.commit()

    print("Applying FX join (date + currency)...")
    apply_fx(con)
    con.commit()

    print("Checks")
    checks = [
        ("fact_event", "SELECT COUNT(*) FROM fact_event"),
        ("fact_order", "SELECT COUNT(*) FROM fact_order"),
        ("event-order match",
         "SELECT COUNT(*) FROM fact_event e LEFT JOIN fact_order o ON o.sales_order_id = e.sales_order_id WHERE o.sales_order_id IS NULL"),
        ("orders with EUR value",
         "SELECT COUNT(*) FROM fact_order WHERE order_value_eur IS NOT NULL"),
        ("billing lag", "SELECT SUM(flag_billing_lag) FROM fact_order"),
        ("dispute rework", "SELECT SUM(flag_dispute_rework) FROM fact_order"),
        ("hold", "SELECT SUM(flag_hold) FROM fact_order"),
        ("credit-class hold", "SELECT SUM(flag_credit_hold) FROM fact_order"),
    ]
    for label, q in checks:
        value = con.execute(q).fetchone()[0]
        print(f"  {label}: {value}")

    elapsed = datetime.now() - started
    print(f"Database: {DB_PATH}")
    print(f"Elapsed: {elapsed}")
    con.close()


if __name__ == "__main__":
    main()
