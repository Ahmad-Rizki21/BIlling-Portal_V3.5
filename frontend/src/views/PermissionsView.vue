<template>
  <v-container fluid class="pa-0">
    <!-- Modern Header with Gradient Background -->
    <div class="header-section">
      <v-container class="pa-6">
        <div class="d-flex align-center">
          <div class="header-icon-wrapper me-4">
            <v-avatar class="header-avatar" color="transparent" size="56">
              <v-icon color="white" size="28">mdi-shield-key</v-icon>
            </v-avatar>
          </div>
          <div class="flex-grow-1">
            <h1 class="header-title text-white mb-1">Permissions Management</h1>
            <p class="header-subtitle text-white mb-0 opacity-90">Kelola semua hak akses sistem dengan mudah dan aman</p>
          </div>
          <v-btn 
            color="white" 
            variant="elevated"
            size="large"
            elevation="0"
            @click="generatePermissions"
            :loading="generating"
            prepend-icon="mdi-auto-fix"
            class="text-none font-weight-bold generate-btn"
            :class="{ 'generate-btn--loading': generating }"
          >
            <span class="text-purple">Auto Generate Permissions</span>
          </v-btn>
        </div>
      </v-container>
    </div>

    <!-- Main Content Area -->
    <v-container class="pa-6">
      <!-- Stats Cards -->
      <div class="stats-section mb-6">
        <v-row>
          <v-col cols="12" sm="6" md="3">
            <v-card class="stats-card stats-card--purple" elevation="0">
              <v-card-text class="pa-4">
                <div class="d-flex align-center">
                  <div class="stats-icon me-3">
                    <v-icon color="purple" size="24">mdi-shield-check</v-icon>
                  </div>
                  <div>
                    <div class="text-h5 font-weight-bold text-purple">{{ permissions.length }}</div>
                    <div class="text-caption text-medium-emphasis">Total Permissions</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="stats-card stats-card--success" elevation="0">
              <v-card-text class="pa-4">
                <div class="d-flex align-center">
                  <div class="stats-icon me-3">
                    <v-icon color="success" size="24">mdi-plus-circle</v-icon>
                  </div>
                  <div>
                    <div class="text-h5 font-weight-bold text-success">{{ createPermissions }}</div>
                    <div class="text-caption text-medium-emphasis">Create Permissions</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="stats-card stats-card--info" elevation="0">
              <v-card-text class="pa-4">
                <div class="d-flex align-center">
                  <div class="stats-icon me-3">
                    <v-icon color="info" size="24">mdi-eye</v-icon>
                  </div>
                  <div>
                    <div class="text-h5 font-weight-bold text-info">{{ viewPermissions }}</div>
                    <div class="text-caption text-medium-emphasis">View Permissions</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="stats-card stats-card--error" elevation="0">
              <v-card-text class="pa-4">
                <div class="d-flex align-center">
                  <div class="stats-icon me-3">
                    <v-icon color="error" size="24">mdi-delete</v-icon>
                  </div>
                  <div>
                    <div class="text-h5 font-weight-bold text-error">{{ deletePermissions }}</div>
                    <div class="text-caption text-medium-emphasis">Delete Permissions</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Enhanced Permissions Table -->
      <v-card class="permissions-table-card" elevation="0">
        <div class="table-header">
          <v-card-title class="d-flex align-center pa-6">
            <div class="d-flex align-center flex-grow-1">
              <v-icon color="purple" size="24" class="me-3">mdi-format-list-bulleted</v-icon>
              <span class="text-h6 font-weight-bold">Daftar Hak Akses</span>
            </div>
            <div class="d-flex align-center gap-3">
              <v-text-field
                v-model="search"
                prepend-inner-icon="mdi-magnify"
                label="Cari permissions..."
                variant="outlined"
                density="compact"
                hide-details
                class="search-field"
                clearable
              />
              <v-chip 
                :color="permissions.length > 0 ? 'purple' : 'grey'" 
                variant="tonal" 
                size="small"
                class="permissions-counter"
              >
                <v-icon start size="16">mdi-counter</v-icon>
                {{ filteredPermissions.length }} permissions
              </v-chip>
            </div>
          </v-card-title>
        </div>

        <v-divider />

        <v-data-table
          :headers="headers"
          :items="filteredPermissions"
          :loading="loading"
          :search="search"
          item-value="id"
          items-per-page="20"
          class="permissions-table"
          loading-text="Memuat permissions..."
          no-data-text="Tidak ada permissions ditemukan"
        >
          <template v-slot:loading>
            <v-skeleton-loader type="table-row@5" />
          </template>

          <template v-slot:item.id="{ item }">
            <div class="id-cell">
              <v-chip size="small" variant="outlined" color="grey-darken-1">
                #{{ item.id }}
              </v-chip>
            </div>
          </template>

          <template v-slot:item.name="{ item }">
            <div class="permission-name-cell">
              <v-chip 
                :color="getActionColor(item.name)" 
                variant="flat"
                size="default"
                class="permission-chip"
              >
                <v-icon 
                  :icon="getActionIcon(item.name)" 
                  size="16" 
                  start
                />
                {{ formatPermissionName(item.name) }}
              </v-chip>
            </div>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="actions-cell">
              <v-tooltip :text="`View details for ${formatPermissionName(item.name)}`">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    icon="mdi-information-outline"
                    size="small"
                    variant="text"
                    color="info"
                    @click="viewPermissionDetails(item)"
                  />
                </template>
              </v-tooltip>
            </div>
          </template>

          <template v-slot:bottom>
            <div class="table-footer">
              <v-divider />
              <div class="d-flex justify-center pa-4">
                <v-pagination
                  v-model="page"
                  :length="Math.ceil(filteredPermissions.length / itemsPerPage)"
                  :total-visible="5"
                  color="purple"
                  rounded
                />
              </div>
            </div>
          </template>
        </v-data-table>
      </v-card>
    </v-container>
    
    <!-- Enhanced Snackbar -->
    <v-snackbar 
      v-model="snackbar.show" 
      :color="snackbar.color" 
      :timeout="4000"
      location="top right"
      variant="elevated"
      class="custom-snackbar"
    >
      <div class="d-flex align-center">
        <v-icon 
          :icon="getSnackbarIcon(snackbar.color)" 
          size="20" 
          class="me-2"
        />
        {{ snackbar.text }}
      </div>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';

