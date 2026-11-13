"""
Mathematical and Statistical Unit Tests for Trend Detective Engine.
Asserts Hamed-Rao Mann-Kendall, Theil-Sen, Hyperbolic OLS Bands, MAD, and Benjamini-Hochberg FDR.
"""

import numpy as np
import pytest

from api.trend_engine import (
    analyze_time_series_trend,
    benjamini_hochberg_fdr,
    calculate_lag1_autocorrelation,
    compute_climatologies_and_anomalies,
    compute_mann_kendall_trend,
    compute_ols_hyperbolic_bands,
    compute_welch_epoch_ttest_and_cohens_d,
    detect_mad_episodic_outliers,
    filter_incomplete_boundary_years,
)
from scripts.seed_supabase import (
    generate_mississippi_west_series,
    generate_pearl_river_series,
)


def test_boundary_year_filtering():
    """Assert incomplete start/end calendar years (<10 months) are dropped."""
    series = []
    # Incomplete start year 2000 (only 4 months)
    for m in range(9, 13):
        series.append({"date": f"2000-{m:02d}", "value": 10.0})
    # Complete year 2001 (12 months)
    for m in range(1, 13):
        series.append({"date": f"2001-{m:02d}", "value": 11.0})
    # Complete year 2002 (12 months)
    for m in range(1, 13):
        series.append({"date": f"2002-{m:02d}", "value": 12.0})
    # Incomplete end year 2003 (only 5 months)
    for m in range(1, 6):
        series.append({"date": f"2003-{m:02d}", "value": 13.0})

    filtered = filter_incomplete_boundary_years(series, season="all")
    years_present = {int(r["date"][:4]) for r in filtered}

    assert 2000 not in years_present, "Incomplete start year must be dropped"
    assert 2003 not in years_present, "Incomplete end year must be dropped"
    assert 2001 in years_present
    assert 2002 in years_present
    assert len(filtered) == 24


def test_climatologies_and_anomalies_conservation():
    """Assert monthly climatologies properly remove seasonal cycle."""
    # Synthetic series with strong sinusoidal cycle
    series = []
    for y in range(2000, 2010):
        for m in range(1, 13):
            val = 20.0 + (10.0 * np.sin(2 * np.pi * m / 12.0))
            series.append({"date": f"{y}-{m:02d}", "value": val})

    enriched, climatologies = compute_climatologies_and_anomalies(series)
    assert len(climatologies) == 12

    anomalies = [r["anomaly"] for r in enriched]
    assert np.isclose(np.mean(anomalies), 0.0, atol=1e-3)
    assert np.all(np.abs(anomalies) < 0.01), "Pure seasonal sine wave should yield ~0 anomalies"


def test_autocorrelation_calculation():
    """Assert lag-1 autocorrelation detects persistent red-noise series."""
    # Persistent autoregressive series: X_t = 0.8 * X_{t-1} + e_t
    np.random.seed(42)
    n = 200
    ar_series = np.zeros(n)
    for t in range(1, n):
        ar_series[t] = 0.8 * ar_series[t - 1] + np.random.normal(0, 0.5)

    r1 = calculate_lag1_autocorrelation(ar_series)
    assert r1 > 0.5, f"AR(1) series with phi=0.8 should have r1 > 0.5, got {r1}"

    # White noise series
    white_noise = np.random.normal(0, 1.0, size=200)
    r1_white = calculate_lag1_autocorrelation(white_noise)
    assert abs(r1_white) < 0.25, f"White noise should have low autocorrelation, got {r1_white}"


def test_hamed_rao_switch_rule():
    """Assert automatic promotion to Hamed-Rao modified test when r1 > 0.20."""
    dates = [f"2010-{m:02d}" for m in range(1, 13)] * 5
    vals = np.linspace(10, 20, len(dates))

    # Case 1: High autocorrelation (r1 = 0.35 > 0.20)
    res_hr = compute_mann_kendall_trend(vals, dates, lag1_autocorr=0.35)
    assert res_hr["test_used"] == "Hamed-Rao Modified Mann-Kendall"

    # Case 2: Low autocorrelation (r1 = 0.08 <= 0.20)
    res_std = compute_mann_kendall_trend(vals, dates, lag1_autocorr=0.08)
    assert res_std["test_used"] == "Standard Mann-Kendall"


def test_theil_sen_slope_directionality():
    """Assert positive and negative slopes are correctly quantified."""
    dates = [f"2010-{m:02d}" for m in range(1, 13)] * 10
    n = len(dates)

    # Positive upward trend
    up_vals = np.linspace(5.0, 15.0, n)
    res_up = compute_mann_kendall_trend(up_vals, dates, lag1_autocorr=0.0)
    assert res_up["sen_slope"] > 0
    assert res_up["is_significant"] is True

    # Negative downward trend
    down_vals = np.linspace(15.0, 5.0, n)
    res_down = compute_mann_kendall_trend(down_vals, dates, lag1_autocorr=0.0)
    assert res_down["sen_slope"] < 0
    assert res_down["is_significant"] is True


