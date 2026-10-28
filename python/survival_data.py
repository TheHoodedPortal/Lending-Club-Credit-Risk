"""Construct snapshot-censored survival events for Lending Club loans."""

def add_survival_events(df, today):
    """Modify df in place and return the count of missing resolved event dates."""
    # This extract has no charge-off date. Last payment is only a proxy for
    # resolved-event timing; it can precede charge-off substantially. Missing or
    # impossible proxy dates are excluded from survival fitting, not imputed.
    resolved_for_time = df["loan_status"].isin({"Fully Paid", "Charged Off", "Default", "Does not meet the credit policy. Status:Fully Paid", "Does not meet the credit policy. Status:Charged Off"})
    event_date = df["last_pymnt_d"].where(resolved_for_time, today)
    event_date = event_date.where(event_date.between(df["issue_d"], today))
    df["months_obs"] = ((event_date - df["issue_d"]).dt.days / 30).clip(lower=0).round(1)
    df["default_event"] = df["loan_status"].isin({"Default", "Charged Off", "Does not meet the credit policy. Status:Charged Off"}).astype(int)
    # Monthly date precision: payoff in the final contractual month is maturity,
    # not early payoff. Exact timing near maturity cannot be determined.
    payoff_month = (df["last_pymnt_d"].dt.year - df["issue_d"].dt.year)*12 + df["last_pymnt_d"].dt.month - df["issue_d"].dt.month
    df["prepaid"] = (df["loan_status"].isin({"Fully Paid", "Does not meet the credit policy. Status:Fully Paid"}) & payoff_month.notna() & (payoff_month < df["term"] - 1)).astype(int)
    return int((resolved_for_time & event_date.isna()).sum())

