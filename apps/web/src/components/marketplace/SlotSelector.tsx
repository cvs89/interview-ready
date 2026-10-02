"use client";

import type { AvailabilitySlot, Booking, PaymentCheckoutResponse } from "@interview-ready/api-types";
import { AlertCircle, Calendar, CheckCircle, Clock, CreditCard, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

import { useAuth } from "../../context/AuthContext";
import {
  calculateDurationMinutes,
  formatCurrency,
  formatUtcToLocal,
  type ApiError,
} from "../../lib/api-client";
import { ReservationTimer } from "../booking/ReservationTimer";

interface SlotSelectorProps {
  interviewerId: string;
  interviewerName: string;
  slots: AvailabilitySlot[];
}

export function SlotSelector({ interviewerName, slots }: SlotSelectorProps) {
  const router = useRouter();
  const { user, api } = useAuth();

  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [activeBooking, setActiveBooking] = useState<Booking | null>(null);
  const [isReserving, setIsReserving] = useState(false);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const availableSlots = slots.filter((s) => s.status === "AVAILABLE");

  const handleSelectSlot = async (slot: AvailabilitySlot) => {
    if (!user) {
      router.push(`/auth/sign-in?redirect=/interviewers/${slot.interviewer_id}`);
      return;
    }

    setErrorMsg(null);
    setSelectedSlot(slot);
    setIsReserving(true);

    try {
      const booking = await api.post<Booking>("/api/v1/bookings/reserve", {
        slot_id: slot.id,
      });
      setActiveBooking(booking);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      if (
        apiErr.status === 409 ||
        (typeof apiErr.code === "string" && apiErr.code.includes("SLOT"))
      ) {
        setErrorMsg(
          "The selected slot is no longer available. Please refresh and select another time."
        );
      } else if (apiErr.code === "CANNOT_BOOK_OWN_SLOT") {
        setErrorMsg("You cannot book your own interview slot.");
      } else {
        setErrorMsg(apiErr.message || "Failed to reserve slot. Please try again.");
      }
      setSelectedSlot(null);
      setActiveBooking(null);
    } finally {
      setIsReserving(false);
    }
  };

  const handleProceedToCheckout = async () => {
    if (!activeBooking) return;
    setIsCheckingOut(true);
    setErrorMsg(null);

    try {
      const returnUrl = `${window.location.origin}/bookings/${activeBooking.id}/confirmation`;
      const checkoutRes = await api.post<PaymentCheckoutResponse>(
        `/api/v1/payments/${activeBooking.id}/checkout`,
        {
          success_url: returnUrl,
          cancel_url: `${window.location.origin}/interviewers/${selectedSlot?.interviewer_id}`,
        }
      );

      if (checkoutRes.checkout_url) {
        // Direct to payment gateway or mock checkout
        window.location.href = checkoutRes.checkout_url;
      }
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      if (apiErr.code === "RESERVATION_EXPIRED" || apiErr.status === 409) {
        setErrorMsg("Your reservation has expired. Please select a slot again.");
        setActiveBooking(null);
        setSelectedSlot(null);
      } else {
        setErrorMsg(apiErr.message || "Checkout could not be initiated.");
      }
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleTimerExpired = () => {
    setErrorMsg("Your 10-minute reservation has expired. Please select the slot again.");
    setActiveBooking(null);
    setSelectedSlot(null);
  };

  return (
    <div className="space-y-6">
      {errorMsg && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
          <div className="flex-1 text-sm font-medium">{errorMsg}</div>
        </div>
      )}

      {/* Active Reservation Banner */}
      {activeBooking && activeBooking.reservation_expires_at && selectedSlot && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle className="h-5 w-5 text-blue-600" />
                <h4 className="font-bold text-gray-900 text-base">Slot Temporarily Reserved</h4>
              </div>
              <p className="text-sm text-gray-600">
                Mock interview with <span className="font-semibold">{interviewerName}</span> for{" "}
                <span className="font-semibold text-gray-900">
                  {formatCurrency(activeBooking.price_minor, activeBooking.currency)}
                </span>
              </p>
            </div>
            <ReservationTimer
              expiresAt={activeBooking.reservation_expires_at}
              onExpire={handleTimerExpired}
            />
          </div>

          <div className="mt-5 flex items-center gap-3">
            <button
              onClick={handleProceedToCheckout}
              disabled={isCheckingOut}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition disabled:opacity-50"
            >
              {isCheckingOut ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Initiating Checkout...
                </>
              ) : (
                <>
                  <CreditCard className="h-4 w-4" />
                  Proceed to Payment ({formatCurrency(activeBooking.price_minor, activeBooking.currency)})
                </>
              )}
            </button>
            <button
              onClick={() => {
                setActiveBooking(null);
                setSelectedSlot(null);
              }}
              disabled={isCheckingOut}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition disabled:opacity-50"
            >
              Choose Different Slot
            </button>
          </div>
        </div>
      )}

      {/* Slots List */}
      <div>
        <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-blue-600" />
          Available Times
        </h3>

        {availableSlots.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center">
            <p className="text-sm font-medium text-gray-600">No open interview slots available right now.</p>
            <p className="text-xs text-gray-400 mt-1">Please check back later or contact the interviewer.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {availableSlots.map((slot) => {
              const { dateStr, timeStr, timeZone } = formatUtcToLocal(slot.start_time);
              const duration = calculateDurationMinutes(slot.start_time, slot.end_time);
              const isSelected = selectedSlot?.id === slot.id;

              return (
                <button
                  key={slot.id}
                  data-testid={`slot-button-${slot.id}`}
                  onClick={() => handleSelectSlot(slot)}
                  disabled={isReserving || (activeBooking !== null && !isSelected)}
                  className={`flex flex-col text-left p-4 rounded-xl border transition ${
                    isSelected
                      ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500"
                      : "border-gray-200 bg-white hover:border-blue-300 hover:shadow-sm"
                  } disabled:opacity-60`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="font-semibold text-gray-900 text-sm">{dateStr}</span>
                    <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      {formatCurrency(slot.price_minor, slot.currency)}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-gray-600 mb-1">
                    <Clock className="h-3.5 w-3.5 text-gray-400" />
                    <span>
                      {timeStr} ({duration} mins)
                    </span>
                  </div>

                  <div className="text-[11px] text-gray-400">
                    Timezone: <span className="font-medium text-gray-500">{timeZone}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
