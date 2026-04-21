"""Primary Output #1: success-rate heatmap (4 portfolios x 3 scenarios)
with a separate right-hand subplot for the sticky-minus-fragile regime spread.

Fixed color scales across targets:
    success rate: 0%-100%, RdYlGn (red=low, green=high)
    spread:      -8pp..+8pp, RdBu_r centered at 0
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import FIGURES_DIR, RESULTS_DIR  # noqa: E402

PORTFOLIO_ORDER = [
    "aggressive_80_20",
    "traditional_60_40",
    "moderate_40_60",
    "preservation_25_75",
]
PORTFOLIO_LABELS = {
    "aggressive_80_20":   "Aggressive 80/20",
    "traditional_60_40":  "Traditional 60/40",
    "moderate_40_60":     "Moderate 40/60",
    "preservation_25_75": "Preservation 25/75",
}
SCENARIO_ORDER = ["sticky", "baseline", "fragile"]
SCENARIO_LABELS = {"sticky": "Sticky", "baseline": "Baseline", "fragile": "Fragile"}

SPREAD_VMAX = 8.0
ANNOT_FS = 13

FINDINGS: dict[int, tuple[str, str]] = {
    15_000_000: (
        "At lower legacy target, preservation improves to ~52% but remains below balanced portfolios.",
        "Regime sensitivity pattern preserved across balanced portfolios.",
    ),
    20_000_000: (
        "Preservation portfolio shows structural failure across all regimes (~31%).",
        "Balanced portfolios show 5-6pp fragile-over-sticky regime sensitivity.",
    ),
    25_000_000: (
        "Sign-flip in preservation row: sticky regime beats fragile by 2.4pp at high legacy target.",
        "Positive equity-bond correlation in R3 benefits upside tail when only luck can reach target.",
    ),
}


def _success_matrix(results: dict, target: float) -> np.ndarray:
    m = np.zeros((len(PORTFOLIO_ORDER), len(SCENARIO_ORDER)))
    for i, p in enumerate(PORTFOLIO_ORDER):
        for j, s in enumerate(SCENARIO_ORDER):
            tr = results[(p, s)]["terminal_real"]
            m[i, j] = float((tr >= target).mean())
    return m


def plot_success_heatmap(results_pkl_path: str | Path,
                         target: float,
                         output_path: str | Path,
                         title_suffix: str = "") -> None:
    with Path(results_pkl_path).open("rb") as f:
        data = pickle.load(f)
    results = data["results"]

    success = _success_matrix(results, target)
    spread_pp = (success[:, 0] - success[:, 2]) * 100  # sticky minus fragile

    fig, (ax_main, ax_spread) = plt.subplots(
        1, 2, figsize=(12, 6),
        gridspec_kw={"width_ratios": [4, 1], "wspace": 0.35},
        constrained_layout=True,
    )

    im = ax_main.imshow(
        success, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto",
    )
    ax_main.set_xticks(range(len(SCENARIO_ORDER)))
    ax_main.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER],
                            fontsize=11)
    ax_main.set_yticks(range(len(PORTFOLIO_ORDER)))
    ax_main.set_yticklabels([PORTFOLIO_LABELS[p] for p in PORTFOLIO_ORDER],
                            fontsize=11)
    ax_main.set_xlabel("Transition Scenario", fontsize=11)
    ax_main.set_ylabel("Portfolio", fontsize=11)

    for i in range(len(PORTFOLIO_ORDER)):
        for j in range(len(SCENARIO_ORDER)):
            ax_main.text(j, i, f"{success[i, j]:.1%}",
                         ha="center", va="center",
                         fontsize=ANNOT_FS, color="black")

    cbar = fig.colorbar(im, ax=ax_main, fraction=0.05, pad=0.04)
    cbar.set_label("Success Rate", rotation=270, labelpad=14, fontsize=11)
    cbar.ax.tick_params(labelsize=10)

    norm = TwoSlopeNorm(vmin=-SPREAD_VMAX, vcenter=0.0, vmax=SPREAD_VMAX)
    im2 = ax_spread.imshow(
        spread_pp.reshape(-1, 1),
        cmap="RdBu_r", norm=norm, aspect="auto",
    )
    ax_spread.set_xticks([0])
    ax_spread.set_xticklabels(["Sticky - Fragile"], fontsize=11)
    ax_spread.set_yticks(range(len(PORTFOLIO_ORDER)))
    ax_spread.set_yticklabels([])
    ax_spread.set_xlabel("Regime Spread (pp)", fontsize=11)

    for i in range(len(PORTFOLIO_ORDER)):
        val = spread_pp[i]
        color = "white" if abs(val) > SPREAD_VMAX * 0.5 else "black"
        ax_spread.text(0, i, f"{val:+.1f}pp",
                       ha="center", va="center",
                       fontsize=ANNOT_FS, color=color)

    cbar2 = fig.colorbar(im2, ax=ax_spread, fraction=0.25, pad=0.04)
    cbar2.set_label("Sticky - Fragile (pp)", rotation=270, labelpad=14, fontsize=11)
    cbar2.ax.tick_params(labelsize=10)

    suffix_str = f"  {title_suffix}" if title_suffix else ""
    fig.suptitle(
        f"Success Rate by Portfolio x Transition Scenario "
        f"(Legacy Target: ${target/1e6:.0f}M real){suffix_str}",
        fontsize=13,
    )

    target_int = int(target)
    if target_int in FINDINGS:
        line1, line2 = FINDINGS[target_int]
        fig.text(0.02, 0.045, line1, fontsize=8, style="italic", ha="left")
        fig.text(0.02, 0.015, line2, fontsize=8, style="italic", ha="left")

    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    out_dir = Path(FIGURES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = {
        15_000_000: out_dir / "heatmap_target_15M.png",
        20_000_000: out_dir / "heatmap_target_20M.png",
        25_000_000: out_dir / "heatmap_target_25M.png",
    }
    for tgt, out in targets.items():
        plot_success_heatmap(pkl, tgt, out)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
