<template>
  <v-container fluid class="pa-sm-6 pa-4">
    <div class="d-flex align-center mb-6 page-header">
      <div class="d-flex align-center">
        <v-avatar class="me-3" color="primary" size="40">
          <v-icon color="white">mdi-wifi-star</v-icon>
        </v-avatar>
        <div>
          <h1 class="text-h4 font-weight-bold text-primary">Manajemen Langganan</h1>
          <p class="text-subtitle-1 text-medium-emphasis mb-0">Kelola semua langganan pelanggan</p>
        </div>
      </div>
      <v-spacer class="d-none d-md-block"></v-spacer>
      
      <!-- Enhanced Action Buttons -->
      <div class="header-actions">
        <v-btn 
          class="import-btn" 
          @click="dialogImport = true" 
          prepend-icon="mdi-file-upload-outline"
          size="default"
        >
          Import
        </v-btn>
        <v-btn 
          class="export-btn" 
          @click="exportLangganan" 
          prepend-icon="mdi-file-download-outline"
          size="default"
        >
          Export
        </v-btn>
        <v-btn 
          class="add-subscription-btn"
          size="default"
          @click="openDialog()"
          prepend-icon="mdi-plus-circle"
        >
          Tambah Langganan
        </v-btn>
      </div> 
    </div>
        <v-dialog v-model="dialogImport" max-width="600px" persistent>
      <v-card class="import-dialog">
        <v-card-title class="import-dialog-header">Import Langganan</v-card-title>
        <v-card-text class="import-dialog-content">
          <v-alert 
            type="info" 
            variant="tonal" 
            class="import-info-alert"
          >
            Gunakan <strong>Email Pelanggan</strong> dan <strong>Nama Paket Layanan</strong> sebagai kunci pencocokan.
            <a :href="`${apiClient.defaults.baseURL}/langganan/template/csv`" download>Unduh template di sini</a>.
          </v-alert>
          
          <v-alert 
            v-if="importErrors.length" 
            type="error" 
            closable 
            @update:model-value="importErrors = []"
            class="import-error-alert"
          >
            <ul>
              <li v-for="(err, i) in importErrors" :key="i">{{ err }}</li>
            </ul>
          </v-alert>
          
          <v-file-input
            :model-value="fileToImport"
            @update:model-value="handleFileSelection"
            label="Pilih file CSV"
            accept=".csv"
            variant="outlined"
            class="import-file-input"
          ></v-file-input>
        </v-card-text>
        <v-card-actions class="import-dialog-actions">
          <v-spacer></v-spacer>
          <v-btn class="import-cancel-btn" @click="closeImportDialog">Batal</v-btn>
          <v-btn 
            class="import-upload-btn" 
            @click="importFromCsv" 
            :loading="importing" 
            :disabled="!fileToImport.length"
          >
            Unggah
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

        <v-card class="filter-card mb-4" elevation="1" rounded="lg">
      <v-card-text class="pa-3">
        <v-row dense>
          <v-col cols="12" md="4">
            <v-text-field
              :density="fieldDensity"
              v-model="searchQuery"
              label="Cari Nama Pelanggan"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              hide-details
              clearable
              class="compact-field"
            ></v-text-field>
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="selectedPaket"
              :items="paketLayananSelectList"
              item-title="nama_paket"
              item-value="id"
              label="Filter Paket Layanan"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="compact-field"
            ></v-select>
          </v-col>

          <v-col cols="12" md="3">
            <v-select
              v-model="selectedStatus"
              :items="statusOptions"
              label="Filter Status"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="compact-field"
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="2" class="d-flex align-center">
            <v-btn
              variant="text"
              color="primary"
              @click="resetFilters"
              class="reset-filter-btn"
              size="small"
            >
              <v-icon start size="16">mdi-refresh</v-icon>
              Reset
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card elevation="3" class="rounded-lg">
      <v-card-title class="d-flex align-center pa-4 pa-sm-6 bg-grey-lighten-5">
        <v-icon start icon="mdi-format-list-bulleted-square" color="primary"></v-icon>
        <span class="text-h6 font-weight-bold">Daftar Langganan</span>
        <v-spacer></v-spacer>
        <v-chip color="primary" variant="outlined" size="small">
          {{ langgananList.length }} langganan
        </v-chip>
      </v-card-title>

      <v-expand-transition>
        <div v-if="selectedLangganan.length > 0" class="selection-toolbar pa-4">
          <span class="font-weight-bold text-primary">{{ selectedLangganan.length }} langganan terpilih</span>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete-sweep"
            @click="dialogBulkDelete = true"
          >
            Hapus Terpilih
          </v-btn>
        </div>
      </v-expand-transition>
      
      <div class="table-responsive-wrapper">
        <v-data-table
          v-model="selectedLangganan"
          :headers="headers"
          :items="langgananList"
          :loading="loading"
          item-value="id"
          class="elevation-0"
          :items-per-page="10"
          show-select
          return-object
        >

          <template v-slot:item.nomor="{ index }: { index: number }">
            {{ index + 1 }}
          </template>

          <template v-slot:item.pelanggan_id="{ item }: { item: Langganan }">
            <div class="font-weight-bold">{{ getPelangganName(item.pelanggan_id) }}</div>
            <div class="text-caption text-medium-emphasis">ID: {{ item.pelanggan_id }}</div>
          </template>

          <template v-slot:item.pelanggan.alamat="{ item }: { item: Langganan }">
            <div class="text-caption" style="max-width: 200px; white-space: normal;">
              {{ item.pelanggan.alamat }}
            </div>
          </template>

          <template v-slot:item.paket_layanan_id="{ item }: { item: Langganan }">
            <div class="font-weight-medium">{{ getPaketName(item.paket_layanan_id) }}</div>
          </template>
          
          <template v-slot:item.metode_pembayaran="{ item }: { item: Langganan }">
            <v-chip
              size="small"
              variant="tonal"
              :color="item.metode_pembayaran === 'Prorate' ? 'blue' : 'grey-darken-1'"
            >
              {{ item.metode_pembayaran }}
            </v-chip>
          </template>

          <template v-slot:item.harga_awal="{ item }: { item: Langganan }">
            <div class="font-weight-bold text-right">
              {{ formatCurrency(item.harga_awal) }}
            </div>
          </template>

          <template v-slot:item.harga_final="{ item }"> <div class="font-weight-bold text-right">
              {{ formatCurrency(item.harga_final) }} </div>
          </template>

          <template v-slot:item.status="{ item }: { item: Langganan }">
            <v-chip
              size="small"
              :color="getStatusColor(item.status)"
              class="font-weight-bold"
            >
              {{ item.status }}
            </v-chip>
          </template>
          
          <template v-slot:item.tgl_jatuh_tempo="{ item }: { item: Langganan }">
              {{ formatDate(item.tgl_jatuh_tempo) }}
          </template>

          <template v-slot:item.actions="{ item }: { item: Langganan }">
            <div class="d-flex justify-center ga-2">
              <v-btn size="small" variant="tonal" color="primary" @click="openDialog(item)">
                <v-icon start size="16">mdi-pencil</v-icon> Edit
              </v-btn>
              <v-btn size="small" variant="tonal" color="error" @click="openDeleteDialog(item)">
                <v-icon start size="16">mdi-delete</v-icon> Hapus
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </div>
    </v-card>

