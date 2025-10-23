<template>
 <v-app class="modern-app">
    <v-system-bar 
     v-if="settingsStore.maintenanceMode.isActive"
      color="warning" 
      window 
      class="maintenance-banner" 
      >
      <v-icon class="me-2">mdi-alert</v-icon>
      <span>{{ settingsStore.maintenanceMode.message }}</span>
    </v-system-bar>

    <!-- Navigation Drawer (Sidebar) -->
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail && !isMobile"
      :temporary="isMobile"
      :permanent="!isMobile"
      class="modern-drawer"
      :width="isMobile ? '280' : '280'"
      :key="forceRender"
    >
      <v-list-item class="sidebar-header" :class="{'px-0': rail && !isMobile}" :ripple="false">
        <div class="header-flex-container">
          <img v-if="!rail || isMobile" :src="logoSrc" alt="Jelantik Logo" class="sidebar-logo-full"/>
          
          <v-icon v-if="rail && !isMobile" color="primary" size="large">mdi-alpha-j</v-icon>

          <div v-if="!rail || isMobile" class="sidebar-title-wrapper">
            <h1 class="sidebar-title">Artacom Ftth</h1>
            <span class="sidebar-subtitle">PORTAL CUSTOMER V3</span>
          </div>

          <v-spacer v-if="!rail || isMobile"></v-spacer>

          <v-btn
            v-if="!isMobile"
            icon="mdi-chevron-left"
            variant="text"
            size="small"
            @click.stop="rail = !rail"
          ></v-btn>
          
          <v-btn
            v-if="isMobile"
            icon="mdi-close"
            variant="text"
            size="small"
            @click.stop="drawer = false"
          ></v-btn>
        </div>
      </v-list-item>

      <v-divider></v-divider>

      <div class="navigation-wrapper" :key="'nav-wrapper-' + forceRender">
        <v-list nav class="navigation-menu" :key="menuKey">
          <template v-for="group in filteredMenuGroups" :key="group.title + '-' + menuKey + '-' + forceRender">
            <v-list-subheader v-if="!rail || isMobile" class="menu-subheader" :key="'subheader-' + group.title + '-' + forceRender">{{ group.title }}</v-list-subheader>

            <template v-for="item in group.items" :key="item.title + '-' + item.value + '-' + forceRender">
              <v-list-group
                v-if="'children' in item"
                :value="item.value"
                :key="'group-' + item.value + '-' + forceRender"
              >
                <template v-slot:activator="{ props }">
                  <v-list-item
                    v-bind="props"
                    :prepend-icon="item.icon"
                    :title="item.title"
                    class="nav-item"
                    :key="'activator-' + item.value + '-' + forceRender"
                  ></v-list-item>
                </template>

                <v-list-item
                  v-for="subItem in item.children"
                  :key="subItem.title + '-' + subItem.to + '-' + forceRender"
                  :title="subItem.title"
                  :to="subItem.to"
                  :prepend-icon="subItem.icon"
                  class="nav-sub-item"
                ></v-list-item>
              </v-list-group>

              <v-list-item
                v-else
                :prepend-icon="item.icon"
                :title="item.title"
                :value="item.value"
                :to="item.to"
                class="nav-item"
                :key="'item-' + item.value + '-' + forceRender"
              >
                <template v-slot:append>
                  <v-tooltip location="end">
                    <template v-slot:activator="{ props }">
                      <v-badge
                        v-if="item.value === 'langganan' && suspendedCount > 0"
                        color="error"
                        :content="suspendedCount"
                        inline
                        v-bind="props"
                      ></v-badge>
                    </template>
                    <span>{{ suspendedCount }} langganan berstatus "Suspended"</span>
                  </v-tooltip>
                  <v-tooltip location="end">
                    <template v-slot:activator="{ props }">
                      <v-badge
                        v-if="item.value === 'langganan' && stoppedCount > 0"
                        color="grey"
                        :content="stoppedCount"
                        inline
                        class="ms-2"
                        v-bind="props"
                      ></v-badge>
                    </template>
                    <span>{{ stoppedCount }} langganan berstatus "Berhenti"</span>
                  </v-tooltip>
                  <v-tooltip location="end">
                    <template v-slot:activator="{ props }">
                      <v-badge
                        v-if="item.value === 'invoices' && unpaidInvoiceCount > 0"
                        color="warning"
                        :content="unpaidInvoiceCount"
                        inline
                        v-bind="props"
                      ></v-badge>
                    </template>
                    <span>{{ unpaidInvoiceCount }} invoice belum dibayar</span>
                  </v-tooltip>
                </template>
              </v-list-item>
            </template>
          </template>
        </v-list>
      </div>

      <template v-slot:append>
        <div class="logout-section pa-4">
          <v-btn
            :block="!rail || isMobile"
            variant="tonal"
            color="grey-darken-1"
            class="logout-btn"
            :icon="rail && !isMobile"
            @click="handleLogout"
          >
            <v-icon v-if="rail && !isMobile">mdi-logout</v-icon>
            <span v-if="!rail || isMobile" class="d-flex align-center"><v-icon left>mdi-logout</v-icon>Logout</span>
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- App Bar (Header) -->
    <v-app-bar elevation="0" class="modern-app-bar">
      <v-btn
        icon="mdi-menu"
        variant="text"
        @click.stop="toggleDrawer"
      ></v-btn>
      <v-spacer></v-spacer>
      
      <v-btn icon variant="text" @click="toggleTheme" class="header-action-btn theme-toggle-btn">
        <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>

      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon variant="text" class="header-action-btn" v-bind="props">
            <v-badge :content="notifications.length" color="error" :model-value="notifications.length > 0">
              <v-icon>mdi-bell-outline</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <v-list class="pa-0" :width="isMobile ? '90vw' : '300'">
          <v-list-item class="font-weight-bold bg-grey-lighten-4">
              Notifikasi
              <template v-slot:append v-if="notifications.length > 0">
                  <v-btn variant="text" size="small" @click="markAllAsRead">Bersihkan</v-btn>
              </template>
          </v-list-item>
          <v-divider></v-divider>
          <div v-if="notifications.length === 0" class="text-center text-medium-emphasis pa-4">
              Tidak ada notifikasi baru.
          </div>
          <template v-else>
            <v-list-item
              v-for="(notif, index) in notifications"
              :key="index"
              class="py-2 notification-item"
              @click="handleNotificationClick(notif)"
            >
              <template v-slot:prepend>
                <v-avatar :color="getNotificationColor(notif.type)" size="32" class="me-3">
                    <v-icon size="18">{{ getNotificationIcon(notif.type) }}</v-icon>
                </v-avatar>
              </template>

              <div v-if="notif.type === 'new_payment'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Pembayaran Diterima</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  <strong>{{ notif.data?.invoice_number || 'N/A' }}</strong> dari <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> telah lunas.
                </v-list-item-subtitle>
              </div>

              <div v-else-if="notif.type === 'new_customer_for_noc'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Pelanggan Baru</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> perlu dibuatkan Data Teknis.
                </v-list-item-subtitle>
              </div>

              <div v-else-if="notif.type === 'new_technical_data'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Data Teknis Baru</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  Data teknis untuk <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> telah ditambahkan.
                </v-list-item-subtitle>
              </div>

              <div v-else class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Notifikasi</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ notif.message || 'Anda memiliki notifikasi baru' }}
                </v-list-item-subtitle>
              </div>
            </v-list-item>
          </template>
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Main Content -->
    <v-main class="modern-main" :class="{ 'with-bottom-nav': isMobile }">
      <router-view></router-view>
    </v-main>
    
    <!-- Bottom Navigation (Mobile Only) -->
    <v-bottom-navigation
      v-if="isMobile"
      v-model="activeBottomNav"
      class="mobile-bottom-nav"
      grow
      elevation="8"
      height="65"
    >
      <v-btn value="dashboard" @click="navigateTo('/dashboard')">
        <v-icon>mdi-home-variant</v-icon>
        <span>Dashboard</span>
      </v-btn>

      <v-btn value="pelanggan" @click="navigateTo('/pelanggan')">
        <v-icon>mdi-account-group-outline</v-icon>
        <span>Pelanggan</span>
      </v-btn>

      <v-btn value="langganan" @click="navigateTo('/langganan')">
        <v-badge
          v-if="suspendedCount > 0 || stoppedCount > 0"
          :content="suspendedCount + stoppedCount"
          color="error"
          overlap
        >
          <v-icon>mdi-wifi-star</v-icon>
        </v-badge>
        <v-icon v-else>mdi-wifi-star</v-icon>
        <span>Langganan</span>
      </v-btn>

      <v-btn value="trouble-tickets" @click="navigateTo('/trouble-tickets')">
        <v-badge
          v-if="openTicketsCount > 0"
          :content="openTicketsCount"
          color="warning"
          overlap
        >
          <v-icon>mdi-ticket-confirmation-outline</v-icon>
        </v-badge>
        <v-icon v-else>mdi-ticket-confirmation-outline</v-icon>
        <span>Tickets</span>
      </v-btn>

      <v-btn value="invoices" @click="navigateTo('/invoices')">
        <v-badge
          v-if="unpaidInvoiceCount > 0"
          :content="unpaidInvoiceCount"
          color="orange"
          overlap
        >
          <v-icon>mdi-file-document-outline</v-icon>
        </v-badge>
        <v-icon v-else>mdi-file-document-outline</v-icon>
        <span>Invoice</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- Footer (Desktop Only) -->
    <v-footer 
      v-if="!isMobile"
      app 
      height="69px" 
      class="d-flex align-center justify-center text-medium-emphasis footer-responsive" 
      style="border-top: 1px solid rgba(0,0,0,0.08);"
    >
      <div class="footer-content">
        &copy; {{ new Date().getFullYear() }} <strong>Artacom Billing System</strong>. All Rights Design Reserved by 
        <a 
          href="https://www.instagram.com/amad.dyk/" 
          target="_blank" 
          rel="noopener noreferrer"
          class="text-decoration-none text-primary"
        >
          amad.dyk
        </a>
      </div>
    </v-footer>

  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useTheme } from 'vuetify'
