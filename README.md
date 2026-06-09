# Lending Club Credit Risk — Forward-Looking Loss Reserve

**How much should a lender set aside today for the losses its current loan book will eventually take?**

This project answers that question for a real book: 2.26 million Lending Club loans issued between 2007 and 2018. Models trained on the loans whose outcomes are already known score the 911,000 loans still open, and the result is a dollar reserve for the live book — backtested against what actually happened.

**[Try the live dashboard →](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/)** Score any loan profile and stress the whole reserve, right in the browser. Described in [its own section](#the-interactive-dashboard) below.

---

## The question

A lender holding a book of loans needs to know, *today*, how much to reserve for the losses that book will take over its remaining life. Reserve too little and a downturn threatens solvency. Reserve too much and capital sits idle.

The standard framework (IFRS 9 / CECL) is **expected credit loss**:

```
Expected loss = probability of default × loss given default × exposure at default
```

That breaks the problem into three questions:

1. **How likely is each open loan to default over its remaining life?** (probability of default, PD)
2. **If it defaults, what share of the money is lost?** (loss given default, LGD)
3. **How much will be at stake when it happens?** (exposure at default)

Answer all three for every open loan, sum it up, and you have the reserve.

One discipline applies throughout: a model scoring a loan today may only use information known today. Outcomes train the models — they never leak into a prediction.

## The answer

| | |
|---|---|
| Open loans on the book | 911,000 loans, **$9.5B** still owed |
| Expected credit loss — the reserve | **$1.02B** (10.7% of outstanding) |
| The same reserve if default rates double | **$1.65B** (17.4%) |

The reserve is model-driven and backtested: on past loan cohorts that have fully played out under normal conditions, the predicted loss rate lands within about a point of what actually happened ([section 5](#5-does-it-hold-up-a-backtest)).

---

## The analysis, step by step

### 1. The data, and what "delinquent" means

Every loan carries a Lending Club **grade from A (safest) to G (riskiest)** — the lender's own risk score, set before issue. It is the strongest single signal in the data.

A loan is labelled **delinquent** if its status is `Late (31–120 days)`, `Default`, or `Charged Off` — the closest the data comes to a serious, cash-flow-interrupting delinquency. By that definition **12.9%** of loans go bad, climbing steeply with grade: **3.6% of Grade A loans, 40.0% of Grade G.**

![Delinquency rate by loan grade](output/figures/delinquency_by_grade.png)

The book then splits in two. **Resolved loans** (fully paid or charged off) have known outcomes — they are what the models learn from. **Active loans** (current, in grace, or late) are still open — they are the book the reserve is for. The models also use the active loans' history so far: they know those loans haven't defaulted *yet*, without pretending to know how they end.

One trap in this data is worth naming early. Recent loans look deceptively safe simply because they haven't had time to go bad yet — *maturation bias*. The cohort curves below show every vintage's delinquency climbing as it ages, with the 2007–08 crisis cohorts standing well above the rest. Both the forward-looking method and the backtest have to account for this.

![Delinquency by issue cohort and grade](output/figures/vintage_curves_by_grade.png)

### 2. Will a loan default — and when?

**First, what separates good borrowers from bad.** A logistic regression predicts default from information available at issue. To keep the labels honest, it is trained and tested only on **matured loans** — loans whose full term had already run out, so every label is a final outcome rather than a loan that is merely "good so far." Trained on matured loans issued through 2014 and tested on the matured 2015 cohort, the model scores **AUC = 0.68**.

More interesting than the score is what the model learned. The chart puts every factor on a common footing — each point is the change in default probability from a one-standard-deviation increase in that factor:

![What drives a borrower to default](output/figures/marginal_effects.png)

**The price of risk leads.** The interest rate — the lender's own all-in pricing of the borrower — and the grade behind it carry the most signal. Higher income and a better credit score are the strongest protective factors. Read those top two bars together rather than as separate findings: rate and grade are about 0.95 correlated (the lender sets the rate *from* the grade), so they're really a single "price of risk" signal the regression has split across two bars — which is also why their relative heights aren't worth over-interpreting. (Nonlinear versions of income and debt-to-income were tested and didn't improve the AUC, so the model stays linear.)

The 0.68 itself is worth pausing on: consumer default is only **partly predictable**, because its strongest triggers — job loss, illness, divorce — appear in no loan application. That irreducible uncertainty is the reason reserves exist.

**Second, the timing.** Whether a loan defaults isn't enough — the reserve needs to know *when* the risk sits. A survival model (Cox proportional hazards) tracks how default risk unfolds month by month over a loan's life. Grade A loans stay healthy for years; nearly half of Grade G loans stop paying within five years.

![Survival curves by grade](output/figures/kaplan_meier_by_grade.png)

Two details make this model the engine of the reserve:

- **It can start the clock today.** For a loan that is already 20 months old, the model conditions on the fact that it has survived those 20 months and prices only the road ahead. Nothing about the future is assumed — only the loan's age today.
- **Default and early payoff compete.** Many borrowers pay their loans off early, and a loan that has been paid off can never default. The reserve therefore fits *two* hazards — one for default, one for payoff — and walks them forward together. Skipping this is a common shortcut, and it quietly overstates default risk; the backtest in section 5 shows by how much.

### 3. When a loan defaults, how much is lost?

The loss on a defaulted loan is the principal still owed, minus whatever collections later claw back. The natural question: can that severity be predicted loan by loan, the way default probability can?

**It can't — and that's the finding.** Regressing loss severity on every loan feature — grade, rate, FICO, income, term, even months on book — explains just **0.6%** of its variation, and no single feature explains even 0.2%. There is no collateral behind an unsecured loan, so what comes back after a default is essentially luck. It doesn't track the borrower.

The honest estimate is therefore the observed average — a measured fact, not an assumption. Across roughly 269,000 charged-off loans, the lender recovered about **11 cents per dollar owed**. Loss given default is **~89%**, and it is nearly identical in every grade:

![Loss given default on the outstanding balance](output/figures/lgd_outstanding.png)

The timing effect you might expect in severity — *a seasoned loan loses less* — isn't missing. It lives in the exposure instead: what falls as a loan ages is not the loss **rate** but the **balance left to lose**. So the reserve holds severity flat at 89% and lets the amortising balance do that work.

### 4. The reserve on today's book

Now everything is applied to the 911,000 open loans. Each one is walked forward, month by month, from its current age to its maturity. In any month it does one of three things — defaults, pays off early, or survives to the next month — with probabilities from the survival models. If it defaults in a given month, the loss is 89% of the balance it would still owe that month, starting from its actual balance today. Summing the probability-weighted losses across every month and every loan gives the reserve:

![Forward-looking ECL by grade](output/figures/ecl_by_grade.png)

**$1.02B against $9.5B outstanding — 10.7%.** Grade C carries the largest share ($324M), not because it is the riskiest grade but because there is so much of it. Concentration matters as much as rate. One deliberate conservatism: loans already 31–120 days late are reserved in full, as if default were certain. Some of those loans actually cure, so this padding leans the reserve safe.

**A bad year is systemic, not random.** With 900,000 loans, the luck of individual defaults averages out almost completely — simulating the book with independent defaults barely moves the 95th percentile off the mean. What actually threatens the reserve is a downturn lifting *everyone's* default rate at once. So the stress test scales default probabilities across the whole book:

![Reserve under systemic stress](output/figures/ecl_stress.png)

| Scenario | Reserve | % of outstanding |
|---|---|---|
| Base (current conditions) | $1,015M | 10.7% |
| Mild stress (+25% PD) | $1,187M | 12.5% |
| Moderate stress (+50% PD) | $1,350M | 14.2% |
| Severe (2× PD) | $1,653M | 17.4% |

### 5. Does it hold up? A backtest

The honest test: refit everything — survival models and loss severity — using only loans issued through 2014, predict each issue-year cohort's lifetime loss rate from day one, and compare against what those loans actually went on to lose.

![Backtest: predicted vs realized loss by vintage](output/figures/ecl_backtest.png)

Three things to read off the chart:

- **On normal, fully-played-out years the prediction sits on top of reality.** The 2010–2014 cohorts land within about a point (2011: predicted 9.3% vs actual 10.2%; 2014: 10.1% vs 10.3%). The first cohorts past the training cutoff, 2015–16, come in modestly under (9.5% vs 11.2%, and 9.3% vs 10.8%) — those loans performed worse than their paperwork suggested, a known episode of loosening underwriting that no loan-level feature captures.
- **The 2007–08 crisis years are under-predicted.** The model has no macroeconomic input, so it cannot see a recession coming. This is the strongest argument for holding a stressed reserve, not the base one, when conditions look threatening.
- **The newest cohorts show predicted above actual** simply because those loans haven't had time to default yet.

A methodological note: an earlier version of this model, without the competing payoff hazard, over-predicted *every* matured year by 2–4 points. Treating prepayment properly is what centred the calibration.

The takeaway: loan-level features get the level right in normal times, and the things they cannot see — the cycle, a badly underwritten cohort — are exactly what the stress range is for.

---

## The interactive dashboard

Everything above is wrapped in a single-file dashboard: [`index.html`](index.html), [live here](https://thehoodedportal.github.io/Lending-Club-Credit-Risk/). The fitted models are baked into the page — no server, no install.

Set a borrower's profile and months on book, and it returns the remaining-life default probability (with a rank against the live book), the expected exposure at default, the expected loss, and a survival curve showing when the risk sits. A second panel holds the whole-book reserve and lets you flip through the downturn scenarios.

---

## Method summary

| Step | What's done | Library |
|---|---|---|
| Data prep | 2.26M rows: parse, clean, compute loan age, flag resolved vs active | `pandas`, `numpy` |
| Exploration | Distributions, correlations, vintage curves | `matplotlib`, `seaborn` |
| PD — drivers | Logistic regression on application-time features; matured loans only, temporal train/test split | `scikit-learn`, `statsmodels` |
| PD — timing | Two Cox hazards — default and early payoff — walked forward monthly as competing risks | `lifelines` |
| LGD | Measured 89% loss on outstanding principal; regression confirms it is unpredictable (R² < 1%) | `pandas`, `statsmodels` |
| Exposure | Each loan's actual balance rolled forward on its amortisation schedule, weighted across possible default months | `numpy` |
| Reserve | Per-loan expected loss summed over the active book, plus systemic PD stress and the vintage backtest | `numpy` |

---

## Repository and running it

```
├── index.html            ← interactive dashboard (live demo)
├── data/
│   ├── raw/              ← original CSV (not tracked — too large for GitHub)
│   └── processed/        ← cleaned data (generated by 00_ingest.py, not tracked)
├── python/
│   ├── 00_ingest.py      ← load and clean; add loan age + resolved/active flag
│   ├── 01_eda.ipynb      ← explore the loans
│   ├── 02_cohort.ipynb   ← vintage analysis over time
│   ├── 03_models.ipynb   ← PD (logistic + survival) and LGD models
│   ├── 04_reserve.ipynb  ← forward-looking ECL on the active book + backtest
│   └── requirements.txt
├── output/figures/       ← charts
└── README.md
```

```bash
pip install -r python/requirements.txt
# download the Lending Club CSV from Kaggle into data/raw/, then from the project root:
python python/00_ingest.py
jupyter notebook python/
# after refitting 04_reserve.ipynb, refresh the embedded dashboard payload:
python python/05_sync_dashboard.py
```

Requires Python 3.10+. The raw CSV (`accepted_2007_to_2018Q4.csv`, ~1.7GB) is not tracked — download it from [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) into `data/raw/` first.

---

## Caveats

- **This is one lender's unsecured consumer loans.** The method transfers to other credit; the specific numbers don't.
- **There is no macroeconomic variable.** The model prices loans, not the economy, so it cannot anticipate a recession — the backtest shows it missing 2007–08. A production reserve would overlay a macro scenario on top; here, the stress scenarios stand in for that judgement.
- **There is no vintage-quality variable.** Cohorts underwritten more loosely than their features show (2015–16) come in 1–2 points under-predicted. The stress range absorbs this too.
- **The reserve rests on stated choices.** Severity is held flat at 89%, ignoring collection costs and the time value of recoveries — true severity is, if anything, a touch higher. Exposure assumes scheduled amortisation from each loan's actual balance. Loans 31–120 days late are reserved in full. Default and payoff risks are assumed to share nothing beyond the loan's features. The honest output is the stress range, not any single number.
- **Default is partly unpredictable.** Job loss, illness, divorce — no application data contains them. That is not a flaw in the model; it is the reason reserves exist.

---

## Data source

[Lending Club Loan Data — Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) · `accepted_2007_to_2018Q4.csv` (2.26M loans, 151 columns)
