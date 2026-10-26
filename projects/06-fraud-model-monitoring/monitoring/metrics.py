"""Monitoring metrics for a binary fraud model.

Every function takes plain arrays of labels, scores or feature values, so the same
checks work on any model's output, including a vendor score whose internals you
cannot see.
"""
import numpy as np
from sklearn.metrics import roc_auc_score


def psi(expected, actual, bins=10, eps=1e-6):
    """Population stability index of `actual` against the baseline `expected`.

    Bin edges are the baseline's quantiles, so each baseline bin holds about the
    same share. Features with very few distinct values (a 0/1 flag) are compared
    value by value. Common reading: under 0.10 stable, 0.10 to 0.25 watch,
    over 0.25 investigate.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        values = np.union1d(np.unique(expected), np.unique(actual))
        e = np.array([(expected == v).mean() for v in values])
        a = np.array([(actual == v).mean() for v in values])
    else:
        inner = edges[1:-1]
        n_bins = len(inner) + 1
        e = np.bincount(np.searchsorted(inner, expected, side="right"), minlength=n_bins) / len(expected)
        a = np.bincount(np.searchsorted(inner, actual, side="right"), minlength=n_bins) / len(actual)
    e = np.clip(e, eps, None)
    a = np.clip(a, eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def ks_statistic(y_true, scores):
    """Largest gap between the score distributions of fraud and non-fraud."""
    y = np.asarray(y_true).astype(bool)
    s = np.asarray(scores, dtype=float)
    pos, neg = np.sort(s[y]), np.sort(s[~y])
    grid = np.unique(s)
    cdf_pos = np.searchsorted(pos, grid, side="right") / len(pos)
    cdf_neg = np.searchsorted(neg, grid, side="right") / len(neg)
    return float(np.max(np.abs(cdf_pos - cdf_neg)))


def auc_and_gini(y_true, scores):
    """Ranking power across all cut-offs. Gini = 2 x AUC - 1."""
    auc = float(roc_auc_score(y_true, scores))
    return auc, 2 * auc - 1


def alert_metrics(y_true, scores, threshold, amounts=None):
    """What happens at the alert cut-off: workload, fraud caught, dollars caught."""
    y = np.asarray(y_true).astype(bool)
    alert = np.asarray(scores, dtype=float) >= threshold
    tp = int(np.sum(alert & y))
    fp = int(np.sum(alert & ~y))
    fn = int(np.sum(~alert & y))
    out = {
        "alert_rate": float(alert.mean()),
        "detection_rate": tp / (tp + fn) if (tp + fn) else float("nan"),
        "precision": tp / (tp + fp) if (tp + fp) else float("nan"),
        "false_positives_per_fraud": fp / tp if tp else float("inf"),
    }
    if amounts is not None:
        amt = np.asarray(amounts, dtype=float)
        fraud_value = amt[y].sum()
        out["value_detection_rate"] = float(amt[alert & y].sum() / fraud_value) if fraud_value else float("nan")
    return out
