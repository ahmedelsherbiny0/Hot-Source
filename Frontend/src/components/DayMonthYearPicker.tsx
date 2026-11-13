"use client";

import React from "react";
import { ChevronDown, Calendar } from "lucide-react";

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

interface DayMonthYearPickerProps {
  label: string;
  value: string; // Format: "YYYY-MM-DD"
  onChange: (val: string) => void;
  minYear?: number;
  maxYear?: number;
}

export default function DayMonthYearPicker({
  label,
  value,
  onChange,
  minYear = 1980,
  maxYear = 2026,
}: DayMonthYearPickerProps) {
  // Parse date parts safely
  const parts = (value || "2003-01-01").split("-");
  const year = parseInt(parts[0], 10) || 2003;
  const month = parseInt(parts[1], 10) || 1;
  const day = parseInt(parts[2], 10) || 1;

  // Maximum valid days in this specific month/year
  const daysInMonth = new Date(year, month, 0).getDate();
  const validDay = Math.min(day, daysInMonth);

  const handleDayChange = (newDay: number) => {
    const formatted = `${year}-${String(month).padStart(2, "0")}-${String(newDay).padStart(2, "0")}`;
    onChange(formatted);
  };

  const handleMonthChange = (newMonth: number) => {
    const maxDays = new Date(year, newMonth, 0).getDate();
    const clampedDay = Math.min(validDay, maxDays);
    const formatted = `${year}-${String(newMonth).padStart(2, "0")}-${String(clampedDay).padStart(2, "0")}`;
    onChange(formatted);
  };

  const handleYearChange = (newYear: number) => {
    const maxDays = new Date(newYear, month, 0).getDate();
    const clampedDay = Math.min(validDay, maxDays);
    const formatted = `${newYear}-${String(month).padStart(2, "0")}-${String(clampedDay).padStart(2, "0")}`;
    onChange(formatted);
  };

  const daysList = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const yearsList = Array.from({ length: maxYear - minYear + 1 }, (_, i) => maxYear - i);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
            {label}
          </span>
          <span className="text-[10px] font-mono font-semibold text-[#5cd466]">
            ({String(validDay).padStart(2, "0")}/{String(month).padStart(2, "0")}/{year})
          </span>
        </div>

        {/* Visual Calendar picker button that syncs with native date input */}
        <label className="relative flex items-center gap-1 text-[10px] font-semibold text-slate-400 hover:text-[#5cd466] bg-[#142d14] hover:bg-[#1a3d1a] px-2 py-0.5 rounded-full border border-[#224d22] cursor-pointer transition-colors">
          <Calendar className="w-3 h-3 text-[#5cd466]" />
          <span>Calendar</span>
          <input
            type="date"
            value={value}
            min={`${minYear}-01-01`}
            max={`${maxYear}-12-31`}
            onChange={(e) => e.target.value && onChange(e.target.value)}
            className="sr-only"
          />
        </label>
      </div>

      <div className="grid grid-cols-3 gap-1.5">
        {/* Day Selector */}
        <div className="relative">
          <label className="text-[9px] text-slate-400 font-medium block mb-0.5">Day</label>
          <div className="relative">
            <select
              value={validDay}
              onChange={(e) => handleDayChange(Number(e.target.value))}
              className="w-full appearance-none bg-[#d9d9d9] text-slate-900 font-bold font-mono text-xs rounded-xl py-1.5 pl-2 pr-5 focus:outline-none focus:ring-2 focus:ring-[#5cd466] shadow-sm cursor-pointer"
            >
              {daysList.map((d) => (
                <option key={d} value={d}>
                  {String(d).padStart(2, "0")}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-700 absolute right-1.5 top-2 pointer-events-none" />
          </div>
        </div>

        {/* Month Selector */}
        <div className="relative">
          <label className="text-[9px] text-slate-400 font-medium block mb-0.5">Month</label>
          <div className="relative">
            <select
              value={month}
              onChange={(e) => handleMonthChange(Number(e.target.value))}
              className="w-full appearance-none bg-[#d9d9d9] text-slate-900 font-bold font-mono text-xs rounded-xl py-1.5 pl-1.5 pr-5 focus:outline-none focus:ring-2 focus:ring-[#5cd466] shadow-sm cursor-pointer"
            >
              {MONTH_NAMES.map((name, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {String(idx + 1).padStart(2, "0")} - {name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-700 absolute right-1.5 top-2 pointer-events-none" />
          </div>
        </div>

        {/* Year Selector */}
        <div className="relative">
          <label className="text-[9px] text-slate-400 font-medium block mb-0.5">Year</label>
          <div className="relative">
            <select
              value={year}
              onChange={(e) => handleYearChange(Number(e.target.value))}
              className="w-full appearance-none bg-[#d9d9d9] text-slate-900 font-bold font-mono text-xs rounded-xl py-1.5 pl-2 pr-5 focus:outline-none focus:ring-2 focus:ring-[#5cd466] shadow-sm cursor-pointer"
            >
              {yearsList.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-700 absolute right-1.5 top-2 pointer-events-none" />
          </div>
        </div>
      </div>
    </div>
  );
}
