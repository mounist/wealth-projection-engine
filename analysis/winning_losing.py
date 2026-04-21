"""Primary Output #5: anatomy of success vs failure paths.

Split paths by terminal_real vs target, then compare:
  - regime-occupancy fractions (full horizon, first 10y, last 10y)
  - starting regime distribution
  - median wealth trajectory (with p25-p75 band)
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

from config import FIGURES_DIR, INFLATION_BASE, RESULTS_DIR  # noqa: E402

COLOR_SUCC = "#2e8b57"
COLOR_FAIL = "#b04a2f"
REGIME_LABELS = ["R1", "R2", "R3"]

PORTFOLIO_LABEL = {
    "aggressive_80_20":   "80/20 Aggressive",
    "traditional_60_40":  "60/40 Traditional",
    "moderate_40_60":     "40/60 Moderate",
    "preservation_25_75": "25/75 Preservation",
}


def _regime_fractions(regime_paths_slice: np.ndarray) -> np.ndarray:
    """Per-path regime occupancy fraction over a slice of quarters.
    Returns (n_paths, 3) array.
    """
    n, q = regime_paths_slice.shape
    out = np.zeros((n, 3))
    for r in (0, 1, 2):
        out[:, r] = (regime_paths_slice == r).mean(axis=1)
    return out


def analyze_path_anatomy(results_pkl_path: str | Path,
                         portfolio_key: str,
                         scenario_key: str,
                         target: float,
                         output_path: str | Path) -> dict:
    with Path(results_pkl_path).open("rb") as f:
        data = pickle.load(f)
    combo = data["results"][(portfolio_key, scenario_key)]

    W = combo["wealth_paths"]        # (n, 121) nominal
    rp = combo["regime_paths"]       # (n, 120) regime indices
    n_paths, ncol = W.shape
    n_q = ncol - 1

    infl_q = INFLATION_BASE / 4
    deflator = (1 + infl_q) ** np.arange(n_q + 1)
    W_real = W / deflator

    terminal_real = W_real[:, -1]
    succ_mask = terminal_real >= target
    fail_mask = ~succ_mask
    n_succ = int(succ_mask.sum())
    n_fail = int(fail_mask.sum())

    frac_full = _regime_fractions(rp)
    frac_first = _regime_fractions(rp[:, :40])     # quarters 0..39
    frac_last = _regime_fractions(rp[:, -40:])     # quarters 80..119
    start_regime = rp[:, 0]

    def _starting_dist(mask: np.ndarray) -> np.ndarray:
        sr = start_regime[mask]
        return np.array([(sr == r).mean() for r in (0, 1, 2)])

    summary = {
        "n_succ": n_succ,
        "n_fail": n_fail,
        "full":  {"succ": frac_full[succ_mask].mean(axis=0),
                  "fail": frac_full[fail_mask].mean(axis=0)},
        "first": {"succ": frac_first[succ_mask].mean(axis=0),
                  "fail": frac_first[fail_mask].mean(axis=0)},
        "last":  {"succ": frac_last[succ_mask].mean(axis=0),
                  "fail": frac_last[fail_mask].mean(axis=0)},
        "starting": {"succ": _starting_dist(succ_mask),
                     "fail": _starting_dist(fail_mask)},
        "mean_terminal_real": {
            "succ": float(terminal_real[succ_mask].mean()),
            "fail": float(terminal_real[fail_mask].mean()),
        },
    }

    # Trajectory quantiles
    years = np.arange(n_q + 1) / 4.0
    Ws_real = W_real[succ_mask] / 1e6
    Wf_real = W_real[fail_mask] / 1e6
    succ_med = np.median(Ws_real, axis=0)
    succ_p25 = np.percentile(Ws_real, 25, axis=0)
    succ_p75 = np.percentile(Ws_real, 75, axis=0)
    fail_med = np.median(Wf_real, axis=0)
    fail_p25 = np.percentile(Wf_real, 25, axis=0)
    fail_p75 = np.percentile(Wf_real, 75, axis=0)

    # ---------------- Print table ----------------
    print(f"Anatomy: {portfolio_key} x {scenario_key}, "
          f"target=${target/1e6:.0f}M real")
    print("=" * 82)
    print(f"{'':<28}{'Success (N='+str(n_succ)+')':>26}"
          f"{'Failure (N='+str(n_fail)+')':>26}")
    for label, key in [("Full horizon", "full"),
                       ("First 10yr", "first"),
                       ("Last 10yr", "last")]:
        for r in (0, 1, 2):
            row_label = f"{label} R{r+1} frac"
            s = summary[key]["succ"][r] * 100
            f_ = summary[key]["fail"][r] * 100
            print(f"{row_label:<28}{s:>25.1f}%{f_:>25.1f}%")
    for r in (0, 1, 2):
        row_label = f"Starting regime R{r+1}"
        s = summary["starting"]["succ"][r] * 100
        f_ = summary["starting"]["fail"][r] * 100
        print(f"{row_label:<28}{s:>25.1f}%{f_:>25.1f}%")
    print(f"{'Mean terminal real':<28}"
          f"{'$'+format(summary['mean_terminal_real']['succ']/1e6, '.2f')+'M':>26}"
          f"{'$'+format(summary['mean_terminal_real']['fail']/1e6, '.2f')+'M':>26}")

    # ---------------- Plot ----------------
    fig = plt.figure(figsize=(14, 6), constrained_layout=True)
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.6], wspace=0.32)
    axA1 = fig.add_subplot(gs[0, 0])
    axA2 = fig.add_subplot(gs[0, 1], sharey=axA1)
    axA3 = fig.add_subplot(gs[0, 2], sharey=axA1)
    axB = fig.add_subplot(gs[0, 3])

    x = np.arange(3)
    w = 0.36
    max_y = 0.0
    for ax, key, title in [(axA1, "full", "Full 30y"),
                           (axA2, "first", "First 10y"),
                           (axA3, "last", "Last 10y")]:
        s = summary[key]["succ"] * 100
        f_ = summary[key]["fail"] * 100
        ax.bar(x - w/2, s, width=w, color=COLOR_SUCC, label="Success")
        ax.bar(x + w/2, f_, width=w, color=COLOR_FAIL, label="Failure")
        for xi, v in zip(x - w/2, s):
            ax.text(xi, v + 0.8, f"{v:.1f}", ha="center", va="bottom",
                    fontsize=8, color=COLOR_SUCC)
        for xi, v in zip(x + w/2, f_):
            ax.text(xi, v + 0.8, f"{v:.1f}", ha="center", va="bottom",
                    fontsize=8, color=COLOR_FAIL)
        ax.set_xticks(x)
        ax.set_xticklabels(REGIME_LABELS, fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.5, alpha=0.5)
        max_y = max(max_y, s.max(), f_.max())

    axA1.set_ylim(0, max_y * 1.20)
    axA1.set_ylabel("Mean regime occupancy (%)", fontsize=11)
    axA1.legend(loc="upper right", fontsize=9, framealpha=0.9)
    for ax in (axA2, axA3):
        plt.setp(ax.get_yticklabels(), visible=False)

    # Panel B: trajectory
    axB.fill_between(years, succ_p25, succ_p75, color=COLOR_SUCC, alpha=0.20)
    axB.fill_between(years, fail_p25, fail_p75, color=COLOR_FAIL, alpha=0.20)
    axB.plot(years, succ_med, color=COLOR_SUCC, linewidth=2.2,
             label=f"Success median (N={n_succ})")
    axB.plot(years, fail_med, color=COLOR_FAIL, linewidth=2.2,
             label=f"Failure median (N={n_fail})")
    axB.axhline(target / 1e6, color="black", linestyle="--", linewidth=1.2,
                label=f"Target ${target/1e6:.0f}M real")
    axB.set_xlabel("Years", fontsize=11)
    axB.set_ylabel("Real Wealth ($M)", fontsize=11)
    axB.set_xlim(0, n_q / 4)
    axB.set_ylim(bottom=0)
    axB.grid(True, linestyle=":", linewidth=0.5, alpha=0.55)
    axB.legend(loc="upper left", fontsize=9, framealpha=0.9)
    axB.set_title("Median wealth trajectory (shaded: p25-p75)", fontsize=11)

    fig.suptitle(
        f"Anatomy of Success vs Failure "
        f"({PORTFOLIO_LABEL[portfolio_key]}, {scenario_key.capitalize()} "
        f"Scenario, ${target/1e6:.0f}M Target)",
        fontsize=13,
    )
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return summary


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    out = Path(FIGURES_DIR) / "winning_losing_anatomy.png"
    analyze_path_anatomy(pkl, "traditional_60_40", "baseline",
                         20_000_000, out)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
