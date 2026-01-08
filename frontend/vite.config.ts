import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0', // Needed for Docker
    port: 5173,
    watch: {
      usePolling: true, // Needed for Windows Docker mounts sometimes
    }
  },
  preview: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: true, // Use boolean true to allow all, or array of strings
  }
})
