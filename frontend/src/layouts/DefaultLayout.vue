<template>
  <v-app class="modern-app">
    <!-- Maintenance Banner -->
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
      class="modern-drawer elevation-3"
      :width="isMobile ? '300' : '300'"
      :key="forceRender"
    >
      <!-- Header Section -->
      <div class="sidebar-header-modern" :class="{'rail-mode': rail && !isMobile}">
        <div class="header-content">
          <!-- Logo -->
          <div class="logo-wrapper" @click="handleLogoClick">
            <img
              v-if="!rail || isMobile"
              :src="logoSrc"
              alt="Jelantik Logo"
              class="sidebar-logo"
            />
            <v-avatar v-else color="primary" size="40">
              <span class="text-h6 font-weight-bold">J</span>
            </v-avatar>
          </div>

          <!-- Title -->
          <div v-if="!rail || isMobile" class="title-wrapper">
            <h1 class="app-title">Artacom Ftth</h1>
            <p class="app-subtitle">Portal Customer V3</p>
          </div>

          <!-- Toggle Button -->
          <v-btn
            v-if="!isMobile"
            variant="text"
            size="small"
            class="toggle-btn"
            @click.stop="rail = !rail"
          ></v-btn>
          
          <v-btn
            v-if="isMobile"
            icon="mdi-close"
            variant="text"
            size="small"
            class="close-btn"
            @click.stop="drawer = false"
          ></v-btn>
        </div>
      </div>

      <v-divider class="my-2"></v-divider>

      <!-- Navigation Menu -->
      <div class="navigation-container" :key="'nav-wrapper-' + forceRender">
        <v-list nav class="navigation-list" :key="menuKey">
          <template v-for="group in filteredMenuGroups" :key="group.title + '-' + menuKey">
            <!-- Group Header -->
            <div 
              v-if="!rail || isMobile" 
              class="menu-group-header"
              :key="'header-' + group.title"
            >
              <span class="group-title">{{ group.title }}</span>
              <v-divider class="group-divider"></v-divider>
            </div>

            <!-- Menu Items -->
            <template v-for="item in group.items" :key="item.value + '-' + forceRender">
              <!-- Item with Children (Expandable) -->
              <v-list-group
                v-if="'children' in item"
                :value="item.value"
                :key="'group-' + item.value"
                class="menu-group"
              >
                <template v-slot:activator="{ props }">
                  <v-list-item
                    v-bind="props"
                    :prepend-icon="item.icon"
                    class="menu-item parent-item"
                    :key="'activator-' + item.value"
                  >
                    <v-list-item-title class="item-title">
                      {{ item.title }}
                    </v-list-item-title>
                  </v-list-item>
                </template>

                <!-- Sub Items -->
                <v-list-item
                  v-for="subItem in item.children"
                  :key="subItem.value + '-sub'"
                  :title="subItem.title"
                  :to="subItem.to"
                  :prepend-icon="subItem.icon"
                  class="menu-item sub-item"
                >
                </v-list-item>
              </v-list-group>

              <!-- Single Item -->
              <v-list-item
                v-else
                :prepend-icon="item.icon"
                :value="item.value"
                :to="item.to"
                class="menu-item single-item"
                :key="'item-' + item.value"
              >
                <v-list-item-title class="item-title">
                  {{ item.title }}
                </v-list-item-title>

                <!-- Badges -->
                <template v-slot:append>
                  <div class="badges-wrapper">
                    <v-tooltip location="top" v-if="item.value === 'langganan' && suspendedCount > 0">
                      <template v-slot:activator="{ props }">
                        <v-badge
                          color="error"
                          :content="suspendedCount"
                          inline
                          v-bind="props"
                          class="badge-item"
                        ></v-badge>
                      </template>
                      <span>{{ suspendedCount }} langganan berstatus "Suspended"</span>
                    </v-tooltip>

                    <v-tooltip location="top" v-if="item.value === 'langganan' && stoppedCount > 0">
                      <template v-slot:activator="{ props }">
                        <v-badge
                          color="grey"
                          :content="stoppedCount"
                          inline
                          v-bind="props"
                          class="badge-item ms-1"
                        ></v-badge>
                      </template>
                      <span>{{ stoppedCount }} langganan berstatus "Berhenti"</span>
                    </v-tooltip>

                    <v-tooltip location="top" v-if="item.value === 'invoices' && unpaidInvoiceCount > 0">
                      <template v-slot:activator="{ props }">
                        <v-badge
                          color="warning"
                          :content="unpaidInvoiceCount"
                          inline
                          v-bind="props"
                          class="badge-item"
                        ></v-badge>
                      </template>
                      <span>{{ unpaidInvoiceCount }} invoice belum dibayar</span>
                    </v-tooltip>
                  </div>
                </template>
              </v-list-item>
            </template>
          </template>
        </v-list>
      </div>

      <!-- Logout Section -->
      <template v-slot:append>
        <div class="logout-container">
          <v-divider class="mb-1"></v-divider>
          <v-btn
            :block="!rail || isMobile"
            variant="flat"
            color="error"
            class="logout-btn"
            :icon="rail && !isMobile"
            @click="handleLogout"
          >
            <v-icon :start="!rail || isMobile">mdi-logout</v-icon>
            <span v-if="!rail || isMobile">Logout</span>
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
        class="menu-toggle"
      ></v-btn>

      <v-toolbar-title class="app-bar-title" v-if="!isMobile">
        <span class="text-h6 font-weight-medium">{{ currentPageTitle }}</span>
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <!-- Theme Toggle -->
      <v-btn 
        icon 
        variant="text" 
        @click="toggleTheme" 
        class="header-icon-btn"
      >
        <v-icon>
          {{ theme.global.current.value.dark ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}
        </v-icon>
      </v-btn>

      <!-- Notifications -->
      <v-menu offset-y max-width="400">
        <template v-slot:activator="{ props }">
          <v-btn 
            icon 
            variant="text" 
            class="header-icon-btn" 
            v-bind="props"
          >
            <v-badge 
              :content="notifications.length" 
              color="error" 
              :model-value="notifications.length > 0"
              overlap
            >
              <v-icon>mdi-bell-outline</v-icon>
            </v-badge>
          </v-btn>
        </template>

        <!-- Modern Notification Card -->
        <div class="modern-notification-container">
          <div class="notification-header-section">
            <div class="d-flex align-center">
              <v-icon class="me-3" color="primary" size="24">mdi-bell-ring</v-icon>
              <div>
                <div class="notification-main-title">Notifikasi</div>
                <div class="notification-subtitle text-caption">
                  {{ notifications.length }} {{ notifications.length === 0 ? 'Tidak ada notifikasi baru' : 'notifikasi baru' }}
                </div>
              </div>
            </div>
            <v-btn
              v-if="notifications.length > 0"
              variant="text"
              size="small"
              color="primary"
              @click="markAllAsRead"
              class="text-none"
            >
              <v-icon size="16" class="me-1">mdi-check-all</v-icon>
              Baca semua
            </v-btn>
          </div>

          <v-divider class="notification-divider"></v-divider>

          <div class="notification-list-section">
            <!-- Empty State -->
            <div v-if="notifications.length === 0" class="empty-notification-state">
              <div class="empty-notification-icon">
                <v-icon size="64" color="grey-lighten-2">mdi-bell-off-outline</v-icon>
                <v-icon size="64" color="grey-lighten-3" class="icon-background">mdi-bell</v-icon>
              </div>
              <div class="empty-notification-text">
                <div class="empty-title">Tenang</div>
                <div class="empty-subtitle">Tidak ada notifikasi baru untuk Anda</div>
              </div>
            </div>

            <!-- Notification Items -->
            <div v-else class="notification-items-container">
              <div
                v-for="(notif, index) in notifications"
                :key="index"
                class="modern-notification-item"
                @click="handleNotificationClick(notif)"
                :class="{ 'notification-item-unread': !notif.read }"
              >
                <div class="notification-content">
                  <div class="notification-avatar-container">
                    <div class="notification-avatar" :class="`avatar-${getNotificationColor(notif.type)}`">
                      <v-icon size="20" color="white">
                        {{ getNotificationIcon(notif.type) }}
                      </v-icon>
                    </div>
                    <div v-if="!notif.read" class="notification-dot"></div>
                  </div>

                  <div class="notification-message">
                    <div class="notification-type">
                      <span class="notification-label" :class="`label-${getNotificationColor(notif.type)}`">
                        {{ getNotificationTitle(notif.type) }}
                      </span>
                      <span class="notification-time">
                        {{ formatNotificationTime(notif.created_at) }}
                      </span>
                    </div>
                    <div class="notification-description">
                      {{ getNotificationMessage(notif) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-menu>
    </v-app-bar>

    <!-- Main Content -->
    <v-main class="modern-main" :class="{ 'with-bottom-nav': isMobile }">
      <router-view></router-view>
    </v-main>

    <!-- Bottom Navigation (Mobile) -->
    <v-bottom-navigation
      v-if="isMobile"
      v-model="activeBottomNav"
      class="mobile-bottom-nav"
      grow
      elevation="8"
      height="65"
      bg-color="surface"
    >
      <v-btn value="dashboard" @click="navigateTo('/dashboard')">
        <v-icon>mdi-view-dashboard</v-icon>
        <span>Dashboard</span>
      </v-btn>

      <v-btn value="pelanggan" @click="navigateTo('/pelanggan')">
        <v-icon>mdi-account-group</v-icon>
        <span>Pelanggan</span>
      </v-btn>

      <v-btn value="langganan" @click="navigateTo('/langganan')">
        <v-badge
          v-if="suspendedCount > 0 || stoppedCount > 0"
          :content="suspendedCount + stoppedCount"
          color="error"
          overlap
        >
          <v-icon>mdi-wifi</v-icon>
        </v-badge>
        <v-icon v-else>mdi-wifi</v-icon>
        <span>Langganan</span>
      </v-btn>

      <v-btn value="trouble-tickets" @click="navigateTo('/trouble-tickets')">
        <v-badge
          v-if="openTicketsCount > 0"
          :content="openTicketsCount"
          color="warning"
          overlap
        >
          <v-icon>mdi-ticket</v-icon>
        </v-badge>
        <v-icon v-else>mdi-ticket</v-icon>
        <span>Tickets</span>
      </v-btn>

      <v-btn value="invoices" @click="navigateTo('/invoices')">
        <v-badge
          v-if="unpaidInvoiceCount > 0"
          :content="unpaidInvoiceCount"
          color="orange"
          overlap
        >
          <v-icon>mdi-file-document</v-icon>
        </v-badge>
        <v-icon v-else>mdi-file-document</v-icon>
        <span>Invoice</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- Footer (Desktop) -->
    <v-footer 
      v-if="!isMobile"
      app 
      class="modern-footer"
    >
      <div class="footer-content">
        <span class="text-body-2">
          &copy; {{ new Date().getFullYear() }} 
          <strong>Artacom Billing System</strong>. 
          All Rights Reserved. Designed by 
          <a 
            href="https://www.instagram.com/amad.dyk/" 
            target="_blank" 
            rel="noopener noreferrer"
            class="footer-link"
          >
            amad.dyk
          </a>
        </span>
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
import logoLight from '@/assets/images/Jelantik-Light.webp';
import logoDark from '@/assets/images/Jelantik-Dark.webp';

// --- State ---
const theme = useTheme();
const { mobile } = useDisplay();
const drawer = ref(true);
const rail = ref(false);
const router = useRouter();
const route = useRoute();
const activeBottomNav = ref('dashboard');

const notifications = ref<any[]>([]);
const suspendedCount = ref(0);
const unpaidInvoiceCount = ref(0);
const stoppedCount = ref(0);
const openTicketsCount = ref(0);
const userCount = ref(0);
const roleCount = ref(0);
const authStore = useAuthStore();
const settingsStore = useSettingsStore();
let socket: WebSocket | null = null;

const userPermissions = ref<string[]>([]);
const forceRender = ref(0);

const isMobile = computed(() => mobile.value);
const logoSrc = computed(() => {
  return theme.global.current.value.dark ? logoDark : logoLight;
});

// Computed untuk judul halaman saat ini
const currentPageTitle = computed(() => {
  const path = route.path;
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/dashboard-pelanggan': 'Dashboard Pelanggan',
    '/pelanggan': 'Data Pelanggan',
    '/langganan': 'Langganan',
    '/data-teknis': 'Data Teknis',
    '/harga-layanan': 'Brand & Paket',
    '/kalkulator': 'Simulasi Harga',
    '/syarat-ketentuan': 'Syarat & Ketentuan',
    '/trouble-tickets': 'Trouble Tickets',
    '/trouble-tickets/reports': 'Ticket Reports',
    '/invoices': 'Invoices',
    '/reports/revenue': 'Laporan Pendapatan',
    '/mikrotik': 'Mikrotik Servers',
    '/traffic-monitoring': 'Traffic Monitoring',
    '/network-management/olt': 'OLT Management',
    '/odp-management': 'ODP Management',
    '/inventory': 'Manajemen Inventaris',
    '/users': 'Users',
    '/roles': 'Roles',
    '/permissions': 'Permissions',
    '/activity-logs': 'Activity Log',
    '/management/sk': 'Kelola S&K',
    '/management/settings': 'Pengaturan',
  };
  return titles[path] || 'Artacom FTTH';
});

// Watch notifications
watch(notifications, (newVal) => {
  if (!newVal || !Array.isArray(newVal)) {
    console.warn('[State] notifications bukan array, reset ke array kosong');
    notifications.value = [];
  }
}, { deep: true });

// Watch authStore.user
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

function refreshMenu() {
  forceRender.value++;
  nextTick(() => {});
}

watch(userPermissions, () => {
  refreshMenu();
}, { deep: true });

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

function toggleDrawer() {
  if (isMobile.value) {
    drawer.value = !drawer.value;
  } else {
    rail.value = !rail.value;
  }
}

// Menu Groups dengan deskripsi
const menuGroups = ref([
  { 
    title: 'DASHBOARD', 
    items: [
      { 
        title: 'Dashboard', 
        icon: 'mdi-view-dashboard-outline', 
        value: 'dashboard-group',
        description: 'Ringkasan sistem & statistik',
        permission: 'view_dashboard',
        children: [
          { 
            title: 'Dashboard Admin', 
            icon: 'mdi-shield-crown-outline', 
            to: '/dashboard', 
            permission: 'view_dashboard',
            description: 'Panel kontrol administrator',
            value: 'dashboard-admin'
          },
          { 
            title: 'Dashboard Jakinet', 
            icon: 'mdi-account-supervisor-outline', 
            to: '/dashboard-pelanggan', 
            permission: 'view_dashboard_pelanggan',
            description: 'Portal pelanggan Jakinet',
            value: 'dashboard-jakinet'
          }
        ]
      },
    ] 
  },
  
  { 
    title: 'FTTH', 
    items: [
      { 
        title: 'Data Pelanggan', 
        icon: 'mdi-account-group-outline', 
        value: 'pelanggan', 
        to: '/pelanggan', 
        permission: 'view_pelanggan',
        description: 'Kelola data pelanggan'
      },
      { 
        title: 'Langganan', 
        icon: 'mdi-wifi-star', 
        value: 'langganan', 
        to: '/langganan', 
        badge: suspendedCount, 
        badgeColor: 'orange', 
        permission: 'view_langganan',
        description: 'Status & paket langganan'
      },
      { 
        title: 'Data Teknis', 
        icon: 'mdi-lan-connect', 
        value: 'teknis', 
        to: '/data-teknis', 
        permission: 'view_data_teknis',
        description: 'Konfigurasi teknis jaringan'
      },
      { 
        title: 'Brand & Paket', 
        icon: 'mdi-package-variant', 
        value: 'harga', 
        to: '/harga-layanan', 
        permission: 'view_brand_&_paket',
        description: 'Daftar paket & harga layanan'
      },
    ]
  },

  { 
    title: 'BILLING', 
    items: [
      { 
        title: 'Invoices', 
        icon: 'mdi-receipt-text-outline', 
        value: 'invoices', 
        to: '/invoices', 
        badge: 0, 
        badgeColor: 'grey-darken-1', 
        permission: 'view_invoices',
        description: 'Tagihan & pembayaran'
      },
      { 
        title: 'Laporan Pendapatan', 
        icon: 'mdi-chart-line', 
        value: 'revenue-report', 
        to: '/reports/revenue', 
        permission: 'view_reports_revenue',
        description: 'Analisis pendapatan'
      }
    ]
  },

  { 
    title: 'LAINNYA', 
    items: [
      { 
        title: 'Simulasi Harga', 
        icon: 'mdi-calculator-variant-outline', 
        value: 'kalkulator', 
        to: '/kalkulator', 
        permission: 'view_simulasi_harga',
        description: 'Hitung estimasi biaya'
      },
      { 
        title: 'S&K', 
        icon: 'mdi-file-document-outline', 
        value: 'sk', 
        to: '/syarat-ketentuan', 
        permission: null,
        description: 'Syarat & ketentuan layanan'
      }
    ]
  },

  { 
    title: 'SUPPORT', 
    items: [
      { 
        title: 'Trouble Tickets', 
        icon: 'mdi-lifebuoy', 
        value: 'trouble-tickets', 
        to: '/trouble-tickets', 
        permission: 'view_trouble_tickets',
        description: 'Kelola tiket gangguan'
      },
      { 
        title: 'Ticket Reports', 
        icon: 'mdi-chart-box-outline', 
        value: 'trouble-ticket-reports', 
        to: '/trouble-tickets/reports', 
        permission: 'view_trouble_tickets',
        description: 'Laporan tiket support'
      },
    ]
  },


  { 
    title: 'NETWORK MANAGEMENT', 
    items: [
      { 
        title: 'Mikrotik Servers', 
        icon: 'mdi-server-network', 
        value: 'mikrotik', 
        to: '/mikrotik', 
        permission: 'view_mikrotik_servers',
        description: 'Kelola server Mikrotik'
      },
      { 
        title: 'Traffic Monitoring', 
        icon: 'mdi-chart-timeline-variant', 
        value: 'traffic-monitoring', 
        to: '/traffic-monitoring', 
        permission: 'view_traffic_monitoring',
        description: 'Monitor trafik jaringan'
      },
      { 
        title: 'OLT Management', 
        icon: 'mdi-router-network', 
        value: 'olt', 
        to: '/network-management/olt', 
        permission: 'view_olt',
        description: 'Kelola perangkat OLT'
      },
      { 
        title: 'ODP Management', 
        icon: 'mdi-sitemap-outline', 
        value: 'odp', 
        to: '/odp-management', 
        permission: 'view_odp_management',
        description: 'Kelola titik distribusi optik'
      },
      { 
        title: 'Manajemen Inventaris', 
        icon: 'mdi-archive-outline', 
        value: 'inventory', 
        to: '/inventory', 
        permission: 'view_inventory',
        description: 'Stok perangkat & material'
      }
    ]
  },

  { 
    title: 'MANAGEMENT', 
    items: [
      { 
        title: 'Users', 
        icon: 'mdi-account-cog-outline', 
        value: 'users', 
        to: '/users', 
        badge: userCount, 
        badgeColor: 'primary', 
        permission: 'view_users',
        description: 'Kelola pengguna sistem'
      },
      { 
        title: 'Roles', 
        icon: 'mdi-shield-account-outline', 
        value: 'roles', 
        to: '/roles', 
        badge: roleCount, 
        badgeColor: 'primary', 
        permission: 'view_roles',
        description: 'Atur peran & akses'
      },
      { 
        title: 'Permissions', 
        icon: 'mdi-shield-key-outline', 
        value: 'permissions', 
        to: '/permissions', 
        permission: 'view_permissions',
        description: 'Hak akses sistem'
      },
      { 
        title: 'Activity Log', 
        icon: 'mdi-history', 
        value: 'activity-logs', 
        to: '/activity-logs', 
        permission: 'view_activity_log',
        description: 'Riwayat aktivitas pengguna'
      },
      { 
        title: 'Kelola S&K', 
        icon: 'mdi-file-edit-outline', 
        value: 'sk-management', 
        to: '/management/sk', 
        permission: 'manage_sk',
        description: 'Edit syarat & ketentuan'
      },
      { 
        title: 'Pengaturan', 
        icon: 'mdi-cog-outline', 
        value: 'settings', 
        to: '/management/settings', 
        permission: 'manage_settings',
        description: 'Konfigurasi sistem'
      }
    ]
  },
]);

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

// Notification helpers
function getNotificationTitle(type: string) {
  const titles: Record<string, string> = {
    'new_payment': 'Pembayaran Diterima',
    'new_customer_for_noc': 'Pelanggan Baru',
    'new_customer': 'Pelanggan Baru',
    'new_technical_data': 'Data Teknis Baru'
  };
  return titles[type] || 'Notifikasi';
}

function getNotificationMessage(notif: any) {
  switch (notif.type) {
    case 'new_payment':
      return `${notif.data?.invoice_number || 'N/A'} dari ${notif.data?.pelanggan_nama || 'N/A'} telah lunas`;
    case 'new_customer_for_noc':
    case 'new_customer':
      return `${notif.data?.pelanggan_nama || 'N/A'} perlu dibuatkan Data Teknis`;
    case 'new_technical_data':
      return `Data teknis untuk ${notif.data?.pelanggan_nama || 'N/A'} telah ditambahkan`;
    default:
      return notif.message || 'Anda memiliki notifikasi baru';
  }
}

function getNotificationIcon(type: string) {
  const icons: Record<string, string> = {
    'new_payment': 'mdi-cash-check',
    'new_customer_for_noc': 'mdi-account-plus',
    'new_customer': 'mdi-account-plus',
    'new_technical_data': 'mdi-lan-connect'
  };
  return icons[type] || 'mdi-bell';
}

function getNotificationColor(type: string) {
  const colors: Record<string, string> = {
    'new_payment': 'success',
    'new_customer_for_noc': 'info',
    'new_customer': 'info',
    'new_technical_data': 'primary'
  };
  return colors[type] || 'grey';
}

function formatNotificationTime(dateString?: string): string {
  if (!dateString) return 'Baru saja';

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'Baru saja';
    } else if (diffMins < 60) {
      return `${diffMins} menit yang lalu`;
    } else if (diffHours < 24) {
      return `${diffHours} jam yang lalu`;
    } else if (diffDays < 7) {
      return `${diffDays} hari yang lalu`;
    } else {
      return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      });
    }
  } catch (error) {
    return 'Baru saja';
  }
}

