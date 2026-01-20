<template>
  <v-container fluid class="pa-4 pa-md-6 diskon-view">
    <!-- Header Section with Dynamic Gradient -->
    <div class="header-card mb-6 animate-fade-in">
      <div class="header-glass-effect"></div>
      <div class="header-content">
        <v-row align="center" class="ma-0">
          <v-col cols="12" md="auto" class="d-flex align-center mb-4 mb-md-0">
            <div class="icon-wrapper me-4">
              <v-avatar class="header-avatar" size="64">
                <v-icon color="white" size="32">mdi-percent-outline</v-icon>
              </v-avatar>
            </div>
            <div>
              <h1 class="text-h4 text-md-h3 font-weight-bold text-white mb-1 header-title">
                Manajemen Diskon
              </h1>
              <p class="header-subtitle text-white mb-0">
                Kelola diskon berdasarkan cluster/alamat pelanggan
              </p>
            </div>
          </v-col>
          <v-spacer class="d-none d-md-flex"></v-spacer>
          <v-col cols="12" md="auto">
            <v-btn
              color="white"
              size="large"
              elevation="8"
              @click="openDialog()"
              prepend-icon="mdi-plus-circle"
              class="text-none font-weight-bold px-6 add-btn"
              variant="elevated"
              block
            >
              <span class="gradient-text">Tambah Diskon</span>
            </v-btn>
          </v-col>
        </v-row>
      </div>
    </div>

    <!-- Main Content Card -->
    <div class="content-section animate-slide-up">
      <v-card 
        elevation="0" 
        class="main-card rounded-xl overflow-hidden"
        :class="{ 'dark-card': isDark }"
      >
        <!-- Card Header -->
        <div class="card-header-wrapper">
          <v-card-title class="d-flex flex-column flex-sm-row align-sm-center pa-6">
            <div class="d-flex align-center mb-3 mb-sm-0">
              <div class="title-icon-wrapper me-3">
                <v-icon color="primary" size="28">mdi-ticket-percent</v-icon>
              </div>
              <span class="text-h5 text-sm-h6 font-weight-bold">Daftar Diskon</span>
            </div>
            <v-spacer class="d-none d-sm-flex"></v-spacer>
            <v-chip
              :color="isDark ? 'green-darken-2' : 'green'"
              variant="flat"
              size="default"
              prepend-icon="mdi-counter"
              class="counter-chip"
            >
              <span class="font-weight-bold">{{ diskonList.length }} Diskon</span>
            </v-chip>
          </v-card-title>
        </div>

        <!-- Filter Section -->
        <v-card-text class="pa-4 pa-md-6 filter-section">
          <v-row>
            <v-col cols="12" sm="6" md="4">
              <v-text-field
                v-model="searchQuery"
                label="Cari diskon..."
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                class="search-field"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="filterActive"
                :items="activeFilterOptions"
                label="Filter Status"
                prepend-inner-icon="mdi-filter"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>

        <!-- Data Table with Mobile Optimization -->
        <div class="table-wrapper">
          <v-data-table
            :headers="headers"
            :items="filteredDiskonList"
            :loading="loading"
            item-value="id"
            class="elevation-0 custom-table"
            :loading-text="'Memuat data diskon...'"
            :mobile-breakpoint="0"
          >
            <template v-slot:loading>
              <div class="pa-4">
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </div>
            </template>

            <template v-slot:item.nama_diskon="{ item }">
              <div class="d-flex align-center py-2">
                <v-avatar size="36" class="discount-avatar me-3">
                  <v-icon color="white" size="18">mdi-percent</v-icon>
                </v-avatar>
                <span class="font-weight-medium text-body-1">{{ item.nama_diskon }}</span>
              </div>
            </template>

            <template v-slot:item.persentase_diskon="{ item }">
              <v-chip
                :color="isDark ? 'success-darken-1' : 'success'"
                variant="flat"
                size="default"
                class="font-weight-bold percentage-chip"
              >
                {{ item.persentase_diskon }}%
              </v-chip>
            </template>

            <template v-slot:item.cluster="{ item }">
              <v-chip
                :color="isDark ? 'blue-darken-2' : 'blue'"
                variant="tonal"
                size="default"
                prepend-icon="mdi-map-marker"
                class="cluster-chip"
              >
                {{ item.cluster }}
              </v-chip>
            </template>

            <template v-slot:item.is_active="{ item }">
              <v-chip
                :color="item.is_active ? (isDark ? 'success-darken-1' : 'success') : (isDark ? 'error-darken-1' : 'error')"
                variant="flat"
                size="default"
                :prepend-icon="item.is_active ? 'mdi-check-circle' : 'mdi-cancel'"
                class="status-chip"
              >
                {{ item.is_active ? 'Aktif' : 'Nonaktif' }}
              </v-chip>
            </template>

            <template v-slot:item.periode="{ item }">
              <div class="periode-info">
                <div v-if="item.tgl_mulai || item.tgl_selesai" class="text-caption">
                  <div v-if="item.tgl_mulai" class="mb-1">
                    <v-icon size="12" class="me-1">mdi-calendar-start</v-icon>
                    {{ formatDate(item.tgl_mulai) }}
                  </div>
                  <div v-if="item.tgl_selesai">
                    <v-icon size="12" class="me-1">mdi-calendar-end</v-icon>
                    {{ formatDate(item.tgl_selesai) }}
                  </div>
                </div>
                <v-chip v-else color="grey" variant="tonal" size="small">Tanpa periode</v-chip>
              </div>
            </template>

            <template v-slot:item.actions="{ item }">
              <div class="d-flex ga-2 action-buttons">
                <v-tooltip text="Edit" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      size="small"
                      variant="tonal"
                      color="primary"
                      @click="editItem(item)"
                      icon="mdi-pencil"
                      class="action-btn"
                    ></v-btn>
                  </template>
                </v-tooltip>
                
                <v-tooltip :text="item.is_active ? 'Pause' : 'Activate'" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      v-if="item.is_active"
                      size="small"
                      variant="tonal"
                      color="warning"
                      @click="toggleActive(item)"
                      icon="mdi-pause"
                      class="action-btn"
                    ></v-btn>
                    <v-btn
                      v-bind="props"
                      v-else
                      size="small"
                      variant="tonal"
                      color="success"
                      @click="toggleActive(item)"
                      icon="mdi-play"
                      class="action-btn"
                    ></v-btn>
                  </template>
                </v-tooltip>

                <v-tooltip text="Delete" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      size="small"
                      variant="tonal"
                      color="error"
                      @click="deleteItem(item)"
                      icon="mdi-delete"
                      class="action-btn"
                    ></v-btn>
                  </template>
                </v-tooltip>
              </div>
            </template>
          </v-data-table>
        </div>
      </v-card>
    </div>

    <!-- Dialog Form with Enhanced Styling -->
    <v-dialog 
      v-model="dialog" 
      max-width="650px" 
      persistent
      :fullscreen="isMobile"
      transition="dialog-bottom-transition"
    >
      <v-card class="dialog-card" :class="{ 'dark-card': isDark }">
        <v-card-title class="dialog-header pa-6">
          <div class="d-flex align-center">
            <v-icon size="28" class="me-3" color="primary">
              {{ editedIndex === -1 ? 'mdi-plus-circle' : 'mdi-pencil' }}
            </v-icon>
            <span class="text-h5 font-weight-bold">{{ formTitle }}</span>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-6">
          <v-form ref="form" v-model="valid">
            <v-text-field
              v-model="editedItem.nama_diskon"
              label="Nama Diskon"
              :rules="[rules.required]"
              variant="outlined"
              prepend-inner-icon="mdi-tag"
              required
              class="mb-2"
            ></v-text-field>

            <v-text-field
              v-model.number="editedItem.persentase_diskon"
              label="Persentase Diskon (%)"
              type="number"
              :rules="[rules.required, rules.min, rules.max]"
              variant="outlined"
              prepend-inner-icon="mdi-percent"
              suffix="%"
              required
              class="mb-2"
            ></v-text-field>

            <v-combobox
              v-model="editedItem.cluster"
              :items="clusterSuggestions"
              label="Cluster / Alamat"
              :rules="[rules.required]"
              variant="outlined"
              prepend-inner-icon="mdi-map-marker"
              placeholder="Contoh: Waringin, Blok A, dll"
              required
              class="mb-2"
            ></v-combobox>

            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="editedItem.tgl_mulai"
                  label="Tanggal Mulai (Opsional)"
                  type="date"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-start"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="editedItem.tgl_selesai"
                  label="Tanggal Selesai (Opsional)"
                  type="date"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-end"
                  :min="editedItem.tgl_mulai"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-switch
              v-model="editedItem.is_active"
              color="success"
              label="Status Aktif"
              prepend-icon="mdi-power"
              inset
              class="mt-2"
            ></v-switch>
          </v-form>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="pa-6">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            @click="closeDialog"
            size="large"
            class="text-none px-6"
          >
            Batal
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="saveItem"
            :loading="saving"
            :disabled="!valid"
            size="large"
            class="text-none px-6"
          >
            <v-icon start>mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="450px">
      <v-card class="dialog-card delete-dialog" :class="{ 'dark-card': isDark }">
        <v-card-title class="pa-6">
          <div class="d-flex align-center">
            <v-icon size="28" color="error" class="me-3">mdi-alert-circle</v-icon>
            <span class="text-h6 font-weight-bold">Konfirmasi Hapus</span>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-6">
          <p class="text-body-1 mb-0">
            Apakah Anda yakin ingin menonaktifkan diskon 
            <strong class="text-primary">"{{ itemToDelete?.nama_diskon }}"</strong>?
          </p>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="pa-6">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            @click="deleteDialog = false"
            size="large"
            class="text-none px-6"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="elevated" 
            @click="confirmDelete" 
            :loading="deleting"
            size="large"
            class="text-none px-6"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useTheme, useDisplay } from 'vuetify';
