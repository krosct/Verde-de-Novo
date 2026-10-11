import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const nodeEnv = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const apiTarget = nodeEnv.VITE_API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    proxy: {
      "/api": apiTarget,
    },
  },
  plugins: [
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.png", "img/perfil.webp", ".well-known/assetlinks.json"],
      manifest: {
        name: "Verde de Novo",
        short_name: "Verde de Novo",
        description:
          "Fotografe a planta inteira e veja a espécie provável, o que merece atenção e como ajudá-la a crescer. Não é diagnóstico.",
        lang: "pt-BR",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#0b1220",
        theme_color: "#0f766e",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,webp,webmanifest}"],
        navigateFallback: "/index.html",
        runtimeCaching: [],
      },
    }),
  ],
});
