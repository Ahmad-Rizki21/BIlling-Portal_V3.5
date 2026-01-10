<template>
  <v-container fluid class="edit-langganan-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-pattern"></div>
      <div class="header-content">
        <v-btn
          icon="mdi-arrow-left"
          variant="text"
          color="white"
          class="back-btn glass-btn"
          @click="router.go(-1)"
        ></v-btn>
        
        <div class="header-info ms-4">
          <div class="header-badge mb-2">
            <v-icon size="14" start>mdi-pencil</v-icon>
            EDIT MODE
          </div>
          <h1 class="header-title">Edit Langganan</h1>
          <p class="header-subtitle">Perbarui informasi dan status langganan pelanggan</p>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="content-wrapper">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <v-progress-circular indeterminate color="primary" size="64" width="6"></v-progress-circular>
        <p class="mt-4 text-h6 text-medium-emphasis">Memuat data langganan...</p>
      </div>

      <!-- Error State -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mb-6 rounded-xl"
        border="start"
        prominent
      >
        <template v-slot:prepend>
          <div class="alert-icon-wrapper error">
            <v-icon color="error">mdi-alert-circle</v-icon>
          </div>
        </template>
        <div class="text-h6 font-weight-bold mb-1">Terjadi Kesalahan</div>
        <div class="text-body-1">{{ error }}</div>
        <template v-slot:append>
          <v-btn color="error" variant="flat" @click="fetchLanggananDetail" class="rounded-lg px-4">
            Coba Lagi
          </v-btn>
        </template>
      </v-alert>

      <!-- Edit Form -->
      <div v-else-if="editedItem" class="form-container">
        <v-row>
          <!-- Left Column: Main Form -->
          <v-col cols="12" lg="9">
            <v-form ref="formRef" v-model="formValid" lazy-validation>
              
              <!-- Customer Profile Card -->
              <v-card class="mb-6 rounded-xl overflow-hidden" elevation="2" border>
                <div class="customer-card-header">
                  <v-icon size="24" class="me-3">mdi-account-circle</v-icon>
                  <span class="text-subtitle-1 font-weight-bold">Informasi Pelanggan</span>
                </div>
                <v-card-text class="pa-6">
                  <div class="d-flex align-start gap-4">
                    <v-avatar color="primary" size="72" class="elevation-2">
                      <span class="text-h4 font-weight-bold text-white">
                        {{ getPelangganName(editedItem.pelanggan_id).charAt(0).toUpperCase() }}
                      </span>
                    </v-avatar>
                    
                    <div class="flex-grow-1 min-w-0">
                      <h3 class="text-h6 font-weight-bold mb-2">
                        {{ getPelangganName(editedItem.pelanggan_id) }}
                      </h3>
                      
                      <div class="d-flex flex-wrap gap-2 mb-3">
                        <v-chip size="small" color="primary" variant="tonal" class="font-weight-medium">
                          <v-icon start size="16">mdi-identifier</v-icon>
                          ID: {{ editedItem.pelanggan_id }}
                        </v-chip>
                        <v-chip size="small" color="success" variant="tonal" class="font-weight-medium">
                          <v-icon start size="16">mdi-phone</v-icon>
                          {{ getPelangganPhone(editedItem.pelanggan_id) }}
                        </v-chip>
                      </div>
                      
                      <div class="d-flex align-start">
                        <v-icon size="18" class="me-2 mt-1 text-medium-emphasis">mdi-map-marker</v-icon>
                        <span class="text-body-2 text-medium-emphasis" style="line-height: 1.6;">
                          {{ getPelangganAddress(editedItem.pelanggan_id) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </v-card-text>
              </v-card>

              <!-- Package & Payment -->
              <v-card class="mb-6 rounded-xl" elevation="0" border>
                <v-card-title class="d-flex align-center user-select-none px-6 pt-6 pb-2">
                  <v-icon color="primary" class="me-3">mdi-wifi-star</v-icon>
                  <span class="text-h6 font-weight-bold">Paket & Pembayaran</span>
                </v-card-title>
                
                <v-card-text class="px-6 pb-6">
                  <v-row>
                    <v-col cols="12">
                       <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">PAKET LAYANAN</label>
                       <v-select
                        v-model="editedItem.paket_layanan_id"
                        :items="filteredPaketLayanan"
                        :loading="paketLoading"
                        item-title="nama_paket"
                        item-value="id"
                        variant="outlined"
                        placeholder="Pilih paket layanan"
                        color="primary"
                        :rules="[rules.required]"
                        hide-details="auto"
                        class="mb-4 custom-select"
                        readonly
                        disabled
                      >
                         <template v-slot:selection="{ item }">
                           <div class="d-flex align-center" style="width: 100%">
                              <span class="font-weight-medium text-truncate">{{ item.raw.nama_paket || 'Paket Tidak Dikenal' }}</span>
                              <v-spacer></v-spacer>
                              <v-chip v-if="item.raw.kecepatan" size="x-small" color="success" variant="flat" class="font-weight-bold ms-2">
                                {{ item.raw.kecepatan }} Mbps
                              </v-chip>
                           </div>
                         </template>
                         <template v-slot:item="{ props, item }">
                            <v-list-item v-bind="props" rounded="lg" class="mb-1">
                               <template v-slot:append>
                                  <span class="text-primary font-weight-bold">{{ formatCurrency(item.raw.harga) }}</span>
                               </template>
                               <v-list-item-subtitle class="mt-1">
                                  <v-chip size="x-small" color="success" variant="tonal">{{ item.raw.kecepatan }} Mbps</v-chip>
                               </v-list-item-subtitle>
                            </v-list-item>
                         </template>
                      </v-select>
                    </v-col>

                    <v-col cols="12" md="6">
                       <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">METODE PEMBAYARAN</label>
                       <v-select
                        v-model="editedItem.metode_pembayaran"
                        :items="[
                          { title: 'Otomatis (Bulanan)', value: 'Otomatis', icon: 'mdi-calendar-sync' },
                          { title: 'Prorate (Proporsional)', value: 'Prorate', icon: 'mdi-calculator' }
                        ]"
                        variant="outlined"
                        color="primary"
                        hide-details="auto"
                        class="custom-select"
                      >
                         <template v-slot:item="{ props, item }">
                            <v-list-item v-bind="props" rounded="lg">
                               <template v-slot:prepend>
                                  <v-icon color="primary" class="me-2">{{ item.raw.icon }}</v-icon>
                               </template>
                            </v-list-item>
                         </template>
                      </v-select>
                    </v-col>
                    
                    <v-col cols="12" md="6" v-if="editedItem.metode_pembayaran === 'Prorate'">
                       <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">TANGGAL MULAI</label>
                       <v-text-field
                          v-model="editedItem.tgl_mulai_langganan"
                          type="date"
                          variant="outlined"
                          color="primary"
                          hide-details="auto"
                       ></v-text-field>
                    </v-col>
                    
                    <v-col cols="12" v-if="editedItem.metode_pembayaran === 'Prorate'">
                      <v-checkbox
                        v-model="isProratePlusFull"
                        color="primary"
                        hide-details
                        density="compact"
                      >
                        <template v-slot:label>
                          <span class="text-body-2 font-weight-medium">Sertakan tagihan penuh bulan depan</span>
                        </template>
                      </v-checkbox>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- Status & Schedule -->
              <v-card class="mb-6 rounded-xl" elevation="0" border>
                <v-card-title class="d-flex align-center user-select-none px-6 pt-6 pb-2">
                  <v-icon color="primary" class="me-3">mdi-check-network</v-icon>
                  <span class="text-h6 font-weight-bold">Status & Jadwal</span>
                </v-card-title>
                
                <v-card-text class="px-6 pb-6">
                  <v-row>
                    <v-col cols="12" md="6">
                      <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">STATUS LANGGANAN</label>
                      <v-select
                        v-model="editedItem.status"
                        :items="['Aktif', 'Suspended', 'Berhenti']"
                        variant="outlined"
                        color="primary"
                        :rules="[rules.required]"
                        hide-details="auto"
                      >
                         <template v-slot:selection="{ item }">
                            <v-chip 
                              :color="getStatusColor(item.raw)" 
                              variant="elevated" 
                              size="small" 
                              class="font-weight-bold uppercase"
                            >
                               {{ item.raw }}
                            </v-chip>
                         </template>
                      </v-select>
                    </v-col>
                    
                    <v-col cols="12" md="6">
                      <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">JATUH TEMPO</label>
                      <v-text-field
                        v-model="editedItem.tgl_jatuh_tempo"
                        type="date"
                        variant="outlined"
                        color="primary"
                        :rules="[rules.required]"
                        hide-details="auto"
                      ></v-text-field>
                    </v-col>
                    
                    <v-col cols="12">
                      <v-expand-transition>
                        <div v-if="editedItem.status === 'Aktif' || editedItem.status === 'Berhenti'">
                          <label class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">
                             STATUS MODEM <span class="text-error">*</span>
                          </label>
                          <v-select
                            v-model="editedItem.status_modem"
                            :items="getStatusModemOptions(editedItem.status || '')"
                            item-title="title"
                            item-value="value"
                            variant="outlined"
                            color="primary"
                            hide-details="auto"
                            placeholder="Pilih kondisi modem"
                          ></v-select>
                        </div>
                      </v-expand-transition>
                    </v-col>
                    
                    <v-col cols="12">
                       <v-expand-transition>
                         <div v-if="editedItem.status === 'Berhenti'">
                           <div class="d-flex align-center mb-2 mt-2">
                              <label class="text-caption font-weight-bold text-medium-emphasis">ALASAN BERHENTI</label>
                           </div>
                           <v-textarea
                             v-model="editedItem.alasan_berhenti"
                             variant="outlined"
                             rows="3"
                             auto-grow
                             color="error"
                             placeholder="Contoh: Pindah rumah, tidak puas dengan layanan..."
                             hide-details="auto"
                             class="mb-2"
                           ></v-textarea>
                         </div>
                       </v-expand-transition>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

            </v-form>
          </v-col>

          <!-- Right Column: Summary Sticky -->
          <v-col cols="12" lg="3">
            <div class="sticky-summary">
              <!-- Price Receipt Card -->
              <v-card class="rounded-xl overflow-hidden pricing-card" elevation="4">
                <div class="receipt-header">
                  <div class="text-overline text-white opacity-80 mb-1">TOTAL ESTIMASI</div>
                  <div class="text-h4 font-weight-bold text-white receipt-amount">
                    {{ formatCurrency(editedItem.harga_awal) }}
                  </div>
                  <div class="text-caption text-white opacity-70 mt-1">
                    {{ editedItem.metode_pembayaran === 'Otomatis' ? '/ bulan' : 'tagihan pertama' }}
                  </div>
                </div>
                
                <!-- Prorate Details -->
                <div class="px-6 py-4 bg-surface" v-if="editedItem.metode_pembayaran === 'Prorate' && isProratePlusFull && hargaProrate > 0">
                   <div class="d-flex justify-space-between mb-2 text-body-2">
                      <span class="text-medium-emphasis">Biaya Prorate</span>
                      <span class="font-weight-medium">{{ formatCurrency(hargaProrate) }}</span>
                   </div>
                   <div class="d-flex justify-space-between text-body-2">
                      <span class="text-medium-emphasis">Bulan Depan</span>
                      <span class="font-weight-medium">{{ formatCurrency(hargaNormal) }}</span>
                   </div>
                   <v-divider class="my-3 border-dashed"></v-divider>
                   <div class="d-flex align-top gap-2">
                      <v-icon size="16" color="info" class="mt-1">mdi-information</v-icon>
                      <span class="text-caption text-medium-emphasis">Tagihan mencakup sisa hari bulan ini ditambah satu bulan penuh berikutnya.</span>
                   </div>
                </div>

                <v-divider></v-divider>
                
                <v-card-actions class="pa-4 bg-surface">
                   <v-btn
                      block
                      color="primary"
                      size="large"
                      variant="elevated"
                      height="48"
                      @click="saveLangganan"
                      :loading="saving"
                      :disabled="!isFormValid"
                      class="font-weight-bold text-none rounded-lg"
                   >
                      <v-icon start>mdi-content-save-check</v-icon>
                      Simpan Perubahan
                   </v-btn>
                </v-card-actions>
              </v-card>
              
              <v-btn
                block
                variant="text"
                color="medium-emphasis"
                class="mt-4 text-none"
                @click="router.go(-1)"
              >
                Batalkan Perubahan
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </div>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '@/services/api';

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
  tgl_berhenti?: string | null;
  alasan_berhenti?: string | null;
  status_modem?: string | null;
  riwayat_tgl_berhenti?: string | null;
}

