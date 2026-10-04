import { ArrowRight, Laptop, Video } from "lucide-react";
import React, { useState } from "react";

interface DeepLinkPromptProps {
  onManualJoin: (url: string) => void;
  isLoading?: boolean;
}

export function DeepLinkPrompt({ onManualJoin, isLoading }: DeepLinkPromptProps) {
  const [inputUrl, setInputUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUrl.trim()) {
      onManualJoin(inputUrl.trim());
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-[#FFF8F0] p-6 text-[#342523]"
      data-testid="deep-link-prompt"
    >
      <div className="w-full max-w-lg rounded-[28px] border border-[#EADBCE] bg-[#FFFDFB] p-8 sm:p-10 shadow-xl text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] mb-6 shadow-xs">
          <Laptop className="h-8 w-8" />
        </div>

        <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523] mb-3">
          Interview Ready Desktop
        </h1>
        <p className="text-sm text-[#6E5652] max-w-sm mx-auto mb-8 leading-relaxed">
          The desktop client is listening for interview deep links. Click &ldquo;Join Interview Call&rdquo;
          from your web dashboard to launch into your live session.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="text-left">
            <label
              htmlFor="deepLinkInput"
              className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-2"
            >
              Manual Join Link / Ticket
            </label>
            <input
              id="deepLinkInput"
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="interviewapp://join?ticket=...&bookingId=..."
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFF8F0] px-4 py-3 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !inputUrl.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-[#9B3B25] px-6 py-3.5 text-sm font-medium text-white shadow-md hover:bg-[#83321F] active:scale-98 transition disabled:opacity-50 cursor-pointer"
            data-testid="manual-join-submit-btn"
          >
            <Video className="h-4 w-4" />
            <span>{isLoading ? "Connecting to Session..." : "Join Interview Session"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
