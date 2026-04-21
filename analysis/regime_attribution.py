"""Primary Output #4: regime attribution.

For each portfolio (baseline scenario), reconstruct quarterly portfolio
returns from wealth paths, convert to real, stratify by the regime active
that quarter, and compute a mean annualized real return per regime.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    ANNUAL_SPEND_REAL,
    FIGURES_DIR,
    INFLATION_BASE,
    PORTFOLIOS,
    RESULTS_DIR,
)

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
REGIME_COLORS = {0: "#2a6fb0", 1: "#2e8b57", 2: "#b04a2f"}
REGIME_LABELS = {
    0: "R1 Accumulation (2001-2011)",
    1: "R2 QE era (2011-2019)",
    2: "R3 Post-QE (2019-present)",
}
WR_REAL = ANNUAL_SPEND_REAL / 20_000_000  # 0.025


def compute_regime_attribution(results_pkl_path: str | Path,
                               scenario: str = "baseline") -> dict:
    """Return per-(portfolio, regime) mean annualized REAL portfolio return."""
    with Path(results_pkl_path).open("rb") as f:
        data = pickle.load(f)
    results = data["results"]

    infl_q = INFLATION_BASE / 4
    spend_q_real = ANNUAL_SPEND_REAL / 4

    out: dict[str, dict[int, float]] = {}
    for pname in PORTFOLIO_ORDER:
        combo = results[(pname, scenario)]
        W = combo["wealth_paths"]           # (n_paths, n_q+1) nominal
        rp = combo["regime_paths"]          # (n_paths, n_q) int
        n_paths, ncol = W.shape
        n_q = ncol - 1

        withdrawals_nominal = spend_q_real * (1 + infl_q) ** np.arange(1, n_q + 1)
        nom_q = (W[:, 1:] + withdrawals_nominal) / W[:, :-1] - 1.0
        real_q = (1 + nom_q) / (1 + infl_q) - 1.0

        by_regime: dict[int, float] = {}
        for r in (0, 1, 2):
            mask = rp == r
            if mask.any():
                mean_q = float(real_q[mask].mean())
                by_regime[r] = mean_q * 4.0  # annualized (arithmetic)
            else:
                by_regime[r] = float("nan")
        out[pname] = by_regime

    return {"scenario": scenario, "portfolios": out}


def plot_regime_attribution(attribution_data: dict,
                            output_path: str | Path) -> None:
    portfolios = attribution_data["portfolios"]

    x = np.arange(len(PORTFOLIO_ORDER))
    w = 0.26

    fig, ax = plt.subplots(figsize=(12, 6))

    for r in (0, 1, 2):
        vals = np.array([portfolios[p][r] * 100 for p in PORTFOLIO_ORDER])
        offset = (r - 1) * w
        bars = ax.bar(x + offset, vals, width=w,
                      color=REGIME_COLORS[r], label=REGIME_LABELS[r])
        for xi, v in zip(x + offset, vals):
            ax.text(xi, v + 0.15, f"{v:.1f}%",
                    ha="center", va="bottom", fontsize=9,
                    color=REGIME_COLORS[r])

    ax.axhline(WR_REAL * 100, color="black", linestyle="--", linewidth=1.3,
               label=f"2.5% real WR hurdle")

    ax.set_xticks(x)
    ax.set_xticklabels([PORTFOLIO_SHORT[p] for p in PORTFOLIO_ORDER],
                       fontsize=11)
    ax.set_ylabel("Annualized Real Return (%)", fontsize=11)
    ax.set_xlabel("Portfolio (equity/bond)", fontsize=11)

    ax.set_title("Portfolio Returns by Active Regime "
                 "(Baseline Transition Scenario)", fontsize=13, pad=18)
    ax.text(0.5, 1.01,
            "Conditional on regime active in a given quarter, annualized",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=10, style="italic", color="#444")

    ax.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.55)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.9)

    ymin = min(-0.5,
               min(portfolios[p][r] * 100
                   for p in PORTFOLIO_ORDER for r in (0, 1, 2)) - 1.0)
    ymax = max(portfolios[p][r] * 100
               for p in PORTFOLIO_ORDER for r in (0, 1, 2)) + 1.5
    ax.set_ylim(ymin, ymax)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    attribution = compute_regime_attribution(pkl, scenario="baseline")

    # Summary table
    print("Annualized real return by active regime (baseline scenario)")
    print("=" * 72)
    header = f"{'portfolio':<22}{'R1':>12}{'R2':>12}{'R3':>12}"
    print(header)
    for pname in PORTFOLIO_ORDER:
        r1 = attribution["portfolios"][pname][0] * 100
        r2 = attribution["portfolios"][pname][1] * 100
        r3 = attribution["portfolios"][pname][2] * 100
        print(f"{pname:<22}{r1:>11.2f}%{r2:>11.2f}%{r3:>11.2f}%")

    out = Path(FIGURES_DIR) / "regime_attribution.png"
    plot_regime_attribution(attribution, out)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
