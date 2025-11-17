<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="header-card mb-4 mb-md-6">
      <div class="d-flex flex-column align-center gap-4">
        <div class="d-flex align-center header-info">
          <div class="header-avatar-wrapper">
            <v-avatar class="header-avatar" color="transparent" size="50">
              <v-icon color="white" size="28">mdi-history</v-icon>
            </v-avatar>
          </div>
          <div class="ml-4">
            <h1 class="header-title">Log Aktivitas</h1>
            <p class="header-subtitle">Melacak semua perubahan data penting dalam sistem</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Logs Card -->
    <v-card class="activity-card" elevation="0" rounded="xl">
      <!-- Card Header -->
      <div class="table-header">
        <v-card-title class="d-flex align-center pa-6">
          <div class="d-flex align-center flex-grow-1">
            <v-icon color="purple" size="24" class="me-3">mdi-format-list-bulleted</v-icon>
            <div>
              <h2 class="text-h6 font-weight-bold mb-0">Riwayat Aktivitas Pengguna</h2>
              <p class="text-caption text-medium-emphasis mb-0">
                {{ totalLogs }} total aktivitas tercatat
              </p>
            </div>
          </div>

          <!-- Refresh Button -->
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            color="purple"
            :loading="loading"
            @click="refreshData"
            class="refresh-btn"
          ></v-btn>
        </v-card-title>
      </div>

      <v-divider class="card-divider"></v-divider>

      <!-- Data Table -->
      <div class="table-container">
        <v-data-table-server
          v-model:items-per-page="itemsPerPage"
          :headers="headers"
          :items="logs"
          :items-length="totalLogs"
          :loading="loading"
          @update:options="fetchLogs"
          class="activity-table"
          :no-data-text="'Belum ada aktivitas yang tercatat'"
          loading-text="Memuat data log..."
          :items-per-page-options="[10, 25, 50, 100]"
        >
          <!-- User Column -->
          <template v-slot:item.user="{ item }">
            <div class="user-cell d-flex align-center py-2">
              <div class="user-avatar-wrapper me-3">
                <v-avatar size="36" class="user-avatar">
                  <div class="user-avatar-bg">
                    <span class="user-initial">{{ item.user.name.charAt(0).toUpperCase() }}</span>
                  </div>
                </v-avatar>
              </div>
              <div class="user-info">
                <div class="user-name font-weight-bold text-body-2">{{ item.user.name }}</div>
                <div class="user-email text-caption text-medium-emphasis">{{ item.user.email }}</div>
              </div>
            </div>
          </template>

          <!-- Action Column -->
          <template v-slot:item.action="{ item }">
            <v-chip 
              :color="getActionColor(item.action)" 
              variant="flat" 
              size="small" 
              class="action-chip font-weight-bold"
              label
            >
              <v-icon start size="16">{{ getActionIcon(item.action) }}</v-icon>
              {{ item.action }}
            </v-chip>
          </template>

          <!-- Timestamp Column -->
          <template v-slot:item.timestamp="{ item }">
            <div class="timestamp-cell">
              <div class="timestamp-primary text-body-2 font-weight-medium">
                {{ formatDate(item.timestamp) }}
              </div>
              <div class="timestamp-secondary text-caption text-medium-emphasis">
                {{ formatTime(item.timestamp) }}
              </div>
            </div>
          </template>

          <!-- Details Column -->
          <template v-slot:item.details="{ item }">
            <div class="details-cell text-center">
              <v-btn
                v-if="item.details"
                icon
                variant="text"
                size="small"
                color="primary"
                class="details-btn"
                @click="showDetails(item.details)"
              >
                <v-icon size="20">mdi-code-json</v-icon>
              </v-btn>
              <span v-else class="text-disabled">-</span>
            </div>
          </template>

          <!-- Loading State -->
          <template v-slot:loading>
            <div class="loading-container d-flex flex-column align-center justify-center pa-8">
              <v-progress-circular 
                indeterminate 
                color="primary" 
                size="48"
                width="4"
              ></v-progress-circular>
              <p class="text-body-2 text-medium-emphasis mt-4 mb-0">Memuat data log...</p>
            </div>
          </template>

          <!-- No Data State -->
          <template v-slot:no-data>
            <div class="no-data-container d-flex flex-column align-center justify-center pa-8">
              <v-icon size="64" color="disabled" class="mb-4">mdi-history-off</v-icon>
              <p class="text-h6 font-weight-medium text-medium-emphasis mb-2">Belum ada aktivitas</p>
              <p class="text-body-2 text-disabled mb-0">Data aktivitas akan muncul setelah ada perubahan sistem</p>
            </div>
          </template>
        </v-data-table-server>
      </div>
    </v-card>

    <!-- Details Dialog -->
    <v-dialog v-model="dialog" max-width="600" class="details-dialog">
      <v-card class="dialog-card" rounded="xl">
        <!-- Dialog Header -->
        <div class="dialog-header pa-4 pa-md-6">
          <div class="d-flex align-center">
            <div class="dialog-icon-wrapper me-3">
              <v-icon color="primary" size="24">mdi-code-braces</v-icon>
            </div>
            <div class="flex-grow-1">
              <h3 class="dialog-title text-h6 font-weight-bold mb-0">Detail Aktivitas</h3>
              <p class="dialog-subtitle text-caption text-medium-emphasis mb-0">Informasi lengkap perubahan data</p>
            </div>
            <v-btn 
              icon="mdi-close" 
              variant="text" 
              size="small"
              color="grey"
              @click="dialog = false"
              class="close-btn"
            ></v-btn>
          </div>
        </div>

        <v-divider class="dialog-divider"></v-divider>

        <!-- Dialog Content -->
        <div class="dialog-content">
          <v-list v-if="detailsObject" class="details-list">
            <template v-for="(value, key, index) in detailsObject" :key="key">
              <v-list-item class="detail-item px-4 px-md-6 py-3">
                <div class="detail-content w-100">
                  <div class="detail-key text-primary font-weight-bold text-body-2 mb-1">
                    {{ formatKey(key) }}
                  </div>
                  <div class="detail-value text-body-2 text-medium-emphasis">
                    {{ formatValue(value) }}
                  </div>
                </div>
              </v-list-item>
              <v-divider 
                v-if="index < Object.keys(detailsObject).length - 1" 
                class="detail-divider"
              ></v-divider>
            </template>
          </v-list>
        </div>

        <!-- Dialog Actions -->
        <div class="dialog-actions pa-4 pa-md-6">
          <v-spacer></v-spacer>
          <v-btn 
            variant="tonal" 
            color="primary"
            @click="dialog = false"
            class="close-dialog-btn"
          >
            Tutup
          </v-btn>
        </div>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import apiClient from '@/services/api';

