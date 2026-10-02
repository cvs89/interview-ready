import type { InterviewerProfile } from "@interview-ready/api-types";
import { Award, Briefcase, Calendar, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import React from "react";

import { formatCurrency } from "../../lib/api-client";

interface InterviewerCardProps {
  profile: InterviewerProfile;
}

export function InterviewerCard({ profile }: InterviewerCardProps) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition">
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="font-bold text-lg text-gray-900">{profile.full_name}</h3>
              {profile.is_verified && (
                <span title="Verified Interviewer">
                  <CheckCircle2 className="h-4 w-4 text-blue-600 fill-blue-50" />
                </span>
              )}
            </div>
            <p className="text-sm font-medium text-gray-600">{profile.title || "Technical Interviewer"}</p>
          </div>
          {profile.default_rate_minor !== null && profile.default_rate_minor !== undefined && (
            <div className="text-right">
              <span className="text-xs text-gray-500 block">Rate from</span>
              <span className="font-bold text-gray-900 text-base">
                {formatCurrency(profile.default_rate_minor, profile.currency || "INR")}
              </span>
            </div>
          )}
        </div>

        {profile.years_experience !== null && profile.years_experience !== undefined && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
            <Briefcase className="h-3.5 w-3.5 text-gray-400" />
            <span>{profile.years_experience} years industry experience</span>
          </div>
        )}

        {profile.bio && (
          <p className="text-sm text-gray-600 line-clamp-3 mb-4 leading-relaxed">
            {profile.bio}
          </p>
        )}

        {profile.skills && profile.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-5">
            {profile.skills.map((s) => (
              <span
                key={s.id}
                className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700"
              >
                <Award className="h-3 w-3" />
                {s.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-100 pt-4 mt-auto">
        <Link
          href={`/interviewers/${profile.id}`}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition"
        >
          <Calendar className="h-4 w-4" />
          View Availability & Book
        </Link>
      </div>
    </div>
  );
}
