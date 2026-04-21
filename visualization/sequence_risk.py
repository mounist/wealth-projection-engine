"""Sequence-of-returns risk for HNW setting: two-panel figure.

Panel A: histogram of forward/reversed terminal-wealth ratios (aggregate).
Panel B: stratified bars of mean terminal wealth by worst-year bucket.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import FIGURES_DIR, RESULTS_DIR  # noqa: E402

COLOR_FWD = "#0b3d91"   # forward = navy
COLOR_REV = "#b04a2f"   # reversed = rust


def plot_sequence_of_returns(distribution_results_path: str | Path,
                             output_path: str | Path) -> None:
    with Path(distribution_results_path).open("r") as f:
        payload = json.load(f)

    agg = payload["aggregate"]
    ratios = np.asarray(payload["ratios"], dtype=float)
    strat = payload["stratified"]

    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(14, 6),
        gridspec_kw={"width_ratios": [1.1, 1.0], "wspace": 0.28},
        constrained_layout=True,
    )

    # -----------------------------------------------------------------
    # Panel A: ratio histogram (log x)
    # -----------------------------------------------------------------
    safe = ratios[(ratios > 0) & np.isfinite(ratios)]
    lo = max(float(np.percentile(safe, 0.5)), 1e-3)
    hi = min(float(np.percentile(safe, 99.5)), 1e3)
    bins = np.logspace(np.log10(lo), np.log10(hi), 60)
    axA.hist(safe, bins=bins, color="#6a8ec2", edgecolor="white",
             linewidth=0.5)
    axA.set_xscale("log")
    axA.axvline(1.0, color="black", linestyle="--", linewidth=1.4)
    axA.set_xlabel("Forward / Reversed terminal-wealth ratio (log scale)",
                   fontsize=11)
    axA.set_ylabel("Count of paths", fontsize=11)
    axA.set_title("Panel A  Aggregate ratio distribution (n=10,000)",
                  fontsize=12)

    axA.text(
        0.02, 0.97,
        (f"Aggregate: {agg['pct_inverted_fwd_gt_rev']:.1%} inverted, "
         f"{agg['pct_classic_rev_gt_fwd']:.1%} classic,\n"
         f"median ratio {agg['median_ratio']:.3f} - sequence effect "
         f"washes out across random paths"),
        transform=axA.transAxes, ha="left", va="top", fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="gray", alpha=0.92),
    )
    axA.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.5)

    # -----------------------------------------------------------------
    # Panel B: stratified paired bars
    # -----------------------------------------------------------------
    labels = [f"Years {row['bucket']}" for row in strat]
    fwd_means = np.array([row["mean_fwd_real"] for row in strat]) / 1e6
    rev_means = np.array([row["mean_rev_real"] for row in strat]) / 1e6
    ns = [row["n"] for row in strat]

    x = np.arange(len(labels))
    w = 0.38
    axB.bar(x - w/2, fwd_means, width=w, color=COLOR_FWD,
            label="Forward (original order)")
    axB.bar(x + w/2, rev_means, width=w, color=COLOR_REV,
            label="Reversed")

    for i in range(len(labels)):
        axB.text(x[i] - w/2, fwd_means[i] + 0.4, f"${fwd_means[i]:.1f}M",
                 ha="center", va="bottom", fontsize=9, color=COLOR_FWD)
        axB.text(x[i] + w/2, rev_means[i] + 0.4, f"${rev_means[i]:.1f}M",
                 ha="center", va="bottom", fontsize=9, color=COLOR_REV)

    axB.set_xticks(x)
    axB.set_xticklabels([f"{lab}\n(N={n})" for lab, n in zip(labels, ns)],
                        fontsize=10)
    axB.set_ylabel("Mean terminal wealth (real $M)", fontsize=11)
    axB.set_xlabel("Bucket: year with worst annual return", fontsize=11)
    axB.set_title("Panel B  Mean terminal by worst-year timing",
                  fontsize=12)
    axB.set_ylim(0, max(fwd_means.max(), rev_means.max()) * 1.18)
    axB.legend(loc="upper right", fontsize=9, framealpha=0.9,
               borderpad=0.3, handlelength=1.4)
    axB.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.5)

    fig.suptitle(
        "Sequence-of-Returns Risk at HNW 2.5% Withdrawal Rate",
        fontsize=14,
    )

    caption = ("Toxic window shifted to years 21-30 under HNW 2.5% WR "
               "vs Bengen's years 1-10 at 4% WR.  "
               "Mechanism: nominal withdrawals ~2x by year 25 due to inflation, "
               "so late drawdowns hit a larger spending load.")
    fig.text(0.5, 0.02, caption,
             ha="center", va="bottom", fontsize=9.5, style="italic",
             wrap=True,
             bbox=dict(boxstyle="round,pad=0.45", facecolor="#fff8e1",
                       edgecolor="gray", alpha=0.95))
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    json_path = RESULTS_DIR / "sequence_risk_distribution.json"
    out = Path(FIGURES_DIR) / "sequence_of_returns_hnw.png"
    plot_sequence_of_returns(json_path, out)

    old = Path(FIGURES_DIR) / "sequence_of_returns_60_40.png"
    if old.exists():
        old.unlink()
        print(f"removed stale: {old}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
