# Lending Club Credit Risk Analysis

**Estimating the cash-flow buffer a lender needs to absorb loan delinquencies.**

This project analyses 2.26 million loans issued between 2007 and 2018 to answer one practical question: *when borrowers stop paying, how much money should a lender hold in reserve to stay solvent?*

It is built in three languages — **Python** (complete), **R** (in progress), and **STATA** (in progress) — each producing the same analysis independently.

---

## 🔴 Try the live risk scorer

The models below are wrapped in an interactive dashboard you can use right now — adjust a hypothetical borrower's profile and watch the risk outputs update live:

**▶ [Open the interactive dashboard](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)**

It runs entirely in the browser on the project's own fitted coefficients. More detail in [section 7](#7-from-analysis-to-tool-the-interactive-dashboard).

---

## The question

When a borrower misses payments for 90 days, the lender loses the cash flow they were counting on. A bank needs to know, in advance, how large a financial cushion to set aside for this. Set it too low and a downturn threatens solvency; set it too high and capital sits idle.

This project builds a statistically grounded answer in three steps:

1. **How likely is a borrower to default?** (Probability of Default)
2. **If they default, how much is actually lost?** (Loss Given Default)
3. **Combining the two, how big should the buffer be — including under a crisis?**

---

## Headline results

| Question | Answer |
|---|---|
| What share of loans go 90 days delinquent? | **12.9%** |
| When a loan defaults, what fraction is lost? | **46.7%** on average |
| Total expected loss across the portfolio | **$2.13 billion** |
| Buffer needed under normal conditions | **$389M** (39% of one month's cash flow) |
| Buffer needed in a 2008-style crisis | **$1.06B** (105% of one month's cash flow) |

The single most important finding: **a severe downturn would require holding more than an entire month of portfolio cash flow in reserve** — nearly three times the normal-conditions buffer.

---

## How the analysis flows

The project moves from understanding the data, to modelling risk, to sizing the buffer, to wrapping it all in a usable tool. Each stage builds on the last.

### 1. Understanding the loans

The first step is exploring who borrows and how loans are graded. Lending Club assigns each loan a grade from A (safest) to G (riskiest), and that grade turns out to be the strongest single signal of risk.

**Delinquency rises steeply with grade** — from 3.3% for Grade A loans to 38.1% for Grade G.

![Delinquency rate by loan grade](output/figures/delinquency_by_grade.png)

The risk variables also relate to each other in sensible ways. For example, borrowers with higher credit scores get lower interest rates, and higher credit utilisation goes hand in hand with lower scores.

![Relationships between risk variables](output/figures/correlation_heatmap.png)

### 2. Tracking loans over time (vintage analysis)

Grouping loans by the quarter they were issued reveals how different "vintages" performed. The 2007–2008 financial crisis is clearly visible, and recent loans appear artificially safe simply because they haven't had time to go bad yet (a known effect called *maturation bias*).

![Delinquency by issue cohort and grade](output/figures/vintage_curves_by_grade.png)

### 3. Stage 1 — How likely is default?

A logistic regression model predicts whether each loan will become 90 days delinquent. It separates risk well (AUC = 0.68), which is solid for an application-time model — meaning it uses only information available at the point a loan is issued, with no look-ahead into future payment history.

More useful than the score is *what the model learned*. Each factor's effect is shown below in percentage points of default risk, with bars showing the 95% confidence interval. Loan grade dominates; higher income and better credit scores are the strongest protective factors.

![What drives a borrower to default](output/figures/marginal_effects.png)

#### What the model can and can't predict

Loan grade is by far the strongest signal — unsurprising, since it is Lending Club's own risk score, already distilled from credit history and income before a loan is issued. It overlaps so heavily with interest rate (the rate is *set* from the grade) that the two rise in near-perfect lockstep:

| Delinquency rises with grade | Interest rate rises with grade |
|---|---|
| ![Delinquency by grade](output/figures/delinquency_by_grade.png) | ![Interest rate by grade](output/figures/interest_rate_by_grade.png) |

That tight overlap is what makes interest rate's coefficient behave strangely — a problem dissected in the next section.

But the bigger point is the ceiling: at AUC ≈ 0.68, **consumer default is only partly predictable, and that's expected.** The strongest triggers — job loss, illness, divorce — are life events no loan dataset contains. This isn't a weakness in the model; it's the whole reason a buffer exists. If default were perfectly predictable a lender could price it in exactly and hold no reserve. Because it isn't, a cushion sized for the uncertainty is essential — which is what the rest of this project quantifies.

We also model *how quickly* loans fail using survival analysis. Grade A loans stay healthy for years; nearly half of Grade G loans have stopped paying within five years.

![Survival curves by grade](output/figures/kaplan_meier_by_grade.png)

### 4. Stage 2 — How much is lost when default happens?

Knowing a loan will default isn't enough — we need to know how much money is actually lost. A second regression model estimates this "loss given default" for each loan.

The key insight: **loss severity is roughly constant across grades (45–51%)**. In other words, a loan's grade tells you *whether* it will default, but not *how much* you'll lose if it does.

![What determines loss severity](output/figures/lgd_coefficients.png)

#### Diagnosing the coefficients

The loss model has an oddity: the coefficient on grade comes out *negative*, implying worse grades lose less — the opposite of the raw data. The reason becomes obvious once you ask a simpler question: how much of loss severity does each variable explain *on its own*?

| Variable (on its own) | Share of loss severity explained |
|---|---|
| **Months on book** | **68.8%** |
| Revolving utilisation | 0.8% |
| FICO score | 0.6% |
| Loan term | 0.6% |
| Interest rate | 0.5% |
| Loan amount | 0.4% |
| Loan grade | 0.1% |
| Annual income | 0.0% |
| Debt-to-income | 0.0% |

One variable does essentially all the work. **Loss severity is almost entirely a question of *when* a loan fails:** default early and most of the principal is still outstanding; default late and the borrower has already repaid most of it. Grade, FICO, and the rest explain almost nothing by comparison — which is why grade's coefficient in the combined model is small and unstable enough to flip sign. It simply has very little real signal to contribute.

In short: **grade tells you *whether* a borrower defaults; timing tells you *how much* is lost.** Because grade barely affects loss severity, its regression coefficient is unreliable — so wherever this project needs a loss figure per grade (Expected Loss, buffer sizing, the dashboard), it uses the actual average loss observed for each grade instead of the coefficient.

### 5. Putting it together — Expected Loss

Combining the two stages gives **Expected Loss = Probability of Default × Loss Given Default × Loan Exposure** — the standard framework regulated banks use under Basel III.

| Grade | Default probability | Loss if default | Expected loss |
|---|---|---|---|
| A | 3.6% | 45.7% | $104M |
| B | 8.7% | 45.4% | $369M |
| C | 14.4% | 47.0% | **$660M** |
| D | 20.4% | 47.4% | $492M |
| E | 28.3% | 46.8% | $313M |
| F | 36.4% | 47.4% | $138M |
| G | 40.0% | 50.6% | $50M |
| **Total** | | | **$2,126M** |

A subtle but important result: **Grade C loans drive the largest absolute loss** ($660M) — not because they are the riskiest, but because there are so many of them. Concentration matters as much as risk rate.

![Two-stage Expected Loss by grade](output/figures/expected_loss_by_grade.png)

### 6. Sizing the buffer

Finally, the buffer itself. Under normal conditions the portfolio needs roughly **$389M** — about 39% of a month's scheduled cash flow. But the buffer must survive bad years, not just average ones, so it is stress-tested against progressively worse delinquency rates.

| Scenario | Delinquency rate | Buffer required | Share of monthly cash flow |
|---|---|---|---|
| Normal (observed) | 12.9% | $389M | 39% |
| Mild stress | 16.1% | $486M | 48% |
| Moderate stress | 19.3% | $583M | 58% |
| Severe (2007 crisis level) | 35.0% | $1,057M | 105% |

![Buffer under stress scenarios](output/figures/buffer_scenarios.png)

Because recovery rates are uncertain, a sensitivity table shows the buffer across every combination of delinquency and recovery assumptions — giving decision-makers a full picture rather than a single number.

![Buffer sensitivity analysis](output/figures/buffer_sensitivity.png)

---

### 7. From analysis to tool: the interactive dashboard

The final step turns the static models into something a lender could actually use. [`index.html`](index.html) is a self-contained dashboard ([live here](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)) that loads the project's fitted coefficients directly into the browser — no server, no install.

Set a borrower's profile and you immediately see their probability of default, expected loss, and where they rank against the whole portfolio. A live survival curve shows *when* the risk materialises, and a Monte Carlo panel draws 1,000 random loans matching the real grade mix to estimate the reserve such a portfolio would need. It pulls every stage of the project — PD, LGD, survival, and buffer — into one screen.

---

## What's in this repository

```
├── index.html            ← interactive risk dashboard (live demo)
├── data/
│   ├── raw/              ← original CSV (not tracked — too large for GitHub)
│   └── processed/        ← cleaned data (generated by 00_ingest.py, not tracked)
├── python/               ← complete analysis
│   ├── 00_ingest.py      ← load and clean the data
│   ├── 01_eda.ipynb      ← explore the loans
│   ├── 02_cohort.ipynb   ← vintage analysis over time
│   ├── 03_models.ipynb   ← Stage 1 (default) + Stage 2 (loss)
│   ├── 04_buffer.ipynb   ← buffer sizing and stress tests
│   └── requirements.txt
├── r/                    ← R implementation (in progress)
├── stata/                ← STATA implementation (in progress)
├── output/figures/       ← all charts
└── README.md
```

Note: `data/` is not tracked in this repository. After cloning, create `data/raw/`, download the Lending Club CSV into it, and run the ingest script to build the processed dataset.

---

## Method summary

| Phase | Method | Library |
|---|---|---|
| Data cleaning | Column selection, date parsing, feature engineering | `pandas`, `numpy` |
| EDA | Distributions, correlation matrix, cohort analysis | `matplotlib`, `seaborn` |
| Vintage analysis | Cohort curves by grade and year | `pandas`, `matplotlib` |
| Stage 1 — PD | Logistic regression (application-time features only) | `scikit-learn`, `statsmodels` |
| Time-to-stoppage | Cox proportional hazards, Kaplan-Meier | `lifelines` |
| Stage 2 — LGD | OLS regression | `statsmodels` |
| Buffer sizing | Scenario analysis, sensitivity table | `numpy` |

**In plain terms:** `pandas` and `numpy` did the heavy lifting of loading 2.26M loans and reshaping the raw data into clean, model-ready variables. `matplotlib` and `seaborn` produced every chart in this README. The Stage 1 default model was built with `scikit-learn` (for the prediction and accuracy scoring) and `statsmodels` (for the regression coefficients and significance tests). `lifelines` handled the survival analysis — measuring not just *whether* a loan defaults but *how quickly*. The Stage 2 loss model used `statsmodels` for a standard regression. The final buffer figures were straightforward arithmetic on the model outputs, handled in `numpy`.

---

## Running it yourself

```bash
# Install dependencies
pip install -r python/requirements.txt

# Download the Lending Club CSV from Kaggle into data/raw/
# then build the cleaned dataset from the project root:
python python/00_ingest.py

# Open the analysis notebooks
jupyter notebook python/
```

Requires Python 3.10 or newer. The raw CSV (`accepted_2007_to_2018Q4.csv`) must be downloaded manually from [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) and placed in `data/raw/` before running the ingest script.

---

## Important caveats

- **This is consumer credit data.** Lending Club loans are unsecured personal loans. The methodology transfers to commercial lending and leases, but the specific numbers would differ.
- **Recent loans look deceptively safe.** Loans from 2017–2018 hadn't matured when the data was collected, so their delinquency rates understate true risk.
- **The delinquency label is approximate.** Lending Club's available status "Late (31-120 days)" is the closest proxy for 90-day delinquency in this dataset; the 31-day lower bound means some loans in this bucket may have subsequently cured.
- **The PD model uses application-time features only.** Post-origination variables (e.g. months on book) are excluded from the default model to avoid data leakage, and are used only in the survival and loss severity analyses where they are appropriate.
- **Models simplify reality.** Default is partly driven by unpredictable life events, so even a good model leaves meaningful uncertainty — which is exactly why a buffer is needed.

---

## Data source

[Lending Club Loan Data — Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) · `accepted_2007_to_2018Q4.csv` (2.26M loans, 151 columns)
