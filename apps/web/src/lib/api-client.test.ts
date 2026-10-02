import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClient, ApiError, formatCurrency, formatUtcToLocal } from "./api-client";

describe("ApiClient", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("injects fresh Firebase ID token when available", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "123", full_name: "Test User" }),
    });
    global.fetch = mockFetch;

    const getToken = vi.fn().mockResolvedValue("mock-firebase-token-abc");
    const client = new ApiClient("http://api.test", getToken);

    const result = await client.get<{ id: string }>("/auth/me");

    expect(result).toEqual({ id: "123", full_name: "Test User" });
    expect(getToken).toHaveBeenCalled();
    expect(mockFetch).toHaveBeenCalledWith(
      "http://api.test/auth/me",
      expect.objectContaining({
        headers: expect.any(Headers),
        method: "GET",
      })
    );

    const calledHeaders = mockFetch.mock.calls[0][1].headers as Headers;
    expect(calledHeaders.get("Authorization")).toBe("Bearer mock-firebase-token-abc");
  });

  it("parses standard API error envelope into ApiError", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      headers: new Headers({ "x-request-id": "req-12345" }),
      json: async () => ({
        error: {
          code: "SLOT_ALREADY_RESERVED",
          message: "The selected slot is no longer available.",
          request_id: "req-12345",
        },
      }),
    });
    global.fetch = mockFetch;

    const client = new ApiClient("http://api.test");

    await expect(client.post("/api/v1/bookings/reserve", { slot_id: "slot-1" })).rejects.toThrow(
      ApiError
    );

    try {
      await client.post("/api/v1/bookings/reserve", { slot_id: "slot-1" });
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      expect(apiErr.code).toBe("SLOT_ALREADY_RESERVED");
      expect(apiErr.status).toBe(409);
      expect(apiErr.requestId).toBe("req-12345");
      expect(apiErr.message).toBe("The selected slot is no longer available.");
    }
  });

  it("handles 401 unauthenticated response gracefully", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers(),
      json: async () => ({
        error: {
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          request_id: "req-unauth",
        },
      }),
    });
    global.fetch = mockFetch;

    const client = new ApiClient("http://api.test");

    await expect(client.get("/auth/me")).rejects.toThrow(ApiError);
  });
});

describe("Format Utilities", () => {
  it("formats integer minor unit currency amounts correctly", () => {
    expect(formatCurrency(15000, "INR")).toContain("150");
    expect(formatCurrency(0, "INR")).toContain("0");
  });

  it("converts UTC date string to local time information", () => {
    const info = formatUtcToLocal("2027-05-15T14:30:00Z");
    expect(info.dateStr).toBeTruthy();
    expect(info.timeStr).toBeTruthy();
    expect(info.timeZone).toBeTruthy();
  });
});
