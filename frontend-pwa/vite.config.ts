import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
    proxy: {
      '/financial': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => `/api/v1${path}`,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
