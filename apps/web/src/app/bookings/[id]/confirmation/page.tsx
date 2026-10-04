"use client";

import { useParams } from "next/navigation";
import React from "react";

import { PaymentStatusPoller } from "../../../../components/booking/PaymentStatusPoller";

export default function BookingConfirmationPage() {
  const params = useParams();
  const bookingId = params?.id as string;

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#FFF8F0] py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        {bookingId ? (
          <PaymentStatusPoller bookingId={bookingId} />
        ) : (
          <div className="rounded-[24px] border border-red-200 bg-[#FCEBEB] p-6 text-center text-sm text-[#9E2A2B]">
            Invalid or missing booking ID.
          </div>
        )}
      </div>
    </div>
  );
}
