"""Reproduce the Root2Raj retail case study; downloads its public input if absent."""
from pathlib import Path
import hashlib
import json
import sqlite3
import urllib.request
import zipfile
from datetime import datetime, timezone
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
source = DATA / "Online Retail.xlsx"
if not source.exists():
    archive = DATA / "source.zip"
    urllib.request.urlretrieve(SOURCE_URL, archive)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            destination = (DATA / member.filename).resolve()
            if DATA.resolve() not in destination.parents:
                raise ValueError("Unsafe archive path")
        z.extractall(DATA)
print("Reading the historical retail dataset...", flush=True)
raw = pd.read_excel(source, engine="openpyxl")
expected = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
assert expected == set(raw.columns), "Unexpected input schema"
assert len(raw) == 541909, "Unexpected dataset version or incomplete download"
duplicate_count = int(raw.duplicated().sum())
df = raw.drop_duplicates().copy()
df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
df["StockCode"] = df["StockCode"].astype("string").str.strip()
df["Country"] = df["Country"].fillna("Unknown").astype("string")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
df["is_cancellation"] = df["InvoiceNo"].str.upper().str.startswith("C").fillna(False)
valid = (df["InvoiceDate"].notna() & df["InvoiceNo"].notna() & np.isfinite(df["Quantity"]) & np.isfinite(df["UnitPrice"]) & df["UnitPrice"].gt(0) & df["Quantity"].ne(0))
positive = valid & ~df["is_cancellation"] & df["Quantity"].gt(0)
credits = valid & df["is_cancellation"] & df["Quantity"].lt(0)
adjustments = valid & ~df["is_cancellation"] & df["Quantity"].lt(0)
df["record_type"] = "excluded"
df.loc[positive, "record_type"] = "sale"
df.loc[credits, "record_type"] = "cancellation_credit"
df.loc[adjustments, "record_type"] = "negative_adjustment"
df["line_value"] = df["Quantity"] * df["UnitPrice"]
df["month"] = df["InvoiceDate"].dt.strftime("%Y-%m")
commercial = df[df["record_type"].ne("excluded")].copy()
sales = df[positive].copy()
credit_rows = df[credits].copy()
known = sales[sales["CustomerID"].notna()]
gross = float(sales["line_value"].sum())
credit_value = float(-credit_rows["line_value"].sum())
adjustment_value = float(df.loc[adjustments, "line_value"].sum())
net = gross - credit_value + adjustment_value
orders = int(sales["InvoiceNo"].nunique())
customers = known.groupby("CustomerID")["line_value"].sum().sort_values(ascending=False)
known_revenue = float(customers.sum())
top_n = max(1, int(np.ceil(len(customers) * 0.1)))
concentration = float(customers.head(top_n).sum() / known_revenue * 100)
monthly = []
for month, group in commercial.groupby("month", sort=True):
    m_sales = group[group["record_type"].eq("sale")]
    m_credits = group[group["record_type"].eq("cancellation_credit")]
    monthly.append({"month": month, "gross_sales": round(float(m_sales["line_value"].sum()), 2), "credit_value": round(float(-m_credits["line_value"].sum()), 2), "net_recorded_value": round(float(group["line_value"].sum()), 2), "positive_invoices": int(m_sales["InvoiceNo"].nunique()), "partial_month": month == "2011-12"})
country_gross = sales.groupby("Country")["line_value"].sum().sort_values(ascending=False)
countries = [{"country": str(country), "gross_sales": round(float(value), 2), "gross_share_pct": round(float(value / gross * 100), 2)} for country, value in country_gross.head(8).items()]
product_sales = sales.groupby("StockCode")["line_value"].sum()
product_credits = -credit_rows.groupby("StockCode")["line_value"].sum()
credit_leaders = []
for code, value in product_credits.sort_values(ascending=False).head(8).items():
    descriptions = df.loc[df["StockCode"].eq(code), "Description"].dropna()
    label = str(descriptions.mode().iloc[0]) if len(descriptions) else str(code)
    credit_leaders.append({"stock_code": str(code), "description": label, "credit_value": round(float(value), 2), "gross_sales": round(float(product_sales.get(code, 0)), 2)})
