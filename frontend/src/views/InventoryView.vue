<template>
  <v-container fluid class="inventory-container">
    <!-- Header Section -->
    <div class="page-header mb-6">
      <div class="header-content">
        <v-avatar class="header-avatar" color="primary" size="56">
          <v-icon color="white" size="28">mdi-archive-outline</v-icon>
        </v-avatar>
        <div class="header-text">
          <h1 class="page-title">Manajemen Inventaris</h1>
          <p class="page-subtitle">Kelola perangkat, tipe, dan status inventaris</p>
        </div>
      </div>
    </div>

    <!-- Main Card with Modern Design -->
    <v-card class="inventory-card" elevation="0">
      <!-- Modern Tabs -->
      <v-tabs 
        v-model="tab" 
        class="modern-tabs"
        color="primary"
        grow
        slider-color="primary"
        :mobile-breakpoint="600"
      >
        <v-tab value="items" class="tab-item">
          <v-icon start size="22">mdi-package-variant-closed</v-icon>
          <span class="tab-text">Daftar Perangkat</span>
        </v-tab>
        <v-tab value="types" class="tab-item">
          <v-icon start size="22">mdi-shape-outline</v-icon>
          <span class="tab-text">Kelola Tipe Item</span>
        </v-tab>
        <v-tab value="statuses" class="tab-item">
          <v-icon start size="22">mdi-tag-outline</v-icon>
          <span class="tab-text">Kelola Status</span>
        </v-tab>
      </v-tabs>

      <v-divider></v-divider>

      <!-- Tab Content Windows -->
      <v-window v-model="tab" class="tab-window">
        
        <!-- Items Tab -->
        <v-window-item value="items" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Daftar Perangkat</h2>
              <p class="content-subtitle">Kelola semua perangkat inventaris</p>
            </div>
            <v-btn 
              color="primary" 
              class="add-btn"
              elevation="2"
              @click="openItemDialog()"
            >
              <v-icon start>mdi-plus</v-icon>
              <span class="btn-text">Tambah Item</span>
            </v-btn>
          </div>

          <div class="table-container">
            <v-data-table 
              :headers="itemHeaders" 
              :items="inventoryItems" 
              :loading="loading"
              class="modern-table"
              :items-per-page="15"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>
              
              <template v-slot:item.status="{ item }">
                <v-chip 
                  :color="getStatusColor(item.status.name)" 
                  size="default"
                  variant="elevated"
                  class="status-chip"
                >
                  {{ item.status.name }}
                </v-chip>
              </template>
              
              <template v-slot:item.item_type="{ item }">
                <div class="type-wrapper">
                  <v-icon size="18" class="me-2 text-medium-emphasis">mdi-package-variant</v-icon>
                  {{ item.item_type.name }}
                </div>
              </template>
              
              <template v-slot:item.serial_number="{ item }">
                <div class="serial-wrapper">
                  <code class="serial-code">{{ item.serial_number }}</code>
                </div>
              </template>
              
              <template v-slot:item.mac_address="{ item }">
                <div class="mac-wrapper">
                  <code v-if="item.mac_address" class="mac-code">{{ item.mac_address }}</code>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </template>
              
              <template v-slot:item.location="{ item }">
                <div class="location-wrapper">
                  <v-icon v-if="item.location" size="16" class="me-1 text-medium-emphasis">mdi-map-marker</v-icon>
                  <span>{{ item.location || '-' }}</span>
                </div>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <div class="action-buttons">
                  <v-tooltip text="Edit">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="primary"
                        class="action-btn"
                        v-bind="props"
                        @click="openItemDialog(item)"
                      >
                        <v-icon size="20">mdi-pencil</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="Hapus">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="error"
                        class="action-btn"
                        v-bind="props"
                        @click="deleteItem(item)"
                      >
                        <v-icon size="20">mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </template>
              
              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-package-variant-closed-remove</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada perangkat inventaris</p>
                </div>
              </template>
            </v-data-table>
          </div>
        </v-window-item>

        <!-- Types Tab -->
        <v-window-item value="types" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Tipe Item yang Tersedia</h2>
              <p class="content-subtitle">Kelola kategori perangkat inventaris</p>
            </div>
            <v-btn 
              color="primary" 
              class="add-btn"
              elevation="2"
              @click="openTypeDialog()"
            >
              <v-icon start>mdi-plus</v-icon>
              <span class="btn-text">Tambah Tipe Baru</span>
            </v-btn>
          </div>

          <div class="table-container">
            <v-data-table 
              :headers="typeHeaders" 
              :items="itemTypes" 
              :loading="loading"
              class="modern-table"
              :items-per-page="15"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>
              
              <template v-slot:item.name="{ item }">
                <div class="type-name-wrapper">
                  <v-icon size="18" class="me-2 text-primary">mdi-shape</v-icon>
                  <span class="type-name">{{ item.name }}</span>
                </div>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <div class="action-buttons">
                  <v-tooltip text="Edit">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="primary"
                        class="action-btn"
                        v-bind="props"
                        @click="openTypeDialog(item)"
                      >
                        <v-icon size="20">mdi-pencil</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="Hapus">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="error"
                        class="action-btn"
                        v-bind="props"
                        @click="deleteType(item)"
                      >
                        <v-icon size="20">mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </template>
              
              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-shape-outline</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada tipe item</p>
                </div>
              </template>
            </v-data-table>
          </div>
        </v-window-item>

        <!-- Statuses Tab -->
        <v-window-item value="statuses" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Status Inventaris yang Tersedia</h2>
              <p class="content-subtitle">Kelola status kondisi perangkat</p>
            </div>
            <v-btn 
              color="primary" 
              class="add-btn"
              elevation="2"
              @click="openStatusDialog()"
            >
              <v-icon start>mdi-plus</v-icon>
              <span class="btn-text">Tambah Status Baru</span>
            </v-btn>
          </div>

          <div class="table-container">
            <v-data-table 
              :headers="statusHeaders" 
              :items="statuses" 
              :loading="loading"
              class="modern-table"
              :items-per-page="15"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>
              
              <template v-slot:item.name="{ item }">
                <div class="status-name-wrapper">
                  <v-chip 
                    :color="getStatusColor(item.name)" 
                    size="default"
                    variant="elevated"
                    class="status-preview-chip"
                  >
                    {{ item.name }}
                  </v-chip>
                </div>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <div class="action-buttons">
                  <v-tooltip text="Edit">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="primary"
                        class="action-btn"
                        v-bind="props"
                        @click="openStatusDialog(item)"
                      >
                        <v-icon size="20">mdi-pencil</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="Hapus">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="default"
                        variant="text"
                        color="error"
                        class="action-btn"
                        v-bind="props"
                        @click="deleteStatus(item)"
                      >
                        <v-icon size="20">mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </template>
              
              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-tag-outline</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada status inventaris</p>
                </div>
              </template>
            </v-data-table>
          </div>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Item Dialog -->
    <v-dialog v-model="itemDialog" :max-width="isMobile ? '95vw' : '700px'" persistent>
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon class="me-3" color="primary">mdi-package-variant-closed</v-icon>
          <span>{{ formItemTitle }}</span>
          <v-spacer></v-spacer>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeItemDialog"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="dialog-content">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field 
                v-model="editedItem.serial_number" 
                label="Serial Number" 
                variant="outlined" 
                density="comfortable"
                prepend-inner-icon="mdi-identifier"
                class="form-field"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field 
                v-model="editedItem.mac_address" 
                label="MAC Address" 
                variant="outlined" 
                density="comfortable"
                prepend-inner-icon="mdi-network-outline"
                class="form-field"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-select 
                v-model="editedItem.item_type_id" 
                :items="itemTypes" 
                item-title="name" 
                item-value="id" 
                label="Tipe Item" 
                variant="outlined" 
                density="comfortable"
                prepend-inner-icon="mdi-shape"
                class="form-field"
              ></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-select 
                v-model="editedItem.status_id" 
                :items="statuses" 
                item-title="name" 
                item-value="id" 
                label="Status" 
                variant="outlined" 
                density="comfortable"
                prepend-inner-icon="mdi-tag"
                class="form-field"
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-text-field 
                v-model="editedItem.location" 
                label="Lokasi" 
                variant="outlined" 
                density="comfortable"
                prepend-inner-icon="mdi-map-marker"
                class="form-field"
              ></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-textarea 
                v-model="editedItem.notes" 
                label="Catatan" 
                rows="3" 
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-note-text"
                class="form-field"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1"
            @click="closeItemDialog"
            class="cancel-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            color="primary" 
            variant="elevated"
            @click="saveItem" 
            :loading="saving"
            class="save-btn"
          >
            <v-icon start v-if="!saving">mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Type Dialog -->
    <v-dialog v-model="typeDialog" :max-width="isMobile ? '95vw' : '550px'" persistent>
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon class="me-3" color="primary">mdi-shape</v-icon>
          <span>{{ formTypeTitle }}</span>
          <v-spacer></v-spacer>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeTypeDialog"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="dialog-content">
          <v-text-field 
            v-model="editedType.name" 
            label="Nama Tipe" 
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-shape"
            class="form-field"
          ></v-text-field>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1"
            @click="closeTypeDialog"
            class="cancel-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            color="primary" 
            variant="elevated"
            @click="saveType" 
            :loading="saving"
            class="save-btn"
          >
            <v-icon start v-if="!saving">mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Status Dialog -->
    <v-dialog v-model="statusDialog" :max-width="isMobile ? '95vw' : '550px'" persistent>
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon class="me-3" color="primary">mdi-tag</v-icon>
          <span>{{ formStatusTitle }}</span>
          <v-spacer></v-spacer>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeStatusDialog"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="dialog-content">
          <v-text-field 
            v-model="editedStatus.name" 
            label="Nama Status" 
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-tag"
            class="form-field"
          ></v-text-field>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1"
            @click="closeStatusDialog"
            class="cancel-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            color="primary" 
            variant="elevated"
            @click="saveStatus" 
            :loading="saving"
            class="save-btn"
          >
            <v-icon start v-if="!saving">mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="historyDialog" max-width="800px">
        <v-card>
            <v-card-title>Riwayat Perubahan untuk SN: {{ selectedItemForHistory?.serial_number }}</v-card-title>
            <v-card-text>
            <v-data-table
                :headers="historyHeaders"
                :items="historyLogs"
                :loading="historyLoading"
                density="compact"
            >
                <template v-slot:item.timestamp="{ item }">
                {{ new Date(item.timestamp).toLocaleString('id-ID') }}
                </template>
                <template v-slot:item.user="{ item }">
                {{ item.user.name }}
                </template>
            </v-data-table>
            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="historyDialog = false">Tutup</v-btn>
            </v-card-actions>
        </v-card>
        </v-dialog>

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useDisplay } from 'vuetify';
import apiClient from '@/services/api';

