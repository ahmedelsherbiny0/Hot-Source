"use client";

import dynamic from "next/dynamic";
import React from "react";
import { LineChart } from "lucide-react";
import type { TrendChartProps } from "./TrendChartInner";

const DynamicChart = dynamic(() => import("./TrendChartInner"), {
  ssr: false,
  loading: () => (
    <div className="h-96 w-full rounded-2xl border border-slate-800 bg-slate-950 flex flex-col items-center justify-center text-slate-500 text-xs">
      <LineChart className="w-8 h-8 animate-pulse text-emerald-400/50 mb-2" />
      <span>Loading Statistical Plotly Engine...</span>
    </div>
  ),
});

export default function TrendChart(props: TrendChartProps) {
  return <DynamicChart {...props} />;
}
