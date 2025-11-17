<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Modern Header with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar class="me-4 elevation-4" color="primary" size="80">
              <v-icon color="white" size="40">mdi-file-document-multiple-outline</v-icon>
            </v-avatar>
            <div>
              <h1 class="text-h4 font-weight-bold text-white mb-2">Manajemen S&K dan Catatan Rilis</h1>
              <p class="header-subtitle mb-0">
                Kelola syarat & ketentuan dan rilis update sistem
              </p>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              variant="elevated"
              size="large"
              elevation="2"
              @click="openDialog()"
              prepend-icon="mdi-plus"
              class="text-none font-weight-bold rounded-lg"
            >
              <span>Tambah Konten</span>
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Card -->
    <v-card class="content-card" elevation="0">
      <div class="table-header">
        <v-card-title class="d-flex align-center pa-6">
          <div class="d-flex align-center flex-grow-1">
            <v-icon color="purple" size="24" class="me-3">mdi-format-list-bulleted</v-icon>
            <span class="text-h6 font-weight-bold">Daftar Konten</span>
          </div>
          <v-chip
            :color="skItems.length > 0 ? 'purple' : 'grey'"
            variant="tonal"
            size="small"
            class="items-counter"
          >
            <v-icon start size="16">mdi-counter</v-icon>
            {{ skItems.length }} item
          </v-chip>
        </v-card-title>
      </div>

      <!-- Desktop Table View -->
      <div v-if="!isMobile" class="table-container">
        <v-data-table
          :headers="headers"
          :items="skItems"
          :loading="loading"
          class="modern-table"
          :items-per-page="10"
          :loading-text="'Memuat data...'"
          :no-data-text="'Belum ada konten tersedia'"
        >
        <template v-slot:loading>
          <SkeletonLoader type="table" :rows="8" />
        </template>

          <template v-slot:item.tipe="{ item }">
            <v-chip 
              :color="item.tipe === 'Pembaruan' ? 'success' : 'primary'"
              size="small"
              variant="tonal"
              class="type-chip"
            >
              <v-icon left size="small">
                {{ item.tipe === 'Pembaruan' ? 'mdi-update' : 'mdi-file-document-outline' }}
              </v-icon>
              {{ item.tipe }}
            </v-chip>
          </template>
          
          <template v-slot:item.versi="{ item }">
            <v-chip 
              v-if="item.versi" 
              color="info" 
              size="small" 
              variant="outlined"
              class="version-chip"
            >
              {{ item.versi }}
            </v-chip>
            <span v-else class="text-medium-emphasis">-</span>
          </template>
          
          <template v-slot:item.created_at="{ item }">
            <div class="date-column">
              <div class="date-primary">{{ formatDate(item.created_at) }}</div>
              <div class="date-secondary">{{ formatTime(item.created_at) }}</div>
            </div>
          </template>
          
          <template v-slot:item.actions="{ item }">
            <div class="action-buttons">
              <v-btn
                icon
                size="small"
                variant="text"
                color="primary"
                class="action-btn"
                @click="openDialog(item)"
              >
                <v-icon size="18">mdi-pencil</v-icon>
                <v-tooltip activator="parent" location="top">Edit</v-tooltip>
              </v-btn>
              <v-btn
                icon
                size="small"
                variant="text"
                color="error"
                class="action-btn"
                @click="openDeleteDialog(item)"
              >
                <v-icon size="18">mdi-delete</v-icon>
                <v-tooltip activator="parent" location="top">Hapus</v-tooltip>
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </div>

      <!-- Mobile Card View -->
      <div v-else class="mobile-cards-container">
        <v-progress-circular v-if="loading" indeterminate color="primary" class="loading-spinner"></v-progress-circular>
        
        <div v-else-if="skItems.length === 0" class="empty-state">
          <v-icon size="64" color="grey-lighten-1">mdi-file-document-outline</v-icon>
          <p class="text-medium-emphasis mt-4">Belum ada konten tersedia</p>
        </div>
        
        <v-card
          v-else
          v-for="item in skItems"
          :key="item.id"
          class="mobile-item-card"
          elevation="1"
        >
          <v-card-text class="mobile-card-content">
            <div class="mobile-card-header">
              <h3 class="mobile-item-title">{{ item.judul }}</h3>
              <div class="mobile-badges">
                <v-chip 
                  :color="item.tipe === 'Pembaruan' ? 'success' : 'primary'"
                  size="small"
                  variant="tonal"
                >
                  {{ item.tipe }}
                </v-chip>
                <v-chip 
                  v-if="item.versi" 
                  color="info" 
                  size="small" 
                  variant="outlined"
                >
                  {{ item.versi }}
                </v-chip>
              </div>
            </div>
            
            <div class="mobile-meta">
              <v-icon size="14" class="meta-icon">mdi-calendar</v-icon>
              <span class="meta-text">{{ formatDate(item.created_at) }}</span>
            </div>
            
            <div class="mobile-actions">
              <v-btn
                variant="outlined"
                color="primary"
                size="small"
                @click="openDialog(item)"
              >
                <v-icon left size="16">mdi-pencil</v-icon>
                Edit
              </v-btn>
              <v-btn
                variant="outlined"
                color="error"
                size="small"
                @click="openDeleteDialog(item)"
              >
                <v-icon left size="16">mdi-delete</v-icon>
                Hapus
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </div>
    </v-card>

    <!-- Add/Edit Dialog -->
    <v-dialog 
      v-model="dialog" 
      :max-width="isMobile ? '95vw' : '700px'" 
      persistent
      :fullscreen="isMobile"
    >
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon left color="primary">
            {{ editedIndex === -1 ? 'mdi-plus-circle' : 'mdi-pencil-circle' }}
          </v-icon>
          {{ formTitle }}
          <v-spacer></v-spacer>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeDialog"
            class="close-btn"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="dialog-content">
          <v-form ref="form" class="form-container">
            <div class="form-section">
              <label class="form-label">Judul Konten</label>
              <v-text-field
                v-model="editedItem.judul"
                placeholder="Masukkan judul konten..."
                variant="outlined"
                density="comfortable"
                class="form-field"
                :rules="[v => !!v || 'Judul harus diisi']"
              ></v-text-field>
            </div>

            <div class="form-section">
              <label class="form-label">Konten</label>
              <v-textarea
                v-model="editedItem.konten"
                placeholder="Masukkan konten (mendukung HTML dasar)..."
                variant="outlined"
                rows="6"
                class="form-field"
                :rules="[v => !!v || 'Konten harus diisi']"
              ></v-textarea>
              <v-card variant="tonal" color="info" class="mt-2">
                <v-card-text class="pa-3">
                  <div class="d-flex align-center">
                    <v-icon left size="18" color="info">mdi-information</v-icon>
                    <span class="text-caption">Anda dapat menggunakan tag HTML dasar seperti &lt;strong&gt;, &lt;em&gt;, &lt;p&gt;, &lt;br&gt;</span>
                  </div>
                </v-card-text>
              </v-card>
            </div>

            <div class="form-section">
              <label class="form-label">Tipe Konten</label>
              <v-select
                v-model="editedItem.tipe"
                :items="['Ketentuan', 'Pembaruan']"
                variant="outlined"
                density="comfortable"
                class="form-field"
                :rules="[v => !!v || 'Tipe harus dipilih']"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:prepend>
                      <v-icon>
                        {{ item.value === 'Pembaruan' ? 'mdi-update' : 'mdi-file-document-outline' }}
                      </v-icon>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </div>

            <div v-if="editedItem.tipe === 'Pembaruan'" class="form-section">
              <label class="form-label">Versi</label>
              <v-text-field
                v-model="editedItem.versi"
                placeholder="contoh: v2.1.0"
                variant="outlined"
                density="comfortable"
                class="form-field"
                :rules="editedItem.tipe === 'Pembaruan' ? [v => !!v || 'Versi harus diisi untuk tipe Pembaruan'] : []"
              >
                <template v-slot:prepend-inner>
                  <v-icon size="18" color="info">mdi-tag</v-icon>
                </template>
              </v-text-field>
            </div>
          </v-form>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeDialog"
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
            <v-icon left>mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="dialogDelete" :max-width="isMobile ? '95vw' : '500px'">
      <v-card class="delete-dialog">
        <v-card-title class="delete-header">
          <v-icon left color="error">mdi-alert-circle</v-icon>
          Konfirmasi Hapus
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="delete-content">
          <div class="delete-message">
            <p>Anda yakin ingin menghapus konten ini?</p>
            <v-card variant="tonal" color="error" class="mt-4">
              <v-card-text class="pa-3">
                <div class="font-weight-bold">{{ itemToDelete?.judul }}</div>
                <div class="text-caption text-medium-emphasis">{{ itemToDelete?.tipe }}</div>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="delete-actions">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeDeleteDialog"
          >
            Batal
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="deleteItemConfirm"
            :loading="deleting"
          >
            <v-icon left>mdi-delete</v-icon>
            Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useDisplay } from 'vuetify';