// --- INTERFACES ---
interface ItemType { id: number; name: string; }
interface Status { id: number; name: string; }
interface InventoryItem {
  id: number;
  serial_number: string;
  mac_address: string | null;
  location: string | null;
  notes: string | null;
  item_type_id: number;
  status_id: number;
  item_type: ItemType;
  status: Status;
}

// --- COMPOSABLES ---
const { mobile } = useDisplay();
const isMobile = computed(() => mobile.value);

// --- STATE ---
const tab = ref('items');
const loading = ref(true);
const saving = ref(false);

const historyDialog = ref(false);
const historyLoading = ref(false);
const historyLogs = ref<any[]>([]);
const selectedItemForHistory = ref<InventoryItem | null>(null);
const historyHeaders = [
  { title: 'Waktu', key: 'timestamp' },
  { title: 'Aksi / Perubahan', key: 'action' },
  { title: 'Oleh', key: 'user' },
];



// State for Inventory Items
const inventoryItems = ref<InventoryItem[]>([]);
const itemDialog = ref(false);
const editedItem = ref<Partial<InventoryItem>>({});
const itemHeaders = [
  { title: 'Serial Number', key: 'serial_number' },
  { title: 'MAC Address', key: 'mac_address' },
  { title: 'Tipe', key: 'item_type.name' },
  { title: 'Status', key: 'status.name' },
  { title: 'Lokasi', key: 'location' },
  { title: 'Aksi', key: 'actions', sortable: false },
];

