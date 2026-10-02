"use client";

import type { Booking } from "@interview-ready/api-types";
import { AlertCircle, CheckCircle2, Clock, Loader2 } from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { formatCurrency } from "../../lib/api-client";

interface PaymentStatusPollerProps {
  bookingId: string;
}

export function PaymentStatusPoller({ bookingId }: PaymentStatusPollerProps) {
  const { api } = useAuth();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [status, setStatus] = useState<"polling" | "confirmed" | "pending_timeout" | "failed">(
    "polling"
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 15; // 15 * 2s = 30s
    let isCancelled = false;

    const poll = async () => {
      try {
        const data = await api.get<Booking>(`/api/v1/bookings/${bookingId}`);
        if (isCancelled) return;
        setBooking(data);

        if (data.status === "CONFIRMED" || data.status === "IN_PROGRESS") {
          setStatus("confirmed");
          return;
        } else if (data.status === "CANCELLED" || data.status === "EXPIRED") {
          setStatus("failed");
          setErrorMsg(`Booking was not confirmed (status: ${data.status}).`);
          return;
        }

        attempts += 1;
        if (attempts >= maxAttempts) {
          setStatus("pending_timeout");
          return;
        }

        setTimeout(poll, 2000);
      } catch {
        if (isCancelled) return;
        attempts += 1;
        if (attempts >= maxAttempts) {
          setStatus("pending_timeout");
        } else {
          setTimeout(poll, 2000);
        }
      }
    };

    poll();

    return () => {
      isCancelled = true;
    };
  }, [api, bookingId]);

  if (status === "confirmed") {
    return (
      <div className="rounded-2xl border border-green-200 bg-green-50 p-8 text-center shadow-sm">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600 mb-4">
          <CheckCircle2 className="h-10 w-10" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Confirmed!</h2>
        <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
          Payment webhook confirmation received. Your mock interview slot is booked and secured.
        </p>

        {booking && (
          <div className="bg-white rounded-xl border border-green-100 p-4 max-w-sm mx-auto text-left text-sm space-y-2 mb-6 shadow-sm">
            <div className="flex justify-between text-gray-600">
              <span>Amount Paid:</span>
              <span className="font-semibold text-gray-900">
                {formatCurrency(booking.price_minor, booking.currency)}
              </span>
            </div>
            <div className="flex justify-between text-gray-600">
              <span>Status:</span>
              <span className="font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded text-xs">
                CONFIRMED
              </span>
            </div>
          </div>
        )}

        <div className="flex justify-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
          >
            Go to My Bookings
          </Link>
          <Link
            href="/marketplace"
            className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            Browse More Interviewers
          </Link>
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 mb-4">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Payment Not Completed</h2>
        <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
          {errorMsg || "The booking reservation could not be confirmed."}
        </p>
        <Link
          href="/marketplace"
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
        >
          Return to Marketplace
        </Link>
      </div>
    );
  }

  if (status === "pending_timeout") {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 text-amber-700 mb-4">
          <Clock className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Payment Processing</h2>
        <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
          We are waiting for the payment provider webhook to deliver confirmation. Your slot status will automatically update in your dashboard once processed.
        </p>
        <Link
          href="/dashboard"
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-blue-700 transition"
        >
          View Dashboard
        </Link>
      </div>
    );
  }

  // Polling in progress
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-sm" data-testid="payment-polling">
      <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600 mb-4" />
      <h3 className="font-bold text-lg text-gray-900 mb-2">Verifying Payment Confirmation</h3>
      <p className="text-sm text-gray-500 max-w-sm mx-auto">
        Waiting for verified payment webhook from provider...
      </p>
    </div>
  );
}
