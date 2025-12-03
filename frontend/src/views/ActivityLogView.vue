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

    <!-- Filters Section -->
    <v-card class="filter-card mb-4 mb-md-6" elevation="0" rounded="xl">
      <v-card-title class="d-flex align-center pa-6">
        <v-icon color="purple" size="24" class="me-3">mdi-filter-variant</v-icon>
        <div>
          <h3 class="text-h6 font-weight-bold mb-0">Filter Pencarian</h3>
          <p class="text-caption text-primary mb-0">Temukan aktivitas dengan cepat</p>
        </div>
        <v-spacer></v-spacer>
        <v-btn
          v-if="hasActiveFilters"
          variant="text"
          color="error"
          prepend-icon="mdi-refresh"
          size="small"
          @click="clearFilters"
          class="clear-filters-btn"
        >
          Reset Filter
        </v-btn>
      </v-card-title>

      <v-divider class="filter-divider"></v-divider>

      <v-card-text class="filter-content pa-6">
        <v-row dense>
          <!-- Search Keyword -->
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.search"
              label="Cari aktivitas..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              placeholder="Kata kunci"
              class="search-field"
              @update:model-value="debouncedSearch"
            ></v-text-field>
          </v-col>

          <!-- User Filter -->
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.user_id"
              :items="userOptions"
              label="Pengguna"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              placeholder="Semua pengguna"
              item-title="name"
              item-value="id"
              class="user-filter"
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <!-- Action Filter -->
          <v-col cols="12" md="2">
            <v-select
              v-model="filters.action"
              :items="actionOptions"
              label="Aksi"
              prepend-inner-icon="mdi-cog"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              placeholder="Semua aksi"
              class="action-filter"
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <!-- Date Range Filter -->
          <v-col cols="12" md="4">
            <div class="d-flex gap-2">
              <v-text-field
                v-model="filters.date_from"
                type="date"
                label="Dari tanggal"
                prepend-inner-icon="mdi-calendar-start"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                class="date-from-filter"
                @update:model-value="applyFilters"
              ></v-text-field>
              <v-text-field
                v-model="filters.date_to"
                type="date"
                label="Sampai tanggal"
                prepend-inner-icon="mdi-calendar-end"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                class="date-to-filter"
                @update:model-value="applyFilters"
              ></v-text-field>
            </div>
          </v-col>
        </v-row>

        <!-- Active Filters Display -->
        <div v-if="hasActiveFilters" class="active-filters mt-4">
          <div class="d-flex align-center flex-wrap gap-2">
            <span class="text-caption text-primary me-2">Filter aktif:</span>
            <v-chip
              v-if="filters.search"
              color="primary"
              variant="tonal"
              size="small"
              closable
              @click:close="filters.search = ''; applyFilters()"
            >
              <v-icon start size="14">mdi-magnify</v-icon>
              {{ filters.search }}
            </v-chip>
            <v-chip
              v-if="filters.user_id"
              color="purple"
              variant="tonal"
              size="small"
              closable
              @click:close="filters.user_id = null; applyFilters()"
            >
              <v-icon start size="14">mdi-account</v-icon>
              {{ getUserDisplayName(filters.user_id) }}
            </v-chip>
            <v-chip
              v-if="filters.action"
              :color="getActionColor(filters.action)"
              variant="tonal"
              size="small"
              closable
              @click:close="filters.action = ''; applyFilters()"
            >
              <v-icon start size="14">{{ getActionIcon(filters.action) }}</v-icon>
              {{ filters.action }}
            </v-chip>
            <v-chip
              v-if="filters.date_from"
              color="indigo"
              variant="tonal"
              size="small"
              closable
              @click:close="filters.date_from = ''; applyFilters()"
            >
              <v-icon start size="14">mdi-calendar-start</v-icon>
              {{ formatDateFilter(filters.date_from) }}
            </v-chip>
            <v-chip
              v-if="filters.date_to"
              color="indigo"
              variant="tonal"
              size="small"
              closable
              @click:close="filters.date_to = ''; applyFilters()"
            >
              <v-icon start size="14">mdi-calendar-end</v-icon>
              {{ formatDateFilter(filters.date_to) }}
            </v-chip>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Activity Logs Card -->
    <v-card class="activity-card" elevation="0" rounded="xl">
      <!-- Card Header -->
      <div class="table-header">
        <v-card-title class="d-flex align-center pa-6">
          <div class="d-flex align-center flex-grow-1">
            <v-icon color="purple" size="24" class="me-3">mdi-format-list-bulleted</v-icon>
            <div>
              <h2 class="text-h6 font-weight-bold mb-0">Riwayat Aktivitas Pengguna</h2>
              <p class="text-caption text-primary mb-0">
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
                @click="showDetails(item.details, item)"
              >
                <v-icon size="20">mdi-code-json</v-icon>
              </v-btn>
              <span v-else class="text-info">-</span>
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
              <p class="text-h6 font-weight-medium text-primary mb-2">Belum ada aktivitas</p>
              <p class="text-body-2 text-info mb-0">Data aktivitas akan muncul setelah ada perubahan sistem</p>
            </div>
          </template>
        </v-data-table-server>
      </div>
    </v-card>

    <!-- Enhanced Details Dialog -->
    <v-dialog v-model="dialog" max-width="800" class="details-dialog" persistent>
      <v-card class="dialog-card" rounded="xl">
        <!-- Dialog Header with Gradient -->
        <div class="dialog-header-enhanced pa-4 pa-md-6">
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <div class="dialog-icon-wrapper-enhanced me-3">
                <v-icon color="white" size="28">mdi-information-outline</v-icon>
              </div>
              <div>
                <h3 class="dialog-title-enhanced text-h5 font-weight-bold mb-0">Detail Aktivitas</h3>
                <p class="dialog-subtitle-enhanced text-caption mb-0">Informasi lengkap perubahan data sistem</p>
              </div>
            </div>
            <v-btn
              icon="mdi-close"
              variant="elevated"
              size="small"
              color="white"
              class="close-btn-enhanced"
              @click="dialog = false"
            ></v-btn>
          </div>
        </div>

        <!-- Dialog Content with Cards -->
        <div class="dialog-content-enhanced pa-6">
          <!-- Summary Section -->
          <div v-if="selectedLog" class="summary-section mb-6">
            <div class="summary-header d-flex align-center mb-4">
              <div class="summary-avatar-wrapper me-3">
                <v-avatar size="48" class="summary-avatar">
                  <div class="summary-avatar-bg">
                    <span class="summary-initial">{{ selectedLog.user.name.charAt(0).toUpperCase() }}</span>
                  </div>
                </v-avatar>
              </div>
              <div class="summary-info flex-grow-1">
                <h4 class="summary-user-name text-h6 font-weight-bold mb-1">{{ selectedLog.user.name }}</h4>
                <div class="summary-user-email text-body-2 text-medium-emphasis mb-2">{{ selectedLog.user.email }}</div>
                <div class="d-flex align-center gap-2">
                  <v-chip
                    :color="getActionColor(selectedLog.action)"
                    variant="elevated"
                    size="small"
                    class="summary-action-chip font-weight-bold"
                    label
                  >
                    <v-icon start size="16">{{ getActionIcon(selectedLog.action) }}</v-icon>
                    {{ selectedLog.action }}
                  </v-chip>
                  <v-chip
                    color="info"
                    variant="tonal"
                    size="small"
                    class="timestamp-chip"
                    label
                  >
                    <v-icon start size="14">mdi-clock-outline</v-icon>
                    {{ formatFullDateTime(selectedLog.timestamp) }}
                  </v-chip>
                </div>
              </div>
            </div>
          </div>

          <!-- Details Content -->
          <div v-if="detailsObject" class="details-content">
            <!-- Action Path -->
            <v-card class="detail-card mb-4" elevation="0" variant="outlined">
              <v-card-title class="detail-card-header d-flex align-center pa-4">
                <v-icon color="primary" size="20" class="me-2">mdi-route</v-icon>
                <span class="text-subtitle-1 font-weight-bold">Action Path</span>
              </v-card-title>
              <v-divider class="detail-divider"></v-divider>
              <v-card-text class="pa-4">
                <code class="action-path">{{ selectedLog?.action || 'N/A' }}</code>
              </v-card-text>
            </v-card>

            <!-- Request Details -->
            <v-card class="detail-card mb-4" elevation="0" variant="outlined">
              <v-card-title class="detail-card-header d-flex align-center pa-4">
                <v-icon color="success" size="20" class="me-2">mdi-code-json</v-icon>
                <span class="text-subtitle-1 font-weight-bold">Request Details</span>
                <v-spacer></v-spacer>
                <v-btn
                  icon="mdi-content-copy"
                  variant="text"
                  size="small"
                  color="primary"
                  @click="copyToClipboard(JSON.stringify(detailsObject, null, 2))"
                  class="copy-btn"
                >
                  <v-icon size="18">mdi-content-copy</v-icon>
                </v-btn>
              </v-card-title>
              <v-divider class="detail-divider"></v-divider>
              <v-card-text class="pa-4">
                <div class="details-grid">
                  <template v-for="(value, key, index) in detailsObject" :key="key">
                    <div class="detail-item-enhanced">
                      <div class="detail-label">
                        <v-icon size="16" class="label-icon">mdi-chevron-right</v-icon>
                        <span class="label-text">{{ formatKey(key) }}</span>
                      </div>
                      <div class="detail-value-wrapper">
                        <div class="detail-value-content">
                          {{ formatValueEnhanced(value) }}
                        </div>
                        <v-chip
                          v-if="getValueType(value) !== 'string'"
                          :color="getValueTypeColor(getValueType(value))"
                          variant="tonal"
                          size="x-small"
                          class="value-type-chip ml-2"
                        >
                          {{ getValueType(value) }}
                        </v-chip>
                      </div>
                    </div>
                    <v-divider
                      v-if="index < Object.keys(detailsObject).length - 1"
                      class="detail-divider-enhanced my-3"
                    ></v-divider>
                  </template>
                </div>
              </v-card-text>
            </v-card>
          </div>

          <!-- Empty State -->
          <div v-else class="empty-state text-center py-8">
            <v-icon size="64" color="disabled" class="mb-4">mdi-information-off-outline</v-icon>
            <p class="text-h6 font-weight-medium text-primary mb-2">Tidak Ada Detail</p>
            <p class="text-body-2 text-info mb-0">Aktivitas ini tidak memiliki informasi detail tambahan</p>
          </div>
        </div>

        <!-- Dialog Actions -->
        <div class="dialog-actions-enhanced pa-4 pa-md-6">
          <v-btn
            variant="tonal"
            color="info"
            prepend-icon="mdi-download"
            @click="downloadDetails"
            class="action-btn me-3"
          >
            Export JSON
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            variant="elevated"
            color="primary"
            prepend-icon="mdi-close"
            @click="dialog = false"
            class="action-btn"
          >
            Tutup
          </v-btn>
        </div>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import apiClient from '@/services/api';