<v-dialog v-model="dialog" max-width="800px" persistent scrollable>
  <v-card class="subscription-modal">
    <!-- Simplified Header -->
    <v-card-title class="modal-header">
      <div class="header-content">
        <v-icon color="white" size="24" class="me-3">
          {{ editedIndex === -1 ? 'mdi-plus-circle' : 'mdi-pencil' }}
        </v-icon>
        <div>
          <h3 class="header-title">{{ formTitle }}</h3>
          <p class="header-subtitle">
            {{ editedIndex === -1 ? 'Tambahkan langganan baru untuk pelanggan' : 'Perbarui informasi langganan' }}
          </p>
        </div>
      </div>
    </v-card-title>

    <!-- Form Content -->
    <v-card-text class="modal-content">
      <v-form ref="formRef" v-model="formValid" lazy-validation>
        <!-- Customer Selection -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-account</v-icon>
            Informasi Pelanggan
          </h4>
          <v-autocomplete
            v-model="editedItem.pelanggan_id"
            :items="dropdownPelangganSource"
            item-title="nama"
            item-value="id"
            label="Pilih Pelanggan"
            placeholder="Ketik nama pelanggan untuk mencari..."
            variant="outlined"
            prepend-inner-icon="mdi-account-search"
            :rules="[rules.required]"
            :disabled="editedIndex !== -1"
            density="comfortable"
            clearable
            hide-details="auto"
            class="mb-4"
          >
            <template v-slot:item="{ props, item }">
              <v-list-item v-bind="props" class="px-4">
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32">
                    <v-icon color="white" size="16">mdi-account</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">
                  {{ item.raw.nama }}
                  <v-chip
                    v-if="item.raw.id === newPelangganIdMarker"
                    size="x-small"
                    color="success"
                    variant="elevated"
                    class="ms-2"
                  >
                    NEW
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>ID: {{ item.raw.id }}</v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-autocomplete>
        </div>

        <!-- Package and Payment -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-wifi</v-icon>
            Paket & Pembayaran
          </h4>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="editedItem.paket_layanan_id"
                :items="filteredPaketLayanan"
                :loading="paketLoading"
                item-title="nama_paket"
                item-value="id"
                label="Pilih Paket Layanan"
                :disabled="!editedItem.pelanggan_id || isPaketLocked"
                placeholder="Pilih pelanggan terlebih dahulu"
                variant="outlined"
                prepend-inner-icon="mdi-wifi-star"
                :rules="[rules.required]"
                density="comfortable"
                hide-details="auto"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props" class="px-4">
                    <template v-slot:prepend>
                      <v-avatar color="indigo" size="32">
                        <v-icon color="white" size="16">mdi-wifi</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-medium">{{ item.raw.nama_paket }}</v-list-item-title>
                    <v-list-item-subtitle>{{ item.raw.kecepatan }} Mbps - {{ formatCurrency(item.raw.harga) }}</v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-select
                v-model="editedItem.metode_pembayaran"
                :items="[
                  { title: 'Otomatis (Bulanan)', value: 'Otomatis' }, 
                  { title: 'Prorate (Proporsional)', value: 'Prorate' }
                ]"
                label="Metode Pembayaran"
                variant="outlined"
                prepend-inner-icon="mdi-cash-multiple"
                density="comfortable"
                hide-details="auto"
              ></v-select>
            </v-col>
          </v-row>

          <!-- Pricing Display -->
          <div v-if="editedItem.metode_pembayaran === 'Otomatis'" class="mt-4">
            <v-text-field
              :model-value="editedItem.harga_awal"
              label="Total Harga Bulanan"
              variant="outlined"
              prepend-inner-icon="mdi-currency-usd"
              prefix="Rp"
              readonly
              density="comfortable"
              class="price-field"
            ></v-text-field>
          </div>

          <!-- Prorate Options -->
          <template v-if="editedItem.metode_pembayaran === 'Prorate'">
            <v-row class="mt-2">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedItem.tgl_mulai_langganan"
                  label="Tanggal Mulai Langganan"
                  type="date"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-start"
                  density="comfortable"
                  hide-details="auto"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6" class="d-flex align-center">
                <v-switch
                  v-model="isProratePlusFull"
                  color="primary"
                  label="Sertakan tagihan penuh bulan depan"
                  inset
                  hide-details
                  density="comfortable"
                ></v-switch>
              </v-col>
            </v-row>

            <!-- Prorate Pricing Info -->
            <div class="mt-4">
              <v-alert
                v-if="isProratePlusFull && hargaProrate > 0"
                variant="tonal"
                color="info"
                icon="mdi-information-outline"
                density="compact"
                class="mb-4"
              >
                <div class="text-body-2">
                  <strong>Rincian Tagihan Pertama:</strong>
                  <div class="ms-2 mt-1">
                    • Biaya Prorate: {{ formatCurrency(hargaProrate) }}<br>
                    • Biaya Bulan Depan: {{ formatCurrency(hargaNormal) }}
                  </div>
                </div>
              </v-alert>

              <v-text-field
                :model-value="editedItem.harga_awal"
                :label="isProratePlusFull ? 'Total Tagihan Pertama' : 'Total Harga Prorate'"
                variant="outlined"
                prepend-inner-icon="mdi-currency-usd-circle"
                prefix="Rp"
                readonly
                density="comfortable"
                class="price-field"
              ></v-text-field>
            </div>
          </template>
        </div>

        <!-- Status and Schedule -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-cog</v-icon>
            Status & Jadwal
          </h4>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="editedItem.status"
                :items="[
                  { title: 'Aktif', value: 'Aktif' },
                  { title: 'Suspended', value: 'Suspended' },
                  { title: 'Berhenti', value: 'Berhenti' }
                ]"
                label="Status Langganan"
                variant="outlined"
                prepend-inner-icon="mdi-check-circle-outline"
                :rules="[rules.required]"
                density="comfortable"
                hide-details="auto"
              ></v-select>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                v-model="editedItem.tgl_jatuh_tempo"
                label="Tanggal Jatuh Tempo"
                type="date"
                variant="outlined"
                prepend-inner-icon="mdi-calendar-alert"
                density="comfortable"
                hide-details="auto"
              ></v-text-field>
            </v-col>
          </v-row>
        </div>
      </v-form>
    </v-card-text>

    <!-- Action Buttons -->
    <v-card-actions class="modal-actions">
      <v-spacer></v-spacer>
      <v-btn
        variant="text"
        color="grey-darken-1"
        @click="closeDialog"
        class="text-none"
      >
        Batal
      </v-btn>
      <v-btn
        color="primary"
        variant="flat"
        @click="saveLangganan"
        :loading="saving"
        :disabled="!isFormValid"
        class="text-none"
      >
        <v-icon start size="18">{{ editedIndex === -1 ? 'mdi-plus' : 'mdi-content-save' }}</v-icon>
        {{ editedIndex === -1 ? 'Tambah Langganan' : 'Simpan Perubahan' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
    <!-- Enhanced Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="rounded-xl elevation-8">
        <div class="delete-header text-center pa-8">
          <v-avatar size="64" color="error" class="mb-4">
            <v-icon size="32" color="white">mdi-delete-alert</v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold text-error mb-2">Konfirmasi Hapus</h2>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Apakah Anda yakin ingin menghapus langganan untuk pelanggan 
            <strong class="text-primary">{{ getPelangganName(itemToDelete?.pelanggan_id) }}</strong>?
          </p>
          <v-alert variant="tonal" color="warning" class="mt-4 text-start">
            <v-icon start>mdi-alert-triangle</v-icon>
            Tindakan ini tidak dapat dibatalkan
          </v-alert>
        </div>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1" 
            @click="closeDeleteDialog"
            class="text-none me-2"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmDelete" 
            :loading="deleting"
            class="text-none"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogBulkDelete" max-width="500px">
      <v-card class="rounded-xl elevation-8">
        <div class="delete-header text-center pa-8">
          <v-avatar size="64" color="error" class="mb-4">
            <v-icon size="32" color="white">mdi-delete-alert</v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold text-error mb-2">Konfirmasi Hapus Massal</h2>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Anda yakin ingin menghapus <strong>{{ selectedLangganan.length }} langganan</strong> yang dipilih?
          </p>
        </div>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1" 
            @click="dialogBulkDelete = false"
            class="text-none me-2"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmBulkDelete" 
            :loading="deleting"
            class="text-none"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup lang="ts">
// import { ref, onMounted, computed, watch } from 'vue';
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import apiClient from '@/services/api';
import { useDisplay } from 'vuetify';
import { debounce } from 'lodash-es';


// --- Responsive State ---
const { mobile } = useDisplay();
const fieldDensity = computed(() => mobile.value ? 'compact' : 'comfortable');
const notificationPelangganList = ref<PelangganSelectItem[] | null>(null);

// --- Interfaces ---
interface Langganan {
  id: number;
  pelanggan_id: number;
  paket_layanan_id: number;
  status: string;
  pelanggan: PelangganData;
  tgl_jatuh_tempo: string | null;
  tgl_invoice_terakhir: string | null;
  metode_pembayaran: string;
  harga_awal: number | null;
  harga_final: number;
  tgl_mulai_langganan?: string | null; 
}

interface PelangganData {
  id: number;
  nama: string;
  alamat: string;
}

interface PelangganSelectItem {
  id: number;
  nama: string;
  id_brand: string;
}

interface PaketLayananSelectItem {
  id: number;
  nama_paket: string;
  kecepatan: number;
  harga: number;
  id_brand: string;
}

// --- State ---
const langgananList = ref<Langganan[]>([]);
const pelangganSelectList = ref<PelangganSelectItem[]>([]);
const paketLayananSelectList = ref<PaketLayananSelectItem[]>([]);
const filteredPaketLayanan = ref<PaketLayananSelectItem[]>([]);

const loading = ref(true);
const paketLoading = ref(true);
const isPaketLocked = ref(false);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const editedIndex = ref(-1);
const formValid = ref(false);

const selectedLangganan = ref<Langganan[]>([]);
const dialogBulkDelete = ref(false);

const dialogImport = ref(false);
const importing = ref(false);
const fileToImport = ref<File[]>([]);
const importErrors = ref<string[]>([]);

const searchQuery = ref('');
const selectedPaket = ref<number | null>(null);
const selectedStatus = ref<string | null>(null);
const statusOptions = ref(['Aktif', 'Suspended', 'Berhenti']);

const isProratePlusFull = ref<boolean>(false);
const hargaProrate = ref<number>(0);
const hargaNormal = ref<number>(0);


function handleFileSelection(newFiles: File | File[]) {
  importErrors.value = [];
  if (Array.isArray(newFiles)) {
    fileToImport.value = newFiles;
  } else if (newFiles) {
    fileToImport.value = [newFiles];
  } else {
    fileToImport.value = [];
  }
}

function closeImportDialog() {
  dialogImport.value = false;
  fileToImport.value = [];
  importErrors.value = [];
}

const defaultItem: Partial<Langganan> = {
  pelanggan_id: undefined,
  paket_layanan_id: undefined,
  status: 'Aktif',
  tgl_jatuh_tempo: null,
  tgl_invoice_terakhir: null,
  metode_pembayaran: 'Otomatis',
  harga_awal: 0,
  tgl_mulai_langganan: null,
};
const editedItem = ref({ ...defaultItem });
const itemToDelete = ref<Langganan | null>(null);
const newPelangganIdMarker = ref<number | null>(null);

const isEditMode = computed(() => editedIndex.value > -1);

// --- Validation Rules ---
const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi',
};

// --- Headers ---
const headers = [
  { title: 'No', key: 'nomor', sortable: false, width: '5%' }, // Beri lebar sangat kecil
  // ATUR LEBAR NAMA DAN ALAMAT SECARA EKSPLISIT
  { title: 'Nama Pelanggan', key: 'pelanggan.nama', sortable: true, width: '15%' }, 
  { title: 'Alamat', key: 'pelanggan.alamat', sortable: false, width: '15%' },
  // Beri juga lebar pada kolom lain agar lebih seimbang
  { title: 'Paket Layanan', key: 'paket_layanan_id', width: '15%' },
  { title: 'Metode Bayar', key: 'metode_pembayaran', align: 'center', width: '15%' },
  { title: 'Harga', key: 'harga_final', align: 'end' },
  { title: 'Status', key: 'status', align: 'center', width: '20%' },
  { title: 'Jatuh Tempo', key: 'tgl_jatuh_tempo', align: 'center', width: '20%' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center', width: '20%' },
] as const;

// --- Computed Properties ---
const formTitle = computed(() => (editedIndex.value === -1 ? 'Tambah Langganan Baru' : 'Edit Langganan'));
const isFormValid = computed(() => !!(editedItem.value.pelanggan_id && editedItem.value.paket_layanan_id && editedItem.value.status && editedItem.value.harga_awal! > 0));

// --- Lifecycle ---
onMounted(() => {
  fetchLangganan();
  fetchPelangganForSelect();
  fetchPaketLayananForSelect();

  window.addEventListener('new-notification', handleNewNotification);

});

onUnmounted(() => {
  window.removeEventListener('new-notification', handleNewNotification);
});

const dropdownPelangganSource = computed(() => {
  // Jika dialog dibuka oleh notifikasi, gunakan daftar sementara (yang hanya berisi 1 pelanggan)
  if (notificationPelangganList.value) {
    return notificationPelangganList.value;
  }
  // Jika tidak, gunakan daftar normal yang sudah difilter
  return eligiblePelangganForSelect.value;
});

watch(() => editedItem.value.pelanggan_id, async (newPelangganId) => {
  // Reset HANYA pilihan paket layanan
  editedItem.value.paket_layanan_id = undefined;
  isPaketLocked.value = false;
  
  // Baris yang menyebabkan error ('hargaAwal.value = 0;') sudah dihapus.

  if (!newPelangganId) {
    filteredPaketLayanan.value = [];
    return;
  }

  try {
    // 1. Panggil API untuk mendapatkan detail lengkap pelanggan
    const response = await apiClient.get(`/pelanggan/${newPelangganId}`);
    const pelangganDetail = response.data;

    if (!pelangganDetail || !pelangganDetail.id_brand || !pelangganDetail.layanan) {
      filteredPaketLayanan.value = [];
      return;
    }

    const customerBrandId = pelangganDetail.id_brand;
    const customerLayananName = pelangganDetail.layanan;

    // 2. Saring daftar paket berdasarkan brand pelanggan
    filteredPaketLayanan.value = paketLayananSelectList.value.filter(
      paket => paket.id_brand === customerBrandId
    );

    // 3. Cari dan pilih paket yang namanya cocok dengan layanan pelanggan
    const matchedPaket = filteredPaketLayanan.value.find(
      paket => paket.nama_paket === customerLayananName
    );

    if (matchedPaket) {
      // Jika paket cocok, langsung pilih paket tersebut.
      // Perubahan ini akan otomatis memicu watch lain yang menghitung harga.
      editedItem.value.paket_layanan_id = matchedPaket.id;
      isPaketLocked.value = true;
    }

  } catch (error) {
    console.error("Gagal mengambil detail pelanggan:", error);
    filteredPaketLayanan.value = [];
  }
}, { immediate: true });


const handleNewNotification = async (event: Event) => {
  const customEvent = event as CustomEvent;
  const notificationData = customEvent.detail;

  if (notificationData.type === 'new_technical_data' && notificationData.data.pelanggan_id) {
    const newPelangganId = notificationData.data.pelanggan_id;
    newPelangganIdMarker.value = newPelangganId;
    
    await fetchPelangganForSelect();
    await fetchLangganan();

    // Cari objek pelanggan yang baru dari daftar yang sudah di-update
    const newPelanggan = pelangganSelectList.value.find(p => p.id === newPelangganId);
    
    if (newPelanggan) {
      // Isi daftar sementara HANYA dengan pelanggan baru tersebut
      notificationPelangganList.value = [newPelanggan];
    }

    openDialog();
    
    nextTick(() => {
      editedItem.value.pelanggan_id = newPelangganId;
    });
  }
};



watch(
  () => [
    editedItem.value.metode_pembayaran, 
    editedItem.value.paket_layanan_id, 
    editedItem.value.pelanggan_id, 
    editedItem.value.tgl_mulai_langganan,
    isProratePlusFull.value // Pantau juga switch
  ],
  async ([metode, paketId, pelangganId, tglMulai, proratePlus]) => {
    
    // Reset rincian harga setiap kali ada perubahan
    hargaProrate.value = 0;
    hargaNormal.value = 0;

    // Jika beralih ke Otomatis, matikan switch
    if (metode === 'Otomatis') {
      isProratePlusFull.value = false;
    }

    if (metode === 'Prorate' && !tglMulai && editedIndex.value === -1) {
      return; 
    }
    
    if (!dialog.value || !paketId || !pelangganId) {
      if(editedIndex.value === -1) {
        editedItem.value.harga_awal = 0;
      }
      return;
    }

    let endpoint = '/langganan/calculate-price';
    // Pilih endpoint yang benar
    if (metode === 'Prorate' && proratePlus) {
      endpoint = '/langganan/calculate-prorate-plus-full';
    }

    try {
      const payload = {
        paket_layanan_id: paketId,
        metode_pembayaran: metode,
        pelanggan_id: pelangganId,
        ...(metode !== 'Otomatis' && { tgl_mulai: tglMulai })
      };
      
      const response = await apiClient.post(endpoint, payload);
      
      // Tangani dua jenis response
      if (metode === 'Prorate' && proratePlus) {
        editedItem.value.harga_awal = response.data.harga_total_awal;
        hargaProrate.value = response.data.harga_prorate || 0;
        hargaNormal.value = response.data.harga_normal || 0;
      } else {
        editedItem.value.harga_awal = response.data.harga_awal;
      }
      
      editedItem.value.tgl_jatuh_tempo = response.data.tgl_jatuh_tempo;
      
    } catch (error: unknown) {
      console.error(`Error memanggil API ${endpoint}:`, error);
      editedItem.value.harga_awal = 0;
    }
  },
  { deep: true }
);



// --- API Methods ---
async function fetchLangganan() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    if (selectedPaket.value) {
      params.append('paket_layanan_id', String(selectedPaket.value));
    }
    if (selectedStatus.value) {
      params.append('status', selectedStatus.value);
    }
    
    const response = await apiClient.get<Langganan[]>(`/langganan/?${params.toString()}`);
    langgananList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data langganan:", error);
  } finally {
    loading.value = false;
  }
}