import apiClient from '@/services/api';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

interface SKItem {
  id: number;
  judul: string;
  konten: string;
  tipe: string;
  versi: string | null;
  created_at: string;
}

// Display composable for responsive design
const { mobile } = useDisplay();
const isMobile = computed(() => mobile.value);

const skItems = ref<SKItem[]>([]);
const loading = ref(true);
const dialog = ref(false);
const dialogDelete = ref(false);
const saving = ref(false);
const deleting = ref(false);

const editedIndex = ref(-1);
const editedItem = ref<Partial<SKItem>>({});
const itemToDelete = ref<SKItem | null>(null);

const formTitle = computed(() => editedIndex.value === -1 ? 'Tambah Konten Baru' : 'Edit Konten');

const headers = [
  { 
    title: 'Judul', 
    key: 'judul',
    sortable: true,
    width: '35%'
  },
  { 
    title: 'Tipe', 
    key: 'tipe',
    sortable: true,
    width: '15%'
  },
  { 
    title: 'Versi', 
    key: 'versi',
    sortable: false,
    width: '12%'
  },
  { 
    title: 'Dibuat Pada', 
    key: 'created_at',
    sortable: true,
    width: '23%'
  },
  { 
    title: 'Actions', 
    key: 'actions', 
    sortable: false,
    width: '15%',
    align: 'center' as const
  },
] as const;

