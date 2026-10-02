"use client";

import { Download, Laptop, RefreshCw, X } from "lucide-react";
import React from "react";

export interface DesktopFallbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRetry: () => void;
  isRetrying?: boolean;
}

export function DesktopFallbackModal({
  isOpen,
  onClose,
  onRetry,
  isRetrying = false,
}: DesktopFallbackModalProps) {
  if (!isOpen) return null;

  const winUrl =
    process.env.NEXT_PUBLIC_DESKTOP_DOWNLOAD_WINDOWS ||
    "https://github.com/interview-ready/releases/download/latest/InterviewReady-Setup.exe";
  const macUrl =
    process.env.NEXT_PUBLIC_DESKTOP_DOWNLOAD_MACOS ||
    "https://github.com/interview-ready/releases/download/latest/InterviewReady.dmg";
  const linuxUrl =
    process.env.NEXT_PUBLIC_DESKTOP_DOWNLOAD_LINUX ||
    "https://github.com/interview-ready/releases/download/latest/InterviewReady.AppImage";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      data-testid="desktop-fallback-modal"
    >
      <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-gray-100">
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-start gap-4 mb-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <Laptop className="h-6 w-6" />
          </div>
          <div>
            <h3 id="modal-title" className="text-xl font-bold text-gray-900">
              Launching Interview Ready Desktop
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              Secure live video and coding environment handoff
            </p>
          </div>
        </div>

        {/* Instructions */}
        <div className="space-y-4 text-sm text-gray-600 mb-6">
          <div className="rounded-xl bg-blue-50/80 border border-blue-100 p-4">
            <h4 className="font-semibold text-blue-900 mb-1 flex items-center gap-1.5">
              <span>Browser Prompt Notice</span>
            </h4>
            <p className="text-xs text-blue-700 leading-relaxed">
              If your browser prompted you to &ldquo;Open Interview Ready&rdquo; or allow custom
              protocol links, please click <strong>Open</strong> or <strong>Allow</strong>.
            </p>
          </div>

          <div className="border border-gray-200 rounded-xl p-4 space-y-3">
            <h4 className="font-semibold text-gray-900 text-xs uppercase tracking-wider">
              Haven&apos;t installed the desktop app yet?
            </h4>
            <p className="text-xs text-gray-500">
              Download the official Interview Ready client for low-latency WebRTC video and live code editor:
            </p>

            <div className="grid grid-cols-3 gap-2 pt-1">
              <a
                href={winUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-2 text-center text-xs font-medium text-gray-800 hover:bg-gray-100 hover:border-gray-300 transition"
              >
                <Download className="h-4 w-4 text-blue-600" />
                <span>Windows</span>
              </a>
              <a
                href={macUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-2 text-center text-xs font-medium text-gray-800 hover:bg-gray-100 hover:border-gray-300 transition"
              >
                <Download className="h-4 w-4 text-blue-600" />
                <span>macOS</span>
              </a>
              <a
                href={linuxUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-2 text-center text-xs font-medium text-gray-800 hover:bg-gray-100 hover:border-gray-300 transition"
              >
                <Download className="h-4 w-4 text-blue-600" />
                <span>Linux</span>
              </a>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col-reverse sm:flex-row sm:items-center justify-end gap-3 pt-2 border-t border-gray-100">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            Close
          </button>
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition disabled:opacity-50"
            data-testid="retry-launch-btn"
          >
            <RefreshCw className={`h-4 w-4 ${isRetrying ? "animate-spin" : ""}`} />
            {isRetrying ? "Minting New Ticket..." : "Retry Open Desktop"}
          </button>
        </div>
      </div>
    </div>
  );
}
