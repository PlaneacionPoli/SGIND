import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration — SGIND v2
 *
 * Por defecto los tests corren contra http://localhost:3000 (Next.js dev).
 * En CI se inicia el servidor automáticamente con `webServer`.
 * Los tests usan `page.route()` para mockear la API cuando el backend no está disponible.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // Intercept API calls — tests aplican mocks cuando el backend no responde
    extraHTTPHeaders: { "x-playwright": "1" },
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Inicia Next.js dev server automáticamente si no está corriendo
  webServer: process.env.CI
    ? {
        command: "npm run build && npm run start",
        url: "http://localhost:3000",
        reuseExistingServer: false,
        timeout: 120_000,
      }
    : {
        command: "npm run dev",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
