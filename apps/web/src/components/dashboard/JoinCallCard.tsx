"use client";

import type { Booking, JoinStatusResponse, MintDesktopTicketResponse } from "@interview-ready/api-types";
import { AlertCircle, Calendar, CheckCircle2, Clock, Loader2, Video } from "lucide-react";
import React, { useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { formatCurrency, formatUtcToLocal } from "../../lib/api-client";
import { DesktopFallbackModal } from "./DesktopFallbackModal";

interface JoinCallCardProps {
  booking: Booking;
  userRole?: "CANDIDATE" | "INTERVIEWER" | "ADMIN";
}

export function JoinCallCard({ booking, userRole }: JoinCallCardProps) {
  const { api } = useAuth();

  const [joinStatus, setJoinStatus] = useState<JoinStatusResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(true);
  const [isMinting, setIsMinting] = useState<boolean>(false);
  const [showFallbackModal, setShowFallbackModal] = useState<boolean>(false);
  const [countdownText, setCountdownText] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch join status on mount and interval
  const fetchJoinStatus = React.useCallback(async () => {
    try {
      const data = await api.get<JoinStatusResponse>(
        `/api/v1/bookings/${booking.id}/join-status`
      );
      setJoinStatus(data);
    } catch {
      // Ignore initial background polling error
    } finally {
      setLoadingStatus(false);
    }
  }, [api, booking.id]);

  useEffect(() => {
    let isCancelled = false;

    fetchJoinStatus();

    // Poll join status every 10 seconds for real-time window tracking
    const pollInterval = setInterval(() => {
      if (!isCancelled) {
        fetchJoinStatus();
      }
    }, 10000);

    return () => {
      isCancelled = true;
      clearInterval(pollInterval);
    };
  }, [fetchJoinStatus]);

  // Real-time countdown timer tick
  useEffect(() => {
    if (!joinStatus) return;

    const updateTimer = () => {
      const now = Date.now();
      const openTime = new Date(joinStatus.join_available_at).getTime();
      const closeTime = new Date(joinStatus.join_closes_at).getTime();

      if (now < openTime) {
        const diffSec = Math.max(0, Math.floor((openTime - now) / 1000));
        const mins = Math.floor(diffSec / 60);
        const secs = diffSec % 60;
        setCountdownText(`Opens in ${mins}m ${String(secs).padStart(2, "0")}s`);
      } else if (now >= openTime && now < closeTime) {
        const diffSec = Math.max(0, Math.floor((closeTime - now) / 1000));
        const mins = Math.floor(diffSec / 60);
        const secs = diffSec % 60;
        setCountdownText(`Join window closes in ${mins}m ${String(secs).padStart(2, "0")}s`);
      } else {
        setCountdownText("Session closed");
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [joinStatus]);

  // Mint ticket and launch deep link
  const handleLaunchDesktop = async () => {
    setIsMinting(true);
    setErrorMessage(null);

    try {
      const response = await api.post<MintDesktopTicketResponse>(
        "/api/v1/auth/mint-desktop-ticket",
        {
          booking_id: booking.id,
        }
      );

      // Construct deep link with URL-encoded parameters
      const deepLink = `interviewapp://join?ticket=${encodeURIComponent(
        response.ticket
      )}&bookingId=${encodeURIComponent(booking.id)}`;

      // Launch deep link without logging sensitive ticket
      window.location.href = deepLink;

      // Show fallback modal with retry options
      setShowFallbackModal(true);
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setErrorMessage(eObj.message || "Failed to mint desktop ticket. Please try again.");
    } finally {
      setIsMinting(false);
    }
  };

  const createdInfo = formatUtcToLocal(booking.created_at);
  const isCandidate = userRole !== "INTERVIEWER";

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:border-blue-200 transition"
      data-testid={`join-call-card-${booking.id}`}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider ${
                booking.status === "CONFIRMED"
                  ? "bg-green-100 text-green-800"
                  : booking.status === "IN_PROGRESS"
                    ? "bg-blue-100 text-blue-800 animate-pulse"
                    : "bg-gray-100 text-gray-700"
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              {booking.status.replace("_", " ")}
            </span>

            <span className="text-xs text-gray-400 font-mono">
              Ref: {booking.id.slice(0, 8)}
            </span>

            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium">
              {isCandidate ? "Candidate Session" : "Interviewer Session"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span>
              Booked for <span className="font-semibold">{createdInfo.dateStr}</span> ({createdInfo.timeZone})
            </span>
          </div>

          <div className="text-sm font-semibold text-gray-900">
            Price: {formatCurrency(booking.price_minor, booking.currency)}
          </div>

          {countdownText && (
            <div
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg ${
                joinStatus?.can_join
                  ? "bg-green-50 text-green-700 border border-green-200"
                  : "bg-gray-50 text-gray-600 border border-gray-200"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{countdownText}</span>
            </div>
          )}

          {errorMessage && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 mt-1">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Join CTA Action */}
        <div className="flex flex-col items-start md:items-end gap-2">
          {loadingStatus ? (
            <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              Checking window...
            </div>
          ) : joinStatus?.can_join ? (
            <button
              onClick={handleLaunchDesktop}
              disabled={isMinting}
              className="flex items-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-bold text-white shadow-md hover:bg-green-700 active:scale-95 transition disabled:opacity-50"
              data-testid={`join-interview-btn-${booking.id}`}
            >
              {isMinting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Launching Desktop...
                </>
              ) : (
                <>
                  <Video className="h-4 w-4" />
                  Join Interview Call
                </>
              )}
            </button>
          ) : (
            <div className="flex flex-col md:items-end gap-1">
              <button
                disabled
                className="flex items-center gap-2 rounded-xl bg-gray-100 border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-400 cursor-not-allowed"
                data-testid={`join-interview-disabled-btn-${booking.id}`}
              >
                <Video className="h-4 w-4 text-gray-300" />
                Join Interview Call
              </button>
              <span className="text-xs text-gray-500">
                {joinStatus?.reason === "JOIN_WINDOW_NOT_STARTED"
                  ? "Join button enables 10 mins before call"
                  : joinStatus?.reason === "JOIN_WINDOW_EXPIRED"
                    ? "Join window has expired"
                    : "Join is currently unavailable"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Desktop Fallback Modal */}
      <DesktopFallbackModal
        isOpen={showFallbackModal}
        onClose={() => setShowFallbackModal(false)}
        onRetry={handleLaunchDesktop}
        isRetrying={isMinting}
      />
    </div>
  );
}