import apiClient from '@/services/api';

// Vuetify composables
const theme = useTheme();
const { mobile } = useDisplay();

// Computed properties for theme
const isDark = computed(() => theme.global.current.value.dark);
const isMobile = computed(() => mobile.value);

// Types
interface Diskon {
  id?: number;
  nama_diskon: string;
  persentase_diskon: number;
  cluster: string;
  is_active: boolean;
  tgl_mulai?: string;
  tgl_selesai?: string;
}

// State
const diskonList = ref<Diskon[]>([]);
const loading = ref(true);
const dialog = ref(false);
const deleteDialog = ref(false);
const saving = ref(false);
const deleting = ref(false);
const valid = ref(false);
const form = ref();
const searchQuery = ref('');
const filterActive = ref<boolean | null>(null);

// Cluster suggestions from existing pelanggan
const clusterSuggestions = ref<string[]>([]);

const editedIndex = ref(-1);
const editedItem = ref<Diskon>({
  nama_diskon: '',
  persentase_diskon: 0,
  cluster: '',
  is_active: true,
  tgl_mulai: '',
  tgl_selesai: '',
});

const defaultItem: Diskon = {
  nama_diskon: '',
  persentase_diskon: 0,
  cluster: '',
  is_active: true,
  tgl_mulai: '',
  tgl_selesai: '',
};

