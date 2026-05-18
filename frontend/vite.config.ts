import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Запуск: из папки frontend — `npm install` затем `npm run dev` → http://localhost:3000
// Прокси на Django: убедитесь, что backend слушает http://127.0.0.1:8000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: false,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
