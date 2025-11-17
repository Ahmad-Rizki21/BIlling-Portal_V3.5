<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <div class="d-flex align-center">
              <v-avatar class="me-4 elevation-4" color="gradient" size="56">
                <v-icon color="white" size="28">mdi-tag-multiple</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-1">Brand & Paket Layanan</h1>
                <p class="header-subtitle mb-0">
                  Kelola brand provider dan paket yang ditawarkan dengan mudah
                </p>
              </div>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              color="white"
              size="large"
              elevation="4"
              @click="openBrandDialog()"
              prepend-icon="mdi-plus-circle"
              class="text-none font-weight-bold px-6"
              variant="elevated"
            >
              <span class="text-primary">Tambah Brand</span>
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">
      <!-- Brand Provider Card -->
        <v-card elevation="8" class="rounded-xl mb-6 overflow-hidden brand-provider-card">
        <div class="card-header">
          <v-card-title class="d-flex align-center pa-4 pa-sm-6">
            <v-icon color="primary" size="24" class="me-3">mdi-domain</v-icon>
            <span class="text-h6 font-weight-bold">Daftar Brand Provider</span>
            <v-spacer></v-spacer>
            <v-chip
              color="green"
              variant="elevated"
              size="small"
              prepend-icon="mdi-counter"
            >
              {{ brands.length }} Brand{{ brands.length !== 1 ? 's' : '' }}
            </v-chip>
          </v-card-title>
        </div>
        
        <v-data-table
          :headers="brandHeaders"
          :items="brands"
          :loading="brandLoading"
          item-value="id_brand"
          class="elevation-0 brand-table"
          @click:row="handleRowClick"
          :row-props="getRowProps"
          :loading-text="'Memuat data brand...'"
        >
          <template v-slot:loading>
            <SkeletonLoader type="table" :rows="5" />
          </template>

          <template v-slot:item.id_brand="{ item }">
            <v-chip
              color="blue-grey"
              variant="tonal"
              size="small"
              class="font-weight-bold"
            >
              {{ item.id_brand }}
            </v-chip>
          </template>

          <template v-slot:item.brand="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="32" color="primary" class="me-3">
                <span class="text-caption font-weight-bold">
                  {{ item.brand.substring(0, 2).toUpperCase() }}
                </span>
              </v-avatar>
              <span class="font-weight-medium">{{ item.brand }}</span>
            </div>
          </template>

          <template v-slot:item.pajak="{ item }">
            <v-chip
              :color="item.pajak > 10 ? 'orange' : 'green'"
              variant="tonal"
              size="small"
            >
              {{ item.pajak }}%
            </v-chip>
          </template>

          <template v-slot:item.xendit_key_name="{ item }">
            <v-chip
              color="purple"
              variant="outlined"
              size="small"
              prepend-icon="mdi-key"
            >
              {{ item.xendit_key_name }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="d-flex ga-2">
              <v-btn 
                size="small" 
                variant="tonal" 
                color="primary" 
                @click.stop="openBrandDialog(item)"
                icon="mdi-pencil"
                class="rounded-lg"
              ></v-btn>
              <v-btn 
                size="small" 
                variant="tonal" 
                color="error" 
                @click.stop="openDeleteBrandDialog(item)"
                icon="mdi-delete"
                class="rounded-lg"
              ></v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card>
      </div>

      <!-- Package Details Section -->
      <v-expand-transition>
        <div v-if="selectedBrand">
          <div class="content-wrapper">
            <v-card elevation="8" class="rounded-xl overflow-hidden package-details-card">
            <div class="package-header">
              <v-card-title class="d-flex align-center pa-6">
                <v-icon color="white" size="24" class="me-3">mdi-package-variant</v-icon>
                <div>
                  <span class="text-h6 font-weight-bold text-white">Paket Layanan untuk</span>
                  <v-chip color="white" class="ms-3 elevation-2" size="large">
                    <v-avatar start color="primary" size="24">
                      <span class="text-caption font-weight-bold text-white">
                        {{ selectedBrand.brand.substring(0, 2).toUpperCase() }}
                      </span>
                    </v-avatar>
                    <span class="font-weight-bold text-white">{{ selectedBrand.brand }}</span>
                  </v-chip>
                </div>
                <v-spacer></v-spacer>
                <v-btn 
                  color="white" 
                  variant="elevated"
                  @click="openPackageDialog()"
                  prepend-icon="mdi-plus-circle"
                  class="text-none font-weight-bold px-4"
                  elevation="4"
                >
                  <span class="text-primary">Tambah Paket</span>
                </v-btn>
              </v-card-title>
            </div>
            
            <v-data-table
              :headers="packageHeaders"
              :items="filteredPackages"
              :loading="packageLoading"
              item-value="id"
              class="elevation-0 package-table"
              :loading-text="'Memuat data paket...'"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@3"></v-skeleton-loader>
              </template>

              <template v-slot:item.nama_paket="{ item }">
                <div class="d-flex align-center">
                  <v-icon color="primary" class="me-2">mdi-wifi</v-icon>
                  <span class="font-weight-medium">{{ item.nama_paket }}</span>
                </div>
              </template>

              <template v-slot:item.kecepatan="{ item }">
                <v-chip
                  color="blue"
                  variant="tonal"
                  size="small"
                  prepend-icon="mdi-speedometer"
                >
                  {{ item.kecepatan }} Mbps
                </v-chip>
              </template>

              <template v-slot:item.harga="{ item }">
                <div class="text-end">
                  <span class="text-h6 font-weight-bold text-green-darken-2">
                    {{ formatCurrency(item.harga) }}
                  </span>
                  <div class="text-caption text-medium-emphasis">per bulan</div>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="d-flex ga-2">
                  <v-btn 
                    size="small" 
                    variant="tonal" 
                    color="primary" 
                    @click="openPackageDialog(item)"
                    icon="mdi-pencil"
                    class="rounded-lg"
                  ></v-btn>
                  <v-btn 
                    size="small" 
                    variant="tonal" 
                    color="error" 
                    @click="openDeletePackageDialog(item)"
                    icon="mdi-delete"
                    class="rounded-lg"
                  ></v-btn>
                </div>
              </template>

              <template v-slot:no-data>
                <div class="text-center pa-8 no-data-section">
                  <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-package-variant-closed</v-icon>
                  <div class="text-h6 text-medium-emphasis mb-2">Belum ada paket layanan</div>
                  <div class="text-body-2 text-medium-emphasis">
                    Klik tombol "Tambah Paket" untuk menambahkan paket baru
                  </div>
                </div>
              </template>
            </v-data-table>
          </v-card>
          </div>
        </div>
      </v-expand-transition>

      <!-- Empty State for Brand Selection -->
      <div class="content-wrapper">
        <v-card
          v-if="!selectedBrand && brands.length > 0"
          elevation="4"
          class="rounded-xl pa-8 text-center mt-8 empty-state-card"
      >
        <v-icon size="80" color="grey-lighten-1" class="mb-4">mdi-mouse-left-click</v-icon>
        <div class="text-h6 text-medium-emphasis mb-2">Pilih Brand untuk Melihat Paket</div>
        <div class="text-body-2 text-medium-emphasis">
          Klik salah satu brand di tabel atas untuk melihat paket layanan yang tersedia
        </div>
      </v-card>
    </div>

    <HargaLayananDialog v-model="dialogBrand" :edited-item="editedBrand" @save="saveBrand" />
    <PaketLayananDialog v-model="dialogPackage" :edited-item="editedPackage" :brand-id="selectedBrand?.id_brand" @save="savePackage" />
  </v-container>
</template>

<script setup lang="ts">
// Import library Vue yang dibutuhin buat komponen reaktif
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';  // API client buat komunikasi sama backend
import type { HargaLayanan, PaketLayanan } from '@/interfaces/layanan';

// Import komponen dialog buat form input
import HargaLayananDialog from '@/components/dialogs/HargaLayananDialog.vue';
import PaketLayananDialog from '@/components/dialogs/PaketLayananDialog.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

// ===== STATE MANAGEMENT =====
// Data arrays buat nyimpan brand dan paket dari API
const brands = ref<HargaLayanan[]>([]);      // Data semua brand provider
const packages = ref<PaketLayanan[]>([]);   // Data semua paket layanan

// Loading states buat indikator loading
const brandLoading = ref(true);     // Loading pas fetch data brand
const packageLoading = ref(true);   // Loading pas fetch data paket

// Selected brand buat filter paket
const selectedBrand = ref<HargaLayanan | null>(null);

// ===== DIALOG STATE MANAGEMENT =====
// Kontrol visibility dialog buat masing-masing form
const dialogBrand = ref(false);     // Dialog buat input brand
const dialogPackage = ref(false);   // Dialog buat input paket

// Data buat form edit (bisa kosong atau ada data yang diedit)
const editedBrand = ref<Partial<HargaLayanan>>({});     // Data brand yang lagi diedit
const editedPackage = ref<Partial<PaketLayanan>>({});   // Data paket yang lagi diedit

// Index buat tracking item yang lagi diedit di array
let editedBrandIndex = -1;      // Index brand yang diedit
let editedPackageIndex = -1;    // Index paket yang diedit

// ===== TABLE HEADERS CONFIGURATION =====
// Konfigurasi kolom buat tabel brand provider
const brandHeaders = [
  { title: 'ID Brand', key: 'id_brand', width: '15%' },           // ID unik brand
  { title: 'Nama Brand', key: 'brand', width: '30%' },            // Nama brand provider
  { title: 'Pajak', key: 'pajak', align: 'center' as const, width: '15%' },    // Persentase pajak
  { title: 'Key Xendit', key: 'xendit_key_name', width: '25%' },  // Nama key payment gateway
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' as const, width: '15%' },  // Kolom aksi
];

// Konfigurasi kolom buat tabel paket layanan
const packageHeaders = [
  { title: 'Nama Paket', key: 'nama_paket', width: '40%' },        // Nama paket internet
  { title: 'Kecepatan', key: 'kecepatan', align: 'center' as const, width: '20%' },  // Kecepatan internet
  { title: 'Harga', key: 'harga', align: 'end' as const, width: '25%' },            // Harga paket
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' as const, width: '15%' },  // Kolom aksi
];

// ===== COMPUTED PROPERTIES =====
// Filter paket berdasarkan brand yang dipilih
const filteredPackages = computed(() => {
  if (!selectedBrand.value) return [];  // Kalo belum ada brand yang dipilih, return kosong
  return packages.value.filter((p: PaketLayanan) => p.id_brand === selectedBrand.value!.id_brand);
});

// ===== LIFECYCLE HOOKS =====
// Jalankan fungsi-fungsi ini pas komponen pertama kali dimuat
onMounted(() => {
  fetchBrands();   // Ambil data brand dari API
  fetchPackages(); // Ambil data paket dari API
});
async function fetchBrands() {
  brandLoading.value = true;
  try {
    const response = await apiClient.get<HargaLayanan[]>('/harga_layanan/');
    brands.value = response.data.map(brand => ({
      ...brand,
      id_brand: brand.id_brand.trim()
    }));
  } finally {
    brandLoading.value = false;
  }
}

async function fetchPackages() {
  packageLoading.value = true;
  try {
    const response = await apiClient.get<PaketLayanan[]>('/paket_layanan/');
    packages.value = response.data;
  } finally {
    packageLoading.value = false;
  }
}

// Brand Dialog Logic
function openBrandDialog(item?: HargaLayanan) {
  editedBrandIndex = item ? brands.value.findIndex(b => b.id_brand === item.id_brand) : -1;
  editedBrand.value = item ? { ...item } : { pajak: 11.0 };
  dialogBrand.value = true;
}

async function saveBrand(item: HargaLayanan) {
  if (editedBrandIndex > -1) {
    await apiClient.patch(`/harga_layanan/${item.id_brand}`, item);
  } else {
    await apiClient.post('/harga_layanan/', item);
  }
  fetchBrands();
}

// Package Dialog Logic
function openPackageDialog(item?: PaketLayanan) {
  editedPackageIndex = item ? packages.value.findIndex(p => p.id === item.id) : -1;
  editedPackage.value = item ? { ...item } : {};
  dialogPackage.value = true;
}

async function savePackage(item: PaketLayanan) {
  if (editedPackageIndex > -1) {
    await apiClient.patch(`/paket_layanan/${item.id}`, item);
  } else {
    item.id_brand = selectedBrand.value!.id_brand.trim();
    await apiClient.post('/paket_layanan/', item);
  }
  fetchPackages();
}

// Row Click & Styling
function handleRowClick(_event: Event, { item }: { item: HargaLayanan }) {
  if (selectedBrand.value && selectedBrand.value.id_brand === item.id_brand) {
    selectedBrand.value = null;
  } else {
    selectedBrand.value = item;
  }
}

function getRowProps({ item }: { item: HargaLayanan }) {
  return {
    class: selectedBrand.value?.id_brand === item.id_brand ? 'selected-row' : '',
    style: 'cursor: pointer;'
  };
}

// --- Helper Functions ---
function formatCurrency(value: number) {
  if(isNaN(value)) return "Rp 0";
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value);
}

