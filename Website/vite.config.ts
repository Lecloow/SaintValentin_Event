import { defineConfig } from 'vite'

export default defineConfig({
  base: '/SaintValentin_Event/',
  server: {
    port: 5173,
  },
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        profile: 'profile.html',
        questionnaire: 'questionnaire.html'
      }
    }
  }
})