import { useDisplay } from 'vuetify'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import apiClient from '@/services/api';
import logo from '@/assets/Jelantik 1.svg';

// --- State ---
const theme = useTheme();
const { mobile } = useDisplay();
const drawer = ref(true);
const rail = ref(false);
const router = useRouter();
const route = useRoute();
const activeBottomNav = ref('dashboard');

// PERBAIKAN: Inisialisasi notifications dengan validasi lebih baik
const notifications = ref<any[]>([]);
// PERBAIKAN: Tambahkan watcher untuk memastikan notifications tetap array
watch(notifications, (newVal) => {
  if (!newVal || !Array.isArray(newVal)) {
    console.warn('[State] notifications bukan array, reset ke array kosong');
    notifications.value = [];
  }
}, { deep: true });

const suspendedCount = ref(0);
const unpaidInvoiceCount = ref(0);
const stoppedCount = ref(0);
const openTicketsCount = ref(0);
const userCount = ref(0);
const roleCount = ref(0);
const authStore = useAuthStore();
let socket: WebSocket | null = null;

// Use ref with watcher for better reactivity with Proxy objects
const userPermissions = ref<string[]>([]);

// Watch authStore.user for changes and update permissions reactively
watch(
  () => authStore.user,
  (newUser) => {
    if (newUser?.role) {
      const role = newUser.role;
      if (typeof role === 'object' && role !== null && role.name) {
        if (role.name.toLowerCase() === 'admin') {
          userPermissions.value = ['*'];
        } else {
          userPermissions.value = role.permissions?.map((p: any) => p.name) || [];
        }
      } else {
        userPermissions.value = [];
      }
    } else {
      userPermissions.value = [];
    }
  },
  { deep: true, immediate: true }
);

