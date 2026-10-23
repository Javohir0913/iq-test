import { defineConfig, devices } from "@playwright/test";

// E2E testlar ishlayotgan stackka qarshi: docker compose up -d --build, so‘ng npm run e2e
export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.BASE_URL || "http://localhost",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 860 } } },
    { name: "mobile", use: { ...devices["Pixel 5"], viewport: { width: 360, height: 780 } } },
  ],
});
