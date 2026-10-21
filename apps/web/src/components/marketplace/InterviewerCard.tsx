import type { InterviewerProfile } from "@interview-ready/api-types";
import { ArrowRight, Award, Briefcase, Calendar, ShieldCheck } from "lucide-react";
import Link from "next/link";
import React from "react";

import { formatCurrency } from "../../lib/api-client";

interface InterviewerCardProps {
  profile: InterviewerProfile;
}

export function sanitizeInterviewerBio(bio?: string | null, title?: string | null): string | null {
  if (!bio) return null;
  let cleaned = bio
    // Strip email addresses
    .replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, "")
    // Strip URLs and LinkedIn paths
    .replace(/https?:\/\/\S+|www\.\S+|linkedin\.com\/\S+/gi, "")
    // Strip phone numbers (e.g. +91-8949542711, +1 234 567 8900)
    .replace(/(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4}/g, "")
    // Strip leading ALL-CAPS full name headers (e.g., "SAGAR TIWARI ")
    .replace(/^[A-Z]{2,}(?:\s+[A-Z]{2,}){1,3}\s+/, "");

  // If the bio starts with the exact role title repeated from a resume header, trim the duplicate prefix
  if (title && cleaned.toLowerCase().startsWith(title.trim().toLowerCase())) {
    const afterTitle = cleaned.slice(title.trim().length).replace(/^[\s|•,-]+/, "");
    if (afterTitle.length > 20) {
      cleaned = afterTitle;
    }
  }

  cleaned = cleaned
    .replace(/\s*\|\s*/g, " • ")
    .replace(/(?:•\s*){2,}/g, "• ")
    .replace(/\s{2,}/g, " ")
    .replace(/^[•|\s,-]+|[•|\s,-]+$/g, "")
    .trim();

  return cleaned || null;
}

export function InterviewerCard({ profile }: InterviewerCardProps) {
  const shortId = profile.id.split("-")[0].slice(0, 4).toUpperCase();
  const roleTitle = (
    profile.title ||
    profile.full_name?.split("•")[0] ||
    "Technical Interviewer"
  ).trim();
  const cleanBio = sanitizeInterviewerBio(profile.bio, roleTitle);

  return (
    <div className="card-confidence card-confidence-interactive flex flex-col justify-between p-6 sm:p-7">
      <div>
        {/* Top Row: Anonymous Verified Badge + Session Price */}
        <div className="flex items-center justify-between gap-3 mb-4">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#E8F4EC] border border-[#B4DEC4] px-3 py-1 text-xs font-semibold text-[#2C6E49]">
            <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-[#2C6E49]" />
            <span>{profile.is_verified ? `Verified • #${shortId}` : `Mentor • #${shortId}`}</span>
          </span>

          {profile.default_rate_minor !== null && profile.default_rate_minor !== undefined && (
            <div className="text-right shrink-0">
              <span className="font-editorial font-bold text-[#9B3B25] text-lg sm:text-xl leading-none">
                {formatCurrency(profile.default_rate_minor, profile.currency || "INR")}
              </span>
              <span className="text-[11px] font-medium text-[#96817D] block mt-0.5">
                per session
              </span>
            </div>
          )}
        </div>

        {/* Full-Width Role Title */}
        <h3 className="font-editorial font-bold text-xl sm:text-[22px] text-[#342523] leading-snug mb-2">
          {roleTitle}
        </h3>

        {/* Experience & Anonymity Sub-bar */}
        <div className="flex flex-wrap items-center gap-y-1 gap-x-2.5 text-xs font-medium text-[#6E5652] mb-4 pb-4 border-b border-[#F2E6D8]">
          {profile.years_experience !== null && profile.years_experience !== undefined && (
            <span className="inline-flex items-center gap-1.5">
              <Briefcase className="h-3.5 w-3.5 text-[#9B3B25] shrink-0" />
              <span>{profile.years_experience} yrs experience</span>
            </span>
          )}
          <span className="text-[#D5C3B0]">•</span>
          <span className="text-[#6E5652]">Anonymous Vetted Leader</span>
        </div>

        {/* Sanitized Bio */}
        {cleanBio && (
          <p className="text-sm text-[#4E3936] line-clamp-3 mb-5 leading-relaxed font-sans">
            {cleanBio}
          </p>
        )}

        {/* Skills */}
        {profile.skills && profile.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-5">
            {profile.skills.map((s) => (
              <span
                key={s.id}
                className="inline-flex items-center gap-1 rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-2.5 py-0.5 text-xs font-medium text-[#342523]"
              >
                <Award className="h-3 w-3 text-[#9B3B25] shrink-0" />
                <span>{s.name}</span>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Footer CTA */}
      <div className="border-t border-[#EADBCE] pt-4 mt-auto">
        <Link
          href={`/interviewers/${profile.id}`}
          className="btn-pill-primary w-full justify-center gap-2 py-2.5 px-5 text-sm whitespace-nowrap"
        >
          <Calendar className="h-4 w-4 shrink-0" />
          <span>View Available Times</span>
          <ArrowRight className="h-4 w-4 shrink-0" />
        </Link>
      </div>
    </div>
  );
}
