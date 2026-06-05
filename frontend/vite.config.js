import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.VITE_PORT || '3000'),
    strictPort: false,
    proxy: {
      '/api': {
        target: `http://${process.env.API_HOST || 'localhost'}:${process.env.API_PORT || '8000'}`,
        changeOrigin: true
      }
    },
    hmr: process.env.VITE_HMR_HOST
      ? {
          host: process.env.VITE_HMR_HOST,
          port: parseInt(process.env.VITE_HMR_PORT || '3000'),
          protocol: 'ws'
        }
      : undefined
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