interface PelangganData {
  id: number;
  nama: string;
  alamat: string;
  no_telp?: string;
}

interface PelangganSelectItem {
  id: number;
  nama: string;
  id_brand: string;
  alamat?: string;
  no_telp?: string;
}

interface PaketLayananSelectItem {
  id: number;
  nama_paket: string;
  kecepatan: number;
  harga: number;
  id_brand: string;
}

// --- Router ---
const route = useRoute();
const router = useRouter();
const langgananId = Number(route.params.id);

// --- State ---
const loading = ref(true);
const error = ref<string | null>(null);
const saving = ref(false);
const formValid = ref(false);
const formRef = ref();
const paketLoading = ref(false);

const langgananData = ref<Langganan | null>(null);
const pelangganSelectList = ref<PelangganSelectItem[]>([]);
const paketLayananSelectList = ref<PaketLayananSelectItem[]>([]);
const filteredPaketLayanan = ref<PaketLayananSelectItem[]>([]);

const editedItem = ref<Partial<Langganan>>({});
const isProratePlusFull = ref<boolean>(false);
const hargaProrate = ref<number>(0);
const hargaNormal = ref<number>(0);

// --- Validation Rules ---
const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi',
};

// --- Computed Properties ---
const isFormValid = computed(() => !!(editedItem.value.pelanggan_id && editedItem.value.paket_layanan_id && editedItem.value.status));

