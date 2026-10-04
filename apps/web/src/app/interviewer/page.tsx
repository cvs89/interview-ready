"use client";

import type {
  AvailabilitySlot,
  Booking,
  InterviewerProfile,
  ParsedProfileDocumentResponse,
  Skill,
} from "@interview-ready/api-types";
import {
  AlertCircle,
  Briefcase,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Tag,
  Trash2,
  Upload,
  UserCheck,
  Video,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/api-client";

type TabType = "profile" | "skills" | "slots" | "bookings";

export default function InterviewerPortalPage() {
  const router = useRouter();
  const { user, api, getIdToken, loading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<TabType>("profile");
  const [profile, setProfile] = useState<InterviewerProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Setup / Edit Profile Form State
  const [title, setTitle] = useState("");
  const [bio, setBio] = useState("");
  const [yearsExperience, setYearsExperience] = useState<number>(5);
  const [rateMajor, setRateMajor] = useState<number>(5000);
  const [currency, setCurrency] = useState("INR");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Document Auto-fill State
  const [parsingDocument, setParsingDocument] = useState(false);
  const [suggestedSkills, setSuggestedSkills] = useState<string[]>([]);

  // Skills State
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [skillYears, setSkillYears] = useState(3);
  const [addingSkill, setAddingSkill] = useState(false);

  // Slots State
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotStartTime, setSlotStartTime] = useState("");
  const [slotEndTime, setSlotEndTime] = useState("");
  const [slotPriceMajor, setSlotPriceMajor] = useState<number>(5000);
  const [slotCurrency, setSlotCurrency] = useState("INR");
  const [creatingSlot, setCreatingSlot] = useState(false);

  // Bookings State
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loadingBookings, setLoadingBookings] = useState(false);

  // Load Profile
  const loadProfile = useCallback(async () => {
    setLoadingProfile(true);
    setProfileError(null);
    try {
      const data = await api.get<InterviewerProfile>("/interviewers/me/profile");
      setProfile(data);
      setTitle(data.title || "");
      setBio(data.bio || "");
      setYearsExperience(data.years_experience ?? 5);
      if (data.linkedin_url) {
        setLinkedinUrl(data.linkedin_url);
      }
      if (data.default_rate_minor) {
        setRateMajor(Math.round(data.default_rate_minor / 100));
      }
      if (data.currency) {
        setCurrency(data.currency);
        setSlotCurrency(data.currency);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.code === "PROFILE_NOT_FOUND") {
        setProfile(null);
      } else {
        const eObj = err as { message?: string };
        setProfileError(eObj.message || "Failed to load interviewer profile.");
      }
    } finally {
      setLoadingProfile(false);
    }
  }, [api]);

  // Load Skills catalog
  const loadSkills = useCallback(async () => {
    try {
      const data = await api.get<Skill[]>("/skills");
      setAllSkills(data);
      if (data.length > 0 && !selectedSkillId) {
        setSelectedSkillId(data[0].id);
      }
    } catch {
      // non-fatal
    }
  }, [api, selectedSkillId]);

  // Load Slots
  const loadSlots = useCallback(async () => {
    setLoadingSlots(true);
    try {
      const data = await api.get<AvailabilitySlot[]>("/interviewers/me/slots");
      setSlots(data);
    } catch {
      // non-fatal
    } finally {
      setLoadingSlots(false);
    }
  }, [api]);

  // Load Bookings
  const loadBookings = useCallback(async () => {
    setLoadingBookings(true);
    try {
      const data = await api.get<Booking[]>("/api/v1/bookings/me");
      setBookings(data);
    } catch {
      // non-fatal
    } finally {
      setLoadingBookings(false);
    }
  }, [api]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/interviewer");
      return;
    }
    if (user) {
      loadProfile();
      loadSkills();
    }
  }, [authLoading, loadProfile, loadSkills, router, user]);

  useEffect(() => {
    if (profile) {
      if (activeTab === "slots") loadSlots();
      if (activeTab === "bookings") loadBookings();
    }
  }, [activeTab, loadBookings, loadSlots, profile]);

  // Handle Document Upload & Auto-fill
  const handleDocumentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setParsingDocument(true);
    setProfileError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = await getIdToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://interview-ready-api-153072465008.europe-west1.run.app";
      const res = await fetch(`${apiUrl}/interviewers/me/parse-document`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Could not extract data from document");
      }
      const data: ParsedProfileDocumentResponse = await res.json();
      if (data.title) setTitle(data.title);
      if (data.bio) setBio(data.bio);
      if (data.years_experience !== null && data.years_experience !== undefined) {
        setYearsExperience(data.years_experience);
      }
      if (data.suggested_rate_minor) {
        setRateMajor(Math.round(data.suggested_rate_minor / 100));
      }
      if (data.suggested_currency) {
        setCurrency(data.suggested_currency);
      }
      if (data.skills && data.skills.length > 0) {
        setSuggestedSkills(data.skills);
      }
      setActionSuccess("Extracted profile details successfully via AI! Review and confirm below.");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to parse document. You can fill in the details manually.");
    } finally {
      setParsingDocument(false);
      e.target.value = "";
    }
  };

  // Handle Create Profile
  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError(null);
    try {
      const created = await api.post<InterviewerProfile>("/interviewers/me/profile", {
        title,
        bio,
        years_experience: Number(yearsExperience),
        default_rate_minor: Number(rateMajor) * 100,
        currency,
        linkedin_url: linkedinUrl.trim() || undefined,
      });
      setProfile(created);
      setActionSuccess("Interviewer profile created and submitted for verification!");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to create profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle Update Profile
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError(null);
    try {
      const updated = await api.patch<InterviewerProfile>("/interviewers/me/profile", {
        title,
        bio,
        years_experience: Number(yearsExperience),
        default_rate_minor: Number(rateMajor) * 100,
        currency,
        linkedin_url: linkedinUrl.trim() || undefined,
      });
      setProfile(updated);
      setActionSuccess("Profile updated successfully!");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to update profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle Re-submit Verification
  const handleResubmitVerification = async () => {
    setSavingProfile(true);
    setProfileError(null);
    try {
      await api.post("/interviewers/me/verification");
      await loadProfile();
      setActionSuccess("Verification request re-submitted!");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to submit verification request.");
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle Add Skill
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSkillId) return;
    setAddingSkill(true);
    try {
      const updated = await api.post<InterviewerProfile>("/interviewers/me/skills", {
        skill_id: selectedSkillId,
        years_experience: Number(skillYears),
      });
      setProfile(updated);
      setActionSuccess("Skill added successfully!");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to add skill.");
    } finally {
      setAddingSkill(false);
    }
  };

  // Handle Remove Skill
  const handleRemoveSkill = async (skillId: string) => {
    try {
      await api.delete(`/interviewers/me/skills/${skillId}`);
      if (profile) {
        setProfile({
          ...profile,
          skills: profile.skills.filter((s) => s.id !== skillId),
        });
      }
      setActionSuccess("Skill removed.");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to remove skill.");
    }
  };

  // Handle Create Slot
  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slotStartTime || !slotEndTime) return;
    setCreatingSlot(true);
    setProfileError(null);
    try {
      const startIso = new Date(slotStartTime).toISOString();
      const endIso = new Date(slotEndTime).toISOString();

      await api.post("/interviewers/me/slots", {
        start_time: startIso,
        end_time: endIso,
        price_minor: Number(slotPriceMajor) * 100,
        currency: slotCurrency,
      });
      await loadSlots();
      setActionSuccess("Availability slot published to marketplace!");
      setSlotStartTime("");
      setSlotEndTime("");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to publish slot.");
    } finally {
      setCreatingSlot(false);
    }
  };

  // Handle Delete Slot
  const handleDeleteSlot = async (slotId: string) => {
    try {
      await api.delete(`/interviewers/me/slots/${slotId}`);
      setSlots((prev) => prev.filter((s) => s.id !== slotId));
      setActionSuccess("Slot removed.");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setProfileError(eObj.message || "Failed to delete slot.");
    }
  };

  if (authLoading || loadingProfile) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center bg-[#FFF8F0]">
        <Loader2 className="h-8 w-8 animate-spin text-[#9B3B25]" />
      </div>
    );
  }

  // View: Initial Profile Onboarding
  if (!profile) {
    return (
      <div className="min-h-screen bg-[#FFF8F0] py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-[24px] border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-sm">
            <div className="flex items-center gap-3.5 border-b border-[#EADBCE] pb-6 mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25]">
                <Briefcase className="h-6 w-6" />
              </div>
              <div>
                <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523]">Setup Your Interviewer Profile</h1>
                <p className="text-sm text-[#6E5652] mt-0.5">
                  Complete your details to apply for verified interviewer status.
                </p>
              </div>
            </div>

            {/* AI Auto-fill Banner */}
            <div className="mb-8 rounded-2xl border-2 border-dashed border-[#ECC2A4] bg-[#FDF5EE]/60 p-6 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] mb-2">
                <Sparkles className="h-5 w-5" />
              </div>
              <h3 className="font-medium text-[#342523] text-sm">Auto-fill from LinkedIn PDF or Resume</h3>
              <p className="text-xs text-[#6E5652] mt-1 max-w-md mx-auto">
                On LinkedIn: Go to your profile &rarr; click <strong>More</strong> &rarr; click <strong>Save to PDF</strong>. Upload it here to auto-populate your details in seconds.
              </p>
              <label className="mt-4 inline-flex items-center gap-2 rounded-full bg-[#9B3B25] px-6 py-2.5 text-xs font-semibold text-white shadow hover:bg-[#83321F] cursor-pointer transition">
                {parsingDocument ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                <span>{parsingDocument ? "Extracting with AI..." : "Upload LinkedIn PDF / Resume"}</span>
                <input
                  type="file"
                  accept=".pdf,.txt,.doc,.docx"
                  onChange={handleDocumentUpload}
                  disabled={parsingDocument}
                  className="hidden"
                />
              </label>
            </div>

            {actionSuccess && (
              <div className="mb-6 flex items-center gap-2 rounded-2xl border border-green-200 bg-[#E8F4EC] p-3.5 text-sm text-[#2C6E49]">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-[#2C6E49]" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {profileError && (
              <div className="mb-6 flex items-center gap-2 rounded-2xl border border-red-200 bg-[#FCEBEB] p-3.5 text-sm text-[#9E2A2B]">
                <AlertCircle className="h-4 w-4 shrink-0 text-[#9E2A2B]" />
                <span>{profileError}</span>
              </div>
            )}

            <form onSubmit={handleCreateProfile} className="space-y-6">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                  LinkedIn Profile URL
                </label>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/in/your-profile"
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                />
                <p className="text-[11px] text-[#96817D] mt-1">
                  Used by administrators to verify your employment and assign the Verified badge.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                  Professional Title / Headline
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Staff Software Engineer @ Google"
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                  Bio & Interviewing Background
                </label>
                <textarea
                  rows={4}
                  required
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Describe your engineering focus, past tech stacks, and how you mentor or interview candidates."
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                />
              </div>

              {suggestedSkills.length > 0 && (
                <div className="rounded-2xl border border-[#ECC2A4] bg-[#FDF5EE]/50 p-4">
                  <span className="text-xs font-semibold text-[#9B3B25]">Detected Skills from Profile:</span>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {suggestedSkills.map((sk) => (
                      <span key={sk} className="rounded-full bg-[#F8DDC9] px-3 py-0.5 text-xs font-medium text-[#9B3B25]">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Years of Experience
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={80}
                    required
                    value={yearsExperience}
                    onChange={(e) => setYearsExperience(Number(e.target.value))}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Default Rate (per hour)
                  </label>
                  <input
                    type="number"
                    min={0}
                    required
                    value={rateMajor}
                    onChange={(e) => setRateMajor(Number(e.target.value))}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  >
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-[#EADBCE] flex items-center justify-between">
                <Link href="/dashboard" className="text-sm font-medium text-[#6E5652] hover:text-[#342523]">
                  Cancel
                </Link>
                <button
                  type="submit"
                  disabled={savingProfile}
                  className="inline-flex items-center gap-2 rounded-full bg-[#9B3B25] px-6 py-3 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition disabled:opacity-50"
                >
                  {savingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserCheck className="h-4 w-4" />}
                  <span>Submit Profile & Request Verification</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // View: Main Interviewer Dashboard
  const isVerified = profile.is_verified;
  const isPending = profile.verification_status === "PENDING";
  const isRejected = profile.verification_status === "REJECTED";

  return (
    <div className="min-h-screen bg-[#FFF8F0] py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header Banner */}
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523]">{profile.full_name}</h1>
                {isVerified ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-[#C5E1D0] bg-[#E8F4EC] px-3 py-1 text-xs font-semibold text-[#2C6E49]">
                    <ShieldCheck className="h-3.5 w-3.5" /> Verified Interviewer
                  </span>
                ) : isPending ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-[#FADBB0] bg-[#FEF3E2] px-3 py-1 text-xs font-semibold text-[#A65E00]">
                    <Clock className="h-3.5 w-3.5" /> Verification Pending
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-[#F5C2B8] bg-[#FCEBEB] px-3 py-1 text-xs font-semibold text-[#9E2A2B]">
                    <ShieldAlert className="h-3.5 w-3.5" /> Verification Rejected
                  </span>
                )}
              </div>
              <p className="text-sm font-medium text-[#6E5652] mt-1">{profile.title}</p>
              <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-[#6E5652]">
                <span>
                  Rate: {profile.currency} {profile.default_rate_minor ? (profile.default_rate_minor / 100).toLocaleString() : "—"} / hr
                </span>
                <span>•</span>
                <span>{profile.years_experience} years experience</span>
                {profile.linkedin_url && (
                  <>
                    <span>•</span>
                    <a
                      href={profile.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-[#9B3B25] hover:underline"
                    >
                      <span>LinkedIn Profile</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              {isRejected && (
                <button
                  onClick={handleResubmitVerification}
                  disabled={savingProfile}
                  className="inline-flex items-center gap-1.5 rounded-full bg-[#A65E00] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#8E4F00] transition"
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Resubmit Verification
                </button>
              )}
              <Link
                href={`/interviewers/${profile.id}`}
                className="inline-flex items-center gap-1.5 rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] shadow-sm hover:bg-[#FDF5EE] transition"
              >
                Public Profile View
              </Link>
            </div>
          </div>

          {/* Verification Status Notice */}
          {isPending && (
            <div className="mt-6 rounded-2xl border border-[#FADBB0] bg-[#FEF3E2] p-4 text-xs sm:text-sm text-[#A65E00] flex items-start gap-3">
              <Clock className="h-5 w-5 text-[#A65E00] shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Your interviewer profile is under review.</p>
                <p className="text-[#8E4F00] mt-0.5">
                  Our operations team verifies all interviewers to guarantee candidate quality. Once approved, you can publish availability slots to the marketplace.
                </p>
              </div>
            </div>
          )}
        </div>

        {actionSuccess && (
          <div className="mb-6 flex items-center justify-between rounded-2xl border border-green-200 bg-[#E8F4EC] p-3.5 text-sm text-[#2C6E49]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#2C6E49] shrink-0" />
              <span>{actionSuccess}</span>
            </div>
            <button onClick={() => setActionSuccess(null)} className="text-xs font-semibold text-[#2C6E49] hover:underline">
              Dismiss
            </button>
          </div>
        )}

        {profileError && (
          <div className="mb-6 flex items-center gap-2 rounded-2xl border border-red-200 bg-[#FCEBEB] p-3.5 text-sm text-[#9E2A2B]">
            <AlertCircle className="h-4 w-4 text-[#9E2A2B] shrink-0" />
            <span>{profileError}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-[#EADBCE] mb-8">
          <nav className="flex space-x-8 overflow-x-auto">
            <button
              onClick={() => setActiveTab("profile")}
              className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-medium transition whitespace-nowrap ${
                activeTab === "profile"
                  ? "border-[#9B3B25] text-[#9B3B25]"
                  : "border-transparent text-[#6E5652] hover:border-[#EADBCE] hover:text-[#342523]"
              }`}
            >
              <Briefcase className="h-4 w-4" /> Profile & Pricing
            </button>

            <button
              onClick={() => setActiveTab("skills")}
              className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-medium transition whitespace-nowrap ${
                activeTab === "skills"
                  ? "border-[#9B3B25] text-[#9B3B25]"
                  : "border-transparent text-[#6E5652] hover:border-[#EADBCE] hover:text-[#342523]"
              }`}
            >
              <Tag className="h-4 w-4" /> Technical Skills ({profile.skills.length})
            </button>

            <button
              onClick={() => setActiveTab("slots")}
              className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-medium transition whitespace-nowrap ${
                activeTab === "slots"
                  ? "border-[#9B3B25] text-[#9B3B25]"
                  : "border-transparent text-[#6E5652] hover:border-[#EADBCE] hover:text-[#342523]"
              }`}
            >
              <Calendar className="h-4 w-4" /> Availability Slots
            </button>

            <button
              onClick={() => setActiveTab("bookings")}
              className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-medium transition whitespace-nowrap ${
                activeTab === "bookings"
                  ? "border-[#9B3B25] text-[#9B3B25]"
                  : "border-transparent text-[#6E5652] hover:border-[#EADBCE] hover:text-[#342523]"
              }`}
            >
              <Video className="h-4 w-4" /> Scheduled Sessions
            </button>
          </nav>
        </div>

        {/* Tab 1: Profile & Pricing */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            {/* Quick Auto-update from Document */}
            <div className="rounded-[20px] border border-[#ECC2A4] bg-[#FDF5EE]/50 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] shrink-0">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-[#342523]">Auto-update from LinkedIn PDF or Resume</h3>
                  <p className="text-xs text-[#6E5652]">
                    Upload an updated LinkedIn export or CV to refresh your title, experience, and bio automatically.
                  </p>
                </div>
              </div>
              <label className="shrink-0 inline-flex items-center gap-2 rounded-full bg-[#9B3B25] px-5 py-2.5 text-xs font-semibold text-white shadow hover:bg-[#83321F] cursor-pointer transition">
                {parsingDocument ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                <span>{parsingDocument ? "Extracting..." : "Upload Document"}</span>
                <input
                  type="file"
                  accept=".pdf,.txt,.doc,.docx"
                  onChange={handleDocumentUpload}
                  disabled={parsingDocument}
                  className="hidden"
                />
              </label>
            </div>

            <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
              <h2 className="font-serif text-xl font-normal text-[#342523] mb-6">Edit Profile & Default Pricing</h2>
              <form onSubmit={handleUpdateProfile} className="space-y-6">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    LinkedIn Profile URL
                  </label>
                  <input
                    type="url"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    placeholder="https://www.linkedin.com/in/your-profile"
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Headline / Title
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Bio
                  </label>
                  <textarea
                    rows={5}
                    required
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                      Years of Experience
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={80}
                      required
                      value={yearsExperience}
                      onChange={(e) => setYearsExperience(Number(e.target.value))}
                      className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                      Hourly Rate
                    </label>
                    <input
                      type="number"
                      min={0}
                      required
                      value={rateMajor}
                      onChange={(e) => setRateMajor(Number(e.target.value))}
                      className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                      Currency
                    </label>
                    <select
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                    >
                      <option value="INR">INR (₹)</option>
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t border-[#EADBCE] flex justify-end">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="inline-flex items-center gap-2 rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition disabled:opacity-50"
                  >
                    {savingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserCheck className="h-4 w-4" />}
                    <span>Save Profile Changes</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Tab 2: Technical Skills */}
        {activeTab === "skills" && (
          <div className="space-y-8">
            <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
              <h2 className="font-serif text-xl font-normal text-[#342523] mb-4">Add Specialized Skill</h2>
              <form onSubmit={handleAddSkill} className="flex flex-col sm:flex-row sm:items-end gap-4">
                <div className="flex-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Skill / Domain
                  </label>
                  <select
                    value={selectedSkillId}
                    onChange={(e) => setSelectedSkillId(e.target.value)}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  >
                    {allSkills.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="w-full sm:w-48">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Years Experience
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={skillYears}
                    onChange={(e) => setSkillYears(Number(e.target.value))}
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <button
                  type="submit"
                  disabled={addingSkill || !selectedSkillId}
                  className="inline-flex items-center justify-center gap-1.5 rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] transition disabled:opacity-50"
                >
                  {addingSkill ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  <span>Add Skill</span>
                </button>
              </form>
            </div>

            <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
              <h3 className="font-serif text-xl font-normal text-[#342523] mb-4">Your Added Skills</h3>
              {profile.skills.length === 0 ? (
                <p className="text-sm text-[#6E5652]">No skills added yet. Add your core competencies above.</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {profile.skills.map((skill) => (
                    <div
                      key={skill.id}
                      className="flex items-center justify-between rounded-2xl border border-[#EADBCE] bg-[#FFFDFB] p-4"
                    >
                      <div>
                        <h4 className="font-medium text-[#342523] text-sm">{skill.name}</h4>
                        <p className="text-xs text-[#6E5652] mt-0.5">{skill.years_experience} years experience</p>
                      </div>
                      <button
                        onClick={() => handleRemoveSkill(skill.id)}
                        className="text-[#96817D] hover:text-[#9E2A2B] transition p-1"
                        title="Remove skill"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Availability & Slots */}
        {activeTab === "slots" && (
          <div className="space-y-8">
            {!isVerified ? (
              <div className="rounded-[24px] border border-[#FADBB0] bg-[#FEF3E2] p-8 text-center">
                <Clock className="mx-auto h-12 w-12 text-[#A65E00] mb-3" />
                <h3 className="font-serif text-xl font-normal text-[#342523]">Verification Required</h3>
                <p className="text-sm text-[#8E4F00] max-w-md mx-auto mt-1">
                  Only approved interviewers can publish availability slots to the marketplace. Your profile is currently pending review by our operations team.
                </p>
              </div>
            ) : (
              <>
                {/* Add Slot Form */}
                <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
                  <h2 className="font-serif text-xl font-normal text-[#342523] mb-4">Publish New Availability Slot</h2>
                  <form onSubmit={handleCreateSlot} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                          Start Time
                        </label>
                        <input
                          type="datetime-local"
                          required
                          value={slotStartTime}
                          onChange={(e) => setSlotStartTime(e.target.value)}
                          className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                          End Time
                        </label>
                        <input
                          type="datetime-local"
                          required
                          value={slotEndTime}
                          onChange={(e) => setSlotEndTime(e.target.value)}
                          className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                          Slot Price
                        </label>
                        <input
                          type="number"
                          min={0}
                          required
                          value={slotPriceMajor}
                          onChange={(e) => setSlotPriceMajor(Number(e.target.value))}
                          className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                          Currency
                        </label>
                        <select
                          value={slotCurrency}
                          onChange={(e) => setSlotCurrency(e.target.value)}
                          className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                        >
                          <option value="INR">INR (₹)</option>
                          <option value="USD">USD ($)</option>
                          <option value="EUR">EUR (€)</option>
                          <option value="GBP">GBP (£)</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        disabled={creatingSlot}
                        className="inline-flex items-center gap-2 rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition disabled:opacity-50"
                      >
                        {creatingSlot ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                        <span>Publish Slot</span>
                      </button>
                    </div>
                  </form>
                </div>

                {/* Slot List */}
                <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-serif text-xl font-normal text-[#342523]">Your Slots</h3>
                    <button
                      onClick={loadSlots}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-[#9B3B25] hover:underline"
                    >
                      <RefreshCw className="h-3.5 w-3.5" /> Refresh
                    </button>
                  </div>

                  {loadingSlots ? (
                    <div className="py-8 text-center text-sm text-[#6E5652]">Loading slots...</div>
                  ) : slots.length === 0 ? (
                    <p className="text-sm text-[#6E5652]">No availability slots published yet.</p>
                  ) : (
                    <div className="divide-y divide-[#EADBCE]">
                      {slots.map((slot) => {
                        const start = new Date(slot.start_time);
                        const end = new Date(slot.end_time);
                        const isAvailable = slot.status === "AVAILABLE";

                        return (
                          <div key={slot.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-[#342523] text-sm">
                                  {start.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
                                </span>
                                <span className="text-xs text-[#6E5652]">
                                  {start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} – {end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                </span>
                                <span
                                  className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                                    isAvailable
                                      ? "bg-[#E8F4EC] text-[#2C6E49] border border-[#C5E1D0]"
                                      : "bg-[#FDF5EE] text-[#6E5652]"
                                  }`}
                                >
                                  {slot.status}
                                </span>
                              </div>
                              <p className="text-xs text-[#6E5652] mt-1">
                                Price: {slot.currency} {(slot.price_minor / 100).toLocaleString()}
                              </p>
                            </div>

                            {isAvailable && (
                              <button
                                onClick={() => handleDeleteSlot(slot.id)}
                                className="text-xs text-[#9E2A2B] hover:text-[#802223] font-medium inline-flex items-center gap-1"
                              >
                                <Trash2 className="h-3.5 w-3.5" /> Cancel Slot
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 4: Scheduled Sessions */}
        {activeTab === "bookings" && (
          <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-serif text-xl font-normal text-[#342523]">Your Scheduled Interview Sessions</h3>
              <button
                onClick={loadBookings}
                className="inline-flex items-center gap-1 text-xs font-semibold text-[#9B3B25] hover:underline"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </button>
            </div>

            {loadingBookings ? (
              <div className="py-8 text-center text-sm text-[#6E5652]">Loading sessions...</div>
            ) : bookings.length === 0 ? (
              <p className="text-sm text-[#6E5652]">No upcoming mock interview sessions scheduled.</p>
            ) : (
              <div className="divide-y divide-[#EADBCE]">
                {bookings.map((b) => (
                  <div key={b.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[#342523] text-sm">
                          Booking #{b.id.slice(0, 8)}
                        </span>
                        <span
                          className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                            b.status === "CONFIRMED"
                              ? "bg-[#E8F4EC] text-[#2C6E49] border border-[#C5E1D0]"
                              : b.status === "IN_PROGRESS"
                              ? "bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4]"
                              : "bg-[#FDF5EE] text-[#6E5652]"
                          }`}
                        >
                          {b.status}
                        </span>
                      </div>
                      <p className="text-xs text-[#6E5652] mt-1">
                        Fee: {b.currency} {(b.price_minor / 100).toLocaleString()} • Created: {new Date(b.created_at).toLocaleDateString()}
                      </p>
                    </div>

                    <Link
                      href={`/bookings/${b.id}/confirmation`}
                      className="inline-flex items-center gap-1.5 rounded-full bg-[#9B3B25] px-4 py-2 text-xs font-medium text-white shadow hover:bg-[#83321F] transition"
                    >
                      <Video className="h-3.5 w-3.5" /> Session Details & Room
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
