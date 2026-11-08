import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

declare const process: { env: Record<string, string | undefined> };

// REST endpoints of vdsim.service; the dev server forwards them to the API (default http://127.0.0.1:8000)
const API = process.env.MOTIONENGINE_API ?? "http://127.0.0.1:8000";
const apiPaths = ["/health", "/metrics", "/vehicle", "/trajectory", "/simulate", "/plan", "/predict", "/models",
  "/openapi.json", "/docs", "/redoc"];

export default defineConfig({
  plugins: [react()],
  server: { proxy: Object.fromEntries(apiPaths.map((p) => [p, { target: API, changeOrigin: true }])) },
  build: {
    target: "es2022",
    sourcemap: true,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes("node_modules/katex")) return "katex";
          if (id.includes("node_modules/uplot")) return "uplot";
          if (/node_modules\/(react|react-dom|scheduler|react-router)/.test(id)) return "react";
          if (id.includes("node_modules/i18next") || id.includes("node_modules/react-i18next")) return "i18n";
          return undefined;
        },
      },
    },
  },
  test: { environment: "jsdom", globals: false },
});
