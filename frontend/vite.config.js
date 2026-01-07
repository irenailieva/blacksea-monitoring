import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
    allowedHosts: true,
  }
})