// --- Watchers ---
watch(() => editedItem.value.pelanggan_id, async (newPelangganId) => {
  if (newPelangganId && paketLayananSelectList.value.length > 0) {
    await filterPaketForCustomer(newPelangganId);
  }
});

// --- Lifecycle ---
onMounted(async () => {
  await fetchLanggananDetail();
  await fetchPelangganForSelect();
  await fetchPaketLayananForSelect();

  // After all data is loaded, filter paket for the current customer
  if (editedItem.value.pelanggan_id) {
    await filterPaketForCustomer(editedItem.value.pelanggan_id);
  }
});

// --- API Methods ---
async function fetchLanggananDetail() {
  if (!langgananId) {
    error.value = 'ID langganan tidak valid';
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const response = await apiClient.get(`/langganan/${langgananId}`);
    langgananData.value = response.data;
    editedItem.value = { ...response.data };

    // Setelah data dimuat, filter paket layanan
    if (editedItem.value.pelanggan_id) {
      await filterPaketForCustomer(editedItem.value.pelanggan_id);
    }
  } catch (err) {
    console.error('Gagal mengambil detail langganan:', err);
    error.value = 'Gagal memuat data langganan. Silakan coba lagi.';
  } finally {
    loading.value = false;
  }
}

async function fetchPelangganForSelect() {
  try {
    const response = await apiClient.get<{ data: PelangganSelectItem[] }>('/pelanggan/?for_invoice_selection=true');
    if (response.data && Array.isArray(response.data.data)) {
      pelangganSelectList.value = response.data.data;
    }
  } catch (error) {
    console.error("Gagal mengambil data pelanggan untuk select:", error);
    pelangganSelectList.value = [];
  }
}

