"""
Statistical Trend Engine for Trend Detective.
Implements rigorous non-parametric tests, autocorrelation correction, OLS hyperbolic confidence bounds,
MAD episodic outlier detection, Welch's epoch t-test, Cohen's d, and pure-NumPy Benjamini-Hochberg FDR.
"""

from collections import defaultdict
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pymannkendall as mk
from scipy import stats


# ==============================================================================
# 1. Boundary Year Filtering & Preprocessing
# ==============================================================================

def filter_incomplete_boundary_years(
    records: List[Dict[str, Any]], season: str = "all"
) -> List[Dict[str, Any]]:
    """
    Drop incomplete boundary years prior to aggregation:
    - Full-year analysis requires >= 10 valid calendar months.
    - Seasonal splits (summer/winter) require >= 5 valid months (or >= 2 for 3-month splits).
    Prevents partial current-year satellite records (e.g. partial 2026 data) from distorting slopes.
    """
    if not records:
        return []

    # Filter by season first if applicable
    filtered_by_season = []
    for r in records:
        date_str = r["date"]
        month = int(date_str[5:7])

        if season == "summer" and month not in (6, 7, 8):
            continue
        elif season == "winter" and month not in (12, 1, 2):
            continue

        filtered_by_season.append(r)

    if not filtered_by_season:
        return []

    # Group counts by year
    year_records = defaultdict(list)
    for r in filtered_by_season:
        year = int(r["date"][:4])
        year_records[year].append(r)

    years = sorted(year_records.keys())
    if len(years) <= 1:
        return filtered_by_season

    first_year = years[0]
    last_year = years[-1]

    # Required threshold: 10 months for full year, 2 for 3-month season splits, or 5 for broader splits
    min_months = 10 if season == "all" else (2 if season in ("summer", "winter") else 5)

    valid_records = []
    for year in years:
        count = len(year_records[year])
        # Drop start or end year if incomplete
        if (year in (first_year, last_year)) and count < min_months:
            continue
        valid_records.extend(year_records[year])

    # If all boundary filtering eliminated too many years, fallback to seasonal records
    if len(valid_records) < 12 and len(filtered_by_season) >= 12:
        return filtered_by_season

    return sorted(valid_records, key=lambda x: x["date"])


# ==============================================================================
# 2. Climatology & De-seasonalization
# ==============================================================================

def compute_climatologies_and_anomalies(
    records: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[int, float]]:
    """
    Group observations by calendar month (1..12) to compute monthly baseline climatologies.
    Subtract climatology from each observation to isolate true non-seasonal anomalies:
    A(t) = Y(t) - mean(Y_m)
    """
    if not records:
        return [], {}

    month_buckets = defaultdict(list)
    for r in records:
        m = int(r["date"][5:7])
        month_buckets[m].append(r["value"])

    climatologies = {
        m: float(np.mean(vals)) if vals else 0.0
        for m, vals in month_buckets.items()
    }

    enriched = []
    for r in records:
        m = int(r["date"][5:7])
        clim = climatologies.get(m, 0.0)
        anomaly = round(r["value"] - clim, 4)

        item = dict(r)
        item["anomaly"] = anomaly
        enriched.append(item)

    return enriched, climatologies


# ==============================================================================
# 3. Autocorrelation & Mann-Kendall with Hamed-Rao Correction
# ==============================================================================

def calculate_lag1_autocorrelation(series: np.ndarray) -> float:
    """
    Compute lag-1 serial autocorrelation (r1) on de-seasonalized anomalies:
    r1 = sum((A_t - mean_A) * (A_{t+1} - mean_A)) / sum((A_t - mean_A)^2)
    """
    n = len(series)
    if n < 3:
        return 0.0

    mean = np.mean(series)
    denom = np.sum((series - mean) ** 2)
    if denom == 0:
        return 0.0

    numer = np.sum((series[:-1] - mean) * (series[1:] - mean))
    r1 = float(numer / denom)
    return round(float(np.clip(r1, -0.99, 0.99)), 4)


