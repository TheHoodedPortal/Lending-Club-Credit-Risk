# Lending Club Credit Risk: Forward-Looking Loss Reserve

How much should a lender set aside today for losses on loans that are still open?

This project estimates that reserve for Lending Club's 2007-2018 consumer-loan book. It cleans 2.26 million loans, learns from loans that have already resolved, then scores the 911,000 loans still open as of the March 2019 servicing snapshot.

The result is a loan-level expected credit loss model, a backtest by vintage, and a single-file browser dashboard.

[Try the live dashboard](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)

## Headline Result

| Measure | Result |
|---|---:|
| Open loans | 911,000 |
| Outstanding principal | $9.5B |
| Base expected credit loss | $1.02B |
| Base reserve rate | 10.7% of outstanding |
| Reserve if default rates double | $1.65B |
| Stressed reserve rate | 17.4% of outstanding |

The base reserve is not a worst-case number. It is the model's current-condition estimate. The stress range is more useful for planning because consumer credit losses move together in downturns.

## What The Model Estimates

The reserve follows the expected-credit-loss framework:

```text
expected loss = probability of default × loss given default × exposure at default
```

That means each open loan needs three estimates:

| Component | Meaning | How this project estimates it |
|---|---|---|
| Probability of default (PD) | Chance the loan defaults over its remaining life | Cox survival models, conditioned on the loan's current age |
| Loss given default (LGD) | Share of the outstanding balance lost after default | Observed average loss on charged-off loans |
| Exposure at default (EAD) | Balance expected to remain if default occurs | Actual current balance rolled forward on the amortization schedule |

The key rule is that a loan is scored only with information available at the scoring date. Outcomes are used to train and validate the model, not as predictors for open loans.

## Data Setup

The raw data is Lending Club's accepted-loans file, `accepted_2007_to_2018Q4.csv`. The servicing fields run through March 2019, so the project uses `2019-03-01` as the snapshot date.

A loan is treated as seriously delinquent if its status is:

- `Late (31-120 days)`
- `Default`
- `Charged Off`
- `Does not meet the credit policy. Status:Charged Off`

By that definition, 12.9% of all loans become delinquent. Risk rises sharply by Lending Club grade, from Grade A to Grade G.

![Delinquency rate by loan grade](output/figures/delinquency_by_grade.png)

The data is split into two working groups:

- **Resolved loans:** fully paid, charged off, or defaulted loans with known outcomes. These form the training history.
- **Active loans:** current, grace-period, or late loans still open at the snapshot. These are the loans being reserved against.

Recent loans can look artificially safe because they have not had enough time to fail. The model handles that by using survival analysis rather than treating every current loan as permanently good.

![Delinquency by issue cohort and grade](output/figures/vintage_curves_by_grade.png)

## Default Risk

The project uses two views of default risk.

First, a logistic regression explains which application-time features separate safer borrowers from riskier borrowers. It is trained only on matured loans, so each training label is a final outcome rather than a loan that is merely current so far. The out-of-time AUC on the matured 2015 cohort is 0.68.

![What drives a borrower to default](output/figures/marginal_effects.png)

The strongest signals are the lender's own pricing and grade, followed by borrower income and credit score. Interest rate and grade should be read together: they are highly correlated because the rate is largely set from the grade.

Second, the reserve needs timing, not just a lifetime yes/no probability. A Cox survival model estimates month-by-month default risk. A second Cox model estimates early payoff, because a loan that prepays can no longer default. The reserve walks both hazards forward together as competing risks.

![Survival curves by grade](output/figures/kaplan_meier_by_grade.png)

This lets the model score a loan from where it is today. A loan that has already survived 20 months is not treated like a brand-new loan; the model prices only the remaining term.

## Loss Severity

For charged-off loans, loss is measured on the outstanding principal at default:

```text
LGD = (principal still owed - recoveries) / principal still owed
```

Severity is not meaningfully predictable from the available borrower or loan features. A regression on grade, rate, FICO, income, term, and other fields explains less than 1% of LGD variation.

The project therefore uses the observed average: Lending Club recovered about 11 cents per dollar owed, so LGD is about 89%.

![Loss given default on the outstanding balance](output/figures/lgd_outstanding.png)

The fact that older loans usually lose fewer dollars is handled through EAD, not LGD. As a loan amortizes, there is less balance left to lose.

## Reserve Calculation

For each active loan, the model starts from its current age and current outstanding balance. Each future month has three possible outcomes:

- the loan defaults,
- the loan prepays,
- or the loan survives to the next month.