// Delete Functions
async function deleteBrand(id_brand: string) {
  try {
    await apiClient.delete(`/harga_layanan/${id_brand}`);
    fetchBrands(); // Refresh brands
    fetchPackages(); // Refresh packages
    // Clear selection if deleted brand was selected
    if (selectedBrand.value && selectedBrand.value.id_brand === id_brand) {
      selectedBrand.value = null;
    }
  } catch (error) {
    console.error('Error deleting brand:', error);
    alert('Gagal menghapus brand. Pastikan tidak ada pelanggan yang menggunakan brand ini.');
  }
}

function openDeleteBrandDialog(item: HargaLayanan) {
  if (confirm(`Apakah Anda yakin ingin menghapus brand "${item.brand}"? Semua paket layanan terkait juga akan terhapus.`)) {
    deleteBrand(item.id_brand);
  }
}
async function deletePackage(paketId: number) {
  try {
    await apiClient.delete(`/paket_layanan/${paketId}`);
    fetchPackages(); // Refresh packages
  } catch (error) {
    console.error('Error deleting package:', error);
    alert('Gagal menghapus paket. Pastikan tidak ada pelanggan yang menggunakan paket ini.');
  }
}

function openDeletePackageDialog(item: PaketLayanan) {
  if (confirm(`Apakah Anda yakin ingin menghapus paket "${item.nama_paket}"?`)) {
    deletePackage(item.id!);
  }
}
</script>

