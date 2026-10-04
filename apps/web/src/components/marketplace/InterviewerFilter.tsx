"use client";

import type { Skill } from "@interview-ready/api-types";
import { Filter, RotateCcw } from "lucide-react";
import React, { useState } from "react";

export interface FilterValues {
  skill?: string;
  minYearsExperience?: number;
  minPriceMinor?: number;
  maxPriceMinor?: number;
  availableFrom?: string;
  availableTo?: string;
}

interface InterviewerFilterProps {
  skills: Skill[];
  values: FilterValues;
  onChange: (newValues: FilterValues) => void;
  onReset: () => void;
}

export function InterviewerFilter({ skills, values, onChange, onReset }: InterviewerFilterProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleFieldChange = (key: keyof FilterValues, value: unknown) => {
    onChange({
      ...values,
      [key]: value === "" || value === null ? undefined : value,
    });
  };

  return (
    <div className="card-confidence p-5 sm:p-6">
      <div className="flex items-center justify-between border-b border-[#EADBCE] pb-4 mb-4">
        <div className="flex items-center gap-2 font-editorial text-lg font-bold text-[#342523]">
          <Filter className="h-5 w-5 text-[#9B3B25]" />
          <span>Filters</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onReset}
            className="flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold text-[#6E5652] hover:bg-[#FDF5EE] hover:text-[#9B3B25] transition cursor-pointer"
            type="button"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>
          <button
            type="button"
            className="md:hidden text-xs font-semibold rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-3 py-1 text-[#9B3B25]"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? "Hide" : "Show Filters"}
          </button>
        </div>
      </div>

      <div className={`space-y-4 ${mobileOpen ? "block" : "hidden md:block"}`}>
        {/* Skill Filter */}
        <div>
          <label htmlFor="skill-filter" className="block text-xs font-semibold text-[#6E5652] uppercase tracking-wider mb-1.5">
            Skill / Topic
          </label>
          <select
            id="skill-filter"
            value={values.skill || ""}
            onChange={(e) => handleFieldChange("skill", e.target.value)}
            className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
          >
            <option value="">All Skills</option>
            {skills.map((s) => (
              <option key={s.id} value={s.slug}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Experience Filter */}
        <div>
          <label htmlFor="exp-filter" className="block text-xs font-semibold text-[#6E5652] uppercase tracking-wider mb-1.5">
            Min Experience (Years)
          </label>
          <input
            id="exp-filter"
            type="number"
            min={0}
            max={50}
            placeholder="e.g. 5"
            value={values.minYearsExperience ?? ""}
            onChange={(e) =>
              handleFieldChange(
                "minYearsExperience",
                e.target.value ? parseInt(e.target.value, 10) : undefined
              )
            }
            className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
          />
        </div>

        {/* Price Range */}
        <div>
          <label className="block text-xs font-semibold text-[#6E5652] uppercase tracking-wider mb-1.5">
            Price Range (INR)
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              min={0}
              placeholder="Min"
              value={values.minPriceMinor !== undefined ? values.minPriceMinor / 100 : ""}
              onChange={(e) =>
                handleFieldChange(
                  "minPriceMinor",
                  e.target.value ? Math.round(parseFloat(e.target.value) * 100) : undefined
                )
              }
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
            />
            <input
              type="number"
              min={0}
              placeholder="Max"
              value={values.maxPriceMinor !== undefined ? values.maxPriceMinor / 100 : ""}
              onChange={(e) =>
                handleFieldChange(
                  "maxPriceMinor",
                  e.target.value ? Math.round(parseFloat(e.target.value) * 100) : undefined
                )
              }
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
            />
          </div>
        </div>

        {/* Date / Availability */}
        <div>
          <label htmlFor="avail-from-filter" className="block text-xs font-semibold text-[#6E5652] uppercase tracking-wider mb-1.5">
            Available From
          </label>
          <input
            id="avail-from-filter"
            type="datetime-local"
            value={values.availableFrom ? values.availableFrom.slice(0, 16) : ""}
            onChange={(e) =>
              handleFieldChange(
                "availableFrom",
                e.target.value ? new Date(e.target.value).toISOString() : undefined
              )
            }
            className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
          />
        </div>
      </div>
    </div>
  );
}
