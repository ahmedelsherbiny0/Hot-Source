"use client";

import dynamic from "next/dynamic";
import React from "react";
import { Globe } from "lucide-react";
import type { MapSelectorProps } from "./MapSelectorInner";

const DynamicMap = dynamic(() => import("./MapSelectorInner"), {
  ssr: false,
  loading: () => (
    <div className="h-72 w-full rounded-2xl border border-slate-800 bg-slate-950 flex flex-col items-center justify-center text-slate-500 text-xs">
      <Globe className="w-8 h-8 animate-pulse text-cyan-400/50 mb-2" />
      <span>Loading Geospatial Engine...</span>
    </div>
  ),
});

export default function MapSelector(props: MapSelectorProps) {
  return <DynamicMap {...props} />;
}
