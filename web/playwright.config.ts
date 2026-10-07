import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.spec.ts",
  use: { baseURL: "http://127.0.0.1:5173/app/" },
  webServer: {
    command: "npm run dev -- --port 5173",
    url: "http://127.0.0.1:5173/app/",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
