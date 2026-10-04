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
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#342523]/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      data-testid="desktop-fallback-modal"
    >
      <div className="relative w-full max-w-lg card-confidence p-6 sm:p-8 shadow-2xl border border-[#EADBCE]">
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-full p-2 text-[#6E5652] hover:bg-[#FDF5EE] hover:text-[#342523] transition cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-start gap-4 mb-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4]">
            <Laptop className="h-6 w-6" />
          </div>
          <div>
            <h3 id="modal-title" className="font-editorial text-xl sm:text-2xl font-bold text-[#342523]">
              Launching Interview Ready Desktop
            </h3>
            <p className="text-xs sm:text-sm text-[#6E5652] mt-0.5">
              Secure live video and coding environment handoff
            </p>
          </div>
        </div>

        {/* Instructions */}
        <div className="space-y-4 text-sm text-[#4E3936] mb-6">
          <div className="rounded-2xl bg-[#FDF5EE] border border-[#ECC2A4] p-4">
            <h4 className="font-semibold text-[#9B3B25] text-xs uppercase tracking-wider mb-1">
              Browser Prompt Notice
            </h4>
            <p className="text-xs text-[#6E5652] leading-relaxed">
              If your browser prompted you to &ldquo;Open Interview Ready&rdquo; or allow custom
              protocol links, please click <strong>Open</strong> or <strong>Allow</strong>.
            </p>
          </div>

          <div className="border border-[#EADBCE] rounded-2xl p-4 sm:p-5 space-y-3 bg-[#FFFDFB]">
            <h4 className="font-semibold text-[#342523] text-xs uppercase tracking-wider">
              Haven&apos;t installed the desktop app yet?
            </h4>
            <p className="text-xs text-[#6E5652] leading-relaxed">
              Download the official Interview Ready client for low-latency WebRTC video and live code editor:
            </p>

            <div className="grid grid-cols-3 gap-2.5 pt-1">
              <a
                href={winUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-xl border border-[#EADBCE] bg-white p-2.5 text-center text-xs font-semibold text-[#342523] hover:border-[#9B3B25] hover:bg-[#FDF5EE] transition"
              >
                <Download className="h-4 w-4 text-[#9B3B25]" />
                <span>Windows</span>
              </a>
              <a
                href={macUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-xl border border-[#EADBCE] bg-white p-2.5 text-center text-xs font-semibold text-[#342523] hover:border-[#9B3B25] hover:bg-[#FDF5EE] transition"
              >
                <Download className="h-4 w-4 text-[#9B3B25]" />
                <span>macOS</span>
              </a>
              <a
                href={linuxUrl}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center justify-center gap-1 rounded-xl border border-[#EADBCE] bg-white p-2.5 text-center text-xs font-semibold text-[#342523] hover:border-[#9B3B25] hover:bg-[#FDF5EE] transition"
              >
                <Download className="h-4 w-4 text-[#9B3B25]" />
                <span>Linux</span>
              </a>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col-reverse sm:flex-row sm:items-center justify-end gap-3 pt-3 border-t border-[#EADBCE]">
          <button
            onClick={onClose}
            className="btn-pill-secondary px-5 py-2.5 text-sm"
          >
            Close
          </button>
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="btn-pill-primary px-6 py-2.5 text-sm gap-2"
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
