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
      <div className="card-confidence p-8 sm:p-10 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#E8F4EC] text-[#2C6E49] border border-[#B4DEC4] mb-4">
          <CheckCircle2 className="h-9 w-9" />
        </div>
        <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#342523] mb-2">
          Booking Confirmed!
        </h2>
        <p className="text-sm text-[#6E5652] max-w-md mx-auto mb-6 leading-relaxed">
          Payment webhook confirmation received. Your mock interview slot is booked and secured.
        </p>

        {booking && (
          <div className="bg-[#FFFDFB] rounded-2xl border border-[#EADBCE] p-5 max-w-sm mx-auto text-left text-sm space-y-2.5 mb-7">
            <div className="flex justify-between text-[#6E5652]">
              <span>Amount Paid:</span>
              <span className="font-editorial font-bold text-[#9B3B25] text-base">
                {formatCurrency(booking.price_minor, booking.currency)}
              </span>
            </div>
            <div className="flex justify-between items-center text-[#6E5652]">
              <span>Status:</span>
              <span className="badge-confidence-confirmed text-xs">
                CONFIRMED
              </span>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row justify-center gap-3">
          <Link
            href="/dashboard"
            className="btn-pill-primary px-6 py-2.5 text-sm"
          >
            Go to My Bookings
          </Link>
          <Link
            href="/marketplace"
            className="btn-pill-secondary px-6 py-2.5 text-sm"
          >
            Browse More Interviewers
          </Link>
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="card-confidence p-8 sm:p-10 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#FCEBEB] text-[#9E2A2B] border border-[#F5C2C2] mb-4">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h2 className="font-editorial text-2xl font-bold text-[#342523] mb-2">
          Payment Not Completed
        </h2>
        <p className="text-sm text-[#6E5652] max-w-md mx-auto mb-6">
          {errorMsg || "The booking reservation could not be confirmed."}
        </p>
        <Link
          href="/marketplace"
          className="btn-pill-primary px-6 py-2.5 text-sm inline-flex"
        >
          Return to Marketplace
        </Link>
      </div>
    );
  }

  if (status === "pending_timeout") {
    return (
      <div className="card-confidence p-8 sm:p-10 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#FEF3E2] text-[#A65E00] border border-[#FAD7A0] mb-4">
          <Clock className="h-8 w-8" />
        </div>
        <h2 className="font-editorial text-2xl font-bold text-[#342523] mb-2">
          Payment Processing
        </h2>
        <p className="text-sm text-[#6E5652] max-w-md mx-auto mb-6 leading-relaxed">
          We are waiting for the payment gateway webhook to deliver final confirmation. Your slot status will automatically update in your dashboard once processed.
        </p>
        <Link
          href="/dashboard"
          className="btn-pill-primary px-6 py-2.5 text-sm inline-flex"
        >
          View Dashboard
        </Link>
      </div>
    );
  }

  // Polling in progress
  return (
    <div className="card-confidence p-10 sm:p-12 text-center" data-testid="payment-polling">
      <Loader2 className="mx-auto h-10 w-10 animate-spin text-[#9B3B25] mb-4" />
      <h3 className="font-editorial text-xl font-bold text-[#342523] mb-2">
        Verifying Payment Confirmation
      </h3>
      <p className="text-sm text-[#6E5652] max-w-sm mx-auto">
        Waiting for verified webhook from payment gateway...
      </p>
    </div>
  );
}
