import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/login': 'http://localhost:8000',
      '/import': 'http://localhost:8000',
    },
  },
})