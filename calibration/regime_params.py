"""Regime calibration: load combined returns, assign regime, estimate params.

Regime windows are the capstone's Bai-Perron break points, aligned to month-ends.
Dates before R1 (pre-2001-01-31) are excluded from regime estimation.
"""
from __future__ import annotations

import math

import pandas as pd

from data.wrds_loader import load_bond_monthly, load_equity_monthly

REGIMES: list[tuple[str, str, str]] = [
    ("R1", "2001-01-31", "2011-04-30"),
    ("R2", "2011-05-31", "2019-01-31"),
    ("R3", "2019-02-28", "2024-12-31"),
]


def load_combined_returns() -> pd.DataFrame:
    """Load equity + bond, inner-join on date.

    Returns DataFrame with columns: date, equity_ret, bond_ret.
    """
    eq = load_equity_monthly()
    bd = load_bond_monthly()
    df = (
        pd.merge(eq, bd, on="date", how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )
    return df


def assign_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'regime' column (R1/R2/R3/None) based on the capstone windows."""
    out = df.copy()
    out["regime"] = pd.NA
    for name, start, end in REGIMES:
        mask = (out["date"] >= pd.Timestamp(start)) & (out["date"] <= pd.Timestamp(end))
        out.loc[mask, "regime"] = name
    return out


def estimate_regime_params(df: pd.DataFrame) -> pd.DataFrame:
    """For each regime, compute monthly-derived annualized moments + correlation.

    Returns DataFrame indexed by regime name with columns:
    n_months, equity_mu_ann, equity_sigma_ann, bond_mu_ann, bond_sigma_ann, correlation.
    """
    sqrt12 = math.sqrt(12.0)
    rows = []
    for name, _start, _end in REGIMES:
        sub = df[df["regime"] == name]
        rows.append({
            "regime": name,
            "n_months": int(len(sub)),
            "equity_mu_ann": float(sub["equity_ret"].mean() * 12.0),
            "equity_sigma_ann": float(sub["equity_ret"].std(ddof=1) * sqrt12),
            "bond_mu_ann": float(sub["bond_ret"].mean() * 12.0),
            "bond_sigma_ann": float(sub["bond_ret"].std(ddof=1) * sqrt12),
            "correlation": float(sub["equity_ret"].corr(sub["bond_ret"])),
        })
    return pd.DataFrame(rows).set_index("regime")
