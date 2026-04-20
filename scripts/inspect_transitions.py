"""Print the three scenario transition matrices and their stationary
distributions; save to artifacts/results/transition_matrices.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration.transition_matrix import get_all_matrices  # noqa: E402
from config import RESULTS_DIR  # noqa: E402

LABELS = ["R1", "R2", "R3"]


def stationary(T: np.ndarray) -> np.ndarray:
    """Left eigenvector of T with eigenvalue 1, normalized to sum to 1."""
    vals, vecs = np.linalg.eig(T.T)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    v = np.real(vecs[:, idx])
    v = v / v.sum()
    return v


def print_matrix(name: str, T: np.ndarray) -> None:
    print("=" * 60)
    print(f"Scenario: {name}")
    print("=" * 60)
    header = "       " + "".join(f"{c:>10}" for c in LABELS)
    print(header)
    for i, row_label in enumerate(LABELS):
        cells = "".join(f"{T[i, j]:>10.4f}" for j in range(3))
        print(f"{row_label:<7}{cells}")
    pi = stationary(T)
    print("stationary:   " + "  ".join(f"{LABELS[i]}={pi[i]:.4f}" for i in range(3)))
    print()


def main() -> None:
    matrices = get_all_matrices()
    for name, T in matrices.items():
        print_matrix(name, T)

    out_path = RESULTS_DIR / "transition_matrices.json"
    dump = {
        name: {
            "matrix": T.tolist(),
            "row_labels": LABELS,
            "col_labels": LABELS,
            "stationary": stationary(T).tolist(),
        }
        for name, T in matrices.items()
    }
    with out_path.open("w") as f:
        json.dump(dump, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
