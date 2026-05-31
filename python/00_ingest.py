"""
00_ingest.py
------------
Load raw Lending Club data, select relevant columns, clean and engineer
features, and save a processed file ready for analysis.

Output: data/processed/loans_clean.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
RAW  = Path("data/raw/accepted_2007_to_2018Q4.csv")
OUT  = Path("data/processed/loans_clean.parquet")
OUT.parent.mkdir(parents=True, exist_ok=True)

# ── Columns to keep ──────────────────────────────────────────────────────────
COLS = [
    "loan_status", "issue_d", "last_pymnt_d", "installment",
    "loan_amnt", "funded_amnt", "out_prncp", "total_pymnt",
    "int_rate", "grade", "sub_grade", "term", "dti",
    "fico_range_low", "fico_range_high", "annual_inc", "emp_length",
    "home_ownership", "purpose", "addr_state", "delinq_2yrs",
    "open_acc", "pub_rec", "revol_util", "total_acc",
]

# ── Load ─────────────────────────────────────────────────────────────────────
print("Loading raw data (this may take a minute)...")
df = pd.read_csv(RAW, usecols=COLS, low_memory=False)
print(f"  Loaded {len(df):,} rows × {len(df.columns)} columns")

# ── Clean: term ───────────────────────────────────────────────────────────────
df["term"] = df["term"].str.strip().str.extract(r"(\d+)")[0].astype(float)

# ── Clean: emp_length ─────────────────────────────────────────────────────────
df["emp_length"] = (df["emp_length"]
                    .replace({"10+ years": "10", "< 1 year": "0"})
                    .str.extract(r"(\d+)")[0]
                    .astype(float))

# ── int_rate and revol_util are already numeric ───────────────────────────────
df["int_rate"]   = pd.to_numeric(df["int_rate"],   errors="coerce") / 100
df["revol_util"] = pd.to_numeric(df["revol_util"], errors="coerce") / 100

# ── Parse dates ───────────────────────────────────────────────────────────────
df["issue_d"]      = pd.to_datetime(df["issue_d"],      format="%b-%Y")
df["last_pymnt_d"] = pd.to_datetime(df["last_pymnt_d"], format="%b-%Y",
                                    errors="coerce")

df["issue_year"]    = df["issue_d"].dt.year
df["issue_quarter"] = df["issue_d"].dt.to_period("Q").astype(str)

today = pd.Timestamp("2019-01-01")
df["months_obs"] = (
    (df["last_pymnt_d"].fillna(today) - df["issue_d"])
    .dt.days / 30
).clip(lower=0).round(1)

# ── Target variable ───────────────────────────────────────────────────────────
BAD_STATUS = {
    "Default",
    "Charged Off",
    "Late (31-120 days)",
    "Does not meet the credit policy. Status:Charged Off",
}
# Note: Lending Club's "Late (31-120 days)" is the closest available label
# to 90-day delinquency. The 31-day lower bound means this bucket captures
# some loans that may have cured, but it is the most appropriate proxy
# for cash-flow interruption in this dataset.
df["delq90"] = df["loan_status"].isin(BAD_STATUS).astype(int)
print(f"  90-day delinquency rate: {df['delq90'].mean():.2%} "
      f"({df['delq90'].sum():,} loans)")

# ── FICO midpoint ─────────────────────────────────────────────────────────────
df["fico"] = (df["fico_range_low"] + df["fico_range_high"]) / 2

# ── Check nulls before dropping ───────────────────────────────────────────────
required = ["int_rate", "dti", "fico", "loan_amnt", "term"]
print("\nNull counts in required columns:")
print(df[required].isnull().sum().to_string())

before = len(df)
df = df.dropna(subset=required)
print(f"\n  Dropped {before - len(df):,} rows | {len(df):,} remaining")

# ── Save ──────────────────────────────────────────────────────────────────────
df.to_parquet(OUT, index=False)
print(f"  Saved → {OUT}")
print(f"  Final shape: {df.shape}")
