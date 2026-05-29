# Lending Club Credit Risk Analysis

A quantitative credit risk project analysing 10 years of Lending Club loan data to identify predictors of 90-day payment stoppages and estimate the cash-flow buffer required to absorb interruptions.

Built in three languages — **Python**, **R**, and **STATA** — to demonstrate cross-platform analytical capability.

---

## Project goal

VersaBank and similar Schedule I lenders need a statistically defensible method for sizing the liquidity buffer required when borrowers enter 90-day delinquency. This project:

1. Reconstructs historical cash-flow streams from ~2.26M loans (2007–2018)
2. Identifies drivers of 90-day payment stoppages via logistic regression and survival analysis
3. Estimates the required buffer using quantile regression and Monte Carlo simulation
4. Stress-tests the buffer under elevated delinquency scenarios

---

## Data

**Source:** [Lending Club Loan Data — Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club)

- `accepted_2007_to_2018Q4.csv.gz` (~2.26M rows, 151 columns)
- Raw data is excluded from this repo (see `.gitignore`)

---

## Repository structure

```
├── data/
│   ├── raw/              ← original CSV (gitignored)
│   └── processed/        ← cleaned outputs
├── python/
│   ├── 00_ingest.py      ← load, clean, feature engineering
│   ├── 01_eda.ipynb      ← exploratory analysis
│   ├── 02_cohort.ipynb   ← vintage & cohort curves
│   ├── 03_models.ipynb   ← logistic regression, Cox PH
│   ├── 04_buffer.ipynb   ← buffer estimation & stress testing
│   └── requirements.txt
├── r/
│   ├── 00_ingest.R
│   ├── 01_eda.R
│   ├── 02_cohort.R
│   ├── 03_models.R
│   ├── 04_buffer.R
│   └── report.qmd
├── stata/
│   ├── 00_ingest.do
│   ├── 01_eda.do
│   ├── 02_cohort.do
│   ├── 03_models.do
│   ├── 04_buffer.do
│   └── master.do
├── output/
│   ├── figures/
│   └── tables/
└── README.md
```

---

## Methods

| Phase | Method | Library |
|---|---|---|
| Delinquency prediction | Logistic regression | `statsmodels`, `scikit-learn` |
| Time-to-stoppage | Cox proportional hazards | `lifelines` |
| Cohort performance | Vintage curve analysis | `pandas`, `matplotlib` |
| Buffer sizing | Quantile regression + Monte Carlo | `statsmodels`, `numpy` |

---

## Key findings

*To be updated as analysis is completed.*

---

## Setup

```bash
cd python
pip install -r requirements.txt
jupyter notebook
```

**Python 3.10+** recommended.

---

## Limitations

Lending Club data represents unsecured consumer credit. Findings are directionally informative for commercial lending and lease portfolios but should be interpreted with that distinction in mind.