// Fungsi yang di-debounce untuk menerapkan filter
const applyFilters = debounce(() => {
  fetchLangganan();
}, 500); // Tunda 500ms

// Perhatikan perubahan pada filter dan panggil fungsi applyFilters
watch([searchQuery, selectedPaket, selectedStatus], () => {
  applyFilters();
});


async function confirmBulkDelete() {
  const itemsToDelete = [...selectedLangganan.value];
  if (itemsToDelete.length === 0) return;

  deleting.value = true;
  try {
    const deletePromises = itemsToDelete.map(langganan =>
      apiClient.delete(`/langganan/${langganan.id}`)
    );
    await Promise.all(deletePromises);

    // Asumsi Anda punya fungsi showSnackbar
    // showSnackbar(`${itemsToDelete.length} langganan berhasil dihapus.`, 'success');
    
    fetchLangganan();
    selectedLangganan.value = [];
  } catch (error) {
    console.error("Gagal melakukan hapus massal langganan:", error);
    // showSnackbar('Terjadi kesalahan saat menghapus data.', 'error');
  } finally {
    deleting.value = false;
    dialogBulkDelete.value = false;
  }
}

// Fungsi untuk mereset semua filter
function resetFilters() {
  searchQuery.value = '';
  selectedPaket.value = null;
  selectedStatus.value = null;
}
// ============================================

const eligiblePelangganForSelect = computed(() => {
  // Saat mode Edit, tampilkan semua pelanggan agar pilihan yang ada tidak hilang
  if (isEditMode.value) {
    return pelangganSelectList.value;
  }
  
  // Saat mode Tambah, filter pelanggan
  // 1. Buat daftar ID semua pelanggan yang SUDAH punya langganan
  const subscribedPelangganIds = new Set(langgananList.value.map(l => l.pelanggan_id));
  
  // 2. Kembalikan HANYA pelanggan yang ID-nya TIDAK ADA di daftar langganan
  return pelangganSelectList.value.filter(p => !subscribedPelangganIds.has(p.id));
});

async function fetchPelangganForSelect() {
  try {
    const response = await apiClient.get<PelangganSelectItem[]>('/pelanggan/');
    pelangganSelectList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data pelanggan untuk select:", error);
  }
}

async function fetchPaketLayananForSelect() {
  paketLoading.value = true;
  try {
    const response = await apiClient.get<PaketLayananSelectItem[]>('/paket_layanan/');
    paketLayananSelectList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data paket layanan untuk select:", error);
    paketLayananSelectList.value = [];
  } finally {
    paketLoading.value = false;
  }
}

function openDialog(item?: Langganan) {
  editedIndex.value = item ? langgananList.value.findIndex(l => l.id === item.id) : -1;
  editedItem.value = item ? { ...item } : { ...defaultItem };
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  // Reset daftar sementara saat dialog ditutup
  notificationPelangganList.value = null; 
  setTimeout(() => {
    editedItem.value = { ...defaultItem };
    editedIndex.value = -1;
  }, 300);
}

async function saveLangganan() {
  // Validasi form (tidak berubah)
  if (!isFormValid.value) return;
  
  saving.value = true;
  
  // Siapkan payload yang akan dikirim ke backend
  const dataToSave = {
    pelanggan_id: editedItem.value.pelanggan_id,
    paket_layanan_id: editedItem.value.paket_layanan_id,
    status: editedItem.value.status,
    metode_pembayaran: editedItem.value.metode_pembayaran,
    tgl_mulai_langganan: editedItem.value.tgl_mulai_langganan,

    // Kirim status switch ke backend
    sertakan_bulan_depan: isProratePlusFull.value 
  };

  try {
    if (editedIndex.value > -1) {
      // Logika update tidak perlu mengirim 'sertakan_bulan_depan'
      // jadi kita bisa gunakan payload yang lebih sederhana
      const updatePayload = {
        paket_layanan_id: editedItem.value.paket_layanan_id,
        status: editedItem.value.status,
        metode_pembayaran: editedItem.value.metode_pembayaran,
        tgl_jatuh_tempo: editedItem.value.tgl_jatuh_tempo,
        harga_awal: editedItem.value.harga_awal
      };
      await apiClient.patch(`/langganan/${editedItem.value.id}`, updatePayload);
    } else {
      // Saat membuat baru, kirim payload yang sudah kita siapkan
      await apiClient.post('/langganan/', dataToSave);
    }
    fetchLangganan();
    closeDialog();
  } catch (error) { 
    console.error("Gagal menyimpan data langganan:", error);
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: Langganan) {
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
    await apiClient.delete(`/langganan/${itemToDelete.value.id}`);
    fetchLangganan();
    closeDeleteDialog();
  } catch (error) {
    console.error("Gagal menghapus langganan:", error);
  } finally {
    deleting.value = false;
  }
}

// --- Helper Methods ---
function getPelangganName(pelangganId: number | undefined): string {
  if (!pelangganId) return 'N/A';
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.nama || `ID ${pelangganId}`;
}

function getPaketName(paketId: number | undefined): string {
    if (!paketId) return 'N/A';
    const paket = paketLayananSelectList.value.find(p => p.id === paketId);
    return paket?.nama_paket || `ID Paket ${paketId}`;
}

