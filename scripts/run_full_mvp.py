"""Day 2 Task 1: full MVP run.

4 portfolios x 3 transition scenarios, 10,000 paths, 30y (120 quarters),
seed=42 per combo (deterministic, fresh RNG state each run).

Saves artifacts/results/full_mvp.pkl and prints the success-rate table.
"""
from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import (  # noqa: E402
    ANNUAL_SPEND_REAL,
    HORIZON_YEARS,
    INFLATION_BASE,
    INITIAL_WEALTH,
    LEGACY_TARGET_REAL,
    PORTFOLIOS,
    REGIME_PARAMS,
    RESULTS_DIR,
    SEED,
)
from simulation.monte_carlo import run_monte_carlo_vectorized as run_monte_carlo  # noqa: E402

N_PATHS = 10_000
N_QUARTERS = HORIZON_YEARS * 4
SCENARIOS = ("baseline", "sticky", "fragile")


def main() -> None:
    matrices = get_all_matrices()
    cum_inflation = (1 + INFLATION_BASE / 4) ** N_QUARTERS

    metadata = {
        "n_paths": N_PATHS,
        "n_quarters": N_QUARTERS,
        "horizon_years": HORIZON_YEARS,
        "seed": SEED,
        "legacy_target": LEGACY_TARGET_REAL,
        "initial_wealth": INITIAL_WEALTH,
        "annual_spend_real": ANNUAL_SPEND_REAL,
        "inflation_base": INFLATION_BASE,
        "cum_inflation_30y": float(cum_inflation),
        "portfolios": dict(PORTFOLIOS),
        "scenarios": list(SCENARIOS),
    }
    results: dict[tuple[str, str], dict] = {}

    print(f"Full MVP: {len(PORTFOLIOS)} portfolios x {len(SCENARIOS)} scenarios "
          f"= {len(PORTFOLIOS) * len(SCENARIOS)} combos")
    print(f"n_paths={N_PATHS}  n_quarters={N_QUARTERS}  seed={SEED}")
    print("-" * 72)

    t_all = time.perf_counter()
    for pname, alloc in PORTFOLIOS.items():
        for scen in SCENARIOS:
            t0 = time.perf_counter()
            out = run_monte_carlo(
                T=matrices[scen],
                regime_params=REGIME_PARAMS,
                allocation=alloc,
                start_wealth=INITIAL_WEALTH,
                real_spend_annual=ANNUAL_SPEND_REAL,
                inflation_ann=INFLATION_BASE,
                n_paths=N_PATHS,
                n_quarters=N_QUARTERS,
                seed=SEED,
            )
            terminal_nominal = out["wealth_paths"][:, -1]
            terminal_real = terminal_nominal / cum_inflation
            success = float((terminal_real >= LEGACY_TARGET_REAL).mean())
            dt = time.perf_counter() - t0

            results[(pname, scen)] = {
                "wealth_paths": out["wealth_paths"],
                "regime_paths": out["regime_paths"],
                "terminal_nominal": terminal_nominal,
                "terminal_real": terminal_real,
                "success_rate_20M": success,
                "initial_regimes": out["initial_regimes"],
            }
            print(f"  {pname:<20} x {scen:<9}  success={success:>6.2%}   "
                  f"done in {dt:6.2f}s")

    total_dt = time.perf_counter() - t_all
    print("-" * 72)
    print(f"Total runtime: {total_dt:.2f}s")

    out_path = RESULTS_DIR / "full_mvp.pkl"
    with out_path.open("wb") as f:
        pickle.dump({"metadata": metadata, "results": results}, f)
    print(f"Saved: {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")

    print()
    print("=" * 72)
    print(f"Success rate  P(real terminal >= ${LEGACY_TARGET_REAL/1e6:.0f}M)")
    print("=" * 72)
    header = f"{'':<20}" + "".join(f"{s:>10}" for s in SCENARIOS)
    print(header)
    for pname in PORTFOLIOS:
        cells = "".join(
            f"{results[(pname, s)]['success_rate_20M']:>9.1%} "
            for s in SCENARIOS
        )
        print(f"{pname:<20}{cells}")


if __name__ == "__main__":
    main()