// Semua fungsi lainnya tetap sama seperti kode asli
// (fetchSidebarBadges, connectWebSocket, disconnectWebSocket, dll.)

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

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.warn(`[Audio] Failed to play audio (${audioFile}):`, error);
          fallbackBeep();
        });
      }
    }
  } catch (error) {
    console.error('[Audio] Failed to create/play audio:', error);
    fallbackBeep();
  }
}

function fallbackBeep() {
  try {
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
    }
  } catch (error) {
    console.warn('[Audio] AudioContext fallback failed:', error);
  }
}

async function refreshTokenAndReconnect() {
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
    const success = await authStore.refreshToken();
    if (success) {
      sessionStorage.removeItem(retryKey);
      connectWebSocket();
    } else {
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

  // Validasi token sebelum connect
  if (!token || token.length < 10) {
    console.warn('[WebSocket] Token tidak valid atau terlalu pendek');
    return;
  }

  const hostname = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  let wsUrl = '';

  // Encode token untuk URL safety
  const encodedToken = encodeURIComponent(token);

  if (hostname === 'billingftth.my.id') {
      wsUrl = `${protocol}//${hostname}/ws/notifications?token=${encodedToken}`;
  } else {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
      const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
      wsUrl = `${wsProtocol}//${wsHost}/ws/notifications?token=${encodedToken}`;
  }

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 30000);

    let lastTokenCheck = 0;
    const TOKEN_CHECK_INTERVAL = 120000;
    const TOKEN_CHECK_COOLDOWN = 30000;

    tokenCheckInterval = setInterval(async () => {
      const now = Date.now();

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
        return;
      }

      if (!data.id) {
        data.id = Date.now() + Math.floor(Math.random() * 10000);
      }

      const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];

      if (data.type === 'new_customer') {
        data.type = 'new_customer_for_noc';
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
          return;
        }
        if ((data.type === 'new_customer_for_noc' || data.type === 'new_customer') && !data.data.pelanggan_nama) {
          return;
        }
        if (data.type === 'new_technical_data' && !data.data.pelanggan_nama) {
          return;
        }

        notifications.value.unshift(data);

        if (notifications.value.length > 20) {
          notifications.value = notifications.value.slice(0, 20);
        }
        
        playSound(data.type);
        
        if (typeof window !== 'undefined' && window.dispatchEvent) {
          window.dispatchEvent(new CustomEvent('new-notification', { detail: data }));
        }
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
    console.warn(`[WebSocket] Koneksi ditutup: Kode ${event.code}, Reason: ${event.reason || 'No reason provided'}`);
    socket = null;

    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    const shouldNotReconnect = [1000, 1001, 1005, 1006, 1008].includes(event.code) ||
                               event.reason === "Connection replaced" ||
                               event.reason === "Logout Pengguna" ||
                               event.reason?.includes("Invalid token") ||
                               event.reason?.includes("Token decode failed") ||
                               event.reason?.includes("Token expired") ||
                               event.reason?.includes("Token signature invalid");

    // Handle token-related errors with better feedback
    if (event.code === 1008 || event.reason?.includes("Invalid token") || event.reason?.includes("Token decode failed") || event.reason?.includes("Token expired") || event.reason?.includes("Token signature invalid")) {
      console.warn('[WebSocket] Token invalid atau expired, forcing logout...');
      console.warn(`[WebSocket] Error details: Code=${event.code}, Reason=${event.reason}`);

      // Clear tokens and logout
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      // Clear any pending reconnect attempts
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }

      authStore.logout();
      router.push('/login');
      return;
    }

    // Only reconnect if user is still authenticated and reconnection is allowed
    if (authStore.isAuthenticated && !shouldNotReconnect) {
      if (event.code === 1008) {
        // Token error - use refresh token approach
        reconnectTimeout = setTimeout(refreshTokenAndReconnect, 1000);
      } else {
        // Other errors - standard reconnection
        reconnectTimeout = setTimeout(connectWebSocket, 5000);
      }
    }
  };
}