raw_invoice = raw["InvoiceNo"].astype("string")
raw_positive = raw["Quantity"].gt(0) & raw["UnitPrice"].gt(0) & ~raw_invoice.str.upper().str.startswith("C").fillna(False)
raw_gross = float((raw.loc[raw_positive, "Quantity"] * raw.loc[raw_positive, "UnitPrice"]).sum())
audit = {"raw_rows": len(raw), "exact_duplicates_removed": duplicate_count, "rows_after_deduplication": len(df), "sale_rows": int(positive.sum()), "cancellation_credit_rows": int(credits.sum()), "negative_adjustment_rows": int(adjustments.sum()), "excluded_rows": int(df["record_type"].eq("excluded").sum()), "missing_customer_ids_raw": int(raw["CustomerID"].isna().sum()), "missing_customer_pct_raw": round(float(raw["CustomerID"].isna().mean() * 100), 2), "missing_descriptions_raw": int(raw["Description"].isna().sum()), "gross_sales_with_duplicates": round(raw_gross, 2), "gross_sales_duplicate_difference": round(raw_gross - gross, 2), "known_customer_gross_sales": round(known_revenue, 2)}
checks = {"expected_row_count": len(raw) == 541909, "row_partition_reconciles": sum(audit[k] for k in ["sale_rows", "cancellation_credit_rows", "negative_adjustment_rows", "excluded_rows"]) == len(df), "duplicates_reconcile": len(raw) - len(df) == duplicate_count, "value_reconciles": abs(net - float(commercial["line_value"].sum())) < 0.01, "monthly_value_reconciles": abs(net - sum(x["net_recorded_value"] for x in monthly)) < 0.1, "known_customer_coverage_bounded": 0 <= known_revenue <= gross + 0.01, "credit_value_nonnegative": credit_value >= 0}
assert all(checks.values()), checks
print("Saving local evidence and SQL validation...", flush=True)
with sqlite3.connect(OUT / "retail.sqlite") as connection:
    columns = ["InvoiceNo", "StockCode", "Quantity", "UnitPrice", "InvoiceDate", "Country", "record_type", "line_value", "month"]
    commercial[columns].to_sql("invoice_lines", connection, if_exists="replace", index=False, chunksize=10000)
    sql_net = connection.execute("SELECT SUM(line_value) FROM invoice_lines").fetchone()[0]
    checks["sqlite_value_reconciles"] = abs(sql_net - net) < 0.01
assert all(checks.values()), checks
result = {"title": "Retail revenue, with the credits left in", "source": {"name": "UCI Online Retail", "author": "Daqing Chen", "year": 2015, "doi": "10.24432/C5BW33", "url": "https://archive.ics.uci.edu/dataset/352/online%2Bretail", "download_url": SOURCE_URL, "license": "CC BY 4.0", "file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "period_start": df["InvoiceDate"].min().isoformat(), "period_end": df["InvoiceDate"].max().isoformat()}, "computed_at_utc": datetime.now(timezone.utc).isoformat(), "metrics": {"gross_positive_invoice_value": round(gross, 2), "cancellation_credit_value": round(credit_value, 2), "negative_adjustment_value": round(adjustment_value, 2), "net_recorded_invoice_value": round(net, 2), "credit_to_gross_value_pct": round(credit_value / gross * 100, 2), "positive_invoices": orders, "identified_purchasing_customers": len(customers), "top_decile_known_customer_revenue_share_pct": round(concentration, 2), "top_decile_customer_count": top_n, "known_customer_sales_coverage_pct": round(known_revenue / gross * 100, 2)}, "audit": audit, "checks": checks, "monthly": monthly, "countries": countries, "largest_credited_codes": credit_leaders, "limitations": ["Historical, single-retailer data from 2010-2011; not a description of today's retail market.", "Exact duplicate removal is an explicit assumption; identical invoice lines might represent legitimate repeats. The revenue sensitivity is reported.", "Cancellation invoice codes identify credits; no matching to original sale invoices has been established. Credit-to-gross value is not a product return rate.", "Recorded invoice values include non-merchandise codes and exclude invalid, zero-price or inconsistent lines; they are not audited accounts or profit.", "Customer concentration uses only identified purchasers and positive sales; missing customer IDs limit coverage.", "December 2011 ends on December 9 and must not be compared directly with full months.", "The data cannot establish why cancellations occurred or whether an intervention would improve performance."]}
(OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
(OUT / "validation.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
print(json.dumps({"metrics": result["metrics"], "audit": audit, "checks": checks}, indent=2), flush=True)
