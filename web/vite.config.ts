import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'

import { tanstackStart } from '@tanstack/react-start/plugin/vite'

import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const config = defineConfig({
  resolve: { tsconfigPaths: true },
  // Login cookies need the API on the app's own origin, as the web host's proxy does in prod.
  server: {
    proxy: { '/api': { target: 'http://localhost:8000', ws: true } },
  },
  plugins: [
    devtools(),
    tailwindcss(),
    tanstackStart({ spa: { enabled: true } }),
    viteReact(),
  ],
})

export default config
