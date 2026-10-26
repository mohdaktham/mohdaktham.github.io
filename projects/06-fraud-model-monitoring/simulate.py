"""Simulated card transactions with three planted events.

None of this is real customer data. The generator exists to rehearse a monitoring
workflow, so each event below is planted on purpose for the monthly report to find:

  2025-06  Online spending shift: the card-not-present share rises from 30% to 50%.
           The inputs drift, but the way fraud happens does not change.
  2025-08  Data feed fault: distance_from_home arrives as 0 for 40% of transactions,
           as if a missing value had been filled with a default. Fixed from 2025-09.
  2025-10  New fraud pattern: a fraud type appears that looks like ordinary daytime,
           in-person, small-ticket spending. The inputs barely move.
"""
import numpy as np
import pandas as pd

FEATURES = ["amount", "hour", "merchant_risk", "distance_from_home",
            "velocity_24h", "card_present", "account_age_days"]
MONTHS = [str(p) for p in pd.period_range("2025-01", "2025-12", freq="M")]


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def _transactions(rng, n, cnp_share):
    night = rng.random(n) < 0.08
    hour = np.where(night, rng.integers(0, 6, n),
                    np.clip(np.round(rng.normal(14, 4, n)), 6, 23)).astype(int)
    return pd.DataFrame({
        "amount": np.round(rng.lognormal(3.6, 1.0, n), 2),
        "hour": hour,
        "merchant_risk": np.round(rng.beta(2, 8, n), 3),
        "distance_from_home": np.round(rng.lognormal(1.5, 1.0, n), 1),
        "velocity_24h": rng.poisson(2, n),
        "card_present": (rng.random(n) >= cnp_share).astype(int),
        "account_age_days": np.clip(rng.exponential(900, n), 1, 5000).astype(int),
    })


def _classic_fraud_probability(df, shift=0.0):
    z = (-9.6 + shift
         + 1.0 * (np.log(df["amount"]) - 3.6)
         + 2.4 * (df["hour"] < 6)
         + 6.0 * (df["merchant_risk"] - 0.2)
         + 1.5 * (np.log1p(df["distance_from_home"]) - 1.5)
         + 0.6 * (df["velocity_24h"] - 2)
         + 2.2 * (1 - df["card_present"])
         + 1.8 * (df["account_age_days"] < 90))
    return _sigmoid(z)


def simulate_month(rng, month, n=20_000):
    df = _transactions(rng, n, cnp_share=0.50 if month == "2025-06" else 0.30)
    shift = -0.3 if month >= "2025-10" else 0.0
    df["is_fraud"] = (rng.random(n) < _classic_fraud_probability(df, shift)).astype(int)
    df["fraud_type"] = np.where(df["is_fraud"] == 1, "classic", "none")

    if month >= "2025-10":
        new = (rng.random(n) < 0.002) & (df["is_fraud"] == 0)
        k = int(new.sum())
        df.loc[new, "amount"] = np.round(rng.lognormal(3.2, 0.5, k), 2)
        df.loc[new, "hour"] = rng.integers(10, 19, k)
        df.loc[new, "card_present"] = 1
        df.loc[new, "distance_from_home"] = np.round(rng.lognormal(1.0, 0.6, k), 1)
        df.loc[new, "is_fraud"] = 1
        df.loc[new, "fraud_type"] = "new_pattern"

    fault = (rng.random(n) < 0.40) if month == "2025-08" else np.zeros(n, dtype=bool)
    df["distance_as_received"] = np.where(fault, 0.0, df["distance_from_home"])

    df.insert(0, "month", month)
    return df


def simulate(seed=7, n_per_month=20_000):
    rng = np.random.default_rng(seed)
    return pd.concat([simulate_month(rng, m, n_per_month) for m in MONTHS], ignore_index=True)