const itemToDelete = ref<Diskon | null>(null);

// Active filter options
const activeFilterOptions = [
  { title: 'Semua', value: null },
  { title: 'Aktif', value: true },
  { title: 'Nonaktif', value: false },
];

// Headers
const headers = [
  { title: 'Nama Diskon', key: 'nama_diskon', sortable: true },
  { title: 'Persentase', key: 'persentase_diskon', sortable: true },
  { title: 'Cluster', key: 'cluster', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Periode', key: 'periode', sortable: false },
  { title: 'Aksi', key: 'actions', sortable: false, align: 'end' as const },
];

// Validation rules
const rules = {
  required: (v: any) => !!v || 'Field ini wajib diisi',
  min: (v: number) => v > 0 || 'Minimal 1%',
  max: (v: number) => v <= 100 || 'Maksimal 100%',
};

// Computed
const formTitle = computed(() => (editedIndex.value === -1 ? 'Tambah Diskon' : 'Edit Diskon'));

const filteredDiskonList = computed(() => {
  let filtered = diskonList.value;

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      (item) =>
        item.nama_diskon.toLowerCase().includes(query) ||
        item.cluster.toLowerCase().includes(query)
    );
  }

  // Filter by active status
  if (filterActive.value !== null) {
    filtered = filtered.filter((item) => item.is_active === filterActive.value);
  }

  return filtered;
});

// Methods
async function fetchDiskon() {
  loading.value = true;
  try {
    const response = await apiClient.get('/diskon/');
    diskonList.value = response.data.data || response.data;
  } catch (error) {
    console.error('Error fetching diskon:', error);
  } finally {
    loading.value = false;
  }
}

