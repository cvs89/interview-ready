"use client";

import type { Booking } from "@interview-ready/api-types";
import { AlertCircle, Calendar, Loader2, RefreshCw, UserCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";

import { BookingList } from "../../components/dashboard/BookingList";
import { useAuth } from "../../context/AuthContext";

export default function DashboardPage() {
  const router = useRouter();
  const { user, apiUser, api, loading: authLoading } = useAuth();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBookings = useCallback(
    async (isManualRefresh = false) => {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        const data = await api.get<Booking[]>("/api/v1/bookings/me");
        setBookings(data);
      } catch (err: unknown) {
        const eObj = err as { message?: string };
        setError(eObj.message || "Failed to load bookings.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [api]
  );

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/sign-in?redirect=/dashboard");
      return;
    }

    if (user) {
      fetchBookings();
    }
  }, [authLoading, fetchBookings, router, user]);

  if (authLoading || loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const isInterviewer = apiUser?.role === "INTERVIEWER";
  const displayName = apiUser?.full_name || user?.displayName || user?.email || "User";

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 pb-6 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Welcome, {displayName}!
            </h1>
            {isInterviewer && (
              <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
                <UserCheck className="h-3 w-3" /> Interviewer
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {isInterviewer
              ? "View and join your scheduled mock interview sessions as candidate or interviewer."
              : "Track your scheduled mock interview sessions and launch into the live interview room."}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchBookings(true)}
            disabled={refreshing}
            aria-label="Refresh bookings"
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3.5 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 text-gray-500 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>

          <Link
            href="/marketplace"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
          >
            <Calendar className="h-4 w-4" />
            Book New Slot
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Bookings Hub */}
      <BookingList bookings={bookings} userRole={apiUser?.role} />
    </div>
  );
}
