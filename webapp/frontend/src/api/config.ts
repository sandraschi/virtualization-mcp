/** Backend API base URL. Must match webapp/start.ps1 BackendPort (default 10701). */
export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:10701";