def compute_mann_kendall_trend(
    values: np.ndarray,
    dates: List[str],
    lag1_autocorr: float,
    is_monthly: bool = True,
) -> Dict[str, Any]:
    """
    Execute autocorrelation-aware Mann-Kendall test.
    Automatically switches to Hamed-Rao modified Mann-Kendall when r1 > 0.20
    to prevent inflated false positives in persistent climate variables.
    Computes Theil-Sen's robust slope and cumulative period change.
    """
    n = len(values)
    if n < 3:
        return {
            "sen_slope": 0.0,
            "cumulative_change": 0.0,
            "p_value": 1.0,
            "z_stat": 0.0,
            "test_used": "Standard Mann-Kendall",
            "is_significant": False,
            "lag1_autocorr": lag1_autocorr,
        }

    # Autocorrelation Switch Rule (r1 > 0.20)
    use_hamed_rao = lag1_autocorr > 0.20

    try:
        if use_hamed_rao:
            res = mk.hamed_rao_modification_test(values)
            test_name = "Hamed-Rao Modified Mann-Kendall"
        else:
            res = mk.original_test(values)
            test_name = "Standard Mann-Kendall"

        raw_slope = float(res.slope) if res.slope is not None and not math.isnan(res.slope) else 0.0
        p_val = float(res.p) if res.p is not None and not math.isnan(res.p) else 1.0
        z_stat = float(getattr(res, "z", 0.0))
        if math.isnan(z_stat):
            z_stat = 0.0
    except Exception as e:
        # Fallback to standard Theil-Sen slope via scipy if mk encounters numerical degeneracy
        print(f"[Notice] PyMannKendall calculation fallback: {e}")
        time_steps = np.arange(n)
        res_sen = stats.theilslopes(values, time_steps)
        raw_slope = float(res_sen.slope) if not math.isnan(res_sen.slope) else 0.0
        p_val = 1.0
        z_stat = 0.0
        test_name = "Standard Mann-Kendall"

    # Annualize slope: If monthly time series, multiply by 12
    annual_sen_slope = round(raw_slope * 12.0 if is_monthly else raw_slope, 4)

    # Calculate observation window in years
    start_year = int(dates[0][:4])
    end_year = int(dates[-1][:4])
    delta_years = max(1, end_year - start_year)
    cumulative_change = round(annual_sen_slope * delta_years, 3)

    return {
        "sen_slope": annual_sen_slope,
        "cumulative_change": cumulative_change,
        "p_value": round(p_val, 5),
        "z_stat": round(z_stat, 3),
        "test_used": test_name,
        "is_significant": bool(p_val < 0.05),
        "lag1_autocorr": lag1_autocorr,
    }


# ==============================================================================
# 4. OLS Regression & Hyperbolic 95% Confidence Bounds
# ==============================================================================

def compute_ols_hyperbolic_bands(
    time_steps: np.ndarray,
    values: np.ndarray,
    alpha: float = 0.05,
    is_monthly: bool = True,
) -> Dict[str, Any]:
    """
    Calculate OLS linear regression and true hyperbolic 95% confidence bands:
    y_hat(t) +/- t_{alpha/2, n-2} * s_e * sqrt(1/n + (t - mean_t)^2 / sum((t_i - mean_t)^2))
    """
    n = len(values)
    if n < 3:
        zeros = [0.0] * n
        return {
            "slope": 0.0,
            "intercept": 0.0,
            "r_squared": 0.0,
            "ci_upper": zeros,
            "ci_lower": zeros,
        }

    # Fit OLS
    reg = stats.linregress(time_steps, values)
    slope = float(reg.slope) if not (math.isnan(reg.slope) or math.isinf(reg.slope)) else 0.0
    intercept = float(reg.intercept) if not (math.isnan(reg.intercept) or math.isinf(reg.intercept)) else 0.0
    r_val = float(reg.rvalue) if not (math.isnan(reg.rvalue) or math.isinf(reg.rvalue)) else 0.0
    r_squared = round(float(r_val ** 2), 4)

    # Fitted values
    y_hat = slope * time_steps + intercept

    # Degrees of freedom and critical t-value
    df = n - 2
    t_crit = stats.t.ppf(1.0 - (alpha / 2.0), df)

    # Residual standard error s_e
    residuals = values - y_hat
    s_e = np.sqrt(np.sum(residuals ** 2) / max(1, df))

    # Centroid and sum of squares
    mean_t = np.mean(time_steps)
    s_tt = np.sum((time_steps - mean_t) ** 2)
    s_tt = max(s_tt, 1e-9)

    # Compute hyperbolic band array
    margin = t_crit * s_e * np.sqrt((1.0 / n) + ((time_steps - mean_t) ** 2) / s_tt)
    raw_ci_upper = np.round(y_hat + margin, 3).tolist()
    raw_ci_lower = np.round(y_hat - margin, 3).tolist()
    ci_upper = [0.0 if (math.isnan(x) or math.isinf(x)) else x for x in raw_ci_upper]
    ci_lower = [0.0 if (math.isnan(x) or math.isinf(x)) else x for x in raw_ci_lower]

    annual_ols_slope = round(slope * 12.0 if is_monthly else slope, 4)

    return {
        "slope": annual_ols_slope,
        "intercept": round(intercept, 4),
        "r_squared": r_squared,
        "ci_upper": ci_upper,
        "ci_lower": ci_lower,
    }


