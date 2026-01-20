<template>
  <v-app class="modern-app">
    <!-- Maintenance Mode Overlay for Non-Admin Users -->
    <v-overlay
      v-if="settingsStore.maintenanceMode.isActive && !isAdmin"
      v-model="showMaintenanceOverlay"
      class="maintenance-overlay align-center justify-center"
      scrim="rgba(0, 0, 0, 0.85)"
      persistent
    >
      <v-card class="maintenance-card" elevation="24">
        <div class="maintenance-icon-wrapper">
          <v-icon size="120" color="warning" class="maintenance-icon">mdi-tools</v-icon>
          <div class="maintenance-pulse"></div>
        </div>

        <h1 class="maintenance-title">Sistem Sedang Dalam Maintenance</h1>

        <p class="maintenance-message">
          {{ settingsStore.maintenanceMode.message || 'Sistem sedang dalam perbaikan. Silakan coba lagi nanti.' }}
        </p>

        <v-divider class="my-4"></v-divider>

        <div class="maintenance-info">
          <v-icon size="20" color="info" class="me-2">mdi-information-outline</v-icon>
          <span>Anda tetap bisa login, namun akses ke sistem terbatas saat maintenance.</span>
        </div>

        <div class="maintenance-features">
          <div class="feature-item">
            <v-icon color="success" class="me-2">mdi-check-circle</v-icon>
            <span>Login tetap tersedia</span>
          </div>
          <div class="feature-item">
            <v-icon color="success" class="me-2">mdi-check-circle</v-icon>
            <span>Data tetap aman</span>
          </div>
          <div class="feature-item">
            <v-icon color="success" class="me-2">mdi-check-circle</v-icon>
            <span>Sistem akan kembali normal segera</span>
          </div>
        </div>

        <v-btn
          color="primary"
          variant="elevated"
          size="large"
          class="maintenance-btn"
          @click="refreshPage"
        >
          <v-icon start>mdi-refresh</v-icon>
          Refresh Halaman
        </v-btn>
      </v-card>
    </v-overlay>

    <!-- Admin Banner - Hanya untuk Admin -->
    <v-system-bar
      v-if="settingsStore.maintenanceMode.isActive && isAdmin"
      color="warning"
      window
      class="maintenance-admin-banner"
    >
      <v-icon class="me-2 animate-pulse">mdi-alert-decagram</v-icon>
      <span class="me-2"><strong>Mode Maintenance Aktif:</strong> {{ settingsStore.maintenanceMode.message }}</span>
      <v-spacer></v-spacer>
      <v-chip size="small" color="error" variant="elevated">
        <v-icon start size="small">mdi-shield-crown</v-icon>
        Admin Access
      </v-chip>
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
                  v-for="subItem in (item as any).children"
                  :key="(subItem as any).value + '-sub'"
                  :value="(subItem as any).value"
                  :to="(subItem as any).to"
                  :prepend-icon="(subItem as any).icon"
                  class="menu-item sub-item"
                >
                  <v-list-item-title class="item-title">
                    {{ (subItem as any).title }}
                  </v-list-item-title>

                  <!-- Badge Section for Sub Items -->
                  <template v-slot:append v-if="!rail || isMobile">
                    <div class="badges-wrapper">
                      <!-- Langganan Badges -->
                      <template v-if="(subItem as any).value === 'langganan'">
                        <v-tooltip location="top" v-if="suspendedCount > 0">
                          <template v-slot:activator="{ props }">
                            <v-badge
                              color="error"
                              :content="suspendedCount"
                              inline
                              v-bind="props"
                              class="badge-item badge-suspended"
                            ></v-badge>
                          </template>
                          <span>{{ suspendedCount }} langganan berstatus "Suspended"</span>
                        </v-tooltip>

                        <v-tooltip location="top" v-if="stoppedCount > 0">
                          <template v-slot:activator="{ props }">
                            <v-badge
                              color="grey"
                              :content="stoppedCount"
                              inline
                              v-bind="props"
                              class="badge-item ms-1 badge-stopped"
                            ></v-badge>
                          </template>
                          <span>{{ stoppedCount }} langganan berstatus "Berhenti"</span>
                        </v-tooltip>
                      </template>

                      <!-- Invoice Badge -->
                      <template v-if="(subItem as any).value === 'invoices'">
                        <v-tooltip location="top" v-if="unpaidInvoiceCount > 0">
                          <template v-slot:activator="{ props }">
                            <v-badge
                              color="warning"
                              :content="unpaidInvoiceCount"
                              inline
                              v-bind="props"
                              class="badge-item badge-unpaid"
                            ></v-badge>
                          </template>
                          <span>{{ unpaidInvoiceCount }} invoice belum dibayar</span>
                        </v-tooltip>

                        <v-tooltip location="top" v-if="totalInvoiceCount > 0">
                          <template v-slot:activator="{ props }">
                            <v-badge
                              color="info"
                              :content="totalInvoiceCount"
                              inline
                              v-bind="props"
                              class="badge-item ms-1 badge-total"
                            ></v-badge>
                          </template>
                          <span>Total {{ totalInvoiceCount }} invoice</span>
                        </v-tooltip>
                      </template>

                      <!-- Trouble Ticket Badge -->
                      <template v-if="(subItem as any).value === 'trouble-tickets' && openTicketsCount > 0">
                        <v-tooltip location="top">
                          <template v-slot:activator="{ props }">
                            <v-badge
                              color="warning"
                              :content="openTicketsCount"
                              inline
                              v-bind="props"
                              class="badge-item badge-tickets"
                            ></v-badge>
                          </template>
                          <span>{{ openTicketsCount }} tiket gangguan terbuka</span>
                        </v-tooltip>
                      </template>
                    </div>
                  </template>
                </v-list-item>
              </v-list-group>

              <!-- Single Item -->
              <v-list-item
                v-else
                :prepend-icon="(item as any).icon"
                :value="(item as any).value"
                :to="(item as any).to"
                class="menu-item single-item"
                :key="'item-' + (item as any).value"
              >
                <v-list-item-title class="item-title">
                  {{ (item as any).title }}
                </v-list-item-title>

                <!-- Badges -->
                <template v-slot:append>
                  <div class="badges-wrapper">
                    <v-tooltip location="top" v-if="(item as any).value === 'langganan' && suspendedCount > 0">
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

                    <v-tooltip location="top" v-if="(item as any).value === 'langganan' && stoppedCount > 0">
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

                    <v-tooltip location="top" v-if="(item as any).value === 'invoices' && unpaidInvoiceCount > 0">
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

      <!-- Running Text -->
      <div v-if="!isMobile" class="running-text-container mx-4 flex-grow-1">
        <div class="marquee-content">
          <span>
            <v-icon color="primary" class="mr-2" size="small">mdi-bullhorn-outline</v-icon>
            Selamat Datang di&nbsp;<strong>Artacom Billing System</strong>&nbsp;- Portal Manajemen Layanan Internet Terpadu
            <span class="mx-4">•</span>
             <v-icon color="success" class="mr-2" size="small">mdi-check-circle-outline</v-icon>
            Sistem Berjalan Normal
            <span class="mx-4">•</span>
             <v-icon color="info" class="mr-2" size="small">mdi-clock-outline</v-icon>
             Jangan lupa cek invoice jatuh tempo!
          </span>
          <span class="mx-4">•</span>
          <span>
            <v-icon color="warning" class="mr-2" size="small">mdi-alert-outline</v-icon>
            SEMANGATTT MBA UMAYYYY!
          </span>
        </div>
      </div>
      <v-spacer v-else></v-spacer>

      <!-- Global Search -->
      <GlobalSearch class="me-2" />

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
import GlobalSearch from '@/components/GlobalSearch.vue';

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
const totalInvoiceCount = ref(0);
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

