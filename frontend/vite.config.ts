import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    visualizer({
      filename: 'bundle-analysis.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: true
  },
  build: {
    cssCodeSplit: true,
    cssMinify: true,  // Tambah minification untuk CSS
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Dynamic imports are handled automatically
          if (id.includes('node_modules')) {
            // Core Vue ecosystem
            if (id.includes('vue') && !id.includes('vue-echarts') && !id.includes('vue-chartjs')) {
              return 'vue-vendor';
            }
            // Vuetify UI framework
            if (id.includes('vuetify')) {
              return 'vuetify';
            }
            // Chart libraries - these will be loaded dynamically
            if (id.includes('chart.js') || id.includes('vue-chartjs') || id.includes('echarts') || id.includes('vue-echarts')) {
              return 'charts';
            }
            // Map libraries - these will be loaded dynamically
            if (id.includes('mapbox-gl') || id.includes('leaflet')) {
              return 'maps';
            }
            // Utility libraries
            if (id.includes('lodash-es') || id.includes('xlsx') || id.includes('html2canvas')) {
              return 'utils';
            }
            // Network graph libraries
            if (id.includes('d3-force') || id.includes('v-network-graph')) {
              return 'network';
            }
            // Other third-party libraries
            return 'vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'vuetify'],
  },
})