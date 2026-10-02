"use client";

import type { AvailabilitySlot, InterviewerProfile } from "@interview-ready/api-types";
import { Award, Briefcase, CheckCircle2, ChevronLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import React, { useEffect, useState } from "react";

import { SlotSelector } from "../../../components/marketplace/SlotSelector";
import { useAuth } from "../../../context/AuthContext";
import { formatCurrency } from "../../../lib/api-client";

export default function InterviewerProfilePage() {
  const params = useParams();
  const interviewerId = params?.id as string;
  const { api } = useAuth();

  const [profile, setProfile] = useState<InterviewerProfile | null>(null);
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!interviewerId) return;
    let isCancelled = false;
    setLoading(true);

    Promise.all([
      api.get<InterviewerProfile>(`/interviewers/${interviewerId}`),
      api.get<AvailabilitySlot[]>(`/interviewers/${interviewerId}/slots`),
    ])
      .then(([profData, slotsData]) => {
        if (!isCancelled) {
          setProfile(profData);
          setSlots(slotsData);
        }
      })
      .catch((err: unknown) => {
        if (!isCancelled) {
          const eObj = err as { message?: string };
          setError(eObj.message || "Interviewer profile not found.");
        }
      })
      .finally(() => {
        if (!isCancelled) setLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [api, interviewerId]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Not Found</h2>
        <p className="text-gray-500 mb-6">{error || "The requested interviewer profile does not exist."}</p>
        <Link
          href="/marketplace"
          className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-500"
        >
          <ChevronLeft className="h-4 w-4" /> Back to Marketplace
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
      <Link
        href="/marketplace"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-600 hover:text-blue-600 transition mb-6"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to Interviewers
      </Link>

      {/* Profile Header */}
      <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm mb-8">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{profile.full_name}</h1>
              {profile.is_verified && (
                <span title="Verified Interviewer">
                  <CheckCircle2 className="h-5 w-5 text-blue-600 fill-blue-50" />
                </span>
              )}
            </div>
            <p className="text-base font-medium text-gray-600 mb-3">{profile.title || "Technical Interviewer"}</p>

            {profile.years_experience !== null && profile.years_experience !== undefined && (
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                <Briefcase className="h-4 w-4 text-gray-400" />
                <span>{profile.years_experience} years engineering experience</span>
              </div>
            )}

            {profile.skills && profile.skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((s) => (
                  <span
                    key={s.id}
                    className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700"
                  >
                    <Award className="h-3 w-3" />
                    {s.name}
                  </span>
                ))}
              </div>
            )}
          </div>

          {profile.default_rate_minor !== null && profile.default_rate_minor !== undefined && (
            <div className="rounded-xl bg-gray-50 border border-gray-200 p-4 text-center sm:text-right min-w-[140px]">
              <span className="text-xs text-gray-500 block">Rate per session</span>
              <span className="text-xl font-bold text-gray-900 block">
                {formatCurrency(profile.default_rate_minor, profile.currency || "INR")}
              </span>
            </div>
          )}
        </div>

        {profile.bio && (
          <div className="border-t border-gray-100 pt-6 mt-6">
            <h3 className="font-semibold text-gray-900 text-sm mb-2">About the Interviewer</h3>
            <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{profile.bio}</p>
          </div>
        )}
      </div>

      {/* Slot Selection Section */}
      <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <SlotSelector
          interviewerId={profile.id}
          interviewerName={profile.full_name}
          slots={slots}
        />
      </div>
    </div>
  );
}
