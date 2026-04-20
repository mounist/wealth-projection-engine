"""Run regime calibration: print empirical params + diff vs v7 hand-coded, save JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.regime_params import (  # noqa: E402
    assign_regime,
    estimate_regime_params,
    load_combined_returns,
)
from config import RESULTS_DIR  # noqa: E402

V7_HAND_CODED: dict[str, dict[str, float]] = {
    "R1": {"equity_mu_ann": 0.09, "equity_sigma_ann": 0.16,
           "bond_mu_ann": 0.04, "bond_sigma_ann": 0.06, "correlation": -0.10},
    "R2": {"equity_mu_ann": 0.11, "equity_sigma_ann": 0.13,
           "bond_mu_ann": 0.03, "bond_sigma_ann": 0.05, "correlation": -0.30},
    "R3": {"equity_mu_ann": 0.07, "equity_sigma_ann": 0.18,
           "bond_mu_ann": 0.045, "bond_sigma_ann": 0.08, "correlation": 0.40},
}

METRICS = ["equity_mu_ann", "equity_sigma_ann",
           "bond_mu_ann", "bond_sigma_ann", "correlation"]


def _fmt(metric: str, value: float) -> str:
    if metric == "correlation":
        return f"{value:+.3f}"
    return f"{value:+.2%}"


def main() -> None:
    df = load_combined_returns()
    df = assign_regime(df)
    params = estimate_regime_params(df)

    print("=" * 80)
    print("Empirical regime parameters — CRSP equity + FIXEDTERM 10Y Treasury")
    print("Bai-Perron windows: R1 2001-01 → 2011-04, R2 2011-05 → 2019-01, R3 2019-02 → 2024-12")
    print("=" * 80)
    disp = params.copy()
    for col in ["equity_mu_ann", "equity_sigma_ann", "bond_mu_ann", "bond_sigma_ann"]:
        disp[col] = params[col].map(lambda x: f"{x:+.2%}")
    disp["correlation"] = params["correlation"].map(lambda x: f"{x:+.3f}")
    print(disp.to_string())

    print()
    print("=" * 80)
    print("Empirical vs v7 hand-coded   flags: mean/vol |diff|>2pp, rho |diff|>0.15")
    print("=" * 80)
    header = f"{'regime':<6} {'metric':<18} {'empirical':>12} {'v7':>12} {'diff':>12}  flag"
    print(header)
    print("-" * len(header))
    any_flag = False
    for regime in ("R1", "R2", "R3"):
        for metric in METRICS:
            e = float(params.loc[regime, metric])
            v = float(V7_HAND_CODED[regime][metric])
            d = e - v
            thr = 0.15 if metric == "correlation" else 0.02
            flag = "!!" if abs(d) > thr else ""
            if flag:
                any_flag = True
            print(f"{regime:<6} {metric:<18} "
                  f"{_fmt(metric, e):>12} {_fmt(metric, v):>12} "
                  f"{_fmt(metric, d):>12}  {flag}")
        print("-" * len(header))

    if not any_flag:
        print("No flagged differences.")

    out_path = RESULTS_DIR / "regime_params_empirical.json"
    dump = {
        regime: {
            "n_months": int(params.loc[regime, "n_months"]),
            **{m: float(params.loc[regime, m]) for m in METRICS},
        }
        for regime in params.index
    }
    with out_path.open("w") as f:
        json.dump(dump, f, indent=2)
    print(f"\nSaved empirical params: {out_path}")


if __name__ == "__main__":
    main()
