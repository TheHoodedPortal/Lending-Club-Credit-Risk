# Lending Club Credit Risk — Forward-Looking Loss Reserve

**How much should a lender set aside today for the losses its current loan book will eventually take?**

This project analyses 2.26 million loans issued between 2007 and 2018, trains credit models on the loans whose outcomes are already known, and uses them to estimate the **expected credit loss on the loans that are still open** — the reserve a lender should hold against its live book. It is built in **Python** (complete), with **R** and **STATA** implementations planned to reproduce the same analysis independently.

---

## 🔴 Try the live risk scorer

The models are wrapped in an interactive dashboard — adjust a borrower's profile and watch the risk outputs update live:

**▶ [Open the interactive dashboard](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)**

It runs entirely in the browser on the project's own fitted coefficients. More in [section 6](#6-the-interactive-dashboard).

---

## The question

A lender holding a book of loans needs to know, *today*, how much to reserve for the losses that book will take over its remaining life. Reserve too little and a downturn threatens solvency; too much and capital sits idle. The standard framework (IFRS 9 / CECL, and Basel) is **Expected Credit Loss**:

```
Expected Loss  =  Probability of Default  ×  Loss Given Default  ×  Exposure
```

The work splits into three model questions, then applies them to the live book:

1. **How likely is a loan to default over its remaining life?** (PD)
2. **If it defaults, how much is lost?** (LGD)
3. **Applied to every open loan and summed — what reserve does the book need, and how does it move in a downturn?**

The crucial discipline throughout: a model used to score a loan today may only use information **known today**. Outcomes and post-origination data train the models; they never leak into a forward prediction.

---

## Headline results

| Question | Answer |
|---|---|
| Outstanding exposure on the active book | **$9.5B** (911k open loans) |
| Expected credit loss on that book (the reserve) | **$1.04B** (10.9% of outstanding) |
| Reserve under a severe (2×) downturn in default rates | **~$1.84B** (19%) |
| Historical 90-day delinquency rate (all loans) | 12.9% |
| Default-model discrimination (AUC, out-of-time test on matured loans) | 0.68 |

The reserve is **model-driven and backtested**: on matured, normal-condition vintages the predicted loss rate matches what actually happened.

---

## The analysis, step by step

### 1. The data, and what "delinquent" means

Every loan carries a Lending Club **grade from A (safest) to G (riskiest)** — the lender's own composite risk score, set before issue. It is the strongest single signal of risk in the data.

A loan is labelled **delinquent** if its status is `Late (31–120 days)`, `Default`, or `Charged Off` (the closest available proxy for a serious, cash-flow-interrupting delinquency). On that definition **12.9%** of loans go bad, climbing steeply with grade — **3.6% for Grade A to 40.0% for Grade G.**

![Delinquency rate by loan grade](output/figures/delinquency_by_grade.png)

