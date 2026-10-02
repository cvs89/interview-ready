import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  resolve: { alias: { "@": new URL("./src", import.meta.url).pathname } },
  test: {
    environment: "jsdom",
    env: { NEXT_PUBLIC_API_URL: "http://localhost:8000" },
    setupFiles: ["./vitest.setup.ts"],
  },
});
