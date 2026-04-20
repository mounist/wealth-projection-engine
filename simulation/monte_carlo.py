"""Regime-switching Monte Carlo engine (quarterly step).

Design:
    - Step size: quarterly (30y = 120 steps). Transition matrix is calibrated
      to quarterly exit rates, so step size must match.
    - Initial regime: sampled from the stationary distribution of T.
    - Returns within a regime: multivariate normal on (equity, bond).
"""
from __future__ import annotations

import numpy as np


def compute_stationary(T: np.ndarray) -> np.ndarray:
    """Stationary distribution: left eigenvector of T with eigenvalue 1."""
    eigvals, eigvecs = np.linalg.eig(T.T)
    idx = np.argmin(np.abs(eigvals - 1.0))
    stat = np.real(eigvecs[:, idx])
    stat = stat / stat.sum()
    assert np.allclose(stat.sum(), 1.0)
    assert (stat >= 0).all()
    return stat


def simulate_regime_path(T: np.ndarray, n_quarters: int,
                         start_regime: int) -> np.ndarray:
    """Single regime-chain path of length n_quarters (int array, 0/1/2)."""
    path = np.zeros(n_quarters, dtype=int)
    path[0] = start_regime
    for q in range(1, n_quarters):
        path[q] = np.random.choice(3, p=T[path[q - 1]])
    return path


def sample_returns_given_regime(regime_idx: int,
                                regime_params: dict) -> np.ndarray:
    """Single-quarter draw of (equity_ret, bond_ret) from regime's MVN.

    Annualized → quarterly:  mu_q = mu_ann / 4,  sigma_q = sigma_ann / 2.
    """
    p = regime_params[f"R{regime_idx + 1}"]
    mu_q = np.array([p["equity_mu_ann"] / 4, p["bond_mu_ann"] / 4])
    sig_eq = p["equity_sigma_ann"] / 2
    sig_bd = p["bond_sigma_ann"] / 2
    rho = p["correlation"]
    cov_q = np.array([
        [sig_eq ** 2,            rho * sig_eq * sig_bd],
        [rho * sig_eq * sig_bd,  sig_bd ** 2],
    ])
    return np.random.multivariate_normal(mu_q, cov_q)


def simulate_wealth_path(regime_path: np.ndarray,
                         regime_params: dict,
                         allocation: tuple,
                         start_wealth: float,
                         real_spend_annual: float,
                         inflation_ann: float) -> np.ndarray:
    """Quarterly wealth trajectory. Returns array of length n_quarters+1."""
    n = len(regime_path)
    wealth = np.zeros(n + 1)
    wealth[0] = start_wealth
    infl_q = inflation_ann / 4
    spend_q_real = real_spend_annual / 4

    for q in range(n):
        eq_ret, bd_ret = sample_returns_given_regime(
            regime_path[q], regime_params
        )
        port_ret = allocation[0] * eq_ret + allocation[1] * bd_ret
        wealth[q + 1] = wealth[q] * (1 + port_ret)
        nominal_spend = spend_q_real * (1 + infl_q) ** (q + 1)
        wealth[q + 1] -= nominal_spend

    return wealth


def run_monte_carlo(T: np.ndarray,
                    regime_params: dict,
                    allocation: tuple,
                    start_wealth: float,
                    real_spend_annual: float,
                    inflation_ann: float,
                    n_paths: int,
                    n_quarters: int,
                    seed: int = 42) -> dict:
    """Run full Monte Carlo, sampling initial regimes from T's stationary."""
    np.random.seed(seed)
    stationary = compute_stationary(T)
    initial_regimes = np.random.choice(3, size=n_paths, p=stationary)

    wealth_paths = np.zeros((n_paths, n_quarters + 1))
    regime_paths = np.zeros((n_paths, n_quarters), dtype=int)

    for p in range(n_paths):
        rp = simulate_regime_path(T, n_quarters, initial_regimes[p])
        regime_paths[p] = rp
        wealth_paths[p] = simulate_wealth_path(
            rp, regime_params, allocation, start_wealth,
            real_spend_annual, inflation_ann,
        )

    return {
        "wealth_paths": wealth_paths,
        "regime_paths": regime_paths,
        "stationary": stationary,
        "initial_regimes": initial_regimes,
    }
