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
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail && !isMobile"
      :temporary="isMobile"
      :permanent="!isMobile"
      class="modern-drawer"
      :width="isMobile ? '280' : '280'"
    >
      <v-list-item class="sidebar-header" :class="{'px-0': rail && !isMobile}" :ripple="false">
        <div class="header-flex-container">
          <img v-if="!rail || isMobile" :src="logoSrc" alt="Jelantik Logo" class="sidebar-logo-full"/>
          
          <v-icon v-if="rail && !isMobile" color="primary" size="large">mdi-alpha-j</v-icon>

          <div v-if="!rail || isMobile" class="sidebar-title-wrapper">
            <h1 class="sidebar-title">Artacom Ftth</h1>
            <span class="sidebar-subtitle">PORTAL CUSTOMER V2.5</span>
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

      <div class="navigation-wrapper">
  <v-list nav class="navigation-menu">
    <template v-for="group in filteredMenuGroups" :key="group.title">
      <v-list-subheader v-if="!rail || isMobile" class="menu-subheader">{{ group.title }}</v-list-subheader>
      
      <template v-for="item in group.items" :key="item.title">
        <v-list-group 
          v-if="'children' in item"
          :value="item.value"
        >
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              :prepend-icon="item.icon"
              :title="item.title"
              class="nav-item"
            ></v-list-item>
          </template>

              <v-list-item
          v-for="subItem in item.children"
          :key="subItem.title"
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
                <strong>{{ notif.data.invoice_number }}</strong> dari <strong>{{ notif.data.pelanggan_nama }}</strong> telah lunas.
              </v-list-item-subtitle>
            </div>

            <div v-if="notif.type === 'new_customer_for_noc'" class="notification-content">
              <v-list-item-title class="font-weight-medium text-body-2">Pelanggan Baru</v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                <strong>{{ notif.data.pelanggan_nama }}</strong> perlu dibuatkan Data Teknis.
              </v-list-item-subtitle>
            </div>

          <div v-if="notif.type === 'new_technical_data'" class="notification-content">
            <v-list-item-title class="font-weight-medium text-body-2">Data Teknis Baru</v-list-item-title>
            <v-list-item-subtitle class="text-caption">
              Data teknis untuk <strong>{{ notif.data.pelanggan_nama }}</strong> telah ditambahkan.
            </v-list-item-subtitle>
            </div>

          </v-list-item>
          </v-list>
      </v-menu>
    </v-app-bar>

    <v-main class="modern-main">
      <router-view></router-view>
    </v-main>
    
    <v-footer app height="69px" class="d-flex align-center justify-center text-medium-emphasis footer-responsive" style="border-top: 1px solid rgba(0,0,0,0.08);">
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
import { useRouter } from 'vue-router';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import logoLight from '@/assets/images/Jelantik-Light.webp';
import logoDark from '@/assets/images/Jelantik-Dark.webp';
import { useTheme } from 'vuetify';
import { useDisplay } from 'vuetify';
import apiClient from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import { useSettingsStore } from '@/stores/settings';

// --- State ---
const theme = useTheme();
const { mobile } = useDisplay();
const drawer = ref(true);
const rail = ref(false);
const router = useRouter();
const notifications = ref<any[]>([]);
const suspendedCount = ref(0);
const unpaidInvoiceCount = ref(0);
const stoppedCount = ref(0);
const userCount = ref(0);
const roleCount = ref(0);
const userPermissions = ref<string[]>([]);
const authStore = useAuthStore();
let socket: WebSocket | null = null;
// let reconnectInterval: NodeJS.Timeout | null = null;

// Computed untuk mobile detection
const isMobile = computed(() => mobile.value);
const logoSrc = computed(() => theme.global.current.value.dark ? logoDark : logoLight);
const settingsStore = useSettingsStore();

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
    stoppedCount.value = response.data.stopped_count; // <-- Ambil data baru
  } catch (error) {
    console.error("Gagal mengambil data badge sidebar:", error);
  }
}

// --- Fungsi WebSocket yang Diperbaiki ---
// function connectWebSocket() {
//   if (!authStore.token) return;
//   if (socket && socket.readyState === WebSocket.OPEN) return;

