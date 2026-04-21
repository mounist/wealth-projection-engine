"""Load full_mvp.pkl and recompute success rates at $15M / $20M / $25M real.

No Monte Carlo rerun — just rethresholding terminal_real per combo.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PORTFOLIOS, RESULTS_DIR  # noqa: E402

SCENARIOS = ("baseline", "sticky", "fragile")
TARGETS = (15_000_000, 20_000_000, 25_000_000)


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    with pkl.open("rb") as f:
        data = pickle.load(f)
    results = data["results"]

    # success[target][(portfolio, scenario)] = rate
    success: dict[int, dict[tuple[str, str], float]] = {t: {} for t in TARGETS}
    for (pname, scen), r in results.items():
        tr = r["terminal_real"]
        for t in TARGETS:
            success[t][(pname, scen)] = float((tr >= t).mean())

    for t in TARGETS:
        print("=" * 78)
        print(f"Target: ${t/1e6:.0f}M real")
        print("=" * 78)
        header = (f"{'':<22}"
                  f"{'baseline':>10}{'sticky':>10}{'fragile':>10}"
                  f"{'spread(sticky-fragile)':>25}")
        print(header)
        for pname in PORTFOLIOS:
            base = success[t][(pname, "baseline")]
            stick = success[t][(pname, "sticky")]
            frag = success[t][(pname, "fragile")]
            spread_pp = (stick - frag) * 100
            print(f"{pname:<22}"
                  f"{base:>10.1%}{stick:>10.1%}{frag:>10.1%}"
                  f"{spread_pp:>+22.1f}pp")
        print()

    print("=" * 78)
    print("Preservation 25/75 regime spread (sticky minus fragile) vs target:")
    print("=" * 78)
    for t in TARGETS:
        stick = success[t][("preservation_25_75", "sticky")]
        frag = success[t][("preservation_25_75", "fragile")]
        spread_pp = (stick - frag) * 100
        print(f"  ${t/1e6:>5.0f}M target:  {spread_pp:>+6.1f}pp   "
              f"(sticky {stick:.1%}  fragile {frag:.1%})")


if __name__ == "__main__":
    main()
