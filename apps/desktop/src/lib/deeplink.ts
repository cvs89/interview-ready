import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";

export interface ParsedDeepLink {
  ticket: string;
  bookingId: string;
}

export class DeepLinkError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "DeepLinkError";
    this.code = code;
  }
}

/**
 * Parses and validates an incoming desktop deep link URL.
 * Expected format: interviewapp://join?ticket=<ticket>&bookingId=<bookingId>
 * (or interviewapp://join/?ticket=... or interviewapp:join?ticket=...)
 *
 * Never logs raw deep-link strings containing tickets.
 */
export function parseDeepLinkUrl(rawUrl: string): ParsedDeepLink | null {
  if (!rawUrl || typeof rawUrl !== "string") {
    return null;
  }

  const trimmed = rawUrl.trim();

  // Validate scheme starts with interviewapp
  if (!trimmed.toLowerCase().startsWith("interviewapp:")) {
    return null;
  }

  try {
    // Normalize custom scheme so standard URL parser can parse query params reliably
    const normalized = trimmed.replace(/^interviewapp:\/\/?/i, "http://localhost/");
    const parsed = new URL(normalized);

    // Validate path / host is 'join'
    const pathname = parsed.pathname.replace(/^\/+|\/+$/g, "");
    const host = parsed.host.toLowerCase();

    if (pathname !== "join" && host !== "join" && !normalized.includes("join")) {
      return null;
    }

    const ticket = parsed.searchParams.get("ticket");
    const bookingId = parsed.searchParams.get("bookingId") || parsed.searchParams.get("booking_id");

    if (!ticket || !bookingId || ticket.trim() === "" || bookingId.trim() === "") {
      return null;
    }

    return {
      ticket: ticket.trim(),
      bookingId: bookingId.trim(),
    };
  } catch {
    return null;
  }
}

/**
 * Exchanges a one-time desktop ticket with the backend API.
 * Clears sensitive ticket immediately after request dispatch.
 */
export async function exchangeTicket(
  apiUrl: string,
  ticket: string,
  bookingId?: string
): Promise<ExchangeDesktopTicketResponse> {
  const endpoint = `${apiUrl.replace(/\/$/, "")}/api/v1/auth/exchange-desktop-ticket`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        ticket,
        booking_id: bookingId || undefined,
      }),
    });

    if (!response.ok) {
      let errorCode = "EXCHANGE_FAILED";
      let errorMessage = `Ticket exchange failed with status ${response.status}`;

      try {
        const errorBody = await response.json();
        if (errorBody?.error) {
          errorCode = errorBody.error.code || errorCode;
          errorMessage = errorBody.error.message || errorMessage;
        }
      } catch {
        // Non-JSON response
      }

      if (response.status === 401 || response.status === 400 || errorCode.includes("TICKET")) {
        throw new DeepLinkError(
          "TICKET_INVALID_OR_EXPIRED",
          "The desktop interview ticket is invalid, expired, or has already been used. Please return to the web dashboard to launch again."
        );
      } else if (response.status === 403 || errorCode.includes("WINDOW")) {
        throw new DeepLinkError(
          "JOIN_WINDOW_CLOSED",
          "The interview join window is not open or has already closed."
        );
      } else if (response.status === 404) {
        throw new DeepLinkError(
          "BOOKING_NOT_FOUND",
          "The associated interview booking could not be found."
        );
      }

      throw new DeepLinkError(errorCode, errorMessage);
    }

    const data = (await response.json()) as ExchangeDesktopTicketResponse;
    return data;
  } catch (err: unknown) {
    if (err instanceof DeepLinkError) {
      throw err;
    }
    throw new DeepLinkError(
      "NETWORK_ERROR",
      "Unable to connect to the Interview Ready server. Please check your internet connection."
    );
  }
}
