<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <div class="d-flex align-center">
              <v-avatar class="me-4 elevation-4" color="gradient" size="80">
                <v-icon color="white" size="40">mdi-file-document-outline</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-2">Syarat & Ketentuan</h1>
                <p class="header-subtitle mb-0">
                  Informasi terkini tentang syarat ketentuan dan catatan rilis sistem
                </p>
              </div>
            </div>
            <v-spacer></v-spacer>
            <!-- Action buttons bisa ditambahkan di sini -->
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">

    <v-row class="mb-6 stats-section">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card stat-card-primary" elevation="0">
          <v-card-text class="pa-5">
            <div class="d-flex align-center">
              <div class="stat-icon-wrapper stat-icon-primary">
                <v-icon color="white" size="20">mdi-file-document</v-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ skItems.length }}</div>
                <div class="stat-label">Total Dokumen</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card stat-card-success" elevation="0">
          <v-card-text class="pa-5">
            <div class="d-flex align-center">
              <div class="stat-icon-wrapper stat-icon-success">
                <v-icon color="white" size="20">mdi-update</v-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ updateCount }}</div>
                <div class="stat-label">Pembaruan</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card stat-card-info" elevation="0">
          <v-card-text class="pa-5">
            <div class="d-flex align-center">
              <div class="stat-icon-wrapper stat-icon-info">
                <v-icon color="white" size="20">mdi-gavel</v-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ skCount }}</div>
                <div class="stat-label">S&K</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card stat-card-warning" elevation="0">
          <v-card-text class="pa-5">
            <div class="d-flex align-center">
              <div class="stat-icon-wrapper stat-icon-warning">
                <v-icon color="white" size="20">mdi-clock-outline</v-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ formatLastUpdate() }}</div>
                <div class="stat-label">Update Terakhir</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="search-card mb-6" elevation="0">
      <v-card-text class="pa-5">
        <v-row align="center" no-gutters>
          <v-col cols="12" md="8" class="pe-md-3 mb-4 mb-md-0">
            <v-text-field
              v-model="searchQuery"
              prepend-inner-icon="mdi-magnify"
              label="Cari dokumen..."
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              class="search-field"
              bg-color="transparent"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedType"
              :items="typeOptions"
              label="Filter berdasarkan tipe"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              class="filter-select"
              bg-color="transparent"
            ></v-select>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="main-content-card" elevation="0">
      <v-card-text class="pa-0">
        <div v-if="filteredItems.length > 0" class="documents-list">
          <div
            v-for="item in filteredItems"
            :key="item.id"
            class="document-item"
            :class="{ 'document-item-expanded': expandedItems.includes(item.id) }"
            @click="toggleExpansion(item.id)"
          >
            <div class="document-header">
              <div class="document-header-main">
                <v-chip 
                  size="small" 
                  :color="getChipColor(item.tipe)" 
                  variant="flat"
                  class="type-chip"
                >
                  <v-icon start size="16">{{ getChipIcon(item.tipe) }}</v-icon>
                  {{ item.tipe }}
                </v-chip>
                <h3 class="document-title">{{ item.judul }}</h3>
              </div>
              
              <div class="document-header-meta">
                <v-chip 
                  v-if="item.versi" 
                  size="x-small" 
                  variant="outlined" 
                  color="primary"
                  class="version-chip"
                >
                  v{{ item.versi }}
                </v-chip>
                <span class="date-text">{{ formatDateShort(item.created_at) }}</span>
                <v-btn
                  :icon="expandedItems.includes(item.id) ? 'mdi-chevron-up' : 'mdi-chevron-down'"
                  variant="text"
                  size="small"
                  class="expand-btn"
                ></v-btn>
              </div>
            </div>

            <v-expand-transition>
              <div v-if="expandedItems.includes(item.id)" class="document-content-wrapper">
                <v-divider class="mb-5"></v-divider>
                
                <div class="document-content" v-html="item.konten"></div>
                
                <div class="document-footer mt-5">
                  <div class="footer-info">
                    <div class="footer-item">
                      <v-icon size="16" class="me-2" color="medium-emphasis">mdi-calendar</v-icon>
                      <span class="footer-text">
                        Dipublikasikan pada {{ formatDate(item.created_at) }}
                      </span>
                    </div>
                    <v-chip 
                      size="small" 
                      :color="getStatusColor(item)" 
                      variant="tonal"
                      class="status-chip"
                    >
                      <v-icon start size="14">{{ getStatusIcon(item) }}</v-icon>
                      {{ getStatusText(item) }}
                    </v-chip>
                  </div>
                </div>
              </div>
            </v-expand-transition>
          </div>
        </div>

        <div v-else class="empty-state">
          <div class="empty-state-content">
            <div class="empty-icon-wrapper">
              <v-icon size="64" color="medium-emphasis">mdi-file-document-remove-outline</v-icon>
            </div>
            <h3 class="empty-title">Tidak ada dokumen ditemukan</h3>
            <p class="empty-subtitle">
              {{ searchQuery || selectedType ? 'Coba ubah kriteria pencarian Anda' : 'Belum ada dokumen S&K yang tersedia' }}
            </p>
          </div>
        </div>
      </v-card-text>
    </v-card>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
