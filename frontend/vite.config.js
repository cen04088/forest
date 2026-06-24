import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 코어 분리
          "vendor-vue": ["vue", "vue-router"],
          // Leaflet 지도 라이브러리 (무거움) 분리
          "vendor-leaflet": ["leaflet"],
        },
      },
    },
    // 청크 경고 임계값 상향 (Leaflet이 커서 경고 발생 방지)
    chunkSizeWarningLimit: 800,
  },
});