# ==============================================================================
# 5. MAD Episodic Outlier Shield & Skew Guardrail
# ==============================================================================

def detect_mad_episodic_outliers(
    anomalies: np.ndarray,
    ols_slope: float,
    sen_slope: float,
) -> Tuple[np.ndarray, bool]:
    """
    Detect extreme episodic weather spikes (floods, heatwaves) using Median Absolute Deviation:
    modified_z = 0.6745 * |A_i - median(A)| / MAD
    Flags outliers where |modified_z| > 3.0.
    Triggers outlier_skew_warning if OLS slope diverges from Sen's Slope by > 30%.
    """
    n = len(anomalies)
    if n < 5:
        return np.zeros(n, dtype=bool), False

    med = np.median(anomalies)
    abs_deviations = np.abs(anomalies - med)
    mad = np.median(abs_deviations)

    if mad > 1e-6:
        modified_z = 0.6745 * abs_deviations / mad
    else:
        # Fallback to standard standard deviation if median absolute deviation is near zero
        std = np.std(anomalies)
        modified_z = abs_deviations / max(std, 1e-6)

    outlier_mask = modified_z > 3.0

    # Skew Guardrail: Trigger alert if OLS slope diverges from Sen's slope by > 30%
    denom = max(abs(sen_slope), 1e-4)
    relative_divergence = abs(ols_slope - sen_slope) / denom
    outlier_skew_warning = bool(relative_divergence > 0.30 and np.any(outlier_mask))

    return outlier_mask, outlier_skew_warning


# ==============================================================================
# 6. Welch's Epoch t-Test & Cohen's d Effect Size
# ==============================================================================

def compute_welch_epoch_ttest_and_cohens_d(
    annual_means: np.ndarray,
) -> Dict[str, float]:
    """
    Split complete years into Baseline Era (first half) and Recent Era (second half).
    Run unequal-variance Welch's t-test and compute standardized Cohen's d.
    """
    n = len(annual_means)
    if n < 4:
        return {"welch_t": 0.0, "welch_p": 1.0, "cohens_d": 0.0}

    mid = n // 2
    era1 = annual_means[:mid]
    era2 = annual_means[mid:]

    t_stat, p_val = stats.ttest_ind(era2, era1, equal_var=False)

    s1 = np.std(era1, ddof=1)
    s2 = np.std(era2, ddof=1)
    s_pooled = np.sqrt((s1 ** 2 + s2 ** 2) / 2.0)

    if s_pooled > 1e-6:
        d = (np.mean(era2) - np.mean(era1)) / s_pooled
    else:
        d = 0.0

    return {
        "welch_t": round(float(t_stat), 3),
        "welch_p": round(float(p_val), 5),
        "cohens_d": round(float(d), 3),
    }


# ==============================================================================
# 7. Pure-NumPy Benjamini-Hochberg FDR Multiple-Testing Corrector
# ==============================================================================

