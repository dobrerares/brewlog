import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Backend host the dev server proxies to. Default = same machine as Vite.
  // Override on a separate device (laptop hitting Tailscale): set
  // VITE_API_TARGET in brewlog/.env.local, e.g. http://100.83.42.67:8000
  const target = env.VITE_API_TARGET ?? 'http://localhost:8000'
  const wsTarget = target.replace(/^http/, 'ws')

  return {
    plugins: [tailwindcss(), react()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      proxy: {
        '/api': { target, changeOrigin: true },
        '/graphql': { target, changeOrigin: true },
        '/ws': { target: wsTarget, ws: true, changeOrigin: true },
      },
    },
  }
})