// State for Item Types
const itemTypes = ref<ItemType[]>([]);
const typeDialog = ref(false);
const editedType = ref<Partial<ItemType>>({});
const typeHeaders = [ 
  { title: 'ID', key: 'id' }, 
  { title: 'Nama Tipe', key: 'name' }, 
  { title: 'Aksi', key: 'actions', sortable: false }
];

// State for Statuses
const statuses = ref<Status[]>([]);
const statusDialog = ref(false);
const editedStatus = ref<Partial<Status>>({});
const statusHeaders = [ 
  { title: 'ID', key: 'id' }, 
  { title: 'Nama Status', key: 'name' }, 
  { title: 'Aksi', key: 'actions', sortable: false }
];

// --- Computed Titles ---
const formItemTitle = computed(() => editedItem.value.id ? 'Edit Item' : 'Tambah Item Baru');
const formTypeTitle = computed(() => editedType.value.id ? 'Edit Tipe Item' : 'Tambah Tipe Baru');
const formStatusTitle = computed(() => editedStatus.value.id ? 'Edit Status' : 'Tambah Status Baru');

// --- METHODS ---
async function fetchData() {
  loading.value = true;
  try {
    const [itemsRes, typesRes, statusesRes] = await Promise.all([
      apiClient.get('/inventory/'),
      apiClient.get('/inventory-types/'),
      apiClient.get('/inventory-statuses/'),
    ]);
    inventoryItems.value = itemsRes.data;
    itemTypes.value = typesRes.data;
    statuses.value = statusesRes.data;
  } catch (error) { console.error("Gagal mengambil data:", error); } 
  finally { loading.value = false; }
}