import { debounce } from 'lodash-es';

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

interface Filters {
  search: string;
  user_id: number | null;
  action: string;
  date_from: string;
  date_to: string;
}

const logs = ref<ActivityLog[]>([]);
const loading = ref(true);
const totalLogs = ref(0);
const itemsPerPage = ref(10);
const users = ref<User[]>([]);

const dialog = ref(false);
const detailsObject = ref<Record<string, any> | null>(null);
const selectedLog = ref<ActivityLog | null>(null);

// Filters state
const filters = ref<Filters>({
  search: '',
  user_id: null,
  action: '',
  date_from: '',
  date_to: ''
});

const headers = [
  { title: 'Pengguna', key: 'user', sortable: false, width: '30%' },
  { title: 'Aksi', key: 'action', sortable: false, width: '25%' },
  { title: 'Waktu', key: 'timestamp', sortable: false, width: '25%' },
  { title: 'Detail', key: 'details', sortable: false, align: 'center', width: '20%' },
] as const;

// Computed properties
const hasActiveFilters = computed(() => {
  return filters.value.search ||
         filters.value.user_id ||
         filters.value.action ||
         filters.value.date_from ||
         filters.value.date_to;
});

const userOptions = computed(() => {
  return [
    { title: 'Semua pengguna', value: null },
    ...users.value.map(user => ({
      title: user.name,
      value: user.id,
      subtitle: user.email
    }))
  ];
});

