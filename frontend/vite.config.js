import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
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
                        // Utility libraries - optimized for dynamic imports
                        if (id.includes('xlsx')) {
                            return 'xlsx';
                        }
                        if (id.includes('html2canvas')) {
                            return 'html2canvas';
                        }
                        if (id.includes('lodash-es')) {
                            return 'lodash';
                        }
                        // Network graph libraries
                        if (id.includes('d3-force') || id.includes('v-network-graph')) {
                            return 'network';
                        }
                        // Material Design Icons
                        if (id.includes('@mdi') || id.includes('materialdesignicons')) {
                            return 'mdi';
                        }
                        // Date/time libraries
                        if (id.includes('date-fns') || id.includes('dayjs') || id.includes('moment')) {
                            return 'date';
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
});