// Methods for Inventory Items
function openItemDialog(item: InventoryItem | null = null) {
  editedItem.value = item ? { ...item } : {};
  itemDialog.value = true;
}
function closeItemDialog() {
  itemDialog.value = false;
}
async function saveItem() {
  saving.value = true;
  try {
    const payload = { ...editedItem.value };
    if (payload.id) {
      await apiClient.patch(`/inventory/${payload.id}`, payload);
    } else {
      await apiClient.post('/inventory/', payload);
    }
    await fetchData();
    closeItemDialog();
  } catch (e) { console.error(e); } 
  finally { saving.value = false; }
}
async function deleteItem(item: InventoryItem) {
  if (confirm(`Hapus item SN: ${item.serial_number}?`)) {
    await apiClient.delete(`/inventory/${item.id}`);
    await fetchData();
  }
}

// Methods for Item Types
function openTypeDialog(item: ItemType | null = null) {
  editedType.value = item ? { ...item } : {};
  typeDialog.value = true;
}
function closeTypeDialog() {
  typeDialog.value = false;
}
async function saveType() {
  saving.value = true;
  try {
    const payload = { name: editedType.value.name };
    if (editedType.value.id) {
      await apiClient.patch(`/inventory-types/${editedType.value.id}`, payload);
    } else {
      await apiClient.post('/inventory-types/', payload);
    }
    await fetchData();
    closeTypeDialog();
  } catch (e) { console.error(e); } 
  finally { saving.value = false; }
}
async function deleteType(item: ItemType) {
  if (confirm(`Hapus tipe: ${item.name}?`)) {
    await apiClient.delete(`/inventory-types/${item.id}`);
    await fetchData();
  }
}

