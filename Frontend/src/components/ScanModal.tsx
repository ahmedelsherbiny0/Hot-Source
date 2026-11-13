"use client";

import React, { useEffect, useState } from "react";
import { X, Sparkles, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { MultiRegionScanItem, MultiRegionScanResponse } from "@/types/trends";
import { scanBenchmarks } from "@/lib/api";

interface ScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectBenchmark: (item: MultiRegionScanItem) => void;
}

export default function ScanModal({
  isOpen,
  onClose,
  onSelectBenchmark,
}: ScanModalProps) {
  const [data, setData] = useState<MultiRegionScanResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    scanBenchmarks()
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load multi-region benchmark scan.");
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Multi-Region Benchmark Assessment
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-500/30 text-cyan-400">
                  Benjamini-Hochberg FDR
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Parallelized Mann-Kendall evaluation across curated NASA testbeds with False Discovery Rate correction
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400 text-xs">
              <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
              <span>Scanning benchmark testbeds and adjusting FDR p-values...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && data && (
            <div className="flex flex-col gap-5">
              {/* Stats Summary Bar */}
              <div className="grid grid-cols-3 gap-3 p-3 rounded-xl border border-slate-800 bg-slate-950">
                <div className="text-center">
                  <div className="text-xs text-slate-400">Total Scanned</div>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {data.total_regions} Regions
                  </div>
                </div>
                <div className="text-center border-x border-slate-800">
                  <div className="text-xs text-slate-400">FDR Significance Rate</div>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">
                    {data.significant_count} / {data.total_regions} Verified
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-slate-400">FDR Alpha Threshold</div>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">
                    α = {data.fdr_threshold}
                  </div>
                </div>
              </div>

              {/* Table */}
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Region & Variable</th>
                      <th className="py-3 px-4">Window</th>
                      <th className="py-3 px-4">Sen&apos;s Slope</th>
                      <th className="py-3 px-4">Cumulative</th>
                      <th className="py-3 px-4">Raw p</th>
                      <th className="py-3 px-4">FDR p</th>
                      <th className="py-3 px-4 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {data.results.map((item) => (
                      <tr
                        key={item.region_id}
                        onClick={() => {
                          onSelectBenchmark(item);
                          onClose();
                        }}
                        className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                      >
                        <td className="py-3.5 px-4 font-sans">
                          <div className="font-semibold text-white group-hover:text-cyan-400 transition-colors">
                            {item.region_name}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {item.variable_name} ({item.unit})
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-slate-300">
                          {item.start_year}–{item.end_year}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={
                              (item.sen_slope ?? 0) > 0
                                ? "text-emerald-400"
                                : (item.sen_slope ?? 0) < 0
                                ? "text-amber-400"
                                : "text-slate-400"
                            }
                          >
                            {(item.sen_slope ?? 0) > 0 ? "+" : ""}
                            {(item.sen_slope ?? 0).toFixed(4)}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-200">
                          {(item.cumulative_change ?? 0) > 0 ? "+" : ""}
                          {(item.cumulative_change ?? 0).toFixed(3)}
                        </td>
                        <td className="py-3.5 px-4 text-slate-400">
                          {(item.raw_p_value ?? 1).toFixed(4)}
                        </td>
                        <td className="py-3.5 px-4 text-slate-300 font-bold">
                          {(item.fdr_p_value ?? 1).toFixed(4)}
                        </td>
                        <td className="py-3.5 px-4 text-center font-sans">
                          {item.is_significant ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 border border-emerald-500/30 text-emerald-400">
                              <CheckCircle2 className="w-3 h-3" />
                              SIGNIFICANT
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400">
                              NON-SIG
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="text-[11px] text-slate-500 italic text-center">
                Click any benchmark row to immediately load that testbed and variable into the investigative dashboard.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