// Additional watch for role specifically
watch(
  () => authStore.user?.role,
  (newRole) => {
    if (newRole) {
      if (newRole.name?.toLowerCase() === 'admin') {
        userPermissions.value = ['*'];
      } else {
        userPermissions.value = newRole.permissions?.map((p: any) => p.name) || [];
      }
    }
  },
  { deep: true, immediate: true }
);

// Force re-render trigger
const forceRender = ref(0);

// Manual function to trigger menu refresh
function refreshMenu() {
  forceRender.value++;

  // Force next tick to ensure DOM updates
  nextTick(() => {
    // DOM updated
  });
}

// Watch permissions array specifically
watch(userPermissions, () => {
  refreshMenu();
}, { deep: true });

// Computed untuk mobile detection
const isMobile = computed(() => mobile.value);
const logoSrc = computed(() => theme.global.current.value.dark ? logo : logo);
const settingsStore = useSettingsStore();

// Watch route changes untuk update bottom nav
watch(() => route.path, (newPath) => {
  updateActiveBottomNav(newPath);
});

function updateActiveBottomNav(path: string) {
  if (path.includes('/dashboard')) {
    activeBottomNav.value = 'dashboard';
  } else if (path.includes('/pelanggan')) {
    activeBottomNav.value = 'pelanggan';
  } else if (path.includes('/langganan')) {
    activeBottomNav.value = 'langganan';
  } else if (path.includes('/trouble-tickets')) {
    activeBottomNav.value = 'trouble-tickets';
  } else if (path.includes('/invoices')) {
    activeBottomNav.value = 'invoices';
  }
}

function navigateTo(path: string) {
  router.push(path);
}

// Toggle drawer function untuk mobile/desktop
function toggleDrawer() {
  if (isMobile.value) {
    drawer.value = !drawer.value;
  } else {
    rail.value = !rail.value;
  }
}

async function fetchSidebarBadges() {
  try {
    const response = await apiClient.get('/dashboard/sidebar-badges');
    suspendedCount.value = response.data.suspended_count;
    unpaidInvoiceCount.value = response.data.unpaid_invoice_count;
    stoppedCount.value = response.data.stopped_count;
    openTicketsCount.value = response.data.open_tickets_count || 0;
  } catch (error) {
    console.error("Gagal mengambil data badge sidebar:", error);
  }
}

let pingInterval: NodeJS.Timeout | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;
let notificationCleanupInterval: NodeJS.Timeout | null = null;
let tokenCheckInterval: NodeJS.Timeout | null = null;

function playSound(type: string) {
  try {
    let audioFile = '';
    switch (type) {
      case 'new_payment':
        audioFile = '/pembayaran.mp3';
        break;
      case 'new_customer_for_noc':
      case 'new_customer':
        audioFile = '/payment.mp3';
        break;
      case 'new_technical_data':
        audioFile = '/noc_finance.mp3';
        break;
      default:
        audioFile = '/notification.mp3';
    }

    if (audioFile) {
      const audio = new Audio(audioFile);

      audio.addEventListener('error', (e) => {
        console.error(`[Audio] Failed to load audio (${audioFile}):`, e);
        fallbackBeep();
      });

      audio.addEventListener('ended', () => {
        // Audio finished playing
      });

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          // Playback successful
        }).catch(error => {
          console.warn(`[Audio] Failed to play audio (${audioFile}):`, error);
          fallbackBeep();
        });
      } else {
        fallbackBeep();
      }
    } else {
      fallbackBeep();
    }
  } catch (error) {
    console.error('[Audio] Failed to create/play audio:', error);
    fallbackBeep();
  }
}

function fallbackBeep() {
  try {
    // console.log('[Audio] Fallback beep activated');

    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (AudioContext) {
      const context = new AudioContext();
      const oscillator = context.createOscillator();
      const gainNode = context.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(context.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.3, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);

      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.5);

      // console.log('[Audio] Fallback beep played using AudioContext');
      return;
    }
  } catch (error) {
    console.warn('[Audio] AudioContext fallback failed:', error);
  }

  try {
    const context = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    oscillator.frequency.value = 1000;
    oscillator.type = 'square';
    gainNode.gain.setValueAtTime(0.3, context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.3);

    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.3);

    // console.log('[Audio] Fallback beep played (square wave)');
  } catch (fallbackError) {
    console.warn('[Audio] All fallback methods failed:', fallbackError);
    
    try {
      let originalTitle = document.title;
      let flashInterval: NodeJS.Timeout | null = setInterval(() => {
        document.title = document.title === originalTitle ? "🔔 NOTIFIKASI BARU!" : originalTitle;
      }, 500);

      setTimeout(() => {
        clearInterval(flashInterval);
        document.title = originalTitle;
      }, 3000);
      
      // console.log('[Audio] Visual notification shown (Title flash)');
    } catch (visualError) {
      console.error('[Audio] All audio/visual methods failed:', visualError);
    }
  }
}

async function refreshTokenAndReconnect() {
  // Tambahkan limit untuk menghindari infinite refresh attempts
  const maxRetries = 3;
  const retryKey = 'ws_refresh_retries';
  const currentRetries = parseInt(sessionStorage.getItem(retryKey) || '0');

  if (currentRetries >= maxRetries) {
    console.warn('[WebSocket] Max refresh retries reached, logging out...');
    sessionStorage.removeItem(retryKey);
    authStore.logout();
    return;
  }

  sessionStorage.setItem(retryKey, (currentRetries + 1).toString());

  try {
    // console.log('[WebSocket] Attempting to refresh token...');
    const success = await authStore.refreshToken();
    if (success) {
      // Reset retry counter on success
      sessionStorage.removeItem(retryKey);
      // console.log('[WebSocket] Token refreshed, reconnecting...');
      connectWebSocket();
    } else {
      // console.log('[WebSocket] Token refresh failed, logging out...');
      sessionStorage.removeItem(retryKey);
      authStore.logout();
    }
  } catch (error) {
    console.error('[WebSocket] Token refresh error:', error);
    sessionStorage.removeItem(retryKey);
    authStore.logout();
  }
}

