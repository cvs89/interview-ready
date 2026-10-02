import { render, screen, act } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReservationTimer } from "./ReservationTimer";

describe("ReservationTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders countdown correctly for future expiry time", () => {
    const now = new Date("2026-10-02T12:00:00Z").getTime();
    vi.setSystemTime(now);

    const expiresAt = new Date("2026-10-02T12:09:30Z").toISOString(); // 9 min 30 sec = 570 sec

    render(<ReservationTimer expiresAt={expiresAt} />);

    expect(screen.getByText("Reserved for 09:30")).toBeInTheDocument();
  });

  it("decrements time every second and shows urgency under 2 minutes", () => {
    const now = new Date("2026-10-02T12:00:00Z").getTime();
    vi.setSystemTime(now);

    const expiresAt = new Date("2026-10-02T12:02:02Z").toISOString(); // 122 seconds

    render(<ReservationTimer expiresAt={expiresAt} />);

    expect(screen.getByText("Reserved for 02:02")).toBeInTheDocument();

    // Advance 5 seconds (117 seconds left - urgent)
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(screen.getByText("Reserved for 01:57")).toBeInTheDocument();
    const timerElement = screen.getByTestId("reservation-timer");
    expect(timerElement.className).toContain("animate-pulse");
  });

  it("fires onExpire callback when timer reaches zero", () => {
    const now = new Date("2026-10-02T12:00:00Z").getTime();
    vi.setSystemTime(now);

    const expiresAt = new Date("2026-10-02T12:00:03Z").toISOString(); // 3 seconds
    const onExpire = vi.fn();

    render(<ReservationTimer expiresAt={expiresAt} onExpire={onExpire} />);

    expect(screen.getByText("Reserved for 00:03")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(screen.getByText("Reservation Expired")).toBeInTheDocument();
    expect(onExpire).toHaveBeenCalledTimes(1);
  });
});
