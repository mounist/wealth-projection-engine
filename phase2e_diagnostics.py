"""Phase 2e: verify crsp.tfz_mth_ft for kytreasnox=2000007 (FIXEDTERM 10Y Nominal)."""
import wrds
import pandas as pd

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 240)

db = wrds.Connection(wrds_username="mounist")

# Pull ALL rows from crsp.tfz_mth_ft — filter in pandas (no SQL WHERE)
print("=" * 70)
print("(1) Pulling crsp.tfz_mth_ft (full table)")
print("=" * 70)
tfz = db.raw_sql("SELECT * FROM crsp.tfz_mth_ft")
print(f"Total rows: {len(tfz)}")
print(f"Columns: {list(tfz.columns)}")

# Filter to 10Y
ten_y = tfz[tfz["kytreasnox"] == 2000007].copy()
ten_y["mcaldt"] = pd.to_datetime(ten_y["mcaldt"])
ten_y = ten_y.sort_values("mcaldt").reset_index(drop=True)

print()
print("=" * 70)
print("(2) kytreasnox = 2000007 subset")
print("=" * 70)
print(f"Rows: {len(ten_y)}")
if len(ten_y):
    print(f"Date range: {ten_y['mcaldt'].min().date()}  →  {ten_y['mcaldt'].max().date()}")
    # Uniqueness: one row per (kytreasnox, month)
    months = ten_y["mcaldt"].dt.to_period("M")
    dup = months.duplicated().sum()
    print(f"Duplicate months: {dup}")
    print(f"Unique months: {months.nunique()}  (should equal row count {len(ten_y)})")

print()
print("First 5 rows:")
print(ten_y.head().to_string())
print()
print("Last 5 rows:")
print(ten_y.tail().to_string())

# Summary statistics on return column (whichever is the adjusted total return)
print()
print("=" * 70)
print("(3) Summary stats on return-like columns")
print("=" * 70)
return_cols = [c for c in ten_y.columns
               if 'ret' in c.lower() or 'yld' in c.lower()]
print(f"Return-like columns: {return_cols}")
for col in return_cols:
    if ten_y[col].dtype in ['float64', 'float32']:
        print(f"\n{col}:")
        print(ten_y[col].describe())

db.close()
