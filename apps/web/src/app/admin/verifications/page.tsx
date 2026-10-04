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
        return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
      case "PENDING":
        return "bg-amber-50 text-amber-700 ring-amber-600/20";
      case "IN_REVIEW":
        return "bg-blue-50 text-blue-700 ring-blue-600/20";
      case "REJECTED":
        return "bg-rose-50 text-rose-700 ring-rose-600/20";
      default:
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Interviewer Verification Queue</h2>
          <p className="text-sm text-gray-500">
            Review professional credentials, approve qualified interviewers, or reject applications with feedback.
          </p>
        </div>
        <button
          onClick={() => fetchVerifications()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 border border-red-200 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm flex items-center gap-4">
        <Filter className="h-4 w-4 text-gray-400" />
        <span className="text-xs font-medium text-gray-600">Status Filter:</span>
        <div className="flex flex-wrap gap-2">
          {["ALL", "PENDING", "IN_REVIEW", "APPROVED", "REJECTED"].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setOffset(0);
              }}
              className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                statusFilter === st
                  ? "bg-purple-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Queue Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Applicant</th>
                <th className="px-6 py-3">Professional Title</th>
                <th className="px-6 py-3">Experience</th>
                <th className="px-6 py-3">Submitted</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Review Notes</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-400">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                    <p className="mt-2 text-xs">Loading verifications...</p>
                  </td>
                </tr>
              ) : verifications.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500">
                    No verifications in queue for this status.
                  </td>
                </tr>
              ) : (
                verifications.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50/50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="font-medium text-gray-900 flex items-center gap-2">
                          <span>{v.full_name}</span>
                          {v.linkedin_url && (
                            <a
                              href={v.linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700 hover:bg-blue-100 transition"
                              title="Verify LinkedIn Profile"
                            >
                              <span>LinkedIn</span>
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">{v.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-700">
                      {v.title || "Not specified"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-700">
                      {v.years_experience !== null && v.years_experience !== undefined
                        ? `${v.years_experience} years`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      {v.submitted_at ? new Date(v.submitted_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getStatusBadge(
                          v.status
                        )}`}
                      >
                        {v.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500 max-w-xs truncate">
                      {v.notes || "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <button
                        onClick={() => openReviewModal(v)}
                        className="rounded border border-purple-300 bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-700 hover:bg-purple-100 shadow-sm"
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
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3">
          <span className="text-xs text-gray-500">
            Showing <span className="font-semibold">{verifications.length > 0 ? offset + 1 : 0}</span> to{" "}
            <span className="font-semibold">{Math.min(offset + limit, total)}</span> of{" "}
            <span className="font-semibold">{total}</span> verifications
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || loading}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total || loading}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Review Modal Dialog */}
      {selectedVerif && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-purple-600">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">Review Interviewer Application</h3>
                <p className="text-xs text-gray-500">{selectedVerif.full_name} ({selectedVerif.email})</p>
                {selectedVerif.linkedin_url && (
                  <p className="text-xs mt-1">
                    <a
                      href={selectedVerif.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:underline"
                    >
                      <span>Open Applicant&apos;s LinkedIn Profile</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </p>
                )}
              </div>
            </div>

            {actionError && (
              <div className="mt-4 rounded-lg bg-red-50 p-3 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">Review Decision</label>
                <div className="grid grid-cols-2 gap-3">
                  <label
                    className={`flex items-center justify-center gap-2 rounded-lg border p-3 text-xs font-semibold cursor-pointer transition ${
                      reviewAction === "APPROVED"
                        ? "border-emerald-600 bg-emerald-50 text-emerald-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
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
                    className={`flex items-center justify-center gap-2 rounded-lg border p-3 text-xs font-semibold cursor-pointer transition ${
                      reviewAction === "REJECTED"
                        ? "border-rose-600 bg-rose-50 text-rose-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
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
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Feedback / Notes {reviewAction === "REJECTED" && <span className="text-red-500">* (required for rejection)</span>}
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Notes for applicant and internal audit trail..."
                  className="w-full rounded-lg border border-gray-300 p-2.5 text-xs focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  required={reviewAction === "REJECTED"}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedVerif(null)}
                  disabled={submitting}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`rounded-lg px-4 py-2 text-xs font-medium text-white shadow-sm disabled:opacity-50 ${
                    reviewAction === "APPROVED"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-rose-600 hover:bg-rose-700"
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