function disconnectWebSocket() {
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

async function handleNotificationClick(notification: any) {
  if (!notification || !notification.id) {
    console.error("[Notification] Invalid notification object");
    return;
  }

  const notificationId = notification.id;

  try {
    await apiClient.post(`/notifications/${notificationId}/mark-as-read`);

    if (notifications.value && Array.isArray(notifications.value)) {
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
    }

    if (notification.type === 'new_technical_data') {
      router.push('/langganan');
    } else if (notification.type === 'new_customer_for_noc' || notification.type === 'new_customer') {
      router.push('/data-teknis');
    } else if (notification.type === 'new_payment') {
      router.push('/invoices');
    }

  } catch (error) {
    console.error("[Notification] Gagal menandai notifikasi sebagai sudah dibaca:", error);
  }
}

async function markAllAsRead() {
  try {
    await apiClient.post('/notifications/mark-all-as-read'); 
    notifications.value = [];
  } catch (error) {
    console.error("[Notification] Gagal membersihkan notifikasi:", error);
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

function toggleTheme() {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark';
  theme.change(newTheme);
  localStorage.setItem('theme', newTheme);
}

function handleLogoClick() {
  // Navigasi ke dashboard atau refresh halaman saat logo diklik
  if (route.path !== '/dashboard') {
    router.push('/dashboard');
  } else {
    // Refresh halaman dengan cara yang elegan
    forceRender.value += 1;
  }
}

onMounted(async () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) theme.change(savedTheme);

  await settingsStore.fetchMaintenanceStatus();

  if (isMobile.value) {
    drawer.value = false;
    rail.value = false;
  }

  updateActiveBottomNav(route.path);

  const enableAudioContext = () => {
    document.removeEventListener('click', enableAudioContext);
  };
  document.addEventListener('click', enableAudioContext);

  if (authStore.isAuthenticated && authStore.user) {
    const role = authStore.user.role;
    if (role) {
      if (role.name?.toLowerCase() === 'admin') {
        userPermissions.value = ['*'];
      } else {
        userPermissions.value = role.permissions?.map((p: any) => p.name) || [];
      }
      setTimeout(() => refreshMenu(), 50);
    }
  }

  const userIsValid = await authStore.verifyToken();

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
</script>

<style scoped>
/* ==================== MODERN DESIGN SYSTEM ==================== */

:root {
  --sidebar-width: 300px;
  --sidebar-rail-width: 70px;
  --header-height: 70px;
  --footer-height: 60px;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --transition-speed: 0.3s;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.16);
}

/* ==================== BASE STYLES ==================== */

.modern-app {
  background-color: rgb(var(--v-theme-background));
  transition: background-color var(--transition-speed) ease;
}

/* ==================== SIDEBAR STYLES ==================== */

.modern-drawer {
  border-right: none !important;
  background: rgb(var(--v-theme-surface));
  box-shadow: var(--shadow-md);
  transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-drawer :deep(.v-navigation-drawer__content) {
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Sidebar Header - PERBAIKAN SEJAJAR DENGAN HEADER */
.sidebar-header-modern {
  height: var(--header-height) !important;
  min-height: var(--header-height) !important;
  padding: 0 var(--spacing-md);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.05) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%
  );
  transition: all var(--transition-speed) ease;
  display: flex;
  align-items: center;
}

.sidebar-header-modern.rail-mode {
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Header Content - PERBAIKAN SPACING */
.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

/* Logo Wrapper */
.logo-wrapper {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: var(--radius-md);
  transition: all var(--transition-speed) ease;
  cursor: pointer;
}

.logo-wrapper:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.02);
}

.sidebar-logo {
  height: 56px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  transition: all var(--transition-speed) ease;
  border-radius: var(--radius-sm);
}

.v-theme--dark .sidebar-logo {
  filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.1)) brightness(1.1);
}

