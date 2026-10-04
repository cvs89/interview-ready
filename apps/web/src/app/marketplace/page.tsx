"use client";

import type { InterviewerProfile, Skill } from "@interview-ready/api-types";
import { ChevronLeft, ChevronRight, Loader2, Users } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import { InterviewerCard } from "../../components/marketplace/InterviewerCard";
import {
  InterviewerFilter,
  type FilterValues,
} from "../../components/marketplace/InterviewerFilter";
import { useAuth } from "../../context/AuthContext";

const PAGE_SIZE = 12;

export default function MarketplacePage() {
  const { api } = useAuth();

  const [skills, setSkills] = useState<Skill[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerProfile[]>([]);
  const [filters, setFilters] = useState<FilterValues>({});
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load skills list once
  useEffect(() => {
    let isCancelled = false;
    api
      .get<Skill[]>("/skills")
      .then((data) => {
        if (!isCancelled) setSkills(data);
      })
      .catch(() => {});
    return () => {
      isCancelled = true;
    };
  }, [api]);

  const loadInterviewers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number | undefined> = {
        limit: PAGE_SIZE,
        offset,
        skill: filters.skill,
        min_years_experience: filters.minYearsExperience,
        min_price_minor: filters.minPriceMinor,
        max_price_minor: filters.maxPriceMinor,
        available_from: filters.availableFrom,
        available_to: filters.availableTo,
      };
      const data = await api.get<InterviewerProfile[]>("/interviewers", { params });
      setInterviewers(data);
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setError(eObj.message || "Failed to load interviewers.");
    } finally {
      setLoading(false);
    }
  }, [api, filters, offset]);

  useEffect(() => {
    loadInterviewers();
  }, [loadInterviewers]);

  const handleFilterChange = (newFilters: FilterValues) => {
    setFilters(newFilters);
    setOffset(0); // Reset to first page
  };

  const handleResetFilters = () => {
    setFilters({});
    setOffset(0);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 sm:py-14 bg-[#FFF8F0] min-h-screen">
      {/* Header Banner */}
      <div className="mb-10 max-w-3xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-3.5 py-1 text-xs font-semibold text-[#9B3B25] mb-3">
          <span>Curated Network</span>
        </div>
        <h1 className="font-editorial text-3xl sm:text-5xl font-bold tracking-tight text-[#342523]">
          Discover Technical Interviewers<span className="text-[#9B3B25]">.</span>
        </h1>
        <p className="mt-3 text-base text-[#6E5652] leading-relaxed font-sans">
          Real mock interview practice with approved engineering leaders and hiring managers. Book dedicated slots with clear, upfront pricing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 items-start">
        {/* Filters Sidebar */}
        <aside className="md:col-span-1">
          <div className="sticky top-24">
            <InterviewerFilter
              skills={skills}
              values={filters}
              onChange={handleFilterChange}
              onReset={handleResetFilters}
            />
          </div>
        </aside>

        {/* Interviewers Grid */}
        <div className="md:col-span-3 space-y-6">
          {error && (
            <div className="rounded-2xl border border-[#F5C2C2] bg-[#FCEBEB] p-4 text-sm text-[#9E2A2B]">
              {error}
            </div>
          )}

          {loading ? (
            <div className="card-confidence flex min-h-[340px] items-center justify-center p-12">
              <div className="text-center">
                <Loader2 className="mx-auto h-9 w-9 animate-spin text-[#9B3B25] mb-3" />
                <p className="text-sm text-[#6E5652] font-semibold">Finding available interviewers...</p>
              </div>
            </div>
          ) : interviewers.length === 0 ? (
            <div className="card-confidence flex min-h-[340px] flex-col items-center justify-center p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4] mb-4">
                <Users className="h-7 w-7" />
              </div>
              <h3 className="font-editorial text-xl font-bold text-[#342523] mb-1.5">
                No interviewers matched
              </h3>
              <p className="text-sm text-[#6E5652] max-w-sm mb-5">
                Try widening your skills, experience, or price filters to see more available leaders.
              </p>
              <button
                onClick={handleResetFilters}
                className="btn-pill-primary px-5 py-2 text-sm"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {interviewers.map((profile) => (
                  <InterviewerCard key={profile.id} profile={profile} />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t border-[#EADBCE] pt-6 mt-8">
                <button
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0 || loading}
                  className="btn-pill-secondary px-4 py-2 text-xs gap-1"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>
                <span className="text-xs text-[#6E5652] font-medium">
                  Showing {offset + 1}–{offset + interviewers.length}
                </span>
                <button
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={interviewers.length < PAGE_SIZE || loading}
                  className="btn-pill-secondary px-4 py-2 text-xs gap-1"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
