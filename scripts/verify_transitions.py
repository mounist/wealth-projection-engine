"""Verbatim print of the three scenario transition matrices + verifications."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import TRANSITION_DURATIONS  # noqa: E402

LABELS = ["R1", "R2", "R3"]


def stationary(T: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eig(T.T)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    v = np.real(vecs[:, idx])
    return v / v.sum()


def print_block(name: str, dur: int, T: np.ndarray) -> None:
    print(f"=== {name.upper()} (R3 duration = {dur} months) ===")
    print("          to R1     to R2     to R3")
    for i, rl in enumerate(LABELS):
        print(f"from {rl}   {T[i,0]:.4f}    {T[i,1]:.4f}    {T[i,2]:.4f}")
    pi = stationary(T)
    print(f"    Stationary: [{pi[0]:.4f}, {pi[1]:.4f}, {pi[2]:.4f}]")

    rows_sum_ok = bool(np.allclose(T.sum(axis=1), 1.0))
    nonneg_ok = bool((T >= 0).all())
    pi_sum_ok = bool(np.isclose(pi.sum(), 1.0))
    print(f"    row sums == 1.0 (np.allclose): {rows_sum_ok}")
    print(f"    all entries >= 0:              {nonneg_ok}")
    print(f"    stationary sums to 1.0:        {pi_sum_ok}  (sum={pi.sum():.6f})")
    print()


def main() -> None:
    matrices = get_all_matrices()
    durations = TRANSITION_DURATIONS["R3_scenarios"]
    for name in ("baseline", "sticky", "fragile"):
        print_block(name, durations[name], matrices[name])


if __name__ == "__main__":
    main()
