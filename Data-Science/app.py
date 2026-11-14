import sys
from pathlib import Path
import math
import numpy as np
import pandas as pd
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

# Ensure trend_detective package can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trend_detective.trend_engine import (
    analyze_time_series_trend,
    benjamini_hochberg_fdr,
)
from trend_detective.driver_attribution import attribute_physical_driver
from trend_detective.source_router import (
    VARIABLE_CATALOG,
    get_variable_time_series,
)

# Page configuration
st.set_page_config(
    page_title="Trend Detective | NASA Data Science Workbench",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Theme Styling
st.markdown(
    """
    <style>
    .main { background-color: #070e07; color: #f8fafc; }
    .stMetric { background-color: #0b180b; padding: 15px; border-radius: 12px; border: 1px solid #1b3d1b; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌍 Trend Detective: NASA Earth Observation Data Science Workbench")
st.caption(
    "AI-augmented non-parametric statistical trend detection, autocorrelation correction, "
    "Working-Hotelling hyperbolic confidence bounds, and silent physical driver attribution."
)

# ==============================================================================
# Sidebar Controls
# ==============================================================================
st.sidebar.header("🔬 Investigation Controls")

PRESETS = {
    "Kansas Plains (USA)": {"lat": 38.5, "lon": -98.0, "var": "surface_temp", "id": "kansas"},
    "Arizona Desert (USA)": {"lat": 34.0, "lon": -111.8, "var": "surface_temp", "id": "arizona"},
    "Pearl River Outflow (China)": {"lat": 22.15, "lon": 113.7, "var": "chlorophyll_a", "id": "pearl_river"},
    "Mississippi River West (USA)": {"lat": 29.05, "lon": -90.1, "var": "chlorophyll_a", "id": "mississippi_west"},
    "Nile Delta (Egypt)": {"lat": 31.05, "lon": 31.0, "var": "surface_temp", "id": "nile_delta"},
    "Custom Coordinates": {"lat": 0.0, "lon": 0.0, "var": "surface_temp", "id": None},
}

selected_preset_name = st.sidebar.selectbox("Select Regional Testbed / Preset", list(PRESETS.keys()))
preset = PRESETS[selected_preset_name]

if selected_preset_name == "Custom Coordinates":
    lat = st.sidebar.number_input("Latitude", -90.0, 90.0, 38.5, step=0.1)
    lon = st.sidebar.number_input("Longitude", -180.0, 180.0, -98.0, step=0.1)
    region_id = None
else:
    lat = preset["lat"]
    lon = preset["lon"]
    region_id = preset["id"]
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    st.sidebar.info(f"Coordinates: **{abs(lat):.2f}°{lat_dir}, {abs(lon):.2f}°{lon_dir}**")

variable_options = {
    "surface_temp": "Land Surface Temperature (°C)",
    "chlorophyll_a": "Chlorophyll-a Concentration (mg/m³)",
    "precipitation": "Precipitation Rate (mm/month)",
    "evapotranspiration": "Evapotranspiration Flux (mm/month)",
    "soil_moisture": "Soil Moisture 0–10cm (kg/m²)",
    "surface_runoff": "Surface Runoff Accumulation (kg/m²)",
}

default_var = preset["var"] if preset["var"] in variable_options else "surface_temp"
selected_var = st.sidebar.selectbox(
    "Earth System Variable",
    list(variable_options.keys()),
    index=list(variable_options.keys()).index(default_var),
    format_func=lambda x: variable_options[x],
)

col_y1, col_y2 = st.sidebar.columns(2)
start_year = col_y1.number_input("Start Year", 2000, 2025, 2003)
end_year = col_y2.number_input("End Year", 2000, 2025, 2025)

season = st.sidebar.selectbox("Season Filter", ["all", "summer", "winter"], format_func=lambda x: x.capitalize())
view_mode = st.sidebar.radio("Series View Mode", ["Anomalies (Deseasonalized)", "Raw Observed Values"])

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Statistical Hyperparameters")
alpha_level = st.sidebar.slider("Significance Threshold (α)", 0.01, 0.10, 0.05, step=0.01)
mad_threshold = st.sidebar.slider("MAD Outlier Threshold (|M_i|)", 2.0, 5.0, 3.0, step=0.5)

# ==============================================================================
# Data Fetching & Pipeline Execution
# ==============================================================================
with st.spinner("Executing statistical trend engine & physical driver attribution..."):
    data = get_variable_time_series(
        lat=lat,
        lon=lon,
        variable=selected_var,
        start_year=int(start_year),
        end_year=int(end_year),
        region_id=region_id,
    )
    series = data["series"]
    trend_result = analyze_time_series_trend(series, season=season)
    trend = trend_result["trend"]
    ols = trend_result["ols"]
    processed_series = trend_result["series"]

    driver_result = attribute_physical_driver(
        lat=lat,
        lon=lon,
        variable_key=selected_var,
        primary_series=processed_series,
        trend_stats=trend,
        start_year=int(start_year),
        end_year=int(end_year),
    )

# ==============================================================================
# Top 4-Pillar Summary Cards
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    direction = "Increasing ↗" if trend["sen_slope"] > 0 else "Decreasing ↘" if trend["sen_slope"] < 0 else "Neutral →"
    st.metric(
        "1. What Is Changing",
        f"{VARIABLE_CATALOG[selected_var]['label']}",
        f"{direction} ({(trend['sen_slope'] * 10):+.3f} {data['unit']}/decade)",
    )

with col2:
    st.metric(
        "2. Where",
        selected_preset_name.split(" (")[0],
        f"{lat:.2f}°, {lon:.2f}°",
    )

with col3:
    st.metric(
        "3. By How Much",
        f"{trend['sen_slope']:+.4f} {data['unit']}/yr",
        f"Cumulative: {trend['cumulative_change']:+.3f} {data['unit']}",
    )

with col4:
    sig_label = "SIGNIFICANT ✅" if trend["is_significant"] else "NON-SIGNIFICANT ❌"
    st.metric(
        "4. Significance",
        sig_label,
        f"p = {trend['p_value']:.4f} ({trend['test_used']})",
    )

st.markdown("---")

# ==============================================================================
# Interactive Plotly Trend Visualization
# ==============================================================================
st.subheader("📈 Statistical Trend Decomposition Canvas")

dates = [p["date"] for p in processed_series]
y_vals = [p["anomaly"] if "Anomalies" in view_mode else p["raw_value"] for p in processed_series]
n = len(dates)

if HAS_PLOTLY:
    fig = go.Figure()

    # 1. Shaded Hyperbolic 95% Confidence Band
    if ols and ols.get("ci_upper") and ols.get("ci_lower"):
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ols["ci_upper"],
                mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ols["ci_lower"],
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(74, 222, 128, 0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name="95% Hyperbolic CI Band",
                hoverinfo="skip",
            )
        )

    # 2. Primary Observed Series
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=y_vals,
            mode="lines+markers",
            line=dict(color="#4ade80", width=1.8),
            marker=dict(size=3.5, color="#4ade80"),
            name="Observed Series",
            hovertemplate="<b>%{x}</b><br>Value: %{y:.3f} " + data["unit"] + "<extra></extra>",
        )
    )

    # 3. OLS Linear Regression Fit
    if ols:
        ols_y = [ols["intercept"] + ols["slope"] * i for i in range(n)]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ols_y,
                mode="lines",
                line=dict(dash="dash", color="#94a3b8", width=1.5),
                name=f"OLS Linear Fit (R² = {ols['r_squared']:.2f})",
                hovertemplate="OLS Fit: %{y:.3f}<extra></extra>",
            )
        )

    # 4. Theil-Sen Robust Slope Line
    if trend:
        sen_per_month = trend["sen_slope"] / 12.0
        sorted_y = sorted(y_vals)
        median_y = sorted_y[len(sorted_y) // 2]
        mid_idx = (n - 1) / 2.0
        sen_intercept = median_y - (sen_per_month * mid_idx)
        sen_y = [sen_intercept + (sen_per_month * i) for i in range(n)]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sen_y,
                mode="lines",
                line=dict(color="#22c55e", width=2.5),
                name=f"Theil-Sen Trend ({trend['sen_slope']:+.4f} {data['unit']}/yr)",
                hovertemplate="Theil-Sen: %{y:.3f}<extra></extra>",
            )
        )

    # 5. MAD Episodic Outlier Markers
    outliers = [p for p in processed_series if p.get("is_outlier")]
    if outliers:
        fig.add_trace(
            go.Scatter(
                x=[p["date"] for p in outliers],
                y=[p["anomaly"] if "Anomalies" in view_mode else p["raw_value"] for p in outliers],
                mode="markers",
                marker=dict(symbol="diamond", color="#ef4444", size=8, line=dict(color="#ffffff", width=1)),
                name=f"MAD Episodic Outlier ({len(outliers)})",
                hovertemplate="<b>MAD Outlier Pulse</b><br>%{x}: %{y:.3f} " + data["unit"] + "<extra></extra>",
            )
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11, 24, 11, 0.4)",
        font=dict(color="#cbd5e1"),
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(gridcolor="rgba(148, 163, 184, 0.1)", zerolinecolor="rgba(148, 163, 184, 0.2)"),
        yaxis=dict(
            title=f"{VARIABLE_CATALOG[selected_var]['label']} ({data['unit']})",
            gridcolor="rgba(148, 163, 184, 0.1)",
            zerolinecolor="rgba(148, 163, 184, 0.2)",
        ),
        legend=dict(orientation="h", y=1.12, x=0),
        hovermode="x unified",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    df_plot = pd.DataFrame({"Date": dates, "Observed": y_vals}).set_index("Date")
    st.line_chart(df_plot)

# ==============================================================================
# Scientific Deep-Dive Tabs
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Statistical Engine Diagnostics",
    "🔗 Silent Physical Driver Attribution",
    "🌐 Multi-Region Scan (FDR)",
    "📥 Raw Dataset & CSV Export",
])

with tab1:
    st.subheader("Statistical Tests & Parameter Metrics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Test Applied:** `{trend['test_used']}`")
        st.write(f"**Lag-1 Autocorrelation ($r_1$):** `{trend['lag1_autocorr']:.4f}`")
        st.write(f"**Promoted to Hamed-Rao:** `{trend['lag1_autocorr'] > 0.20}`")
    with c2:
        st.write(f"**Mann-Kendall $Z$-Statistic:** `{trend['z_stat']:.3f}`")
        st.write(f"**Asymptotic $p$-value:** `{trend['p_value']:.5f}`")
        st.write(f"**Theil-Sen Median Slope:** `{trend['sen_slope']:+.5f}`")
    with c3:
        st.write(f"**Welch's Epoch Shift ($t$):** `{trend.get('welch_t', 0.0):.2f}`")
        st.write(f"**Cohen's Effect Size ($d$):** `{trend.get('cohens_d', 0.0):.2f}`")
        st.write(f"**Outlier Slope Skew Warning:** `{trend.get('outlier_skew_warning', False)}`")

with tab2:
    st.subheader("Silent Cause-and-Effect Driver Synthesis")
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.info(f"**Paired Physical Driver:**\n\n`{driver_result['driver_name']}`")
        st.metric(
            "Coupling Strength",
            f"{driver_result['coupling_strength']}",
            f"Pearson r = {driver_result['correlation_r']:+.2f}",
        )
    with col_d2:
        st.success(f"**Natural Language Synthesis:**\n\n{driver_result['driver_reason']}")

with tab3:
    st.subheader("Parallel Benchmark Testbeds with Benjamini-Hochberg FDR")
    scan_benchmarks = [
        {"id": "kansas", "name": "Kansas Plains (USA)", "lat": 38.5, "lon": -98.0, "var": "surface_temp"},
        {"id": "arizona", "name": "Arizona Desert (USA)", "lat": 34.0, "lon": -111.8, "var": "surface_temp"},
        {"id": "pearl_river", "name": "Pearl River Outflow (China)", "lat": 22.15, "lon": 113.7, "var": "chlorophyll_a"},
        {"id": "mississippi_west", "name": "Mississippi River West (USA)", "lat": 29.05, "lon": -90.1, "var": "chlorophyll_a"},
        {"id": "nile_delta", "name": "Nile Delta (Egypt)", "lat": 31.05, "lon": 31.0, "var": "surface_temp"},
    ]

    scan_rows = []
    scan_p_vals = []
    for sb in scan_benchmarks:
        b_data = get_variable_time_series(sb["lat"], sb["lon"], sb["var"], 2003, 2025, region_id=sb["id"])
        b_trend = analyze_time_series_trend(b_data["series"], season="all")["trend"]
        scan_p_vals.append(b_trend["p_value"])
        scan_rows.append({
            "Region": sb["name"],
            "Variable": sb["var"],
            "Sen Slope": f"{b_trend['sen_slope']:+.4f} {b_data['unit']}/yr",
            "Cumulative Change": f"{b_trend['cumulative_change']:+.3f}",
            "Raw p-value": b_trend["p_value"],
        })

    fdr_p, fdr_sig = benjamini_hochberg_fdr(scan_p_vals, alpha=alpha_level)
    for i, row in enumerate(scan_rows):
        row["FDR-Adjusted p"] = round(fdr_p[i], 5)
        row["FDR Status"] = "SIGNIFICANT ✅" if fdr_sig[i] else "NON-SIG ❌"

    st.dataframe(pd.DataFrame(scan_rows), use_container_width=True)

with tab4:
    df_series = pd.DataFrame(processed_series)
    st.dataframe(df_series, use_container_width=True)
    csv = df_series.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Sanitized CSV (RFC 4180)",
        data=csv,
        file_name=f"trend_detective_{selected_var}_{selected_preset_name.split()[0].lower()}.csv",
        mime="text/csv",
    )
