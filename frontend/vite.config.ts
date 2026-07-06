import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El proxy reenvía las llamadas /api al backend FastAPI (puerto 8000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
