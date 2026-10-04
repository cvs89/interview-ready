import type { InterviewerProfile } from "@interview-ready/api-types";
import { Award, Briefcase, Calendar, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import React from "react";

import { formatCurrency } from "../../lib/api-client";

interface InterviewerCardProps {
  profile: InterviewerProfile;
}

export function InterviewerCard({ profile }: InterviewerCardProps) {
  const initials = profile.full_name
    ? profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "IR";

  return (
    <div className="card-confidence card-confidence-interactive flex flex-col justify-between p-6 sm:p-7">
      <div>
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] font-editorial font-bold text-lg border border-[#ECC2A4]">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="font-editorial font-bold text-lg text-[#342523]">
                  {profile.full_name}
                </h3>
              </div>
              <p className="text-xs sm:text-sm font-medium text-[#6E5652]">
                {profile.title || "Technical Interviewer"}
              </p>
            </div>
          </div>

          {profile.default_rate_minor !== null && profile.default_rate_minor !== undefined && (
            <div className="text-right shrink-0">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[#96817D] block">
                Session
              </span>
              <span className="font-editorial font-bold text-[#9B3B25] text-lg sm:text-xl">
                {formatCurrency(profile.default_rate_minor, profile.currency || "INR")}
              </span>
            </div>
          )}
        </div>

        {profile.is_verified && (
          <div className="mb-3">
            <span className="badge-confidence-approved">
              <CheckCircle2 className="h-3.5 w-3.5 text-[#9B3B25]" />
              Platform-approved interviewer
            </span>
          </div>
        )}

        {profile.years_experience !== null && profile.years_experience !== undefined && (
          <div className="flex items-center gap-1.5 text-xs text-[#6E5652] mb-3">
            <Briefcase className="h-3.5 w-3.5 text-[#9B3B25]" />
            <span>{profile.years_experience} years engineering experience</span>
          </div>
        )}

        {profile.bio && (
          <p className="text-sm text-[#4E3936] line-clamp-3 mb-4 leading-relaxed font-sans">
            {profile.bio}
          </p>
        )}

        {profile.skills && profile.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-5">
            {profile.skills.map((s) => (
              <span
                key={s.id}
                className="inline-flex items-center gap-1 rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-2.5 py-0.5 text-xs font-medium text-[#342523]"
              >
                <Award className="h-3 w-3 text-[#9B3B25]" />
                {s.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-[#EADBCE] pt-4 mt-auto">
        <Link
          href={`/interviewers/${profile.id}`}
          className="btn-pill-primary w-full gap-2 py-2.5 text-sm"
        >
          <Calendar className="h-4 w-4" />
          View Available Times →
        </Link>
      </div>
    </div>
  );
}