//   // Untuk development (localhost)
//   if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
//     const wsUrl = `ws://127.0.0.1:8000/ws/notifications?token=${authStore.token}`;
//     console.log(`Connecting to WebSocket at ${wsUrl}`);
//     socket = new WebSocket(wsUrl);
//   } else {
//     // Untuk production - gunakan wss dengan domain yang sama
//     const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
//     const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications?token=${authStore.token}`;
//     console.log(`Connecting to WebSocket at ${wsUrl}`);
//     socket = new WebSocket(wsUrl);
//   }

//   socket.onopen = () => {
//     console.log('WebSocket connection established.');
//     // Clear reconnect interval jika berhasil
//     if (reconnectInterval) {
//       clearInterval(reconnectInterval);
//       reconnectInterval = null;
//     }
//   };

// //   function playSound(type: string) {
// //   let audioFile = '';

// //   if (type === 'new_payment') {
// //     audioFile = '/pembayaran.mp3'; // Suara baru untuk pembayaran
// //   } else if (type === 'new_customer_for_noc') {
// //     audioFile = '/payment.mp3'; // Suara lama untuk pelanggan baru
// //   }

// //   if (audioFile) {
// //     const audio = new Audio(audioFile);
// //     audio.play().catch(error => {
// //       console.error(`Gagal memutar audio (${audioFile}):`, error);
// //     });
// //   }
// // }

// function playSound(type: string) {
//   let audioFile = '';
//   if (type === 'new_payment') {
//     audioFile = '/pembayaran.mp3';
//   } else if (type === 'new_customer_for_noc') {
//     audioFile = '/payment.mp3';
//   } else if (type === 'new_technical_data') {
//     audioFile = '/langganan.mp3';
//   }

//   if (audioFile) {
//     const audio = new Audio(audioFile);
//     audio.play().catch(error => {
//       console.warn(`Gagal memutar audio (${audioFile}):`, error);
//     });
//   }
// }

// socket.onmessage = (event) => {
//   // Log 1: Lihat data mentah yang diterima
//   console.log('--- RAW MESSAGE RECEIVED ---', event.data); 
  
//   try {
//     const data = JSON.parse(event.data);

//     // Log 2: Lihat data setelah di-parse menjadi objek
//     console.log('--- PARSED DATA OBJECT ---', data); 
    
//     const notificationType = data.type;

//     if (['new_payment', 'new_technical_data', 'new_customer_for_noc'].includes(notificationType)) {
//       // Log 3: Konfirmasi tipe notifikasi cocok
//       console.log('--- NOTIFICATION TYPE MATCHED ---', notificationType); 
      
//       notifications.value = [data, ...notifications.value];
//       playSound(notificationType);
      
//       // Log 4: Lihat isi array notifikasi setelah di-update
//       console.log('--- UPDATED NOTIFICATIONS ARRAY ---', notifications.value); 
      
//       const customEvent = new CustomEvent('new-notification', { detail: data });
//       window.dispatchEvent(customEvent);

//     } else {
//       // Log 5: Jika tipe notifikasi tidak cocok
//       console.log('--- NOTIFICATION TYPE MISMATCH ---', notificationType); 
//     }
//   } catch (error) {
//     console.error('Error parsing WebSocket message:', error);
//   }
// };

//   socket.onerror = (error) => {
//     console.error('WebSocket error:', error);
//   };

//   socket.onclose = (event) => {
//     console.log('WebSocket closed:', event.code, event.reason);
    
//     // Hanya reconnect jika user masih authenticated dan bukan intentional close
//     if (authStore.isAuthenticated && event.code !== 1000) {
//       console.log('WebSocket closed unexpectedly. Attempting to reconnect...');
//       if (!reconnectInterval) {
//         reconnectInterval = setInterval(() => {
//           if (authStore.isAuthenticated) {
//             connectWebSocket();
//           } else {
//             disconnectWebSocket();
//           }
//         }, 5000);
//       }
//     }
//   };
// }

let pingInterval: NodeJS.Timeout | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;