async function fetchClusterSuggestions() {
  try {
    // Gunakan endpoint khusus yang lebih efisien untuk mendapatkan semua cluster unik
    const response = await apiClient.get('/diskon/clusters/list');
    
    // Response sudah berupa array string cluster yang sorted
    clusterSuggestions.value = response.data || [];
    
    console.log(`✅ Loaded ${clusterSuggestions.value.length} unique clusters`);
  } catch (error) {
    console.error('Error fetching cluster suggestions:', error);
    // Fallback: coba ambil dari pelanggan jika endpoint baru gagal
    try {
      const response = await apiClient.get('/pelanggan/', { params: { limit: 2000 } });
      const pelanggan = response.data.data || response.data;
      
      const clusters = new Set<string>();
      pelanggan.forEach((p: any) => {
        if (p.alamat && p.alamat.trim()) {
          clusters.add(p.alamat.trim());
        }
      });
      
      clusterSuggestions.value = Array.from(clusters).sort();
      console.log(`⚠️ Fallback: Loaded ${clusterSuggestions.value.length} clusters from pelanggan`);
    } catch (fallbackError) {
      console.error('Error in fallback cluster fetch:', fallbackError);
    }
  }
}

function openDialog(item?: Diskon) {
  if (item) {
    editedIndex.value = diskonList.value.indexOf(item);
    editedItem.value = { ...item };
  } else {
    editedIndex.value = -1;
    editedItem.value = { ...defaultItem };
  }
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  setTimeout(() => {
    editedItem.value = { ...defaultItem };
    editedIndex.value = -1;
    if (form.value) form.value.reset();
  }, 300);
}

async function saveItem() {
  if (!form.value.validate()) return;

  saving.value = true;
  try {
    const data = { ...editedItem.value };

    if (editedIndex.value > -1) {
      // Update existing
      await apiClient.put(`/diskon/${editedItem.value.id}`, data);
    } else {
      // Create new
      await apiClient.post('/diskon/', data);
    }

    await fetchDiskon();
    closeDialog();
  } catch (error) {
    console.error('Error saving diskon:', error);
  } finally {
    saving.value = false;
  }
}

function editItem(item: Diskon) {
  openDialog(item);
}

function openDeleteDialog(item: Diskon) {
  itemToDelete.value = item;
  deleteDialog.value = true;
}

function deleteItem(item: Diskon) {
  openDeleteDialog(item);
}

async function confirmDelete() {
  deleting.value = true;
  try {
    await apiClient.delete(`/diskon/${itemToDelete.value?.id}`);
    await fetchDiskon();
    deleteDialog.value = false;
  } catch (error) {
    console.error('Error deleting diskon:', error);
  } finally {
    deleting.value = false;
  }
}

async function toggleActive(item: Diskon) {
  try {
    const endpoint = item.is_active ? `/diskon/${item.id}` : `/diskon/${item.id}/activate`;
    if (item.is_active) {
      // Deactivate - update is_active to false
      await apiClient.put(endpoint, { is_active: false });
    } else {
      // Activate using activate endpoint
      await apiClient.post(endpoint);
    }
    await fetchDiskon();
  } catch (error) {
    console.error('Error toggling diskon status:', error);
  }
}

function formatDate(dateString: string) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

// Lifecycle
onMounted(() => {
  fetchDiskon();
  fetchClusterSuggestions();
});
</script>

<style scoped>
/* ========== Animations ========== */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

/* ========== Header Styles ========== */
.diskon-view {
  min-height: 100vh;
  background: linear-gradient(180deg, 
    rgba(103, 126, 234, 0.03) 0%, 
    rgba(118, 75, 162, 0.02) 100%
  );
}

.header-card {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 24px;
  padding: 32px;
  overflow: hidden;
  box-shadow: 
    0 20px 60px -12px rgba(103, 126, 234, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 25px 70px -15px rgba(103, 126, 234, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.15) inset;
}

.header-glass-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
  pointer-events: none;
}

.header-content {
  position: relative;
  z-index: 2;
}

.icon-wrapper {
  position: relative;
}