<style scoped>
/* ========== LIGHT MODE STYLES ========== */

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

.content-wrapper {
  margin: 0;
  width: 100%;
}

/* Maximize card width */
.brand-provider-card {
  width: 100%;
}

.brand-provider-card :deep(.v-card-text) {
  padding: 0 !important;
}

/* Header styling */
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

/* Card styling */
.brand-provider-card,
.package-details-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Card headers - Light Mode */
.card-header {
  background: linear-gradient(135deg, rgba(0, 105, 92, 0.05) 0%, rgba(38, 166, 154, 0.03) 100%);
  border-bottom: 1px solid rgba(0, 105, 92, 0.1);
  transition: all 0.3s ease;
}

.package-header {
  background: linear-gradient(135deg, #00695c 0%, #00897b 100%);
}

/* Empty state card styling */
.empty-state-card {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  transition: all 0.3s ease;
}

.no-data-section {
  background: transparent;
  transition: all 0.3s ease;
}

/* Table styling - Light Mode */
.brand-table :deep(.v-data-table__td) {
  padding: 12px 6px !important;
}

.brand-table :deep(.v-data-table__th) {
  padding: 12px 6px !important;
}

.brand-table :deep(.v-data-table__wrapper) {
  padding: 0 !important;
}

.brand-table :deep(.v-data-table__table) {
  width: 100% !important;
}

.brand-table :deep(tbody tr) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgb(var(--v-theme-surface));
}

