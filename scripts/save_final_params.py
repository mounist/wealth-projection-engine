"""Dump the final hybrid-calibrated REGIME_PARAMS to JSON and print it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import REGIME_PARAMS, RESULTS_DIR  # noqa: E402


def main() -> None:
    out_path = RESULTS_DIR / "regime_params_final.json"
    with out_path.open("w") as f:
        json.dump(REGIME_PARAMS, f, indent=2)

    print("=" * 72)
    print("Final hybrid-calibrated REGIME_PARAMS (from config.py)")
    print("=" * 72)
    print(json.dumps(REGIME_PARAMS, indent=2))
    print()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