// Computed untuk cek apakah user adalah admin
const isAdmin = computed(() => {
  const user = authStore.user;
  if (user?.role) {
    return user.role.name?.toLowerCase() === 'admin';
  }
  return false;
});

// State untuk maintenance overlay
const showMaintenanceOverlay = computed(() => {
  return settingsStore.maintenanceMode.isActive && !isAdmin.value;
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
    '/kalkulator-diskon': 'Kalkulator Diskon',
    '/syarat-ketentuan': 'Syarat & Ketentuan',
    '/trouble-tickets': 'Trouble Tickets',
    '/trouble-tickets/reports': 'Ticket Reports',
    '/invoices': 'Invoices',
    '/diskon': 'Diskon',
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
        title: 'Management Pelanggan', 
        icon: 'mdi-account-network-outline', 
        value: 'management-pelanggan',
        description: 'Kelola data pelanggan & layanan',
        permission: null,
        children: [
          { 
            title: 'Pelanggan', 
            icon: 'mdi-account-group-outline', 
            value: 'pelanggan', 
            to: '/pelanggan', 
            permission: 'view_pelanggan',
            description: 'Kelola data pelanggan'
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
            title: 'Brand & Paket', 
            icon: 'mdi-package-variant', 
            value: 'harga', 
            to: '/harga-layanan', 
            permission: 'view_brand_&_paket',
            description: 'Daftar paket & harga layanan'
          },
        ]
      },
    ]
  },

  {
    title: 'BILLING',
    items: [
      {
        title: 'Billing & Reports',
        icon: 'mdi-cash-multiple',
        value: 'billing-group',
        description: 'Kelola tagihan & laporan',
        permission: null,
        children: [
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
            title: 'Diskon',
            icon: 'mdi-percent-outline',
            value: 'diskon',
            to: '/diskon',
            permission: 'manage_diskon',
            description: 'Kelola diskon per cluster'
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
    ]
  },

  {
    title: 'LAINNYA', 
    items: [
      { 
        title: 'Tools & Resources', 
        icon: 'mdi-toolbox-outline', 
        value: 'tools-group',
        description: 'Alat bantu & sumber daya',
        permission: null,
        children: [
          {
            title: 'Simulasi Harga',
            icon: 'mdi-calculator-variant-outline',
            value: 'kalkulator',
            to: '/kalkulator',
            permission: 'view_simulasi_harga',
            description: 'Hitung estimasi biaya'
          },
          {
            title: 'Kalkulator Diskon',
            icon: 'mdi-percent-outline',
            value: 'kalkulator-diskon',
            to: '/kalkulator-diskon',
            permission: 'view_simulasi_harga',
            description: 'Hitung simulasi diskon'
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
    ]
  },

  { 
    title: 'SUPPORT', 
    items: [
      { 
        title: 'Customer Support', 
        icon: 'mdi-headset', 
        value: 'support-group',
        description: 'Layanan dukungan pelanggan',
        permission: null,
        children: [
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
    ]
  },


  { 
    title: 'NETWORK MANAGEMENT', 
    items: [
      { 
        title: 'Network Management', 
        icon: 'mdi-network-outline', 
        value: 'network-management-group',
        description: 'Kelola infrastruktur jaringan',
        permission: null,
        children: [
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
          },
        ]
      },
    ]
  },

  { 
    title: 'MANAGEMENT', 
    items: [
      { 
        title: 'System Management', 
        icon: 'mdi-cog-outline', 
        value: 'system-management-group',
        description: 'Kelola sistem & pengguna',
        permission: null,
        children: [
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
      // If item has children, check if any child has permission
      if ('children' in item && item.children) {
        const allowedChildren = item.children.filter(child => 
          !('permission' in child) || !child.permission || userPermissions.value.includes(child.permission)
        );
        return allowedChildren.length > 0;
      }
      
      // For items without children, check their own permission
      const hasPermission = !('permission' in item) || !item.permission || userPermissions.value.includes(item.permission);
      return hasPermission;
    }).map(item => {
      // Filter children if item has them
      if ('children' in item && item.children) {
        return {
          ...item,
          children: item.children.filter(child => 
            !('permission' in child) || !child.permission || userPermissions.value.includes(child.permission)
          )
        };
      }
      return item;
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
    totalInvoiceCount.value = response.data.total_invoice_count;
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

        // Update badge sidebar secara real-time
        fetchSidebarBadges();

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

// Refresh halaman untuk maintenance mode
function refreshPage() {
  window.location.reload();
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
  background: #fafafa !important;
  border-right: 1px solid #e0e0e0 !important;
  box-shadow: none !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-drawer :deep(.v-navigation-drawer__content) {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Header Section - Minimalist */
.sidebar-header-modern {
  height: var(--header-height);
  min-height: var(--header-height);
  padding: 0 23px;
  background: #ffffff !important;
  border-bottom: none;
  display: flex;
  align-items: center;
  gap: 13px;
  transition: all 0.3s ease;
}

.sidebar-header-modern.rail-mode {
  padding: 0 8px;
  justify-content: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

/* Logo */
.logo-wrapper {
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.logo-wrapper:hover {
  opacity: 0.8;
}

.sidebar-logo {
  height: 48px;
  width: auto;
  object-fit: contain;
}

/* Title */
.title-wrapper {
  flex: 1;
  min-width: 0;
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
  line-height: 1.3;
  letter-spacing: -0.02em;
}

.app-subtitle {
  font-size: 0.75rem;
  color: #757575;
  margin: 0;
  font-weight: 500;
  line-height: 1.3;
}

/* Toggle Button */
.toggle-btn,
.close-btn {
  opacity: 0.6;
  transition: all 0.2s ease;
}

.toggle-btn:hover,
.close-btn:hover {
  opacity: 1;
  background-color: #f5f5f5 !important;
}

/* Navigation Container */
.navigation-container {
  flex: 1;
  overflow-y: auto !important;
  overflow-x: hidden;
  padding: 16px 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(33, 150, 243, 0.3) transparent;
  height: 100%;
  max-height: calc(100vh - 180px);
}

.navigation-container::-webkit-scrollbar {
  width: 4px;
}

.navigation-container::-webkit-scrollbar-track {
  background: transparent;
}

.navigation-container::-webkit-scrollbar-thumb {
  background-color: #d0d0d0;
  border-radius: 2px;
}

.navigation-container::-webkit-scrollbar-thumb:hover {
  background-color: #b0b0b0;
}

.navigation-list {
  padding: 0 12px;
}

/* Menu Group Header - Minimalist */
.menu-group-header {
  margin: 24px 0 8px 0;
  padding: 0 8px;
}

.menu-group-header:first-child {
  margin-top: 0;
  padding-top: 0;
}

.group-title {
  font-size: 0.6875rem;
  font-weight: 800;
  color: #1a1a1a;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  display: block;
  margin-bottom: 8px;
}

.group-divider {
  display: none;
}

/* Menu Items - Clean & Simple */
.menu-item {
  border-radius: 8px;
  margin-bottom: 4px;
  min-height: 40px;
  transition: all 0.2s ease;
  position: relative;
  overflow: visible;
  background: transparent;
}

.menu-item :deep(.v-list-item__prepend) {
  margin-inline-end: 12px !important;
  width: 20px;
  display: flex;
  justify-content: center;
}

.menu-item :deep(.v-icon) {
  font-size: 20px;
  color: #1976D2;
  transition: all 0.2s ease;
}

.menu-item::before {
  display: none;
}

.menu-item:not(.v-list-item--active):hover {
  background-color: rgba(33, 150, 243, 0.08);
  transform: none;
}

.menu-item:not(.v-list-item--active):hover :deep(.v-icon) {
  color: #1565C0;
}

/* Active Menu Item - Simple & Clean */
.menu-item.v-list-item--active {
  background: rgba(33, 150, 243, 0.1) !important;
  color: #1976D2 !important;
  font-weight: 600;
  box-shadow: none;
  border: none;
  border-radius: 8px;
  position: relative;
  overflow: visible;
  transform: none;
  margin: 0;
  animation: none;
}

.menu-item.v-list-item--active::before {
  display: none;
}

.menu-item.v-list-item--active :deep(.v-icon) {
  color: #1976D2;
}

.menu-item.v-list-item--active::after {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #1976D2;
  border-radius: 0 2px 2px 0;
}

.item-title {
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.4;
  color: #424242;
}

.menu-item.v-list-item--active .item-title {
  color: #1976D2;
  font-weight: 600;
}

.item-description {
  display: none;
}

/* Parent Menu Items (with dropdown) */
.parent-item {
  font-weight: 500;
}

.parent-item :deep(.v-list-group__header__append) {
  margin-inline-start: auto !important;
}

.parent-item :deep(.v-list-group__header__append .v-icon) {
  font-size: 18px;
  color: #9e9e9e;
}

/* Sub Items - Clean */
.sub-item {
  padding-left: 48px !important;
  min-height: 36px;
  margin-bottom: 2px;
}

.sub-item .item-title {
  font-size: 0.8125rem;
  font-weight: 400;
}

.sub-item:hover {
  background-color: #fafafa;
}

.sub-item.v-list-item--active {
  background: rgba(33, 150, 243, 0.08) !important;
}

.sub-item.v-list-item--active::after {
  left: 36px;
  height: 16px;
}

/* Menu Group */
.menu-group :deep(.v-list-group__items) {
  --indent-padding: 0px;
  padding-top: 4px;
  padding-bottom: 4px;
}

/* Badges - Premium Look (Matching User Image) */
.badges-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.badge-item :deep(.v-badge__badge) {
  font-size: 0.65rem !important;
  font-weight: 800 !important;
  min-width: 20px !important;
  height: 20px !important;
  padding: 0 6px !important;
  border-radius: 10px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* Specific Badge Styles (Outlined Style like example image) */
.badge-suspended :deep(.v-badge__badge) {
  background-color: #FFF5F5 !important;
  color: #E53E3E !important;
  border: 1.5px solid #FEB2B2 !important;
}

.badge-stopped :deep(.v-badge__badge) {
  background-color: #F7FAFC !important;
  color: #4A5568 !important;
  border: 1.5px solid #CBD5E0 !important;
}

.badge-unpaid :deep(.v-badge__badge) {
  background-color: #FFFAF0 !important;
  color: #DD6B20 !important;
  border: 1.5px solid #FBD38D !important;
}

.badge-total :deep(.v-badge__badge) {
  background-color: #EBF8FF !important;
  color: #3182CE !important;
  border: 1.5px solid #90CDF4 !important;
}

.badge-tickets :deep(.v-badge__badge) {
  background-color: #FFF5F5 !important;
  color: #C53030 !important;
  border: 1.5px solid #FC8181 !important;
}

/* Rail Mode */
.v-navigation-drawer--rail .navigation-list {
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.v-navigation-drawer--rail .menu-group-header {
  display: none;
}

.v-navigation-drawer--rail .menu-item {
  justify-content: center;
  padding: 0 !important;
  margin: 4px 0;
  width: 64px;
  height: 48px;
  display: flex;
  align-items: center;
  border-radius: 8px;
}

.v-navigation-drawer--rail .menu-item :deep(.v-list-item__prepend) {
  margin-inline-end: 0 !important;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
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

.v-navigation-drawer--rail .menu-item :deep(.v-icon) {
  opacity: 1 !important;
  font-size: 22px !important;
  margin: 0 auto !important;
}

.v-navigation-drawer--rail .menu-item.v-list-item--active::after {
  display: none;
}

.v-navigation-drawer--rail .menu-item.v-list-item--active {
  background: rgba(33, 150, 243, 0.15) !important;
}

/* Logout Section - Minimalist */
.logout-container {
  padding: 12px 23px;
  background: transparent;
  backdrop-filter: none;
  border-top: none;
}

.logout-btn {
  border-radius: 8px !important;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex !important;
  min-height: 40px;
  margin: 0;
  padding: 0 16px !important;
  background: #ffffff !important;
  color: #d32f2f !important;
  border: 1px solid #e0e0e0;
}

.logout-btn:hover {
  background: #ffebee !important;
  border-color: #d32f2f;
  box-shadow: none;
  transform: none;
}

.v-navigation-drawer--rail .logout-container {
  padding: 8px 4px;
}

.v-navigation-drawer--rail .logout-btn {
  min-width: 48px;
  width: 48px;
  height: 48px;
  padding: 0 !important;
  border-radius: 8px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
}

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

/* ==================== MAINTENANCE OVERLAY ==================== */

.maintenance-overlay {
  z-index: 9999 !important;
}

.maintenance-card {
  max-width: 600px;
  width: 90%;
  padding: 48px;
  border-radius: 24px !important;
  background: rgb(var(--v-theme-surface));
  text-align: center;
}

.maintenance-icon-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 32px;
}

.maintenance-icon {
  animation: float 3s ease-in-out infinite;
}

.maintenance-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: rgba(251, 191, 36, 0.1);
  animation: pulse-ring 2s ease-out infinite;
}

.maintenance-pulse::before,
.maintenance-pulse::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: rgba(251, 191, 36, 0.1);
}

.maintenance-pulse::before {
  width: 180px;
  height: 180px;
  animation: pulse-ring 2s ease-out infinite 0.5s;
}

.maintenance-pulse::after {
  width: 210px;
  height: 210px;
  animation: pulse-ring 2s ease-out infinite 1s;
}

@keyframes pulse-ring {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(0.8);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.maintenance-title {
  font-size: 2rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
}

.maintenance-message {
  font-size: 1.125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 24px;
  line-height: 1.6;
}

.maintenance-info {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(var(--v-theme-info), 0.1);
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 0.9375rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.maintenance-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.maintenance-btn {
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.02em;
  padding: 0 32px;
  height: 48px;
}

/* ==================== MAINTENANCE ADMIN BANNER ==================== */

.maintenance-admin-banner {
  height: 48px !important;
  font-size: 0.875rem !important;
  font-weight: 600;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.15), rgba(251, 191, 36, 0.05)) !important;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}

/* ==================== DARK THEME ==================== */

.v-theme--dark .modern-app {
  background-color: #0a0e1a;
}

.v-theme--dark .modern-drawer {
  background: #1a1f2e !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 0 24px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .sidebar-header-modern {
  background: #151b2d !important;
  border-bottom: none;
}

.v-theme--dark .app-title {
  color: #ffffff;
}

.v-theme--dark .app-subtitle {
  color: rgba(255, 255, 255, 0.6);
}

.v-theme--dark .toggle-btn:hover,
.v-theme--dark .close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

/* Navigation Container Dark Mode */
.v-theme--dark .navigation-container::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.2);
}

.v-theme--dark .navigation-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

/* Menu Group Header Dark Mode */
.v-theme--dark .group-title {
  color: rgba(255, 255, 255, 0.9);
}

/* Menu Items Dark Mode */
.v-theme--dark .menu-item {
  color: rgba(255, 255, 255, 0.87);
}

.v-theme--dark .menu-item:hover {
  background: rgba(255, 255, 255, 0.05) !important;
}

.v-theme--dark .menu-item.v-list-item--active {
  background: rgba(33, 150, 243, 0.15) !important;
  color: rgb(var(--v-theme-primary));
}

.v-theme--dark .menu-item.v-list-item--active::after {
  background: rgb(var(--v-theme-primary));
}

.v-theme--dark .item-title {
  color: rgba(255, 255, 255, 0.87);
}

.v-theme--dark .menu-item.v-list-item--active .item-title {
  color: rgb(var(--v-theme-primary));
}

.v-theme--dark .menu-item :deep(.v-icon) {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .menu-item.v-list-item--active :deep(.v-icon) {
  color: rgb(var(--v-theme-primary));
}

.v-theme--dark .menu-item:hover :deep(.v-icon) {
  color: rgba(255, 255, 255, 0.9);
}

/* Sub Items Dark Mode */
.v-theme--dark .sub-item {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .sub-item:hover {
  background: rgba(255, 255, 255, 0.05) !important;
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .sub-item.v-list-item--active {
  background: rgba(33, 150, 243, 0.1) !important;
  color: rgb(var(--v-theme-primary));
}

/* Logout Button Dark Mode */
.v-theme--dark .logout-container {
  background: rgba(10, 14, 26, 0.5);
}

.v-theme--dark .logout-btn {
  background: rgba(211, 47, 47, 0.15) !important;
  color: #ef5350 !important;
  border: 1px solid rgba(211, 47, 47, 0.3);
}

.v-theme--dark .logout-btn:hover {
  background: rgba(211, 47, 47, 0.25) !important;
  border-color: #ef5350;
}

/* App Bar Dark Mode */
.v-theme--dark .modern-app-bar {
  background: #151b2d !important;
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .app-bar-title {
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .header-icon-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* Mobile Bottom Nav Dark Mode */
.v-theme--dark .mobile-bottom-nav {
  background: #151b2d !important;
  border-top-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .mobile-bottom-nav :deep(.v-btn) {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .mobile-bottom-nav :deep(.v-btn--active) {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Footer Dark Mode */
.v-theme--dark .modern-footer {
  background: #151b2d;
  border-top-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.2);
}

.v-theme--dark .footer-content {
  color: rgba(255, 255, 255, 0.7);
}

/* Notification Dark Mode */
.v-theme--dark .modern-notification-container {
  background: #1a1f2e;
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .notification-header-section {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.15) 0%,
    rgba(var(--v-theme-secondary), 0.08) 100%
  );
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .notification-main-title {
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .notification-subtitle {
  color: rgba(255, 255, 255, 0.6);
}

.v-theme--dark .modern-notification-item {
  background: rgba(255, 255, 255, 0.03);
}

.v-theme--dark .modern-notification-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.v-theme--dark .modern-notification-item.notification-item-unread {
  background: rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .notification-title {
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .notification-message {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .notification-time {
  color: rgba(255, 255, 255, 0.5);
}

.v-theme--dark .empty-title {
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .empty-subtitle {
  color: rgba(255, 255, 255, 0.6);
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

/* ==================== RUNNING TEXT ==================== */

.running-text-container {
  overflow: hidden;
  position: relative;
  background: rgba(var(--v-theme-primary), 0.04);
  border-radius: 50px;
  height: 36px;
  display: flex;
  align-items: center;
  border: 1px dashed rgba(var(--v-theme-primary), 0.2);
  margin: 0 auto;
  mask-image: linear-gradient(to right, transparent 0%, black 5%, black 95%, transparent 100%);
  -webkit-mask-image: linear-gradient(to right, transparent 0%, black 5%, black 95%, transparent 100%);
}

.marquee-content {
  white-space: nowrap;
  animation: marquee 35s linear infinite;
  padding-left: 100%;
  display: flex;
  align-items: center;
  min-width: 100%;
}

.marquee-content span {
  display: flex;
  align-items: center;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.85rem;
  font-weight: 500;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}

/* Pause on hover */
.running-text-container:hover .marquee-content {
  animation-play-state: paused;
}
</style>