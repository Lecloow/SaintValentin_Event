import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/import': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})