import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Frontend calls /api/* → FastAPI on :8000 during dev (avoids CORS hassle).
      '/api': 'http://localhost:8000',
    },
  },
})
