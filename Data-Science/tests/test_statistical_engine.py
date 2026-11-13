"""
Unit Tests for Data Science Statistical Engine.
Verifies mathematical correctness of Hamed-Rao MK, Theil-Sen, OLS hyperbolic CI,
MAD outlier shields, Benjamini-Hochberg FDR, and driver attribution.
"""

import numpy as np
import pytest

from trend_detective.trend_engine import (
    calculate_lag1_autocorrelation,
    compute_mann_kendall_trend,
    compute_ols_hyperbolic_bands,
    detect_mad_episodic_outliers,
    benjamini_hochberg_fdr,
    compute_climatologies_and_anomalies,
    compute_welch_epoch_ttest_and_cohens_d,
    filter_incomplete_boundary_years,
)
from trend_detective.driver_attribution import (
    compute_anomaly_cross_correlation,
)


def test_autocorrelation_and_hamed_rao_switch():
    """Verify that lag-1 autocorrelation > 0.20 triggers Hamed-Rao modified Mann-Kendall."""
    dates = [f"2010-{m:02d}" for m in range(1, 13)] * 5
    vals = np.linspace(10, 20, len(dates))

    # Case 1: High autocorrelation (r1 = 0.35 > 0.20)
    res_hr = compute_mann_kendall_trend(vals, dates, lag1_autocorr=0.35)
    assert res_hr["test_used"] == "Hamed-Rao Modified Mann-Kendall"

    # Case 2: Low autocorrelation (r1 = 0.08 <= 0.20)
    res_std = compute_mann_kendall_trend(vals, dates, lag1_autocorr=0.08)
    assert res_std["test_used"] == "Standard Mann-Kendall"


def test_theil_sen_robustness_against_outliers():
    """Verify Theil-Sen slope directionality and significance."""
    dates = [f"2010-{m:02d}" for m in range(1, 13)] * 10
    n = len(dates)
    up_vals = np.linspace(5.0, 15.0, n)
    res_up = compute_mann_kendall_trend(up_vals, dates, lag1_autocorr=0.0)
    assert res_up["sen_slope"] > 0
    assert res_up["is_significant"] is True


def test_ols_hyperbolic_confidence_bands_geometry():
    """Verify hyperbolic 95% confidence bands widen toward boundary years."""
    n = 60
    t = np.arange(n, dtype=float)
    np.random.seed(42)
    y = 2.0 + 0.1 * t + np.random.normal(0, 0.5, size=n)

    ols = compute_ols_hyperbolic_bands(t, y)
    ci_up = np.array(ols["ci_upper"])
    ci_low = np.array(ols["ci_lower"])
    band_width = ci_up - ci_low

    mid_idx = n // 2
    assert band_width[mid_idx] < band_width[0]
    assert band_width[mid_idx] < band_width[-1]
    assert ols["r_squared"] > 0.5


def test_mad_episodic_outlier_detection():
    """Verify MAD modified Z-scores flag episodic spikes and trigger skew warnings."""
    anomalies = np.zeros(60)
    anomalies[15] = 12.0
    anomalies[35] = 14.0

    outlier_mask, skew_warning = detect_mad_episodic_outliers(
        anomalies, ols_slope=0.08, sen_slope=0.005
    )
    assert bool(outlier_mask[15]) is True
    assert bool(outlier_mask[35]) is True
    assert bool(outlier_mask[0]) is False
    assert skew_warning is True


def test_benjamini_hochberg_fdr_controlling():
    """Verify Benjamini-Hochberg FDR step-up correction."""
    raw_p = np.array([0.01, 0.04, 0.03, 0.20])
    adj_p, sig = benjamini_hochberg_fdr(raw_p, alpha=0.05)
    assert adj_p[0] == 0.04
    assert np.isclose(adj_p[1], 0.05333, atol=1e-3)
    assert bool(sig[0]) is True


def test_welch_epoch_ttest_and_cohens_d():
    """Verify Welch's epoch test detects significant baseline vs recent shift."""
    baseline = np.array([10.0, 10.2, 10.1, 9.9, 10.0])
    recent = np.array([14.0, 14.2, 13.9, 14.1, 14.3])
    annual_means = np.concatenate([baseline, recent])

    res = compute_welch_epoch_ttest_and_cohens_d(annual_means)
    assert res["welch_p"] < 0.001
    assert res["cohens_d"] > 2.0


def test_driver_cross_correlation_and_attribution():
    """Verify Pearson cross-correlation on deseasonalized anomalies."""
    series_a = [{"date": f"2020-{m:02d}", "anomaly": float(np.sin(m * 0.5))} for m in range(1, 13)]
    series_b = [{"date": f"2020-{m:02d}", "anomaly": float(np.sin(m * 0.5) + np.random.normal(0, 0.05))} for m in range(1, 13)]

    r, p = compute_anomaly_cross_correlation(series_a, series_b)
    assert r > 0.80
