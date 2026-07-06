import { defineConfig } from 'vite'
import react from '@vitejs/react-refresh' // ya '@vitejs/plugin-react' jo bhi aapka default ho

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://weather-backend-amit.onrender.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
