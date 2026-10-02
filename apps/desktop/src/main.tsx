import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";
import { Loader2 } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import ReactDOM from "react-dom/client";

import { DeepLinkPrompt } from "./components/DeepLinkPrompt";
import { DevicePreview } from "./components/DevicePreview";
import { ErrorDisplay } from "./components/ErrorDisplay";
import { LiveRoom } from "./components/LiveRoom";
import { DeepLinkError, exchangeTicket, parseDeepLinkUrl } from "./lib/deeplink";
import "./styles.css";

type AppScreen = "prompt" | "exchanging" | "preview" | "room" | "error";

export function App() {
  const [screen, setScreen] = useState<AppScreen>("prompt");
  const [session, setSession] = useState<ExchangeDesktopTicketResponse | null>(null);
  const [initialSettings, setInitialSettings] = useState<{ isMicOn: boolean; isCamOn: boolean }>({
    isMicOn: true,
    isCamOn: true,
  });
  const [errorInfo, setErrorInfo] = useState<{ code: string; message: string } | null>(null);

  const apiUrl =
    (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ||
    "http://localhost:8000";

  // Handle incoming deep link string
  const handleDeepLink = useCallback(
    async (rawUrl: string) => {
      const parsed = parseDeepLinkUrl(rawUrl);

      if (!parsed) {
        setErrorInfo({
          code: "INVALID_DEEP_LINK",
          message: "The provided deep link URL is not in a valid format. Expected interviewapp://join?ticket=...&bookingId=...",
        });
        setScreen("error");
        return;
      }

      setScreen("exchanging");
      setErrorInfo(null);

      try {
        // Exchange ticket immediately and clear ticket from caller scope
        const sessionData = await exchangeTicket(apiUrl, parsed.ticket, parsed.bookingId);
        setSession(sessionData);
        setScreen("preview");
      } catch (err: unknown) {
        if (err instanceof DeepLinkError) {
          setErrorInfo({ code: err.code, message: err.message });
        } else {
          setErrorInfo({
            code: "EXCHANGE_ERROR",
            message: "Failed to exchange desktop ticket. Please launch the session again from the web dashboard.",
          });
        }
        setScreen("error");
      }
    },
    [apiUrl]
  );

  // Listen for deep link events from browser/Tauri window
  useEffect(() => {
    // 1. Check window URL query params on cold load (for web/testing simulation)
    if (typeof window !== "undefined" && window.location.search) {
      const fullUrl = `interviewapp://join${window.location.search}`;
      handleDeepLink(fullUrl);
    }

    // 2. Listen for custom window messages or custom events
    const handleCustomEvent = (e: Event) => {
      const customEvent = e as CustomEvent<{ url: string }>;
      if (customEvent.detail?.url) {
        handleDeepLink(customEvent.detail.url);
      }
    };

    window.addEventListener("interviewapp:deeplink", handleCustomEvent);
    return () => {
      window.removeEventListener("interviewapp:deeplink", handleCustomEvent);
    };
  }, [handleDeepLink]);

  const handleEnterRoom = (settings: { isMicOn: boolean; isCamOn: boolean }) => {
    setInitialSettings(settings);
    setScreen("room");
  };

  const handleLeaveRoom = () => {
    setSession(null);
    setScreen("prompt");
  };

  const handleReset = () => {
    setSession(null);
    setErrorInfo(null);
    setScreen("prompt");
  };

  if (screen === "exchanging") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#08111f] p-6 text-white text-center">
        <Loader2 className="h-10 w-10 animate-spin text-blue-500 mb-4" />
        <h2 className="text-xl font-bold">Verifying Interview Ticket</h2>
        <p className="text-sm text-gray-400 mt-1 max-w-sm">
          Exchanging one-time security ticket with LiveKit media coordinator...
        </p>
      </div>
    );
  }

  if (screen === "error" && errorInfo) {
    return (
      <ErrorDisplay
        code={errorInfo.code}
        message={errorInfo.message}
        onReset={handleReset}
      />
    );
  }

  if (screen === "preview" && session) {
    return (
      <DevicePreview
        session={session}
        onJoinRoom={handleEnterRoom}
        onCancel={handleReset}
      />
    );
  }

  if (screen === "room" && session) {
    return (
      <LiveRoom
        session={session}
        initialSettings={initialSettings}
        onLeaveRoom={handleLeaveRoom}
      />
    );
  }

  return <DeepLinkPrompt onManualJoin={handleDeepLink} />;
}

// Ensure root is present before rendering
const rootElement = document.getElementById("root");
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
