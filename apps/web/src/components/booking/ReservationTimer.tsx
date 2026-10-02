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
      className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium ${
        isExpired
          ? "bg-red-100 text-red-700 border border-red-200"
          : isUrgent
            ? "bg-amber-100 text-amber-800 border border-amber-200 animate-pulse"
            : "bg-blue-50 text-blue-700 border border-blue-100"
      } ${className}`}
      data-testid="reservation-timer"
    >
      {isExpired || isUrgent ? (
        <AlertTriangle className="h-4 w-4 shrink-0" />
      ) : (
        <Clock className="h-4 w-4 shrink-0" />
      )}
      <span>
        {isExpired ? "Reservation Expired" : `Reserved for ${formattedTime}`}
      </span>
    </div>
  );
}
