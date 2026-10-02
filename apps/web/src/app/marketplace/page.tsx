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
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Banner */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight sm:text-4xl">
          Discover Technical Interviewers
        </h1>
        <p className="mt-2 text-base text-gray-600 max-w-2xl">
          Book 1-on-1 mock interviews with vetted engineers and hiring managers from top tech companies.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
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
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex min-h-[300px] items-center justify-center rounded-2xl border border-gray-100 bg-white p-12">
              <div className="text-center">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600 mb-2" />
                <p className="text-sm text-gray-500 font-medium">Finding available interviewers...</p>
              </div>
            </div>
          ) : interviewers.length === 0 ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-white p-12 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-3">
                <Users className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-1">No interviewers matched</h3>
              <p className="text-sm text-gray-500 max-w-sm mb-4">
                Try adjusting your skills, experience, or price filters to see more results.
              </p>
              <button
                onClick={handleResetFilters}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
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
              <div className="flex items-center justify-between border-t border-gray-200 pt-6 mt-8">
                <button
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0 || loading}
                  className="flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition shadow-sm"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>
                <span className="text-xs text-gray-500 font-medium">
                  Showing {offset + 1}–{offset + interviewers.length}
                </span>
                <button
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={interviewers.length < PAGE_SIZE || loading}
                  className="flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition shadow-sm"
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