interface User {
  id: number;
  name: string;
  email: string;
}

interface ActivityLog {
  id: number;
  user: User;
  timestamp: string;
  action: string;
  details?: string;
}

const logs = ref<ActivityLog[]>([]);
const loading = ref(true);
const totalLogs = ref(0);
const itemsPerPage = ref(10);

const dialog = ref(false);
const detailsObject = ref<Record<string, any> | null>(null);

const headers = [
  { title: 'Pengguna', key: 'user', sortable: false, width: '30%' },
  { title: 'Aksi', key: 'action', sortable: false, width: '25%' },
  { title: 'Waktu', key: 'timestamp', sortable: false, width: '25%' },
  { title: 'Detail', key: 'details', sortable: false, align: 'center', width: '20%' },
] as const;

async function fetchLogs({ page, itemsPerPage }: { page: number, itemsPerPage: number }) {
  loading.value = true;
  try {
    const response = await apiClient.get('/activity-logs', {
      params: {
        skip: (page - 1) * itemsPerPage,
        limit: itemsPerPage,
      },
    });
    logs.value = response.data.items;
    totalLogs.value = response.data.total;
  } catch (error) {
    console.error("Gagal mengambil data log aktivitas:", error);
  } finally {
    loading.value = false;
  }
}

function refreshData() {
  fetchLogs({ page: 1, itemsPerPage: itemsPerPage.value });
}

