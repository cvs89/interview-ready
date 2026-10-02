import type { Booking, JoinStatusResponse, MintDesktopTicketResponse } from "@interview-ready/api-types";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../../context/AuthContext";
import { JoinCallCard } from "./JoinCallCard";

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const mockBooking: Booking = {
  id: "booking-123-abc",
  slot_id: "slot-456",
  candidate_id: "cand-789",
  interviewer_id: "int-101",
  status: "CONFIRMED",
  price_minor: 12000,
  currency: "INR",
  created_at: "2026-10-02T12:00:00Z",
};

describe("JoinCallCard", () => {
  const mockGet = vi.fn();
  const mockPost = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      api: {
        get: mockGet,
        post: mockPost,
      },
    });
  });

  it("disables join button when can_join is false outside join window", async () => {
    const closedStatus: JoinStatusResponse = {
      booking_id: mockBooking.id,
      can_join: false,
      server_time: "2026-10-02T12:00:00Z",
      join_available_at: "2026-10-02T13:50:00Z",
      join_closes_at: "2026-10-02T15:30:00Z",
      reason: "JOIN_WINDOW_NOT_STARTED",
    };

    mockGet.mockResolvedValueOnce(closedStatus);

    render(<JoinCallCard booking={mockBooking} userRole="CANDIDATE" />);

    await waitFor(() => {
      expect(
        screen.getByTestId(`join-interview-disabled-btn-${mockBooking.id}`)
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Join button enables 10 mins before call")).toBeInTheDocument();
  });

  it("enables join button when can_join is true", async () => {
    const openStatus: JoinStatusResponse = {
      booking_id: mockBooking.id,
      can_join: true,
      server_time: "2026-10-02T13:55:00Z",
      join_available_at: "2026-10-02T13:50:00Z",
      join_closes_at: "2026-10-02T15:30:00Z",
      room_name: "room-abc-xyz",
    };

    mockGet.mockResolvedValueOnce(openStatus);

    render(<JoinCallCard booking={mockBooking} userRole="CANDIDATE" />);

    await waitFor(() => {
      expect(
        screen.getByTestId(`join-interview-btn-${mockBooking.id}`)
      ).toBeInTheDocument();
    });

    const joinBtn = screen.getByTestId(`join-interview-btn-${mockBooking.id}`);
    expect(joinBtn).toBeEnabled();
  });

  it("mints ticket, properly URL-encodes deep link, launches deep link, and opens fallback modal", async () => {
    const originalLocation = window.location;
    const locationMock = { origin: "http://localhost:3000", href: "" };
    Object.defineProperty(window, "location", {
      configurable: true,
      value: locationMock,
    });

    const openStatus: JoinStatusResponse = {
      booking_id: mockBooking.id,
      can_join: true,
      server_time: "2026-10-02T13:55:00Z",
      join_available_at: "2026-10-02T13:50:00Z",
      join_closes_at: "2026-10-02T15:30:00Z",
      room_name: "room-abc-xyz",
    };

    const ticketResponse: MintDesktopTicketResponse = {
      ticket: "ticket+with special/chars==&123",
      expires_in_seconds: 60,
      join_closes_at: "2026-10-02T15:30:00Z",
      booking_id: mockBooking.id,
    };

    mockGet.mockResolvedValueOnce(openStatus);
    mockPost.mockResolvedValueOnce(ticketResponse);

    render(<JoinCallCard booking={mockBooking} userRole="CANDIDATE" />);

    await waitFor(() => {
      expect(
        screen.getByTestId(`join-interview-btn-${mockBooking.id}`)
      ).toBeInTheDocument();
    });

    const joinBtn = screen.getByTestId(`join-interview-btn-${mockBooking.id}`);
    fireEvent.click(joinBtn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/mint-desktop-ticket", {
        booking_id: mockBooking.id,
      });
      // Verify deep link URL encoding
      const encodedTicket = encodeURIComponent("ticket+with special/chars==&123");
      const expectedDeepLink = `interviewapp://join?ticket=${encodedTicket}&bookingId=${encodeURIComponent(
        mockBooking.id
      )}`;
      expect(locationMock.href).toBe(expectedDeepLink);
      // Verify fallback modal appears
      expect(screen.getByTestId("desktop-fallback-modal")).toBeInTheDocument();
    });

    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });

  it("mints a fresh ticket on repeated retry from fallback modal", async () => {
    const originalLocation = window.location;
    const locationMock = { origin: "http://localhost:3000", href: "" };
    Object.defineProperty(window, "location", {
      configurable: true,
      value: locationMock,
    });

    const openStatus: JoinStatusResponse = {
      booking_id: mockBooking.id,
      can_join: true,
      server_time: "2026-10-02T13:55:00Z",
      join_available_at: "2026-10-02T13:50:00Z",
      join_closes_at: "2026-10-02T15:30:00Z",
    };

    const firstTicket: MintDesktopTicketResponse = {
      ticket: "ticket-attempt-1",
      expires_in_seconds: 60,
      join_closes_at: "2026-10-02T15:30:00Z",
      booking_id: mockBooking.id,
    };

    const retryTicket: MintDesktopTicketResponse = {
      ticket: "ticket-attempt-2-fresh",
      expires_in_seconds: 60,
      join_closes_at: "2026-10-02T15:30:00Z",
      booking_id: mockBooking.id,
    };

    mockGet.mockResolvedValueOnce(openStatus);
    mockPost.mockResolvedValueOnce(firstTicket);
    mockPost.mockResolvedValueOnce(retryTicket);

    render(<JoinCallCard booking={mockBooking} userRole="CANDIDATE" />);

    await waitFor(() => {
      expect(screen.getByTestId(`join-interview-btn-${mockBooking.id}`)).toBeInTheDocument();
    });

    // 1st attempt
    fireEvent.click(screen.getByTestId(`join-interview-btn-${mockBooking.id}`));

    await waitFor(() => {
      expect(screen.getByTestId("desktop-fallback-modal")).toBeInTheDocument();
      expect(locationMock.href).toBe(
        `interviewapp://join?ticket=${encodeURIComponent("ticket-attempt-1")}&bookingId=${mockBooking.id}`
      );
    });

    // Retry in modal
    const retryBtn = screen.getByTestId("retry-launch-btn");
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledTimes(2);
      expect(locationMock.href).toBe(
        `interviewapp://join?ticket=${encodeURIComponent("ticket-attempt-2-fresh")}&bookingId=${mockBooking.id}`
      );
    });

    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });
});