/* Title Wrapper - PERBAIKAN */
.title-wrapper {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
  margin: 0;
  letter-spacing: -0.02em;
}

.app-subtitle {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
  line-height: 1.2;
}

.toggle-btn,
.close-btn {
  flex-shrink: 0;
  opacity: 0.7;
  transition: all var(--transition-speed) ease;
  margin-left: auto;
}

.toggle-btn:hover,
.close-btn:hover {
  opacity: 1;
  background-color: rgba(var(--v-theme-primary), 0.1);
}

/* Navigation Container */
.navigation-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--spacing-md) 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-on-surface), 0.2) transparent;
}

.navigation-container::-webkit-scrollbar {
  width: 6px;
}

.navigation-container::-webkit-scrollbar-track {
  background: transparent;
}

.navigation-container::-webkit-scrollbar-thumb {
  background-color: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.navigation-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.3);
}

.navigation-list {
  padding: 0 var(--spacing-md);
}

/* Menu Group Header */
.menu-group-header {
  margin: var(--spacing-lg) 0 var(--spacing-sm) 0;
  padding: 0 var(--spacing-sm);
}

.menu-group-header:first-child {
  margin-top: 0;
}

.group-title {
  font-size: 0.7rem;
  font-weight: 900;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  display: block;
  margin-bottom: var(--spacing-xs);
  margin-left: 12px;
  margin-top: 8px;
}

