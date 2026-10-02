"use client";

import type { Booking } from "@interview-ready/api-types";
import { Calendar, CheckCircle2, Clock, ExternalLink, XCircle } from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { formatCurrency, formatUtcToLocal } from "../../lib/api-client";
import { JoinCallCard } from "./JoinCallCard";

interface BookingListProps {
  bookings: Booking[];
  userRole?: "CANDIDATE" | "INTERVIEWER" | "ADMIN";
}

type TabType = "upcoming" | "completed" | "cancelled";

export function BookingList({ bookings, userRole }: BookingListProps) {
  const { api } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>("upcoming");

  const upcomingBookings = bookings.filter(
    (b) => b.status === "CONFIRMED" || b.status === "IN_PROGRESS"
  );
  const completedBookings = bookings.filter((b) => b.status === "COMPLETED");
  const cancelledBookings = bookings.filter(
    (b) =>
      b.status === "CANCELLED" ||
      b.status === "EXPIRED" ||
      b.status === "REFUNDED" ||
      b.status === "NO_SHOW" ||
      b.status === "PENDING_PAYMENT"
  );

  const displayedBookings =
    activeTab === "upcoming"
      ? upcomingBookings
      : activeTab === "completed"
        ? completedBookings
        : cancelledBookings;

  return (
    <div className="space-y-6" data-testid="booking-list">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 gap-4 sm:gap-8">
        <button
          onClick={() => setActiveTab("upcoming")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 ${
            activeTab === "upcoming"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
          data-testid="tab-upcoming"
        >
          <span>Upcoming</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${
              activeTab === "upcoming" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"
            }`}
          >
            {upcomingBookings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("completed")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 ${
            activeTab === "completed"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
          data-testid="tab-completed"
        >
          <span>Completed</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${
              activeTab === "completed" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"
            }`}
          >
            {completedBookings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("cancelled")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 ${
            activeTab === "cancelled"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
          data-testid="tab-cancelled"
        >
          <span>Cancelled / Expired</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${
              activeTab === "cancelled" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"
            }`}
          >
            {cancelledBookings.length}
          </span>
        </button>
      </div>

      {/* Content */}
      {displayedBookings.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-3">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="font-bold text-lg text-gray-900 mb-1">
            No {activeTab.replace("_", " ")} interviews
          </h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
            {activeTab === "upcoming"
              ? "You do not have any scheduled interviews right now. Find an interviewer and book a slot!"
              : activeTab === "completed"
                ? "No completed interviews yet. Your past sessions and feedback will appear here."
                : "No cancelled or expired interview records."}
          </p>
          {activeTab === "upcoming" && (
            <Link
              href="/marketplace"
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
            >
              Browse Interviewers
            </Link>
          )}
        </div>
      ) : activeTab === "upcoming" ? (
        <div className="space-y-4">
          {displayedBookings.map((booking) => (
            <JoinCallCard key={booking.id} booking={booking} userRole={userRole} />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {displayedBookings.map((booking) => {
            const createdInfo = formatUtcToLocal(booking.created_at);
            const isPendingPayment = booking.status === "PENDING_PAYMENT";

            return (
              <div
                key={booking.id}
                className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6"
                data-testid={`booking-card-${booking.id}`}
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider ${
                        booking.status === "COMPLETED"
                          ? "bg-blue-100 text-blue-800"
                          : booking.status === "PENDING_PAYMENT"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {booking.status === "COMPLETED" && <CheckCircle2 className="h-3.5 w-3.5" />}
                      {booking.status === "PENDING_PAYMENT" && <Clock className="h-3.5 w-3.5" />}
                      {(booking.status === "CANCELLED" || booking.status === "EXPIRED") && (
                        <XCircle className="h-3.5 w-3.5 text-red-500" />
                      )}
                      {booking.status.replace("_", " ")}
                    </span>

                    <span className="text-xs text-gray-400 font-mono">
                      Ref: {booking.id.slice(0, 8)}
                    </span>
                  </div>

                  <div className="text-sm text-gray-700">
                    Booked on <span className="font-semibold">{createdInfo.dateStr}</span>
                  </div>

                  <div className="text-sm font-semibold text-gray-900">
                    Amount: {formatCurrency(booking.price_minor, booking.currency)}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {isPendingPayment && (
                    <button
                      onClick={async () => {
                        const returnUrl = `${window.location.origin}/bookings/${booking.id}/confirmation`;
                        const checkoutRes = await api.post<{ checkout_url: string }>(
                          `/api/v1/payments/${booking.id}/checkout`,
                          { success_url: returnUrl }
                        );
                        if (checkoutRes.checkout_url) {
                          window.location.href = checkoutRes.checkout_url;
                        }
                      }}
                      className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
                    >
                      Complete Payment
                    </button>
                  )}

                  <Link
                    href={`/bookings/${booking.id}/confirmation`}
                    className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
                  >
                    <ExternalLink className="h-3.5 w-3.5" /> Details
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
