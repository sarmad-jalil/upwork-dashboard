import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In production the FastAPI backend serves this build from its own origin, so the
// app calls the API with relative paths. During `npm run dev` those same relative
// paths need forwarding to the backend — hence the proxy below.
const API_PREFIXES = ['/profiles', '/profile', '/jobs', '/job', '/proposal', '/tools', '/health']

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((p) => [p, { target: 'http://localhost:8000', changeOrigin: true }]),
    ),
  },
})
