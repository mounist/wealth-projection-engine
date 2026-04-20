"""Phase 2b: find the INDEX-LEVEL monthly Treasury total return table + 10Y id."""
import wrds
import pandas as pd

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 220)

print("=" * 70)
print("Connecting to WRDS as mounist ...")
print("=" * 70)
db = wrds.Connection(wrds_username="mounist")


def run(label, sql):
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    try:
        df = db.raw_sql(sql)
        print(df.to_string())
        return df
    except Exception as e:
        print(f"ERROR: {e}")
        return None


# Step A: candidate tables
a = run(
    "(A) crsp tables matching %tfz% / %trs% / %idx%",
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='crsp'
      AND (table_name LIKE '%tfz%' OR table_name LIKE '%trs%' OR table_name LIKE '%idx%')
    ORDER BY table_name
    """,
)

# Step C: index families in crsp.tfz_idx (using ttermmin/ttermmax/tidxfam/ttermlbl/tseldesc)
c = run(
    "(C) crsp.tfz_idx — distinct index families & term labels",
    """
    SELECT DISTINCT tidxfam, ttermmin, ttermmax, ttermlbl, tseldesc
    FROM crsp.tfz_idx
    ORDER BY tidxfam, ttermmin
    """,
)

# Also check tfz_idx full column list (since user says columns are ttermmin/ttermmax)
run(
    "(C2) crsp.tfz_idx — column list",
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='crsp' AND table_name='tfz_idx'
    ORDER BY ordinal_position
    """,
)

# Step B: for each candidate index-monthly-looking table, show columns
if a is not None and len(a):
    candidates = [
        t for t in a["table_name"].tolist()
        if ("idx" in t and ("mth" in t or "month" in t))
        or t in ("tfz_idx_mth", "tfz_mthidx", "tfz_mth_idx")
    ]
    print("\n" + "=" * 70)
    print(f"(B) candidate index-monthly tables to inspect: {candidates}")
    print("=" * 70)
    for tbl in candidates:
        run(
            f"(B) columns of crsp.{tbl}",
            f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='crsp' AND table_name='{tbl}'
            ORDER BY ordinal_position
            """,
        )

# Step D: find 10Y constant-maturity rows in crsp.tfz_idx
d = run(
    "(D) crsp.tfz_idx — rows where ttermmin/ttermmax suggest ~10Y",
    """
    SELECT kytreasnox, tidxfam, ttermmin, ttermmax, ttermlbl, tseldesc
    FROM crsp.tfz_idx
    WHERE (ttermmin BETWEEN 9 AND 11 OR ttermmax BETWEEN 9 AND 11)
       OR ttermlbl ILIKE '%10%'
       OR tseldesc ILIKE '%10%'
    ORDER BY tidxfam, ttermmin
    """,
)

# Step E: sample rows from candidate monthly-index table for a likely 10Y id
# Try the most common name; if that fails show what we found in B.
print("\n" + "=" * 70)
print("(E) sample rows — attempt with likely table/id combos")
print("=" * 70)
if d is not None and len(d):
    id_candidates = d["kytreasnox"].unique().tolist()[:5]
    for tbl in ("tfz_idx_mth", "tfz_mthidx"):
        for kid in id_candidates:
            q = f"""
                SELECT *
                FROM crsp.{tbl}
                WHERE kytreasnox = {kid}
                ORDER BY mcaldt DESC
                LIMIT 3
            """
            print(f"\n--- crsp.{tbl} kytreasnox={kid} ---")
            try:
                df = db.raw_sql(q)
                print(df.to_string())
            except Exception as e:
                print(f"ERROR: {e}")

db.close()
print("\nDone.")
