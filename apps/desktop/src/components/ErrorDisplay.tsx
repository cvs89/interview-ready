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
      className="flex min-h-screen items-center justify-center p-6 bg-[#08111f] text-white"
      data-testid="desktop-error-display"
    >
      <div className="w-full max-w-md rounded-2xl border border-red-500/30 bg-[#0d1b2e] p-8 shadow-2xl text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-red-400 mb-4">
          {isSecurityOrTicket ? <ShieldAlert className="h-8 w-8" /> : <AlertCircle className="h-8 w-8" />}
        </div>

        <h2 className="text-xl font-bold text-white mb-2">
          {isSecurityOrTicket ? "Ticket Expired or Invalid" : "Connection Issue"}
        </h2>

        <p className="text-sm text-gray-300 mb-6 leading-relaxed">
          {message}
        </p>

        <div className="flex flex-col gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-blue-500 transition"
              data-testid="error-retry-btn"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </button>
          )}

          {onReset && (
            <button
              onClick={onReset}
              className="flex items-center justify-center gap-2 rounded-xl border border-gray-700 bg-gray-800/60 px-5 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition"
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
