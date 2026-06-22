/** Backend API base URL. Use 127.0.0.1 not localhost — Windows resolves localhost to ::1 (IPv6) which the backend doesn't bind to. */
export const API_BASE =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:10701";
