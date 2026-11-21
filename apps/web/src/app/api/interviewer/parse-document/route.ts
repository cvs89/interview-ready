import { NextResponse } from "next/server";

const MAX_DOCUMENT_BYTES = 5 * 1024 * 1024;
const API_URL =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://api.interview-ready.net";

export async function POST(request: Request): Promise<Response> {
  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > MAX_DOCUMENT_BYTES + 64 * 1024) {
    return NextResponse.json(
      { error: { code: "DOCUMENT_TOO_LARGE", message: "Resume files must be 5 MB or smaller." } },
      { status: 413 }
    );
  }

  const contentType = request.headers.get("content-type");
  if (!contentType?.startsWith("multipart/form-data")) {
    return NextResponse.json(
      { error: { code: "INVALID_DOCUMENT_UPLOAD", message: "A resume file is required." } },
      { status: 400 }
    );
  }

  const body = await request.arrayBuffer();
  if (body.byteLength > MAX_DOCUMENT_BYTES + 64 * 1024) {
    return NextResponse.json(
      { error: { code: "DOCUMENT_TOO_LARGE", message: "Resume files must be 5 MB or smaller." } },
      { status: 413 }
    );
  }

  const headers = new Headers({ "Content-Type": contentType, Accept: "application/json" });
  const authorization = request.headers.get("authorization");
  if (authorization) headers.set("Authorization", authorization);

  try {
    const upstream = await fetch(`${API_URL.replace(/\/$/, "")}/interviewers/me/parse-document`, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
        "x-request-id": upstream.headers.get("x-request-id") || "unknown",
      },
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "UPLOAD_SERVICE_UNAVAILABLE",
          message: "The resume service is temporarily unavailable. Please try again.",
        },
      },
      { status: 503 }
    );
  }
}