async function fetchPaketLayananForSelect() {
  paketLoading.value = true;
  try {
    const response = await apiClient.get<PaketLayananSelectItem[]>('/paket_layanan/');
    paketLayananSelectList.value = response.data;
  } catch (error: any) {
    console.error("Gagal mengambil data paket layanan untuk select:", error);
    paketLayananSelectList.value = [];
  } finally {
    paketLoading.value = false;
  }
}

async function filterPaketForCustomer(pelangganId: number) {
  paketLoading.value = true; // Set to true at start
  
  if (!pelangganId) {
    filteredPaketLayanan.value = [];
    paketLoading.value = false;
    return;
  }

  try {
    const response = await apiClient.get(`/pelanggan/${pelangganId}`);
    const pelangganDetail = response.data;

    if (!pelangganDetail || !pelangganDetail.id_brand || !pelangganDetail.layanan) {
      filteredPaketLayanan.value = [];
      paketLoading.value = false;
      return;
    }

    const customerBrandId = pelangganDetail.id_brand;

    filteredPaketLayanan.value = paketLayananSelectList.value.filter(
      paket => paket.id_brand === customerBrandId
    );

    // If no packages found for this brand, show all packages as fallback
    if (filteredPaketLayanan.value.length === 0) {
      filteredPaketLayanan.value = [...paketLayananSelectList.value];
    }
    
    // Ensure currently selected package is in the list (even if it doesn't match filter)
    const currentPaketId = editedItem.value.paket_layanan_id;
    if (currentPaketId && !filteredPaketLayanan.value.some(p => p.id === currentPaketId)) {
      const currentPaket = paketLayananSelectList.value.find(p => p.id === currentPaketId);
      if (currentPaket) {
        filteredPaketLayanan.value.push(currentPaket);
      }
    }
  } catch (error: any) {
    console.error("Gagal mengambil detail pelanggan:", error);
    filteredPaketLayanan.value = [...paketLayananSelectList.value]; // Show all on error
  } finally {
    paketLoading.value = false; // Always set to false
  }
}

