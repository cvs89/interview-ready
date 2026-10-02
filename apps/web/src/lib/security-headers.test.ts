import { describe, expect, it } from "vitest";

import nextConfig from "../../next.config";

describe("Web Security Headers Configuration", () => {
  it("defines comprehensive security headers on all routes", async () => {
    expect(nextConfig.headers).toBeDefined();
    if (!nextConfig.headers) return;

    const headersConfig = await nextConfig.headers();
    expect(headersConfig).toHaveLength(1);
    expect(headersConfig[0].source).toBe("/:path*");

    const headerKeys = headersConfig[0].headers.map((h) => h.key);
    expect(headerKeys).toContain("Content-Security-Policy");
    expect(headerKeys).toContain("Strict-Transport-Security");
    expect(headerKeys).toContain("X-Content-Type-Options");
    expect(headerKeys).toContain("X-Frame-Options");
    expect(headerKeys).toContain("Referrer-Policy");
    expect(headerKeys).toContain("Permissions-Policy");

    const cspHeader = headersConfig[0].headers.find(
      (h) => h.key === "Content-Security-Policy"
    )?.value;
    expect(cspHeader).toContain("default-src 'self'");
    expect(cspHeader).toContain("frame-ancestors 'none'");

    const frameHeader = headersConfig[0].headers.find((h) => h.key === "X-Frame-Options")?.value;
    expect(frameHeader).toBe("DENY");

    const contentTypeHeader = headersConfig[0].headers.find(
      (h) => h.key === "X-Content-Type-Options"
    )?.value;
    expect(contentTypeHeader).toBe("nosniff");
  });
});