The book splits into **resolved loans** (Fully Paid / Charged Off / Default — outcomes known, they anchor what the models learn) and **active loans** (Current / In-grace / Late — still open, the book we *reserve against*; they contribute to the survival model only as censored observations, since their outcomes aren't known yet). Grouping by issue quarter shows the 2007–08 crisis clearly, and shows that recent vintages look deceptively safe because they haven't had time to go bad yet — *maturation bias*, which the forward-looking approach and the backtest both account for.

![Delinquency by issue cohort and grade](output/figures/vintage_curves_by_grade.png)

### 2. Probability of default — and *when*

**Discrimination (application-time).** A logistic regression predicts whether a loan will default using only information available at issue. It is trained and tested **only on matured loans** — those whose full scheduled term had elapsed by the snapshot — so every label is a final lifetime outcome rather than a still-open loan that might yet go bad. The split is temporal: train on matured loans issued ≤ 2014, test out-of-time on the fully-seasoned 2015 cohort (**AUC = 0.68** — solid for consumer credit, where the strongest default triggers are life events no application captures). More useful than the score is *what it learned*: each bar is the change in default probability for a one-standard-deviation increase in a factor, on a common footing. **The price of risk leads — interest rate (the lender's full risk pricing) and grade carry the most signal; higher income and a better credit score are the strongest protective factors.** (Functional form was checked with binned-residual plots: nonlinear terms — a log transform of income, a quadratic in debt-to-income — were tested but didn't improve the out-of-time AUC, so the model is kept linear for simplicity.)

![What drives a borrower to default](output/figures/marginal_effects.png)

The ceiling is the point: at AUC ≈ 0.68 **consumer default is only partly predictable**, because the strongest triggers — job loss, illness, divorce — are life events no loan dataset contains. That irreducible uncertainty is exactly why a reserve exists.

**Timing (the forward-looking engine).** A Cox proportional-hazards survival model captures not just *whether* but *when* loans default. Grade A loans stay healthy for years; nearly half of Grade G loans have stopped paying within five years. This is what makes a forward-looking PD possible: for a loan that has **already survived to its current age**, the model gives its probability of defaulting over its *remaining* life — using only its age today, no look-ahead. The reserve actually fits **two competing hazards — default and early payoff** — because a loan that prepays can no longer default; ignoring that (the classic single-risk shortcut) overstates default risk, which the backtest below makes visible.

![Survival curves by grade](output/figures/kaplan_meier_by_grade.png)

### 3. Loss given default — can we predict it?

When a loan defaults the lender loses the **outstanding principal**, less whatever it recovers (`loss = LGD × exposure-at-default`). The natural question is whether that loss severity can be modelled loan-by-loan, the way default probability is.

**It can't — and that's the finding.** A regression of LGD on *every* loan feature — grade, rate, FICO, income, term, even months-on-book — explains just **0.6%** of its variation, and no single feature reaches 0.2%. On an unsecured loan there's no collateral, so what gets recovered after default is essentially idiosyncratic; it doesn't track the borrower or the loan.

So the honest estimate is simply the **observed average** — and that's a measured fact, not an assumption. For each defaulted loan, take the principal still owed when it stopped paying (borrowed minus repaid), subtract whatever was later clawed back through collections; that's the loss. Across the ~269,000 charged-off loans the lender got back only about **11 cents on the dollar**, so **LGD ≈ 89%** — and flat across grades:

![Loss given default on the outstanding balance](output/figures/lgd_outstanding.png)

The timing effect you might expect in severity — a seasoned loan loses less — isn't gone; it lives in the **exposure**. How much is still owed falls as a loan amortises, so the reserve holds severity flat at ~89% and lets the outstanding balance carry the variation (and at portfolio scale the loan-to-loan scatter diversifies away).

### 4. The forward-looking reserve

Putting the pieces together on the **active book** — every open loan is walked forward month by month from its current age to maturity. Each month it either defaults, pays off early, or survives (the competing-risks probabilities); a default in month *m* loses `LGD (≈89%) × balance owed in month m`, where the balance is the loan's **actual outstanding balance today** rolled forward along its amortisation schedule. Summing the probability-weighted losses over every remaining month and every loan:

![Forward-looking ECL by grade](output/figures/ecl_by_grade.png)

The reserve comes to **$1.04B on $9.5B of outstanding exposure (10.9%)**. **Grade C drives the largest absolute share** ($332M) — not because it's the riskiest, but because there is so much of it. Concentration matters as much as rate. One deliberate conservatism: loans already 31–120 days late are reserved in full (default treated as certain, on today's balance) — real roll rates from that bucket are high but below 100%.

**A bad year is *systemic*, not random.** With ~900k loans, individual-loan default randomness diversifies away almost entirely — a Monte-Carlo over independent defaults gives a 95th percentile essentially equal to the mean. The reserve's real uncertainty is a **downturn lifting everyone's default rate at once**, so the book is stress-tested by scaling PD:

![Reserve under systemic stress](output/figures/ecl_stress.png)

| Scenario | Reserve | % of outstanding |
|---|---|---|
| Base (current conditions) | $1,038M | 10.9% |
| Mild stress (+25% PD) | $1,244M | 13.1% |
| Moderate stress (+50% PD) | $1,448M | 15.3% |
| Severe (2× PD) | $1,844M | 19.4% |

### 5. Does it hold up? A backtest

The honest test: train the models — survival *and* loss severity — on a **past slice** (loans issued ≤ 2014), then predict each vintage's lifetime loss rate and compare to what was actually realized.

![Backtest: predicted vs realized loss by vintage](output/figures/ecl_backtest.png)

