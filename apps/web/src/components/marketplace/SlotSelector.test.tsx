import type { AvailabilitySlot, Booking, PaymentCheckoutResponse, User } from "@interview-ready/api-types";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/api-client";
import { SlotSelector } from "./SlotSelector";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const mockSlot: AvailabilitySlot = {
  id: "slot-1",
  interviewer_id: "int-123",
  start_time: "2026-10-03T10:00:00Z",
  end_time: "2026-10-03T11:00:00Z",
  status: "AVAILABLE",
  price_minor: 15000,
  currency: "INR",
};

const mockUser: User = {
  id: "user-cand-1",
  firebase_uid: "fb-cand-1",
  email: "candidate@example.com",
  full_name: "Candidate Test",
  role: "CANDIDATE",
  status: "ACTIVE",
  email_verified: true,
  created_at: "2026-10-02T10:00:00Z",
  updated_at: "2026-10-02T10:00:00Z",
};

describe("SlotSelector", () => {
  const mockPush = vi.fn();
  const mockPost = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      push: mockPush,
    });
  });

  it("redirects unauthenticated user to sign in when clicking a slot", async () => {
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: null,
      api: { post: mockPost },
    });

    render(
      <SlotSelector
        interviewerId="int-123"
        interviewerName="Alex Interviewer"
        slots={[mockSlot]}
      />
    );

    const slotBtn = screen.getByTestId("slot-button-slot-1");
    fireEvent.click(slotBtn);

    expect(mockPush).toHaveBeenCalledWith("/auth/sign-in?redirect=/interviewers/int-123");
    expect(mockPost).not.toHaveBeenCalled();
  });

  it("reserves slot successfully for authenticated user", async () => {
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      api: { post: mockPost },
    });

    const mockBooking: Booking = {
      id: "booking-abc",
      slot_id: "slot-1",
      candidate_id: mockUser.id,
      interviewer_id: "int-123",
      status: "PENDING_PAYMENT",
      price_minor: 15000,
      currency: "INR",
      reservation_expires_at: new Date(Date.now() + 600000).toISOString(),
      created_at: new Date().toISOString(),
    };

    mockPost.mockResolvedValueOnce(mockBooking);

    render(
      <SlotSelector
        interviewerId="int-123"
        interviewerName="Alex Interviewer"
        slots={[mockSlot]}
      />
    );

    const slotBtn = screen.getByTestId("slot-button-slot-1");
    fireEvent.click(slotBtn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/bookings/reserve", {
        slot_id: "slot-1",
      });
      expect(screen.getByText("Slot Temporarily Reserved")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /proceed to payment/i })
    ).toBeInTheDocument();
  });

  it("handles 409 slot conflict error gracefully", async () => {
    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      api: { post: mockPost },
    });

    mockPost.mockRejectedValueOnce(
      new ApiError("SLOT_ALREADY_RESERVED", "Slot is already reserved.", 409, "req-123")
    );

    render(
      <SlotSelector
        interviewerId="int-123"
        interviewerName="Alex Interviewer"
        slots={[mockSlot]}
      />
    );

    const slotBtn = screen.getByTestId("slot-button-slot-1");
    fireEvent.click(slotBtn);

    await waitFor(() => {
      expect(
        screen.getByText(
          "The selected slot is no longer available. Please refresh and select another time."
        )
      ).toBeInTheDocument();
    });
  });

  it("initiates checkout and redirects when Proceed to Payment is clicked", async () => {
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        origin: "http://localhost:3000",
        href: "",
      },
    });

    (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      api: { post: mockPost },
    });

    const mockBooking: Booking = {
      id: "booking-abc",
      slot_id: "slot-1",
      candidate_id: mockUser.id,
      interviewer_id: "int-123",
      status: "PENDING_PAYMENT",
      price_minor: 15000,
      currency: "INR",
      reservation_expires_at: new Date(Date.now() + 600000).toISOString(),
      created_at: new Date().toISOString(),
    };

    const mockCheckoutRes: PaymentCheckoutResponse = {
      payment_id: "pay-123",
      booking_id: "booking-abc",
      provider: "mock",
      checkout_url: "https://stripe.test/session/xyz",
      amount_minor: 15000,
      currency: "INR",
      status: "REQUIRES_PAYMENT",
    };

    mockPost.mockResolvedValueOnce(mockBooking);
    mockPost.mockResolvedValueOnce(mockCheckoutRes);

    render(
      <SlotSelector
        interviewerId="int-123"
        interviewerName="Alex Interviewer"
        slots={[mockSlot]}
      />
    );

    const slotBtn = screen.getByTestId("slot-button-slot-1");
    fireEvent.click(slotBtn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /proceed to payment/i })).toBeInTheDocument();
    });

    const checkoutBtn = screen.getByRole("button", { name: /proceed to payment/i });
    fireEvent.click(checkoutBtn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        "/api/v1/payments/booking-abc/checkout",
        expect.objectContaining({
          success_url: "http://localhost:3000/bookings/booking-abc/confirmation",
          cancel_url: "http://localhost:3000/interviewers/int-123",
        })
      );
      expect(window.location.href).toBe("https://stripe.test/session/xyz");
    });

    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });
});
