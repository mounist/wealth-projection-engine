"""Phase 2 diagnostics: discover correct WRDS schemas/columns for Treasury + CPI."""
import wrds
import pandas as pd

pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)

print("=" * 70)
print("Connecting to WRDS as mounist ...")
print("=" * 70)
db = wrds.Connection(wrds_username="mounist")

# ---------------------------------------------------------------------------
# (1) CRSP Treasury: find 10Y constant-maturity index + verify columns
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("(1a) crsp.tfz_idx — treasury index families, filter termmin>=9 & termmax<=11")
print("=" * 70)
q1a = """
    SELECT kytreasnox, tidxfam, termmin, termmax
    FROM crsp.tfz_idx
    WHERE termmin >= 9 AND termmax <= 11
    ORDER BY tidxfam, kytreasnox
"""
try:
    df = db.raw_sql(q1a)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(1b) crsp.tfz_mth — column list")
print("=" * 70)
q1b = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='crsp' AND table_name='tfz_mth'
    ORDER BY ordinal_position
"""
try:
    df = db.raw_sql(q1b)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(1c) crsp.tfz_idx — column list (to understand schema)")
print("=" * 70)
q1c = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='crsp' AND table_name='tfz_idx'
    ORDER BY ordinal_position
"""
try:
    df = db.raw_sql(q1c)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(1d) Sample rows from crsp.tfz_mth for a candidate 10Y kytreasnox")
print("=" * 70)
q1d = """
    SELECT *
    FROM crsp.tfz_mth
    WHERE mcaldt BETWEEN '2020-01-01' AND '2020-12-31'
    LIMIT 5
"""
try:
    df = db.raw_sql(q1d)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

# ---------------------------------------------------------------------------
# (2) CPI: find right table + column in frb / frb_all
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("(2a) frb schema — tables matching %cpi%")
print("=" * 70)
q2a = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='frb' AND table_name ILIKE '%cpi%'
    ORDER BY table_name
"""
try:
    df = db.raw_sql(q2a)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(2b) frb_all schema — tables matching %cpi%")
print("=" * 70)
q2b = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='frb_all' AND table_name ILIKE '%cpi%'
    ORDER BY table_name
"""
try:
    df = db.raw_sql(q2b)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(2c) frb schema — all tables (in case CPI is named differently)")
print("=" * 70)
q2c = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='frb'
    ORDER BY table_name
"""
try:
    df = db.raw_sql(q2c)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("(2d) frb_all schema — all tables")
print("=" * 70)
q2d = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='frb_all'
    ORDER BY table_name
"""
try:
    df = db.raw_sql(q2d)
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

db.close()
print("\nDone.")
