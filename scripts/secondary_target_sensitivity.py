"""Secondary Output #8: Legacy Target Sensitivity.

Reuse full_mvp.pkl (baseline scenario only). Compare success at $15M/$20M/$25M.
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

from config import FIGURES_DIR, RESULTS_DIR  # noqa: E402

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
TARGETS = [15_000_000, 20_000_000, 25_000_000]
TARGET_COLORS = {15_000_000: "#6aa870", 20_000_000: "#4a7dbf", 25_000_000: "#b04a2f"}


def main() -> None:
    with (RESULTS_DIR / "full_mvp.pkl").open("rb") as f:
        data = pickle.load(f)
    results = data["results"]

    succ: dict[tuple[str, int], float] = {}
    for p in PORTFOLIO_ORDER:
        tr = results[(p, "baseline")]["terminal_real"]
        for t in TARGETS:
            succ[(p, t)] = float((tr >= t).mean())

    print("Legacy-target sensitivity (baseline scenario)")
    print("=" * 72)
    print(f"{'portfolio':<22}{'$15M':>12}{'$20M':>12}{'$25M':>12}")
    for p in PORTFOLIO_ORDER:
        s15, s20, s25 = (succ[(p, t)] for t in TARGETS)
        print(f"{p:<22}{s15:>11.1%}{s20:>11.1%}{s25:>11.1%}")

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(PORTFOLIO_ORDER))
    w = 0.26
    for i, t in enumerate(TARGETS):
        vals = np.array([succ[(p, t)] * 100 for p in PORTFOLIO_ORDER])
        offset = (i - 1) * w
        ax.bar(x + offset, vals, width=w, color=TARGET_COLORS[t],
               label=f"${t/1e6:.0f}M")
        for xi, v in zip(x + offset, vals):
            ax.text(xi, v + 1.0, f"{v:.1f}%", ha="center", va="bottom",
                    fontsize=9, color=TARGET_COLORS[t])

    ax.set_xticks(x)
    ax.set_xticklabels([PORTFOLIO_SHORT[p] for p in PORTFOLIO_ORDER],
                       fontsize=11)
    ax.set_ylabel("Success Rate (%)", fontsize=11)
    ax.set_xlabel("Portfolio (equity/bond)", fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.5)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9, title="Target")
    ax.set_title("Legacy Target Sensitivity (Baseline Transition Scenario)",
                 fontsize=13)

    caption = ("Shows asymmetric regime sensitivity across target levels. "
               "At conventional $20M (preserve real initial wealth), target "
               "lies near the regime-spread inflection point for preservation "
               "portfolios.")
    fig.text(0.5, 0.02, caption, ha="center", fontsize=9, style="italic",
             wrap=True,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff8e1",
                       edgecolor="gray", alpha=0.95))

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    out = Path(FIGURES_DIR) / "target_sensitivity.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
