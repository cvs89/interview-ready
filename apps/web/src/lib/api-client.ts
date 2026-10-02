import type { ApiErrorEnvelope } from "@interview-ready/api-types";

export class ApiError extends Error {
  code: string;
  status: number;
  requestId: string;

  constructor(code: string, message: string, status: number, requestId: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  params?: Record<string, string | number | boolean | undefined | null>;
  body?: unknown;
  token?: string | null;
}

export class ApiClient {
  private baseUrl: string;
  private getToken?: () => Promise<string | null>;

  constructor(baseUrl?: string, getToken?: () => Promise<string | null>) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    this.getToken = getToken;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, body, headers = {}, token, signal, ...rest } = options;

    let url = path.startsWith("http")
      ? path
      : `${this.baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;

    if (params) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, String(value));
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes("?") ? "&" : "?") + queryString;
      }
    }

    const requestHeaders = new Headers(headers);
    if (!requestHeaders.has("Accept")) {
      requestHeaders.set("Accept", "application/json");
    }

    const authToken = token !== undefined ? token : this.getToken ? await this.getToken() : null;
    if (authToken && !requestHeaders.has("Authorization")) {
      requestHeaders.set("Authorization", `Bearer ${authToken}`);
    }

    let requestBody: BodyInit | undefined;
    if (body !== undefined) {
      if (body instanceof FormData || typeof body === "string") {
        requestBody = body as BodyInit;
      } else {
        requestHeaders.set("Content-Type", "application/json");
        requestBody = JSON.stringify(body);
      }
    }

    const response = await fetch(url, {
      ...rest,
      headers: requestHeaders,
      body: requestBody,
      signal,
    });

    if (!response.ok) {
      let code = "HTTP_ERROR";
      let message = `Request failed with status ${response.status}`;
      let requestId = response.headers.get("x-request-id") || "unknown";

      try {
        const errorBody = (await response.json()) as ApiErrorEnvelope;
        if (errorBody?.error) {
          code = errorBody.error.code || code;
          message = errorBody.error.message || message;
          requestId = errorBody.error.request_id || requestId;
        }
      } catch {
        // Response wasn't JSON
      }

      throw new ApiError(code, message, response.status, requestId);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  }

  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: "POST", body });
  }

  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: "PATCH", body });
  }

  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }
}

export function formatCurrency(amountMinor: number, currency: string = "INR"): string {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amountMinor / 100);
  } catch {
    return `${currency} ${(amountMinor / 100).toFixed(2)}`;
  }
}

export function formatUtcToLocal(utcDateString: string): {
  dateStr: string;
  timeStr: string;
  timeZone: string;
} {
  try {
    const date = new Date(utcDateString);
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const dateStr = date.toLocaleDateString(undefined, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    const timeStr = date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
    return { dateStr, timeStr, timeZone };
  } catch {
    return { dateStr: utcDateString, timeStr: "", timeZone: "UTC" };
  }
}

export function calculateDurationMinutes(startTime: string, endTime: string): number {
  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  return Math.round((end - start) / (1000 * 60));
}
