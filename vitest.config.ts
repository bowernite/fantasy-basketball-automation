import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: { bindings: {
          RUN_TOKEN: "test-run-token",
          FF_EMAIL: "owner@example.com",
          FF_PASSWORD: "test-password",
        }, },
    }),
  ],
  test: { include: ["src/worker/**/*.test.ts"] },
});
