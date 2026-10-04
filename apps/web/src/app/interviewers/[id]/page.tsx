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
      <div className="flex min-h-[60vh] items-center justify-center bg-[#FFF8F0]">
        <Loader2 className="h-8 w-8 animate-spin text-[#9B3B25]" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-10 shadow-sm max-w-lg mx-auto">
          <h2 className="font-serif text-2xl font-normal text-[#342523] mb-2">Profile Not Found</h2>
          <p className="text-[#6E5652] text-sm mb-6">{error || "The requested interviewer profile does not exist."}</p>
          <Link
            href="/marketplace"
            className="inline-flex items-center gap-1 rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] transition"
          >
            <ChevronLeft className="h-4 w-4" /> Back to Marketplace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FFF8F0] py-10">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/marketplace"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[#6E5652] hover:text-[#9B3B25] transition mb-6"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Interviewers
        </Link>

        {/* Profile Header */}
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-sm mb-8">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#342523]">{profile.full_name}</h1>
                {profile.is_verified && (
                  <span title="Verified Interviewer">
                    <CheckCircle2 className="h-5 w-5 text-[#2C6E49] fill-[#E8F4EC]" />
                  </span>
                )}
              </div>
              <p className="text-base font-medium text-[#6E5652] mb-3">{profile.title || "Technical Interviewer"}</p>

              {profile.years_experience !== null && profile.years_experience !== undefined && (
                <div className="flex items-center gap-2 text-sm text-[#6E5652] mb-4">
                  <Briefcase className="h-4 w-4 text-[#96817D]" />
                  <span>{profile.years_experience} years engineering experience</span>
                </div>
              )}

              {profile.skills && profile.skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((s) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center gap-1.5 rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-3.5 py-1 text-xs font-semibold text-[#9B3B25]"
                    >
                      <Award className="h-3.5 w-3.5" />
                      {s.name}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {profile.default_rate_minor !== null && profile.default_rate_minor !== undefined && (
              <div className="rounded-2xl bg-[#FFFDFB] border border-[#EADBCE] p-5 text-center sm:text-right min-w-[160px]">
                <span className="text-xs font-medium text-[#6E5652] uppercase tracking-wider block">Rate per session</span>
                <span className="text-2xl font-serif font-normal text-[#342523] block mt-1">
                  {formatCurrency(profile.default_rate_minor, profile.currency || "INR")}
                </span>
              </div>
            )}
          </div>

          {profile.bio && (
            <div className="border-t border-[#EADBCE] pt-6 mt-6">
              <h3 className="font-medium text-[#342523] text-sm uppercase tracking-wider mb-2">About the Interviewer</h3>
              <p className="text-sm text-[#6E5652] leading-relaxed whitespace-pre-line">{profile.bio}</p>
            </div>
          )}
        </div>

        {/* Slot Selection Section */}
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-sm">
          <SlotSelector
            interviewerId={profile.id}
            interviewerName={profile.full_name}
            slots={slots}
          />
        </div>
      </div>
    </div>
  );
}