function playSound(type: string) {
  let audioFile = '';
  if (type === 'new_payment') {
    audioFile = '/pembayaran.mp3';
  } else if (type === 'new_customer_for_noc') {
    audioFile = '/payment.mp3';
  } else if (type === 'new_technical_data') {
    audioFile = '/noc_finance.mp3';
  }

  if (audioFile) {
    const audio = new Audio(audioFile);
    audio.play().catch(error => {
      console.warn(`Gagal memutar audio (${audioFile}):`, error);
    });
  }
}

function connectWebSocket() {
  // 1. Hentikan jika sudah ada koneksi atau tidak ada token
  if (!authStore.token || (socket && socket.readyState === WebSocket.OPEN)) {
    return;
  }
  
  // Hentikan timer reconnect yang mungkin sedang berjalan
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
  
  const token = authStore.token;
  const hostname = window.location.hostname;
  let wsUrl = '';

  // 2. Tentukan URL berdasarkan lingkungan (produksi atau development)
  if (hostname === 'billingftth.my.id') {
      // Produksi (Sudah Benar)
      wsUrl = `wss://${hostname}/api/ws/notifications?token=${token}`;
  } else {
      // Lokal (Perbaiki di sini, hapus /api)
      wsUrl = `ws://localhost:8000/ws/notifications?token=${token}`; 
  }

  // 3. Buat koneksi dengan URL yang sudah pasti benar
  console.log(`[WebSocket] Mencoba terhubung ke ${wsUrl}`);
  socket = new WebSocket(wsUrl);

  // --- Sisa event handler (onopen, onmessage, dll.) bisa tetap sama ---
  socket.onopen = () => {
    console.log('[WebSocket] Koneksi berhasil dibuat.');
    if (pingInterval) clearInterval(pingInterval);
    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 30000);
  };

  socket.onmessage = (event) => {
    if (event.data === 'pong') return;
    
    console.log('[WebSocket] Pesan diterima:', event.data);
    try {
      const data = JSON.parse(event.data); // 'data' di sini adalah objek notifikasi tunggal
      if (['new_payment', 'new_technical_data', 'new_customer_for_noc'].includes(data.type)) {
        notifications.value = [data, ...notifications.value];
        playSound(data.type);
        window.dispatchEvent(new CustomEvent('new-notification', { detail: data }));
      }
    } catch (error) {
      console.error('[WebSocket] Gagal mem-parse pesan:', error);
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
    
    if (authStore.isAuthenticated && event.code !== 1000) {
      console.log('[WebSocket] Menjadwalkan reconnect dalam 5 detik...');
      reconnectTimeout = setTimeout(connectWebSocket, 5000);
    }
  };
}

function disconnectWebSocket() {
  console.log('[WebSocket] Memutuskan koneksi secara manual...');
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
  if (pingInterval) clearInterval(pingInterval);

  if (socket) {
    socket.onclose = null; // Hapus listener onclose agar tidak memicu reconnect
    socket.close(1000, "Logout Pengguna");
    socket = null;
  }
}
// --- AKHIR BLOK KODE WEBSOCKET ---


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
    { title: 'S&K', icon: 'mdi-file-document-outline', value: 'sk', to: '/syarat-ketentuan', permission: null } // <-- Tambahkan ini
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

const filteredMenuGroups = computed(() => {
  if (userPermissions.value.includes('*')) return menuGroups.value;
  return menuGroups.value.map(group => ({
    ...group,
    items: group.items.filter(item => !item.permission || userPermissions.value.includes(item.permission)),
  })).filter(group => group.items.length > 0);
});



onMounted(async () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) theme.global.name.value = savedTheme;


  await settingsStore.fetchMaintenanceStatus(); 

  // Set drawer behavior based on screen size
  if (isMobile.value) {
    drawer.value = false;
    rail.value = false;
  }

  const enableAudioContext = () => {
    // Fungsi ini akan dijalankan sekali saat user mengklik
    // dan setelah itu listener-nya akan dihapus.
    console.log('User interaction detected. Audio playback is now enabled for this session.');
    document.removeEventListener('click', enableAudioContext);
  };
  document.addEventListener('click', enableAudioContext);
  
  const userIsValid = await authStore.verifyToken();
  if (userIsValid && authStore.user?.role) {
    const role = authStore.user.role;
    if (typeof role === 'object' && role !== null && role.name) {
      if (role.name.toLowerCase() === 'admin') userPermissions.value = ['*'];
      else userPermissions.value = role.permissions?.map((p: any) => p.name) || [];
    }
    fetchRoleCount();
    fetchUserCount();
    // fetchSuspendedCount();
    fetchSidebarBadges();
    fetchUnreadNotifications(); // <-- PANGGIL FUNGSI UNTUK MENGAMBIL NOTIFIKASI
    connectWebSocket(); // Memulai WebSocket setelah user terverifikasi
  }
});

