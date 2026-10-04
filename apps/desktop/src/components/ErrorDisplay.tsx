import { AlertCircle, ArrowLeft, RefreshCw, ShieldAlert } from "lucide-react";
import React from "react";

interface ErrorDisplayProps {
  code: string;
  message: string;
  onRetry?: () => void;
  onReset?: () => void;
}

export function ErrorDisplay({ code, message, onRetry, onReset }: ErrorDisplayProps) {
  const isSecurityOrTicket =
    code === "TICKET_INVALID_OR_EXPIRED" || code === "DUPLICATE_TICKET" || code === "REPLAYED_TICKET";

  return (
    <div
      className="flex min-h-screen items-center justify-center p-6 bg-[#FFF8F0] text-[#342523]"
      data-testid="desktop-error-display"
    >
      <div className="w-full max-w-md rounded-[28px] border border-[#EADBCE] bg-[#FFFDFB] p-8 sm:p-10 shadow-xl text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#FCEBEB] text-[#9E2A2B] mb-5 shadow-xs">
          {isSecurityOrTicket ? <ShieldAlert className="h-8 w-8" /> : <AlertCircle className="h-8 w-8" />}
        </div>

        <h2 className="font-serif text-2xl font-normal text-[#342523] mb-3">
          {isSecurityOrTicket ? "Ticket Expired or Invalid" : "Connection Issue"}
        </h2>

        <p className="text-sm text-[#6E5652] mb-8 leading-relaxed">
          {message}
        </p>

        <div className="flex flex-col gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center justify-center gap-2 rounded-full bg-[#9B3B25] px-6 py-3 text-sm font-medium text-white shadow-md hover:bg-[#83321F] active:scale-98 transition cursor-pointer"
              data-testid="error-retry-btn"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </button>
          )}

          {onReset && (
            <button
              onClick={onReset}
              className="flex items-center justify-center gap-2 rounded-full border border-[#EADBCE] bg-[#FFF8F0] px-6 py-3 text-sm font-medium text-[#6E5652] hover:text-[#342523] hover:bg-[#F8DDC9]/50 transition cursor-pointer"
              data-testid="error-reset-btn"
            >
              <ArrowLeft className="h-4 w-4" />
              Return to Launch Screen
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
