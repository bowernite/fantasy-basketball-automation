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
          PUSHOVER_TOKEN: "test-pushover-token",
          PUSHOVER_USER: "test-pushover-user",
          TRELLO_API_KEY: "test-trello-key",
          TRELLO_TOKEN: "test-trello-token",
          TRELLO_LIST: "test-trello-list",
          HEALTHCHECK_URL: "https://hc-ping.com/test-check",
        }, },
    }),
  ],
  test: { include: ["src/worker/**/*.test.ts"] },
});