// import { useTheme } from 'vuetify'; // DIHAPUS: Tidak digunakan
import apiClient from '@/services/api';

interface SKItem {
  id: number;
  judul: string;
  konten: string;
  tipe: string;
  versi: string | null;
  created_at: string;
}

// State
// const theme = useTheme(); // DIHAPUS: Tidak digunakan
const skItems = ref<SKItem[]>([]);
const searchQuery = ref('');
const selectedType = ref<string | null>(null);
const expandedItems = ref<number[]>([]);

// Computed properties
const typeOptions = computed(() => {
  const types = [...new Set(skItems.value.map(item => item.tipe))];
  return types.map(type => ({ title: type, value: type }));
});

const filteredItems = computed(() => {
  let filtered = skItems.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(item => 
      item.judul.toLowerCase().includes(query) ||
      item.konten.toLowerCase().includes(query) ||
      item.tipe.toLowerCase().includes(query)
    );
  }

  if (selectedType.value) {
    filtered = filtered.filter(item => item.tipe === selectedType.value);
  }

  return filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
});

const updateCount = computed(() => 
  skItems.value.filter(item => item.tipe === 'Pembaruan').length
);

const skCount = computed(() => 
  skItems.value.filter(item => item.tipe !== 'Pembaruan').length
);

// Functions
async function fetchSK() {
  try {
    const response = await apiClient.get('/sk/');
    skItems.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data S&K:", error);
  }
}

function toggleExpansion(id: number) {
  const index = expandedItems.value.indexOf(id);
  if (index > -1) {
    expandedItems.value.splice(index, 1);
  } else {
    expandedItems.value.push(id);
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit', 
    month: 'long', 
    year: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit'
  });
}

function formatDateShort(dateString: string) {
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit', 
    month: 'short', 
    year: 'numeric'
  });
}

function formatLastUpdate() {
  if (skItems.value.length === 0) return '-';
  const latest = skItems.value.reduce((latest, item) => 
    new Date(item.created_at) > new Date(latest.created_at) ? item : latest
  );
  const days = Math.floor((new Date().getTime() - new Date(latest.created_at).getTime()) / (1000 * 60 * 60 * 24));
  return days === 0 ? 'Hari ini' : `${days} hari`;
}

function getChipColor(tipe: string) {
  switch (tipe) {
    case 'Pembaruan': return 'success';
    case 'Syarat & Ketentuan': return 'primary';
    case 'Kebijakan': return 'info';
    case 'Panduan': return 'warning';
    default: return 'grey';
  }
}

