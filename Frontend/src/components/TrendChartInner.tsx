"use client";

import React, { useMemo } from "react";
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { TrendAnalysisResponse } from "@/types/trends";
import { Loader2 } from "lucide-react";

const Plot = createPlotlyComponent(Plotly);

export interface TrendChartProps {
  dataA: TrendAnalysisResponse | null;
  dataB?: TrendAnalysisResponse | null;
  viewMode: "anomalies" | "raw";
  isDivergenceMode: boolean;
  isLoading?: boolean;
  className?: string;
}

interface SingleChartPanelProps {
  data: TrendAnalysisResponse;
  accent: "green" | "lime";
  labelPrefix?: string;
  viewMode: "anomalies" | "raw";
  height?: string;
}

function SingleChartPanel({
  data,
  accent,
  labelPrefix,
  viewMode,
  height = "h-44",
}: SingleChartPanelProps) {
  const isGreen = accent === "green";
  const borderColor = isGreen ? "border-[#22c55e]" : "border-[#a3e635]";
  const lineColor = isGreen ? "#4ade80" : "#bef264";
  const fillColor = isGreen
    ? "rgba(34, 197, 94, 0.15)"
    : "rgba(163, 230, 53, 0.15)";
  const bgTint = isGreen ? "bg-[#0a180a]/90" : "bg-[#14210a]/90";

  const chartData = useMemo(() => {
    if (!data.series || data.series.length === 0) return [];

    const traces: any[] = [];
    const dates = data.series.map((p) => p.date);
    const yVals = data.series.map((p) =>
      viewMode === "anomalies" ? p.anomaly : p.raw_value
    );
    const n = dates.length;

    // 1. Shaded Hyperbolic 95% Confidence Band
    if (
      data.ols &&
      data.ols.ci_upper &&
      data.ols.ci_lower &&
      data.ols.ci_upper.length === n
    ) {
      traces.push({
        x: dates,
        y: data.ols.ci_upper,
        type: "scatter",
        mode: "lines",
        line: { color: "transparent" },
        showlegend: false,
        hoverinfo: "skip",
      });

      traces.push({
        x: dates,
        y: data.ols.ci_lower,
        type: "scatter",
        mode: "lines",
        fill: "tonexty",
        fillcolor: fillColor,
        line: { color: "transparent" },
        name: "95% CI Band",
        hoverinfo: "skip",
      });
    }

    // 2. Primary Observed Series
    traces.push({
      x: dates,
      y: yVals,
      type: "scatter",
      mode: "lines",
      line: { color: lineColor, width: 2 },
      name: `${data.region_label}`,
      hovertemplate: `<b>%{x}</b><br>Value: %{y:.3f} ${data.unit}<extra></extra>`,
    });

    // 3. OLS Linear Regression
    if (data.ols && typeof data.ols.intercept === "number" && typeof data.ols.slope === "number") {
      const olsY = dates.map(
        (_, i) => (data.ols.intercept || 0) + (data.ols.slope || 0) * i
      );
      const r2Text =
        typeof data.ols.r_squared === "number" && !isNaN(data.ols.r_squared)
          ? data.ols.r_squared.toFixed(2)
          : "N/A";
      traces.push({
        x: dates,
        y: olsY,
        type: "scatter",
        mode: "lines",
        line: { dash: "dash", color: "#94a3b8", width: 1.2 },
        name: `OLS Fit (R²=${r2Text})`,
        hovertemplate: `OLS: %{y:.3f} ${data.unit}<extra></extra>`,
      });
    }

    // 4. Theil-Sen Robust Slope Line
    if (data.trend && typeof data.trend.sen_slope === "number") {
      const senPerMonth = data.trend.sen_slope / 12;
      const sortedY = [...yVals].sort((a, b) => a - b);
      const medianY = sortedY[Math.floor(sortedY.length / 2)] || 0;
      const midIdx = (n - 1) / 2;
      const senIntercept = medianY - senPerMonth * midIdx;
      const senY = dates.map((_, i) => senIntercept + senPerMonth * i);

      const sign = data.trend.sen_slope >= 0 ? "+" : "";
      traces.push({
        x: dates,
        y: senY,
        type: "scatter",
        mode: "lines",
        line: { color: isGreen ? "#22c55e" : "#84cc16", width: 2.2 },
        name: `Theil-Sen (${sign}${data.trend.sen_slope.toFixed(3)}/yr)`,
        hovertemplate: `Sen Slope: %{y:.3f}<extra></extra>`,
      });
    }

    // 5. MAD Outliers
    const outliers = data.series.filter((p) => p.is_outlier);
    if (outliers.length > 0) {
      traces.push({
        x: outliers.map((p) => p.date),
        y: outliers.map((p) =>
          viewMode === "anomalies" ? p.anomaly : p.raw_value
        ),
        type: "scatter",
        mode: "markers",
        marker: {
          symbol: "diamond",
          color: "#ef4444",
          size: 7,
          line: { color: "#ffffff", width: 1 },
        },
        name: "MAD Outlier",
        hovertemplate: `<b>Outlier Spike</b><br>%{x}: %{y:.3f}<extra></extra>`,
      });
    }

    return traces;
  }, [data, accent, viewMode]);

  const layout = useMemo(() => {
    return {
      autosize: true,
      margin: { l: 45, r: 25, t: 15, b: 25 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: {
        family: "ui-sans-serif, system-ui, sans-serif",
        color: "#94a3b8",
        size: 10,
      },
      xaxis: {
        gridcolor: "rgba(148, 163, 184, 0.08)",
        zerolinecolor: "rgba(148, 163, 184, 0.15)",
        tickfont: { color: "#94a3b8", size: 9 },
        showgrid: true,
      },
      yaxis: {
        gridcolor: "rgba(148, 163, 184, 0.08)",
        zerolinecolor: "rgba(148, 163, 184, 0.15)",
        tickfont: { color: "#94a3b8", size: 9 },
        showgrid: true,
      },
      showlegend: false,
      hovermode: "x unified" as const,
    };
  }, []);

  return (
    <div
      className={`relative w-full ${height} rounded-3xl border-2 ${borderColor} ${bgTint} backdrop-blur-md p-3.5 shadow-2xl flex flex-col`}
    >
      {/* Top Axis Label matching Figma mockup */}
      <div className="flex items-center justify-between text-xs font-bold text-white px-2">
        <div className="flex items-center gap-1.5">
          <span className="capitalize">
            {data.variable_name.replace(/_/g, " ")}
          </span>
          <span className="text-white">↑</span>
          {labelPrefix && (
            <span className="text-[11px] font-medium text-slate-300 ml-1">
              ({labelPrefix})
            </span>
          )}
        </div>
        <div className="text-[10px] text-slate-300 font-mono">
          Sen&apos;s Slope: {(data.trend?.sen_slope ?? 0) >= 0 ? "+" : ""}
          {(data.trend?.sen_slope ?? 0).toFixed(4)} {data.unit}/yr
        </div>
      </div>

      {/* Plotly Chart Canvas */}
      <div className="flex-1 w-full min-h-0">
        <Plot
          data={chartData}
          layout={layout}
          config={{
            responsive: true,
            displayModeBar: false,
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
        />
      </div>

      {/* Bottom Axis Label matching Figma mockup */}
      <div className="flex justify-end text-xs font-bold text-white px-2 mt-[-4px]">
        <span>Time →</span>
      </div>
    </div>
  );
}

export default function TrendChartInner({
  dataA,
  dataB,
  viewMode,
  isDivergenceMode,
  isLoading = false,
  className = "w-full",
}: TrendChartProps) {
  if (isLoading) {
    return (
      <div className="w-full h-56 rounded-3xl border border-[#22c55e]/40 bg-[#0a180a]/90 backdrop-blur-md flex flex-col items-center justify-center gap-2 text-green-400 text-xs font-semibold shadow-2xl">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span>Calculating Hamed-Rao Trend & Confidence Bounds...</span>
      </div>
    );
  }

  if (!dataA) {
    return (
      <div className="w-full h-56 rounded-3xl border border-slate-800 bg-[#0a180a]/90 backdrop-blur-md flex items-center justify-center text-slate-400 text-xs">
        Click &quot;Calculate&quot; to compute trends and render statistical charts.
      </div>
    );
  }

  // Screen 4: Divergence Mode (Two Stacked Cards matching MacBook Air - 4.png)
  if (isDivergenceMode && dataB) {
    return (
      <div className={`flex flex-col gap-3 w-full ${className}`}>
        {/* Top Card: Region A (Lime Accent) */}
        <SingleChartPanel
          data={dataA}
          accent="lime"
          labelPrefix={dataA.region_label}
          viewMode={viewMode}
          height="h-44"
        />

        {/* Bottom Card: Region B (Green Accent) */}
        <SingleChartPanel
          data={dataB}
          accent="green"
          labelPrefix={dataB.region_label}
          viewMode={viewMode}
          height="h-44"
        />
      </div>
    );
  }

  // Screen 3: Single Region (Single Bottom Card matching MacBook Air - 3.png)
  return (
    <div className={`w-full ${className}`}>
      <SingleChartPanel
        data={dataA}
        accent="green"
        labelPrefix={dataA.region_label}
        viewMode={viewMode}
        height="h-60"
      />
    </div>
  );
}
