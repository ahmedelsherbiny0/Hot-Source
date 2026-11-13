"""
Trend Detective - Data Science & Scientific Computing Package.
NASA Earth Observation statistical trend engine and physical driver attribution.
"""

from .trend_engine import (
    analyze_time_series_trend,
    calculate_lag1_autocorrelation,
    compute_mann_kendall_trend,
    compute_ols_hyperbolic_bands,
    detect_mad_episodic_outliers,
    benjamini_hochberg_fdr,
    compute_climatologies_and_anomalies,
    compute_welch_epoch_ttest_and_cohens_d,
    filter_incomplete_boundary_years,
)

from .driver_attribution import (
    attribute_physical_driver,
    compute_anomaly_cross_correlation,
    DRIVER_PAIRINGS,
)

from .source_router import (
    VARIABLE_CATALOG,
    get_variable_time_series,
    generate_synthetic_physical_series,
    validate_spatial_and_temporal_boundaries,
)

__version__ = "1.0.0"

__all__ = [
    "analyze_time_series_trend",
    "calculate_lag1_autocorrelation",
    "compute_mann_kendall_trend",
    "compute_ols_hyperbolic_bands",
    "detect_mad_episodic_outliers",
    "benjamini_hochberg_fdr",
    "compute_climatologies_and_anomalies",
    "compute_welch_epoch_ttest_and_cohens_d",
    "filter_incomplete_boundary_years",
    "attribute_physical_driver",
    "compute_anomaly_cross_correlation",
    "DRIVER_PAIRINGS",
    "VARIABLE_CATALOG",
    "get_variable_time_series",
    "generate_synthetic_physical_series",
    "validate_spatial_and_temporal_boundaries",
]