function getChipIcon(tipe: string) {
  switch (tipe) {
    case 'Pembaruan': return 'mdi-update';
    case 'Syarat & Ketentuan': return 'mdi-gavel';
    case 'Kebijakan': return 'mdi-shield-check';
    case 'Panduan': return 'mdi-book-open-variant';
    default: return 'mdi-file-document';
  }
}

function getStatusColor(item: SKItem) {
  const daysSinceCreated = Math.floor((new Date().getTime() - new Date(item.created_at).getTime()) / (1000 * 60 * 60 * 24));
  if (daysSinceCreated <= 7) return 'success';
  if (daysSinceCreated <= 30) return 'info';
  return 'grey';
}

function getStatusIcon(item: SKItem) {
  const daysSinceCreated = Math.floor((new Date().getTime() - new Date(item.created_at).getTime()) / (1000 * 60 * 60 * 24));
  if (daysSinceCreated <= 7) return 'mdi-new-box';
  if (daysSinceCreated <= 30) return 'mdi-clock-outline';
  return 'mdi-archive-outline';
}

function getStatusText(item: SKItem) {
  const daysSinceCreated = Math.floor((new Date().getTime() - new Date(item.created_at).getTime()) / (1000 * 60 * 60 * 24));
  if (daysSinceCreated <= 7) return 'Baru';
  if (daysSinceCreated <= 30) return 'Terkini';
  return 'Arsip';
}

onMounted(fetchSK);
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

/* Page Header */
.page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px; /* DIKURANGI: Sudut lebih tegas */
  padding: 24px; /* DIKURANGI: Padding lebih kecil */
  background: linear-gradient(135deg, 
    rgb(var(--v-theme-primary)) 0%, 
    rgb(var(--v-theme-secondary)) 100%
  );
  color: white;
  box-shadow: 0 8px 30px rgba(var(--v-theme-primary), 0.2); /* DIUBAH: Shadow lebih soft */
}

.header-decoration {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%); /* DIUBAH: Opacity lebih rendah */
  border-radius: 50%;
  pointer-events: none;
}

