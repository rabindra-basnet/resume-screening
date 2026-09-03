import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build the React app into ./dist. The FastAPI backend mounts this folder as
// static assets and serves it with a SPA catch-all at the app root.
export default defineConfig({
  plugins: [react()],
  base: "/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  server: {
    port: 5173,
    // During local dev, forward API calls to the FastAPI backend.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
