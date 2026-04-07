import { fileURLToPath, URL } from 'node:url';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  base: './',
  plugins: [
    vue(),
    federation({
      name: 'musicpilot',
      filename: 'remoteEntry.js',
      exposes: {
        './Dashboard': './src/plugin/Dashboard.vue',
        './Page': './src/plugin/Page.vue',
      },
      shared: {
        vue: {
          requiredVersion: false,
        },
      },
      format: 'esm',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: true,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'esnext',
    cssCodeSplit: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
});