function connectWebSocket() {
  if (!authStore.token || (socket && socket.readyState === WebSocket.OPEN)) {
    return;
  }
  
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
  
  const token = authStore.token;
  const hostname = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  let wsUrl = '';

  if (hostname === 'billingftth.my.id') {
      wsUrl = `${protocol}//${hostname}/ws/notifications?token=${token}`;
  } else {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
      const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
      wsUrl = `${wsProtocol}//${wsHost}/ws/notifications?token=${token}`; 
  }

  // console.log(`[WebSocket] Mencoba terhubung ke ${wsUrl}`);
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    // console.log('[WebSocket] Koneksi berhasil dibuat.');

    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 30000);

    // Optimasi: kurangi frequency dan tambahkan smart checking
    let lastTokenCheck = 0;
    const TOKEN_CHECK_INTERVAL = 120000; // 2 menit (sebelumnya 1 menit)
    const TOKEN_CHECK_COOLDOWN = 30000; // 30 detik cooldown antar checks

    tokenCheckInterval = setInterval(async () => {
      const now = Date.now();

      // Jika terlalu sering cek, skip
      if (now - lastTokenCheck < TOKEN_CHECK_COOLDOWN) {
        return;
      }

      if (socket && socket.readyState === WebSocket.OPEN) {
        try {
          const isValid = await authStore.verifyToken();
          lastTokenCheck = now;

          if (!isValid) {
            console.warn('[WebSocket] Token no longer valid, attempting refresh...');
            if (tokenCheckInterval) {
              clearInterval(tokenCheckInterval);
              tokenCheckInterval = null;
            }
            await refreshTokenAndReconnect();
          }
        } catch (error) {
          console.error('[WebSocket] Token check failed:', error);
          // Jika token check gagal, anggap token invalid
          if (tokenCheckInterval) {
            clearInterval(tokenCheckInterval);
            tokenCheckInterval = null;
          }
          await refreshTokenAndReconnect();
        }
      }
    }, TOKEN_CHECK_INTERVAL);
  };

  socket.onmessage = (event) => {
    if (event.data === 'pong' || event.data === 'ping') {
      return;
    }

    try {
      if (!event.data) {
        console.warn('[WebSocket] Received empty message');
        return;
      }

      let data;
      if (typeof event.data === 'string') {
        try {
          data = JSON.parse(event.data);
        } catch (parseError) {
          console.error('[WebSocket] Gagal parse JSON:', parseError);
          console.error('[WebSocket] Raw data:', event.data);
          return;
        }
      } else {
        data = event.data;
      }
      
      if (!data || typeof data !== 'object') {
        console.warn('[WebSocket] Invalid data format received:', data);
        return;
      }

      if (data.type === 'ping' || data.type === 'pong') {
        return;
      }
      
      if (!notifications.value || !Array.isArray(notifications.value)) {
        console.warn('[WebSocket] notifications.value bukan array, inisialisasi ulang...');
        notifications.value = [];
      }
      
      if (data.action && data.action.includes('/auth/')) {
        // console.log('[WebSocket] Skipping auth-related notification:', data.action);
        return;
      }

      if (!data.id) {
        data.id = Date.now() + Math.floor(Math.random() * 10000);
        // console.log('[WebSocket] Generated ID for notification:', data.id);
      }

      const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];

      if (data.type === 'new_customer') {
        data.type = 'new_customer_for_noc';
        // console.log('[WebSocket] Normalized notification type from new_customer to new_customer_for_noc');
      }
      
      if (validTypes.includes(data.type)) {
        if (!data.timestamp) {
          data.timestamp = new Date().toISOString();
        }
        
        if (!data.message) {
          switch (data.type) {
            case 'new_payment':
              data.message = `Pembayaran baru diterima${data.data?.pelanggan_nama ? ` dari ${data.data.pelanggan_nama}` : ''}`;
              break;
            case 'new_customer_for_noc':
              data.message = `Pelanggan baru${data.data?.pelanggan_nama ? ` '${data.data.pelanggan_nama}'` : ''} telah ditambahkan`;
              break;
            case 'new_technical_data':
              data.message = `Data teknis baru${data.data?.pelanggan_nama ? ` untuk ${data.data.pelanggan_nama}` : ''} telah ditambahkan`;
              break;
            default:
              data.message = 'Notifikasi baru diterima';
          }
        }
        
        if (!data.data) {
          data.data = {};
        }
        
        if (data.type === 'new_payment' && !data.data.invoice_number) {
          // console.log('[WebSocket] Skipping new_payment notification without invoice_number');
          return;
        }
        if ((data.type === 'new_customer_for_noc' || data.type === 'new_customer') && !data.data.pelanggan_nama) {
          // console.log('[WebSocket] Skipping new_customer notification without pelanggan_nama');
          return;
        }
        if (data.type === 'new_technical_data' && !data.data.pelanggan_nama) {
          // console.log('[WebSocket] Skipping new_technical_data notification without pelanggan_nama');
          return;
        }

        notifications.value.unshift(data);

        if (notifications.value.length > 20) {
          notifications.value = notifications.value.slice(0, 20);
        }

        // console.log('[WebSocket] Notification added to list:', data.type, data.message);
        
        playSound(data.type);
        
        if (typeof window !== 'undefined' && window.dispatchEvent) {
          window.dispatchEvent(new CustomEvent('new-notification', { detail: data }));
        }
      }
      
    } catch (error) {
      console.error('[WebSocket] Gagal mem-parse pesan:', error);
      console.error('[WebSocket] Raw message:', event.data);
    }
  };

  socket.onerror = (error) => {
    console.error('[WebSocket] Terjadi error:', error);
    socket?.close();
  };

  socket.onclose = (event) => {
    console.warn(`[WebSocket] Koneksi ditutup: Kode ${event.code}`);
    socket = null;

    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    const shouldNotReconnect = [1000, 1001, 1005, 1006, 1008].includes(event.code) ||
                               event.reason === "Connection replaced" ||
                               event.reason === "Logout Pengguna" ||
                               event.reason?.includes("Invalid token") ||
                               event.reason?.includes("Token decode failed");

    // Special handling for 403 Forbidden (invalid token)
    if (event.code === 1008 || event.reason?.includes("Invalid token") || event.reason?.includes("Token decode failed")) {
      console.warn('[WebSocket] Token invalid, forcing logout...');
      // Hapus token yang invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      authStore.logout();
      router.push('/login');
      return;
    }

    if (authStore.isAuthenticated && !shouldNotReconnect) {
      if (event.code === 1008) {
        // console.log('[WebSocket] Connection closed due to token policy, attempting refresh...');
        reconnectTimeout = setTimeout(refreshTokenAndReconnect, 1000);
      } else {
        // console.log('[WebSocket] Menjadwalkan reconnect dalam 5 detik...');
        reconnectTimeout = setTimeout(connectWebSocket, 5000);
      }
    } else if (shouldNotReconnect) {
      // console.log(`[WebSocket] Tidak reconnect karena penutupan normal: ${event.reason || event.code}`);
    }
  };
}

