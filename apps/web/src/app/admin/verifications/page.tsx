"use client";

import type { AdminInterviewerVerificationResponse, AdminVerificationListResponse } from "@interview-ready/api-types";
import { AlertCircle, CheckCircle, Clock, ExternalLink, Filter, RefreshCw, XCircle } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../../context/AuthContext";
import { ApiError } from "../../../lib/api-client";

export default function AdminVerificationsPage() {
  const { api } = useAuth();
  const [verifications, setVerifications] = useState<AdminInterviewerVerificationResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review Modal State
  const [selectedVerif, setSelectedVerif] = useState<AdminInterviewerVerificationResponse | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [reviewNotes, setReviewNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchVerifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };
      if (statusFilter !== "ALL") params.status = statusFilter;

      const data = await api.get<AdminVerificationListResponse>("/admin/verifications", { params });
      setVerifications(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load verification queue");
      }
    } finally {
      setLoading(false);
    }
  }, [api, limit, offset, statusFilter]);

  useEffect(() => {
    fetchVerifications();
  }, [fetchVerifications]);

  const openReviewModal = (v: AdminInterviewerVerificationResponse) => {
    setSelectedVerif(v);
    setReviewAction("APPROVED");
    setReviewNotes("");
    setActionError(null);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVerif) return;
    setSubmitting(true);
    setActionError(null);

    try {
      await api.patch(`/admin/interviewer-verifications/${selectedVerif.interviewer_id}`, {
        status: reviewAction,
        notes: reviewNotes.trim() || undefined,
      });
      setSelectedVerif(null);
      await fetchVerifications();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to submit verification review");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-[#E8F4EC] text-[#2C6E49] border border-[#C5E1D0]";
      case "PENDING":
        return "bg-[#FEF3E2] text-[#A65E00] border border-[#FADBB0]";
      case "IN_REVIEW":
        return "bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4]";
      case "REJECTED":
        return "bg-[#FCEBEB] text-[#9E2A2B] border border-[#F5C2B8]";
      default:
        return "bg-[#FDF5EE] text-[#6E5652] border border-[#EADBCE]";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523]">Interviewer Verification Queue</h2>
          <p className="text-sm text-[#6E5652] mt-1">
            Review professional credentials, approve qualified interviewers, or reject applications with feedback.
          </p>
        </div>
        <button
          onClick={() => fetchVerifications()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] shadow-sm transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-[#6E5652] ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-2xl bg-[#FCEBEB] p-4 border border-red-200 text-sm text-[#9E2A2B] flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="rounded-[24px] border border-[#EADBCE] bg-white p-4 shadow-sm flex items-center gap-4">
        <Filter className="h-4 w-4 text-[#96817D]" />
        <span className="text-xs font-semibold uppercase tracking-wider text-[#6E5652]">Status Filter:</span>
        <div className="flex flex-wrap gap-2">
          {["ALL", "PENDING", "IN_REVIEW", "APPROVED", "REJECTED"].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setOffset(0);
              }}
              className={`rounded-full px-3.5 py-1 text-xs font-medium transition ${
                statusFilter === st
                  ? "bg-[#9B3B25] text-white shadow-sm"
                  : "bg-[#FDF5EE] text-[#6E5652] hover:bg-[#F8DDC9]"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Queue Table */}
      <div className="overflow-hidden rounded-[24px] border border-[#EADBCE] bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#EADBCE] text-left text-sm">
            <thead className="bg-[#FFFDFB] text-xs font-semibold text-[#6E5652] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Applicant</th>
                <th className="px-6 py-3.5">Professional Title</th>
                <th className="px-6 py-3.5">Experience</th>
                <th className="px-6 py-3.5">Submitted</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Review Notes</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EADBCE] bg-white">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#6E5652]">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[#9B3B25] border-t-transparent" />
                    <p className="mt-2 text-xs">Loading verifications...</p>
                  </td>
                </tr>
              ) : verifications.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#6E5652]">
                    No verifications in queue for this status.
                  </td>
                </tr>
              ) : (
                verifications.map((v) => (
                  <tr key={v.id} className="hover:bg-[#FFF8F0]/60 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="font-medium text-[#342523] flex items-center gap-2">
                          <span>{v.full_name}</span>
                          {v.linkedin_url && (
                            <a
                              href={v.linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-2 py-0.5 text-[10px] font-semibold text-[#9B3B25] hover:bg-[#F8DDC9] transition"
                              title="Verify LinkedIn Profile"
                            >
                              <span>LinkedIn</span>
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          )}
                        </div>
                        <div className="text-xs text-[#6E5652]">{v.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-[#342523]">
                      {v.title || "Not specified"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-[#342523]">
                      {v.years_experience !== null && v.years_experience !== undefined
                        ? `${v.years_experience} years`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-[#6E5652]">
                      {v.submitted_at ? new Date(v.submitted_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getStatusBadge(
                          v.status
                        )}`}
                      >
                        {v.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-[#6E5652] max-w-xs truncate">
                      {v.notes || "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <button
                        onClick={() => openReviewModal(v)}
                        className="rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-3.5 py-1 text-xs font-semibold text-[#9B3B25] hover:bg-[#F8DDC9] shadow-sm transition"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between border-t border-[#EADBCE] px-6 py-3.5 bg-[#FFFDFB]">
          <span className="text-xs text-[#6E5652]">
            Showing <span className="font-semibold text-[#342523]">{verifications.length > 0 ? offset + 1 : 0}</span> to{" "}
            <span className="font-semibold text-[#342523]">{Math.min(offset + limit, total)}</span> of{" "}
            <span className="font-semibold text-[#342523]">{total}</span> verifications
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || loading}
              className="rounded-full border border-[#EADBCE] bg-white px-3.5 py-1 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total || loading}
              className="rounded-full border border-[#EADBCE] bg-white px-3.5 py-1 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Review Modal Dialog */}
      {selectedVerif && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-[24px] bg-white p-6 sm:p-8 shadow-xl border border-[#EADBCE]">
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#FEF3E2] text-[#A65E00]">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-serif text-lg font-normal text-[#342523]">Review Interviewer Application</h3>
                <p className="text-xs text-[#6E5652]">{selectedVerif.full_name} ({selectedVerif.email})</p>
                {selectedVerif.linkedin_url && (
                  <p className="text-xs mt-1">
                    <a
                      href={selectedVerif.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-medium text-[#9B3B25] hover:underline"
                    >
                      <span>Open Applicant&apos;s LinkedIn Profile</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </p>
                )}
              </div>
            </div>

            {actionError && (
              <div className="mt-4 rounded-2xl bg-[#FCEBEB] p-3 border border-red-200 text-xs text-[#9E2A2B] flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-2">Review Decision</label>
                <div className="grid grid-cols-2 gap-3">
                  <label
                    className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-xs font-semibold cursor-pointer transition ${
                      reviewAction === "APPROVED"
                        ? "border-[#2C6E49] bg-[#E8F4EC] text-[#2C6E49]"
                        : "border-[#EADBCE] bg-[#FFFDFB] text-[#342523] hover:bg-white"
                    }`}
                  >
                    <input
                      type="radio"
                      name="decision"
                      value="APPROVED"
                      checked={reviewAction === "APPROVED"}
                      onChange={() => setReviewAction("APPROVED")}
                      className="hidden"
                    />
                    <CheckCircle className="h-4 w-4" />
                    Approve Interviewer
                  </label>

                  <label
                    className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-xs font-semibold cursor-pointer transition ${
                      reviewAction === "REJECTED"
                        ? "border-[#9E2A2B] bg-[#FCEBEB] text-[#9E2A2B]"
                        : "border-[#EADBCE] bg-[#FFFDFB] text-[#342523] hover:bg-white"
                    }`}
                  >
                    <input
                      type="radio"
                      name="decision"
                      value="REJECTED"
                      checked={reviewAction === "REJECTED"}
                      onChange={() => setReviewAction("REJECTED")}
                      className="hidden"
                    />
                    <XCircle className="h-4 w-4" />
                    Reject Application
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                  Feedback / Notes {reviewAction === "REJECTED" && <span className="text-[#9E2A2B]">* (required for rejection)</span>}
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Notes for applicant and internal audit trail..."
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] p-3 text-xs text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  required={reviewAction === "REJECTED"}
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setSelectedVerif(null)}
                  disabled={submitting}
                  className="rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`rounded-full px-5 py-2 text-xs font-medium text-white shadow-sm transition disabled:opacity-50 ${
                    reviewAction === "APPROVED"
                      ? "bg-[#2C6E49] hover:bg-[#215236]"
                      : "bg-[#9E2A2B] hover:bg-[#802223]"
                  }`}
                >
                  {submitting ? "Processing..." : `Confirm ${reviewAction === "APPROVED" ? "Approval" : "Rejection"}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
