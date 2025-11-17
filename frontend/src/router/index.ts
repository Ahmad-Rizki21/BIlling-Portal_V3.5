// src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import DashboardView from '../views/DashboardView.vue';
import { getEncryptedToken } from '@/utils/crypto';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Rute untuk halaman yang memerlukan login (DIBUNGKUS OLEH DefaultLayout)
    {
      path: '/',
      component: DefaultLayout,
      meta: { requiresAuth: true },
      children: [
        // TAMBAHKAN INI: Jika user ke path '/', langsung arahkan ke dashboard
        { path: '', redirect: '/dashboard' },
        
        // Definisikan semua halaman di sini
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView
        },
        {
          path: 'users',
          name: 'users',
          // Gunakan lazy loading untuk performa yang lebih baik
          component: () => import('../views/UsersView.vue')
        },
        {
          path: 'roles',
          name: 'roles',
          component: () => import('../views/RolesView.vue')
        },
        {
          path: 'mikrotik',
          name: 'mikrotik',
          component: () => import('../views/MikrotikView.vue')
        },
        {
          path: 'pelanggan',
          name: 'pelanggan',
          component: () => import('../views/PelangganView.vue')
        },
        {
          path: 'langganan',
          name: 'langganan',
          component: () => import('../views/LanggananView.vue')
        },
        {
          path: 'langganan/:id/edit',
          name: 'edit-langganan',
          component: () => import('../views/EditLangganan.vue')
        },
        {
          path: 'harga-layanan',
          name: 'harga-layanan',
          component: () => import('../views/HargaLayananView.vue')
        },
        {
          path: 'data-teknis',
          name: 'data-teknis',
          component: () => import('../views/DataTeknisView.vue')
        },
        {
          path: 'traffic-monitoring',
          name: 'traffic-monitoring',
          component: () => import('../views/TrafficMonitoringView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_traffic_monitoring']
          }
        },
        {
          path: 'invoices',
          name: 'invoices',
          component: () => import('../views/InvoicesView.vue')
        },
        {
          path: 'permissions',
          name: 'permissions',
          component: () => import('../views/PermissionsView.vue')
        },
        {
          path: 'syarat-ketentuan',
          name: 'syarat-ketentuan',
          component: () => import('../views/SKView.vue')
        },
        {
          path: 'management/sk',
          name: 'sk-management',
          component: () => import('../views/SKManagementView.vue'),
          meta: { permission: 'manage_sk' } // Lindungi dengan permission
        },
        {
          path: 'kalkulator',
          name: 'kalkulator',
          component: () => import('../views/CalculatorView.vue'),
          meta: { permission: 'use_calculator' } // Beri permission jika perlu
        },
        {
          path: 'reports/revenue',
          name: 'revenue-report',
          component: () => import('../views/RevenueReportView.vue'),
          meta: { permission: 'view_reports_revenue' } 
        },
        {
          path: 'network-management/olt', // Buat URL yang rapi
          name: 'olt-management',
          component: () => import('../views/OLTView.vue'),
          meta: { permission: 'view_olt' } // Beri permission jika perlu
        },
        {
          path: 'odp-management', // URL yang akan diakses
          name: 'odp-management',
          component: () => import('../views/ODPView.vue'),
          meta: { permission: 'view_odp_management' } // Lindungi dengan permission
        },
        {
          path: '/topology/olt/:olt_id',
          name: 'TopologyView',
          component: () => import('@/views/TopologyView.vue'), // Halaman baru yang akan kita buat
          meta: { requiresAuth: true, layout: 'default' }
        },
        {
          path: '/management/settings', // URL untuk halaman pengaturan
          name: 'SystemSettings',
          component: () => import('@/views/Management/Settings.vue'),
          meta: { requiresAuth: true, layout: 'default' } // Pastikan hanya user terotentikasi yang bisa akses
        },
        {
          path: '/inventory',
          name: 'inventory',
          component: () => import('../views/InventoryView.vue'),
          meta: { requiresAuth: true } // Opsional: jika rute ini butuh login
        },
        {
          path: '/dashboard-pelanggan',
          name: 'DashboardPelanggan',
          component: () => import('@/views/DashboardPelangganView.vue'),
          meta: { 
            requiresAuth: true, 
            roles: ['Direktur', 'Admin', 'Monitoring']
          }
        },
        {
          path: '/activity-logs',
          name: 'ActivityLogs',
          component: () => import('@/views/ActivityLogView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_activity_log']
          },
        },
        {
          path: '/trouble-tickets',
          name: 'TroubleTickets',
          component: () => import('@/views/TroubleTicketView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_trouble_tickets']
          },
        },
        {
          path: '/trouble-tickets/:id',
          name: 'TroubleTicketDetail',
          component: () => import('@/views/TroubleTicketDetailView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_trouble_tickets']
          },
        },
        {
          path: '/trouble-tickets/:id/action',
          name: 'TicketAction',
          component: () => import('@/views/TicketActionView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_trouble_tickets']
          },
        },
        {
          path: '/trouble-tickets/reports',
          name: 'TroubleTicketReports',
          component: () => import('@/views/TroubleTicketReportView.vue'),
          meta: {
            requiresAuth: true,
            permissions: ['view_trouble_tickets']
          },
        },
      ],
    },
    

    // Rute untuk halaman login (TIDAK ADA LAYOUT)
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true }
    },
  ],
});

// Navigation guard Anda sudah benar, biarkan seperti ini.
router.beforeEach(async (to, _from, next) => {
  const token = getEncryptedToken('access_token');
  const isAuthenticated = !!token;
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/login');
  }
  
  if (to.meta.guest && isAuthenticated) {
    return next('/dashboard');
  }
  
  next();
});

export default router;