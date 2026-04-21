# Deferred to Phase 2. Current implementation (quarterly full
# realization + no loss harvesting) does not represent any realistic
# HNW tax scenario. Retained as reference only.
"""Secondary Output #6: Tax Drag Sensitivity (equity mu reduction approach).

Tax drag is modeled by reducing equity_mu_ann in each regime before running
the standard Monte Carlo. Three scenarios:
  - No tax:        equity mu unchanged
  - Moderate tax:  equity mu - 1.5% / yr  (typical HNW tax-efficient)
  - High tax:      equity mu - 3.0% / yr  (inefficient taxable account)

Follows Horan (2007) / Kitces benchmark-style tax-drag calibration.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import (  # noqa: E402
    ANNUAL_SPEND_REAL,
    FIGURES_DIR,
    HORIZON_YEARS,
    INFLATION_BASE,
    INITIAL_WEALTH,
    LEGACY_TARGET_REAL,
    PORTFOLIOS,
    REGIME_PARAMS,
    SEED,
)
from simulation.monte_carlo import run_monte_carlo_vectorized  # noqa: E402

PORTFOLIO_ORDER = [
    "aggressive_80_20",
    "traditional_60_40",
    "moderate_40_60",
    "preservation_25_75",
]
PORTFOLIO_SHORT = {
    "aggressive_80_20":   "80/20",
    "traditional_60_40":  "60/40",
    "moderate_40_60":     "40/60",
    "preservation_25_75": "25/75",
}
DRAG_SCENARIOS = [
    ("No tax",        0.000),
    ("Moderate 1.5%", 0.015),
    ("High 3.0%",     0.030),
]
SCENARIO_COLORS = {
    "No tax":        "#2a6fb0",
    "Moderate 1.5%": "#e0a030",
    "High 3.0%":     "#b04a2f",
}

N_PATHS = 10_000
N_QUARTERS = HORIZON_YEARS * 4
CUM_INFL = (1 + INFLATION_BASE / 4) ** N_QUARTERS


def _apply_drag(drag: float) -> dict:
    rp = copy.deepcopy(REGIME_PARAMS)
    for key in ("R1", "R2", "R3"):
        rp[key]["equity_mu_ann"] = rp[key]["equity_mu_ann"] - drag
    return rp


def _run(alloc: tuple, drag: float) -> float:
    T = get_all_matrices()["baseline"]
    rp = _apply_drag(drag)
    out = run_monte_carlo_vectorized(
        T=T, regime_params=rp, allocation=alloc,
        start_wealth=INITIAL_WEALTH, real_spend_annual=ANNUAL_SPEND_REAL,
        inflation_ann=INFLATION_BASE,
        n_paths=N_PATHS, n_quarters=N_QUARTERS, seed=SEED,
    )
    terminal_real = out["wealth_paths"][:, -1] / CUM_INFL
    return float((terminal_real >= LEGACY_TARGET_REAL).mean())


def main() -> None:
    rows = []
    for p in PORTFOLIO_ORDER:
        alloc = PORTFOLIOS[p]
        vals = [_run(alloc, drag) for _, drag in DRAG_SCENARIOS]
        rng = (max(vals) - min(vals)) * 100  # pp range
        rows.append((p, vals, rng))

    print("Tax-drag sensitivity (baseline scenario, $20M real target)")
    print("=" * 78)
    print(f"{'portfolio':<12}{'No tax':>10}{'Moderate (1.5%)':>18}"
          f"{'High (3.0%)':>14}{'Range':>10}")
    for p, vals, rng in rows:
        no_t, mod, hi = vals
        print(f"{PORTFOLIO_SHORT[p]:<12}{no_t:>9.1%}{mod:>17.1%}"
              f"{hi:>13.1%}{-rng:>7.1f}pp")

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(PORTFOLIO_ORDER))
    w = 0.26
    for i, (label, _drag) in enumerate(DRAG_SCENARIOS):
        vals = np.array([row[1][i] * 100 for row in rows])
        offset = (i - 1) * w
        color = SCENARIO_COLORS[label]
        ax.bar(x + offset, vals, width=w, color=color, label=label)
        for xi, v in zip(x + offset, vals):
            ax.text(xi, v + 1.0, f"{v:.1f}%", ha="center", va="bottom",
                    fontsize=9, color=color)

    ax.set_xticks(x)
    ax.set_xticklabels([PORTFOLIO_SHORT[p] for p in PORTFOLIO_ORDER],
                       fontsize=11)
    ax.set_ylabel("Success Rate (%)", fontsize=11)
    ax.set_xlabel("Portfolio (equity/bond)", fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.5)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.set_title(
        "Tax Drag Sensitivity (Equity mu Adjusted for Tax Efficiency)",
        fontsize=13,
    )

    caption = ("Moderate (1.5% drag): typical tax-efficient HNW management. "
               "High (3.0%): inefficient taxable account. Actual outcome "
               "depends on account structure (taxable / IRA / Roth) and "
               "tax-loss harvesting. Preservation portfolios see smaller drag "
               "because bond returns are largely unaffected (bond income "
               "already taxed at ordinary rate regardless of structure in "
               "most accounts).")
    fig.text(0.5, 0.02, caption, ha="center", fontsize=9, style="italic",
             wrap=True,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff8e1",
                       edgecolor="gray", alpha=0.95))

    fig.tight_layout(rect=[0, 0.12, 1, 1])
    out = Path(FIGURES_DIR) / "tax_drag_sensitivity.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