interface Permission {
  id: number;
  name: string;
}

const permissions = ref<Permission[]>([]);
const loading = ref(true);
const generating = ref(false);
const search = ref('');
const page = ref(1);
const itemsPerPage = ref(20);
const snackbar = ref({ show: false, text: '', color: 'success' });

const headers = [
  { title: 'ID', key: 'id', width: '120px', sortable: true },
  { title: 'Permission Name', key: 'name', sortable: true },
  { title: 'Actions', key: 'actions', width: '100px', sortable: false },
];

// Computed properties untuk stats
const createPermissions = computed(() => 
  permissions.value.filter(p => p.name.startsWith('create')).length
);

const viewPermissions = computed(() => 
  permissions.value.filter(p => p.name.startsWith('view')).length
);

const deletePermissions = computed(() => 
  permissions.value.filter(p => p.name.startsWith('delete')).length
);

const filteredPermissions = computed(() => {
  if (!search.value) return permissions.value;
  return permissions.value.filter(permission =>
    permission.name.toLowerCase().includes(search.value.toLowerCase())
  );
});

onMounted(fetchPermissions);

async function fetchPermissions() {
  loading.value = true;
  try {
    const response = await apiClient.get('/permissions/');
    permissions.value = response.data;
  } catch (error) {
    showSnackbar('Gagal memuat permissions', 'error');
  } finally {
    loading.value = false;
  }
}

async function generatePermissions() {
  generating.value = true;
  try {
    await apiClient.post('/permissions/generate');
    showSnackbar('Permissions berhasil di-generate!', 'success');
    fetchPermissions();
  } catch (error: any) {
    if (error.response && error.response.status === 200) {
      showSnackbar(error.response.data.detail, 'info');
    } else {
      showSnackbar('Gagal men-generate permissions', 'error');
    }
  } finally {
    generating.value = false;
  }
}

function getActionColor(name: string) {
  if (name.startsWith('create')) return 'success';
  if (name.startsWith('view')) return 'info';
  if (name.startsWith('edit')) return 'warning';
  if (name.startsWith('delete')) return 'error';
  return 'grey';
}