.header-content {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-icon-wrapper {
  width: 56px; /* DIKURANGI: Ikon header lebih kecil */
  height: 56px;
  border-radius: 14px; /* DIKURANGI */
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px; /* DIKURANGI */
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-text {
  flex: 1;
}

.page-title {
  font-size: 1.8rem; /* DIKURANGI: Ukuran judul utama lebih kecil */
  font-weight: 700; /* DIUBAH: Sedikit lebih tipis */
  margin-bottom: 4px; /* DIKURANGI */
  line-height: 1.2;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page-subtitle {
  font-size: 1rem; /* DIKURANGI */
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
  line-height: 1.4;
}

/* Stats Section */
.stats-section {
  margin-left: 0;
  margin-right: 0;
}

.stat-card {
  border-radius: 16px; /* DIKURANGI */
  border: 1px solid rgba(var(--v-border-color), 0.08);
  transition: all 0.3s ease; /* DIUBAH: Transisi lebih cepat */
  height: 100%;
  position: relative;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, 
    rgb(var(--v-theme-primary)), 
    rgb(var(--v-theme-secondary))
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px); /* DIKURANGI: Efek hover lebih halus */
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08); /* DIUBAH: Shadow lebih soft */
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-icon-wrapper {
  width: 48px; /* DIKURANGI: Ikon statistik lebih kecil */
  height: 48px;
  border-radius: 12px; /* DIKURANGI */
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px; /* DIKURANGI */
  flex-shrink: 0;
}


.stat-icon-primary { background: linear-gradient(135deg, rgb(var(--v-theme-primary)), rgb(var(--v-theme-primary-lighten-1))); }
.stat-icon-success { background: linear-gradient(135deg, rgb(var(--v-theme-success)), rgb(var(--v-theme-success-lighten-1))); }
.stat-icon-info { background: linear-gradient(135deg, rgb(var(--v-theme-info)), rgb(var(--v-theme-info-lighten-1))); }
.stat-icon-warning { background: linear-gradient(135deg, rgb(var(--v-theme-warning)), rgb(var(--v-theme-warning-lighten-1))); }



.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 1.75rem; /* DIKURANGI: Angka statistik lebih kecil */
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
  margin-bottom: 2px; /* DIKURANGI */
}

.stat-label {
  font-size: 0.75rem; /* DIKURANGI */
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-weight: 600; /* DITAMBAH: Agar lebih terbaca */
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
/* Search Card */
.search-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px; /* DIKURANGI */
  border: 1px solid rgba(var(--v-border-color), 0.08);
}

.search-field :deep(.v-field),
.filter-select :deep(.v-field) {
  border-radius: 12px; /* DIKURANGI */
  box-shadow: none; /* DIHAPUS: Agar lebih clean */
}

.filter-select :deep(.v-field) {
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* Main Content */
.main-content-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px; /* DIKURANGI */
  border: 1px solid rgba(var(--v-border-color), 0.08);
  overflow: hidden;
}



.documents-list {
  padding: 0;
}

.document-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.document-item:last-child {
  border-bottom: none;
}

.document-item:hover {
  background: rgba(var(--v-theme-primary), 0.02);
}

.document-item-expanded {
  background: rgba(var(--v-theme-primary), 0.02);
}

.document-header {
  padding: 16px 24px; /* DIKURANGI: Padding lebih ramping */
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px; /* DIKURANGI */
}

.document-item:last-child { border-bottom: none; }
.document-item:hover { background: rgba(var(--v-theme-primary), 0.02); }
.document-item-expanded { background: rgba(var(--v-theme-primary), 0.03); }

.document-header-main {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  gap: 16px;
}

.document-title {
  font-size: 1.1rem; /* DIKURANGI */
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.document-header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.type-chip {
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: 32px;
}

.version-chip {
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.75rem;
  height: 24px;
}

.date-text {
  font-size: 0.8rem; /* DIKURANGI */
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

.expand-btn {
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.3s ease;
}

.document-item:hover .expand-btn {
  color: rgb(var(--v-theme-primary));
}

.document-content-wrapper {
  padding: 0 24px 24px 24px; /* DIKURANGI */
}

.document-content {
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.7; /* DIUBAH */
  font-size: 0.95rem; /* DIUBAH */
}

.document-content :deep(h1),
.document-content :deep(h2),
.document-content :deep(h3),
.document-content :deep(h4),
.document-content :deep(h5),
.document-content :deep(h6) {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 700;
  margin-top: 2em;
  margin-bottom: 0.75em;
  line-height: 1.3;
}

.document-content :deep(h1) { font-size: 2rem; }
.document-content :deep(h2) { font-size: 1.75rem; }
.document-content :deep(h3) { font-size: 1.5rem; }
.document-content :deep(h4) { font-size: 1.25rem; }

.document-content :deep(p) {
  margin-bottom: 1.25em;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.document-content :deep(ul),
.document-content :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1.25em;
}

.document-content :deep(li) {
  margin-bottom: 0.75em;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.document-content :deep(strong) {
  color: rgb(var(--v-theme-primary));
  font-weight: 700;
}

.document-content :deep(code) {
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
}

.document-footer {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px; /* DIKURANGI */
  padding: 16px; /* DIKURANGI */
  border: 1px solid rgba(var(--v-border-color), 0.05);
}

.footer-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-item {
  display: flex;
  align-items: center;
}

.footer-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-weight: 500;
}

.status-chip {
  border-radius: 12px;
  font-weight: 600;
  height: 32px;
}

/* Empty State */
.empty-state {
  padding: 80px 24px;
  text-align: center;
}

.empty-state-content {
  max-width: 400px;
  margin: 0 auto;
}

.empty-icon-wrapper {
  margin-bottom: 24px;
  opacity: 0.6;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 12px;
}

.empty-subtitle {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.5;
  margin: 0;
}

/* Dark Theme Enhancements */
.v-theme--dark .sk-container {
  background: linear-gradient(180deg, 
    rgba(129, 140, 248, 0.05) 0%, 
    rgb(var(--v-theme-surface)) 20%
  );
}

.v-theme--dark .stat-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.6);
  backdrop-filter: blur(10px);
}

.v-theme--dark .stat-card:hover {
  background: rgba(30, 41, 59, 0.95);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .search-card,
.v-theme--dark .main-content-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.6);
  backdrop-filter: blur(10px);
}