def test_ols_hyperbolic_confidence_bands_geometry():
    """
    Assert true hyperbolic geometry of OLS confidence bands:
    The interval width must be minimum at centroid t_bar and expand at edges.
    """
    n = 60
    t = np.arange(n, dtype=float)
    np.random.seed(42)
    y = 2.0 + 0.1 * t + np.random.normal(0, 0.5, size=n)

    ols = compute_ols_hyperbolic_bands(t, y)
    ci_up = np.array(ols["ci_upper"])
    ci_low = np.array(ols["ci_lower"])
    band_width = ci_up - ci_low

    mid_idx = n // 2
    # Width at centroid should be strictly less than width at the boundaries
    assert band_width[mid_idx] < band_width[0], "Hyperbolic band must be wider at start boundary"
    assert band_width[mid_idx] < band_width[-1], "Hyperbolic band must be wider at end boundary"
    assert ols["r_squared"] > 0.5


def test_mad_episodic_outlier_detection_and_skew():
    """Assert MAD modified Z-scores flag episodic spikes and trigger skew warnings."""
    # Normal background with 2 extreme outlier flood spikes
    anomalies = np.zeros(60)
    anomalies[15] = 12.0  # Spike 1
    anomalies[35] = 14.0  # Spike 2

    # In this case, OLS slope (0.05) diverges from Sen's slope (0.0)
    outlier_mask, skew_warning = detect_mad_episodic_outliers(
        anomalies, ols_slope=0.08, sen_slope=0.005
    )

    assert bool(outlier_mask[15]) is True, "Spike at index 15 must be flagged"
    assert bool(outlier_mask[35]) is True, "Spike at index 35 must be flagged"
    assert bool(outlier_mask[0]) is False
    assert skew_warning is True, "Outlier skew warning must trigger on >30% slope divergence"


def test_welch_epoch_ttest_and_cohens_d():
    """Assert Welch's epoch test detects significant baseline vs recent shift."""
    baseline = np.array([10.0, 10.2, 10.1, 9.9, 10.0])
    recent = np.array([14.0, 14.2, 13.9, 14.1, 14.3])
    annual_means = np.concatenate([baseline, recent])

    res = compute_welch_epoch_ttest_and_cohens_d(annual_means)
    assert res["welch_p"] < 0.001
    assert res["cohens_d"] > 2.0  # Very large effect size


def test_pure_numpy_benjamini_hochberg_fdr():
    """Assert pure-NumPy FDR adjustment matches theoretical step-up values."""
    # Test set of 4 p-values
    raw_p = np.array([0.01, 0.04, 0.03, 0.20])
    adj_p, sig = benjamini_hochberg_fdr(raw_p, alpha=0.05)

    # Sorted order: 0.01 (k=1), 0.03 (k=2), 0.04 (k=3), 0.20 (k=4)
    # k=1: 0.01 * (4/1) = 0.04
    # k=2: 0.03 * (4/2) = 0.06
    # k=3: 0.04 * (4/3) = 0.0533
    # k=4: 0.20 * (4/4) = 0.20
    # Step-up cummin:
    # adj for 0.03 is min(0.06, 0.0533) = 0.0533
    assert adj_p[0] == 0.04
    assert np.isclose(adj_p[1], 0.05333, atol=1e-3)
    assert np.isclose(adj_p[2], 0.05333, atol=1e-3)
    assert adj_p[3] == 0.20
    assert bool(sig[0]) is True  # 0.04 <= 0.05


def test_full_pipeline_on_pearl_river():
    """End-to-end test on calibrated Pearl River benchmark."""
    series = generate_pearl_river_series()
    result = analyze_time_series_trend(series, season="all")

    assert "ols" in result
    assert "trend" in result
    assert result["trend"]["is_significant"] is True
    assert result["trend"]["sen_slope"] > 0
    assert len(result["series"]) == len(series)


def test_full_pipeline_on_mississippi_west_outliers():
    """End-to-end test on Mississippi West flood outliers."""
    series = generate_mississippi_west_series()
    result = analyze_time_series_trend(series, season="all")

    # Verify outlier flags exist on known flood dates
    outlier_dates = {r["date"] for r in result["series"] if r.get("is_outlier")}
    assert "2011-05" in outlier_dates or "2011-06" in outlier_dates
    assert "2019-06" in outlier_dates
