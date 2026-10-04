"use client";

import { AlertTriangle, Clock } from "lucide-react";
import React, { useEffect, useState } from "react";

interface ReservationTimerProps {
  expiresAt: string | Date;
  onExpire?: () => void;
  className?: string;
}

export function ReservationTimer({ expiresAt, onExpire, className = "" }: ReservationTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState<number>(() => {
    const target = new Date(expiresAt).getTime();
    const now = Date.now();
    return Math.max(0, Math.floor((target - now) / 1000));
  });

  useEffect(() => {
    const target = new Date(expiresAt).getTime();

    const interval = setInterval(() => {
      const now = Date.now();
      const diff = Math.max(0, Math.floor((target - now) / 1000));
      setSecondsLeft(diff);

      if (diff <= 0) {
        clearInterval(interval);
        onExpire?.();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt, onExpire]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const formattedTime = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  const isUrgent = secondsLeft > 0 && secondsLeft < 120;
  const isExpired = secondsLeft <= 0;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-semibold tabular-nums transition-colors ${
        isExpired
          ? "bg-[#FCEBEB] text-[#9E2A2B] border border-[#F5C2C2]"
          : isUrgent
            ? "bg-[#FEF3E2] text-[#A65E00] border border-[#FAD7A0] animate-pulse"
            : "bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4]"
      } ${className}`}
      data-testid="reservation-timer"
    >
      {isExpired || isUrgent ? (
        <AlertTriangle className="h-4 w-4 shrink-0" />
      ) : (
        <Clock className="h-4 w-4 shrink-0 text-[#9B3B25]" />
      )}
      <span>
        {isExpired ? "Reservation Expired" : `Reserved for ${formattedTime}`}
      </span>
    </div>
  );
}