async function fetchSK() {
  loading.value = true;
  try {
    const response = await apiClient.get('/sk/');
    skItems.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data S&K:", error);
  } finally {
    loading.value = false;
  }
}

function openDialog(item?: SKItem) {
  editedIndex.value = item ? skItems.value.indexOf(item) : -1;
  editedItem.value = item ? { ...item } : { tipe: 'Ketentuan' };
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = {};
  editedIndex.value = -1;
}

async function saveItem() {
  saving.value = true;
  try {
    if (editedIndex.value > -1) {
      // Update
      await apiClient.patch(`/sk/${editedItem.value.id}`, editedItem.value);
    } else {
      // Create
      await apiClient.post('/sk/', editedItem.value);
    }
    fetchSK();
    closeDialog();
  } catch (error) {
    console.error("Gagal menyimpan item S&K:", error);
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: SKItem) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  itemToDelete.value = null;
}

async function deleteItemConfirm() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/sk/${itemToDelete.value.id}`);
    fetchSK();
    closeDeleteDialog();
  } catch (error) {
    console.error("Gagal menghapus item S&K:", error);
  } finally {
    deleting.value = false;
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit', 
    month: 'long', 
    year: 'numeric'
  });
}

function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString('id-ID', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

onMounted(fetchSK);
</script>

<style scoped>
/* ===== GENERAL LAYOUT ===== */
.modern-container {
  background-color: rgb(var(--v-theme-background));
  min-height: 100vh;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

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

/* Dark mode specific adjustments */
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


/* ===== CONTENT CARD ===== */
.content-card {
  border-radius: 16px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  overflow: hidden;
}

/* Table Header */
.table-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.table-header .v-card-title {
  background: transparent;
}

.items-counter {
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* ===== TABLE STYLES ===== */
.table-container {
  overflow-x: auto;
}

.modern-table {
  background: transparent;
}

.modern-table :deep(.v-data-table__wrapper) {
  border-radius: 0;
}

.modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.modern-table :deep(.v-data-table-header th) {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  padding: 1rem;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.type-chip {
  font-weight: 500;
  border-radius: 8px;
}

.version-chip {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.date-column {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date-primary {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.date-secondary {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
}

.action-btn {
  border-radius: 8px;
}

.action-btn:hover {
  transform: scale(1.1);
}

/* ===== MOBILE CARDS ===== */
.mobile-cards-container {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.loading-spinner {
  align-self: center;
  margin: 2rem 0;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.mobile-item-card {
  border-radius: 12px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  transition: all 0.3s ease;
}

.mobile-item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.mobile-card-content {
  padding: 1.25rem;
}

.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.mobile-item-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.3;
  flex: 1;
}

.mobile-badges {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
}

.mobile-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.meta-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.meta-text {
  font-size: 0.875rem;
}

.mobile-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* ===== DIALOG STYLES ===== */
.dialog-card {
  border-radius: 16px;
  background: rgb(var(--v-theme-surface));
  max-height: 90vh;
  overflow: hidden;
}

.dialog-header {
  background: rgba(var(--v-theme-primary), 0.05);
  padding: 1.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.close-btn {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.close-btn:hover {
  background-color: rgba(var(--v-theme-error), 0.1);
  color: rgb(var(--v-theme-error));
}

.dialog-content {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.form-field :deep(.v-field) {
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.form-field :deep(.v-field:hover) {
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.form-field :deep(.v-field--focused) {
  background: rgba(var(--v-theme-primary), 0.05);
}

.dialog-actions {
  padding: 1.5rem;
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.cancel-btn {
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: none;
  font-weight: 500;
}

.save-btn {
  border-radius: 10px;
  text-transform: none;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
}

.save-btn:hover {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.4);
}

/* ===== DELETE DIALOG ===== */
.delete-dialog {
  border-radius: 16px;
}

.delete-header {
  background: rgba(var(--v-theme-error), 0.05);
  color: rgb(var(--v-theme-error));
  padding: 1.5rem;
  font-weight: 600;
}

.delete-content {
  padding: 2rem;
}

.delete-message p {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1rem;
  margin-bottom: 0;
}

.delete-actions {
  padding: 1.5rem;
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

/* ===== DARK MODE SPECIFIC ===== */
.v-theme--dark .content-card {
  background: #1e293b;
  border: 1px solid #334155;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.v-theme--dark .card-header {
  background: rgba(129, 140, 248, 0.1);
  border-bottom: 1px solid #334155;
}

.v-theme--dark .modern-table :deep(.v-data-table-header) {
  background: rgba(51, 65, 85, 0.5);
}

.v-theme--dark .modern-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(129, 140, 248, 0.1);
}

.v-theme--dark .dialog-card {
  background: #1e293b;
}

.v-theme--dark .dialog-header {
  background: rgba(129, 140, 248, 0.1);
  border-bottom: 1px solid #334155;
}

.v-theme--dark .dialog-content {
  background: #1e293b;
}

.v-theme--dark .dialog-actions {
  background: rgba(51, 65, 85, 0.3);
}

.v-theme--dark .delete-header {
  background: rgba(239, 68, 68, 0.1);
}

.v-theme--dark .delete-actions {
  background: rgba(51, 65, 85, 0.3);
}

/* ===== RESPONSIVE DESIGN ===== */
@media (max-width: 768px) {
  .modern-container {
    padding: 1rem;
  }
  
  .header-content {
    padding: 20px;
  }

  .header-section h1 {
    font-size: 1.5rem !important;
  }

  .header-subtitle {
    font-size: 0.95rem;
  }
  
  .mobile-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .mobile-badges {
    flex-direction: row;
    align-self: flex-start;
  }
  
  .mobile-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .mobile-actions .v-btn {
    width: 100%;
  }
  
  .dialog-content {
    padding: 1.5rem;
    max-height: 70vh;
  }
  
  .form-container {
    gap: 1.25rem;
  }
  
  .dialog-actions {
    padding: 1.25rem;
  }
  
  .dialog-actions .v-btn {
    min-width: 100px;
  }
}

@media (max-width: 480px) {
  .modern-container {
    padding: 0.75rem;
  }
  
  .header-section h1 {
    font-size: 1.25rem !important;
  }

  .header-subtitle {
    font-size: 0.85rem;
  }
  
  .mobile-item-title {
    font-size: 1rem;
  }
  
  .mobile-meta {
    font-size: 0.8rem;
  }
  
  .dialog-content {
    padding: 1.25rem;
  }
  
  .dialog-actions {
    padding: 1rem;
  }
}

@media (max-width: 360px) {
  .modern-container {
    padding: 0.5rem;
  }
  
  .header-content {
    padding: 16px;
  }

  .header-section h1 {
    font-size: 1.25rem !important;
  }
  
  .mobile-card-content {
    padding: 1rem;
  }
  
  .dialog-content {
    padding: 1rem;
  }
  
  .form-container {
    gap: 1rem;
  }
}

/* ===== LOADING AND TRANSITION EFFECTS ===== */
.v-progress-circular {
  margin: 2rem auto;
}

.mobile-item-card {
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== DARK MODE ENHANCEMENTS ===== */
.v-theme--dark .modern-container {
  background-color: #0f172a;
}

.v-theme--dark .mobile-item-card {
  background: #1e293b;
  border: 1px solid #334155;
}

.v-theme--dark .mobile-item-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .form-field :deep(.v-field) {
  background: rgba(51, 65, 85, 0.3);
}

.v-theme--dark .form-field :deep(.v-field:hover) {
  background: rgba(51, 65, 85, 0.5);
}

.v-theme--dark .form-field :deep(.v-field--focused) {
  background: rgba(129, 140, 248, 0.1);
}

/* ===== ACCESSIBILITY IMPROVEMENTS ===== */
.action-btn:focus {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.add-btn:focus {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

/* ===== SMOOTH SCROLLBAR FOR WEBKIT ===== */
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.5);
}

/* ===== HIGH CONTRAST MODE SUPPORT ===== */
@media (prefers-contrast: high) {
  .content-card {
    border: 2px solid rgba(var(--v-border-color), 1);
  }
  
  .mobile-item-card {
    border: 2px solid rgba(var(--v-border-color), 1);
  }
  
  .type-chip,
  .version-chip,
  .items-count-chip {
    border: 1px solid currentColor;
  }
}

/* ===== PRINT STYLES ===== */
@media print {
  .header-card,
  .mobile-actions,
  .dialog-actions {
    display: none !important;
  }
  
  .content-card {
    box-shadow: none;
    border: 1px solid #000;
  }
  
  .modern-table,
  .mobile-cards-container {
    background: white !important;
    color: black !important;
  }
}
</style>