onUnmounted(() => {
  disconnectWebSocket();
});

onUnmounted(() => disconnectWebSocket());

function toggleTheme() {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark';
  theme.global.name.value = newTheme;
  localStorage.setItem('theme', newTheme);
}

// --- FUNGSI BARU UNTUK MENGAMBIL NOTIFIKASI DARI DATABASE ---
async function fetchUnreadNotifications() {
  try {
    // Ganti dengan endpoint API Anda yang sebenarnya
    const response = await apiClient.get('/notifications/unread'); 
    notifications.value = response.data;
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
  // 1. Tandai notifikasi sebagai sudah dibaca di backend
  try {
    // Ganti dengan endpoint API Anda
    await apiClient.post(`/notifications/${notification.id}/mark-as-read`); 
    
    // 2. Hapus notifikasi dari daftar di frontend secara visual
    notifications.value = notifications.value.filter(n => n.id !== notification.id);

    // 3. Arahkan pengguna ke halaman yang relevan
    if (notification.type === 'new_technical_data') {
      router.push('/langganan');
    } else if (notification.type === 'new_customer_for_noc') {
      router.push('/data-teknis');
    } else if (notification.type === 'new_payment') {
      // Mungkin arahkan ke detail invoice jika ada ID-nya
      router.push('/invoices');
    }

  } catch (error) {
    console.error("Gagal menandai notifikasi sebagai sudah dibaca:", error);
  }
}

async function markAllAsRead() {
  try {
    // Ganti dengan endpoint API Anda
    await apiClient.post('/notifications/mark-all-as-read'); 
    notifications.value = []; // Kosongkan daftar di frontend
  } catch (error) {
    console.error("Gagal membersihkan notifikasi:", error);
  }
}



// async function fetchSuspendedCount() {
//   try {
//     const response = await apiClient.get('/langganan?status=Ditangguhkan');
//     suspendedCount.value = response.data.length;
//   } catch (error) {
//     console.error("Gagal mengambil jumlah langganan yang ditangguhkan:", error);
//   }
// }

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
  /* Mengurangi padding kiri untuk menyelaraskan dengan parent */
  padding-left: 16px !important;
  /* Atau gunakan margin-left negatif untuk menarik ke kiri */
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

/* Alternatif lain - override Vuetify's default indentation */
.v-list-group .v-list-item {
  padding-inline-start: 16px !important;
}

/* Atau gunakan custom class untuk lebih spesifik */
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
  white-space: normal !important;      /* Izinkan teks untuk wrap ke baris baru */
  line-height: 1.4;                  /* Perbaiki jarak antar baris agar mudah dibaca */
  -webkit-line-clamp: 2; 
  line-clamp: 2;              /* Batasi teks hingga 2 baris */
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-item.v-list-item {
  min-height: 60px !important;         /* Beri tinggi minimal untuk menampung 2 baris */
  height: auto !important;             /* Biarkan tinggi item menyesuaikan konten */
  align-items: center;               /* Posisikan avatar dan teks di tengah */
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

/* Dark mode logo adjustment */
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
  /* Hapus 'color: white;' dari sini agar warna default Vuetify berlaku */
}

/* Tambahkan aturan baru ini */
.v-list-item--active .badge-chip {
  color: white !important; /* Jadikan warna teks putih HANYA saat item aktif */
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

.maintenance-banner {
  /* Memperbesar tinggi banner */
  height: 50px !important; 
  
  /* Memperbesar ukuran font */
  font-size: 2rem !important; 
  
  /* Membuat teks sedikit lebih tebal */
  font-weight: 600;

  /* Memastikan konten berada di tengah secara horizontal */
  justify-content: center; 
}

/* Footer responsive */
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
}
</style>