<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center flex-wrap gap-4">
            <div class="d-flex align-center flex-grow-1">
              <v-avatar class="me-4 elevation-4 bg-white/10" color="transparent" size="64">
                <v-icon color="white" size="32">mdi-router-wireless</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-1">OLT Management</h1>
                <p class="header-subtitle mb-0">
                  Manage and monitor your OLT devices
                </p>
              </div>
            </div>
            <v-btn
              color="white"
              variant="elevated"
              size="large"
              elevation="4"
              @click="openDialog()"
              prepend-icon="mdi-plus"
              class="text-none font-weight-bold px-6 rounded-lg add-btn"
            >
              Tambah OLT
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-center align-center py-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- Empty State -->
    <div v-else-if="olts.length === 0" class="text-center py-12">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-server-network-off</v-icon>
      <h3 class="text-h6 text-grey-darken-1 font-weight-regular">Belum ada OLT yang terdaftar</h3>
      <v-btn
        color="primary"
        variant="text"
        class="mt-2 text-none"
        @click="openDialog()"
      >
        Tambah OLT Baru
      </v-btn>
    </div>

    <!-- Server Cards Grid -->
    <v-row v-else>
      <v-col
        v-for="item in olts"
        :key="item.id"
        cols="12"
        sm="6"
        md="4"
        xl="3"
      >
        <v-card
          class="server-card h-100 d-flex flex-column"
          elevation="0"
          border
        >
          <!-- Status Line Indicator -->
          <div class="status-line"></div>

          <v-card-text class="pt-5 pb-2 flex-grow-1">
            <div class="d-flex justify-space-between align-start mb-4">
              <!-- Icon Container -->
              <div class="icon-box elevation-2">
                <v-icon color="primary" size="28">mdi-router-wireless</v-icon>
              </div>

              <!-- Action Menu -->
              <v-menu location="bottom end">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon
                    variant="text"
                    density="comfortable"
                    color="grey-darken-1"
                    v-bind="props"
                  >
                    <v-icon>mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>
                <v-list density="compact" elevation="3" rounded="lg" class="py-2">
                  <v-list-item @click="openDialog(item)" value="edit" class="px-4">
                    <template v-slot:prepend>
                      <v-icon size="small" color="primary" class="me-3">mdi-pencil</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-medium">Edit Konfigurasi</v-list-item-title>
                  </v-list-item>
                  
                  <v-divider class="my-1"></v-divider>
                  
                  <v-list-item @click="openDeleteDialog(item)" value="delete" class="px-4 text-error">
                    <template v-slot:prepend>
                      <v-icon size="small" color="error" class="me-3">mdi-delete</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-medium text-error">Hapus OLT</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>

            <!-- Server Info -->
            <div class="mb-4">
              <h3 class="text-h6 font-weight-bold text-grey-darken-3 mb-1 text-truncate">
                {{ item.nama_olt }}
              </h3>
              <div class="d-flex align-center">
                <v-icon size="16" color="primary" class="me-2">mdi-ip-network</v-icon>
                <span class="text-body-2 font-weight-medium text-grey-darken-1 font-mono">
                  {{ item.ip_address }}
                </span>
              </div>
            </div>

            <v-divider class="mb-4 border-opacity-75"></v-divider>

            <!-- Details Grid -->
            <v-row dense class="mb-0 g-3">
              <v-col cols="6">
                <div class="detail-item">
                  <div class="text-caption text-grey mb-1">Tipe OLT</div>
                  <div class="d-flex align-center">
                    <v-chip
                      size="x-small"
                      color="blue-grey"
                      variant="flat"
                      class="font-weight-bold"
                    >
                      {{ item.tipe_olt }}
                    </v-chip>
                  </div>
                </div>
              </v-col>
              
              <v-col cols="6">
                <div class="detail-item text-right">
                  <div class="text-caption text-grey mb-1">Username</div>
                  <div class="font-weight-medium text-body-2 text-grey-darken-2 text-truncate">
                    {{ item.username || '-' }}
                  </div>
                </div>
              </v-col>

              <v-col cols="12" class="mt-2">
                 <div class="detail-item bg-grey-lighten-4 pa-2 rounded-lg">
                    <div class="d-flex align-center justify-space-between">
                       <span class="text-caption text-grey-darken-1">Mikrotik Server:</span>
                       <span class="text-caption font-weight-bold text-primary text-truncate ms-2">
                          {{ getMikrotikName(item.mikrotik_server_id) }}
                       </span>
                    </div>
                 </div>
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions class="px-4 pb-4 pt-0">
            <v-btn
              block
              height="44"
              rounded="lg"
              :loading="testingConnectionId === item.id"
              @click="testConnection(item)"
              :color="connectionStatus[item.id] ? 'success' : 'primary'"
              :variant="connectionStatus[item.id] ? 'flat' : 'tonal'"
              class="font-weight-bold text-capitalize"
              elevation="0"
            >
              <template v-if="connectionStatus[item.id]">
                <v-icon start class="me-2">mdi-check-circle</v-icon>
                Terhubung
              </template>
              <template v-else>
                <v-icon start class="me-2">mdi-connection</v-icon>
                Test Connection
              </template>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog Edit/Add -->
    <v-dialog v-model="dialog" max-width="500px" persistent transition="dialog-bottom-transition">
      <v-card rounded="xl" class="overflow-visible">
        <div class="dialog-header-accent"></div>
        <v-card-title class="text-h5 font-weight-bold pt-6 px-6 pb-2">
          {{ formTitle }}
        </v-card-title>
        
        <v-card-text class="pt-4 px-6 pb-6">
          <v-form @submit.prevent="saveOLT" ref="form">
            <v-row dense>
               <v-col cols="12">
                   <p class="text-caption text-grey-darken-1 font-weight-bold mb-2 text-uppercase">Informasi Utama</p>
               </v-col>
              <v-col cols="12">
                <v-text-field 
                  v-model="editedItem.nama_olt" 
                  label="Nama OLT" 
                  placeholder="Contoh: OLT-Pusat"
                  variant="outlined" 
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-format-title"
                  :rules="[rules.required]"
                  class="mb-1"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="editedItem.ip_address" 
                  label="IP Address" 
                  placeholder="192.168.1.1"
                  variant="outlined" 
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-ip-network"
                  :rules="[rules.required, rules.ip]"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select 
                  v-model="editedItem.tipe_olt" 
                  :items="oltTypes" 
                  label="Tipe Perangkat" 
                  variant="outlined" 
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-server"
                  :rules="[rules.required]"
                ></v-select>
              </v-col>

               <v-col cols="12" class="mt-2">
                   <p class="text-caption text-grey-darken-1 font-weight-bold mb-2 text-uppercase">Kredensial & Integrasi</p>
               </v-col>

              <v-col cols="12">
                <v-select
                  v-model="editedItem.mikrotik_server_id"
                  :items="mikrotikList"
                  item-title="name"
                  item-value="id"
                  label="Mikrotik Server Terkait"
                  variant="outlined"
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-router"
                  :loading="loadingMikrotiks"
                  :rules="[rules.required]"
                  no-data-text="Tidak ada server Mikrotik"
                ></v-select>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="editedItem.username" 
                  label="Username" 
                  variant="outlined" 
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-account"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="editedItem.password" 
                  label="Password" 
                  type="password" 
                  variant="outlined" 
                  density="comfortable"
                  color="primary"
                  bg-color="grey-lighten-5"
                  prepend-inner-icon="mdi-lock"
                  :placeholder="isEditMode ? '••••••••' : ''"
                  :hint="isEditMode ? 'Biarkan kosong jika tidak ingin mengubah' : ''"
                  persistent-hint
                  :rules="isEditMode ? [] : [rules.required]"
                ></v-text-field>
              </v-col>
            </v-row>

            <div class="d-flex gap-3 mt-6">
               <v-btn 
                  variant="tonal" 
                  color="grey" 
                  size="large" 
                  class="flex-grow-1"
                  @click="closeDialog"
               >
                  Batal
               </v-btn>
               <v-btn 
                  color="primary" 
                  type="submit" 
                  size="large" 
                  elevation="2"
                  class="flex-grow-1"
                  :loading="saving"
               >
                  {{ isEditMode ? 'Simpan Perubahan' : 'Tambah OLT' }}
               </v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Dialog Hapus -->
    <v-dialog v-model="dialogDelete" max-width="400px">
        <v-card rounded="xl">
            <div class="d-flex justify-center pt-8 pb-4">
               <v-avatar color="red-lighten-4" size="80">
                  <v-icon color="error" size="40">mdi-alert-circle-outline</v-icon>
               </v-avatar>
            </div>
            <v-card-title class="text-h5 text-center font-weight-bold">Hapus OLT?</v-card-title>
            <v-card-text class="text-center text-body-1 text-grey-darken-1 px-6">
                Apakah Anda yakin ingin menghapus data OLT <span class="font-weight-bold text-black">{{ itemToDelete?.nama_olt }}</span>? Tindakan ini tidak dapat dibatalkan.
            </v-card-text>
            <v-card-actions class="pa-6">
                <v-row dense gap="3">
                   <v-col cols="6">
                      <v-btn block variant="tonal" color="grey" height="44" @click="closeDeleteDialog">Batal</v-btn>
                   </v-col>
                   <v-col cols="6">
                      <v-btn block color="error" height="44" elevation="2" @click="confirmDelete" :loading="deleting">Ya, Hapus</v-btn>
                   </v-col>
                </v-row>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      location="top right"
      variant="elevated"
      elevation="8"
      rounded="lg"
    >
      <div class="d-flex align-center">
        <v-icon
          :icon="snackbar.color === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'"
          class="me-3"
          size="24"
        ></v-icon>
        <div class="font-weight-medium text-body-1">{{ snackbar.text }}</div>
      </div>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';

