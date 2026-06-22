import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const BACKEND_PORT = 10701;

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["goliath"],
    port: 10700,
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
      },
      "/docs": {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
      },
      "/openapi.json": {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
      },
      "/redoc": {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
});
