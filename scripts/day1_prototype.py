"""Day 1 Monte Carlo prototype — numbers only, no charts.

60/40, $20M start, $500K real/yr spend, 2.5% inflation, 1000 paths, 30 years.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import INFLATION_BASE, REGIME_PARAMS, SEED  # noqa: E402
from simulation.monte_carlo import run_monte_carlo  # noqa: E402

ALLOCATION = (0.60, 0.40)
START_WEALTH = 20_000_000.0
REAL_SPEND_ANNUAL = 500_000.0
N_PATHS = 1_000
N_QUARTERS = 120
LEGACY_TARGETS = [15_000_000, 20_000_000, 25_000_000]
PCTILES = [5, 25, 50, 75, 95]


def _fmt_money(x: float) -> str:
    return f"${x/1e6:>8.2f}M"


def _percentiles(arr: np.ndarray) -> dict[int, float]:
    return {p: float(np.percentile(arr, p)) for p in PCTILES}


def main() -> None:
    T = get_all_matrices()["baseline"]
    result = run_monte_carlo(
        T=T,
        regime_params=REGIME_PARAMS,
        allocation=ALLOCATION,
        start_wealth=START_WEALTH,
        real_spend_annual=REAL_SPEND_ANNUAL,
        inflation_ann=INFLATION_BASE,
        n_paths=N_PATHS,
        n_quarters=N_QUARTERS,
        seed=SEED,
    )

    wealth_paths = result["wealth_paths"]
    regime_paths = result["regime_paths"]
    stationary = result["stationary"]
    initial_regimes = result["initial_regimes"]

    terminal_nominal = wealth_paths[:, -1]
    infl_q = INFLATION_BASE / 4
    cum_inflation = (1 + infl_q) ** N_QUARTERS
    terminal_real = terminal_nominal / cum_inflation

    print("=" * 72)
    print("Day 1 prototype — 60/40, $20M, $500K real spend, 2.5% infl, baseline T")
    print(f"n_paths={N_PATHS}  n_quarters={N_QUARTERS}  seed={SEED}")
    print("=" * 72)

    print("\nStationary (baseline): "
          f"R1={stationary[0]:.4f}  R2={stationary[1]:.4f}  R3={stationary[2]:.4f}")
    ir_counts = np.bincount(initial_regimes, minlength=3) / N_PATHS
    print(f"Initial regime sample: R1={ir_counts[0]:.4f}  "
          f"R2={ir_counts[1]:.4f}  R3={ir_counts[2]:.4f}")
    print(f"Cumulative inflation over 30y: {cum_inflation:.4f}x")

    print("\nTerminal NOMINAL wealth:")
    print(f"  mean = {_fmt_money(terminal_nominal.mean())}")
    pn = _percentiles(terminal_nominal)
    for p in PCTILES:
        print(f"  p{p:<2} = {_fmt_money(pn[p])}")

    print("\nTerminal REAL wealth (deflated):")
    print(f"  mean = {_fmt_money(terminal_real.mean())}")
    pr = _percentiles(terminal_real)
    for p in PCTILES:
        print(f"  p{p:<2} = {_fmt_money(pr[p])}")

    print("\nSuccess rates on terminal REAL wealth:")
    for tgt in LEGACY_TARGETS:
        rate = float((terminal_real >= tgt).mean())
        print(f"  P(real terminal >= ${tgt/1e6:>5.1f}M) = {rate:.4f}")

    print("\nRegime time exposure (avg fraction of quarters per regime):")
    exposure = np.zeros(3)
    for r in range(3):
        exposure[r] = float((regime_paths == r).mean())
    for r in range(3):
        print(f"  R{r+1}: {exposure[r]:.4f}   "
              f"(stationary: {stationary[r]:.4f})")

    print("\n" + "=" * 72)
    print("Client-conditional analysis — paths starting in R3")
    print("=" * 72)
    mask_r3 = initial_regimes == 2
    n_r3 = int(mask_r3.sum())
    print(f"Paths starting in R3: {n_r3} / {N_PATHS}")

    if n_r3:
        terminal_real_r3 = terminal_real[mask_r3]
        print("\nTerminal REAL wealth | init regime = R3:")
        pr3 = _percentiles(terminal_real_r3)
        print(f"  mean = {_fmt_money(terminal_real_r3.mean())}")
        for p in PCTILES:
            print(f"  p{p:<2} = {_fmt_money(pr3[p])}")

        print("\nSuccess rates (R3-start subset) with delta vs unconditional:")
        for tgt in LEGACY_TARGETS:
            cond = float((terminal_real_r3 >= tgt).mean())
            uncond = float((terminal_real >= tgt).mean())
            delta = cond - uncond
            print(f"  P(>= ${tgt/1e6:>5.1f}M | R3-start) = {cond:.4f}   "
                  f"(unconditional {uncond:.4f}, delta {delta:+.4f})")


if __name__ == "__main__":
    main()