If default happens in a month, the loss is the LGD multiplied by the balance expected to remain in that month. Summing those probability-weighted losses across all months and all active loans gives the reserve.

![Forward-looking ECL by grade](output/figures/ecl_by_grade.png)

Base result: **$1.02B** expected credit loss on **$9.5B** outstanding, or **10.7%** of the active book. Grade C contributes the largest dollar loss because it has the most outstanding balance, not because it is the riskiest grade.

Loans already `Late (31-120 days)` are reserved in full as a conservative assumption.

## Stress Scenarios

The stress test scales monthly default probabilities inside the competing-risk walk. That means stressed scenarios change both the chance of default and the expected timing of default.

![Reserve under systemic stress](output/figures/ecl_stress.png)

| Scenario | Reserve | % of outstanding |
|---|---:|---:|
| Base | $1,015M | 10.7% |
| Mild stress (+25% default risk) | $1,187M | 12.5% |
| Moderate stress (+50% default risk) | $1,350M | 14.2% |
| Severe stress (2x default risk) | $1,653M | 17.4% |
| Extreme stress (2.5x default risk) | $1,930M | 20.3% |

With roughly 900,000 loans, individual borrower randomness mostly diversifies away. The bigger risk is systemic: an economy-wide shock that lifts default rates across the book at the same time.

## Backtest

The backtest refits the survival models and LGD using only loans issued through 2014. It then predicts lifetime loss rates by issue year and compares those predictions with realized losses.

![Backtest: predicted vs realized loss by vintage](output/figures/ecl_backtest.png)

The model is reasonably calibrated in normal, fully seasoned years. The 2010-2014 cohorts are within about one percentage point of realized losses. It underpredicts the 2007-2008 crisis cohorts because there is no macroeconomic input, and it modestly underpredicts 2015-2016, when loan performance worsened beyond what the application fields suggested.

That is the central lesson of the backtest: loan-level features can estimate normal-condition losses, but stress overlays are needed for the credit cycle and underwriting shifts.

## Interactive Dashboard

The dashboard is [`index.html`](index.html), also published here:

[https://thehoodedportal.github.io/Lending-Club-Credit-Risk/](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)

It lets you:

- score an example borrower profile,
- see remaining-life default probability,
- estimate exposure and expected loss,
- view the survival curve,
- and switch between portfolio stress scenarios.

The dashboard uses the model payload exported by `python/04_reserve.ipynb` to `output/dashboard_model.json`. `python/05_sync_dashboard.py` embeds that payload into `index.html` so the dashboard stays tied to the latest fitted model.

## Project Layout

```text
.
├── index.html                       # single-file interactive dashboard
├── data/
│   ├── raw/                         # raw Lending Club CSV, not tracked
│   └── processed/                   # generated parquet, not tracked
├── output/
│   ├── dashboard_model.json         # dashboard model payload
│   └── figures/                     # generated charts used in this README
├── python/
│   ├── 00_ingest.py                 # load, clean, snapshot, feature engineering
│   ├── 01_eda.ipynb                 # exploratory charts
│   ├── 02_cohort.ipynb              # vintage and cohort analysis
│   ├── 03_models.ipynb              # default drivers, survival, LGD
│   ├── 04_reserve.ipynb             # reserve, stress scenarios, backtest, export
│   ├── 05_sync_dashboard.py         # embed dashboard_model.json into index.html
│   └── requirements.txt
└── README.md
```

## Running The Project

Install dependencies:

```bash
pip install -r python/requirements.txt
```

Download the Lending Club CSV from Kaggle and place it here:

```text
data/raw/accepted_2007_to_2018Q4.csv
```

Then run:

```bash
python python/00_ingest.py
jupyter notebook python/
```

Run the notebooks in order. After rerunning `04_reserve.ipynb`, refresh the dashboard payload:

```bash
python python/05_sync_dashboard.py
```

The raw CSV is about 1.7GB and is not tracked. The cleaned parquet is generated by `00_ingest.py` and is also not tracked.

## Caveats

- The data is from one unsecured consumer lender. The method transfers better than the exact numbers.
- There is no macroeconomic forecast. The stress scenarios stand in for recession or cycle effects.
- There is no explicit vintage-quality variable. If a cohort is underwritten worse than its application fields imply, the model can miss that.
- LGD is held flat at about 89%. This is supported by the data, but it ignores collection costs and the time value of recoveries.
- Loans already `Late (31-120 days)` are reserved in full. That is conservative because some late loans cure.
- The result should be read as a reserve range, not a single certain number.

## Data Source

[Lending Club Loan Data on Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club): `accepted_2007_to_2018Q4.csv`