function disconnectWebSocket() {
  // console.log('[WebSocket] Memutuskan koneksi secara manual...');
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
  if (notificationCleanupInterval) {
    clearInterval(notificationCleanupInterval);
    notificationCleanupInterval = null;
  }
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
    tokenCheckInterval = null;
  }

  if (socket) {
    socket.onclose = null;
    socket.close(1000, "Logout Pengguna");
    socket = null;
  }
}

const menuGroups = ref([
    { title: 'DASHBOARD', items: [
      { 
        title: 'Dashboard', 
        icon: 'mdi-home-variant', 
        value: 'dashboard-group', 
        permission: 'view_dashboard',
        children: [
          { title: 'Dashboard Admin', icon: 'mdi-home-variant', to: '/dashboard', permission: 'view_dashboard' },
          { title: 'Dashboard Jakinet', icon: 'mdi-account-group', to: '/dashboard-pelanggan', permission: 'view_dashboard_pelanggan' }
        ]
      },
    ] },
  
  { title: 'FTTH', items: [
      { title: 'Data Pelanggan', icon: 'mdi-account-group-outline', value: 'pelanggan', to: '/pelanggan', permission: 'view_pelanggan' },
      { title: 'Langganan', icon: 'mdi-wifi-star', value: 'langganan', to: '/langganan', badge: suspendedCount, badgeColor: 'orange', permission: 'view_langganan' },
      { title: 'Data Teknis', icon: 'mdi-database-cog-outline', value: 'teknis', to: '/data-teknis', permission: 'view_data_teknis' },
      { title: 'Brand & Paket', icon: 'mdi-tag-multiple-outline', value: 'harga', to: '/harga-layanan', permission: 'view_brand_&_paket' },
  ]},
  { title: 'LAINNYA', items: [
    { title: 'Simulasi Harga', icon: 'mdi-calculator', value: 'kalkulator', to: '/kalkulator', permission: 'view_simulasi_harga' },
    { title: 'S&K', icon: 'mdi-file-document-outline', value: 'sk', to: '/syarat-ketentuan', permission: null }
  ]},
  { title: 'SUPPORT', items: [
    { title: 'Trouble Tickets', icon: 'mdi-ticket-confirmation-outline', value: 'trouble-tickets', to: '/trouble-tickets', permission: 'view_trouble_tickets' },
    { title: 'Ticket Reports', icon: 'mdi-chart-box-outline', value: 'trouble-ticket-reports', to: '/trouble-tickets/reports', permission: 'view_trouble_tickets' },
  ]},
  { title: 'BILLING', items: [
    { title: 'Invoices', icon: 'mdi-file-document-outline', value: 'invoices', to: '/invoices', badge: 0, badgeColor: 'grey-darken-1', permission: 'view_invoices' },
    { title: 'Laporan Pendapatan', icon: 'mdi-chart-line', value: 'revenue-report', to: '/reports/revenue', permission: 'view_reports_revenue' }
  ]},
  { title: 'NETWORK MANAGEMENT', items: [
    { title: 'Mikrotik Servers', icon: 'mdi-server', value: 'mikrotik', to: '/mikrotik', permission: 'view_mikrotik_servers' },
    { title: 'OLT Management', icon: 'mdi-router-network', value: 'olt', to: '/network-management/olt', permission: 'view_olt' },
    { title: 'ODP Management', icon: 'mdi-sitemap', value: 'odp', to: '/odp-management', permission: 'view_odp_management' },
    { title: 'Manajemen Inventaris', icon: 'mdi-archive-outline', value: 'inventory', to: '/inventory', permission: 'view_inventory' }
  ]},
  { title: 'MANAGEMENT', items: [
      { title: 'Users', icon: 'mdi-account-cog-outline', value: 'users', to: '/users', badge: userCount, badgeColor: 'primary', permission: 'view_users' },
      { title: 'Roles', icon: 'mdi-shield-account-outline', value: 'roles', to: '/roles', badge: roleCount, badgeColor: 'primary', permission: 'view_roles' },
      { title: 'Permissions', icon: 'mdi-shield-key-outline', value: 'permissions', to: '/permissions', permission: 'view_permissions' },
      { title: 'Activity Log', icon: 'mdi-history', value: 'activity-logs', to: '/activity-logs', permission: 'view_activity_log' },
      { title: 'Kelola S&K', icon: 'mdi-file-edit-outline', value: 'sk-management', to: '/management/sk', permission: 'manage_sk' },
      { title: 'Pengaturan', icon: 'mdi-cog-outline', value: 'settings', to: '/management/settings', permission: 'manage_settings' }
  ]},
]);

