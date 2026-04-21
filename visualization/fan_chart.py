"""Primary Output #2: 30-year real-wealth fan chart (one portfolio x one scenario).

p5-p95 (lightest), p25-p75 (darker), p50 (solid), a faint sample of
individual paths, and reference lines at the legacy target and $0.
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

PORTFOLIO_LABELS = {
    "aggressive_80_20":   "Aggressive 80/20",
    "traditional_60_40":  "Traditional 60/40",
    "moderate_40_60":     "Moderate 40/60",
    "preservation_25_75": "Preservation 25/75",
}
SCENARIO_LABELS = {"sticky": "Sticky", "baseline": "Baseline", "fragile": "Fragile"}

SAMPLE_PATHS = 20
SAMPLE_SEED = 42


def _real_wealth(nominal: np.ndarray, infl_ann: float) -> np.ndarray:
    n_q = nominal.shape[1]
    deflator = (1 + infl_ann / 4) ** np.arange(n_q)
    return nominal / deflator


def plot_fan_chart(results_pkl_path: str | Path,
                   portfolio: str,
                   scenario: str,
                   target: float,
                   output_path: str | Path,
                   ylim: tuple[float, float] = (0.0, 130.0)) -> None:
    with Path(results_pkl_path).open("rb") as f:
        data = pickle.load(f)
    combo = data["results"][(portfolio, scenario)]
    nominal = combo["wealth_paths"]
    real = _real_wealth(nominal, INFLATION_BASE) / 1e6  # $M

    n_quarters = real.shape[1] - 1
    years = np.arange(n_quarters + 1) / 4.0

    p5, p25, p50, p75, p95 = np.percentile(real, [5, 25, 50, 75, 95], axis=0)

    fig, ax = plt.subplots(figsize=(12, 6))

    rng = np.random.default_rng(SAMPLE_SEED)
    idx = rng.choice(real.shape[0], size=SAMPLE_PATHS, replace=False)
    for i in idx:
        ax.plot(years, real[i], color="gray", alpha=0.10, linewidth=0.8)

    ax.fill_between(years, p5, p95, color="#4a7dbf", alpha=0.20,
                    label="p5 - p95")
    ax.fill_between(years, p25, p75, color="#4a7dbf", alpha=0.45,
                    label="p25 - p75")
    ax.plot(years, p50, color="#0b3d91", linewidth=2.0, label="Median (p50)")

    target_m = target / 1e6
    ax.axhline(target_m, color="#b04a2f", linestyle="--", linewidth=1.5,
               label=f"Legacy target (${target_m:.0f}M real)")
    ax.axhline(0.0, color="black", linestyle="-", linewidth=0.8,
               label="Failure ($0)")

    ax.set_xlabel("Years", fontsize=11)
    ax.set_ylabel("Real Wealth ($M, 2024 dollars)", fontsize=11)
    ax.set_xlim(0, n_quarters / 4)
    ax.set_ylim(*ylim)
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.6)

    terminal = real[:, -1]
    med_t = float(np.median(terminal))
    p5_t = float(np.percentile(terminal, 5))
    p95_t = float(np.percentile(terminal, 95))
    success = float((terminal >= target / 1e6).mean())
    stats_text = (
        f"Median terminal: ${med_t:.1f}M\n"
        f"P5 / P95: ${p5_t:.1f}M / ${p95_t:.1f}M\n"
        f"Success rate: {success:.1%}"
    )
    ax.text(0.72, 0.05, stats_text, transform=ax.transAxes,
            fontsize=9, va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="gray", alpha=0.9))

    title = (f"30-Year Real Wealth Projection - "
             f"{PORTFOLIO_LABELS[portfolio]} Portfolio "
             f"({SCENARIO_LABELS[scenario]} Regime Scenario)")
    ax.set_title(title, fontsize=12)
    ax.legend(loc="upper left", fontsize=10, framealpha=0.9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    pkl = RESULTS_DIR / "full_mvp.pkl"
    out_dir = Path(FIGURES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plans = [
        ("traditional_60_40",  "baseline", "fan_chart_60_40_baseline_20M.png"),
        ("aggressive_80_20",   "baseline", "fan_chart_80_20_baseline_20M.png"),
        ("moderate_40_60",     "baseline", "fan_chart_40_60_baseline_20M.png"),
        ("preservation_25_75", "baseline", "fan_chart_25_75_baseline_20M.png"),
    ]
    for portfolio, scenario, fname in plans:
        out = out_dir / fname
        plot_fan_chart(pkl, portfolio, scenario, 20_000_000, out)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
