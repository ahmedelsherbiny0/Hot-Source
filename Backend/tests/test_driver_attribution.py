"""
Unit tests for Silent Physical Driver Attribution & Diagnostic Synthesis Engine.
"""

import numpy as np
import pytest

from api.driver_attribution import (
    DRIVER_PAIRINGS,
    attribute_physical_driver,
    compute_anomaly_cross_correlation,
    synthesize_natural_language_explanation,
)


def test_driver_pairings_catalog():
    """Verify all expected domain cause-and-effect pairings are configured."""
    assert "evapotranspiration" in DRIVER_PAIRINGS
    assert DRIVER_PAIRINGS["evapotranspiration"]["driver_variable"] == "precipitation"

    assert "soil_moisture" in DRIVER_PAIRINGS
    assert DRIVER_PAIRINGS["soil_moisture"]["driver_variable"] == "precipitation"

    assert "precipitation" in DRIVER_PAIRINGS
    assert DRIVER_PAIRINGS["precipitation"]["driver_variable"] == "surface_temp"

    assert "surface_temp" in DRIVER_PAIRINGS
    assert DRIVER_PAIRINGS["surface_temp"]["driver_variable"] == "evapotranspiration"


def test_anomaly_cross_correlation_strong_positive():
    """Verify perfect in-phase anomalies produce r = +1.0 and Strong coupling."""
    primary = [{"date": f"2020-{m:02d}", "anomaly": float(m)} for m in range(1, 13)]
    driver = [{"date": f"2020-{m:02d}", "anomaly": float(m * 2)} for m in range(1, 13)]

    r_val, coupling = compute_anomaly_cross_correlation(primary, driver)
    assert np.isclose(r_val, 1.0, atol=1e-2)
    assert coupling == "Strong"


def test_anomaly_cross_correlation_strong_negative():
    """Verify anti-correlated anomalies produce negative r and Strong coupling (|r| >= 0.50)."""
    primary = [{"date": f"2020-{m:02d}", "anomaly": float(m)} for m in range(1, 13)]
    driver = [{"date": f"2020-{m:02d}", "anomaly": float(-m)} for m in range(1, 13)]

    r_val, coupling = compute_anomaly_cross_correlation(primary, driver)
    assert np.isclose(r_val, -1.0, atol=1e-2)
    assert coupling == "Strong"


def test_anomaly_cross_correlation_moderate_and_weak():
    """Verify coupling thresholds for moderate and weak."""
    # Weak coupling (orthogonal sine & cosine series: correlation r ~ 0.0)
    primary = [{"date": f"2020-{m:02d}", "anomaly": float(np.sin(2 * np.pi * m / 12.0))} for m in range(1, 13)]
    driver = [{"date": f"2020-{m:02d}", "anomaly": float(np.cos(2 * np.pi * m / 12.0))} for m in range(1, 13)]
    r_val, coupling = compute_anomaly_cross_correlation(primary, driver)
    assert abs(r_val) < 0.25
    assert coupling == "Weak"


def test_date_alignment_intersection():
    """Verify only common date timestamps are correlated."""
    # Primary has 2018-2020, driver has 2019-2021 (overlap is 2019-2020)
    primary = [{"date": f"{y}-{m:02d}", "anomaly": 1.0} for y in range(2018, 2021) for m in range(1, 13)]
    driver = [{"date": f"{y}-{m:02d}", "anomaly": 1.0} for y in range(2019, 2022) for m in range(1, 13)]

    r_val, coupling = compute_anomaly_cross_correlation(primary, driver)
    # Both are constants, should return Weak without crashing
    assert coupling == "Weak"


def test_synthesize_explanation_prioritizes_documented_reason():
    """Assert pre-documented case study reason is preserved."""
    doc_reason = "Curated NASA Giovanni Chlorophyll-a eutrophication case study."
    text = synthesize_natural_language_explanation(
        variable_key="chlorophyll_a",
        paired_info=DRIVER_PAIRINGS["chlorophyll_a"],
        r_val=0.65,
        coupling="Strong",
        trend_stats={"sen_slope": 0.04, "p_value": 0.001, "is_significant": True},
        documented_reason=doc_reason,
    )
    assert text == doc_reason


def test_synthesize_explanation_significant_with_outlier():
    """Assert diagnosis reports trend significance, slope, and MAD outlier alerts."""
    trend_stats = {
        "sen_slope": 0.35,
        "p_value": 0.002,
        "is_significant": True,
        "test_used": "Hamed-Rao Modified Mann-Kendall",
        "outlier_skew_warning": True,
        "cumulative_change": 8.75,
    }
    text = synthesize_natural_language_explanation(
        variable_key="evapotranspiration",
        paired_info=DRIVER_PAIRINGS["evapotranspiration"],
        r_val=0.72,
        coupling="Strong",
        trend_stats=trend_stats,
    )

    assert "Statistically significant upward (increasing) trend" in text
    assert "Hamed-Rao" in text
    assert "Median Absolute Deviation (MAD)" in text
    assert "Strong physical coupling" in text
    assert "Precipitation Rate" in text


def test_synthesize_explanation_avoids_type_ii_error():
    """Assert non-significant trend avoids asserting 'no change occurred'."""
    trend_stats = {
        "sen_slope": 0.01,
        "p_value": 0.34,
        "is_significant": False,
        "test_used": "Standard Mann-Kendall",
        "outlier_skew_warning": False,
        "cumulative_change": 0.25,
    }
    text = synthesize_natural_language_explanation(
        variable_key="soil_moisture",
        paired_info=DRIVER_PAIRINGS["soil_moisture"],
        r_val=0.15,
        coupling="Weak",
        trend_stats=trend_stats,
    )

    assert "No statistically significant monotonic trend detected" in text
    assert "interannual variability" in text


def test_attribute_physical_driver_end_to_end(monkeypatch):
    """Verify master attribution function returns schema-compliant dictionary."""
    primary_series = [
        {"date": f"2020-{m:02d}", "value": 15.0 + m, "anomaly": float(m - 6)}
        for m in range(1, 13)
    ]
    trend_stats = {
        "sen_slope": 0.2,
        "p_value": 0.01,
        "is_significant": True,
        "test_used": "Hamed-Rao Modified Mann-Kendall",
        "cumulative_change": 5.0,
        "outlier_skew_warning": False,
    }

    # Mock get_variable_time_series for instantaneous offline unit testing
    mock_driver_series = [
        {"date": f"2020-{m:02d}", "value": 20.0 + (m * 2)} for m in range(1, 13)
    ]
    monkeypatch.setattr(
        "api.driver_attribution.get_variable_time_series",
        lambda **kwargs: {"series": mock_driver_series, "cache_hit": True},
    )

    result = attribute_physical_driver(
        lat=31.0,
        lon=31.0,
        variable_key="evapotranspiration",
        primary_series=primary_series,
        trend_stats=trend_stats,
        start_year=2020,
        end_year=2020,
    )

    assert "paired_variable" in result
    assert result["paired_variable"] == "precipitation"
    assert "driver_name" in result
    assert "correlation_r" in result
    assert "coupling_strength" in result
    assert "driver_reason" in result
    assert len(result["driver_reason"]) > 30