// Key untuk memaksa re-render menu ketika permissions berubah
const menuKey = computed(() => {
  return JSON.stringify(userPermissions.value) + '-' + forceRender.value + '-' + Date.now();
});

const filteredMenuGroups = computed(() => {
  if (userPermissions.value.includes('*')) {
    return menuGroups.value;
  }

  const filtered = menuGroups.value.map(group => {
    const allowedItems = group.items.filter(item => {
      const hasPermission = !item.permission || userPermissions.value.includes(item.permission);
      return hasPermission;
    });

    return {
      ...group,
      items: allowedItems
    };
  }).filter(group => group.items.length > 0);

  return filtered;
});

onMounted(async () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) theme.change(savedTheme);

  await settingsStore.fetchMaintenanceStatus();

  if (isMobile.value) {
    drawer.value = false;
    rail.value = false;
  }

  // Update active bottom nav based on current route
  updateActiveBottomNav(route.path);

  const enableAudioContext = () => {
    // console.log('User interaction detected. Audio playback is now enabled for this session.');
    document.removeEventListener('click', enableAudioContext);
  };
  document.addEventListener('click', enableAudioContext);

  // Check if user is already authenticated
  if (authStore.isAuthenticated && authStore.user) {
    const role = authStore.user.role;
    if (role) {
      if (role.name?.toLowerCase() === 'admin') {
        userPermissions.value = ['*'];
      } else {
        userPermissions.value = role.permissions?.map((p: any) => p.name) || [];
      }
      // Force menu refresh after initial permissions set
      setTimeout(() => refreshMenu(), 50);
    }
  }

  const userIsValid = await authStore.verifyToken();

  // Force menu refresh after verification
  setTimeout(() => {
    refreshMenu();
  }, 100);

  if (userIsValid && authStore.user?.role) {
    fetchRoleCount();
    fetchUserCount();
    fetchSidebarBadges();
    fetchUnreadNotifications();
    connectWebSocket();
    
    notificationCleanupInterval = setInterval(() => {
      if (notifications.value && Array.isArray(notifications.value)) {
        const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];
        notifications.value = notifications.value.filter(notif => {
          if (notif.action && notif.action.includes('/auth/')) {
            return false;
          }
          
          if (!validTypes.includes(notif.type)) {
            return false;
          }
          
          if (notif.type === 'new_payment' && !notif.data?.invoice_number) {
            return false;
          }
          if ((notif.type === 'new_customer_for_noc' || notif.type === 'new_customer') && !notif.data?.pelanggan_nama) {
            return false;
          }
          if (notif.type === 'new_technical_data' && !notif.data?.pelanggan_nama) {
            return false;
          }
          
          return true;
        });
      }
    }, 30000);
  }
});

onUnmounted(() => {
  disconnectWebSocket();
});

function toggleTheme() {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark';
  theme.change(newTheme);
  localStorage.setItem('theme', newTheme);
}

async function fetchUnreadNotifications() {
  try {
    const response = await apiClient.get('/notifications/unread'); 
    const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];
    const filteredNotifications = response.data.notifications.filter((notif: any) => {
      if (notif.action && notif.action.includes('/auth/')) {
        return false;
      }
      
      if (!validTypes.includes(notif.type)) {
        return false;
      }
      
      if (notif.type === 'new_payment' && !notif.data?.invoice_number) {
        return false;
      }
      if ((notif.type === 'new_customer_for_noc' || notif.type === 'new_customer') && !notif.data?.pelanggan_nama) {
        return false;
      }
      if (notif.type === 'new_technical_data' && !notif.data?.pelanggan_nama) {
        return false;
      }
      
      return true;
    });
    
    notifications.value = filteredNotifications.slice(0, 20);
  } catch (error) {
    console.error("Gagal mengambil notifikasi yang belum dibaca:", error);
  }
}

function getNotificationIcon(type: string) {
  switch (type) {
    case 'new_payment': return 'mdi-cash-check';
    case 'new_customer_for_noc': return 'mdi-account-plus-outline';
    case 'new_technical_data': return 'mdi-lan-connect';
    default: return 'mdi-bell-outline';
  }
}

function getNotificationColor(type: string) {
  switch (type) {
    case 'new_payment': return 'success';
    case 'new_customer_for_noc': return 'info';
    case 'new_technical_data': return 'cyan';
    default: return 'grey';
  }
}