// Methods for Statuses
function openStatusDialog(item: Status | null = null) {
  editedStatus.value = item ? { ...item } : {};
  statusDialog.value = true;
}
function closeStatusDialog() {
  statusDialog.value = false;
}
async function saveStatus() {
  saving.value = true;
  try {
    const payload = { name: editedStatus.value.name };
    if (editedStatus.value.id) {
      await apiClient.patch(`/inventory-statuses/${editedStatus.value.id}`, payload);
    } else {
      await apiClient.post('/inventory-statuses/', payload);
    }
    await fetchData();
    closeStatusDialog();
  } catch (e) { console.error(e); } 
  finally { saving.value = false; }
}
async function deleteStatus(item: Status) {
  if (confirm(`Hapus status: ${item.name}?`)) {
    await apiClient.delete(`/inventory-statuses/${item.id}`);
    await fetchData();
  }
}

function getStatusColor(statusName: string = '') {
  const name = statusName.toLowerCase();
  if (name === 'terpasang') return 'success';
  if (name === 'rusak') return 'error';
  if (name === 'dalam perbaikan') return 'warning';
  if (name === 'perbaikan') return 'warning';
  if (name === 'gudang') return 'info';
  if (name === 'hilang') return 'error';
  if (name === 'dismantle') return 'grey-darken-1';
  return 'primary';
}

onMounted(fetchData);
</script>

<style scoped>
/* === CONTAINER & LAYOUT === */
.inventory-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 32px;
}

/* === PAGE HEADER === */
.page-header {
  margin-bottom: 40px;
}

.header-content {
  display: flex;
  align-items: center;
}

.header-avatar {
  margin-right: 20px;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 1.125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  font-weight: 400;
}

/* === MAIN CARD === */
.inventory-card {
  border-radius: 16px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

/* === MODERN TABS === */
.modern-tabs {
  background: rgb(var(--v-theme-surface));
}

.modern-tabs :deep(.v-tab) {
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0.5px;
  min-height: 72px;
  font-size: 1rem;
  transition: all 0.3s ease;
  padding: 0 24px;
}

.modern-tabs :deep(.v-tab--selected) {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-secondary), 0.1) 100%);
  color: rgb(var(--v-theme-primary));
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tab-text {
  font-size: 1rem;
  font-weight: 500;
}

/* === TAB CONTENT === */
.tab-window {
  min-height: 500px;
}

.tab-content {
  padding: 32px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 20px;
}

.content-title-wrapper {
  flex: 1;
}

.content-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  line-height: 1.3;
}

.content-subtitle {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
}

.add-btn {
  border-radius: 12px;
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0.5px;
  padding: 0 28px;
  height: 48px;
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.25);
  transition: all 0.3s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.35);
}

.btn-text {
  font-size: 1rem;
}

/* === TABLE STYLING === */
.table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.modern-table {
  background: rgb(var(--v-theme-surface));
}

.modern-table :deep(.v-data-table__wrapper) {
  border-radius: 12px;
}

.modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-primary), 0.05);
}

.modern-table :deep(.v-data-table-header th) {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  font-size: 0.95rem;
  letter-spacing: 0.5px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1);
  padding: 20px 16px;
  height: 60px;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04);
}

.modern-table :deep(.v-data-table__td) {
  padding: 20px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.5);
  font-size: 0.9rem;
  line-height: 1.4;
}

/* === TABLE CELL CONTENT === */
.status-chip {
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-size: 0.85rem;
  padding: 8px 12px;
}

.type-wrapper,
.serial-wrapper,
.mac-wrapper,
.location-wrapper {
  display: flex;
  align-items: center;
}

.serial-code,
.mac-code {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.type-name-wrapper {
  display: flex;
  align-items: center;
}

.type-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.status-name-wrapper {
  display: flex;
  align-items: center;
}

.status-preview-chip {
  font-weight: 500;
  border-radius: 8px;
  font-size: 0.85rem;
  padding: 8px 12px;
}

/* === ACTION BUTTONS === */
.action-buttons {
  display: flex;
  gap: 6px;
}

.action-btn {
  border-radius: 8px;
  transition: all 0.3s ease;
  min-width: 44px;
  min-height: 44px;
}

.action-btn:hover {
  transform: scale(1.1);
}

/* === NO DATA STATE === */
.no-data-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
}

