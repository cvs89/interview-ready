import { describe, expect, it, vi, beforeEach } from "vitest";

import { DeepLinkError, exchangeTicket, parseDeepLinkUrl } from "./deeplink";

describe("deeplink parser", () => {
  it("correctly parses valid standard deep link URL", () => {
    const rawUrl = "interviewapp://join?ticket=abc123ticket&bookingId=booking-456";
    const result = parseDeepLinkUrl(rawUrl);

    expect(result).not.toBeNull();
    expect(result?.ticket).toBe("abc123ticket");
    expect(result?.bookingId).toBe("booking-456");
  });

  it("handles URL-encoded query parameters correctly", () => {
    const rawUrl =
      "interviewapp://join?ticket=ticket%2Bwith%2Fspecial%3D%3Dchars&bookingId=booking%2Duuid%2D123";
    const result = parseDeepLinkUrl(rawUrl);

    expect(result).not.toBeNull();
    expect(result?.ticket).toBe("ticket+with/special==chars");
    expect(result?.bookingId).toBe("booking-uuid-123");
  });

  it("handles alternative query param snake_case booking_id and trailing slash", () => {
    const rawUrl = "interviewapp://join/?ticket=sec_ticket_999&booking_id=booking-789";
    const result = parseDeepLinkUrl(rawUrl);

    expect(result).not.toBeNull();
    expect(result?.ticket).toBe("sec_ticket_999");
    expect(result?.bookingId).toBe("booking-789");
  });

  it("returns null for invalid scheme or missing parameters", () => {
    expect(parseDeepLinkUrl("https://join?ticket=123&bookingId=456")).toBeNull();
    expect(parseDeepLinkUrl("interviewapp://join?ticket=&bookingId=456")).toBeNull();
    expect(parseDeepLinkUrl("interviewapp://join?ticket=123")).toBeNull();
    expect(parseDeepLinkUrl("interviewapp://other?ticket=123&bookingId=456")).toBeNull();
    expect(parseDeepLinkUrl("")).toBeNull();
  });
});

describe("exchangeTicket", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("exchanges valid ticket successfully and returns session data", async () => {
    const mockSession = {
      session_jwt: "jwt.token.abc",
      livekit_url: "wss://livekit.example.com",
      livekit_token: "lk_token_123",
      room_name: "room-test-1",
      session_id: "session-uuid-1",
      booking_id: "booking-uuid-1",
      role: "CANDIDATE",
      expires_in_seconds: 3600,
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockSession,
    });

    const result = await exchangeTicket("http://localhost:8000", "ticket-xyz", "booking-uuid-1");

    expect(result).toEqual(mockSession);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/exchange-desktop-ticket",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ ticket: "ticket-xyz", booking_id: "booking-uuid-1" }),
      })
    );
  });

  it("throws TICKET_INVALID_OR_EXPIRED error on 401 response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({
        error: { code: "TICKET_EXPIRED", message: "Ticket expired" },
      }),
    });

    await expect(
      exchangeTicket("http://localhost:8000", "expired-ticket", "booking-uuid-1")
    ).rejects.toThrow(DeepLinkError);

    try {
      await exchangeTicket("http://localhost:8000", "expired-ticket", "booking-uuid-1");
    } catch (err) {
      expect((err as DeepLinkError).code).toBe("TICKET_INVALID_OR_EXPIRED");
    }
  });

  it("throws JOIN_WINDOW_CLOSED error on 403 response", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({
        error: { code: "JOIN_WINDOW_NOT_OPEN", message: "Window not open" },
      }),
    });

    try {
      await exchangeTicket("http://localhost:8000", "valid-ticket", "booking-uuid-1");
    } catch (err) {
      expect((err as DeepLinkError).code).toBe("JOIN_WINDOW_CLOSED");
    }
  });

  it("handles network failure gracefully", async () => {
    global.fetch = vi.fn().mockRejectedValueOnce(new Error("Network failed"));

    try {
      await exchangeTicket("http://localhost:8000", "ticket-abc", "booking-uuid-1");
    } catch (err) {
      expect((err as DeepLinkError).code).toBe("NETWORK_ERROR");
    }
  });
});
