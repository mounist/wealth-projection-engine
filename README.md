# wealth-projection

Monte Carlo wealth projection with regime-switching returns.

## Layout
- `data/` — WRDS loaders (equity, bond, CPI)
- `calibration/` — regime parameter estimation
- `simulation/` — Monte Carlo engine
- `analysis/` — results analysis
- `visualization/` — plotting
- `artifacts/` — cached data, results, figures (gitignored)

## Setup
```
pip install -r requirements.txt
export WRDS_USERNAME=<your_wrds_user>
```
