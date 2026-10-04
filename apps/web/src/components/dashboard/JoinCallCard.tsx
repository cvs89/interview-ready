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
      className="card-confidence p-6 sm:p-7 hover:border-[#ECC2A4] transition"
      data-testid={`join-call-card-${booking.id}`}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-xs font-semibold ${
                booking.status === "CONFIRMED"
                  ? "bg-[#E8F4EC] text-[#2C6E49] border border-[#B4DEC4]"
                  : booking.status === "IN_PROGRESS"
                    ? "bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4] animate-pulse"
                    : "bg-[#FFFDFB] text-[#6E5652] border border-[#EADBCE]"
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              {booking.status.replace("_", " ")}
            </span>

            <span className="text-xs text-[#96817D] font-mono">
              Ref: {booking.id.slice(0, 8)}
            </span>

            <span className="text-xs bg-[#FDF5EE] border border-[#ECC2A4] text-[#9B3B25] px-2.5 py-0.5 rounded-full font-medium">
              {isCandidate ? "Candidate Session" : "Interviewer Session"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-sm text-[#4E3936]">
            <Calendar className="h-4 w-4 text-[#9B3B25]" />
            <span>
              Booked for <span className="font-semibold text-[#342523]">{createdInfo.dateStr}</span> ({createdInfo.timeZone})
            </span>
          </div>

          <div className="text-sm font-semibold text-[#342523]">
            Price: <span className="font-editorial text-[#9B3B25] text-base">{formatCurrency(booking.price_minor, booking.currency)}</span>
          </div>

          {countdownText && (
            <div
              className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full tabular-nums ${
                joinStatus?.can_join
                  ? "bg-[#E8F4EC] text-[#2C6E49] border border-[#B4DEC4]"
                  : "bg-[#FFFDFB] text-[#6E5652] border border-[#EADBCE]"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{countdownText}</span>
            </div>
          )}

          {errorMessage && (
            <div className="flex items-center gap-1.5 text-xs text-[#9E2A2B] mt-1">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Join CTA Action */}
        <div className="flex flex-col items-start md:items-end gap-2 shrink-0">
          {loadingStatus ? (
            <div className="flex items-center gap-2 text-xs text-[#96817D] py-2">
              <Loader2 className="h-4 w-4 animate-spin text-[#9B3B25]" />
              Checking window...
            </div>
          ) : joinStatus?.can_join ? (
            <button
              onClick={handleLaunchDesktop}
              disabled={isMinting}
              className="btn-pill-primary gap-2 py-3 px-6 text-sm font-bold shadow-md"
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
            <div className="flex flex-col md:items-end gap-1.5">
              <button
                disabled
                className="btn-pill-secondary opacity-60 cursor-not-allowed gap-2"
                data-testid={`join-interview-disabled-btn-${booking.id}`}
              >
                <Video className="h-4 w-4 text-[#96817D]" />
                Join Interview Call
              </button>
              <span className="text-xs text-[#96817D]">
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
