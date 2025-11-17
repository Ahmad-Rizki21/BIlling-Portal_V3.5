<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <div class="d-flex align-center">
              <v-avatar class="me-4 elevation-4" color="primary" size="80">
                <v-icon color="white" size="40">mdi-server</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-2">Mikrotik Servers</h1>
                <p class="header-subtitle mb-0">
                  Kelola koneksi ke server Mikrotik Anda
                </p>
              </div>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              color="white"
              variant="elevated"
              size="large"
              elevation="4"
              @click="openDialog()"
              prepend-icon="mdi-plus-circle-outline"
              class="text-none font-weight-bold w-100 w-md-auto rounded-lg"
              style="color: #4338ca !important;"
            >
              Tambah Server
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">

    <v-card class="filter-card mb-6" elevation="0">
      <div class="d-flex flex-wrap align-center gap-4 pa-4">
        <v-text-field
          v-model="searchQuery"
          label="Cari Server (Nama atau IP)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          class="flex-grow-1"
          style="min-width: 300px;"
        ></v-text-field>

        <v-select
          v-model="selectedIsActive"
          :items="[{title: 'Aktif', value: true}, {title: 'Nonaktif', value: false}]"
          label="Filter Status Server"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 200px;"
        ></v-select>
        
        <v-select
          v-model="selectedConnectionStatus"
          :items="['Success', 'Failed']"
          label="Filter Status Koneksi"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 200px;"
        ></v-select>

        <v-btn
            variant="text"
            @click="resetFilters"
            class="text-none"
        >
          Reset Filter
        </v-btn>
      </div>
    </v-card>
    <v-card elevation="3" class="rounded-lg">
      </v-card>

    <!-- Main Data Table Card -->
    <v-card elevation="3" class="rounded-lg">
      <v-card-title class="d-flex align-center pa-6 bg-grey-lighten-5">
        <v-icon start icon="mdi-format-list-bulleted-square" color="info"></v-icon>
        <span class="text-h6 font-weight-bold">Daftar Server</span>
        <v-spacer></v-spacer>
        <v-chip color="info" variant="outlined" size="small">
          {{ servers.length }} servers
        </v-chip>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="servers"
        :loading="loading"
        item-value="id"
        class="elevation-0"
        :items-per-page="10"
      >
      <template v-slot:loading>
        <SkeletonLoader type="table" :rows="6" />
      </template>

        <template v-slot:item.name="{ item }">
          <div class="font-weight-bold">{{ item.name }}</div>
        </template>

        <template v-slot:item.server_info="{ item }">
          <div class="d-flex align-center gap-2">
            <v-icon size="16" color="grey-darken-1">mdi-server</v-icon>
            <span class="font-mono text-body-2">{{ item.host_ip }}:{{ item.port }}</span>
          </div>
        </template>

        <template v-slot:item.is_active="{ item }">
          <v-chip :color="item.is_active ? 'success' : 'grey'" size="small" variant="tonal">
            <v-icon start size="14">{{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}</v-icon>
            {{ item.is_active ? 'Aktif' : 'Nonaktif' }}
          </v-chip>
        </template>

        <template v-slot:item.last_connection_status="{ item }">
            <v-chip :color="getConnectionColor(item.last_connection_status)" variant="tonal" size="small">
              <v-icon start size="14">{{ getConnectionIcon(item.last_connection_status) }}</v-icon>
              {{ item.last_connection_status || 'Belum diuji' }}
            </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex justify-center ga-2">
            <v-btn 
              size="small" 
              variant="tonal" 
              color="teal" 
              @click="handleTestConnection(item)"
              class="text-none"
              :loading="testingConnectionId === item.id"
            >
              <v-icon start size="16">mdi-connection</v-icon>
              Test
            </v-btn>
            <v-btn size="small" variant="tonal" color="primary" @click="openDialog(item)">
              <v-icon start size="16">mdi-pencil</v-icon> Edit
            </v-btn>
            <v-btn size="small" variant="tonal" color="error" @click="openDeleteDialog(item)">
              <v-icon start size="16">mdi-delete</v-icon> Hapus
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Enhanced Add/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="700px" persistent>
      <v-card class="rounded-xl elevation-8 dialog-card">
        <!-- Enhanced Header with Gradient -->
        <v-card-title class="pa-0">
          <div class="dialog-header pa-6">
            <div class="d-flex align-center">
              <v-avatar class="me-4" color="white" size="48">
                <v-icon color="info" size="28">{{ editedIndex === -1 ? 'mdi-server-plus' : 'mdi-server-edit' }}</v-icon>
              </v-avatar>
              <div>
                <h2 class="text-h5 text-white font-weight-bold mb-1">{{ formTitle }}</h2>
                <p class="text-subtitle-2 text-blue-lighten-4 mb-0">
                  {{ editedIndex === -1 ? 'Tambahkan server Mikrotik baru ke sistem' : 'Perbarui informasi server Mikrotik' }}
                </p>
              </div>
            </div>
          </div>
        </v-card-title>

        <v-card-text class="pa-8">
          <v-form ref="serverForm" v-model="formValid">
            <!-- Server Information Section -->
            <div class="form-section mb-6">
              <div class="section-header mb-4">
                <v-icon class="me-2" color="info">mdi-information-outline</v-icon>
                <span class="text-h6 font-weight-bold text-info">Informasi Server</span>
              </div>
              
              <v-row class="ma-0">
                <v-col cols="12" class="pb-2">
                  <v-text-field 
                    v-model="editedItem.name" 
                    label="Nama Server" 
                    variant="outlined"
                    prepend-inner-icon="mdi-server"
                    :rules="[rules.required]"
                    color="info"
                    class="elegant-input"
                    hint="Masukkan nama identifikasi untuk server ini"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" md="8" class="pb-2">
                  <v-text-field 
                    v-model="editedItem.host_ip" 
                    label="Host / IP Address" 
                    variant="outlined"
                    prepend-inner-icon="mdi-ip-network"
                    :rules="[rules.required]"
                    color="info"
                    class="elegant-input"
                    hint="IP Address atau hostname server Mikrotik"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" md="4" class="pb-2">
                  <v-text-field 
                    v-model.number="editedItem.port" 
                    label="Port API" 
                    type="number"
                    variant="outlined"
                    prepend-inner-icon="mdi-ethernet"
                    color="info"
                    class="elegant-input"
                    hint="Default: 8728"
                  ></v-text-field>
                </v-col>
              </v-row>
            </div>

            <!-- Authentication Section -->
            <div class="form-section mb-6">
              <div class="section-header mb-4">
                <v-icon class="me-2" color="deep-orange">mdi-shield-key</v-icon>
                <span class="text-h6 font-weight-bold text-deep-orange">Kredensial Login</span>
              </div>
              
              <v-row class="ma-0">
                <v-col cols="12" md="6" class="pb-2">
                  <v-text-field 
                    v-model="editedItem.username" 
                    label="Username" 
                    variant="outlined"
                    prepend-inner-icon="mdi-account"
                    :rules="[rules.required]"
                    color="deep-orange"
                    class="elegant-input"
                    autocomplete="username"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" md="6" class="pb-2">
                  <v-text-field 
                    v-model="editedItem.password" 
                    label="Password" 
                    :type="showPassword ? 'text' : 'password'"
                    variant="outlined"
                    prepend-inner-icon="mdi-lock"
                    :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                    @click:append-inner="showPassword = !showPassword"
                    color="deep-orange"
                    class="elegant-input"
                    :placeholder="editedIndex > -1 ? 'Kosongkan jika tidak berubah' : 'Masukkan password'"
                    autocomplete="current-password"
                  ></v-text-field>
                </v-col>
              </v-row>
            </div>

            <!-- Server Status Section -->
            <div class="form-section">
              <div class="section-header mb-4">
                <v-icon class="me-2" color="success">mdi-toggle-switch</v-icon>
                <span class="text-h6 font-weight-bold text-success">Status Server</span>
              </div>
              
              <v-card variant="tonal" color="success" class="pa-4">
                <div class="d-flex align-center justify-space-between">
                  <div>
                    <h3 class="text-subtitle-1 font-weight-bold mb-1">Aktivasi Server</h3>
                    <p class="text-body-2 text-medium-emphasis mb-0">
                      {{ editedItem.is_active ? 'Server akan aktif dan dapat digunakan' : 'Server akan dinonaktifkan sementara' }}
                    </p>
                  </div>
                  <v-switch 
                    v-model="editedItem.is_active" 
                    color="success"
                    size="large"
                    inset
                    :label="editedItem.is_active ? 'Aktif' : 'Nonaktif'"
                  ></v-switch>
                </div>
              </v-card>
            </div>
          </v-form>
        </v-card-text>

        <!-- Enhanced Footer -->
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            size="large" 
            @click="closeDialog"
            class="text-none me-3"
          >
            <v-icon start>mdi-close</v-icon>
            Batal
          </v-btn>
          <v-btn 
            color="info" 
            variant="flat" 
            size="large"
            @click="saveServer" 
            :loading="saving"
            :disabled="!formValid"
            class="text-none"
            elevation="2"
          >
            <v-icon start>{{ editedIndex === -1 ? 'mdi-content-save-plus' : 'mdi-content-save-edit' }}</v-icon>
            {{ editedIndex === -1 ? 'Tambah Server' : 'Update Server' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Enhanced Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="rounded-xl elevation-8">
        <v-card-text class="pa-8 text-center">
          <v-avatar color="error" size="80" class="mb-4">
            <v-icon color="white" size="40">mdi-delete-alert</v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold text-error mb-3">Konfirmasi Hapus</h2>
          <p class="text-body-1 text-medium-emphasis mb-4">
            Anda yakin ingin menghapus server 
            <strong class="text-error">{{ itemToDelete?.name }}</strong>?
          </p>
          <v-alert type="warning" variant="tonal" class="text-start">
            <template v-slot:prepend>
              <v-icon>mdi-alert-circle</v-icon>
            </template>
            Tindakan ini tidak dapat dibatalkan. Semua konfigurasi yang terkait dengan server ini akan hilang.
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            size="large" 
            @click="closeDeleteDialog"
            class="text-none me-3"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            size="large"
            @click="confirmDelete" 
            :loading="deleting"
            class="text-none"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000" location="top right">
      <v-icon start>{{ snackbar.icon }}</v-icon>
      {{ snackbar.text }}
    </v-snackbar>
    </div>

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import apiClient from '@/services/api';
import { debounce } from 'lodash-es';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

// --- Type Definitions ---
interface MikrotikServer {
  id: number | null;
  name: string;
  host_ip: string;
  port: number;
  username: string;
  password?: string;
  is_active: boolean;
}

// --- State ---
const servers = ref<any[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const editedIndex = ref(-1);
const testingConnectionId = ref<number | null>(null);
const showPassword = ref(false);
const formValid = ref(false);
const searchQuery = ref('');
const selectedIsActive = ref<boolean | null>(null);
const selectedConnectionStatus = ref<string | null>(null);

const defaultItem: MikrotikServer = { 
  id: null, 
  name: '', 
  host_ip: '', 
  port: 8728, 
  username: '', 
  password: '', 
  is_active: true 
};
const editedItem = ref<MikrotikServer>({ ...defaultItem });
const itemToDelete = ref<any>(null);

const snackbar = ref({ show: false, text: '', color: 'success', icon: 'mdi-check-circle' });

// --- Validation Rules ---
const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi',
};

// --- Headers ---
const headers = [
  { title: 'Nama Server', key: 'name', sortable: true },
  { title: 'Server Info', key: 'server_info', sortable: false },
  { title: 'ROS Version', key: 'ros_version', sortable: false, align: 'center' },
  { title: 'Status', key: 'is_active', align: 'center' },
  { title: 'Koneksi Terakhir', key: 'last_connection_status', align: 'center' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center', width: '320px' },
] as const;

// --- Computed Properties ---
const formTitle = computed(() => editedIndex.value === -1 ? 'Tambah Server Baru' : 'Edit Server');

// --- Lifecycle ---
onMounted(() => {
  fetchServers();
});

// --- Methods ---
async function fetchServers() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    if (selectedIsActive.value !== null) {
      params.append('is_active', String(selectedIsActive.value));
    }
    if (selectedConnectionStatus.value) {
      params.append('last_connection_status', selectedConnectionStatus.value);
    }

    const response = await apiClient.get(`/mikrotik_servers/?${params.toString()}`);
    servers.value = response.data;
  } catch (error) { console.error(error); } 
  finally { loading.value = false; }
}

const applyFilters = debounce(() => {
  fetchServers();
}, 500);

watch([searchQuery, selectedIsActive, selectedConnectionStatus], () => {
  applyFilters();
});

function resetFilters() {
  searchQuery.value = '';
  selectedIsActive.value = null;
  selectedConnectionStatus.value = null;
}

function openDialog(item?: any) {
  editedIndex.value = item ? servers.value.indexOf(item) : -1;
  editedItem.value = item ? { ...item, password: '' } : { ...defaultItem };
  showPassword.value = false;
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = { ...defaultItem };
  editedIndex.value = -1;
  showPassword.value = false;
}

async function saveServer() {
  saving.value = true;
  const payload: Partial<MikrotikServer> = { ...editedItem.value };
  
  if (editedIndex.value > -1 && !payload.password) {
    delete payload.password;
  }

  try {
    if (editedIndex.value > -1) {
      await apiClient.patch(`/mikrotik_servers/${payload.id}`, payload);
    } else {
      await apiClient.post('/mikrotik_servers/', payload);
    }
    fetchServers();
    closeDialog();
    showSnackbar(
      editedIndex.value > -1 ? 'Server berhasil diperbarui!' : 'Server baru berhasil ditambahkan!', 
      'success'
    );
  } catch (error) { 
    console.error(error);
    showSnackbar('Gagal menyimpan server. Silakan coba lagi.', 'error');
  } 
  finally { saving.value = false; }
}

async function handleTestConnection(item: any) {
  testingConnectionId.value = item.id;
  try {
    // A successful request (2xx status) will land here.
    const response = await apiClient.post(`/mikrotik_servers/${item.id}/test_connection`);

    const testResult = response.data.test_result;
    const updatedServer = response.data.updated_server;

    // Show snackbar with the specific success message from the backend
    const rosVersion = testResult.data?.ros_version || 'N/A';
    showSnackbar(`${testResult.message} (ROS: ${rosVersion})`, 'success');

    // Find and update the server in the local array for instant UI refresh
    const index = servers.value.findIndex(s => s.id === item.id);
    if (index !== -1) {
      servers.value[index] = updatedServer;
    }

  } catch (error: any) {
    // A failed request (like 400 Bad Request) will land here.
    if (error.response && error.response.data) {
      const testResult = error.response.data.test_result;
      const updatedServer = error.response.data.updated_server;

      // Show snackbar with the specific failure message from the backend
      showSnackbar(testResult.message, 'error');

      // Find and update the server in the local array to show the 'failure' status
      const index = servers.value.findIndex(s => s.id === item.id);
      if (index !== -1) {
        servers.value[index] = updatedServer;
      }
    } else {
      // Fallback for unexpected network errors
      showSnackbar('An unknown error occurred while testing the connection.', 'error');
    }
  } finally {
    testingConnectionId.value = null;
  }
}

function openDeleteDialog(item: any) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  itemToDelete.value = null;
}

async function confirmDelete() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/mikrotik_servers/${itemToDelete.value.id}`);
    fetchServers();
    closeDeleteDialog();
    showSnackbar('Server berhasil dihapus!', 'success');
  } catch (error) { 
    console.error(error);
    showSnackbar('Gagal menghapus server. Silakan coba lagi.', 'error');
  }
  finally { deleting.value = false; }
}

// --- Helper Methods ---
function showSnackbar(text: string, color: 'success' | 'error' | 'info') {
  snackbar.value = {
    show: true,
    text,
    color,
    icon: color === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'
  };
}

function getConnectionColor(status: string | null): string {
    if (status === 'success') return 'success';
    if (status === 'failure') return 'error';
    return 'grey';
}

function getConnectionIcon(status: string | null): string {
    if (status === 'success') return 'mdi-check-circle';
    if (status === 'failure') return 'mdi-close-circle';
    return 'mdi-help-circle';
}
</script>

<style scoped>
/* Header Card styling - sama seperti halaman lain */
.header-card {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
  background: white;
}

/* Header content untuk memperbesar box */
.header-content {
  padding: 24px 32px;
}

/* Content section - sama seperti halaman lain */
.content-section {
  width: 100%;
}

/* Header Section styling - sama seperti halaman lain */
.header-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.header-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="50" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="30" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
}

/* Header text styling */
.header-section h1 {
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 1.1rem;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  opacity: 0.95;
}

.dialog-card {
  background: #fafafa;
}

.dialog-header {
  background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
  position: relative;
}

.dialog-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"><g fill="%23ffffff" fill-opacity="0.1"><circle cx="30" cy="30" r="2"/></g></svg>');
  opacity: 0.3;
}

/* ============================================
   ENHANCED FILTER CARD STYLING
   ============================================ */

.filter-card {
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  background: linear-gradient(145deg, 
    rgba(var(--v-theme-surface), 0.95) 0%, 
    rgba(var(--v-theme-background), 0.98) 100%);
  backdrop-filter: blur(10px);
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 3px rgba(var(--v-theme-shadow), 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

/* Efek hover pada filter card */
.filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(var(--v-theme-shadow), 0.12),
    0 2px 6px rgba(var(--v-theme-shadow), 0.16);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

/* Efek glow subtle di bagian atas card */
.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(var(--v-theme-primary), 0.6) 50%, 
    transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.filter-card:hover::before {
  opacity: 1;
}

/* Container utama filter */
.filter-card .d-flex {
  padding: 28px 32px !important;
  gap: 20px !important;
}

/* Styling untuk text field pencarian */
.filter-card .v-text-field {
  min-width: 320px !important;
}

.filter-card .v-text-field :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border: 2px solid rgba(var(--v-theme-outline-variant), 0.3) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-text-field :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.filter-card .v-text-field :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

/* Icon pencarian */
.filter-card .v-text-field :deep(.v-field__prepend-inner) {
  padding-right: 12px;
}

.filter-card .v-text-field :deep(.v-field__prepend-inner .v-icon) {
  color: rgba(var(--v-theme-primary), 0.7) !important;
  transition: color 0.2s ease;
}

.filter-card .v-text-field:hover :deep(.v-field__prepend-inner .v-icon) {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Styling untuk select fields (alamat & brand) */
.filter-card .v-select {
  min-width: 220px !important;
}

.filter-card .v-select :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border: 2px solid rgba(var(--v-theme-outline-variant), 0.3) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-select :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.filter-card .v-select :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

/* Label styling yang lebih refined */
.filter-card .v-field :deep(.v-field__label) {
  color: rgba(var(--v-theme-on-surface), 0.7) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
}

.filter-card .v-field--focused :deep(.v-field__label) {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Tombol Reset Filter */
.filter-card .v-btn[variant="text"] {
  border-radius: 14px !important;
  font-weight: 600 !important;
  height: 48px !important;
  min-width: 120px !important;
  color: rgba(var(--v-theme-primary), 0.8) !important;
  background: rgba(var(--v-theme-primary), 0.08) !important;
  border: 1px solid rgba(var(--v-theme-primary), 0.2) !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.filter-card .v-btn[variant="text"]:hover {
  background: rgba(var(--v-theme-primary), 0.12) !important;
  color: rgb(var(--v-theme-primary)) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.filter-card .v-btn[variant="text"]:active {
  transform: translateY(0);
}

/* Efek ripple custom untuk tombol reset */
.filter-card .v-btn[variant="text"]::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.3);
  transition: width 0.3s ease, height 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.filter-card .v-btn[variant="text"]:hover::before {
  width: 100%;
  height: 100%;
}

/* Responsive design untuk mobile */
@media (max-width: 960px) {
  .filter-card .d-flex {
    padding: 20px 24px !important;
    gap: 16px !important;
  }
  
  .filter-card .v-text-field,
  .filter-card .v-select {
    min-width: 100% !important;
  }
  
  .filter-card .v-btn[variant="text"] {
    width: 100% !important;
    margin-top: 8px;
  }
}

@media (max-width: 600px) {
  .filter-card .d-flex {
    padding: 16px 20px !important;
    flex-direction: column !important;
    gap: 12px !important;
  }
  
  .filter-card {
    border-radius: 16px;
    margin: 0 8px;
  }
}

/* Dark mode adjustments */
.v-theme--dark .filter-card {
  background: linear-gradient(145deg, 
    rgba(var(--v-theme-surface), 0.9) 0%, 
    rgba(var(--v-theme-background), 0.95) 100%);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .filter-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.v-theme--dark .filter-card .v-text-field :deep(.v-field),
.v-theme--dark .filter-card .v-select :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.6) !important;
  border-color: rgba(var(--v-theme-outline), 0.3) !important;
}

.v-theme--dark .filter-card .v-text-field :deep(.v-field:hover),
.v-theme--dark .filter-card .v-select :deep(.v-field:hover) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border-color: rgba(var(--v-theme-primary), 0.5) !important;
}

/* Loading state untuk field */
.filter-card .v-field--loading :deep(.v-field) {
  opacity: 0.7;
  pointer-events: none;
}

/* Animasi untuk smooth transitions */
.filter-card * {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Focus ring yang lebih halus */
.filter-card .v-field--focused :deep(.v-field__outline) {
  border-width: 2px !important;
  border-color: rgb(var(--v-theme-primary)) !important;
}

/* Custom scrollbar untuk dropdown */
.filter-card .v-select :deep(.v-list) {
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(var(--v-theme-shadow), 0.15);
}

.filter-card .v-select :deep(.v-list-item) {
  border-radius: 8px;
  margin: 2px 8px;
  transition: all 0.2s ease;
}

.filter-card .v-select :deep(.v-list-item:hover) {
  background: rgba(var(--v-theme-primary), 0.08) !important;
  transform: translateX(4px);
}

.form-section {
  position: relative;
}

.section-header {
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 2px solid #f5f5f5;
}

.elegant-input :deep(.v-field) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.elegant-input :deep(.v-field:hover) {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.elegant-input :deep(.v-field--focused) {
  box-shadow: 0 4px 20px rgba(33, 150, 243, 0.2);
}

.v-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.v-btn {
  transition: all 0.3s ease;
  text-transform: none;
  font-weight: 600;
}

.v-btn:hover {
  transform: translateY(-2px);
}

.v-switch :deep(.v-switch__thumb) {
  transition: all 0.3s ease;
}
</style>