async function handleNotificationClick(notification: any) {
  // console.log('[Notification] handleNotificationClick called with:', notification);

  if (!notification) {
    console.error("[Notification] Invalid notification object: null or undefined");
    alert("Notifikasi tidak valid. Silakan refresh halaman.");
    return;
  }

  if (typeof notification !== 'object') {
    console.error("[Notification] Invalid notification object type:", typeof notification, notification);
    alert("Notifikasi tidak valid. Silakan refresh halaman.");
    return;
  }

  if (!notification.hasOwnProperty('id')) {
    console.error("[Notification] Notification object missing 'id' property:", notification);
    alert("Notifikasi tidak valid (missing ID). Silakan refresh halaman.");
    return;
  }

  const notificationId = notification.id;
  if (notificationId === undefined || notificationId === null || notificationId === '') {
    console.error("[Notification] Invalid notification ID:", notificationId);
    alert("Notifikasi tidak valid (invalid ID). Silakan refresh halaman.");
    return;
  }
  
  if (!notification.hasOwnProperty('type')) {
    console.warn("[Notification] Notification object missing 'type' property:", notification);
    notification.type = 'unknown';
  }

  if (notification.type === 'unknown') {
    console.warn("[Notification] Skipping unknown notification type:", notification);
    if (notifications.value && Array.isArray(notifications.value)) {
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
    }
    return;
  }

  // console.log('[Notification] Processing notification click for ID:', notificationId);

  try {
    if (!apiClient) {
      throw new Error("API client not initialized");
    }

    // console.log(`[Notification] Calling API to mark notification ${notificationId} as read`);

    await apiClient.post(`/notifications/${notificationId}/mark-as-read`);
    // console.log(`[Notification] API response for marking ${notificationId} as read:`);

    if (notifications.value && Array.isArray(notifications.value)) {
      // console.log(`[Notification] Removing notification ${notificationId} from frontend list`);
      notifications.value = notifications.value.filter(n => {
        const match = n.id !== notificationId;
        // console.log(`[Notification] Filter check - comparing ${n.id} !== ${notificationId} = ${match}`);
        return match;
      });
      // console.log(`[Notification] Updated notifications list length: ${notifications.value.length}`);
    } else {
      console.warn("[Notification] notifications.value bukan array:", notifications.value);
      notifications.value = [];
    }

    // console.log(`[Notification] Redirecting based on type: ${notification.type}`);
    
    if (notification.type === 'unknown') {
      // console.log("[Notification] No redirect for unknown notification type");
      return;
    }

    if (notification.type === 'new_technical_data') {
      // console.log("[Notification] Redirecting to /langganan");
      router.push('/langganan');
    } else if (notification.type === 'new_customer_for_noc' || notification.type === 'new_customer') {
      // console.log("[Notification] Redirecting to /data-teknis");
      router.push('/data-teknis');
    } else if (notification.type === 'new_payment') {
      // console.log("[Notification] Redirecting to /invoices");
      router.push('/invoices');
    } else {
      console.warn("[Notification] Unknown notification type, redirecting to home:", notification.type);
      router.push('/');
    }

  } catch (error) {
    console.error("[Notification] Gagal menandai notifikasi sebagai sudah dibaca:", error);
    
    if (error instanceof Error) {
      const errorMessage = error.message.toLowerCase();
      if (errorMessage.includes('404') || errorMessage.includes('not found')) {
        console.warn("[Notification] Notifikasi tidak ditemukan di server, hapus dari daftar lokal");
        if (notifications.value && Array.isArray(notifications.value)) {
          notifications.value = notifications.value.filter(n => n.id !== notificationId);
        }
        if (notification.type === 'new_technical_data') {
          router.push('/langganan');
        } else if (notification.type === 'new_customer_for_noc' || notification.type === 'new_customer') {
          router.push('/data-teknis');
        } else if (notification.type === 'new_payment') {
          router.push('/invoices');
        } else {
          router.push('/');
        }
      } else {
        alert(`Gagal menandai notifikasi sebagai sudah dibaca: ${error.message}`);
      }
    } else {
      alert("Gagal menandai notifikasi sebagai sudah dibaca. Silakan coba lagi.");
    }
  }
}

async function markAllAsRead() {
  try {
    if (!apiClient) {
      throw new Error("API client not initialized");
    }
    
    const response = await apiClient.post('/notifications/mark-all-as-read'); 
    
    if (response && response.status === 200) {
      if (notifications.value && Array.isArray(notifications.value)) {
        notifications.value = [];
      } else {
        console.warn("[Notification] notifications.value bukan array, inisialisasi ulang...");
        notifications.value = [];
      }
      
      // console.log("[Notification] Semua notifikasi telah ditandai sebagai sudah dibaca");
    } else {
      throw new Error(`Unexpected response status: ${response.status}`);
    }
    
  } catch (error) {
    console.error("[Notification] Gagal membersihkan notifikasi:", error);
    
    if (error instanceof Error) {
      alert(`Gagal membersihkan notifikasi: ${error.message}`);
    } else {
      alert("Gagal membersihkan notifikasi. Silakan coba lagi.");
    }
    
    console.warn("[Notification] Fallback ke penghapusan lokal...");
    if (notifications.value && Array.isArray(notifications.value)) {
      notifications.value = [];
    } else {
      notifications.value = [];
    }
  }
}

async function fetchRoleCount() {
  try {
    const response = await apiClient.get('/roles/');
    roleCount.value = response.data.length;
  } catch (error) {
    console.error("Gagal mengambil jumlah roles:", error);
  }
}

async function fetchUserCount() {
  try {
    const response = await apiClient.get('/users/');
    userCount.value = response.data.length;
  } catch (error) {
    console.error("Gagal mengambil jumlah users:", error);
  }
}