def benjamini_hochberg_fdr(
    p_values: np.ndarray, alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Vectorized False Discovery Rate (FDR) Benjamini-Hochberg p-value adjustment in pure NumPy.
    Avoids statsmodels to comply with serverless bundle limits.
    Returns: (adjusted_p_values, is_significant_boolean_array)
    """
    raw_arr = np.asarray(p_values, dtype=float)
    p_arr = np.nan_to_num(raw_arr, nan=1.0)
    m = len(p_arr)
    if m == 0:
        return np.array([]), np.array([], dtype=bool)

    # Sort p-values ascending
    sort_idx = np.argsort(p_arr)
    sorted_p = p_arr[sort_idx]

    ranks = np.arange(1, m + 1)
    # Adjusted p-value formula: p * (m / rank)
    adj_p = sorted_p * (m / ranks)

    # Step-up cumulative minimum from end to beginning
    adj_p = np.minimum.accumulate(adj_p[::-1])[::-1]
    adj_p = np.clip(np.nan_to_num(adj_p, nan=1.0), 0.0, 1.0)

    # Restore original order
    final_adj_p = np.empty(m, dtype=float)
    final_adj_p[sort_idx] = adj_p

    is_significant = final_adj_p <= alpha
    return np.round(final_adj_p, 5), is_significant


# ==============================================================================
# 8. Master Trend Analysis Pipeline
# ==============================================================================

def analyze_time_series_trend(
    series: List[Dict[str, Any]], season: str = "all"
) -> Dict[str, Any]:
    """
    Master trend analysis pipeline:
    1. Filter incomplete boundary years.
    2. Compute climatologies and de-seasonalized anomalies.
    3. Measure lag-1 autocorrelation & execute autocorrelation-aware Mann-Kendall.
    4. Compute OLS regression with true hyperbolic 95% confidence bands.
    5. Flag MAD episodic outliers and evaluate slope skew warning.
    6. Compute Welch's epoch t-test and Cohen's d across complete annual means.
    """
    # 1. Filter boundary years
    clean_records = filter_incomplete_boundary_years(series, season=season)
    if len(clean_records) < 6:
        # Fallback to input series if filter dropped too aggressively
        clean_records = series

    # 2. De-seasonalize
    enriched_records, climatologies = compute_climatologies_and_anomalies(clean_records)

    dates = [r["date"] for r in enriched_records]
    raw_vals = np.array([r["value"] for r in enriched_records], dtype=float)
    anomalies = np.array([r["anomaly"] for r in enriched_records], dtype=float)
    time_steps = np.arange(len(raw_vals), dtype=float)

    # 3. Serial Autocorrelation
    r1 = calculate_lag1_autocorrelation(anomalies)

    # 4. Autocorrelation-aware Mann-Kendall & Theil-Sen
    mk_stats = compute_mann_kendall_trend(anomalies, dates, r1, is_monthly=True)

    # 5. OLS Regression & Hyperbolic Confidence Intervals
    ols_stats = compute_ols_hyperbolic_bands(time_steps, anomalies, is_monthly=True)

    # 6. MAD Outlier Shield
    outlier_mask, outlier_skew_warning = detect_mad_episodic_outliers(
        anomalies, ols_stats["slope"], mk_stats["sen_slope"]
    )
    mk_stats["outlier_skew_warning"] = outlier_skew_warning

    # Tag records with outlier status
    for i, r in enumerate(enriched_records):
        r["is_outlier"] = bool(outlier_mask[i])

    # 7. Annual aggregation for Welch's Epoch t-test and Cohen's d
    year_buckets = defaultdict(list)
    for r in enriched_records:
        y = int(r["date"][:4])
        year_buckets[y].append(r["anomaly"])

    complete_years = sorted(y for y, vals in year_buckets.items() if len(vals) >= 2)
    annual_means = np.array([np.mean(year_buckets[y]) for y in complete_years])
    annual_series = [
        {
            "year": y,
            "mean_value": round(float(np.mean([r["value"] for r in enriched_records if int(r["date"][:4]) == y])), 3),
            "mean_anomaly": round(float(np.mean(year_buckets[y])), 3),
            "months_count": len(year_buckets[y]),
        }
        for y in complete_years
    ]

    welch_results = compute_welch_epoch_ttest_and_cohens_d(annual_means)
    mk_stats["welch_t"] = welch_results["welch_t"]
    mk_stats["welch_p"] = welch_results["welch_p"]
    mk_stats["cohens_d"] = welch_results["cohens_d"]

    return {
        "series": enriched_records,
        "annual_series": annual_series,
        "ols": ols_stats,
        "trend": mk_stats,
        "climatology": climatologies,
    }
