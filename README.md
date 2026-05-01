# DATATHON 2026 Round 1

Analysis and forecasting workspace for DATATHON 2026 Round 1. The repository combines raw competition data, notebook-based business analysis, reusable EDA helpers, model experiments, and the final Kaggle-style submission for daily `Revenue` and `COGS` forecasting.

The main forecasting task is to predict daily `Revenue` and `COGS` from `2023-01-01` through `2024-07-01` using historical data from `2012-07-04` through `2022-12-31`.

Final deliverables:

- Final modeling notebook: `notebooks/03.1_timeseries_forecasting.ipynb`
- Final submission file: `submissions/submission_forecast.csv`

## Repository Structure

```text
.
├── data/raw/                  # Released competition datasets and schema notes
│   ├── analytical/            # sales.csv and sample_submission.csv
│   ├── master/                # products, customers, promotions, geography
│   ├── operational/           # inventory and web_traffic
│   └── transaction/           # orders, order_items, payments, shipments, returns, reviews
├── src/datathon_2026_r1/      # Reusable Python helpers
│   └── eda.py                 # Data loading, validation, EDA report builders
├── notebooks/                 # Analysis and modeling notebooks
├── reports/tables/            # Generated EDA and validation tables
├── reports/latex/             # Report source files
├── models/                    # Saved model configuration JSON files
├── submissions/               # Forecast CSV submissions, including final submission_forecast.csv
├── report.tex                 # Current report draft
└── pyproject.toml             # Python package and dependency definition
```

## Environment

This project is configured with `uv` and requires Python `>=3.14`.

```powershell
uv sync
```

For notebook work, use the project environment as a Jupyter kernel:

```powershell
uv run python -m ipykernel install --user --name datathon-2026-r1
```

Core dependencies include `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `xgboost`, `scipy`, `matplotlib`, `seaborn`, `plotly`, `shap`, and `graphviz`.

The final notebook also imports `prophet` and `statsmodels`. Ensure they are installed in the active environment before rerunning `notebooks/03.1_timeseries_forecasting.ipynb`.

## Data

The raw data is grouped into four layers:

- **Master:** `products.csv`, `customers.csv`, `promotions.csv`, `geography.csv`
- **Transaction:** `orders.csv`, `order_items.csv`, `payments.csv`, `shipments.csv`, `returns.csv`, `reviews.csv`
- **Analytical:** `sales.csv`, `sample_submission.csv`
- **Operational:** `inventory.csv`, `web_traffic.csv`

The detailed schema, nullability assumptions, relationship rules, and time coverage are documented in `data/raw/schema.md`.

Current generated EDA summaries show:

- `sales.csv` covers `2012-07-04` to `2022-12-31`.
- `sample_submission.csv` covers `2023-01-01` to `2024-07-01` and contains 548 forecast rows.
- Raw relationship checks have zero unmatched rows for the tracked foreign-key-style joins.
- Inventory quality checks pass for monthly snapshot dates, flags, quantity ranges, fill rate, sell-through rate, and denormalized product attributes.

## Reusable EDA Module

`src/datathon_2026_r1/eda.py` provides the reusable code surface for loading and validating the raw data.

Typical usage:

```python
from datathon_2026_r1.eda import load_all_tables, write_eda_reports