function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'aktif': return 'green';
    case 'non-aktif': return 'orange';
    case 'berhenti': return 'red';
    default: return 'grey';
  }
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateString: string | Date | null | undefined): string {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Invalid Date';
  return date.toLocaleDateString('id-ID', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}



async function exportLangganan() {
  try {
    const response = await apiClient.get('/langganan/export/csv', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `export_langganan_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error("Gagal mengekspor data langganan:", error);
  }
}

async function importFromCsv() {
  const file = fileToImport.value[0];
  if (!file) return;

  importing.value = true;
  importErrors.value = [];
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post('/langganan/import/csv', formData);
    // Tampilkan notifikasi sukses
    console.log(response.data.message);
    fetchLangganan(); // Muat ulang data
    closeImportDialog();
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    if (detail && detail.errors) {
      importErrors.value = detail.errors;
    } else {
      importErrors.value = [detail || "Terjadi kesalahan."];
    }
  } finally {
    importing.value = false;
  }
}





</script>

<style scoped>

:root {
  /* Light Theme Colors */
  --light-bg-primary: #ffffff;
  --light-bg-secondary: #f8fafc;
  --light-bg-tertiary: #f1f5f9;
  --light-surface: #ffffff;
  --light-surface-variant: #f8fafc;
  --light-border: rgba(0, 0, 0, 0.12);
  --light-border-hover: rgba(0, 0, 0, 0.24);
  --light-text-primary: #1a202c;
  --light-text-secondary: #4a5568;
  --light-text-tertiary: #718096;
  --light-shadow: rgba(0, 0, 0, 0.1);
  --light-shadow-hover: rgba(0, 0, 0, 0.15);
  
  /* Dark Theme Colors */
  --dark-bg-primary: #1a1a1a;
  --dark-bg-secondary: #242424;
  --dark-bg-tertiary: #2d2d2d;
  --dark-surface: #1e1e1e;
  --dark-surface-variant: #2a2a2a;
  --dark-border: rgba(255, 255, 255, 0.12);
  --dark-border-hover: rgba(255, 255, 255, 0.24);
  --dark-text-primary: #ffffff;
  --dark-text-secondary: #e2e8f0;
  --dark-text-tertiary: #a0aec0;
  --dark-shadow: rgba(0, 0, 0, 0.3);
  --dark-shadow-hover: rgba(0, 0, 0, 0.4);
  
  /* Primary Colors */
  --primary-500: #6366f1;
  --primary-600: #4f46e5;
  --primary-700: #4338ca;
  --primary-50: #eef2ff;
  --primary-100: #e0e7ff;
  
  /* Success Colors */
  --success-500: #22c55e;
  --success-600: #16a34a;
  --success-50: #f0fdf4;
  
  /* Info Colors */
  --info-500: #3b82f6;
  --info-600: #2563eb;
  --info-50: #eff6ff;
  
  /* Error Colors */
  --error-500: #ef4444;
  --error-600: #dc2626;
  --error-50: #fef2f2;
}

/* ============================================
   BASE CONTAINER STYLING
   ============================================ */
.v-container {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Light Mode Base */
.v-theme--light .v-container {
  background: linear-gradient(135deg, 
    var(--light-bg-secondary) 0%, 
    var(--light-bg-tertiary) 100%);
  color: var(--light-text-primary);
}

/* Dark Mode Base */
.v-theme--dark .v-container {
  background: linear-gradient(135deg, 
    var(--dark-bg-primary) 0%, 
    var(--dark-bg-secondary) 100%);
  color: var(--dark-text-primary);
}

/* ============================================
   HEADER SECTION STYLING
   ============================================ */
.header-section {
  margin-bottom: 32px;
  padding: 24px 0;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
}

/* Light Mode Header */
.v-theme--light .header-section {
  background: linear-gradient(135deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%);
  border: 1px solid var(--light-border);
  box-shadow: 0 4px 20px var(--light-shadow);
}

/* Dark Mode Header */
.v-theme--dark .header-section {
  background: linear-gradient(135deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%);
  border: 1px solid var(--dark-border);
  box-shadow: 0 4px 20px var(--dark-shadow);
}

/* Header Icon Styling */
.header-section .v-avatar {
  box-shadow: 0 4px 16px rgba(var(--primary-500), 0.3);
}

.header-section .text-primary {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}


/* Enhanced Form Dialog Styling */
        .subscription-form-container {
            max-width: 100vw;
            max-height: 100vh;
            overflow-y: auto;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            font-family: 'Inter', 'Roboto', sans-serif;
        }

        .form-dialog {
            border-radius: 24px !important;
            overflow: hidden;
            max-width: 800px;
            margin: 20px auto;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15), 0 15px 40px rgba(0, 0, 0, 0.1) !important;
            background: white;
        }

        /* Enhanced Header */
        .form-header {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #4338ca 100%) !important;
            position: relative;
            overflow: hidden;
            padding: 32px !important;
            color: white;
        }

        .form-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 200px;
            height: 200%;
            background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
            transform: rotate(25deg);
            transition: all 0.5s ease;
        }

        .form-header:hover::before {
            right: -10%;
            transform: rotate(25deg) scale(1.1);
        }

        .form-header-content {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .form-icon-wrapper {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .form-icon {
            background: white !important;
            color: #6366f1 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            width: 48px !important;
            height: 48px !important;
        }

        .form-title {
            font-size: 2rem !important;
            font-weight: 800 !important;
            margin-bottom: 8px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: 0.5px !important;
            line-height: 1.2 !important;
        }

        .form-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem !important;
            font-weight: 400 !important;
            margin: 0 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            line-height: 1.4 !important;
            letter-spacing: 0.2px !important;
        }

        /* Form Content */
        .form-content {
            padding: 32px !important;
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        }

        /* Form Sections */
        .form-section {
            margin-bottom: 40px !important;
            position: relative;
        }

        .form-section:last-child {
            margin-bottom: 24px !important;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px !important;
            padding: 16px 0 12px 0;
            position: relative;
        }

        .section-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 40px;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, 
                rgba(99, 102, 241, 0.3) 0%,
                rgba(99, 102, 241, 0.1) 50%,
                transparent 100%
            );
        }

        .section-title {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 0.8px !important;
            margin: 0;
        }

        .section-icon {
            color: #6366f1 !important;
            font-size: 1.3rem !important;
        }

        /* Enhanced Form Fields */
        .enhanced-field {
            margin-bottom: 24px !important;
        }

        .enhanced-field .v-field {
            border-radius: 16px !important;
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid rgba(99, 102, 241, 0.1) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
            min-height: 56px !important;
        }

        .enhanced-field .v-field:hover {
            background: rgba(255, 255, 255, 1) !important;
            border-color: rgba(99, 102, 241, 0.3) !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.1) !important;
        }

        .enhanced-field .v-field--focused {
            background: white !important;
            border-color: #6366f1 !important;
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15), 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
        }

        .enhanced-field .v-field__input {
            padding: 16px 20px !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            min-height: 24px !important;
        }

        .enhanced-field .v-field__prepend-inner .v-icon {
            color: rgba(99, 102, 241, 0.7) !important;
            font-size: 1.2rem !important;
            margin-right: 12px !important;
        }

        .enhanced-field .v-field--focused .v-field__prepend-inner .v-icon {
            color: #6366f1 !important;
            transform: scale(1.05);
        }

        /* Price Field Special Styling */
        .price-field .v-field {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
            border-color: rgba(14, 165, 233, 0.3) !important;
        }

        .price-field .v-field:hover {
            border-color: rgba(14, 165, 233, 0.5) !important;
        }

        .price-field .v-field--focused {
            border-color: #0ea5e9 !important;
            box-shadow: 0 8px 25px rgba(14, 165, 233, 0.15), 0 0 0 4px rgba(14, 165, 233, 0.1) !important;
        }

        .price-field .v-field__input {
            color: #0369a1 !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }

        /* Row and Column Spacing */
        .v-row {
            margin-bottom: 16px !important;
        }

        .v-row:last-child {
            margin-bottom: 0 !important;
        }

        /* Switch Styling */
        .v-switch {
            margin-top: 8px;
        }

        /* Alert Styling */
        .v-alert {
            border-radius: 16px !important;
            margin-bottom: 20px !important;
            border: 1px solid rgba(59, 130, 246, 0.2) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08) !important;
        }

        .v-alert--variant-tonal {
            background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%) !important;
        }

        /* Action Footer */
        .action-footer {
            background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
            border-top: 1px solid rgba(0, 0, 0, 0.06);
            padding: 32px !important;
        }

        .action-buttons {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 16px;
        }

        /* Enhanced Buttons */
        .cancel-btn {
            color: #6b7280 !important;
            background: rgba(107, 114, 128, 0.1) !important;
            border: 1px solid rgba(107, 114, 128, 0.2) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            text-transform: none !important;
            padding: 14px 24px !important;
            min-height: 48px !important;
            transition: all 0.3s ease !important;
        }

        .cancel-btn:hover {
            background: rgba(107, 114, 128, 0.15) !important;
            color: #374151 !important;
            border-color: rgba(107, 114, 128, 0.3) !important;
        }

        .save-btn {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: none !important;
            padding: 14px 32px !important;
            font-size: 1rem !important;
            letter-spacing: 0.3px !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3), 0 3px 10px rgba(99, 102, 241, 0.2) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
            min-height: 48px !important;
        }

        .save-btn:hover {
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4), 0 5px 15px rgba(99, 102, 241, 0.3) !important;
        }

        .save-btn:active {
            transform: translateY(0);
            transition: all 0.1s ease;
        }

        /* Button Ripple Effect */
        .save-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transition: width 0.6s ease, height 0.6s ease;
            transform: translate(-50%, -50%);
            z-index: 0;
        }

        .save-btn:active::before {
            width: 300px;
            height: 300px;
        }

        .save-btn .v-btn__content {
            position: relative;
            z-index: 1;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .form-dialog {
                margin: 16px !important;
                max-width: calc(100vw - 32px) !important;
                border-radius: 16px !important;
            }

            .form-header {
                padding: 24px !important;
            }

            .form-title {
                font-size: 1.5rem !important;
                line-height: 1.3 !important;
                text-align: center;
            }

            .form-subtitle {
                font-size: 0.95rem !important;
                text-align: center;
            }

            .form-content {
                padding: 24px !important;
            }

            .form-section {
                margin-bottom: 32px !important;
            }

            .section-title {
                font-size: 1.1rem !important;
            }

            .action-footer {
                padding: 20px !important;
            }

            .action-buttons {
                flex-direction: column;
                width: 100%;
                gap: 12px;
            }

            .cancel-btn,
            .save-btn {
                width: 100%;
                justify-content: center;
            }

            .form-header-content {
                flex-direction: column;
                text-align: center;
                gap: 16px;
            }
        }

        @media (max-width: 480px) {
            .form-header {
                padding: 20px !important;
            }

            .form-title {
                font-size: 1.3rem !important;
            }

            .form-subtitle {
                font-size: 0.9rem !important;
            }

            .form-content {
                padding: 20px !important;
            }

            .enhanced-field {
                margin-bottom: 20px !important;
            }

            .section-title {
                font-size: 1rem !important;
            }
        }

        /* Dark Theme Support */
        @media (prefers-color-scheme: dark) {
            .subscription-form-container {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            }

            .form-dialog {
                background: #1e1e1e;
            }

            .form-content {
                background: linear-gradient(145deg, #1e1e1e 0%, #2a2a2a 100%);
            }

            .section-title {
                color: #e5e7eb;
            }

            .enhanced-field .v-field {
                background: rgba(42, 42, 42, 0.9) !important;
                border-color: rgba(255, 255, 255, 0.1) !important;
                color: #e5e7eb !important;
            }

            .enhanced-field .v-field:hover {
                background: rgba(46, 46, 46, 1) !important;
                border-color: rgba(99, 102, 241, 0.4) !important;
            }

            .enhanced-field .v-field--focused {
                background: rgba(30, 30, 30, 1) !important;
                border-color: #6366f1 !important;
            }

            .action-footer {
                background: linear-gradient(145deg, #2a2a2a 0%, #3d3d3d 100%);
                border-top-color: rgba(255, 255, 255, 0.1);
            }
        }

        /* Smooth Transitions */
        * {
            transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
        }

        /* Focus Visible States for Accessibility */
        .v-btn:focus-visible,
        .v-field:focus-visible,
        .v-select:focus-visible {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }

        /* Loading State */
        .v-btn--loading {
            pointer-events: none;
        }

        .v-btn--loading .v-btn__overlay {
            background: rgba(255, 255, 255, 0.1);
        }

/* ============================================
   ENHANCED BUTTON STYLING
   ============================================ */


/* Modal Styling */
.subscription-modal {
  border-radius: 16px !important;
  overflow: hidden;
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  width: 100%;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 4px;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 0;
  line-height: 1.3;
}

.modal-content {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 32px;
}

.form-section:last-child {
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(var(--v-border-color), 0.12);
}

.price-field {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.modal-actions {
  padding: 20px 24px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background-color: rgba(var(--v-theme-surface), 0.5);
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-header {
    padding: 20px;
  }
  
  .header-title {
    font-size: 1.1rem;
  }
  
  .header-subtitle {
    font-size: 0.85rem;
  }
  
  .modal-content {
    padding: 20px;
    max-height: 65vh;
  }
  
  .form-section {
    margin-bottom: 24px;
  }
  
  .section-title {
    font-size: 0.95rem;
    margin-bottom: 12px;
  }
}

@media (max-width: 600px) {
  .modal-header {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .modal-content {
    padding: 16px;
  }
  
  .modal-actions {
    padding: 16px;
    flex-direction: column;
    gap: 8px;
  }
  
  .modal-actions .v-btn {
    width: 100%;
  }
}

/* Landscape Mobile Optimization */
@media (max-height: 600px) and (orientation: landscape) {
  .modal-content {
    max-height: 50vh;
    padding: 16px 24px;
  }
  
  .form-section {
    margin-bottom: 20px;
  }
  
  .section-title {
    margin-bottom: 12px;
    font-size: 0.9rem;
  }
  
  .modal-header {
    padding: 16px 24px;
  }
  
  .header-title {
    font-size: 1rem;
  }
  
  .header-subtitle {
    font-size: 0.8rem;
  }
}

/* Import Button */
.import-btn {
  background: linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 0 4px 16px rgba(var(--success-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.import-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--success-500), 0.4) !important;
}

/* Export Button */
.export-btn {
  background: linear-gradient(135deg, var(--info-500) 0%, var(--info-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 0 4px 16px rgba(var(--info-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.export-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--info-500), 0.4) !important;
}

/* Add Subscription Button */
.add-subscription-btn {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 16px !important;
  padding: 14px 28px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  font-size: 1rem !important;
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.add-subscription-btn:hover {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%) !important;
  transform: translateY(-3px);
  box-shadow: 0 10px 32px rgba(var(--primary-500), 0.4) !important;
}

/* ============================================
   FILTER CARD STYLING
   ============================================ */
.filter-card {
  border-radius: 20px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  margin-bottom: 24px;
}

/* Light Mode Filter Card */
.v-theme--light .filter-card {
  background: linear-gradient(145deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
  border: 1px solid var(--light-border) !important;
  box-shadow: 0 4px 20px var(--light-shadow) !important;
}

.v-theme--light .filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px var(--light-shadow-hover) !important;
  border-color: rgba(var(--primary-500), 0.2) !important;
}

/* Dark Mode Filter Card */
.v-theme--dark .filter-card {
  background: linear-gradient(145deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
  border: 1px solid var(--dark-border) !important;
  box-shadow: 0 4px 20px var(--dark-shadow) !important;
}

.v-theme--dark .filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px var(--dark-shadow-hover) !important;
  border-color: rgba(var(--primary-500), 0.3) !important;
}

/* Filter Card Top Border Effect */
.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--primary-500) 50%, 
    transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.filter-card:hover::before {
  opacity: 1;
}


.v-data-table :deep(td),
.v-data-table :deep(th) {
  /* Kurangi padding horizontal dari default 16px menjadi 8px */
  padding: 0 8px !important; 
}

/* ============================================
   FORM FIELD STYLING
   ============================================ */

/* Base Field Styling */
.enhanced-form-field .v-field {
  border-radius: 12px !important;
  border-width: 2px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Light Mode Fields */
.v-theme--light .enhanced-form-field .v-field {
  background: rgba(255, 255, 255, 0.9) !important;
  border-color: var(--light-border) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
}

.v-theme--light .enhanced-form-field .v-field:hover {
  background: rgba(255, 255, 255, 1) !important;
  border-color: rgba(var(--primary-500), 0.4) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.1) !important;
}

.v-theme--light .enhanced-form-field .v-field--focused {
  background: white !important;
  border-color: var(--primary-500) !important;
  box-shadow: 0 0 0 4px rgba(var(--primary-500), 0.1) !important;
}

/* Dark Mode Fields */
.v-theme--dark .enhanced-form-field .v-field {
  background: rgba(42, 42, 42, 0.9) !important;
  border-color: var(--dark-border) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
  color: var(--dark-text-primary) !important;
}

.v-theme--dark .enhanced-form-field .v-field:hover {
  background: rgba(46, 46, 46, 1) !important;
  border-color: rgba(var(--primary-500), 0.5) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.2) !important;
}

.v-theme--dark .enhanced-form-field .v-field--focused {
  background: var(--dark-surface-variant) !important;
  border-color: var(--primary-500) !important;
  box-shadow: 0 0 0 4px rgba(var(--primary-500), 0.2) !important;
}

/* Field Input Text Color */
.v-theme--dark .enhanced-form-field .v-field__input {
  color: var(--dark-text-primary) !important;
}

.v-theme--light .enhanced-form-field .v-field__input {
  color: var(--light-text-primary) !important;
}

/* Field Label Colors */
.v-theme--dark .enhanced-form-field .v-field-label {
  color: var(--dark-text-secondary) !important;
}

.v-theme--light .enhanced-form-field .v-field-label {
  color: var(--light-text-secondary) !important;
}

/* ============================================
   DATA TABLE STYLING
   ============================================ */
.v-data-table {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08) !important;
}

/* Light Mode Data Table */
.v-theme--light .v-data-table {
  background: var(--light-surface) !important;
  border: 1px solid var(--light-border) !important;
}

.v-theme--light .v-data-table .v-data-table-header {
  background: linear-gradient(135deg, 
    var(--light-surface-variant) 0%, 
    var(--light-bg-tertiary) 100%) !important;
  border-bottom: 1px solid var(--light-border) !important;
}

.v-theme--light .v-data-table tbody tr:nth-child(even) {
  background: rgba(var(--primary-50), 0.3) !important;
}

.v-theme--light .v-data-table tbody tr:hover {
  background: rgba(var(--primary-50), 0.6) !important;
}

/* Dark Mode Data Table */
.v-theme--dark .v-data-table {
  background: var(--dark-surface) !important;
  border: 1px solid var(--dark-border) !important;
}

.v-theme--dark .v-data-table .v-data-table-header {
  background: linear-gradient(135deg, 
    var(--dark-surface-variant) 0%, 
    var(--dark-bg-tertiary) 100%) !important;
  border-bottom: 1px solid var(--dark-border) !important;
}

.v-theme--dark .v-data-table tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02) !important;
}

.v-theme--dark .v-data-table tbody tr:hover {
  background: rgba(var(--primary-500), 0.1) !important;
}

/* Data Table Text Colors */
.v-theme--dark .v-data-table th,
.v-theme--dark .v-data-table td {
  color: var(--dark-text-primary) !important;
}

.v-theme--light .v-data-table th,
.v-theme--light .v-data-table td {
  color: var(--light-text-primary) !important;
}

/* ============================================
   IMPORT DIALOG STYLING
   ============================================ */
.import-dialog {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.15) !important;
}

/* Import Dialog Header */
.import-dialog-header {
  background: linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%) !important;
  color: white !important;
  padding: 24px 32px !important;
  position: relative;
  overflow: hidden;
}

.import-dialog-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 100px;
  height: 200%;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(15deg);
  transition: all 0.3s ease;
}

/* Import Dialog Content - Light Mode */
.v-theme--light .import-dialog-content {
  background: linear-gradient(145deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
  color: var(--light-text-primary) !important;
}

/* Import Dialog Content - Dark Mode */
.v-theme--dark .import-dialog-content {
  background: linear-gradient(145deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
  color: var(--dark-text-primary) !important;
}

/* Import File Input Styling */
.import-file-input .v-field {
  border-radius: 16px !important;
  border: 3px dashed rgba(var(--success-500), 0.3) !important;
  min-height: 80px !important;
  padding: 16px !important;
  transition: all 0.3s ease !important;
}

/* Light Mode File Input */
.v-theme--light .import-file-input .v-field {
  background: linear-gradient(135deg, 
    rgba(var(--success-50), 0.5) 0%, 
    rgba(var(--success-50), 0.3) 100%) !important;
}

.v-theme--light .import-file-input .v-field:hover {
  background: linear-gradient(135deg, 
    rgba(var(--success-50), 0.8) 0%, 
    rgba(var(--success-50), 0.6) 100%) !important;
  border-color: rgba(var(--success-500), 0.5) !important;
}

/* Dark Mode File Input */
.v-theme--dark .import-file-input .v-field {
  background: linear-gradient(135deg, 
    rgba(var(--success-500), 0.1) 0%, 
    rgba(var(--success-500), 0.05) 100%) !important;
}

.v-theme--dark .import-file-input .v-field:hover {
  background: linear-gradient(135deg, 
    rgba(var(--success-500), 0.15) 0%, 
    rgba(var(--success-500), 0.1) 100%) !important;
  border-color: rgba(var(--success-500), 0.5) !important;
}

/* ============================================
   FORM DIALOG STYLING
   ============================================ */
.subscription-form-dialog {
  border-radius: 24px !important;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15) !important;
}

/* Enhanced Form Header */
.enhanced-form-header {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 50%, var(--primary-700) 100%) !important;
  position: relative;
  overflow: hidden;
  padding: 32px !important;
}

.enhanced-form-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200%;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  transform: rotate(25deg);
  transition: all 0.5s ease;
}

/* Section Cards - Light Mode */
.v-theme--light .enhanced-section-card {
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.9) 100%) !important;
  border: 1px solid rgba(var(--primary-500), 0.1) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
}

.v-theme--light .enhanced-section-card:hover {
  border-color: rgba(var(--primary-500), 0.2) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08) !important;
}

/* Section Cards - Dark Mode */
.v-theme--dark .enhanced-section-card {
  background: linear-gradient(145deg, 
    rgba(30, 30, 30, 0.95) 0%,
    rgba(42, 42, 42, 0.9) 100%) !important;
  border: 1px solid rgba(var(--primary-500), 0.15) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
}

.v-theme--dark .enhanced-section-card:hover {
  border-color: rgba(var(--primary-500), 0.3) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
}

/* ============================================
   ACTION BUTTONS STYLING
   ============================================ */

/* Cancel Button */
.enhanced-cancel-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  padding: 14px 24px !important;
  transition: all 0.3s ease !important;
}

/* Light Mode Cancel Button */
.v-theme--light .enhanced-cancel-btn {
  color: var(--light-text-secondary) !important;
  background: rgba(107, 114, 128, 0.1) !important;
  border: 1px solid rgba(107, 114, 128, 0.2) !important;
}

.v-theme--light .enhanced-cancel-btn:hover {
  background: rgba(107, 114, 128, 0.15) !important;
  color: var(--light-text-primary) !important;
}

/* Dark Mode Cancel Button */
.v-theme--dark .enhanced-cancel-btn {
  color: var(--dark-text-secondary) !important;
  background: rgba(156, 163, 175, 0.1) !important;
  border: 1px solid rgba(156, 163, 175, 0.2) !important;
}

.v-theme--dark .enhanced-cancel-btn:hover {
  background: rgba(156, 163, 175, 0.15) !important;
  color: var(--dark-text-primary) !important;
}

/* Save Button */
.enhanced-save-btn {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  padding: 14px 32px !important;
  font-size: 1rem !important;
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.enhanced-save-btn:hover {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(var(--primary-500), 0.4) !important;
}

/* ============================================
   ACTION FOOTER STYLING
   ============================================ */

/* Light Mode Action Footer */
.v-theme--light .enhanced-action-footer {
  background: linear-gradient(145deg, 
    var(--light-surface-variant) 0%, 
    var(--light-bg-tertiary) 100%) !important;
  border-top: 1px solid var(--light-border) !important;
}

/* Dark Mode Action Footer */
.v-theme--dark .enhanced-action-footer {
  background: linear-gradient(145deg, 
    var(--dark-surface-variant) 0%, 
    var(--dark-bg-tertiary) 100%) !important;
  border-top: 1px solid var(--dark-border) !important;
}

/* ============================================
   DELETE DIALOG STYLING
   ============================================ */
.delete-header {
  transition: background 0.3s ease;
}

/* Light Mode Delete Header */
.v-theme--light .delete-header {
  background: linear-gradient(135deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
}

/* Dark Mode Delete Header */
.v-theme--dark .delete-header {
  background: linear-gradient(135deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
}

/* ============================================
   SELECTION TOOLBAR
   ============================================ */
.selection-toolbar {
  border-radius: 12px 12px 0 0;
  transition: all 0.3s ease;
}

/* Light Mode Selection Toolbar */
.v-theme--light .selection-toolbar {
  background: rgba(var(--primary-50), 0.6) !important;
  border-bottom: 1px solid rgba(var(--primary-500), 0.15) !important;
  color: var(--light-text-primary) !important;
}

/* Dark Mode Selection Toolbar */
.v-theme--dark .selection-toolbar {
  background: rgba(var(--primary-500), 0.15) !important;
  border-bottom: 1px solid rgba(var(--primary-500), 0.25) !important;
  color: var(--dark-text-primary) !important;
}

/* ============================================
   CHIP STYLING
   ============================================ */
.v-chip {
  font-weight: 600 !important;
  border-radius: 8px !important;
}

/* Status Chips */
.v-chip--color-green {
  background: linear-gradient(135deg, var(--success-500), var(--success-600)) !important;
  color: white !important;
}

.v-chip--color-red {
  background: linear-gradient(135deg, var(--error-500), var(--error-600)) !important;
  color: white !important;
}

.v-chip--color-blue {
  background: linear-gradient(135deg, var(--info-500), var(--info-600)) !important;
  color: white !important;
}

/* ============================================
   RESPONSIVE ENHANCEMENTS
   ============================================ */

@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .import-btn,
  .export-btn,
  .add-subscription-btn {
    width: 100%;
    justify-content: center;
  }
  
  .subscription-form-dialog {
    margin: 16px !important;
    max-width: calc(100vw - 32px) !important;
    border-radius: 16px !important;
  }
  
  .enhanced-form-header {
    padding: 24px !important;
    height: auto; 
  display: flex;
  align-items: center;
  }
  
  .enhanced-section-card {
    padding: 20px !important;
    margin: 0 -4px !important;
  }
  
  .filter-card .d-flex {
    flex-direction: column !important;
    gap: 12px !important;
  }
  
  .enhanced-form-field,
  .v-select,
  .v-text-field {
    min-width: 100% !important;
  }
}

@media (max-width: 480px) {
  .import-dialog-content {
    padding: 20px !important;
  }
  
  .import-dialog-header {
    padding: 20px !important;
  }
  
  .enhanced-action-footer {
    padding: 20px !important;
  }
  
  .enhanced-action-footer .action-buttons {
    flex-direction: column;
    width: 100%;
    gap: 12px;
  }
  
  .enhanced-cancel-btn,
  .enhanced-save-btn {
    width: 100%;
    justify-content: center;
  }
}

/* ============================================
   SMOOTH TRANSITIONS
   ============================================ */
* {
  transition: background-color 0.3s ease,
              border-color 0.3s ease,
              color 0.3s ease,
              box-shadow 0.3s ease;
}

/* ============================================
   ACCESSIBILITY ENHANCEMENTS
   ============================================ */

/* Focus Visible States */
.v-btn:focus-visible,
.v-field:focus-visible,
.v-select:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

/* High Contrast Support */
@media (prefers-contrast: high) {
  :root {
    --light-border: rgba(0, 0, 0, 0.3);
    --dark-border: rgba(255, 255, 255, 0.3);
  }
}

/* ============================================
   TYPOGRAPHY CONSISTENCY
   ============================================ */

/* Ensure consistent font family */
.add-subscription-btn .v-btn__content,
.enhanced-save-btn .v-btn__content,
.enhanced-form-header .form-title,
.enhanced-form-header .form-subtitle,
.enhanced-section-header .section-title,
.step-badge {
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Text selection styling */
.enhanced-form-header .form-title::selection,
.enhanced-form-header .form-subtitle::selection,
.enhanced-section-header .section-title::selection {
  background: rgba(255, 255, 255, 0.3);
  color: inherit;
}

/* Prevent text selection on buttons */
.add-subscription-btn,
.enhanced-save-btn,
.step-badge {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}


/* High contrast mode support */
@media (prefers-contrast: high) {
  .add-subscription-btn,
  .enhanced-save-btn,
  .step-badge {
    border: 2px solid rgba(255, 255, 255, 0.5) !important;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
  }

  .enhanced-section-header .section-title {
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }
}

/* Focus visible states for keyboard navigation */
.add-subscription-btn:focus-visible,
.enhanced-save-btn:focus-visible {
  outline: 3px solid rgba(255, 255, 255, 0.8);
  outline-offset: 2px;
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .add-subscription-btn .v-icon,
  .enhanced-save-btn .v-icon {
    transition: none !important;
  }

  .add-subscription-btn:hover .v-icon {
    transform: none !important;
  }
}

/* ============================================
   ENHANCED IMPORT/EXPORT BUTTONS STYLING
   ============================================ */

/* Container untuk button group di header */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Enhanced Import Button */
.import-btn {
  position: relative;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 
    0 4px 12px rgba(76, 175, 80, 0.3),
    0 2px 6px rgba(76, 175, 80, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
}

.import-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(76, 175, 80, 0.4),
    0 4px 12px rgba(76, 175, 80, 0.3) !important;
}

.import-btn:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

/* Import button icon animation */
.import-btn .v-icon {
  transition: transform 0.3s ease;
}

.import-btn:hover .v-icon {
  transform: translateY(-2px) scale(1.1);
}

/* Enhanced Export Button */
.export-btn {
  position: relative;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 
    0 4px 12px rgba(33, 150, 243, 0.3),
    0 2px 6px rgba(33, 150, 243, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
}

.export-btn:hover {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(33, 150, 243, 0.4),
    0 4px 12px rgba(33, 150, 243, 0.3) !important;
}

.export-btn:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

/* Export button icon animation */
.export-btn .v-icon {
  transition: transform 0.3s ease;
}

.export-btn:hover .v-icon {
  transform: translateY(-2px) scale(1.1);
}

/* Enhanced Add Button */
/* Add Subscription Button - Enhanced */
.add-subscription-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 16px !important;
  padding: 14px 28px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  font-size: 1rem !important;
  letter-spacing: 0.3px !important;
  box-shadow: 
    0 6px 20px rgba(99, 102, 241, 0.3),
    0 3px 10px rgba(99, 102, 241, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
  min-height: 48px !important;
}

.add-subscription-btn:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
  transform: translateY(-3px);
  box-shadow: 
    0 8px 30px rgba(99, 102, 241, 0.4),
    0 5px 15px rgba(99, 102, 241, 0.3) !important;
}

.add-subscription-btn:active {
  transform: translateY(-1px);
  transition: all 0.1s ease;
}

/* Ripple effect for buttons */
.import-btn::before,
.export-btn::before,
.add-subscription-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: width 0.6s ease, height 0.6s ease;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.import-btn:active::before,
.export-btn:active::before,
.add-subscription-btn:active::before {
  width: 300px;
  height: 300px;
}

/* Button text and icon positioning */
.import-btn .v-btn__content,
.export-btn .v-btn__content,
.add-subscription-btn .v-btn__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700 !important;
  font-size: 1rem !important;
  white-space: nowrap;
}

.add-subscription-btn .v-icon {
  font-size: 1.2rem !important;
  transition: transform 0.3s ease;
}

.add-subscription-btn:hover .v-icon {
  transform: scale(1.1) rotate(90deg);
}

/* ============================================
   ENHANCED IMPORT DIALOG STYLING
   ============================================ */

.import-dialog {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 10px 30px rgba(0, 0, 0, 0.1) !important;
}

/* Import dialog header */
.import-dialog-header {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 50%, #388e3c 100%) !important;
  color: white !important;
  padding: 24px 32px !important;
  position: relative;
  overflow: hidden;
}

.import-dialog-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 100px;
  height: 200%;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(15deg);
  transition: all 0.3s ease;
}

.import-dialog-header:hover::before {
  right: -5%;
}

.import-dialog-header .v-card-title {
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  margin: 0 !important;
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-dialog-header .v-card-title::before {
  content: '📊';
  font-size: 1.8rem;
}

/* Import dialog content */
.import-dialog-content {
  padding: 32px !important;
  background: linear-gradient(145deg, #fafafa 0%, #f5f5f5 100%);
}

/* Enhanced info alert */
.import-info-alert {
  border-radius: 12px !important;
  border: 1px solid rgba(33, 150, 243, 0.2) !important;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%) !important;
  padding: 20px !important;
  margin-bottom: 24px !important;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.1) !important;
}

.import-info-alert .v-alert__content {
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
}

.import-info-alert strong {
  color: #1976d2 !important;
  font-weight: 700 !important;
}

.import-info-alert a {
  color: #1976d2 !important;
  text-decoration: none !important;
  font-weight: 600 !important;
  padding: 4px 8px !important;
  border-radius: 6px !important;
  background: rgba(25, 118, 210, 0.1) !important;
  transition: all 0.2s ease !important;
}

.import-info-alert a:hover {
  background: rgba(25, 118, 210, 0.2) !important;
  transform: translateY(-1px);
}

/* Enhanced error alert */
.import-error-alert {
  border-radius: 12px !important;
  background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%) !important;
  border: 1px solid rgba(244, 67, 54, 0.2) !important;
  margin-bottom: 20px !important;
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.1) !important;
}

.import-error-alert ul {
  margin: 0 !important;
  padding-left: 20px !important;
}

.import-error-alert li {
  margin-bottom: 4px !important;
  color: #c62828 !important;
  font-weight: 500 !important;
}

/* Enhanced file input */
.import-file-input {
  margin-top: 24px !important;
}

.import-file-input .v-field {
  border-radius: 16px !important;
  border: 3px dashed rgba(76, 175, 80, 0.3) !important;
  background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e8 100%) !important;
  transition: all 0.3s ease !important;
  min-height: 80px !important;
  padding: 16px !important;
}

.import-file-input .v-field:hover {
  border-color: rgba(76, 175, 80, 0.5) !important;
  background: linear-gradient(135deg, #e8f5e8 0%, #dcedc8 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.15) !important;
}

.import-file-input .v-field--focused {
  border-color: #4caf50 !important;
  background: white !important;
  box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.1) !important;
}

.import-file-input .v-field__input {
  padding-top: 20px !important;
  font-weight: 600 !important;
  color: #2e7d32 !important;
}

.import-file-input .v-field__prepend-inner {
  padding-right: 16px !important;
}

.import-file-input .v-field__prepend-inner .v-icon {
  color: #4caf50 !important;
  font-size: 1.5rem !important;
}

/* Dialog actions */
.import-dialog-actions {
  padding: 24px 32px !important;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.import-dialog-actions .v-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  padding: 12px 24px !important;
}

.import-upload-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
}

.import-upload-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
}

.import-cancel-btn {
  color: #666 !important;
  background: rgba(0, 0, 0, 0.04) !important;
}

.import-cancel-btn:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #333 !important;
}

/* ============================================
   ENHANCED FORM DIALOG STYLING
   ============================================ */

.subscription-form-dialog {
  border-radius: 24px !important;
  overflow: hidden;
  max-width: 900px !important;
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.15),
    0 15px 40px rgba(0, 0, 0, 0.1) !important;
}

/* Enhanced form header with better gradient and animations */
.enhanced-form-header {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #4338ca 100%) !important;
  position: relative;
  overflow: hidden;
  padding: 32px !important;
}

.enhanced-form-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200%;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  transform: rotate(25deg);
  transition: all 0.5s ease;
}

.enhanced-form-header:hover::before {
  right: -10%;
  transform: rotate(25deg) scale(1.1);
}

.enhanced-form-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.3) 20%,
    rgba(255, 255, 255, 0.5) 50%,
    rgba(255, 255, 255, 0.3) 80%,
    rgba(255, 255, 255, 0) 100%
  );
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.enhanced-form-header .form-header-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 20px;
}

.enhanced-form-header .form-icon-wrapper {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.enhanced-form-header .form-icon-wrapper .v-avatar {
  background: white !important;
  color: #6366f1 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Form Title di Dialog Header */
.enhanced-form-header .form-title {
  color: white;
  font-size: 2rem !important;
  font-weight: 800 !important;
  margin-bottom: 8px !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  letter-spacing: 0.5px !important;
  line-height: 1.2 !important;
}

.enhanced-form-header .form-subtitle {
  line-height: 1.4; /* Perbaiki juga line-height untuk subjudul */
}

.enhanced-form-header .form-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem !important;
  font-weight: 400 !important;
  margin: 0 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  line-height: 1.4 !important;
  letter-spacing: 0.2px !important;
}

/* Enhanced step indicator */
.enhanced-step-indicator {
  padding: 32px 0 !important;
  position: relative;
}

.enhanced-step-indicator::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 20%;
  right: 20%;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%,
    rgba(99, 102, 241, 0.2) 25%,
    rgba(99, 102, 241, 0.6) 50%,
    rgba(99, 102, 241, 0.2) 75%,
    transparent 100%
  );
  transform: translateY(-50%);
}

.enhanced-step-indicator .step-badge {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  color: white !important;
  padding: 12px 24px !important;
  border-radius: 50px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  letter-spacing: 0.5px !important;
  text-transform: none !important;
  border: 3px solid white !important;
  box-shadow: 
    0 6px 20px rgba(99, 102, 241, 0.3),
    0 0 0 4px rgba(99, 102, 241, 0.1) !important;
  position: relative;
  z-index: 2;
}


/* Tablet and small desktop */
@media (max-width: 960px) {
  .add-subscription-btn {
    font-size: 0.95rem !important;
    padding: 12px 24px !important;
    min-height: 44px !important;
  }

  .enhanced-form-header .form-title {
    font-size: 1.75rem !important;
  }

  .enhanced-form-header .form-subtitle {
    font-size: 1rem !important;
  }

  .enhanced-section-header .section-title {
    font-size: 1.1rem !important;
    letter-spacing: 0.6px !important;
  }
}

/* Mobile phones */
@media (max-width: 600px) {
  .add-subscription-btn {
    font-size: 0.9rem !important;
    padding: 12px 20px !important;
    min-height: 42px !important;
    letter-spacing: 0.2px !important;
  }

  .enhanced-form-header .form-title {
    font-size: 1.5rem !important;
    line-height: 1.3 !important;
    word-break: break-word;
    text-align: center;
  }

  .enhanced-form-header .form-subtitle {
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    text-align: center;
  }

  .enhanced-section-header .section-title {
    font-size: 1rem !important;
    letter-spacing: 0.4px !important;
  }

  .enhanced-save-btn {
    font-size: 0.95rem !important;
    padding: 12px 24px !important;
    min-height: 44px !important;
  }

  .step-badge {
    font-size: 0.85rem !important;
    padding: 10px 20px !important;
    letter-spacing: 0.3px !important;
  }
}

/* Extra small phones */
@media (max-width: 480px) {
  .add-subscription-btn {
    font-size: 0.85rem !important;
    padding: 10px 16px !important;
    min-height: 40px !important;
  }

  .enhanced-form-header .form-title {
    font-size: 1.3rem !important;
    line-height: 1.2 !important;
  }

  .enhanced-form-header .form-subtitle {
    font-size: 0.9rem !important;
  }

  .enhanced-save-btn {
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    min-height: 42px !important;
  }
}

/* ============================================
   TEXT CONTRAST AND READABILITY ENHANCEMENTS
   ============================================ */

/* Ensure proper contrast for all text */
.add-subscription-btn,
.enhanced-save-btn,
.step-badge {
  color: white !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
}

/* Loading state text visibility */
.add-subscription-btn[loading="true"] .v-btn__content,
.enhanced-save-btn[loading="true"] .v-btn__content {
  opacity: 0.8;
}

/* Disabled state text */
.add-subscription-btn:disabled .v-btn__content,
.enhanced-save-btn:disabled .v-btn__content {
  opacity: 0.6;
  color: rgba(255, 255, 255, 0.7) !important;
}

/* Enhanced form sections */
.enhanced-form-section {
  margin-bottom: 40px !important;
  position: relative;
}

.enhanced-section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px !important;
  padding: 16px 0;
  position: relative;
}

.enhanced-section-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 40px;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    rgba(99, 102, 241, 0.3) 0%,
    rgba(99, 102, 241, 0.1) 50%,
    transparent 100%
  );
}

/* Dark mode section title */
.v-theme--dark .enhanced-section-header .section-title {
  color: #e5e7eb !important;
}

.enhanced-section-header .section-title {
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.8px !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.enhanced-section-header .section-title {
  font-size: 1.3rem !important;
  font-weight: 700 !important;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Enhanced section cards */
.enhanced-section-card {
  border-radius: 20px !important;
  padding: 32px !important;
  border: 1px solid rgba(99, 102, 241, 0.1) !important;
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.9) 0%,
    rgba(249, 250, 251, 0.8) 100%
  ) !important;
  backdrop-filter: blur(10px);
  box-shadow: 
    0 10px 30px rgba(0, 0, 0, 0.05),
    0 4px 10px rgba(99, 102, 241, 0.1) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
}

.enhanced-section-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1, #4f46e5, #4338ca);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.enhanced-section-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.1),
    0 8px 20px rgba(99, 102, 241, 0.2) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
}

.enhanced-section-card:hover::before {
  opacity: 1;
}

/* Enhanced form fields */
.enhanced-form-field .v-field {
  border-radius: 16px !important;
  background: rgba(255, 255, 255, 0.8) !important;
  border: 2px solid rgba(99, 102, 241, 0.1) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
}

.enhanced-form-field .v-field:hover {
  background: rgba(255, 255, 255, 0.95) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.1) !important;
}

.enhanced-form-field .v-field--focused {
  background: white !important;
  border-color: #6366f1 !important;
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(99, 102, 241, 0.15),
    0 0 0 4px rgba(99, 102, 241, 0.1) !important;
}

.enhanced-form-field .v-field__input {
  padding: 16px 20px !important;
  font-size: 1rem !important;
  font-weight: 500 !important;
}

.enhanced-form-field .v-field__prepend-inner .v-icon {
  color: rgba(99, 102, 241, 0.7) !important;
  font-size: 1.2rem !important;
  margin-right: 12px !important;
}

.enhanced-form-field .v-field--focused .v-field__prepend-inner .v-icon {
  color: #6366f1 !important;
  transform: scale(1.1);
}

/* Special styling for price field */
.enhanced-price-field .v-field {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
  border-color: rgba(14, 165, 233, 0.3) !important;
  font-weight: 700 !important;
}

.enhanced-price-field .v-field:hover {
  border-color: rgba(14, 165, 233, 0.5) !important;
}

.enhanced-price-field .v-field--focused {
  border-color: #0ea5e9 !important;
  box-shadow: 
    0 8px 25px rgba(14, 165, 233, 0.15),
    0 0 0 4px rgba(14, 165, 233, 0.1) !important;
}

.enhanced-price-field .v-field__input {
  color: #0369a1 !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
}

/* Enhanced action footer */
.enhanced-action-footer {
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding: 32px !important;
}

.enhanced-action-footer .action-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
}

.enhanced-cancel-btn {
  color: #6b7280 !important;
  background: rgba(107, 114, 128, 0.1) !important;
  border: 1px solid rgba(107, 114, 128, 0.2) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  padding: 14px 24px !important;
  transition: all 0.3s ease !important;
}

.enhanced-cancel-btn:hover {
  background: rgba(107, 114, 128, 0.15) !important;
  color: #374151 !important;
  border-color: rgba(107, 114, 128, 0.3) !important;
}

.enhanced-save-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  padding: 14px 32px !important;
  font-size: 1rem !important;
  letter-spacing: 0.3px !important;
  box-shadow: 
    0 6px 20px rgba(99, 102, 241, 0.3),
    0 3px 10px rgba(99, 102, 241, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
  min-height: 48px !important;
}

.enhanced-save-btn:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(99, 102, 241, 0.4),
    0 5px 15px rgba(99, 102, 241, 0.3) !important;
}

.enhanced-save-btn:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

.enhanced-save-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: width 0.6s ease, height 0.6s ease;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.enhanced-save-btn:active::before {
  width: 300px;
  height: 300px;
}

.enhanced-save-btn .v-btn__content {
  position: relative;
  z-index: 1;
  font-weight: 700 !important;
  letter-spacing: 0.3px !important;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ============================================
   RESPONSIVE ENHANCEMENTS
   ============================================ */

@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .import-btn,
  .export-btn,
  .add-subscription-btn {
    width: 100%;
    justify-content: center;
  }
  
  .subscription-form-dialog {
    margin: 16px !important;
    max-width: calc(100vw - 32px) !important;
    border-radius: 16px !important;
  }
  
  .enhanced-form-header {
    padding: 24px !important;
  }
  
  .enhanced-form-header .form-title {
  font-size: 1.4rem !important;  /* Sedikit kita kecilkan lagi agar pas */
  line-height: 1.3 !important; /* Kita rapatkan jarak antar baris */
  word-break: break-word;     /* Memastikan kata panjang tidak akan keluar dari container */
  }
  
  .enhanced-section-card {
    padding: 20px !important;
    margin: 0 -4px !important;
  }
  
  .enhanced-action-footer {
    padding: 20px !important;
  }
  
  .enhanced-action-footer .action-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .enhanced-cancel-btn,
  .enhanced-save-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .import-dialog-content {
    padding: 20px !important;
  }
  
  .import-dialog-header {
    padding: 20px !important;
  }
  
  .import-dialog-actions {
    padding: 16px 20px !important;
    flex-direction: column;
    gap: 12px;
  }
  
  .import-upload-btn,
  .import-cancel-btn {
    width: 100%;
  }
}

/* Page Header Adjustments */
.page-header {
  flex-wrap: wrap;
  gap: 1rem;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

/* Filter Card Layout */
/* Filter Card Layout */
.filter-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.filter-item {
  flex-grow: 1;
  flex-basis: 200px;
}

/* Data Table Wrapper */
.table-responsive-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.v-data-table {
  min-width: 1200px;
}

/* --- MOBILE OVERRIDES (Following DefaultLayout.vue pattern) --- */

/* Medium screens and down (tablets, large phones) */
@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1.5rem;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions > .v-btn {
    width: 100%;
    justify-content: center;
  }

  /* FIX: Refined filter container for mobile */
  .filter-container {
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
    gap: 12px; /* Reduced gap for a tighter look */
  }

  /* FIX: Specific styling for the reset button on mobile */
  .reset-filter-btn {
    align-self: center; /* Center the button */
    margin-top: 8px; /* Add some space above it */
    flex-grow: 0; /* Prevent it from growing */
    width: auto; /* Let it size to its content */
    padding: 0 24px !important;
  }

  .enhanced-form-header {
    padding: 24px !important;
  }

  .enhanced-form-header .form-title {
    font-size: 1.75rem !important;
  }
  
  /* FIX: Reduced margin between form sections on mobile */
  .enhanced-form-section {
    margin-bottom: 24px !important;
  }
}

/* Small screens (standard mobile phones) */
@media (max-width: 600px) {
  .text-h4 {
    font-size: 1.5rem !important;
  }

  .v-dialog .v-card {
    margin: 16px !important;
    max-width: calc(100vw - 32px) !important;
  }

  .subscription-form-dialog .v-card-text {
    padding: 0 !important;
  }
  
  .subscription-form-dialog .v-container {
    padding: 24px 16px !important;
  }

  .enhanced-section-card {
    padding: 16px !important;
  }

  .enhanced-action-footer {
    padding: 16px !important;
  }
  
  .enhanced-action-footer .action-buttons {
    flex-direction: column;
    width: 100%;
    gap: 12px;
  }
  
  .enhanced-cancel-btn,
  .enhanced-save-btn {
    width: 100%;
    justify-content: center;
  }

  .delete-header {
    padding: 24px 16px !important;
  }
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

.selection-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.15);
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

.v-data-table {
  --v-data-table-header-height: 60px;
}

/* Enhanced Form Styling */
.form-header-gradient {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%);
  position: relative;
  overflow: hidden;
}

.form-header-decoration {
  position: absolute;
  top: 0;
  right: -50px;
  width: 100px;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  transform: skewX(-15deg);
}

.form-icon-container {
  position: relative;
  z-index: 2;
}

.step-indicator {
  position: relative;
}

.step-line {
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #1976d2 50%, transparent 100%);
  flex: 1;
  opacity: 0.3;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section-header {
  display: flex;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(25, 118, 210, 0.1);
}

.enhanced-field {
  margin-bottom: 1rem;
}

.enhanced-field .v-field {
  background-color: rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.enhanced-field .v-field:hover {
  background-color: rgba(255, 255, 255, 0.95) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.enhanced-field .v-field--focused {
  background-color: white !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.15);
}

.price-field .v-field {
  background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%) !important;
  border: 2px solid rgba(76, 175, 80, 0.2) !important;
}

.action-footer {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.save-button {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3) !important;
  transition: all 0.3s ease !important;
}

.save-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4) !important;
}

.delete-header {
  background: linear-gradient(135deg, #fafafa 0%, #f8f8f8 100%);
}

/* Custom scrollbar for dialog */
.v-overlay__content::-webkit-scrollbar {
  width: 6px;
}

.v-overlay__content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.v-overlay__content::-webkit-scrollbar-thumb {
  background: rgba(25, 118, 210, 0.3);
  border-radius: 3px;
}

.v-overlay__content::-webkit-scrollbar-thumb:hover {
  background: rgba(25, 118, 210, 0.5);
}

/* Smooth animations */
.v-dialog > .v-overlay__content {
  animation: dialogSlideIn 0.3s ease-out;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced card styling */
.v-card.rounded-xl {
  border-radius: 16px !important;
  overflow: hidden;
}

/* Field focus effects */
.enhanced-field .v-input--focused .v-field__outline {
  border-color: #1976d2 !important;
  border-width: 2px !important;
}

/* Improved spacing and typography */
.form-section .v-card {
  transition: all 0.3s ease;
}

.form-section .v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
}

/* Enhanced button styles */
.v-btn.text-none {
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px;
}

/* Loading animation enhancement */
.v-btn--loading {
  pointer-events: none;
}

.v-btn--loading .v-btn__overlay {
  background: rgba(255, 255, 255, 0.1);
}

/* Responsive improvements */
@media (max-width: 768px) {
  .form-header-gradient {
    padding: 1.5rem !important;
  }
  
  .form-header-gradient h2 {
    font-size: 1.5rem !important;
  }
  
  .v-dialog > .v-overlay__content {
    margin: 1rem !important;
    max-width: calc(100vw - 2rem) !important;
  }
  
  .step-indicator {
    margin-bottom: 1.5rem !important;
  }
  
  .form-section {
    margin-bottom: 1.5rem !important;
  }
}
</style>