function getActionColor(action: string): string {
  if (action.startsWith('POST')) return 'success';
  if (action.startsWith('PATCH')) return 'warning';
  if (action.startsWith('DELETE')) return 'error';
  if (action.startsWith('GET')) return 'info';
  return 'grey';
}

function getActionIcon(action: string): string {
  if (action.startsWith('POST')) return 'mdi-plus-circle-outline';
  if (action.startsWith('PATCH')) return 'mdi-pencil-outline';
  if (action.startsWith('DELETE')) return 'mdi-delete-outline';
  if (action.startsWith('GET')) return 'mdi-eye-outline';
  return 'mdi-cog-outline';
}

function showDetails(details: string) {
  try {
    detailsObject.value = JSON.parse(details);
  } catch {
    detailsObject.value = { "raw_data": details };
  }
  dialog.value = true;
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
}

function formatValue(value: any): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString('id-ID', { 
    day: 'numeric',
    month: 'short', 
    year: 'numeric' 
  });
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString('id-ID', { 
    hour: '2-digit',
    minute: '2-digit'
  });
}
</script>

<style scoped>
/* Header Card - Mobile Optimized with Fixed Positioning */
.header-card {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  border-radius: 20px;
  padding: 24px;
  color: rgb(var(--v-theme-on-primary));
  box-shadow: 0 8px 32px rgba(var(--v-theme-primary), 0.25);
  position: relative;
}

.header-card .d-flex.flex-column {
  align-items: stretch !important; /* Changed from align-center to stretch */
}

.header-info {
  width: 100%;
  justify-content: flex-start;
  margin-bottom: 0; /* Reset margin */
}

.header-avatar-wrapper {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.header-title {
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 4px;
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  font-size: 0.95rem;
  opacity: 0.85;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Activity Card */
.activity-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.12);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.v-theme--dark .activity-card {
  background: rgba(var(--v-theme-surface), 0.8);
  border: 1px solid rgba(var(--v-border-color), 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
}

/* Table Header */
.table-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.table-header .v-card-title {
  background: transparent;
}



.refresh-btn {
  color: rgba(var(--v-theme-primary), 0.8);
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: rotate(180deg);
}

/* Table Styles */
.table-container {
  background: transparent;
}

.activity-table {
  background: transparent !important;
}

.activity-table :deep(.v-data-table-header) {
  background-color: rgba(var(--v-theme-surface-variant), 0.4) !important;
}

.activity-table :deep(.v-data-table-header th) {
  font-weight: 600 !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  font-size: 0.875rem !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1) !important;
  padding: 16px !important;
}

.activity-table :deep(tbody tr) {
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08) !important;
}

.activity-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.04) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.v-theme--dark .activity-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.activity-table :deep(td) {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08) !important;
  font-size: 0.9rem;
  padding: 16px !important;
}

/* User Cell */
.user-cell {
  min-height: 60px;
}

.user-avatar-wrapper {
  position: relative;
}

.user-avatar {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
  transition: all 0.3s ease;
}

