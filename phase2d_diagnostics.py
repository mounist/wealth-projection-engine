"""Phase 2d: avoid SQL WHERE filtering (immutabledict bug). Pull raw, filter in pandas."""
import wrds
import pandas as pd

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 240)

db = wrds.Connection(wrds_username="mounist")

# Step 1: Pull ALL tfz_idx rows — no WHERE clause, filter in pandas
print("=" * 70)
print("(1) All crsp.tfz_idx rows (filtering in pandas)")
print("=" * 70)

tfz_idx = db.raw_sql("SELECT * FROM crsp.tfz_idx")
print(f"Total rows: {len(tfz_idx)}")
print(f"Columns: {list(tfz_idx.columns)}")
print()

# Filter to FIXEDTERM 10-Year
mask = (tfz_idx['tidxfam'] == 'FIXEDTERM') & \
       (tfz_idx['ttermlbl'].str.contains('10-Year', na=False))
ten_y = tfz_idx[mask]
print("FIXEDTERM 10-Year rows:")
print(ten_y.to_string())
print()

if len(ten_y) > 0:
    ten_y_id = ten_y['kytreasnox'].iloc[0]
    print(f"10Y kytreasnox = {ten_y_id}")
else:
    print("No 10-Year match found. Showing all FIXEDTERM rows:")
    print(tfz_idx[tfz_idx['tidxfam'] == 'FIXEDTERM'].to_string())

# Step 2: List all tables in crsp schema, filter in pandas
print()
print("=" * 70)
print("(2) All crsp tables (filtering for tfz* in pandas)")
print("=" * 70)
all_tables = db.raw_sql("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'crsp'
""")
tfz_tables = all_tables[all_tables['table_name'].str.startswith('tfz')]
print("Tables starting with 'tfz':")
print(tfz_tables.to_string())

db.close()