On **matured, normal-condition vintages the prediction sits on top of reality**: 2010–2014 land within about a point of realized (e.g. 2011: predicted 9.3% vs realized 10.2%; 2014: 10.1% vs 10.3%). The shaded ≤ 2014 years are in-sample; the matured out-of-sample check is 2015–16, where the model under-calls modestly (9.5% vs 11.2% and 9.3% vs 10.8%) — those cohorts performed worse than their observable features suggested (Lending Club's underwriting drifted in 2015–16), and the model carries no vintage-quality variable. An earlier single-risk version of the model ran 2–4 points *over* on every matured year; treating prepayment as a competing risk is what centred the calibration. Two other gaps are expected and informative: the **2007–08 crisis** vintages are under-predicted because the model has no macro variable, and the most **recent** vintages show predicted above realized simply because those loans haven't had time to default yet. The honest conclusion: loan-level features calibrate the *level* well in normal times, and the cycle and cohort effects they can't see are exactly what the stress scenarios are for.

### 6. The interactive dashboard

[`index.html`](index.html) ([live here](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)) loads the fitted coefficients into the browser — no server, no install. Set a borrower's profile and see their probability of default, loss given default, expected loss, and where they rank against the portfolio, plus a live survival curve showing *when* the risk materialises.

---

## What's in this repository

```
├── index.html            ← interactive risk dashboard (live demo)
├── data/
│   ├── raw/              ← original CSV (not tracked — too large for GitHub)
│   └── processed/        ← cleaned data (generated by 00_ingest.py, not tracked)
├── python/               ← complete analysis
│   ├── 00_ingest.py      ← load and clean; add loan age + resolved/active flag
│   ├── 01_eda.ipynb      ← explore the loans
│   ├── 02_cohort.ipynb   ← vintage analysis over time
│   ├── 03_models.ipynb   ← PD (logistic + survival) and LGD models
│   ├── 04_reserve.ipynb  ← forward-looking ECL on the active book + backtest
│   └── requirements.txt
├── r/                    ← R implementation (planned — not yet present)
├── stata/                ← STATA implementation (planned — not yet present)
├── output/figures/       ← charts
└── README.md
```

`data/` is not tracked. After cloning, create `data/raw/`, download the Lending Club CSV into it, and run the ingest script.

---

## Method summary

| Phase | Method | Library |
|---|---|---|
| Data cleaning | Column selection, date parsing, loan age, recovery fields, resolved/active split | `pandas`, `numpy` |
| EDA & vintage analysis | Distributions, correlation, cohort curves | `matplotlib`, `seaborn` |
| PD — discrimination | Logistic regression (application-time features; trained and tested on matured loans only, temporal split) | `scikit-learn`, `statsmodels` |
| PD — timing | Competing risks: cause-specific Cox hazards for default *and* early payoff, Kaplan-Meier → remaining-life PD via monthly cumulative incidence | `lifelines` |
| LGD | Loss on outstanding principal — flat ~89% (recovery ~11%); regression confirms it's unpredictable (R² < 1%) | `pandas`, `statsmodels` |
| Exposure at default | Actual outstanding balance rolled forward on the amortisation schedule, probability-weighted across every possible default month | `numpy` |
| Reserve | Loan-level expected credit loss integrated over the default-time distribution, on the active book (delinquent loans reserved in full) + PD stress + vintage backtest | `numpy` |

---

## Running it yourself

```bash
pip install -r python/requirements.txt
# Download the Lending Club CSV from Kaggle into data/raw/, then from the project root:
python python/00_ingest.py
jupyter notebook python/
```

Requires Python 3.10+. The raw CSV (`accepted_2007_to_2018Q4.csv`) must be downloaded from [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) into `data/raw/` first.

---

## Important caveats

- **This is consumer credit data.** Lending Club loans are unsecured personal loans; the methodology transfers to other lending but the specific numbers would differ.
- **No macroeconomic variable.** The models learn loan-level risk, not the cycle — so they under-predict crisis vintages (visible in the backtest). A production reserve would overlay a macro scenario.
- **No vintage-quality effect.** Prepayment and default are modelled as competing risks (which centred the backtest), but the conversion to probabilities assumes the two hazards share no unobserved dependence beyond the loan features, and cohorts that underwrote worse than their features show (2015–16) are under-called by ~1–2 points. The stress range absorbs this.
- **Maturation.** Recent vintages haven't fully matured; the forward-looking PD projects their remaining life, and the backtest shows the gap explicitly.
- **The reserve rests on stated modelling choices.** LGD is a flat ~89% (≈11% recovery, ignoring collection costs and the time value of recoveries — so true severity is, if anything, a touch higher); exposure rolls each loan's actual balance forward on its amortisation schedule and weights it across possible default months; loans already 31–120 days late are reserved in full. The stress range, not a single point, is the honest output.
- **Models simplify reality.** Default is partly driven by unpredictable life events — which is the whole reason a reserve is needed.

---

## Data source

[Lending Club Loan Data — Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) · `accepted_2007_to_2018Q4.csv` (2.26M loans, 151 columns)
