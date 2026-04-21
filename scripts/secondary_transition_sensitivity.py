"""Secondary Output #7: Transition Probability Sensitivity.

Reuse full_mvp.pkl. Compare success @ $20M real across baseline/sticky/fragile
per portfolio. Save bar chart + print table.
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

from config import FIGURES_DIR, LEGACY_TARGET_REAL, RESULTS_DIR  # noqa: E402

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
SCEN_ORDER = ["baseline", "sticky", "fragile"]
SCEN_COLORS = {"baseline": "#2a6fb0", "sticky": "#6a8ec2", "fragile": "#b04a2f"}


def main() -> None:
    with (RESULTS_DIR / "full_mvp.pkl").open("rb") as f:
        data = pickle.load(f)
    results = data["results"]

    succ: dict[tuple[str, str], float] = {}
    for p in PORTFOLIO_ORDER:
        for s in SCEN_ORDER:
            tr = results[(p, s)]["terminal_real"]
            succ[(p, s)] = float((tr >= LEGACY_TARGET_REAL).mean())

    print(f"Transition sensitivity @ ${LEGACY_TARGET_REAL/1e6:.0f}M real")
    print("=" * 78)
    print(f"{'portfolio':<22}{'baseline':>11}{'sticky':>11}{'fragile':>11}"
          f"{'spread(max-min)':>22}")
    for p in PORTFOLIO_ORDER:
        b = succ[(p, 'baseline')]
        s = succ[(p, 'sticky')]
        f_ = succ[(p, 'fragile')]
        spread = (max(b, s, f_) - min(b, s, f_)) * 100
        print(f"{p:<22}{b:>10.1%}{s:>10.1%}{f_:>10.1%}{spread:>19.1f}pp")

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(PORTFOLIO_ORDER))
    w = 0.26
    for i, s in enumerate(SCEN_ORDER):
        vals = np.array([succ[(p, s)] * 100 for p in PORTFOLIO_ORDER])
        offset = (i - 1) * w
        ax.bar(x + offset, vals, width=w, color=SCEN_COLORS[s],
               label=s.capitalize())
        for xi, v in zip(x + offset, vals):
            ax.text(xi, v + 1.0, f"{v:.1f}%", ha="center", va="bottom",
                    fontsize=9, color=SCEN_COLORS[s])

    ax.set_xticks(x)
    ax.set_xticklabels([PORTFOLIO_SHORT[p] for p in PORTFOLIO_ORDER],
                       fontsize=11)
    ax.set_ylabel("Success Rate (%)", fontsize=11)
    ax.set_xlabel("Portfolio (equity/bond)", fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.5)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.set_title(
        f"Transition Probability Sensitivity "
        f"(${LEGACY_TARGET_REAL/1e6:.0f}M Target)",
        fontsize=13,
    )

    caption = ("Range reflects uncertainty about R3 regime persistence: "
               "baseline (R3 ~100mo), sticky (R3 ~200mo, structural shift), "
               "fragile (R3 ~48mo, transient).")
    fig.text(0.5, 0.02, caption, ha="center", fontsize=9, style="italic",
             wrap=True,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff8e1",
                       edgecolor="gray", alpha=0.95))

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    out = Path(FIGURES_DIR) / "transition_sensitivity.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