// --- Price Calculation Watcher ---
watch(
  () => [
    editedItem.value.metode_pembayaran,
    editedItem.value.paket_layanan_id,
    editedItem.value.pelanggan_id,
    editedItem.value.tgl_mulai_langganan,
    isProratePlusFull.value
  ],
  async ([metode, paketId, pelangganId, tglMulai, proratePlus]) => {
    hargaProrate.value = 0;
    hargaNormal.value = 0;

    if (metode === 'Otomatis') {
      isProratePlusFull.value = false;
    }

    if (metode === 'Prorate' && !tglMulai) {
      return;
    }

    if (!paketId || !pelangganId) {
      if (editedItem.value.harga_awal) {
        editedItem.value.harga_awal = 0;
      }
      return;
    }

    let endpoint = '/langganan/calculate-price';
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

// --- Save Function ---
async function saveLangganan() {
  if (!isFormValid.value) return;

  saving.value = true;

  const updatePayload = {
    paket_layanan_id: editedItem.value.paket_layanan_id,
    status: editedItem.value.status,
    metode_pembayaran: editedItem.value.metode_pembayaran,
    tgl_jatuh_tempo: editedItem.value.tgl_jatuh_tempo,
    harga_awal: editedItem.value.harga_awal,
    tgl_berhenti: editedItem.value.tgl_berhenti || null,
    alasan_berhenti: editedItem.value.alasan_berhenti || null,
    status_modem: editedItem.value.status_modem || null
  };

  try {
    await apiClient.patch(`/langganan/${editedItem.value.id}`, updatePayload);

    // Success - redirect back to langganan list
    router.push('/langganan');
  } catch (error: any) {
    console.error("Gagal menyimpan data langganan:", error);
    error.value = 'Gagal menyimpan perubahan. Silakan coba lagi.';
  } finally {
    saving.value = false;
  }
}

// --- Helper Functions ---
function getPelangganName(pelangganId: number | undefined): string {
  // First try to get from editedItem.pelanggan (loaded subscription data)
  if (editedItem.value?.pelanggan?.nama) {
    return editedItem.value.pelanggan.nama;
  }
  
  // Fallback to pelangganSelectList
  if (!pelangganId) return 'N/A';
  if (!Array.isArray(pelangganSelectList.value)) {
    return `ID ${pelangganId}`;
  }
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.nama || `ID ${pelangganId}`;
}

function getPelangganPhone(pelangganId: number | undefined): string {
  // First try to get from editedItem.pelanggan
  if (editedItem.value?.pelanggan?.no_telp) {
    return editedItem.value.pelanggan.no_telp;
  }
  
  // Fallback to pelangganSelectList
  if (!pelangganId) return '-';
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.no_telp || '-';
}

function getPelangganAddress(pelangganId: number | undefined): string {
  // First try to get from editedItem.pelanggan
  if (editedItem.value?.pelanggan?.alamat) {
    return editedItem.value.pelanggan.alamat;
  }
  
  // Fallback to pelangganSelectList
  if (!pelangganId) return '-';
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.alamat || '-';
}

function getStatusColor(status: string | undefined): string {
  if (!status) return 'grey';
  switch (status) {
    case 'Aktif': return 'success';
    case 'Berhenti': return 'error';
    case 'Isolir': return 'warning';
    case 'Non-Aktif': return 'grey-darken-1';
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

function getStatusModemOptions(langgananStatus: string): Array<{title: string, value: string}> {
  if (langgananStatus === 'Aktif') {
    return [
      { title: '✅ Terpasang', value: 'Terpasang' },
      { title: '🔄 Replacement', value: 'Replacement' },
      { title: '❌ Rusak', value: 'Rusak' }
    ];
  } else if (langgananStatus === 'Berhenti') {
    return [
      { title: '✅ Diambil', value: 'Diambil' },
      { title: '❌ Hilang', value: 'Hilang' },
      { title: '💥 Rusak', value: 'Rusak' }
    ];
  }
  return [];
}
</script>

<style scoped>

/* Container */
.edit-langganan-container {
  min-height: 100vh;
  background: #f8fafc;
  padding: 0;
  padding-bottom: 2rem;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  color: white;
  padding: 2.5rem 2rem 2rem;
  margin-bottom: 0;
  position: relative;
  overflow: hidden;
}

@media (max-width: 768px) {
  .page-header {
    padding: 2rem 1rem 1.5rem;
  }
}

.header-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
}

.header-content {
  display: flex;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 1px;
  backdrop-filter: blur(4px);
}

.header-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0.5rem 0 0.25rem;
  line-height: 1.2;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-subtitle {
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
}

@media (max-width: 768px) {
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 0.875rem;
  }
}

/* Glass Button */
.glass-btn {
  background: rgba(255, 255, 255, 0.2) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.glass-btn:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  transform: translateY(-2px);
}

/* Content Wrapper */
.content-wrapper {
  width: 100%;
  margin-top: 3rem;
  padding: 0 2rem;
  position: relative;
  z-index: 2;
}

/* Mobile responsive padding */
@media (max-width: 768px) {
  .content-wrapper {
    padding: 0 1rem;
  }
}

/* Loading & Error */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.alert-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.alert-icon-wrapper.error {
  background: rgba(var(--v-theme-error), 0.1);
}

/* Customer Card */
.customer-card-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  color: white;
}


/* Custom Select & Inputs */
.custom-select :deep(.v-field),
.v-text-field :deep(.v-field),
.v-textarea :deep(.v-field) {
  border-radius: 12px;
  border-color: rgba(var(--v-theme-outline), 0.2);
  transition: all 0.3s ease;
}

.custom-select :deep(.v-field:hover),
.v-text-field :deep(.v-field:hover) {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 4px rgba(var(--v-theme-primary), 0.05);
}

.custom-select :deep(.v-field.v-field--focused),
.v-text-field :deep(.v-field.v-field--focused) {
  box-shadow: 0 0 0 4px rgba(var(--v-theme-primary), 0.1);
  border-color: rgb(var(--v-theme-primary));
}

/* Pricing Card */
.pricing-card {
  border: none;
  background: white;
}

.receipt-header {
  background: #1e293b;
  padding: 2rem 1.5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.receipt-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: radial-gradient(circle, transparent 50%, #1e293b 50%) 0 0/12px 12px repeat-x;
  transform: translateY(3px);
}

.receipt-amount {
  letter-spacing: -1px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Sticky Summary */
.sticky-summary {
  position: sticky;
  top: 2rem;
}

/* Dark Mode Adjustments */
.v-theme--dark .edit-langganan-container {
  background: #0f172a;
}

.v-theme--dark .loading-state {
  background: #1e293b;
}

.v-theme--dark .receipt-header {
  background: #0f172a;
}

.v-theme--dark .receipt-header::after {
  background: radial-gradient(circle, transparent 50%, #0f172a 50%) 0 0/12px 12px repeat-x;
}

/* Mobile Responsive */
@media (max-width: 960px) {
  .header-title {
    font-size: 2rem;
  }
  
  .sticky-summary {
    position: static;
    margin-top: 2rem;
  }
  
  .page-header {
    padding-bottom: 3rem;
  }
}

@media (max-width: 600px) {
  .header-title {
    font-size: 1.75rem;
  }
  
  .content-wrapper {
    padding: 0 1rem;
  }
  
  .customer-avatar {
    width: 64px !important;
    height: 64px !important;
    margin-top: -32px;
  }
}

/* Animation Enhancements */
.form-card {
  animation: slideInUp 0.6s ease-out;
}

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

.form-section {
  animation: fadeInUp 0.8s ease-out;
  animation-fill-mode: both;
}

.form-section:nth-child(1) { animation-delay: 0.1s; }
.form-section:nth-child(2) { animation-delay: 0.2s; }
.form-section:nth-child(3) { animation-delay: 0.3s; }

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

/* Focus States */
.select-field :deep(.v-field--focused),
.textarea-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

/* Loading States */
.select-field :deep(.v-progress-linear) {
  border-radius: 2px;
}

/* Scrollbar Styling */
.form-content {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.3) transparent;
}

.form-content::-webkit-scrollbar {
  width: 6px;
}

.form-content::-webkit-scrollbar-track {
  background: transparent;
}

.form-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
}

.form-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}
</style>