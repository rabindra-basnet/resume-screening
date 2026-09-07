import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-vite-plugin";

// Build the React app into ./dist. The FastAPI backend mounts this folder as
// static assets and serves it with a SPA catch-all at the app root.
export default defineConfig({
  plugins: [
    react(),
    tanstackRouter({
      target: "react",
      // Routes live in ./src/routes; the file-route tree is generated into
      // ./src/routeTree.gen.ts at build/dev time.
      routesDirectory: "./src/routes",
      generatedRouteTree: "./src/routeTree.gen.ts",
    }),
  ],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  base: "/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          router: ["@tanstack/react-router", "@tanstack/react-store"],
          icons: ["lucide-react"],
        },
      },
    },
  },
  server: {
    port: 5173,
    allowedHosts: true,
    // During local dev, forward API calls to the FastAPI backend.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});