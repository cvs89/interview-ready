import type { Booking, JoinStatusResponse } from "@interview-ready/api-types";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../../context/AuthContext";
import { BookingList } from "./BookingList";

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const mockBookings: Booking[] = [
  {
    id: "booking-upcoming-1",
    slot_id: "slot-1",
    candidate_id: "cand-1",
    interviewer_id: "int-1",
    status: "CONFIRMED",
    price_minor: 10000,
    currency: "INR",
    created_at: "2026-10-02T12:00:00Z",
  },
  {
    id: "booking-completed-1",
    slot_id: "slot-2",
    candidate_id: "cand-1",
    interviewer_id: "int-1",
    status: "COMPLETED",
    price_minor: 12000,
    currency: "INR",
    created_at: "2026-10-01T12:00:00Z",
    completed_at: "2026-10-01T13:00:00Z",
  },
  {
    id: "booking-cancelled-1",
    slot_id: "slot-3",
    candidate_id: "cand-1",
    interviewer_id: "int-1",
    status: "CANCELLED",
    price_minor: 15000,
    currency: "INR",
    created_at: "2026-09-30T12:00:00Z",
    cancelled_at: "2026-09-30T12:30:00Z",
  },
];

describe("BookingList", () => {
  const mockGet = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      api: {
        get: mockGet,
      },
    });
    mockGet.mockResolvedValue({ can_join: false, reason: "JOIN_WINDOW_NOT_STARTED" } as JoinStatusResponse);
  });

  it("renders upcoming bookings by default on upcoming tab", () => {
    render(<BookingList bookings={mockBookings} userRole="CANDIDATE" />);

    expect(screen.getByTestId("join-call-card-booking-upcoming-1")).toBeInTheDocument();
    expect(screen.queryByTestId("booking-card-booking-completed-1")).not.toBeInTheDocument();
    expect(screen.queryByTestId("booking-card-booking-cancelled-1")).not.toBeInTheDocument();
  });

  it("switches to completed tab and shows completed bookings", () => {
    render(<BookingList bookings={mockBookings} userRole="CANDIDATE" />);

    const completedTab = screen.getByTestId("tab-completed");
    fireEvent.click(completedTab);

    expect(screen.getByTestId("booking-card-booking-completed-1")).toBeInTheDocument();
    expect(screen.queryByTestId("join-call-card-booking-upcoming-1")).not.toBeInTheDocument();
  });

  it("switches to cancelled/expired tab and shows cancelled bookings", () => {
    render(<BookingList bookings={mockBookings} userRole="CANDIDATE" />);

    const cancelledTab = screen.getByTestId("tab-cancelled");
    fireEvent.click(cancelledTab);

    expect(screen.getByTestId("booking-card-booking-cancelled-1")).toBeInTheDocument();
    expect(screen.queryByTestId("join-call-card-booking-upcoming-1")).not.toBeInTheDocument();
  });

  it("renders empty state message when no bookings exist in selected tab", () => {
    render(<BookingList bookings={[]} userRole="CANDIDATE" />);

    expect(screen.getByText("No upcoming interviews")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /browse interviewers/i })).toBeInTheDocument();
  });
});