.brand-table :deep(tbody tr:hover) {
  background-color: rgba(0, 105, 92, 0.04) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 105, 92, 0.1);
}

.brand-table :deep(tbody tr.selected-row) {
  background: linear-gradient(135deg, rgba(0, 105, 92, 0.1) 0%, rgba(38, 166, 154, 0.1) 100%) !important;
  border-left: 4px solid #00695c;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 105, 92, 0.15);
}

.package-table :deep(tbody tr) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgb(var(--v-theme-surface));
}

.package-table :deep(tbody tr:hover) {
  background-color: rgba(0, 105, 92, 0.04) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 105, 92, 0.1);
}

/* Button and chip transitions */
.v-btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.v-btn:hover {
  transform: translateY(-2px);
}

.v-chip {
  transition: all 0.3s ease;
}

/* Loading animation */
.v-skeleton-loader {
  background: linear-gradient(
    90deg, 
    rgba(var(--v-theme-on-surface), 0.04) 25%, 
    rgba(var(--v-theme-on-surface), 0.08) 50%, 
    rgba(var(--v-theme-on-surface), 0.04) 75%
  );
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ========== DARK MODE STYLES ========== */

/* Dark mode card adjustments */
.v-theme--dark .brand-provider-card,
.v-theme--dark .package-details-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

/* Dark mode card headers */
.v-theme--dark .card-header {
  background: linear-gradient(
    135deg, 
    rgba(var(--v-theme-on-surface), 0.08) 0%, 
    rgba(var(--v-theme-on-surface), 0.04) 100%
  );
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.v-theme--dark .card-header .v-card-title,
.v-theme--dark .card-header .v-icon {
  color: rgb(var(--v-theme-on-surface));
}

/* Dark mode empty state */
.v-theme--dark .empty-state-card {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.3);
}

.v-theme--dark .no-data-section .v-icon {
  color: rgba(var(--v-theme-on-surface), 0.6) !important;
}

/* Dark mode table styling */
.v-theme--dark .brand-table :deep(tbody tr) {
  background: rgb(var(--v-theme-surface));
}

.v-theme--dark .brand-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .brand-table :deep(tbody tr.selected-row) {
  background: linear-gradient(
    135deg, 
    rgba(38, 166, 154, 0.15) 0%, 
    rgba(38, 166, 154, 0.2) 100%
  ) !important;
  border-left: 4px solid #26a69a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}

.v-theme--dark .package-table :deep(tbody tr) {
  background: rgb(var(--v-theme-surface));
}

.v-theme--dark .package-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Dark mode skeleton loader */
.v-theme--dark .v-skeleton-loader {
  background: linear-gradient(
    90deg, 
    rgba(var(--v-theme-on-surface), 0.08) 25%, 
    rgba(var(--v-theme-on-surface), 0.12) 50%, 
    rgba(var(--v-theme-on-surface), 0.08) 75%
  );
}

/* Dark mode text adjustments */
.v-theme--dark .text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.7) !important;
}

