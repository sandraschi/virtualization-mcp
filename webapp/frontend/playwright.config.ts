import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: "http://localhost:10701",
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: {
    // e2e.ps1 guarantees backend :10701 + frontend :10700 are already up
    // before Playwright starts, so reuse them instead of booting anything.
    command: "uv run python -m virtualization_mcp.server --port 10700",
    port: 10700,
    timeout: 30000,
    reuseExistingServer: true,
  },
});
