import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./main";

describe("Desktop App Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders deep link prompt initially when no URL is provided", () => {
    render(<App />);

    expect(screen.getByTestId("deep-link-prompt")).toBeInTheDocument();
    expect(screen.getByText("Interview Ready Desktop")).toBeInTheDocument();
  });

  it("exchanges ticket and transitions to device preview on manual join submission", async () => {
    const mockSession: ExchangeDesktopTicketResponse = {
      session_jwt: "mock.jwt.test",
      livekit_url: "wss://livekit.test.com",
      livekit_token: "lk_token_123",
      room_name: "room-room-123",
      session_id: "session-1",
      booking_id: "booking-1",
      role: "CANDIDATE",
      expires_in_seconds: 3600,
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockSession,
    });

    render(<App />);

    const input = screen.getByLabelText(/manual join link/i);
    const submitBtn = screen.getByTestId("manual-join-submit-btn");

    fireEvent.change(input, {
      target: { value: "interviewapp://join?ticket=valid_ticket&bookingId=booking-1" },
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId("device-preview-screen")).toBeInTheDocument();
    });

    expect(screen.getByText("Interview Check-in & Setup")).toBeInTheDocument();
  });

  it("displays error screen when ticket is invalid or expired", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({
        error: {
          code: "TICKET_EXPIRED",
          message: "The desktop interview ticket is invalid, expired, or has already been used.",
        },
      }),
    });

    render(<App />);

    const input = screen.getByLabelText(/manual join link/i);
    const submitBtn = screen.getByTestId("manual-join-submit-btn");

    fireEvent.change(input, {
      target: { value: "interviewapp://join?ticket=expired_ticket&bookingId=booking-1" },
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId("desktop-error-display")).toBeInTheDocument();
    });

    expect(screen.getByText("Ticket Expired or Invalid")).toBeInTheDocument();

    const resetBtn = screen.getByTestId("error-reset-btn");
    fireEvent.click(resetBtn);

    expect(screen.getByTestId("deep-link-prompt")).toBeInTheDocument();
  });
});
