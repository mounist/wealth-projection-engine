"""Project configuration: dates, regimes, seeds, WRDS credentials."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_DIR = ARTIFACTS_DIR / "data"
RESULTS_DIR = ARTIFACTS_DIR / "results"
FIGURES_DIR = ARTIFACTS_DIR / "figures"

for _d in (DATA_DIR, RESULTS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

WRDS_USERNAME = os.environ.get("WRDS_USERNAME", "mounist")

START_DATE = "1990-01-01"
END_DATE = "2024-12-31"

R1_END = "2011-04-30"
R2_END = "2019-01-31"

SEED = 42

INFLATION_BASE = 0.025
INFLATION_STRESS_R3 = 0.04

LEGACY_TARGET_REAL = 20_000_000  # locked after Day 1 prototype validation

INITIAL_WEALTH = 20_000_000
ANNUAL_SPEND_REAL = 500_000
HORIZON_YEARS = 30

PORTFOLIOS = {
    "aggressive_80_20":   (0.80, 0.20),
    "traditional_60_40":  (0.60, 0.40),
    "moderate_40_60":     (0.40, 0.60),
    "preservation_25_75": (0.25, 0.75),
}

# Hybrid calibration following standard institutional CMA practice:
#   - Volatilities and correlations: EMPIRICAL from CRSP over
#     Bai-Perron windows (these moments are stable features of
#     the regime)
#   - Expected returns: FORWARD-LOOKING, not realized historical
#     (R3's 14.65% realized equity return reflects the 2020-2024
#     AI rally and is not sustainable as a 30-year forward
#     expectation; R1's 5.2% reflects the 2000s lost decade)
# See artifacts/results/regime_params_empirical.json for full
# empirical values.
REGIME_PARAMS = {
    "R1": {
        "label": "Accumulation (2001-01 to 2011-04)",
        "n_months_historical": 124,
        "equity_mu_ann": 0.070,     # forward (not realized 5.2%)
        "equity_sigma_ann": 0.169,  # empirical
        "bond_mu_ann": 0.040,       # forward (not realized 5.85%)
        "bond_sigma_ann": 0.077,    # empirical
        "correlation": -0.317,      # empirical
    },
    "R2": {
        "label": "QE era (2011-05 to 2019-01)",
        "n_months_historical": 93,
        "equity_mu_ann": 0.090,     # forward, close to realized 10.08%
        "equity_sigma_ann": 0.121,  # empirical
        "bond_mu_ann": 0.030,       # forward, close to realized 3.43%
        "bond_sigma_ann": 0.057,    # empirical
        "correlation": -0.380,      # empirical
    },
    "R3": {
        "label": "Post-QE (2019-02 to present)",
        "n_months_historical": 71,
        "equity_mu_ann": 0.070,     # forward (realized 14.65% is AI-rally artifact)
        "equity_sigma_ann": 0.176,  # empirical
        "bond_mu_ann": 0.040,       # forward (realized -0.09% is 2022 hike shock artifact)
        "bond_sigma_ann": 0.084,    # empirical
        "correlation": +0.273,      # empirical
    },
}

TRANSITION_DURATIONS = {
    "R1_months": 124,   # observed 2001-01 to 2011-04
    "R2_months": 93,    # observed 2011-05 to 2019-01
    "R3_scenarios": {
        "baseline": 100,   # prior: median of R1/R2
        "sticky": 200,     # structural shift hypothesis
        "fragile": 48,     # transient aberration hypothesis
    },
}