.user-avatar-bg {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-initial {
  color: white;
  font-weight: 700;
  font-size: 0.875rem;
}

.user-name {
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.user-email {
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.2;
}

/* Action Chip */
.action-chip {
  font-size: 0.75rem !important;
  height: 28px !important;
  border-radius: 8px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.action-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Timestamp Cell */
.timestamp-cell {
  min-width: 120px;
}

.timestamp-primary {
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.timestamp-secondary {
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.2;
}

/* Details Cell */
.details-btn {
  color: rgba(var(--v-theme-primary), 0.8);
  transition: all 0.3s ease;
}

.details-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: scale(1.1);
}

/* Loading & No Data States */
.loading-container,
.no-data-container {
  min-height: 200px;
}

/* Dialog Styles */
.details-dialog :deep(.v-overlay__content) {
  border-radius: 16px;
}

.dialog-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.12);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.v-theme--dark .dialog-card {
  background: rgba(var(--v-theme-surface), 0.9);
  border: 1px solid rgba(var(--v-border-color), 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
}

.dialog-header {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.v-theme--dark .dialog-header {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.2);
}

.dialog-icon-wrapper {
  width: 40px;
  height: 40px;
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-title {
  color: rgb(var(--v-theme-on-surface));
}

.dialog-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.close-btn {
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.3s ease;
}

.close-btn:hover {
  background-color: rgba(var(--v-theme-error), 0.1);
  color: rgb(var(--v-theme-error));
}

/* Details List */
.details-list {
  max-height: 400px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.3) transparent;
}

.details-list::-webkit-scrollbar {
  width: 6px;
}

.details-list::-webkit-scrollbar-track {
  background: transparent;
}

.details-list::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
}

.detail-item {
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 4px 8px;
}

.detail-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.detail-key {
  font-size: 0.875rem;
}

.detail-value {
  font-size: 0.875rem;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 120px;
  overflow-y: auto;
}

.dialog-actions {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
}

.close-dialog-btn {
  text-transform: none;
  font-weight: 600;
  border-radius: 8px;
}

/* Responsive Design */
@media (max-width: 960px) {
  .header-title {
    font-size: 1.5rem;
  }

  .header-subtitle {
    font-size: 0.95rem;
  }
}

@media (max-width: 768px) {
  .activity-log-container {
    padding: 1rem !important;
  }

  .header-card {
    padding: 20px;
    margin-bottom: 1.5rem;
  }

  .header-avatar {
    width: 48px !important;
    height: 48px !important;
    margin-right: 12px !important;
  }

  .header-title {
    font-size: 1.5rem !important;
  }
  
  .table-header .v-card-title {
    padding: 1rem !important;
  }
  
  .activity-table :deep(th),
  .activity-table :deep(td) {
    padding: 12px 8px !important;
  }
  
  .user-cell {
    min-height: 50px;
  }
  
  .user-avatar {
    width: 32px !important;
    height: 32px !important;
  }
  
  .user-name {
    font-size: 0.875rem;
  }
  
  .user-email {
    font-size: 0.75rem;
  }
  
  .action-chip {
    font-size: 0.7rem !important;
    height: 24px !important;
  }
  
  .timestamp-cell {
    min-width: 100px;
  }
  
  .timestamp-primary,
  .timestamp-secondary {
    font-size: 0.8rem;
  }
  
  .dialog-card {
    margin: 1rem;
  }
  
  .dialog-header,
  .dialog-actions {
    padding: 1rem !important;
  }
  
  .detail-item {
    padding: 12px 1rem !important;
  }
}

@media (max-width: 480px) {
  .activity-log-container {
    padding: 0.75rem !important;
  }
  
  .header-avatar {
    width: 44px !important;
    height: 44px !important;
  }
  
  .header-title {
    font-size: 1.25rem !important;
  }
  
  .activity-table :deep(th),
  .activity-table :deep(td) {
    padding: 8px 4px !important;
    font-size: 0.8rem !important;
  }
  
  .user-name {
    font-size: 0.8rem;
  }
  
  .user-email {
    font-size: 0.7rem;
  }
  
  .action-chip {
    font-size: 0.65rem !important;
    height: 22px !important;
  }
  
  .timestamp-primary,
  .timestamp-secondary {
    font-size: 0.75rem;
  }
  
  .details-btn {
    width: 32px !important;
    height: 32px !important;
  }
  
  .dialog-card {
    margin: 0.5rem;
    max-height: none;
  }
  
  .details-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .detail-item-wrapper {
    padding: 0.75rem;
  }
  
  .value-container {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
}

/* Dark mode specific adjustments */
.v-theme--dark .dialog-icon-wrapper {
  background: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .action-chip {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .details-list::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.5);
}

.v-theme--dark .header-card {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
}

/* Header section background pattern - sama seperti menu lainnya */
.header-card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="50" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="30" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  pointer-events: none;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.activity-card {
  animation: fadeIn 0.6s ease-out;
}

.detail-item {
  animation: fadeIn 0.3s ease-out;
}
</style>