.group-divider {
  opacity: 0.12;
}

/* Menu Items - KEMBALI KE STYLE ORIGINAL */
.menu-item {
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xs);
  min-height: 48px;
  transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.menu-item :deep(.v-list-item__prepend) {
  margin-inline-end: 16px !important;
  width: 24px;
  display: flex;
  justify-content: center;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 3px;
  background: linear-gradient(135deg, 
    rgb(var(--v-theme-primary)) 0%, 
    rgb(var(--v-theme-secondary)) 100%
  );
  transform: scaleY(0);
  transition: transform var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-item:hover::before {
  transform: scaleY(1);
}

.menu-item:not(.v-list-item--active):hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
  transform: translateX(4px);
}

.menu-item.v-list-item--active {
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgba(var(--v-theme-primary), 0.8) 25%,
    rgba(var(--v-theme-secondary), 0.9) 50%,
    rgba(var(--v-theme-primary), 0.7) 75%,
    rgb(var(--v-theme-primary)) 100%
  );
  color: white !important;
  font-weight: 700;
  box-shadow:
    0 8px 24px rgba(var(--v-theme-primary), 0.5),
    0 4px 12px rgba(var(--v-theme-primary), 0.3),
    inset 0 2px 4px rgba(255, 255, 255, 0.3),
    inset 0 -1px 2px rgba(0, 0, 0, 0.1),
    inset 0 0 0 2px rgba(255, 255, 255, 0.4);
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  transform: translateY(-2px);
  margin: 2px 4px;
}


