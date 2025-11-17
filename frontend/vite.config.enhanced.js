import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
// Enhanced plugins (install these first!)
// npm install --save-dev vite-plugin-compression vite-plugin-pwa vite-plugin-imagemin vite-plugin-performance
// Uncomment these imports after installing the packages:
// import { VitePWA } from 'vite-plugin-pwa'
// import viteCompression from 'vite-plugin-compression'
// import viteImagemin from 'vite-plugin-imagemin'
// import { performance } from 'vite-plugin-performance'
// import notifier from 'vite-plugin-notifier'
// https://vitejs.dev/config/
export default defineConfig({
    base: './',
    plugins: [
        vue(),
        // Uncomment these after installing dependencies:
        // PWA Plugin - Progressive Web App features
        /*
        VitePWA({
          registerType: 'autoUpdate',
          workbox: {
            globPatterns: ['**/ 
            * ., { js, css, html, ico, png, svg }, ']
    ]
}, includeAssets, ['favicon.ico', 'apple-touch-icon.png'], manifest, {
    name: 'Artacom FTTH Billing System',
    short_name: 'Artacom Billing',
    theme_color: '#1565c0',
    background_color: '#ffffff',
    display: 'standalone'
});
    * /;
// Advanced compression (Brotli + Gzip)
/*
viteCompression({
  algorithm: 'brotliCompress',
  ext: '.br'
}),
*/
// Image optimization
/*
viteImagemin({
  plugins: [
    imageminMozjpeg({ quality: 80 }),
    imageminPngquant({ quality: [0.65, 0.8] })
  ]
}),
*/
// Enhanced bundle visualization
visualizer({
    filename: 'dist/bundle-analysis.html',
    open: false,
    gzipSize: true,
    brotliSize: true,
    template: 'treemap' // Better visualization
}),
;
resolve: {
    alias: {
        '@';
        resolve(__dirname, 'src'),
            '@components';
        resolve(__dirname, 'src/components'),
            '@views';
        resolve(__dirname, 'src/views'),
            '@assets';
        resolve(__dirname, 'src/assets'),
            '@stores';
        resolve(__dirname, 'src/stores'),
            '@utils';
        resolve(__dirname, 'src/utils'),
            '@api';
        resolve(__dirname, 'src/api'),
        ;
    }
}
server: {
    port: 3000,
        host;
    true,
        cors;
    true,
        headers;
    {
        'Access-Control-Allow-Origin';
        '*';
    }
}
build: {
    // Advanced build optimizations
    minify: 'terser',
        terserOptions;
    {
        compress: {
            drop_console: true,
                drop_debugger;
            true,
                pure_funcs;
            ['console.log'];
        }
        mangle: {
            safari10: true;
        }
    }
    // CSS optimization
    cssCodeSplit: true,
        cssTarget;
    'chrome80',
        cssMinify;
    true,
        // Source maps untuk production debugging
        sourcemap;
    false,
        // Report compressed sizes
        reportCompressedSize;
    true,
        // Advanced chunking strategy
        rollupOptions;
    {
        output: {
            // Enhanced manual chunks
            manualChunks: (id) => {
                // Core Vue ecosystem
                if (id.includes('vue') && !id.includes('vue-echarts') && !id.includes('vue-chartjs')) {
                    return 'vue-core';
                }
                // Router and state management
                if (id.includes('vue-router') || id.includes('pinia')) {
                    return 'vue-ecosystem';
                }
                // Vuetify UI framework
                if (id.includes('vuetify')) {
                    return 'ui-framework';
                }
                // Icon libraries
                if (id.includes('lucide') || id.includes('@mdi')) {
                    return 'icons';
                }
                // Chart libraries - load dynamically
                if (id.includes('chart.js') || id.includes('vue-chartjs')) {
                    return 'charts-canvas';
                }
                if (id.includes('echarts') || id.includes('vue-echarts')) {
                    return 'charts-svg';
                }
                // Map libraries - load dynamically
                if (id.includes('mapbox-gl') || id.includes('leaflet')) {
                    return 'maps-geo';
                }
                // Network graph libraries
                if (id.includes('d3-force') || id.includes('v-network-graph')) {
                    return 'network-graphs';
                }
                // Utility libraries
                if (id.includes('lodash')) {
                    return 'lodash-utils';
                }
                if (id.includes('xlsx') || id.includes('html2canvas')) {
                    return 'file-utils';
                }
                // HTTP client
                if (id.includes('axios')) {
                    return 'http-client';
                }
                // Capacitor mobile
                if (id.includes('@capacitor')) {
                    return 'mobile-runtime';
                }
                // View-based chunks
                if (id.includes('src/views')) {
                    const viewName = id.split('/').pop()?.split('.')[0] || 'view';
                    return `views/${viewName}`;
                }
                // Component-based chunks
                if (id.includes('src/components')) {
                    const componentPath = id.split('src/components/')[1]?.split('/')[0];
                    if (componentPath) {
                        return `components/${componentPath}`;
                    }
                }
                // Default vendor chunk
                if (id.includes('node_modules')) {
                    return 'vendor';
                }
                return 'app';
            },
                // Enhanced file naming
                chunkFileNames;
            (chunkInfo) => {
                const facadeModuleId = chunkInfo.facadeModuleId ?
                    chunkInfo.facadeModuleId.split('/').pop()?.split('.')[0] : 'chunk';
                return `assets/js/${facadeModuleId}-[hash].js`;
            },
                assetFileNames;
            (assetInfo) => {
                const extType = assetInfo.name?.split('.').pop() || '';
                if (['mp4', 'webm', 'ogg', 'mp3', 'wav', 'flac', 'aac'].includes(extType)) {
                    return `assets/media/[name]-[hash][extname]`;
                }
                if (['png', 'jpg', 'jpeg', 'svg', 'gif', 'tiff', 'bmp', 'ico', 'webp'].includes(extType)) {
                    return `assets/images/[name]-[hash][extname]`;
                }
                if (['woff2', 'woff', 'eot', 'ttf', 'otf'].includes(extType)) {
                    return `assets/fonts/[name]-[hash][extname]`;
                }
                if (['css'].includes(extType)) {
                    return `assets/css/[name]-[hash][extname]`;
                }
                return `assets/[name]-[hash][extname]`;
            },
                // Optimize bundle sizes
                inlineDynamicImports;
            false,
                compact;
            true;
        }
    }
    // Performance thresholds
    chunkSizeWarningLimit: 500,
        assetsInlineLimit;
    4096,
        // Target optimization
        target;
    ['es2020', 'chrome87', 'firefox78', 'safari14'];
}
// Advanced dependency optimization
optimizeDeps: {
    include: [
        'vue',
        'vue-router',
        'pinia',
        'vuetify',
        'axios',
        'lodash-es'
    ],
        exclude;
    [
        '@capacitor/core',
        '@capacitor/android'
    ],
        force;
    true;
}
// CSS optimizations
css: {
    preprocessorOptions: {
        scss: {
            additionalData: `@import "@/styles/variables.scss";`;
        }
    }
}
// Define global constants
define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
        __BUILD_TIME__;
    JSON.stringify(new Date().toISOString()),
        __VUE_OPTIONS_API__;
    false,
        __VUE_PROD_DEVTOOLS__;
    false;
}
// Environment-specific optimizations
experimental: {
    renderBuiltUrl(filename, { hostType, type });
    {
        if (hostType === 'js') {
            return { js: `/${filename}` };
        }
        else {
            return { relative: true };
        }
    }
}
