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


def run_monte_carlo_vectorized(T: np.ndarray,
                               regime_params: dict,
                               allocation: tuple,
                               start_wealth: float,
                               real_spend_annual: float,
                               inflation_ann: float,
                               n_paths: int,
                               n_quarters: int,
                               seed: int = 42) -> dict:
    """Vectorized regime-switching Monte Carlo.

    Equivalent in distribution to run_monte_carlo (same regime chain,
    same within-regime MVN) but consumes the RNG in a different order,
    so path-by-path values differ. Statistics match within MC noise.
    """
    np.random.seed(seed)
    stationary = compute_stationary(T)

    regime_paths = np.zeros((n_paths, n_quarters), dtype=int)
    regime_paths[:, 0] = np.random.choice(3, size=n_paths, p=stationary)

    T_cumsum = T.cumsum(axis=1)
    for q in range(1, n_quarters):
        u = np.random.rand(n_paths)
        prev_regime = regime_paths[:, q - 1]
        for r in range(3):
            mask = prev_regime == r
            if mask.any():
                regime_paths[mask, q] = np.searchsorted(T_cumsum[r], u[mask])

    regime_mus = np.zeros((3, 2))
    regime_chols = np.zeros((3, 2, 2))
    for i in range(3):
        p = regime_params[f"R{i + 1}"]
        regime_mus[i] = [p["equity_mu_ann"] / 4, p["bond_mu_ann"] / 4]
        sig_eq = p["equity_sigma_ann"] / 2
        sig_bd = p["bond_sigma_ann"] / 2
        rho = p["correlation"]
        cov_q = np.array([
            [sig_eq ** 2,             rho * sig_eq * sig_bd],
            [rho * sig_eq * sig_bd,   sig_bd ** 2],
        ])
        regime_chols[i] = np.linalg.cholesky(cov_q)

    z = np.random.randn(n_paths, n_quarters, 2)
    returns = np.zeros((n_paths, n_quarters, 2))
    for r in range(3):
        mask = regime_paths == r
        if mask.any():
            returns[mask] = z[mask] @ regime_chols[r].T + regime_mus[r]

    port_returns = (returns[:, :, 0] * allocation[0]
                    + returns[:, :, 1] * allocation[1])

    infl_q = inflation_ann / 4
    spend_q_real = real_spend_annual / 4
    wealth_paths = np.zeros((n_paths, n_quarters + 1))
    wealth_paths[:, 0] = start_wealth
    for q in range(n_quarters):
        wealth_paths[:, q + 1] = wealth_paths[:, q] * (1 + port_returns[:, q])
        nominal_spend = spend_q_real * (1 + infl_q) ** (q + 1)
        wealth_paths[:, q + 1] -= nominal_spend

    return {
        "wealth_paths": wealth_paths,
        "regime_paths": regime_paths,
        "stationary": stationary,
        "initial_regimes": regime_paths[:, 0],
    }


def _draw_regime_paths_and_returns(T, regime_params, n_paths, n_quarters,
                                   allocation, seed):
    """Shared core: regime chain + per-quarter (equity_ret, bond_ret) draws."""
    np.random.seed(seed)
    stationary = compute_stationary(T)

    regime_paths = np.zeros((n_paths, n_quarters), dtype=int)
    regime_paths[:, 0] = np.random.choice(3, size=n_paths, p=stationary)
    T_cumsum = T.cumsum(axis=1)
    for q in range(1, n_quarters):
        u = np.random.rand(n_paths)
        prev = regime_paths[:, q - 1]
        for r in range(3):
            mask = prev == r
            if mask.any():
                regime_paths[mask, q] = np.searchsorted(T_cumsum[r], u[mask])

    regime_mus = np.zeros((3, 2))
    regime_chols = np.zeros((3, 2, 2))
    for i in range(3):
        p = regime_params[f"R{i + 1}"]
        regime_mus[i] = [p["equity_mu_ann"] / 4, p["bond_mu_ann"] / 4]
        sig_eq = p["equity_sigma_ann"] / 2
        sig_bd = p["bond_sigma_ann"] / 2
        rho = p["correlation"]
        cov_q = np.array([
            [sig_eq ** 2,             rho * sig_eq * sig_bd],
            [rho * sig_eq * sig_bd,   sig_bd ** 2],
        ])
        regime_chols[i] = np.linalg.cholesky(cov_q)

    z = np.random.randn(n_paths, n_quarters, 2)
    returns = np.zeros((n_paths, n_quarters, 2))
    for r in range(3):
        mask = regime_paths == r
        if mask.any():
            returns[mask] = z[mask] @ regime_chols[r].T + regime_mus[r]

    return regime_paths, returns, stationary