// --- INTERFACES ---
interface OLT {
  id: number;
  nama_olt: string;
  ip_address: string;
  tipe_olt: string;
  username?: string;
  mikrotik_server_id?: number | null; 
}

interface MikrotikSelectItem {
  id: number;
  name: string;
}

// --- STATE MANAGEMENT ---
const olts = ref<OLT[]>([]);
const mikrotikList = ref<MikrotikSelectItem[]>([]);
const loading = ref(true);
const loadingMikrotiks = ref(false);
const saving = ref(false);
const deleting = ref(false);
const testingConnectionId = ref<number | null>(null);
const connectionStatus = ref<Record<number, boolean>>({}); // Track success status per item

const dialog = ref(false);
const dialogDelete = ref(false);

const editedItem = ref<Partial<OLT> & { password?: string }>({});
const itemToDelete = ref<OLT | null>(null);
const snackbar = ref({ show: false, text: '', color: 'success' });

// --- COMPUTED PROPERTIES ---
const isEditMode = computed(() => !!editedItem.value.id);
const formTitle = computed(() => isEditMode.value ? 'Edit OLT' : 'Tambah OLT Baru');

// --- DATA & CONFIGURATION ---
const oltTypes = ['HSGQ', 'ZTE', 'Huawei', 'Fiberhome', 'Lainnya'];

