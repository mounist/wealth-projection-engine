"""WRDS loaders for monthly equity and 10Y Treasury total-return series.

Both series are returned in DECIMAL units (e.g., 0.008 = 0.8% monthly).
The bond source (crsp.tfz_mth_ft.tmretadj) is published in percent,
so the bond loader divides by 100 to normalize.
"""
from __future__ import annotations

import pandas as pd
import wrds

from config import DATA_DIR, END_DATE, START_DATE, WRDS_USERNAME


def load_equity_monthly(refresh: bool = False) -> pd.DataFrame:
    """Monthly CRSP value-weighted equity return, decimal units.

    Returns DataFrame with columns: date, equity_ret
    """
    cache_path = DATA_DIR / "equity_monthly.parquet"
    if cache_path.exists() and not refresh:
        return pd.read_parquet(cache_path)

    db = wrds.Connection(wrds_username=WRDS_USERNAME)
    df = db.raw_sql(f"""
        SELECT date, vwretd
        FROM crsp.msi
        WHERE date BETWEEN '{START_DATE}' AND '{END_DATE}'
        ORDER BY date
    """)
    db.close()

    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(columns={"vwretd": "equity_ret"})
    df = df.dropna(subset=["equity_ret"]).reset_index(drop=True)

    df.to_parquet(cache_path, index=False)
    return df


def load_bond_monthly(refresh: bool = False) -> pd.DataFrame:
    """Monthly CRSP 10Y Fixed-Term Treasury total return, decimal units.

    Source: crsp.tfz_mth_ft, kytreasnox=2000007
    ("CRSP Fixed Term Index - 10-Year (Nominal)").

    Converts tmretadj from percent to decimal (divide by 100) to match
    the equity return convention.

    Returns DataFrame with columns: date, bond_ret
    """
    cache_path = DATA_DIR / "bond_monthly.parquet"
    if cache_path.exists() and not refresh:
        return pd.read_parquet(cache_path)

    db = wrds.Connection(wrds_username=WRDS_USERNAME)
    df = db.raw_sql(f"""
        SELECT mcaldt, tmretadj
        FROM crsp.tfz_mth_ft
        WHERE kytreasnox = 2000007
          AND mcaldt BETWEEN '{START_DATE}' AND '{END_DATE}'
        ORDER BY mcaldt
    """)
    db.close()

    df["date"] = pd.to_datetime(df["mcaldt"])
    df["bond_ret"] = df["tmretadj"] / 100.0
    df = df[["date", "bond_ret"]].dropna().reset_index(drop=True)

    df.to_parquet(cache_path, index=False)
    return df
