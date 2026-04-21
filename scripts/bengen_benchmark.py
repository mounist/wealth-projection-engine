"""Bengen benchmark: run vectorized MC with a single regime (degenerate T),
classic Bengen params, 60/40, $1M, 4% WR, 3% inflation, 30 years, 10k paths.

Expected success rate (terminal wealth > 0): ~90-96%.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulation.monte_carlo import run_monte_carlo_vectorized  # noqa: E402

BENGEN = {
    "equity_mu_ann": 0.10,
    "equity_sigma_ann": 0.18,
    "bond_mu_ann": 0.05,
    "bond_sigma_ann": 0.07,
    "correlation": -0.10,
}

# Degenerate transition matrix: all paths start in regime 0, stay there forever.
T_SINGLE = np.array([
    [1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
])
REGIME_PARAMS = {"R1": BENGEN, "R2": BENGEN, "R3": BENGEN}

ALLOC = (0.60, 0.40)
W0 = 1_000_000
SPEND = 40_000
INFL = 0.03
N_PATHS = 10_000
N_QUARTERS = 120
SEED = 42


def main() -> None:
    out = run_monte_carlo_vectorized(
        T=T_SINGLE, regime_params=REGIME_PARAMS, allocation=ALLOC,
        start_wealth=W0, real_spend_annual=SPEND, inflation_ann=INFL,
        n_paths=N_PATHS, n_quarters=N_QUARTERS, seed=SEED,
    )
    W = out["wealth_paths"]  # (n_paths, 121)
    rp = out["regime_paths"]

    # Confirm single regime
    uniq_regimes = np.unique(rp)
    print(f"unique regimes visited: {uniq_regimes.tolist()} (expect [0])")

    terminal = W[:, -1]
    success = float((terminal > 0).mean())
    print()
    print("=" * 78)
    print("Bengen benchmark — single regime, 60/40, $1M, 4% WR, 3% infl, 30y, 10k paths")
    print("=" * 78)
    print(f"success (terminal > 0) : {success:.4f}")
    print(f"terminal wealth  mean  : ${terminal.mean()/1e6:>7.2f}M")
    print(f"                p5     : ${np.percentile(terminal, 5)/1e6:>7.2f}M")
    print(f"                p50    : ${np.percentile(terminal, 50)/1e6:>7.2f}M")
    print(f"                p95    : ${np.percentile(terminal, 95)/1e6:>7.2f}M")
    print(f"global min wealth      : ${W.min()/1e6:>7.2f}M")
    print(f"global max wealth      : ${W.max()/1e6:>7.2f}M")

    # Verdict
    if success >= 0.90:
        verdict = "OK  (>= 90%)"
    elif success >= 0.80:
        verdict = "NOTE: engine OK, returns pessimistic (80-89%)"
    else:
        verdict = "!! BUG SUSPECTED (< 80%)"
    print(f"\nverdict: {verdict}")

    # Additional diagnostics if success < 0.90
    if success < 0.90:
        print()
        print("=" * 78)
        print("Diagnostics (success < 0.90)")
        print("=" * 78)

        # (a) Three representative paths (p5, p50, p95 of terminal wealth)
        order = np.argsort(terminal)
        idx_p5 = int(order[int(0.05 * N_PATHS)])
        idx_p50 = int(order[int(0.50 * N_PATHS)])
        idx_p95 = int(order[int(0.95 * N_PATHS)])
        milestones_q = [0, 4, 20, 40, 60, 80, 100, 120]
        print("\n(a) Wealth trajectory at key quarters, representative paths:")
        header = f"{'quarter':>8} {'year':>5}  " + \
                 f"{'p5-path':>14} {'p50-path':>14} {'p95-path':>14}"
        print(header)
        for q in milestones_q:
            y = q // 4
            v5 = W[idx_p5, q]
            v50 = W[idx_p50, q]
            v95 = W[idx_p95, q]
            print(f"{q:>8} {y:>5}  "
                  f"${v5/1e6:>+12.3f}M ${v50/1e6:>+12.3f}M ${v95/1e6:>+12.3f}M")

        # (b) Withdrawal schedule (nominal)
        infl_q = INFL / 4
        spend_q_real = SPEND / 4
        print("\n(b) Nominal quarterly withdrawal at q+1 = spend_q_real * (1+infl_q)^(q+1)")
        print(f"    expected Y1 Q1 (q=0): $10,000 annualized $40,000")
        print(f"    expected Y15 Q1 (q=56): ~$58K annualized (rule-of-thumb $40K * 1.03^14)")
        print(f"    expected Y30 Q1 (q=116): ~$95K annualized ($40K * 1.03^29)")
        for q in [0, 56, 116]:
            nom = spend_q_real * (1 + infl_q) ** (q + 1)
            y = q // 4 + 1
            print(f"    Y{y:>2} Q1  q={q:>3}  nominal quarterly=${nom:>10,.2f}  "
                  f"annualized=${nom*4:>10,.2f}")

        # (c) Deterministic expected-return check (no stochastic noise)
        mu_port_ann = ALLOC[0] * BENGEN["equity_mu_ann"] + \
                      ALLOC[1] * BENGEN["bond_mu_ann"]
        r_q = mu_port_ann / 4
        Wd = np.zeros(N_QUARTERS + 1)
        Wd[0] = W0
        for q in range(N_QUARTERS):
            Wd[q + 1] = Wd[q] * (1 + r_q) - spend_q_real * (1 + infl_q) ** (q + 1)
        print("\n(c) Deterministic path with expected portfolio return "
              f"({mu_port_ann:.1%} ann, {r_q:.4%} q):")
        print(f"    terminal deterministic wealth : ${Wd[-1]/1e6:>8.3f}M")
        print(f"    MC mean terminal wealth       : ${terminal.mean()/1e6:>8.3f}M")
        print(f"    MC p50 terminal wealth        : ${np.percentile(terminal,50)/1e6:>8.3f}M")
        print(f"    deterministic min along path  : ${Wd.min()/1e6:>8.3f}M "
              f"(at q={int(Wd.argmin())})")


if __name__ == "__main__":
    main()