const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi.',
  ip: (value: string) => /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(value) || 'Format IP tidak valid.',
};

// --- LIFECYCLE HOOKS ---
onMounted(() => {
  fetchOLTs();
  fetchMikrotiks();
});

// --- HELPER FUNCTIONS ---
function getMikrotikName(id: number | null | undefined): string {
  if (!id) return '-';
  const server = mikrotikList.value.find(m => m.id === id);
  return server ? server.name : 'Unknown';
}

// --- API FUNCTIONS ---
async function fetchOLTs() {
  loading.value = true;
  try {
    const response = await apiClient.get('/olt/');
    olts.value = response.data;
  } catch (error) {
    showSnackbar("Gagal memuat data OLT", "error");
  } finally {
    loading.value = false;
  }
}

async function fetchMikrotiks() {
  loadingMikrotiks.value = true;
  try {
    const response = await apiClient.get('/mikrotik_servers/');
    mikrotikList.value = response.data;
  } catch (error) {
    console.error("Failed to load Mikrotik servers", error);
  } finally {
    loadingMikrotiks.value = false;
  }
}

function openDialog(item?: OLT) {
  editedItem.value = item ? { ...item, password: '' } : { tipe_olt: 'HSGQ' };
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = {};
}

async function saveOLT() {
  saving.value = true;
  const payload = { ...editedItem.value };
  
  if (isEditMode.value && !payload.password) {
    delete payload.password;
  }

  try {
    if (isEditMode.value) {
      await apiClient.patch(`/olt/${payload.id}`, payload);
    } else {
      await apiClient.post('/olt/', payload);
    }
    fetchOLTs();
    closeDialog();
    showSnackbar(`OLT berhasil ${isEditMode.value ? 'diperbarui' : 'ditambahkan'}`, 'success');
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail?.[0]?.msg || "Gagal menyimpan data OLT";
    showSnackbar(errorMsg, 'error');
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: OLT) {
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
    await apiClient.delete(`/olt/${itemToDelete.value.id}`);
    fetchOLTs();
    showSnackbar('OLT berhasil dihapus', 'success');
  } catch (error) {
    showSnackbar('Gagal menghapus OLT', 'error');
  } finally {
    deleting.value = false;
    closeDeleteDialog();
  }
}

