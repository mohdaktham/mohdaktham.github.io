import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitoring.metrics import alert_metrics, auc_and_gini, ks_statistic, psi  # noqa: E402


def test_psi_is_near_zero_for_the_same_distribution():
    rng = np.random.default_rng(0)
    assert psi(rng.normal(size=50_000), rng.normal(size=50_000)) < 0.01


def test_psi_flags_a_one_standard_deviation_shift():
    rng = np.random.default_rng(1)
    assert psi(rng.normal(size=50_000), rng.normal(1.0, 1.0, 50_000)) > 0.25


def test_psi_on_a_binary_flag_matches_the_formula():
    base = np.array([1] * 700 + [0] * 300)
    new = np.array([1] * 550 + [0] * 450)
    expected = (0.45 - 0.30) * np.log(0.45 / 0.30) + (0.55 - 0.70) * np.log(0.55 / 0.70)
    assert psi(base, new) == pytest.approx(expected, abs=1e-9)


def test_ks_is_one_for_perfect_separation_and_zero_for_none():
    y = np.array([0, 0, 0, 1, 1, 1])
    assert ks_statistic(y, np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])) == 1.0
    assert ks_statistic(y, np.full(6, 0.5)) == 0.0


def test_gini_is_two_auc_minus_one():
    y = np.array([0, 1, 0, 1, 0, 1])
    auc, gini = auc_and_gini(y, np.array([0.1, 0.9, 0.4, 0.35, 0.2, 0.8]))
    assert gini == pytest.approx(2 * auc - 1)


def test_alert_metrics_on_a_hand_worked_example():
    y = np.array([1, 1, 0, 0, 0, 1])
    scores = np.array([0.9, 0.2, 0.8, 0.1, 0.3, 0.7])
    amounts = np.array([100, 50, 10, 10, 10, 25])
    m = alert_metrics(y, scores, 0.5, amounts)
    # alerts on rows 0, 2 and 5: two frauds caught, one false alarm, one fraud missed
    assert m["alert_rate"] == 0.5
    assert m["detection_rate"] == pytest.approx(2 / 3)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["false_positives_per_fraud"] == 0.5
    assert m["value_detection_rate"] == pytest.approx(125 / 175)
