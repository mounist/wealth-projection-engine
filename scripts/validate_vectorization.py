"""Validate run_monte_carlo_vectorized against the original.

1) 1000 paths, 60/40, baseline: compare terminal-real distribution stats
   and success rate. Expect distributions to match within MC noise.
2) 10k paths, 60/40, baseline: time the vectorized engine and report
   speedup vs the 117s measured for the original.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import REGIME_PARAMS  # noqa: E402
from simulation.monte_carlo import (  # noqa: E402
    run_monte_carlo,
    run_monte_carlo_vectorized,
)

ALLOC = (0.60, 0.40)
START = 20_000_000
SPEND = 500_000
INFL = 0.025
N_QUARTERS = 120
LEGACY = 20_000_000
SEED = 42

T = get_all_matrices()["baseline"]
cum_infl = (1 + INFL / 4) ** N_QUARTERS


def stats(arr: np.ndarray) -> dict:
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)),
        "p5": float(np.percentile(arr, 5)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
    }


def fmt(label: str, s: dict) -> str:
    return (f"{label:<14} "
            f"mean=${s['mean']/1e6:>7.2f}M  std=${s['std']/1e6:>7.2f}M  "
            f"p5=${s['p5']/1e6:>7.2f}M  p50=${s['p50']/1e6:>7.2f}M  "
            f"p95=${s['p95']/1e6:>7.2f}M")


# --- Step 1: 1000 paths, both engines ---
print("=" * 78)
print("(1) Distribution comparison @ 1000 paths, 60/40, baseline, seed=42")
print("=" * 78)

t0 = time.perf_counter()
orig = run_monte_carlo(T, REGIME_PARAMS, ALLOC, START, SPEND, INFL,
                       1000, N_QUARTERS, SEED)
dt_orig_1k = time.perf_counter() - t0

t0 = time.perf_counter()
vec = run_monte_carlo_vectorized(T, REGIME_PARAMS, ALLOC, START, SPEND, INFL,
                                 1000, N_QUARTERS, SEED)
dt_vec_1k = time.perf_counter() - t0

tr_orig = orig["wealth_paths"][:, -1] / cum_infl
tr_vec = vec["wealth_paths"][:, -1] / cum_infl
succ_orig = float((tr_orig >= LEGACY).mean())
succ_vec = float((tr_vec >= LEGACY).mean())

print(fmt("original", stats(tr_orig)))
print(fmt("vectorized", stats(tr_vec)))
print()
print(f"success @ $20M real: original={succ_orig:.4f}  vectorized={succ_vec:.4f}  "
      f"delta={succ_vec - succ_orig:+.4f}")

s_o, s_v = stats(tr_orig), stats(tr_vec)
mean_rel = abs(s_v["mean"] - s_o["mean"]) / s_o["mean"]
p50_rel = abs(s_v["p50"] - s_o["p50"]) / s_o["p50"]
print(f"relative |delta| : mean={mean_rel:.4f}  p50={p50_rel:.4f}  "
      f"success(pp)={abs(succ_vec - succ_orig)*100:.2f}")
ok_mean = mean_rel < 0.03
ok_p50 = p50_rel < 0.03
ok_succ = abs(succ_vec - succ_orig) < 0.03
print(f"within tolerance : mean<3%={ok_mean}  p50<3%={ok_p50}  "
      f"success<3pp={ok_succ}")

print()
print(f"timing @ 1000 paths:  original={dt_orig_1k:.2f}s  vectorized={dt_vec_1k:.2f}s")

# --- Step 2: 10k paths, vectorized only ---
print()
print("=" * 78)
print("(2) Speed @ 10k paths, 60/40, baseline, seed=42")
print("=" * 78)
t0 = time.perf_counter()
vec10k = run_monte_carlo_vectorized(T, REGIME_PARAMS, ALLOC, START, SPEND, INFL,
                                    10_000, N_QUARTERS, SEED)
dt_vec_10k = time.perf_counter() - t0
tr_vec10k = vec10k["wealth_paths"][:, -1] / cum_infl
succ_vec10k = float((tr_vec10k >= LEGACY).mean())

print(f"original (measured earlier): 117.0s")
print(f"vectorized:                   {dt_vec_10k:.2f}s")
print(f"speedup:                      {117.0/dt_vec_10k:.1f}x")
print(f"vectorized 10k success @ $20M real: {succ_vec10k:.4f}")
print()
print(fmt("vec @ 10k", stats(tr_vec10k)))

print()
if not (ok_mean and ok_p50 and ok_succ):
    print("!! flag: 1k-path distribution check exceeded 3% / 3pp tolerance")
else:
    print("OK: vectorized engine matches original within tolerance.")
