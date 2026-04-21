"""Aggregate sequence-risk analysis: for all 10k paths, simulate forward vs
reversed return order under the same inflation-indexed withdrawal schedule
and characterize the distribution of fwd/rev terminal-wealth ratios.
"""
from __future__ import annotations

import json
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
    INITIAL_WEALTH,
    LEGACY_TARGET_REAL,
    RESULTS_DIR,
)


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    with pkl.open("rb") as f:
        data = pickle.load(f)
    combo = data["results"][("traditional_60_40", "baseline")]
    W = combo["wealth_paths"]  # (n_paths, 121) nominal
    n_paths, ncol = W.shape
    n_q = ncol - 1

    infl_q = INFLATION_BASE / 4
    spend_q_real = ANNUAL_SPEND_REAL / 4
    withdrawals_nominal = spend_q_real * (1 + infl_q) ** np.arange(1, n_q + 1)
    deflator = (1 + infl_q) ** np.arange(n_q + 1)
    target_real = LEGACY_TARGET_REAL

    # Reconstruct quarterly gross returns per path
    returns = (W[:, 1:] + withdrawals_nominal) / W[:, :-1] - 1.0

    # Simulate forward (should match W) and reversed
    rev_returns = returns[:, ::-1]
    Wfwd = np.zeros_like(W)
    Wrev = np.zeros_like(W)
    Wfwd[:, 0] = INITIAL_WEALTH
    Wrev[:, 0] = INITIAL_WEALTH
    for q in range(n_q):
        Wfwd[:, q + 1] = Wfwd[:, q] * (1 + returns[:, q]) - withdrawals_nominal[q]
        Wrev[:, q + 1] = Wrev[:, q] * (1 + rev_returns[:, q]) - withdrawals_nominal[q]

    # Sanity: forward re-simulation should match stored wealth
    max_err = float(np.max(np.abs(Wfwd - W)))
    print(f"sanity check: max |Wfwd - W_original| = {max_err:.2e}")

    # Deflate to real $
    fwd_T = Wfwd[:, -1] / deflator[-1]
    rev_T = Wrev[:, -1] / deflator[-1]

    # Direction classification
    inverted = fwd_T > rev_T       # forward > reversed
    classic = rev_T > fwd_T        # reversed > forward
    pct_inverted = float(inverted.mean())
    pct_classic = float(classic.mean())

    # Ratio (only where both > 0 for clean ratios)
    both_pos = (fwd_T > 0) & (rev_T > 0)
    ratio = fwd_T[both_pos] / rev_T[both_pos]
    med_ratio = float(np.median(ratio))
    p25_ratio = float(np.percentile(ratio, 25))
    p75_ratio = float(np.percentile(ratio, 75))
    p95_ratio = float(np.percentile(ratio, 95))

    mean_fwd = float(fwd_T.mean())
    mean_rev = float(rev_T.mean())
    succ_fwd = float((fwd_T >= target_real).mean())
    succ_rev = float((rev_T >= target_real).mean())

    # Stratify by worst-year timing
    # Annual gross return per path: product of 4 quarterly gross returns
    q_gross = 1.0 + returns
    annual_gross = q_gross.reshape(n_paths, 30, 4).prod(axis=2)  # (n_paths, 30)
    worst_year = annual_gross.argmin(axis=1) + 1                  # 1..30

    buckets = [
        ("1-10",  (worst_year >= 1)  & (worst_year <= 10)),
        ("11-20", (worst_year >= 11) & (worst_year <= 20)),
        ("21-30", (worst_year >= 21) & (worst_year <= 30)),
    ]

    # --- Histogram of ratio (log scale) ---
    safe_ratio = ratio[(ratio > 0) & np.isfinite(ratio)]
    lo = max(float(np.percentile(safe_ratio, 0.5)), 1e-3)
    hi = min(float(np.percentile(safe_ratio, 99.5)), 1e3)
    bins = np.logspace(np.log10(lo), np.log10(hi), 60)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(safe_ratio, bins=bins, color="#4a7dbf", edgecolor="white",
            linewidth=0.5)
    ax.set_xscale("log")
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.5)
    ax.set_xlabel("Forward / Reversed terminal-wealth ratio (log scale)",
                  fontsize=11)
    ax.set_ylabel("Count of paths", fontsize=11)
    ax.set_title("Sequence-of-returns direction across 10,000 paths "
                 "(60/40, baseline)", fontsize=12)
    ax.text(0.97, 0.95, f"Inverted (fwd > rev): {pct_inverted:.1%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=10,
            color="#0b3d91",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="gray", alpha=0.9))
    ax.text(0.03, 0.95, f"Classic (rev > fwd): {pct_classic:.1%}",
            transform=ax.transAxes, ha="left", va="top", fontsize=10,
            color="#b04a2f",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="gray", alpha=0.9))
    ax.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.5)
    fig.tight_layout()
    out_hist = Path(FIGURES_DIR) / "sequence_ratio_distribution.png"
    fig.savefig(out_hist, dpi=150)
    plt.close(fig)

    # --- Printed output ---
    print()
    print("=" * 72)
    print("Aggregate sequence-risk direction (60/40, baseline, n=10,000)")
    print("=" * 72)
    print(f"Paths with forward > reversed (inverted) : {pct_inverted:.1%}")
    print(f"Paths with reversed > forward (classic)  : {pct_classic:.1%}")
    print(f"Median ratio (fwd/rev)                  : {med_ratio:.3f}")
    print(f"IQR of ratio [p25, p75]                 : [{p25_ratio:.3f}, "
          f"{p75_ratio:.3f}]")
    print(f"p95 of ratio                            : {p95_ratio:.3f}")
    print(f"Mean forward terminal (real)            : ${mean_fwd/1e6:6.2f}M")
    print(f"Mean reversed terminal (real)           : ${mean_rev/1e6:6.2f}M")
    print(f"Forward success rate (>= $20M real)     : {succ_fwd:.1%}")
    print(f"Reversed success rate (>= $20M real)    : {succ_rev:.1%}")

    print()
    print("=" * 72)
    print("Stratified by year with worst annual return")
    print("=" * 72)
    print(f"{'bucket':<10}{'N':>6}  "
          f"{'mean fwd $M':>14}{'mean rev $M':>14}  "
          f"{'fwd succ':>10}{'rev succ':>10}")
    for label, mask in buckets:
        n = int(mask.sum())
        if n == 0:
            print(f"  years {label:<5}  empty bucket")
            continue
        mf = float(fwd_T[mask].mean()) / 1e6
        mr = float(rev_T[mask].mean()) / 1e6
        sf = float((fwd_T[mask] >= target_real).mean())
        sr = float((rev_T[mask] >= target_real).mean())
        print(f"  years {label:<4}{n:>6}  "
              f"{mf:>13.2f}M{mr:>13.2f}M  {sf:>10.1%}{sr:>10.1%}")

    print()
    print("=" * 72)
    print("Interpretation")
    print("=" * 72)
    if pct_inverted > 0.50:
        verdict = ("Sequence risk systematically inverts at low WR "
                   "(forward > reversed > 50% of paths).")
    elif pct_classic > 0.60:
        verdict = ("Classic Bengen direction holds at low WR, "
                   "with weakened magnitude.")
    else:
        verdict = ("Sequence risk is path-dependent at low WR, "
                   "not directionally uniform.")
    print(verdict)
    print()
    print(f"Histogram saved: {out_hist}")

    strat_rows = []
    for label, mask in buckets:
        n = int(mask.sum())
        if n == 0:
            continue
        strat_rows.append({
            "bucket": label,
            "n": n,
            "mean_fwd_real": float(fwd_T[mask].mean()),
            "mean_rev_real": float(rev_T[mask].mean()),
            "fwd_success_20M": float((fwd_T[mask] >= target_real).mean()),
            "rev_success_20M": float((rev_T[mask] >= target_real).mean()),
        })

    json_payload = {
        "portfolio": "traditional_60_40",
        "scenario": "baseline",
        "n_paths": int(n_paths),
        "aggregate": {
            "pct_inverted_fwd_gt_rev": pct_inverted,
            "pct_classic_rev_gt_fwd": pct_classic,
            "median_ratio": med_ratio,
            "p25_ratio": p25_ratio,
            "p75_ratio": p75_ratio,
            "p95_ratio": p95_ratio,
            "mean_fwd_real": mean_fwd,
            "mean_rev_real": mean_rev,
            "fwd_success_20M": succ_fwd,
            "rev_success_20M": succ_rev,
            "verdict": verdict,
        },
        "ratios": ratio.tolist(),
        "stratified": strat_rows,
    }
    json_path = RESULTS_DIR / "sequence_risk_distribution.json"
    with json_path.open("w") as f:
        json.dump(json_payload, f)
    print(f"JSON saved:      {json_path}")


if __name__ == "__main__":
    main()
