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
      <div className="flex min-h-[60vh] items-center justify-center bg-[#FFF8F0]">
        <Loader2 className="h-8 w-8 animate-spin text-[#9B3B25]" />
      </div>
    );
  }

  const isInterviewer = apiUser?.role === "INTERVIEWER";
  const displayName = apiUser?.full_name || user?.displayName || user?.email || "User";

  return (
    <div className="min-h-screen bg-[#FFF8F0] py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EADBCE] pb-6 mb-8">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#342523]">
                Welcome, {displayName}!
              </h1>
              {isInterviewer && (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-3 py-0.5 text-xs font-semibold text-[#9B3B25]">
                  <UserCheck className="h-3.5 w-3.5" /> Interviewer
                </span>
              )}
            </div>
            <p className="text-sm text-[#6E5652] mt-1.5">
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
              className="inline-flex items-center gap-1.5 rounded-full border border-[#EADBCE] bg-white px-4 py-2.5 text-sm font-medium text-[#342523] shadow-sm hover:bg-[#FDF5EE] transition disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 text-[#6E5652] ${refreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>

            <Link
              href="/marketplace"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-[#9B3B25] px-5 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition"
            >
              <Calendar className="h-4 w-4" />
              Book New Slot
            </Link>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-start gap-2.5 rounded-2xl border border-red-200 bg-[#FCEBEB] p-4 text-sm text-[#9E2A2B]">
            <AlertCircle className="h-5 w-5 shrink-0 text-[#9E2A2B] mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Bookings Hub */}
        <BookingList bookings={bookings} userRole={apiUser?.role} />
      </div>
    </div>
  );
}