.v-theme--dark .document-item {
  background: transparent;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
}

.v-theme--dark .document-item:hover,
.v-theme--dark .document-item-expanded {
  background: rgba(129, 140, 248, 0.08);
}

.v-theme--dark .document-footer {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.3);
}

.v-theme--dark .search-field :deep(.v-field),
.v-theme--dark .filter-select :deep(.v-field) {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.4);
}

/* Light Theme Specific */
.v-theme--light .stat-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.v-theme--light .search-card,
.v-theme--light .main-content-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.v-theme--light .document-footer {
  background: rgba(248, 250, 252, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

/* Mobile Responsiveness */
@media (max-width: 1024px) {
  .sk-container {
    padding: 12px;
  }
  
  .page-header {
    padding: 24px;
    border-radius: 20px;
  }
  
  .page-title {
    font-size: 2.25rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
}

@media (max-width: 768px) {
  .sk-container {
    padding: 8px;
  }
  
  .page-header {
    padding: 20px;
    border-radius: 16px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .header-icon-wrapper {
    margin-right: 0;
    margin-bottom: 20px;
    width: 64px;
    height: 64px;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .page-subtitle {
    font-size: 0.95rem;
  }
  
  .document-header {
    padding: 20px 24px;
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    min-height: auto;
  }
  
  .document-header-main {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .document-header-meta {
    width: 100%;
    justify-content: space-between;
  }
  
  .document-title {
    font-size: 1.1rem;
    line-height: 1.4;
  }
  
  .document-content-wrapper {
    padding: 0 24px 24px 24px;
  }
  
  .document-content {
    font-size: 0.95rem;
  }
  
  .stat-number {
    font-size: 1.75rem;
  }
  
  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
    margin-right: 16px;
  }
  
  .footer-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 600px) {
  .sk-container {
    padding: 4px;
  }
  
  .page-header {
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 20px;
  }
  
  .header-icon-wrapper {
    width: 56px;
    height: 56px;
    border-radius: 16px;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .page-subtitle {
    font-size: 0.9rem;
  }
  
  .search-card {
    border-radius: 16px;
  }
  
  .main-content-card {
    border-radius: 16px;
  }
  
  .stat-card {
    border-radius: 16px;
  }
  
  .document-header {
    padding: 16px 20px;
  }
  
  .document-content-wrapper {
    padding: 0 20px 20px 20px;
  }
  
  .document-footer {
    padding: 16px;
    border-radius: 12px;
  }
  
  .type-chip {
    height: 28px;
    font-size: 0.75rem;
  }
  
  .version-chip {
    height: 22px;
    font-size: 0.7rem;
  }
  
  .date-text {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 12px;
    margin-bottom: 16px;
  }
  
  .header-icon-wrapper {
    width: 48px;
    height: 48px;
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 0.85rem;
  }
  
  .document-header {
    padding: 12px 16px;
  }
  
  .document-content-wrapper {
    padding: 0 16px 16px 16px;
  }
  
  .document-content {
    font-size: 0.9rem;
    line-height: 1.6;
  }
  
  .stat-number {
    font-size: 1.5rem;
  }
  
  .stat-label {
    font-size: 0.8rem;
  }
  
  .stat-icon-wrapper {
    width: 44px;
    height: 44px;
    margin-right: 12px;
  }
  
  .search-card .v-card-text {
    padding: 16px;
  }
  
  .empty-state {
    padding: 60px 16px;
  }
  
  .empty-title {
    font-size: 1.25rem;
  }
  
  .empty-subtitle {
    font-size: 0.9rem;
  }
}

@media (max-width: 360px) {
  .sk-container {
    padding: 2px;
  }
  
  .page-header {
    padding: 8px;
    margin-bottom: 12px;
  }
  
  .header-icon-wrapper {
    width: 40px;
    height: 40px;
    margin-bottom: 12px;
  }
  
  .page-title {
    font-size: 1.25rem;
  }
  
  .page-subtitle {
    font-size: 0.8rem;
  }
  
  .document-header {
    padding: 8px 12px;
  }
  
  .document-content-wrapper {
    padding: 0 12px 12px 12px;
  }
  
  .document-content {
    font-size: 0.85rem;
  }
  
  .document-title {
    font-size: 1rem;
  }
  
  .type-chip {
    height: 26px;
    font-size: 0.7rem;
  }
  
  .stat-number {
    font-size: 1.25rem;
  }
  
  .stat-icon-wrapper {
    width: 40px;
    height: 40px;
    margin-right: 10px;
  }
  
  .search-card .v-card-text {
    padding: 12px;
  }
  
  .document-footer {
    padding: 12px;
    border-radius: 8px;
  }
}

/* Animation and Transitions */
.document-item {
  animation: slideInUp 0.4s ease-out;
  animation-fill-mode: both;
}

.document-item:nth-child(1) { animation-delay: 0.1s; }
.document-item:nth-child(2) { animation-delay: 0.2s; }
.document-item:nth-child(3) { animation-delay: 0.3s; }
.document-item:nth-child(4) { animation-delay: 0.4s; }
.document-item:nth-child(5) { animation-delay: 0.5s; }

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card {
  animation: fadeInScale 0.5s ease-out;
  animation-fill-mode: both;
}

.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Enhanced Focus States */
.search-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.filter-select :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

/* Scrollbar Enhancement */
.document-content-wrapper {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.3) transparent;
}

.document-content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.document-content-wrapper::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.document-content-wrapper::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
  transition: background 0.3s ease;
}

.document-content-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* Improved Button States */
.expand-btn:hover {
  background: rgba(var(--v-theme-primary), 0.1);
}

/* Enhanced Chip Styles */
.type-chip {
  position: relative;
  overflow: hidden;
}

.type-chip::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.type-chip:hover::before {
  left: 100%;
}

/* Loading Animation */
.documents-list {
  position: relative;
}

.documents-list::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgb(var(--v-theme-primary)), 
    transparent
  );
  transform: translateX(-100%);
  animation: loadingBar 2s ease-in-out infinite;
  z-index: 1;
}

@keyframes loadingBar {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(0%); }
  100% { transform: translateX(100%); }
}

/* Accessibility Improvements */
.document-item:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.expand-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

/* Print Styles */
@media print {
  .search-card,
  .stats-section,
  .expand-btn {
    display: none;
  }
  
  .document-item {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  
  .document-content-wrapper {
    display: block !important;
  }
  
  .page-header {
    background: none !important;
    color: black !important;
    box-shadow: none !important;
  }
}

/* High DPI Display Support */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .header-icon-wrapper,
  .stat-icon-wrapper {
    transform: translateZ(0);
    -webkit-font-smoothing: antialiased;
  }
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  .document-item,
  .stat-card,
  .search-card,
  .main-content-card {
    animation: none;
    transition: none;
  }
  
  .expand-btn,
  .type-chip,
  .status-chip {
    transition: none;
  }
}

/* Custom Selection Colors */
::selection {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-on-surface));
}

::-moz-selection {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-on-surface));
}
</style>