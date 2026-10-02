"use client";

import { useParams } from "next/navigation";
import React from "react";

import { PaymentStatusPoller } from "../../../../components/booking/PaymentStatusPoller";

export default function BookingConfirmationPage() {
  const params = useParams();
  const bookingId = params?.id as string;

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      {bookingId ? (
        <PaymentStatusPoller bookingId={bookingId} />
      ) : (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
          Invalid or missing booking ID.
        </div>
      )}
    </div>
  );
}