.menu-item.v-list-item--active::before {
  transform: scaleY(1);
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgb(var(--v-theme-secondary)) 100%
  );
  box-shadow: 0 0 8px rgba(var(--v-theme-primary), 0.5);
}

/* Add strong pulse effect for active menu */
.menu-item.v-list-item--active {
  animation: activePulse 2s ease-in-out infinite;
}


/* Strong pulse animation */
@keyframes activePulse {
  0%, 100% {
    box-shadow:
      0 8px 24px rgba(var(--v-theme-primary), 0.5),
      0 4px 12px rgba(var(--v-theme-primary), 0.3),
      inset 0 2px 4px rgba(255, 255, 255, 0.3),
      inset 0 -1px 2px rgba(0, 0, 0, 0.1),
      inset 0 0 0 2px rgba(255, 255, 255, 0.4);
    transform: translateY(-2px) scale(1);
  }
  50% {
    box-shadow:
      0 12px 32px rgba(var(--v-theme-primary), 0.7),
      0 6px 16px rgba(var(--v-theme-primary), 0.4),
      inset 0 2px 4px rgba(255, 255, 255, 0.4),
      inset 0 -1px 2px rgba(0, 0, 0, 0.1),
      inset 0 0 0 3px rgba(255, 255, 255, 0.5);
    transform: translateY(-3px) scale(1.01);
  }
}

.item-title {
  font-size: 0.9375rem;
  font-weight: 500;
  line-height: 1.4;
}