async function testConnection(item: OLT) {
  testingConnectionId.value = item.id;
  try {
    const response = await apiClient.post(`/olt/${item.id}/test-connection`);
    showSnackbar(response.data.message || 'Koneksi berhasil!', 'success');
    
    // Set success status for visuals
    connectionStatus.value[item.id] = true;
    setTimeout(() => {
      connectionStatus.value[item.id] = false;
    }, 4000);
    
  } catch (error: any) {
    const message = error.response?.data?.message || "Koneksi gagal, terjadi error.";
    showSnackbar(message, 'error');
  } finally {
    testingConnectionId.value = null;
  }
}

function showSnackbar(text: string, color: 'success' | 'error' | 'info') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}
</script>

<style scoped>
/* Main Header Styling */
.header-card {
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
  background: white;
  position: relative;
  z-index: 1;
}

.header-section {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  position: relative;
  overflow: hidden;
}

/* Background Pattern overlay */
.header-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 150%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% -50%, rgba(255, 255, 255, 0.15) 0%, transparent 50%);
  z-index: 1;
}

.header-content {
  position: relative;
  padding: 40px 32px;
  z-index: 2;
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.85) !important;
  font-size: 1.1rem;
  letter-spacing: 0.01em;
}

.add-btn {
  color: #4F46E5 !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

/* Server Card Styling */
.server-card {
  border-radius: 20px;
  background: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.server-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.1);
  border-color: rgba(79, 70, 229, 0.2);
}

.status-line {
  height: 4px;
  background: linear-gradient(90deg, #4F46E5, #7C3AED);
  width: 100%;
}

.icon-box {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.server-card:hover .icon-box {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
}

.server-card:hover .icon-box .v-icon {
  color: white !important;
}

.font-mono {
  font-family: 'SF Mono', 'Roboto Mono', monospace;
  letter-spacing: -0.5px;
}

.detail-item {
  transition: all 0.2s ease;
}

/* Dialog Styling */
.dialog-header-accent {
  height: 8px;
  background: linear-gradient(90deg, #4F46E5, #7C3AED);
  width: 100%;
}
</style>