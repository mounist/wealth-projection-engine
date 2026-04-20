"""Regime transition matrix calibration.

Design rationale
----------------
Calibrated (not empirical):
    Post-2019 has zero observed regime exits, so an empirical MLE would be
    degenerate (p_exit_R3 = 0). We instead calibrate exit probabilities from
    observed/assumed average durations via p_exit = 4 / avg_duration_months,
    interpreting the chain at a quarterly step embedded in a monthly return
    stream (hence the factor of 4).

Equal-split off-diagonal:
    Across the calibration sample there is at most one observed transition
    between any pair of regimes. Sample size is insufficient to estimate
    directional transition preferences, so we use an uninformative prior:
    the exit probability from regime i is split equally across the two
    non-current regimes.

Three R3 scenarios:
    Whether the post-2019 regime is transient or structural is an open
    question from the capstone analysis. Rather than pick one, we expose a
    sensitivity axis spanning "transient aberration" (48 months) to
    "structural shift" (200 months), with a baseline at the median of the
    observed R1/R2 durations (100 months).
"""
from __future__ import annotations

import numpy as np


def build_transition_matrix(
    exit_R1: float, exit_R2: float, exit_R3: float
) -> np.ndarray:
    """3x3 row-stochastic transition matrix with equal-split off-diagonal.

    Row i, column j = P(regime at t+1 = j | regime at t = i).
    Exit probability is equally split between the two non-current regimes.
    """
    T = np.array([
        [1 - exit_R1,    exit_R1 / 2,    exit_R1 / 2],
        [exit_R2 / 2,    1 - exit_R2,    exit_R2 / 2],
        [exit_R3 / 2,    exit_R3 / 2,    1 - exit_R3],
    ])
    assert np.allclose(T.sum(axis=1), 1.0), "Rows must sum to 1"
    assert (T >= 0).all(), "All probabilities must be non-negative"
    return T


def get_all_matrices() -> dict[str, np.ndarray]:
    """Return the three scenario transition matrices for sensitivity analysis."""
    EXIT_R1 = 4 / 124
    EXIT_R2 = 4 / 93
    return {
        "baseline": build_transition_matrix(EXIT_R1, EXIT_R2, 4 / 100),
        "sticky":   build_transition_matrix(EXIT_R1, EXIT_R2, 4 / 200),
        "fragile":  build_transition_matrix(EXIT_R1, EXIT_R2, 4 / 48),
    }