.item-description {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  line-height: 1.3;
  margin-top: 2px;
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Sub Items */
.sub-item {
  padding-left: calc(var(--spacing-lg) * 3 + var(--spacing-md) + var(--spacing-lg)) !important;
  min-height: 44px;
}

.sub-item-description {
  font-size: 0.6875rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  line-height: 1.3;
  margin-top: 2px;
}

/* Menu Group */
.menu-group :deep(.v-list-group__items) {
  --indent-padding: 0px;
}

/* Badges */
.badges-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.badge-item :deep(.v-badge__badge) {
  font-size: 0.6875rem;
  font-weight: 600;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
}

/* PERBAIKAN RAIL MODE - FIX ICON TIDAK TERLIHAT */
.v-navigation-drawer--rail .navigation-list {
  padding: 0 var(--spacing-xs);
}

.v-navigation-drawer--rail .menu-group-header {
  display: none;
}

.v-navigation-drawer--rail .menu-item {
  justify-content: center;
  padding: 0 30px !important;
  margin-left: 10px;
}

.v-navigation-drawer--rail .menu-item :deep(.v-list-item__prepend) {
  margin-inline-end: 0 !important;
}

.v-navigation-drawer--rail .menu-item :deep(.v-list-item__content) {
  display: none;
}

.v-navigation-drawer--rail .menu-item :deep(.v-list-item__append) {
  display: none;
}

.v-navigation-drawer--rail .v-list-group__items {
  display: none;
}

/* Pastikan icon terlihat di rail mode */
.v-navigation-drawer--rail .menu-item :deep(.v-icon) {
  opacity: 1 !important;
  font-size: 18px !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}

/* Logout Section */
.logout-container {
  padding: 4px;
  background: rgba(var(--v-theme-surface), 0.5);
  backdrop-filter: blur(10px);
}

.logout-btn {
  border-radius: 12px !important;
  font-weight: 600;
  display: flex !important;
  min-height: 40px;
  margin: 0;
  padding: 0 16px !important;
}

.logout-btn:hover {
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
  transform: translateY(-2px);
}

/* Logout button di rail mode */
.v-navigation-drawer--rail .logout-container {
  padding: 2px;
}

.v-navigation-drawer--rail .logout-btn {
  min-width: 40px;
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 8px;
  margin: 0;
}

/* Center avatar J in rail mode */
.v-navigation-drawer--rail .logo-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.v-navigation-drawer--rail .logo-wrapper .v-avatar {
  margin: 0 auto;
}

/* ==================== APP BAR STYLES ==================== */

.modern-app-bar {
  background: rgb(var(--v-theme-surface)) !important;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(10px);
  transition: all var(--transition-speed) ease;
  height: var(--header-height) !important;
  min-height: var(--header-height) !important;
}

.modern-app-bar :deep(.v-toolbar__content) {
  height: var(--header-height) !important;
  min-height: var(--header-height) !important;
}

.menu-toggle {
  transition: all var(--transition-speed) ease;
  height: 40px !important;
  width: 40px !important;
  margin-top: 15px;
  margin-bottom: 13px;
}

.menu-toggle:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.05);
}

.app-bar-title {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 900;
}

.header-icon-btn {
  transition: all var(--transition-speed) ease;
  height: 40px !important;
  width: 40px !important;
  margin-top: 8px;
  margin-bottom: 8px;
}

.header-icon-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.05);
}


/* ==================== MODERN NOTIFICATION STYLES ==================== */

.modern-notification-container {
  width: 420px;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(var(--v-border-color), 0.1);
  overflow: hidden;
}

.notification-header-section {
  padding: 20px;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.08) 0%,
    rgba(var(--v-theme-secondary), 0.04) 100%
  );
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
}

.notification-main-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.3;
}

.notification-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.8125rem;
  line-height: 1.3;
}

.notification-divider {
  margin: 0;
  border-color: rgba(var(--v-border-color), 0.1) !important;
}

.notification-list-section {
  max-height: 480px;
  overflow-y: auto;
}

/* Empty State */
.empty-notification-state {
  padding: 48px 24px;
  text-align: center;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.02) 0%,
    rgba(var(--v-theme-secondary), 0.01) 100%
  );
}

.empty-notification-icon {
  position: relative;
  display: inline-block;
  margin-bottom: 20px;
}

.icon-background {
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0.1;
}

.empty-notification-text {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
}

.empty-subtitle {
  font-size: 0.9375rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.4;
}

/* Notification Items */
.notification-items-container {
  padding: 8px;
}

.modern-notification-item {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.modern-notification-item:hover {
  background: rgba(var(--v-theme-primary), 0.03);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.modern-notification-item.notification-item-unread {
  background: rgba(var(--v-theme-primary), 0.02);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.modern-notification-item.notification-item-unread::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(var(--v-theme-primary), 0.1) 50%,
    transparent 100%
  );
  opacity: 0.6;
}

.notification-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
}

.notification-avatar-container {
  position: relative;
  flex-shrink: 0;
}

.notification-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.notification-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  background: rgb(var(--v-theme-primary));
  border-radius: 50%;
  border: 2px solid rgb(var(--v-theme-surface));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Avatar Colors */