.no-data-text {
  font-size: 1rem;
  margin-top: 8px;
}

/* === DIALOG STYLING === */
.dialog-card {
  border-radius: 16px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.dialog-header {
  background: rgba(var(--v-theme-primary), 0.05);
  padding: 24px 28px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  font-size: 1.35rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.dialog-content {
  padding: 28px;
}

.dialog-actions {
  padding: 20px 28px;
  background: rgba(var(--v-theme-surface), 0.5);
}

.form-field {
  margin-bottom: 12px;
}

.form-field :deep(.v-field__outline) {
  border-radius: 12px;
}

.form-field :deep(.v-field--focused .v-field__outline) {
  border-width: 2px;
}

.form-field :deep(.v-field__input) {
  font-size: 0.95rem;
  padding: 16px;
}

.form-field :deep(.v-field__prepend-inner) {
  padding-inline-start: 12px;
}

.cancel-btn {
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0 20px;
  height: 44px;
}

.save-btn {
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0 24px;
  height: 44px;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
}

/* === DARK MODE STYLES === */
.v-theme--dark .inventory-card {
  background: #1e293b;
  border: 1px solid #334155;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .modern-table {
  background: #1e293b;
}

.v-theme--dark .modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-primary), 0.15);
}

.v-theme--dark .modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .dialog-card {
  background: #1e293b;
}

.v-theme--dark .dialog-header {
  background: rgba(var(--v-theme-primary), 0.15);
  border-bottom: 1px solid #334155;
}