tables = load_all_tables()
report_paths = write_eda_reports(tables)
```

Important helpers include:

- `read_table(name)`: read one named raw CSV with date parsing.
- `load_all_tables()`: load all released tables into memory.
- `table_summary()` and `column_summary()`: create compact dataset summaries.
- `duplicate_key_report()` and `relationship_checks()`: validate key uniqueness and cross-table links.
- `date_coverage()`: summarize date ranges for all known date columns.
- `build_order_revenue()`: derive order-level gross revenue, net revenue, discount, and item COGS.
- `customer_cohort_summary()`: summarize customer signup cohorts.
- `inventory_schema_quality_checks()`: validate operational inventory schema assumptions.
- `write_eda_reports()`: regenerate the CSV reports under `reports/tables/`.

## Final Forecast Notebook

The final competition forecast is produced by:

```text
notebooks/03.1_timeseries_forecasting.ipynb
```

This notebook is the main forecasting narrative and implementation. It includes:

- Forecast-specific EDA for regime drift, seasonality, Tet effects, day-of-week/day-of-month patterns, odd/even year behavior, and Revenue-COGS structure.
- Calendar-only feature engineering with no lag features, designed for the 548-day forecast horizon.
- Three temporal validation folds, with Fold A using 2022 as the primary validation year.
- Base models: Ridge, LightGBM, Prophet, and 4 LightGBM quarter specialists.
- A 3-tier ensemble and calibration stage.
- Final export to `submissions/submission_forecast.csv`.

The notebook's saved pipeline summary states:

- Features: 81 calendar-only features, no lags.
- Models: Ridge, era-weighted LightGBM, Prophet, and 4 Q-Specialists.
- Tier 1: blend base LightGBM with quarter specialists using specialist fraction `alpha = 0.6`, with Q3 routed fully to specialists in the final tuned alpha map.
- Tier 2: combine model families with `Ridge = 0.10`, `Prophet = 0.10`, `LightGBM = 0.80`.
- Tier 3: apply calibration multipliers `CR = 1.26` for Revenue and `CC = 1.32` for COGS.
- Training: log-space targets with era weights, where 2014-2018 receives weight `1.0` and the remaining years receive weight `0.01`.

### Final Submission

The final saved submission is:

```text
submissions/submission_forecast.csv
```

It follows the official sample submission format:

```text
Date,Revenue,COGS
```

Saved sanity checks from the final notebook:

- Shape: `(548, 3)`
- Date range: `2023-01-01` to `2024-07-01`
- Revenue range: `1,143,817` to `11,780,336`
- COGS range: `1,020,827` to `10,813,515`
- Missing values: none
- Negative forecasts: none

## Supporting Notebook Workflow

Other notebooks capture supporting analysis, earlier baselines, and alternative modeling attempts:

- `01_mcq.ipynb`: multiple-choice or requirement-oriented notes.
- `02_eda.ipynb`: raw table loading, missingness, relationship checks, date coverage, customer cohorts, inventory health, and EDA report generation.
- `02.1_fact_table.ipynb`: order-level, customer-level, and cohort fact table construction.
- `Synthesis.ipynb`: business overview dashboard.
- `Demand-side.ipynb`: customer funnel, cohort retention, repeat purchase timing, and revenue concentration analysis.
- `Supply-side.ipynb`: stockout, overstock, inventory-risk, and supply-demand alignment analysis.
- `03_sale_forecast_baseline.ipynb`: initial sales forecasting pipeline with lag and rolling features.
- `03.1_forcast_v2.ipynb`: residual ensemble baseline with calibrated lag/rolling baselines and residual/direct models.
- `03.1_timeseries_forecasting.ipynb`: final time-series forecasting notebook and source of `submissions/submission_forecast.csv`.
- `03.2_forcast_improve.ipynb`: weighted ensemble forecasting using Ridge, Random Forest, and LightGBM variants.
- `03.3_revenue_forecast.ipynb`: revenue forecasting benchmark notebook.

## Final Forecasting Approach

The final notebook is built around the constraint that a 548-day horizon makes direct lag features unreliable or unavailable. It therefore uses calendar-only features that can be computed for every future date before prediction.

The feature set includes:

- Calendar basics: year, month, day, day of week, day of year, quarter, weekend flags, and month-edge distances.
- Edge-of-month indicators: first and last days of month.
- Trend and regime flags: long-run time index and pre/post-regime indicators.
- Fourier seasonality: annual, weekly, and monthly sine/cosine terms.
- Vietnam holiday and Tet proximity features.
- Black Friday and promotion-window features.
- Odd-year indicator for promotion and margin-cycle effects.

The model stack is intentionally diverse:

- **Ridge:** stable global seasonal anchor trained on normalized features in log-space.
- **LightGBM:** main nonlinear learner with era-based sample weighting and two-phase training.
- **Prophet:** decomposition model trained on the post-2020 regime to extrapolate long-horizon seasonality.
- **Q-Specialists:** 4 quarter-focused LightGBM models, each emphasizing one quarter through sample weighting.

The final ensemble applies:

```text
Tier 1: LGB_blend = alpha * Q-specialist + (1 - alpha) * base LightGBM
Tier 2: raw = 0.10 * Ridge + 0.10 * Prophet + 0.80 * LGB_blend
Tier 3: final = calibration_multiplier * raw
```

## Final Notebook Validation Snapshot

The saved Fold A validation comparison in `notebooks/03.1_timeseries_forecasting.ipynb` uses 2022 as the validation period:

| Model | Revenue MAE | COGS MAE |
|---|---:|---:|
| Ridge | `712,634` | `653,334` |
| LightGBM base | `568,480` | `497,792` |
| Prophet | `991,020` | `896,430` |
| Q-Specialist composed | `542,299` | `503,764` |
| Tier 1: LGB Blend | `547,041` | `494,615` |
| Tier 2: 3-Family Blend | `549,072` | `493,537` |
| Tier 3: Calibrated Final | `536,834` | `481,735` |

Older model artifacts are still preserved under `models/`, `reports/tables/`, and `submissions/` for comparison, but they are not the final submission path.

## Reports and Outputs

Generated report tables live in `reports/tables/`. Important groups:

- `eda_*`: data quality, relationship, date coverage, cohort, seasonality, inventory, and payment/revenue proxy checks.
- `03_1_*`: baseline, optimized baseline, residual model, calibration, and feature importance artifacts.
- `03_2_*`: weighted ensemble validation, weights, and feature importance.
- `03_sales_forecast_*`: model validation and feature importance from the broader forecasting benchmark.

Report source files and visual assets include:

- `report.tex`
- `reports/latex/neurips_2025.tex`
- `architecture.png`
- `demand.png`
- `feature_importance.png`
- `output.pdf`

## Regenerating Common Artifacts

Regenerate EDA report tables from the reusable module:

```powershell
uv run python -c "from datathon_2026_r1.eda import load_all_tables, write_eda_reports; write_eda_reports(load_all_tables())"
```

Model artifacts and submissions are currently produced from notebooks rather than a single command-line training script. To reproduce the final submission, run `notebooks/03.1_timeseries_forecasting.ipynb` end to end; it writes `submissions/submission_forecast.csv`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
