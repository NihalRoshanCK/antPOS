import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import frappeui from 'frappe-ui/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: '../ant_pos/www/antPOS.html',
        outDir: '../ant_pos/public/antPOS',
        emptyOutDir: true,
        // Never ship maps: the build output is served publicly from
        // /assets/ant_pos/antPOS/. Use 'hidden' + an error tracker if you need them.
        sourcemap: false,
      },
    }),
    vue(),
    vueJsx(),
    VitePWA({
      registerType: 'autoUpdate',
      // Registered by hand in src/main.js so a missing Service-Worker-Allowed
      // header degrades quietly instead of throwing on every page load.
      injectRegister: false,
      devOptions: {
        enabled: true,
      },
      // The service worker is served from /assets/ant_pos/antPOS/, so by default
      // its scope cannot reach /antPOS and it never controls the app. Claiming a
      // wider scope requires the `Service-Worker-Allowed: /antPOS/` response
      // header -- see docs/DEPLOYMENT.md.
      scope: '/antPOS/',
      manifest: {
        name: 'antPOS',
        short_name: 'antPOS',
        // start_url must live inside scope or the manifest is rejected and the
        // app cannot be installed. It previously pointed at /antPOS while scope
        // defaulted to /assets/ant_pos/antPOS/. Note the trailing slash: with
        // scope '/antPOS/', a start_url of '/antPOS' is outside scope.
        scope: '/antPOS/',
        start_url: '/antPOS/',
        display: 'standalone',
        description: 'POS system powered by Frappe',
        icons: [
          {
            src: '/assets/ant_pos/manifest/manifest-icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/assets/ant_pos/manifest/manifest-icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'maskable',
          },
          {
            src: '/assets/ant_pos/manifest/manifest-icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/assets/ant_pos/manifest/manifest-icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: ({ url }) =>
              url.origin === self.location.origin &&
              url.pathname.startsWith('/api/'),
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    // Vendor code changes far less often than app code; splitting it means a
    // release only invalidates the app chunk instead of all 2 MB.
    //
    // Only Vue core is split out: it depends on nothing else. frappe-ui must stay
    // in the same chunk as its own dependencies -- with frappe-ui 0.1.278 a
    // separate frappe-ui chunk and the general vendor chunk import each other,
    // and the app crashed at startup with "Cannot access '...' before
    // initialization".
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (/[\\/]node_modules[\\/](vue|vue-router|pinia|@vue)[\\/]/.test(id)) {
            return 'vendor-vue'
          }
          return 'vendor'
        },
      },
    },
  },
  optimizeDeps: {
    include: [
      'frappe-ui > feather-icons',
      'showdown',
      'engine.io-client',
      'tailwind.config.js',
      'prosemirror-state',
      'prosemirror-view',
      'lowlight',
      'interactjs'
    ],
  },
})
