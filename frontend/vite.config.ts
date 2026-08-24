/// <reference types="vitest/config" />
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // The meter sits on a tripod in the auditorium while readings are watched
    // from a phone, so LAN exposure is sometimes needed. The dev proxy has no
    // auth of its own, so it defaults to localhost; set PCA_DEV_LAN to opt in.
    host: process.env.PCA_DEV_LAN ? true : 'localhost',
    allowedHosts: ['localhost'],
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8320',
        ws: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    passWithNoTests: true,
  },
})
