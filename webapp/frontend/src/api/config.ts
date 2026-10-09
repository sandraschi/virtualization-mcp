/** Backend API base URL: same-origin "" by default (vite proxies /api), absolute only inside Tauri. */
function isTauri(): boolean {
  return (
    typeof window !== "undefined" &&
    ("__TAURI__" in window ||
      "__TAURI_INTERNALS__" in window ||
      window.location.host === "tauri.localhost")
  );
}
export const API_BASE = isTauri() ? "http://127.0.0.1:10701" : "";