function getActionIcon(name: string) {
  if (name.startsWith('create')) return 'mdi-plus-circle';
  if (name.startsWith('view')) return 'mdi-eye';
  if (name.startsWith('edit')) return 'mdi-pencil';
  if (name.startsWith('delete')) return 'mdi-delete';
  return 'mdi-shield';
}

function formatPermissionName(name: string) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getSnackbarIcon(color: string) {
  switch (color) {
    case 'success': return 'mdi-check-circle';
    case 'error': return 'mdi-alert-circle';
    case 'info': return 'mdi-information';
    case 'warning': return 'mdi-alert';
    default: return 'mdi-information';
  }
}

function viewPermissionDetails(permission: Permission) {
  showSnackbar(`Viewing details for: ${formatPermissionName(permission.name)}`, 'info');
}

function showSnackbar(text: string, color: string) {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}
</script>

<style scoped>
/* Header Gradient */
.header-section {
  background: linear-gradient(135deg, #7C3AED 0%, #A855F7 50%, #C084FC 100%);
  position: relative;
  overflow: hidden;
}

.header-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)" /></svg>');
  opacity: 0.3;
}

.header-icon-wrapper {
  position: relative;
  z-index: 1;
}

.header-avatar {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.header-title {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header-subtitle {
  font-size: 1.1rem;
  font-weight: 400;
}

.generate-btn {
  transition: all 0.3s ease;
  border-radius: 12px !important;
  backdrop-filter: blur(10px);
}

.generate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(124, 58, 237, 0.3) !important;
}

.generate-btn--loading {
  pointer-events: none;
}

/* Stats Cards */
.stats-section {
  margin-top: -30px;
  position: relative;
  z-index: 2;
}

.stats-card {
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  background: white;
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1) !important;
}

.stats-card--purple:hover {
  box-shadow: 0 12px 40px rgba(124, 58, 237, 0.15) !important;
}

.stats-card--success:hover {
  box-shadow: 0 12px 40px rgba(34, 197, 94, 0.15) !important;
}

.stats-card--info:hover {
  box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15) !important;
}

.stats-card--error:hover {
  box-shadow: 0 12px 40px rgba(239, 68, 68, 0.15) !important;
}

.stats-icon {
  background: rgba(124, 58, 237, 0.1);
  border-radius: 12px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Table Card */
.permissions-table-card {
  border-radius: 20px !important;
  border: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
  background: white;
}

.table-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.search-field {
  max-width: 300px;
}

.search-field :deep(.v-field) {
  border-radius: 12px !important;
}

.permissions-counter {
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* Table Styles */
.permissions-table :deep(.v-data-table__wrapper) {
  border-radius: 0;
}

.permissions-table :deep(.v-data-table-header) {
  background-color: #fafbfc;
}

.permissions-table :deep(.v-data-table-header th) {
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb !important;
}

.permissions-table :deep(.v-data-table__tr:hover) {
  background-color: #f9fafb !important;
}

.id-cell {
  padding: 8px 0;
}

.permission-name-cell {
  padding: 8px 0;
}

.permission-chip {
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: 10px !important;
  padding: 0 4px;
}

.actions-cell {
  padding: 8px 0;
}

.table-footer {
  background: #fafbfc;
}

/* Custom Snackbar */
.custom-snackbar :deep(.v-snackbar__wrapper) {
  border-radius: 12px !important;
  backdrop-filter: blur(10px);
}

/* Responsive Design */
@media (max-width: 960px) {
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 0.95rem;
  }
  
  .generate-btn {
    size: medium;
  }
  
  .search-field {
    max-width: 200px;
  }
}

@media (max-width: 600px) {
  .stats-section {
    margin-top: -20px;
  }
  
  .permissions-table-card {
    border-radius: 16px !important;
  }
  
  .table-header .v-card-title {
    flex-direction: column;
    align-items: stretch !important;
    gap: 16px;
  }
  
  .search-field {
    max-width: 100%;
  }
}

/* Loading Animation */
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.v-skeleton-loader {
  animation: pulse 1.5s ease-in-out infinite;
}

/* Smooth Transitions */
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
}
</style>