.v-theme--dark .empty-state-card .text-h6,
.v-theme--dark .empty-state-card .text-body-2 {
  color: rgba(var(--v-theme-on-surface), 0.8) !important;
}

/* ========== RESPONSIVE DESIGN ========== */

@media (max-width: 960px) {
  .header-section .v-container {
    padding: 1rem !important;
  }
  
  .header-section .d-flex {
    flex-direction: column;
    gap: 1rem;
  }
  
  .v-card .pa-6 {
    padding: 1rem !important;
  }
  
  .brand-table,
  .package-table {
    font-size: 0.875rem;
  }
}

@media (max-width: 600px) {
  .header-section h1 {
    font-size: 1.5rem !important;
  }
  
  .header-subtitle {
    font-size: 0.875rem !important;
  }
  
  .v-card .pa-6 {
    padding: 0.75rem !important;
  }
  
  .d-flex.ga-2 {
    gap: 0.25rem !important;
  }
  
  .v-btn[size="small"] {
    min-width: 32px !important;
    width: 32px !important;
    height: 32px !important;
  }
}

/* ========== ACCESSIBILITY IMPROVEMENTS ========== */

/* Focus states */
.v-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.brand-table :deep(tbody tr):focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .card-header {
    border-bottom-width: 2px;
  }
  
  .empty-state-card {
    border-width: 3px;
  }
  
  .brand-table :deep(tbody tr.selected-row) {
    border-left-width: 6px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .v-btn,
  .v-chip,
  .brand-table :deep(tbody tr),
  .package-table :deep(tbody tr) {
    transition: none;
  }
  
  .v-skeleton-loader {
    animation: none;
  }
  
  .v-btn:hover {
    transform: none;
  }
  
  .brand-table :deep(tbody tr:hover),
  .package-table :deep(tbody tr:hover) {
    transform: none;
  }
}
</style>