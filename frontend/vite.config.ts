import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development the API runs on :8000; the proxy keeps the browser on one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
