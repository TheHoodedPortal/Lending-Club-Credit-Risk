# Lending Club Credit Risk Analysis

A quantitative credit risk project analysing 10 years of Lending Club loan data (2007–2018) to identify predictors of 90-day payment stoppages and estimate the cash-flow buffer required to absorb interruptions.

Built in three languages — **Python** (complete), **R** (in progress), and **STATA** (in progress) — to demonstrate cross-platform analytical capability.

---

## Key findings

| Metric | Value |
|---|---|
| Portfolio size | 2,258,957 loans |
| Overall 90-day delinquency rate | 11.92% |
| Worst cohort | 2007 Q4 (Grade G: 48.6%) |
| Logistic regression AUC | 0.716 |
| Cox model concordance | 0.677 |
| Base buffer requirement | $360M (35.8% of monthly CF) |
| Severe stress buffer (2007 peak) | $1.06B (105% of monthly CF) |

---

## Project goal

Lenders need a statistically defensible method for sizing the liquidity buffer required when borrowers enter 90-day delinquency. This project:

1. Reconstructs historical cash-flow streams from 2.26M loans across 11 years
2. Identifies drivers of 90-day payment stoppages via logistic regression and survival analysis
3. Estimates the required buffer using scenario analysis and sensitivity testing
4. Stress-tests the buffer under elevated delinquency conditions including a 2007-level crisis

---

## Data

**Source:** [Lending Club Loan Data — Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club)

- `accepted_2007_to_2018Q4.csv` (~2.26M rows, 151 columns)
- Raw data is excluded from this repo (see `.gitignore`)

---

## Results

### Delinquency by grade
Clear risk ladder from 3.3% (Grade A) to 38.1% (Grade G), confirming Lending Club's grading system is well-calibrated.

![Delinquency by grade](output/figures/delinquency_by_grade.png)

### Vintage curves
Delinquency rates tracked by issue cohort and grade. Notable features: 2007–2008 financial crisis spike, gradual deterioration in F/G grades through 2015–2016, and maturation bias in 2017–2018 cohorts.

![Vintage curves](output/figures/vintage_curves_by_grade.png)

### Survival analysis
Kaplan-Meier curves show Grade A loans maintain 88% survival at 100 months vs Grade G dropping to 43% by month 60.

![Kaplan-Meier curves](output/figures/kaplan_meier_by_grade.png)

### Buffer stress scenarios
| Scenario | Delinquency rate | Buffer required | % of monthly CF |
|---|---|---|---|
| Base (observed) | 11.9% | $360M | 35.8% |
| Mild stress | 14.9% | $450M | 44.7% |
| Moderate stress | 17.9% | $540M | 53.6% |
| Severe (2007 peak) | 35.0% | $1,057M | 105.0% |

![Buffer scenarios](output/figures/buffer_scenarios.png)

### Sensitivity analysis
Buffer requirement across combinations of delinquency rate (5%–35%) and recovery rate (0%–60%).

![Sensitivity heatmap](output/figures/buffer_sensitivity.png)

---

## Methods

| Phase | Method | Library |
|---|---|---|
| Data cleaning | Column selection, date parsing, feature engineering | `pandas`, `numpy` |
| EDA | Distributions, correlation matrix, cohort analysis | `matplotlib`, `seaborn` |
| Vintage analysis | Cohort curves by grade and year | `pandas`, `matplotlib` |
| Delinquency prediction | Logistic regression | `scikit-learn`, `statsmodels` |
| Time-to-stoppage | Cox proportional hazards, Kaplan-Meier | `lifelines` |
| Buffer sizing | Scenario analysis, sensitivity table | `numpy` |

---

## Repository structure

```
├── data/
│   ├── raw/              ← original CSV (gitignored)
│   └── processed/        ← cleaned .parquet output
├── python/
│   ├── 00_ingest.py      ← load, clean, feature engineering
│   ├── 01_eda.ipynb      ← exploratory analysis
│   ├── 02_cohort.ipynb   ← vintage & cohort curves
│   ├── 03_models.ipynb   ← logistic regression, Cox PH survival model
│   ├── 04_buffer.ipynb   ← buffer estimation & stress testing
│   └── requirements.txt
├── r/                    ← in progress
├── stata/                ← in progress
├── output/
│   └── figures/          ← all charts
└── README.md
```

---

## Setup

```bash
cd python
pip install -r requirements.txt

# Run ingestion first
cd ..
python python/00_ingest.py

# Then open Jupyter for the analysis notebooks
jupyter notebook
```

**Python 3.10+** recommended.

---

## Limitations

- Lending Club data represents unsecured consumer credit. Findings are directionally informative for commercial lending and lease portfolios but should be interpreted with that distinction in mind.
- 2017–2018 cohorts show artificially low delinquency rates due to maturation bias — loans have not had sufficient time to season.
- Buffer estimates assume 90-day stoppages result in full loss of 3 months of scheduled cash flow. Recovery rates are modelled separately in the sensitivity analysis.