.avatar-success {
  background: linear-gradient(135deg, #4CAF50, #45a049) !important;
}

.avatar-info {
  background: linear-gradient(135deg, #2196F3, #1E88E5) !important;
}

.avatar-primary {
  background: linear-gradient(135deg, #1976D2, #1565C0) !important;
}

.avatar-warning {
  background: linear-gradient(135deg, #FF9800, #F57C00) !important;
}

.avatar-error {
  background: linear-gradient(135deg, #F44336, #D32F2F) !important;
}

.notification-message {
  flex: 1;
  min-width: 0;
}

.notification-type {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  flex-wrap: wrap;
  gap: 8px;
}

.notification-label {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  line-height: 1.2;
}

.label-success {
  background: rgba(76, 175, 80, 0.1);
  color: #2E7D32;
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.label-info {
  background: rgba(33, 150, 243, 0.1);
  color: #1565C0;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.label-primary {
  background: rgba(25, 118, 210, 0.1);
  color: #1976D2;
  border: 1px solid rgba(25, 118, 210, 0.2);
}

.notification-time {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-weight: 500;
}

.notification-description {
  font-size: 0.875rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.8);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Scrollbar Styling */
.notification-list-section::-webkit-scrollbar {
  width: 6px;
}

.notification-list-section::-webkit-scrollbar-track {
  background: transparent;
}

.notification-list-section::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.notification-list-section::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}

/* Animations */
.modern-notification-item {
  animation: slideInFromRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-notification-item:nth-child(even) {
  animation-delay: 0.05s;
}

.modern-notification-item:nth-child(3n) {
  animation-delay: 0.1s;
}

@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Hover Effects */
.modern-notification-item:hover .notification-avatar {
  transform: scale(1.05);
  transition: transform var(--transition-speed) ease;
}

.modern-notification-item:hover .notification-dot {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
   0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Dark Theme Adjustments */
.v-theme--dark .modern-notification-container {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .notification-header-section {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.15) 0%,
    rgba(var(--v-theme-secondary), 0.08) 100%
  );
}

.v-theme--dark .notification-dot {
  border-color: rgba(var(--v-theme-surface), 0.8);
}

/* ==================== MAIN CONTENT ==================== */

.modern-main {
  background-color: rgb(var(--v-theme-background));
  transition: background-color var(--transition-speed) ease;
}

.modern-main.with-bottom-nav {
  padding-bottom: 65px !important;
}

/* ==================== BOTTOM NAVIGATION (MOBILE) ==================== */

.mobile-bottom-nav {
  position: fixed !important;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgb(var(--v-theme-surface)) !important;
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.mobile-bottom-nav :deep(.v-btn) {
  height: 65px !important;
  flex-direction: column;
  gap: var(--spacing-xs);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.02em;
  transition: all var(--transition-speed) ease;
}

.mobile-bottom-nav :deep(.v-btn .v-icon) {
  font-size: 24px;
  margin-bottom: 2px;
  transition: all var(--transition-speed) ease;
}

.mobile-bottom-nav :deep(.v-btn--active) {
  color: rgb(var(--v-theme-primary)) !important;
}

.mobile-bottom-nav :deep(.v-btn--active .v-icon) {
  transform: scale(1.1);
}

.mobile-bottom-nav :deep(.v-badge__badge) {
  font-size: 0.625rem;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
}

/* ==================== FOOTER ==================== */

.modern-footer {
  height: var(--footer-height);
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
  background: rgb(var(--v-theme-surface));
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

/* Footer positioning - responsive terhadap sidebar */
.v-navigation-drawer--not-rail ~ .v-main .modern-footer {
  left: 300px !important;
  width: calc(100% - 300px) !important;
}

.v-navigation-drawer--rail ~ .v-main .modern-footer {
  left: 80px !important;
  width: calc(100% - 80px) !important;
}

.v-navigation-drawer--temporary ~ .v-main .modern-footer {
  left: 0 !important;
  width: 100% !important;
}

.footer-content {
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  font-size: 14px;
  padding: 8px 16px;
  height: 100%;
}

.footer-content .text-body-2 {
  font-size: 14px !important;
  line-height: 1.4;
  text-align: center;
}

.footer-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  font-weight: 600;
  transition: all var(--transition-speed) ease;
}

.footer-link:hover {
  color: rgb(var(--v-theme-secondary));
  text-decoration: underline;
}

/* Additional footer enhancements */
.v-theme--dark .modern-footer {
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.2);
}

/* ==================== MAINTENANCE BANNER ==================== */

.maintenance-banner {
  height: 48px !important;
  font-size: 0.875rem !important;
  font-weight: 600;
  justify-content: center;
  box-shadow: var(--shadow-sm);
}

/* ==================== DARK THEME ==================== */

.v-theme--dark .modern-app {
  background-color: #0a0e1a;
}

.v-theme--dark .modern-drawer {
  background: #151b2d;
  box-shadow: 0 0 24px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .sidebar-header-modern {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.08) 0%, 
    rgba(var(--v-theme-secondary), 0.08) 100%
  );
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .modern-app-bar {
  background: #151b2d !important;
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .logout-container {
  background: rgba(10, 14, 26, 0.5);
}

.v-theme--dark .mobile-bottom-nav {
  background: #151b2d !important;
  border-top-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .modern-footer {
  background: #151b2d;
  border-top-color: rgba(255, 255, 255, 0.08);
}

/* ==================== RESPONSIVE DESIGN ==================== */

@media (max-width: 960px) {
  .modern-drawer {
    width: 280px !important;
  }

  .v-navigation-drawer--not-rail ~ .v-main .modern-footer {
    left: 280px !important;
    width: calc(100% - 280px) !important;
  }
}

@media (max-width: 600px) {
  .modern-drawer {
    width: 280px !important;
  }

  .v-navigation-drawer--not-rail ~ .v-main .modern-footer {
    left: 280px !important;
    width: calc(100% - 280px) !important;
  }

  /* Footer tidak perlu positioning khusus di mobile karena sidebar temporary */
  
  .sidebar-logo {
    height: 50px;
  }
  
  .app-title {
    font-size: 1.125rem;
  }
  
  .app-subtitle {
    font-size: 0.6875rem;
  }
  
  .menu-item {
    min-height: 44px;
  }
  
  .item-title {
    font-size: 0.875rem;
  }
  
  .item-description {
    font-size: 0.6875rem;
  }
}

@media (max-width: 400px) {
  .modern-drawer {
    width: 260px !important;
  }
  
  .sidebar-logo {
    height: 46px;
  }
  
  .app-title {
    font-size: 1rem;
  }
  
  .app-subtitle {
    font-size: 0.625rem;
  }
  
  .mobile-bottom-nav :deep(.v-btn) {
    font-size: 0.625rem;
    gap: 2px;
  }
  
  .mobile-bottom-nav :deep(.v-btn .v-icon) {
    font-size: 20px;
  }
}

/* ==================== ANIMATIONS ==================== */

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.menu-item {
  animation: slideIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.notification-item {
  animation: fadeIn 0.3s ease-out;
}

/* ==================== ACCESSIBILITY ==================== */

.menu-item:focus-visible,
.header-icon-btn:focus-visible,
.logout-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

/* ==================== PRINT STYLES ==================== */

@media print {
  .modern-drawer,
  .modern-app-bar,
  .mobile-bottom-nav,
  .modern-footer {
    display: none !important;
  }
  
  .modern-main {
    padding: 0 !important;
  }
}
</style>