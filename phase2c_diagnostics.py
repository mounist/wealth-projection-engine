"""Phase 2c: pin down FIXEDTERM 10Y kytreasnox + correct index-monthly table."""
import wrds
import pandas as pd

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 240)

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


# (1) Explicit kytreasnox for FIXEDTERM 10-Year (Nominal)
q1 = run(
    "(1) FIXEDTERM 10-Year rows in crsp.tfz_idx",
    """
    SELECT kytreasnox, tidxfam, ttermlbl, ttermtype, tseldesc
    FROM crsp.tfz_idx
    WHERE tidxfam = 'FIXEDTERM'
      AND ttermlbl LIKE '%10-Year%'
    """,
)

# (2) Candidate index-monthly tables — single LIKE
q2 = run(
    "(2) crsp tables starting with 'tfz'",
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='crsp' AND table_name LIKE 'tfz%'
    ORDER BY table_name
    """,
)

# (3) Columns for each candidate table that looks like index-monthly
if q2 is not None and len(q2):
    all_tables = q2["table_name"].tolist()
    # Anything with idx + mth/month, plus any obviously index-level table
    candidates = [
        t for t in all_tables
        if ("idx" in t and ("mth" in t or "month" in t))
    ]
    # If nothing matches the strict pattern, fall back to ALL tfz tables with 'mth'
    if not candidates:
        candidates = [t for t in all_tables if "mth" in t or "month" in t]
    print("\n" + "=" * 70)
    print(f"(3) candidate index-monthly tables: {candidates}")
    print("=" * 70)
    for tbl in candidates:
        run(
            f"(3) columns of crsp.{tbl}",
            f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='crsp' AND table_name='{tbl}'
            ORDER BY ordinal_position
            """,
        )

    # (4) Sample 5 rows for each (candidate_table, kytreasnox) pair
    if q1 is not None and len(q1):
        ids = q1["kytreasnox"].unique().tolist()
        print("\n" + "=" * 70)
        print(f"(4) sampling rows for kytreasnox in {ids}")
        print("=" * 70)
        for tbl in candidates:
            for kid in ids:
                print(f"\n--- crsp.{tbl} kytreasnox={kid} ---")
                try:
                    df = db.raw_sql(
                        f"""
                        SELECT *
                        FROM crsp.{tbl}
                        WHERE kytreasnox = {kid}
                        ORDER BY mcaldt DESC
                        LIMIT 5
                        """
                    )
                    print(df.to_string())
                except Exception as e:
                    print(f"ERROR: {e}")

db.close()
print("\nDone.")
