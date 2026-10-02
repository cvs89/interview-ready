import type { Booking } from "@interview-ready/api-types";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../../context/AuthContext";
import { PaymentStatusPoller } from "./PaymentStatusPoller";

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

describe("PaymentStatusPoller", () => {
  const mockGet = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      api: {
        get: mockGet,
      },
    });
  });

  it("shows polling loader initially while booking is pending", async () => {
    const pendingBooking: Booking = {
      id: "booking-123",
      slot_id: "slot-456",
      candidate_id: "user-cand",
      interviewer_id: "user-int",
      status: "PENDING_PAYMENT",
      price_minor: 10000,
      currency: "INR",
      created_at: "2026-10-02T12:00:00Z",
    };

    mockGet.mockResolvedValueOnce(pendingBooking);

    render(<PaymentStatusPoller bookingId="booking-123" />);

    expect(screen.getByTestId("payment-polling")).toBeInTheDocument();
    expect(screen.getByText("Verifying Payment Confirmation")).toBeInTheDocument();
  });

  it("displays confirmed UI when booking reaches CONFIRMED status", async () => {
    const confirmedBooking: Booking = {
      id: "booking-123",
      slot_id: "slot-456",
      candidate_id: "user-cand",
      interviewer_id: "user-int",
      status: "CONFIRMED",
      price_minor: 10000,
      currency: "INR",
      created_at: "2026-10-02T12:00:00Z",
    };

    mockGet.mockResolvedValueOnce(confirmedBooking);

    render(<PaymentStatusPoller bookingId="booking-123" />);

    await waitFor(() => {
      expect(screen.getByText("Booking Confirmed!")).toBeInTheDocument();
    });

    expect(screen.getByText("Payment webhook confirmation received. Your mock interview slot is booked and secured.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /go to my bookings/i })).toHaveAttribute("href", "/dashboard");
  });

  it("displays failure UI when booking status is CANCELLED or EXPIRED", async () => {
    const expiredBooking: Booking = {
      id: "booking-123",
      slot_id: "slot-456",
      candidate_id: "user-cand",
      interviewer_id: "user-int",
      status: "EXPIRED",
      price_minor: 10000,
      currency: "INR",
      created_at: "2026-10-02T12:00:00Z",
    };

    mockGet.mockResolvedValueOnce(expiredBooking);

    render(<PaymentStatusPoller bookingId="booking-123" />);

    await waitFor(() => {
      expect(screen.getByText("Payment Not Completed")).toBeInTheDocument();
    });

    expect(screen.getByText(/Booking was not confirmed \(status: EXPIRED\)/i)).toBeInTheDocument();
  });
});