.v-theme--dark .dialog-actions {
  background: rgba(#0f172a, 0.5);
}

.v-theme--dark .serial-code,
.v-theme--dark .mac-code {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
}

/* === DESKTOP OPTIMIZATIONS === */
@media (min-width: 1024px) {
  .inventory-container {
    padding: 40px 48px;
  }
  
  .page-title {
    font-size: 2.75rem;
  }
  
  .page-subtitle {
    font-size: 1.2rem;
  }
  
  .header-avatar {
    size: 64px;
  }
  
  .content-title {
    font-size: 2rem;
  }
  
  .content-subtitle {
    font-size: 1.1rem;
  }
  
  .tab-content {
    padding: 40px;
  }
  
  .modern-table :deep(.v-data-table-header th) {
    font-size: 1rem;
    padding: 24px 20px;
    height: 64px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 24px 20px;
    font-size: 0.95rem;
  }
  
  .status-chip {
    font-size: 0.9rem;
    padding: 10px 16px;
  }
  
  .status-preview-chip {
    font-size: 0.9rem;
    padding: 10px 16px;
  }
  
  .serial-code,
  .mac-code {
    padding: 8px 16px;
    font-size: 0.9rem;
  }
  
  .type-name {
    font-size: 0.95rem;
  }
  
  .no-data-wrapper {
    padding: 80px 32px;
  }
  
  .no-data-text {
    font-size: 1.1rem;
  }
}

@media (min-width: 1440px) {
  .inventory-container {
    padding: 48px 64px;
  }
  
  .page-title {
    font-size: 3rem;
  }
  
  .page-subtitle {
    font-size: 1.25rem;
  }
  
  .content-title {
    font-size: 2.125rem;
  }
  
  .content-subtitle {
    font-size: 1.125rem;
  }
  
  .tab-content {
    padding: 48px;
  }
  
  .modern-table :deep(.v-data-table-header th) {
    font-size: 1.05rem;
    padding: 28px 24px;
    height: 68px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 28px 24px;
    font-size: 1rem;
  }
  
  .status-chip {
    font-size: 0.95rem;
    padding: 12px 18px;
  }
  
  .status-preview-chip {
    font-size: 0.95rem;
    padding: 12px 18px;
  }
  
  .serial-code,
  .mac-code {
    padding: 10px 18px;
    font-size: 0.95rem;
  }
  
  .type-name {
    font-size: 1rem;
  }
}

/* === RESPONSIVE DESIGN === */

/* Tablet (768px and below) */
@media (max-width: 768px) {
  .inventory-container {
    padding: 16px;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .page-subtitle {
    font-size: 0.9rem;
  }
  
  .content-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .content-title {
    font-size: 1.25rem;
  }
  
  .content-subtitle {
    font-size: 0.85rem;
  }
  
  .add-btn {
    width: 100%;
    height: 48px;
  }
  
  .tab-content {
    padding: 16px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 12px 8px;
  }
  
  .dialog-content {
    padding: 20px;
  }
  
  /* Hide some columns on mobile */
  .modern-table :deep(.v-data-table__th:nth-child(2)),
  .modern-table :deep(.v-data-table__td:nth-child(2)) {
    display: none;
  }
}

/* Mobile (600px and below) */
@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-avatar {
    margin-right: 0;
    margin-bottom: 8px;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 0.85rem;
  }
  
  .tab-text {
    display: none;
  }
  
  .modern-tabs :deep(.v-tab) {
    min-width: 80px;
    padding: 0 12px;
  }
  
  .content-title {
    font-size: 1.1rem;
  }
  
  .content-subtitle {
    font-size: 0.8rem;
  }
  
  .btn-text {
    display: none;
  }
  
  .add-btn {
    min-width: 56px;
    width: auto;
    padding: 0 16px;
  }
  
  /* Further hide columns on small mobile */
  .modern-table :deep(.v-data-table__th:nth-child(3)),
  .modern-table :deep(.v-data-table__td:nth-child(3)) {
    display: none;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
}

/* Small Mobile (480px and below) */
@media (max-width: 480px) {
  .inventory-container {
    padding: 12px;
  }
  
  .page-header {
    margin-bottom: 20px;
  }
  
  .page-title {
    font-size: 1.35rem;
  }
  
  .tab-content {
    padding: 12px;
  }
  
  .content-header {
    gap: 12px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 8px 6px;
    font-size: 0.85rem;
  }
  
  .dialog-content {
    padding: 16px;
  }
  
  .dialog-header {
    padding: 16px 20px;
    font-size: 1.1rem;
  }
  
  .dialog-actions {
    padding: 12px 20px;
  }
}

/* Extra Small Mobile (360px and below) */
@media (max-width: 360px) {
  .inventory-container {
    padding: 8px;
  }
  
  .page-title {
    font-size: 1.25rem;
  }
  
  .page-subtitle {
    font-size: 0.8rem;
  }
  
  .tab-content {
    padding: 8px;
  }
  
  .content-title {
    font-size: 1rem;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 6px 4px;
    font-size: 0.8rem;
  }
  
  /* Show only essential columns on very small screens */
  .modern-table :deep(.v-data-table__th:nth-child(4)),
  .modern-table :deep(.v-data-table__td:nth-child(4)),
  .modern-table :deep(.v-data-table__th:nth-child(5)),
  .modern-table :deep(.v-data-table__td:nth-child(5)) {
    display: none;
  }
}

/* === ANIMATIONS === */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tab-content {
  animation: fadeIn 0.4s ease-out;
}

.status-chip {
  transition: all 0.3s ease;
}

.status-chip:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* === LIGHT/DARK MODE TRANSITIONS === */
.inventory-card,
.dialog-card,
.modern-table,
.form-field,
.status-chip,
.serial-code,
.mac-code {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* === ENHANCED FOCUS STATES === */
.form-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.action-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

/* === LOADING STATES === */
.modern-table :deep(.v-skeleton-loader) {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
}

/* === IMPROVED ACCESSIBILITY === */
.action-btn {
  min-width: 40px;
  min-height: 40px;
}

.tab-item {
  min-height: 48px;
}

/* === PRINT STYLES === */
@media print {
  .add-btn,
  .action-buttons,
  .modern-tabs {
    display: none !important;
  }
  
  .inventory-card {
    box-shadow: none;
    border: 1px solid #ccc;
  }
  
  .page-title {
    color: #000 !important;
  }
}
</style>