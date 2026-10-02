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
      className="flex min-h-screen items-center justify-center bg-[#08111f] p-6 text-white"
      data-testid="deep-link-prompt"
    >
      <div className="w-full max-w-lg rounded-3xl border border-gray-800 bg-[#0d1b2e] p-8 shadow-2xl text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-400 mb-5">
          <Laptop className="h-8 w-8" />
        </div>

        <h1 className="text-2xl font-bold text-white mb-2">Interview Ready Desktop</h1>
        <p className="text-sm text-gray-400 max-w-sm mx-auto mb-8">
          The desktop client is listening for interview deep links. Click &ldquo;Join Interview Call&rdquo;
          from your web dashboard to launch into your live session.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="text-left">
            <label
              htmlFor="deepLinkInput"
              className="block text-xs font-semibold uppercase text-gray-400 mb-1.5"
            >
              Manual Join Link / Ticket
            </label>
            <input
              id="deepLinkInput"
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="interviewapp://join?ticket=...&bookingId=..."
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !inputUrl.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg hover:bg-blue-500 transition disabled:opacity-50"
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
