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
      <div className="flex border-b border-[#EADBCE] gap-3 sm:gap-6">
        <button
          onClick={() => setActiveTab("upcoming")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === "upcoming"
              ? "border-[#9B3B25] text-[#9B3B25]"
              : "border-transparent text-[#6E5652] hover:text-[#342523] hover:border-[#ECC2A4]"
          }`}
          data-testid="tab-upcoming"
        >
          <span>Upcoming</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
              activeTab === "upcoming" ? "bg-[#F8DDC9] text-[#9B3B25]" : "bg-[#FDF5EE] text-[#6E5652]"
            }`}
          >
            {upcomingBookings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("completed")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === "completed"
              ? "border-[#9B3B25] text-[#9B3B25]"
              : "border-transparent text-[#6E5652] hover:text-[#342523] hover:border-[#ECC2A4]"
          }`}
          data-testid="tab-completed"
        >
          <span>Completed</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
              activeTab === "completed" ? "bg-[#F8DDC9] text-[#9B3B25]" : "bg-[#FDF5EE] text-[#6E5652]"
            }`}
          >
            {completedBookings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("cancelled")}
          className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === "cancelled"
              ? "border-[#9B3B25] text-[#9B3B25]"
              : "border-transparent text-[#6E5652] hover:text-[#342523] hover:border-[#ECC2A4]"
          }`}
          data-testid="tab-cancelled"
        >
          <span>Cancelled / Expired</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
              activeTab === "cancelled" ? "bg-[#F8DDC9] text-[#9B3B25]" : "bg-[#FDF5EE] text-[#6E5652]"
            }`}
          >
            {cancelledBookings.length}
          </span>
        </button>
      </div>

      {/* Content */}
      {displayedBookings.length === 0 ? (
        <div className="card-confidence p-10 sm:p-14 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4] mb-4">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="font-editorial text-xl font-bold text-[#342523] mb-1.5">
            No {activeTab.replace("_", " ")} interviews
          </h3>
          <p className="text-sm text-[#6E5652] max-w-sm mx-auto mb-6">
            {activeTab === "upcoming"
              ? "You do not have any scheduled practice sessions right now. Browse our approved interviewers and lock in a slot!"
              : activeTab === "completed"
                ? "No completed interviews yet. Your past sessions and structured feedback will appear here."
                : "No cancelled or expired interview records."}
          </p>
          {activeTab === "upcoming" && (
            <Link
              href="/marketplace"
              className="btn-pill-primary px-6 py-2.5 text-sm inline-flex"
            >
              Browse Interviewers →
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
                className="card-confidence p-6 sm:p-7 flex flex-col md:flex-row md:items-center justify-between gap-6"
                data-testid={`booking-card-${booking.id}`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-center gap-2.5">
                    {booking.status === "COMPLETED" && (
                      <span className="badge-confidence-confirmed text-xs">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        COMPLETED
                      </span>
                    )}
                    {booking.status === "PENDING_PAYMENT" && (
                      <span className="badge-confidence-reserved text-xs">
                        <Clock className="h-3.5 w-3.5" />
                        PENDING PAYMENT
                      </span>
                    )}
                    {(booking.status === "CANCELLED" || booking.status === "EXPIRED" || booking.status === "REFUNDED") && (
                      <span className="badge-confidence-cancelled text-xs">
                        <XCircle className="h-3.5 w-3.5" />
                        {booking.status.replace("_", " ")}
                      </span>
                    )}

                    <span className="text-xs text-[#96817D] font-mono">
                      Ref: {booking.id.slice(0, 8)}
                    </span>
                  </div>

                  <div className="text-sm text-[#4E3936]">
                    Booked on <span className="font-semibold text-[#342523]">{createdInfo.dateStr}</span>
                  </div>

                  <div className="text-sm font-semibold text-[#342523]">
                    Amount: <span className="font-editorial text-[#9B3B25] text-base">{formatCurrency(booking.price_minor, booking.currency)}</span>
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
                      className="btn-pill-primary px-5 py-2 text-sm"
                    >
                      Complete Payment
                    </button>
                  )}

                  <Link
                    href={`/bookings/${booking.id}/confirmation`}
                    className="btn-pill-secondary px-4 py-2 text-xs"
                  >
                    <ExternalLink className="h-3.5 w-3.5 mr-1" /> View Details
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
