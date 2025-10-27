// frontend/src/main.ts

import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'mapbox-gl/dist/mapbox-gl.css';

// Optimize font loading for better LCP
const fontLink = document.createElement('link');
fontLink.rel = 'stylesheet';
fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
fontLink.media = 'print';
fontLink.onload = () => {
    fontLink.media = 'all';
};
document.head.appendChild(fontLink);

// 1. Impor semua yang dibutuhkan
import App from './App.vue'
import router from './router'
// @ts-ignore - Vuetify CSS import
import 'vuetify/dist/vuetify.min.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
// Optimasi: import selective components untuk tree shaking
import * as vuetifyComponents from './plugins/vuetify'
import '@mdi/font/css/materialdesignicons.css'
import 'leaflet/dist/leaflet.css';

import { useAuthStore } from './stores/auth'

// 2. Buat instance Vuetify dengan tema light dan dark yang kontras
const vuetify = createVuetify({
  components: {
    ...components,
    ...vuetifyComponents
  },
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#6366f1',
          secondary: '#8b5cf6',
          accent: '#ec4899',
          error: '#ef4444',
          warning: '#f59e0b',
          info: '#3b82f6',
          success: '#10b981',
          background: '#ffffff',
          surface: '#f8fafc',
        },
      },
      dark: {
        dark: true,
        colors: {
          primary: '#818cf8',
          secondary: '#a78bfa',
          accent: '#f472b6',
          error: '#f87171',
          warning: '#fbbf24',
          info: '#60a5fa',
          success: '#34d399',
          background: '#0f172a',
          surface: '#1e293b',
        },
      },
    },
  },
})


async function startup() {
  const app = createApp(App)
  const pinia = createPinia()
  
  app.use(pinia)

  // 3. Panggil aksi untuk memulihkan sesi
  // Ini akan berjalan SEBELUM aplikasi di-mount
  const authStore = useAuthStore()
  await authStore.initializeAuth()

  app.use(router)
  app.use(vuetify)

  // 4. Mount aplikasi setelah semua siap
  app.mount('#app')
}

startup()