const actionOptions = computed(() => [
  { title: 'POST (Create)', value: 'POST' },
  { title: 'PATCH (Update)', value: 'PATCH' },
  { title: 'DELETE (Remove)', value: 'DELETE' },
  { title: 'GET (View)', value: 'GET' }
]);

// Debounced search function
const debouncedSearch = debounce(() => {
  applyFilters();
}, 500);

// Watch for filter changes
watch(() => filters.value, (newFilters) => {
  console.log('Filters changed:', newFilters);
}, { deep: true });

async function fetchUsers() {
  try {
    const response = await apiClient.get('/users', {
      params: {
        skip: 0,
        limit: 1000, // Get all users for filter options
      },
    });
    users.value = response.data.items;
  } catch (error) {
    console.error("Gagal mengambil data users:", error);
  }
}

async function fetchLogs({ page, itemsPerPage }: { page: number, itemsPerPage: number }) {
  loading.value = true;
  try {
    const params: any = {
      skip: (page - 1) * itemsPerPage,
      limit: itemsPerPage,
    };

    // Add filters to params
    if (filters.value.search) params.search = filters.value.search;
    if (filters.value.user_id) params.user_id = filters.value.user_id;
    if (filters.value.action) params.action = filters.value.action;
    if (filters.value.date_from) params.date_from = filters.value.date_from;
    if (filters.value.date_to) params.date_to = filters.value.date_to;

    const response = await apiClient.get('/activity-logs', { params });
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

function applyFilters() {
  // Reset to first page when filters are applied
  fetchLogs({ page: 1, itemsPerPage: itemsPerPage.value });
}

function clearFilters() {
  filters.value = {
    search: '',
    user_id: null,
    action: '',
    date_from: '',
    date_to: ''
  };
  applyFilters();
}

function getUserDisplayName(userId: number): string {
  const user = users.value.find(u => u.id === userId);
  return user ? user.name : `User ${userId}`;
}

function formatDateFilter(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
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

function showDetails(details: string, log: ActivityLog) {
  selectedLog.value = log;
  try {
    detailsObject.value = JSON.parse(details);
  } catch {
    detailsObject.value = { "raw_data": details };
  }
  dialog.value = true;
}

function formatFullDateTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('id-ID', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function formatValueEnhanced(value: any): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? '✓ Ya' : '✗ Tidak';
  if (typeof value === 'number') return value.toLocaleString('id-ID');
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function getValueType(value: any): string {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'string') return 'string';
  if (Array.isArray(value)) return 'array';
  return 'object';
}

function getValueTypeColor(type: string): string {
  const colors: Record<string, string> = {
    'string': 'blue',
    'number': 'green',
    'boolean': 'purple',
    'object': 'orange',
    'array': 'teal',
    'null': 'grey'
  };
  return colors[type] || 'grey';
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    // Show toast notification here if you have one
    console.log('Copied to clipboard!');
  } catch (err) {
    console.error('Failed to copy:', err);
  }
}

function downloadDetails() {
  if (!detailsObject.value || !selectedLog.value) return;

  const data = {
    log_info: {
      id: selectedLog.value.id,
      user: selectedLog.value.user,
      action: selectedLog.value.action,
      timestamp: selectedLog.value.timestamp
    },
    details: detailsObject.value
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `activity-log-${selectedLog.value.id}-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
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

// Initialize component
fetchUsers();
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
  opacity: 1;
  line-height: 1.3;
  color: white !important;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Filter Card */
.filter-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.12);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.v-theme--dark .filter-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.3);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.filter-card .v-card-title {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.04) 0%, rgba(var(--v-theme-secondary), 0.04) 100%);
}

.v-theme--dark .filter-card .v-card-title {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.08) 0%, rgba(var(--v-theme-secondary), 0.08) 100%);
}

.filter-divider {
  border-color: rgba(var(--v-border-color), 0.08) !important;
}

.filter-content {
  background: transparent;
}

.search-field,
.user-filter,
.action-filter,
.date-from-filter,
.date-to-filter {
  transition: all 0.3s ease;
}

.search-field :deep(.v-field),
.user-filter :deep(.v-field),
.action-filter :deep(.v-field),
.date-from-filter :deep(.v-field),
.date-to-filter :deep(.v-field) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-field :deep(.v-field:hover),
.user-filter :deep(.v-field:hover),
.action-filter :deep(.v-field:hover),
.date-from-filter :deep(.v-field:hover),
.date-to-filter :deep(.v-field:hover) {
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.1);
}

.search-field :deep(.v-field--focused),
.user-filter :deep(.v-field--focused),
.action-filter :deep(.v-field--focused),
.date-from-filter :deep(.v-field--focused),
.date-to-filter :deep(.v-field--focused) {
  box-shadow: 0 2px 12px rgba(var(--v-theme-primary), 0.2);
}

.clear-filters-btn {
  text-transform: none;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.clear-filters-btn:hover {
  background-color: rgba(var(--v-theme-error), 0.08);
  color: rgb(var(--v-theme-error));
}

.active-filters {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
}

.active-filters .v-chip {
  font-weight: 600;
  transition: all 0.3s ease;
}

.active-filters .v-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
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
  color: rgb(var(--v-theme-primary));
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
  color: rgb(var(--v-theme-primary));
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
  color: rgb(var(--v-theme-primary));
  line-height: 1.2;
}

/* Details Cell */
.details-btn {
  color: rgb(var(--v-theme-primary));
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

/* Enhanced Dialog Styles */
.details-dialog :deep(.v-overlay__content) {
  border-radius: 20px;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog-card {
  background: rgb(var(--v-theme-surface));
  border: none;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  transition: all 0.3s ease;
}

.v-theme--dark .dialog-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(30px);
}

/* Enhanced Header */
.dialog-header-enhanced {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  color: white;
  position: relative;
  overflow: hidden;
}

.dialog-header-enhanced::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="50" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="30" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  pointer-events: none;
}

.dialog-icon-wrapper-enhanced {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.dialog-title-enhanced {
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.dialog-subtitle-enhanced {
  color: white !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.close-btn-enhanced {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.close-btn-enhanced:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  transform: scale(1.05);
}

/* Summary Section */
.summary-section {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.04) 0%, rgba(var(--v-theme-secondary), 0.04) 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(var(--v-border-color), 0.08);
}

.summary-avatar-wrapper {
  position: relative;
}

.summary-avatar {
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.2);
  transition: all 0.3s ease;
}

.summary-avatar-bg {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-initial {
  color: white;
  font-weight: 700;
  font-size: 1.2rem;
}

.summary-user-name {
  color: rgb(var(--v-theme-on-surface));
}

.summary-user-email {
  color: rgb(var(--v-theme-primary));
}

.summary-action-chip {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timestamp-chip {
  font-size: 0.75rem;
}

/* Detail Cards */
.detail-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.detail-card:hover {
  box-shadow: 0 4px 20px rgba(var(--v-theme-primary), 0.1);
  transform: translateY(-2px);
}

.detail-card-header {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
}

.detail-divider {
  border-color: rgba(var(--v-border-color), 0.08) !important;
  margin: 0;
}

.action-path {
  background: rgba(var(--v-theme-primary), 0.08);
  padding: 8px 12px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-primary));
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  display: inline-block;
}

/* Details Grid */
.details-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item-enhanced {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), 0.06);
  transition: all 0.3s ease;
}

.detail-item-enhanced:hover {
  background: rgba(var(--v-theme-primary), 0.04);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.1);
  transform: translateY(-1px);
}

.detail-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-icon {
  color: rgb(var(--v-theme-primary));
}

.label-text {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.875rem;
  text-transform: capitalize;
}

.detail-value-wrapper {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.detail-value-content {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  background: rgba(var(--v-theme-surface), 0.5);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  line-height: 1.4;
}

.value-type-chip {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.625rem;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.detail-divider-enhanced {
  border-color: rgba(var(--v-border-color), 0.12) !important;
  margin: 0 !important;
  border-width: 1px;
  border-style: dashed;
}

/* Copy Button */
.copy-btn {
  transition: all 0.3s ease;
}

.copy-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
  transform: scale(1.05);
}

/* Empty State */
.empty-state {
  padding: 32px;
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 12px;
  border: 2px dashed rgba(var(--v-border-color), 0.2);
}

/* Enhanced Dialog Actions */
.dialog-actions-enhanced {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.4) 0%, rgba(var(--v-theme-surface-variant), 0.2) 100%);
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
}

.action-btn {
  text-transform: none;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.3s ease;
  min-width: 120px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Scrollbar Styles */
.detail-value-content::-webkit-scrollbar {
  width: 6px;
}

.detail-value-content::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface), 0.3);
  border-radius: 3px;
}

.detail-value-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
}

.detail-value-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* Dark mode adjustments */
.v-theme--dark .summary-section {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.08) 0%, rgba(var(--v-theme-secondary), 0.08) 100%);
  border: 1px solid rgba(var(--v-border-color), 0.15);
}

.v-theme--dark .detail-item-enhanced {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

.v-theme--dark .detail-value-content {
  background: rgba(var(--v-theme-surface), 0.3);
  border: 1px solid rgba(var(--v-border-color), 0.15);
}

.v-theme--dark .dialog-actions-enhanced {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.2) 0%, rgba(var(--v-theme-surface-variant), 0.1) 100%);
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