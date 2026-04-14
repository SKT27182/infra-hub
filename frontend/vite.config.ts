import path from 'path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const port = Number(env.VITE_PORT)
  const apiTarget = env.VITE_DEV_API_TARGET 
  const allowedHosts = (env.VITE_ALLOWED_HOSTS || 'localhost,127.0.0.1,infra.skt27182.com')
    .split(',')
    .map((h) => h.trim())
    .filter(Boolean)

  if (!Number.isInteger(port) || port <= 0) {
    throw new Error('VITE_PORT must be set to a valid port number in .env')
  }

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port,
      allowedHosts,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '0.0.0.0',
      port,
    },
  }
})
