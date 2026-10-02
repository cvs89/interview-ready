"use client";

import type { AdminBookingItemResponse, AdminBookingListResponse } from "@interview-ready/api-types";
import { AlertCircle, Calendar, Eye, Filter, RefreshCw, UserCheck, Video } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../../context/AuthContext";
import { ApiError, formatCurrency, formatUtcToLocal } from "../../../lib/api-client";

export default function AdminBookingsPage() {
  const { api } = useAuth();
  const [bookings, setBookings] = useState<AdminBookingItemResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal State
  const [selectedBooking, setSelectedBooking] = useState<AdminBookingItemResponse | null>(null);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };
      if (statusFilter !== "ALL") params.status = statusFilter;

      const data = await api.get<AdminBookingListResponse>("/admin/bookings", { params });
      setBookings(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to fetch bookings");
      }
    } finally {
      setLoading(false);
    }
  }, [api, limit, offset, statusFilter]);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "CONFIRMED":
        return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
      case "PENDING_PAYMENT":
        return "bg-amber-50 text-amber-700 ring-amber-600/20";
      case "COMPLETED":
        return "bg-blue-50 text-blue-700 ring-blue-600/20";
      case "CANCELLED":
        return "bg-rose-50 text-rose-700 ring-rose-600/20";
      case "EXPIRED":
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
      default:
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
    }
  };

  const getPaymentBadge = (status: string | null | undefined) => {
    if (!status) return "bg-gray-50 text-gray-500 ring-gray-400/20";
    switch (status) {
      case "PAID":
        return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
      case "PENDING":
        return "bg-amber-50 text-amber-700 ring-amber-600/20";
      case "REFUNDED":
        return "bg-purple-50 text-purple-700 ring-purple-600/20";
      default:
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Bookings Inspection</h2>
          <p className="text-sm text-gray-500">
            Audit interview sessions, participant pairing, schedule timing, and payment states.
          </p>
        </div>
        <button
          onClick={() => fetchBookings()}
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
        <span className="text-xs font-medium text-gray-600">Booking Status:</span>
        <div className="flex flex-wrap gap-2">
          {["ALL", "CONFIRMED", "PENDING_PAYMENT", "COMPLETED", "CANCELLED", "EXPIRED"].map((st) => (
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
              {st.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Bookings Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Booking ID</th>
                <th className="px-6 py-3">Candidate</th>
                <th className="px-6 py-3">Interviewer</th>
                <th className="px-6 py-3">Scheduled Time</th>
                <th className="px-6 py-3">Amount</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Payment</th>
                <th className="px-6 py-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-400">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                    <p className="mt-2 text-xs">Loading bookings...</p>
                  </td>
                </tr>
              ) : bookings.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500">
                    No bookings found for this filter.
                  </td>
                </tr>
              ) : (
                bookings.map((b) => {
                  const { dateStr, timeStr } = formatUtcToLocal(b.slot_start_time);
                  return (
                    <tr key={b.id} className="hover:bg-gray-50/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                        {b.id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="font-medium text-gray-900">{b.candidate_name}</div>
                          <div className="text-xs text-gray-500">{b.candidate_email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="font-medium text-gray-900">{b.interviewer_name}</div>
                          <div className="text-xs text-gray-500">{b.interviewer_email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-700">
                        <div>{dateStr}</div>
                        <div className="text-gray-400">{timeStr}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-semibold text-gray-900">
                        {formatCurrency(b.price_minor, b.currency)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getStatusBadge(
                            b.status
                          )}`}
                        >
                          {b.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getPaymentBadge(
                            b.payment_status
                          )}`}
                        >
                          {b.payment_status || "UNPAID"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                        <button
                          onClick={() => setSelectedBooking(b)}
                          className="rounded border border-gray-300 bg-white p-1.5 text-gray-700 hover:bg-gray-50 shadow-sm"
                          title="View booking details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3">
          <span className="text-xs text-gray-500">
            Showing <span className="font-semibold">{bookings.length > 0 ? offset + 1 : 0}</span> to{" "}
            <span className="font-semibold">{Math.min(offset + limit, total)}</span> of{" "}
            <span className="font-semibold">{total}</span> bookings
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

      {/* Booking Inspection Detail Modal */}
      {selectedBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <Video className="h-5 w-5 text-purple-600" />
                <h3 className="text-base font-semibold text-gray-900">Booking Inspection</h3>
              </div>
              <span className="font-mono text-xs text-gray-400">{selectedBooking.id}</span>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-3 border border-gray-100">
                <div>
                  <span className="text-gray-500">Booking Status:</span>
                  <div className="mt-1 font-semibold text-gray-900">{selectedBooking.status}</div>
                </div>
                <div>
                  <span className="text-gray-500">Payment Status:</span>
                  <div className="mt-1 font-semibold text-gray-900">{selectedBooking.payment_status || "UNPAID"}</div>
                </div>
                <div>
                  <span className="text-gray-500">Amount:</span>
                  <div className="mt-1 font-semibold text-gray-900">
                    {formatCurrency(selectedBooking.price_minor, selectedBooking.currency)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Slot ID:</span>
                  <div className="mt-1 font-mono text-[10px] text-gray-700 truncate">{selectedBooking.slot_id}</div>
                </div>
              </div>

              <div className="border-t border-gray-100 pt-3">
                <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                  <UserCheck className="h-4 w-4 text-blue-600" /> Participants
                </h4>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded border border-gray-200 p-2.5">
                    <span className="text-gray-400 uppercase text-[10px]">Candidate</span>
                    <div className="font-semibold text-gray-900">{selectedBooking.candidate_name}</div>
                    <div className="text-gray-500 text-[11px]">{selectedBooking.candidate_email}</div>
                  </div>
                  <div className="rounded border border-gray-200 p-2.5">
                    <span className="text-gray-400 uppercase text-[10px]">Interviewer</span>
                    <div className="font-semibold text-gray-900">{selectedBooking.interviewer_name}</div>
                    <div className="text-gray-500 text-[11px]">{selectedBooking.interviewer_email}</div>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-100 pt-3">
                <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-purple-600" /> Slot Timeline (UTC & Local)
                </h4>
                <div className="rounded bg-gray-50 p-2.5 space-y-1 text-gray-600 text-[11px]">
                  <div><span className="font-medium">Start:</span> {selectedBooking.slot_start_time}</div>
                  <div><span className="font-medium">End:</span> {selectedBooking.slot_end_time}</div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedBooking(null)}
                className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-medium text-white hover:bg-gray-800"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
