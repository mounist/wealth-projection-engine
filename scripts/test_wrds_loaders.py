"""Smoke test for WRDS monthly loaders. Prints head/tail, shape, date range,
annualized moments, and flags unit-consistency concerns."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data.wrds_loader import load_bond_monthly, load_equity_monthly

SQRT12 = np.sqrt(12.0)


def describe(name: str, df: pd.DataFrame, col: str,
             ann_mean_range: tuple[float, float],
             ann_vol_range: tuple[float, float]) -> None:
    print("=" * 72)
    print(f"{name}")
    print("=" * 72)
    print(f"shape: {df.shape}")
    print(f"date range: {df['date'].min().date()}  ->  {df['date'].max().date()}")
    print("head:")
    print(df.head().to_string(index=False))
    print("tail:")
    print(df.tail().to_string(index=False))

    m = df[col].mean()
    s = df[col].std(ddof=1)
    ann_m = m * 12.0
    ann_s = s * SQRT12
    print()
    print(f"monthly  mean={m:+.6f}  std={s:.6f}  min={df[col].min():+.4f}  max={df[col].max():+.4f}")
    print(f"annualized  mean={ann_m:+.4%}  vol={ann_s:.4%}")

    lo_m, hi_m = ann_mean_range
    lo_v, hi_v = ann_vol_range
    mean_ok = lo_m <= ann_m <= hi_m
    vol_ok = lo_v <= ann_s <= hi_v
    print(f"sanity   ann mean in [{lo_m:.1%},{hi_m:.1%}]? {mean_ok}   "
          f"ann vol in [{lo_v:.1%},{hi_v:.1%}]? {vol_ok}")

    if abs(m) > 0.05:
        print(f"!! UNIT WARNING: monthly mean |{m:.4f}| > 5% — possible units bug.")
    print()


def main() -> None:
    equity = load_equity_monthly()
    bond = load_bond_monthly()

    describe("CRSP equity (vwretd, decimal)", equity, "equity_ret",
             ann_mean_range=(0.08, 0.12),
             ann_vol_range=(0.15, 0.18))
    describe("CRSP 10Y Treasury FIXEDTERM (tmretadj/100)", bond, "bond_ret",
             ann_mean_range=(0.04, 0.06),
             ann_vol_range=(0.06, 0.10))

    merged = pd.merge(equity, bond, on="date", how="inner")
    print("=" * 72)
    print(f"overlap rows after inner join on date: {len(merged)}")
    print(f"overlap range: {merged['date'].min().date()}  ->  {merged['date'].max().date()}")
    print("=" * 72)


if __name__ == "__main__":
    main()