def run_monte_carlo_taxed(T, regime_params, allocation, start_wealth,
                          real_spend_annual, inflation_ann,
                          n_paths, n_quarters, seed=42,
                          tax_rate_cg=0.15):
    """Vectorized MC with simplified capital-gains tax drag.

    Each quarter, if equity_ret > 0, subtract tax_rate_cg * w_eq * equity_ret
    from the portfolio return. Approximates annual-rebalancing gains tax.
    Simplifications: no tax-loss harvesting, no step-up, no Roth.
    """
    regime_paths, returns, stationary = _draw_regime_paths_and_returns(
        T, regime_params, n_paths, n_quarters, allocation, seed,
    )
    eq = returns[:, :, 0]
    bd = returns[:, :, 1]
    port_returns = allocation[0] * eq + allocation[1] * bd
    port_returns -= np.maximum(eq, 0.0) * allocation[0] * tax_rate_cg

    infl_q = inflation_ann / 4
    spend_q_real = real_spend_annual / 4
    wealth_paths = np.zeros((n_paths, n_quarters + 1))
    wealth_paths[:, 0] = start_wealth
    for q in range(n_quarters):
        wealth_paths[:, q + 1] = wealth_paths[:, q] * (1 + port_returns[:, q])
        nominal_spend = spend_q_real * (1 + infl_q) ** (q + 1)
        wealth_paths[:, q + 1] -= nominal_spend

    return {
        "wealth_paths": wealth_paths,
        "regime_paths": regime_paths,
        "stationary": stationary,
        "initial_regimes": regime_paths[:, 0],
    }


def run_monte_carlo_regime_inflation(T, regime_params, allocation, start_wealth,
                                     real_spend_annual, infl_ann_by_regime,
                                     n_paths, n_quarters, seed=42):
    """Vectorized MC with regime-conditional annual inflation.

    infl_ann_by_regime : iterable of 3 floats [infl_R1, infl_R2, infl_R3].
    Per-path cumulative inflation is computed from the realized regime chain
    and drives both nominal withdrawals and the deflator used by callers.

    Returns wealth_paths, regime_paths, stationary, and per-path cumulative
    inflation factor cum_infl of shape (n_paths, n_quarters+1) with
    cum_infl[:, 0] = 1.
    """
    regime_paths, returns, stationary = _draw_regime_paths_and_returns(
        T, regime_params, n_paths, n_quarters, allocation, seed,
    )
    port_returns = (returns[:, :, 0] * allocation[0]
                    + returns[:, :, 1] * allocation[1])

    infl_q_by_regime = np.asarray(infl_ann_by_regime, dtype=float) / 4.0
    infl_q_path = infl_q_by_regime[regime_paths]           # (n_paths, n_quarters)
    cum_infl = np.cumprod(1.0 + infl_q_path, axis=1)       # (n_paths, n_quarters)
    cum_infl_full = np.concatenate(
        [np.ones((n_paths, 1)), cum_infl], axis=1,
    )                                                       # (n_paths, n_quarters+1)

    spend_q_real = real_spend_annual / 4
    wealth_paths = np.zeros((n_paths, n_quarters + 1))
    wealth_paths[:, 0] = start_wealth
    for q in range(n_quarters):
        wealth_paths[:, q + 1] = (
            wealth_paths[:, q] * (1 + port_returns[:, q])
            - spend_q_real * cum_infl_full[:, q + 1]
        )

    return {
        "wealth_paths": wealth_paths,
        "regime_paths": regime_paths,
        "stationary": stationary,
        "initial_regimes": regime_paths[:, 0],
        "cum_infl": cum_infl_full,
    }