.header-avatar {
  background: rgba(255, 255, 255, 0.2) !important;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.header-avatar:hover {
  transform: scale(1.05) rotate(5deg);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.header-title {
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  letter-spacing: -0.5px;
}

.header-subtitle {
  opacity: 0.95;
  font-size: 1rem;
  font-weight: 500;
}

.add-btn {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2) !important;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* ========== Main Card Styles ========== */
.main-card {
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.main-card.dark-card {
  background: rgba(30, 30, 30, 0.95);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.3),
    0 1px 3px rgba(0, 0, 0, 0.2);
}

.card-header-wrapper {
  background: linear-gradient(135deg, 
    rgba(103, 126, 234, 0.08) 0%, 
    rgba(118, 75, 162, 0.06) 100%
  );
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.main-card.dark-card .card-header-wrapper {
  background: linear-gradient(135deg, 
    rgba(103, 126, 234, 0.15) 0%, 
    rgba(118, 75, 162, 0.12) 100%
  );
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.title-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(103, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.title-icon-wrapper:hover {
  background: rgba(103, 126, 234, 0.15);
  transform: rotate(5deg);
}

.counter-chip {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.counter-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* ========== Filter Section ========== */
.filter-section {
  background: rgba(0, 0, 0, 0.01);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.main-card.dark-card .filter-section {
  background: rgba(255, 255, 255, 0.02);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.search-field :deep(.v-field) {
  transition: all 0.3s ease;
}

.search-field :deep(.v-field:hover) {
  box-shadow: 0 2px 8px rgba(103, 126, 234, 0.15);
}

/* ========== Table Styles ========== */
.table-wrapper {
  overflow-x: auto;
}

.custom-table :deep(th) {
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.75rem;
  background: rgba(0, 0, 0, 0.02);
}

.main-card.dark-card .custom-table :deep(th) {
  background: rgba(255, 255, 255, 0.03);
}

.custom-table :deep(tr) {
  transition: all 0.2s ease;
}

.custom-table :deep(tbody tr:hover) {
  background: rgba(103, 126, 234, 0.05) !important;
}

.main-card.dark-card .custom-table :deep(tbody tr:hover) {
  background: rgba(103, 126, 234, 0.1) !important;
}

/* Table Cell Enhancements */
.discount-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  box-shadow: 0 4px 12px rgba(103, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.discount-avatar:hover {
  transform: scale(1.1) rotate(5deg);
}

.percentage-chip {
  font-size: 1rem !important;
  padding: 6px 14px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.percentage-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cluster-chip,
.status-chip {
  transition: all 0.3s ease;
}

.cluster-chip:hover,
.status-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.periode-info {
  min-width: 120px;
}

/* ========== Action Buttons ========== */
.action-buttons {
  gap: 6px;
  flex-wrap: nowrap;
}

.action-btn {
  border-radius: 10px !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* ========== Dialog Styles ========== */
.dialog-card {
  border-radius: 20px !important;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15) !important;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
}

.dialog-card.dark-card {
  background: rgba(30, 30, 30, 0.98);
}

.dialog-header {
  background: linear-gradient(135deg, 
    rgba(103, 126, 234, 0.08) 0%, 
    rgba(118, 75, 162, 0.06) 100%
  );
}

.dialog-card.dark-card .dialog-header {
  background: linear-gradient(135deg, 
    rgba(103, 126, 234, 0.15) 0%, 
    rgba(118, 75, 162, 0.12) 100%
  );
}

.delete-dialog .dialog-header {
  background: linear-gradient(135deg, 
    rgba(244, 67, 54, 0.08) 0%, 
    rgba(211, 47, 47, 0.06) 100%
  );
}

.dialog-card.dark-card.delete-dialog .dialog-header {
  background: linear-gradient(135deg, 
    rgba(244, 67, 54, 0.15) 0%, 
    rgba(211, 47, 47, 0.12) 100%
  );
}

/* ========== Utility Classes ========== */
.rounded-xl {
  border-radius: 16px !important;
}

/* ========== Mobile Responsive ========== */
@media (max-width: 960px) {
  .header-card {
    padding: 24px 20px;
    border-radius: 20px;
  }

  .header-title {
    font-size: 1.75rem !important;
  }

  .header-subtitle {
    font-size: 0.9rem;
  }

  .header-avatar {
    width: 56px !important;
    height: 56px !important;
  }

  .main-card {
    border-radius: 16px !important;
  }

  .table-wrapper {
    margin: 0 -16px;
  }

  .custom-table :deep(.v-data-table__td),
  .custom-table :deep(.v-data-table__th) {
    white-space: nowrap;
  }

  .action-buttons {
    justify-content: flex-end;
  }
}

@media (max-width: 600px) {
  .header-card {
    padding: 20px 16px;
    border-radius: 16px;
  }

  .header-title {
    font-size: 1.5rem !important;
  }

  .header-subtitle {
    font-size: 0.85rem;
  }

  .icon-wrapper {
    margin-right: 12px !important;
  }

  .header-avatar {
    width: 48px !important;
    height: 48px !important;
  }

  .card-header-wrapper {
    padding: 16px !important;
  }

  .filter-section {
    padding: 16px !important;
  }

  .action-btn {
    width: 32px !important;
    height: 32px !important;
  }
}

/* ========== Performance Optimizations ========== */
* {
  will-change: auto;
}

.header-card,
.main-card,
.action-btn,
.add-btn {
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
}
</style>
