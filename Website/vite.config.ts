import { defineConfig, loadEnv } from 'vite'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(__dirname, '..'), '')

  return {
    base: '/SaintValentin_Event/',
    server: {
      port: 5173,
    },
    build: {
      rollupOptions: {
        input: {
          main: 'index.html',
          profile: 'profile.html'
        }
      }
    },
  }
})