function handleLogout() {
  disconnectWebSocket();
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
/* LIGHT THEME */
.modern-app {
  background-color: rgb(var(--v-theme-background));
  transition: background-color 0.3s ease;
}

.notification-content {
  cursor: pointer;
}

.nav-sub-item {
  border-radius: 10px;
  margin-bottom: 4px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  min-height: 44px;
  transition: all 0.3s ease;
  padding-left: 16px !important;
  margin-left: -8px;
}

.nav-sub-item .v-list-item-title {
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-sub-item:not(.v-list-item--active):hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

.v-list-group .v-list-item {
  padding-inline-start: 16px !important;
}

.nav-sub-item.v-list-item {
  padding-inline-start: 16px !important;
  margin-inline-start: 0 !important;
}

.modern-drawer {
  border-right: none;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.08);
  overflow: hidden !important;
  transition: all 0.3s ease;
}

.modern-drawer :deep(.v-navigation-drawer__content) {
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notification-item .v-list-item-subtitle {
  white-space: normal !important;
  line-height: 1.4;
  -webkit-line-clamp: 2; 
  line-clamp: 2;
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-item.v-list-item {
  min-height: 60px !important;
  height: auto !important;
  align-items: center;
}

.sidebar-header {
  height: 65px;
  padding: 0 11.5px !important;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  transition: border-color 0.3s ease;
}

.header-flex-container {
  display: flex;
  align-items: center;
  width: 100%;
}

.sidebar-logo-full {
  height: 45px;
  margin-right: 12px;
  flex-shrink: 0;
  filter: brightness(1);
  transition: filter 0.3s ease;
}

.v-theme--dark .sidebar-logo-full {
  filter: brightness(1.2) contrast(1.1);
}

.sidebar-title-wrapper {
  overflow: hidden;
  white-space: nowrap;
}

.sidebar-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
  margin-bottom: 2px;
  transition: color 0.3s ease;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: color 0.3s ease;
}

.navigation-wrapper {
  flex: 2;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.navigation-wrapper::-webkit-scrollbar {
  display: none;
}

.navigation-menu {
  padding: 0 16px;
}

.menu-subheader {
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.6) !important;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-top: 20px;
  margin-bottom: 8px;
  padding: 0 16px;
  transition: color 0.3s ease;
}

.nav-item {
  border-radius: 10px;
  margin-bottom: 4px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  min-height: 44px;
  transition: all 0.3s ease;
}

.nav-item .v-list-item-title {
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-item:not(.v-list-item--active):hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

.v-list-item--active {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  color: white !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.v-list-item--active .v-list-item-title {
  font-weight: 600;
}

.badge-chip {
  font-size: 0.7rem;
  height: 20px;
  font-weight: 600;
  border-radius: 10px;
}

.v-list-item--active .badge-chip {
  color: white !important;
}

.logout-section {
  flex-shrink: 0;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface), 0.5);
  transition: all 0.3s ease;
}

.logout-btn {
  border-radius: 10px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: normal;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background-color: #ef4444 !important;
  color: white !important;
}

.modern-app-bar {
  background: rgb(var(--v-theme-surface)) !important;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.header-action-btn {
  color: rgba(var(--v-theme-on-surface), 0.8);
  transition: all 0.3s ease;
}

.header-action-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.theme-toggle-btn:hover {
  background-color: rgba(var(--v-theme-warning), 0.1) !important;
  color: rgb(var(--v-theme-warning)) !important;
}

.modern-main {
  background-color: rgb(var(--v-theme-background));
  transition: background-color 0.3s ease;
}

/* Add padding bottom for mobile to accommodate bottom nav */
.modern-main.with-bottom-nav {
  padding-bottom: 65px !important;
}

/* Bottom Navigation Styles */
.mobile-bottom-nav {
  position: fixed !important;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgb(var(--v-theme-surface)) !important;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
}

.mobile-bottom-nav :deep(.v-btn) {
  height: 65px !important;
  flex-direction: column;
  gap: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: none;
  letter-spacing: normal;
}

.mobile-bottom-nav :deep(.v-btn .v-icon) {
  font-size: 24px;
  margin-bottom: 2px;
}

.mobile-bottom-nav :deep(.v-btn--active) {
  color: rgb(var(--v-theme-primary)) !important;
}

.mobile-bottom-nav :deep(.v-btn--active .v-icon) {
  color: rgb(var(--v-theme-primary)) !important;
}

.mobile-bottom-nav :deep(.v-badge__badge) {
  font-size: 0.65rem;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
}

.maintenance-banner {
  height: 50px !important; 
  font-size: 2rem !important; 
  font-weight: 600;
  justify-content: center; 
}

.footer-responsive {
  padding: 0 1rem;
}

.footer-content {
  text-align: center;
  font-size: 0.85rem;
  line-height: 1.4;
}

/* DARK THEME SPECIFIC STYLES */
.v-theme--dark .modern-app {
  background-color: #0f172a;
}

.v-theme--dark .modern-drawer {
  background: #1e293b;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .sidebar-header {
  border-bottom: 1px solid #334155;
}

.v-theme--dark .modern-app-bar {
  background: #1e293b !important;
  border-bottom: 1px solid #334155;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.v-theme--dark .logout-section {
  background: #0f1629;
  border-top: 1px solid #334155;
}

.v-theme--dark .nav-item:not(.v-list-item--active):hover {
  background-color: rgba(129, 140, 248, 0.15);
}

.v-theme--dark .mobile-bottom-nav {
  background: #1e293b !important;
  border-top: 1px solid #334155;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .modern-drawer {
    width: 280px !important;
  }
  
  .sidebar-title {
    font-size: 1.15rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.7rem;
  }
  
  .nav-item {
    min-height: 48px;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.9rem;
  }
  
  .menu-subheader {
    font-size: 0.68rem;
  }
  
  .footer-content {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .modern-drawer {
    width: 260px !important;
  }
  
  .sidebar-logo-full {
    height: 40px;
  }
  
  .sidebar-title {
    font-size: 1.1rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.65rem;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.85rem;
  }
  
  .menu-subheader {
    font-size: 0.65rem;
  }
  
  .footer-content {
    font-size: 0.75rem;
    padding: 0.5rem 0;
  }

  .mobile-bottom-nav :deep(.v-btn) {
    font-size: 0.65rem;
  }

  .mobile-bottom-nav :deep(.v-btn .v-icon) {
    font-size: 22px;
  }
}

@media (max-width: 360px) {
  .modern-drawer {
    width: 240px !important;
  }
  
  .sidebar-logo-full {
    height: 35px;
  }
  
  .sidebar-title {
    font-size: 1rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.6rem;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.8rem;
  }
  
  .footer-content {
    font-size: 0.7rem;
  }

  .mobile-bottom-nav :deep(.v-btn) {
    font-size: 0.6rem;
    gap: 2px;
  }

  .mobile-bottom-nav :deep(.v-btn .v-icon) {
    font-size: 20px;
  }
}
</style>