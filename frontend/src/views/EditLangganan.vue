<template>
  <v-container fluid class="edit-langganan-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <v-btn
          icon="mdi-arrow-left"
          variant="text"
          color="white"
          size="large"
          @click="$router.go(-1)"
          class="back-btn"
        ></v-btn>
        
        <div class="header-info">
          <div class="header-icon">
            <v-icon size="32" color="white">mdi-pencil</v-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">Edit Langganan</h1>
            <p class="header-subtitle">Perbarui informasi langganan pelanggan</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="content-wrapper">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <div class="loading-content">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            width="4"
          ></v-progress-circular>
          <p class="loading-text mt-4">Memuat data langganan...</p>
        </div>
      </div>

      <!-- Error State -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        prominent
        class="error-alert"
        border="start"
      >
        <template v-slot:prepend>
          <v-icon size="24">mdi-alert-circle</v-icon>
        </template>
        <v-alert-title class="text-h6 mb-2">Terjadi Kesalahan</v-alert-title>
        <div class="text-body-1">{{ error }}</div>
        <template v-slot:append>
          <v-btn
            color="error"
            variant="outlined"
            size="small"
            @click="fetchLanggananDetail"
            class="mt-2"
          >
            <v-icon start size="18">mdi-refresh</v-icon>
            Coba Lagi
          </v-btn>
        </template>
      </v-alert>

      <!-- Edit Form -->
      <div v-else-if="editedItem" class="form-wrapper">
        <v-card class="form-card" elevation="0" border>
          <v-card-text class="form-content">
            <v-form ref="formRef" v-model="formValid" lazy-validation>
              
              <!-- Customer Information Section -->
              <div class="form-section">
                <div class="section-header">
                  <div class="section-icon">
                    <v-icon color="primary" size="20">mdi-account</v-icon>
                  </div>
                  <h3 class="section-title">Informasi Pelanggan</h3>
                </div>

                <div class="field-group">
                  <label class="field-label">
                    Pelanggan
                    <span class="required-indicator">*</span>
                  </label>
                  <v-text-field
                    :model-value="getPelangganName(editedItem.pelanggan_id)"
                    variant="outlined"
                    prepend-inner-icon="mdi-account"
                    readonly
                    density="comfortable"
                    hide-details="auto"
                    bg-color="primary-lighten-5"
                    class="readonly-field"
                  ></v-text-field>
                </div>
              </div>

              <!-- Package and Payment Section -->
              <div class="form-section">
                <div class="section-header">
                  <div class="section-icon">
                    <v-icon color="primary" size="20">mdi-wifi</v-icon>
                  </div>
                  <h3 class="section-title">Paket & Pembayaran</h3>
                </div>

                <v-row class="field-row">
                  <v-col cols="12" lg="6" md="6">
                    <div class="field-group">
                      <label class="field-label">
                        Paket Layanan
                        <span class="required-indicator">*</span>
                      </label>
                      <v-select
                        v-model="editedItem.paket_layanan_id"
                        :items="filteredPaketLayanan"
                        :loading="paketLoading"
                        item-title="nama_paket"
                        item-value="id"
                        placeholder="Pilih paket layanan"
                        variant="outlined"
                        prepend-inner-icon="mdi-wifi-star"
                        :rules="[rules.required]"
                        density="comfortable"
                        hide-details="auto"
                        class="select-field"
                      >
                        <template v-slot:item="{ props, item }">
                          <v-list-item v-bind="props" class="package-item">
                            <template v-slot:prepend>
                              <v-avatar color="primary" size="36" class="package-avatar">
                                <v-icon color="white" size="18">mdi-wifi</v-icon>
                              </v-avatar>
                            </template>
                            <v-list-item-title class="package-name">{{ item.raw.nama_paket }}</v-list-item-title>
                            <v-list-item-subtitle class="package-details">{{ item.raw.kecepatan }} Mbps - {{ formatCurrency(item.raw.harga) }}</v-list-item-subtitle>
                          </v-list-item>
                        </template>
                      </v-select>
                    </div>
                  </v-col>

                  <v-col cols="12" lg="6" md="6">
                    <div class="field-group">
                      <label class="field-label">
                        Metode Pembayaran
                        <span class="required-indicator">*</span>
                      </label>
                      <v-select
                        v-model="editedItem.metode_pembayaran"
                        :items="[
                          { title: 'Otomatis (Bulanan)', value: 'Otomatis' },
                          { title: 'Prorate (Proporsional)', value: 'Prorate' }
                        ]"
                        variant="outlined"
                        prepend-inner-icon="mdi-cash-multiple"
                        density="comfortable"
                        hide-details="auto"
                        class="select-field"
                      ></v-select>
                    </div>
                  </v-col>
                </v-row>

                <!-- Pricing Display -->
                <div v-if="editedItem.metode_pembayaran === 'Otomatis'" class="pricing-section">
                  <div class="field-group">
                    <label class="field-label">Total Harga Bulanan</label>
                    <v-text-field
                      :model-value="formatCurrency(editedItem.harga_awal)"
                      variant="outlined"
                      prepend-inner-icon="mdi-currency-usd"
                      readonly
                      density="comfortable"
                      hide-details="auto"
                      bg-color="success-lighten-5"
                      class="price-field"
                    ></v-text-field>
                  </div>
                </div>

                <!-- Prorate Options -->
                <template v-if="editedItem.metode_pembayaran === 'Prorate'">
                  <v-row class="field-row">
                    <v-col cols="12" lg="6" md="6">
                      <div class="field-group">
                        <label class="field-label">Tanggal Mulai Langganan</label>
                        <v-text-field
                          v-model="editedItem.tgl_mulai_langganan"
                          type="date"
                          variant="outlined"
                          prepend-inner-icon="mdi-calendar-start"
                          density="comfortable"
                          hide-details="auto"
                        ></v-text-field>
                      </div>
                    </v-col>

                    <v-col cols="12" lg="6" md="6" class="d-flex align-center">
                      <div class="switch-group">
                        <v-switch
                          v-model="isProratePlusFull"
                          color="primary"
                          label="Sertakan tagihan penuh bulan depan"
                          inset
                          hide-details
                          density="comfortable"
                        ></v-switch>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Prorate Pricing Info -->
                  <div class="pricing-section">
                    <v-alert
                      v-if="isProratePlusFull && hargaProrate > 0"
                      variant="tonal"
                      color="info"
                      density="compact"
                      class="prorate-info"
                      border="start"
                    >
                      <template v-slot:prepend>
                        <v-icon size="20">mdi-information-outline</v-icon>
                      </template>
                      <div class="info-content">
                        <div class="info-title">Rincian Tagihan Pertama:</div>
                        <div class="info-details">
                          <div class="info-item">• Biaya Prorate: {{ formatCurrency(hargaProrate) }}</div>
                          <div class="info-item">• Biaya Bulan Depan: {{ formatCurrency(hargaNormal) }}</div>
                        </div>
                      </div>
                    </v-alert>

                    <div class="field-group">
                      <label class="field-label">
                        {{ isProratePlusFull ? 'Total Tagihan Pertama' : 'Total Harga Prorate' }}
                      </label>
                      <v-text-field
                        :model-value="formatCurrency(editedItem.harga_awal)"
                        variant="outlined"
                        prepend-inner-icon="mdi-currency-usd-circle"
                        readonly
                        density="comfortable"
                        hide-details="auto"
                        bg-color="info-lighten-5"
                        class="price-field"
                      ></v-text-field>
                    </div>
                  </div>
                </template>
              </div>

              <!-- Status and Schedule Section -->
              <div class="form-section">
                <div class="section-header">
                  <div class="section-icon">
                    <v-icon color="primary" size="20">mdi-cog</v-icon>
                  </div>
                  <h3 class="section-title">Status & Jadwal</h3>
                </div>

                <v-row class="field-row">
                  <v-col cols="12" lg="6" md="6">
                    <div class="field-group">
                      <label class="field-label">
                        Status Langganan
                        <span class="required-indicator">*</span>
                      </label>
                      <v-select
                        v-model="editedItem.status"
                        :items="[
                          { title: 'Aktif', value: 'Aktif' },
                          { title: 'Suspended', value: 'Suspended' },
                          { title: 'Berhenti', value: 'Berhenti' }
                        ]"
                        variant="outlined"
                        prepend-inner-icon="mdi-check-circle-outline"
                        :rules="[rules.required]"
                        density="comfortable"
                        hide-details="auto"
                        class="select-field"
                      ></v-select>
                    </div>
                  </v-col>

                  <v-col cols="12" lg="6" md="6">
                    <div class="field-group">
                      <label class="field-label">
                        Tanggal Jatuh Tempo
                        <span class="required-indicator">*</span>
                      </label>
                      <v-text-field
                        v-model="editedItem.tgl_jatuh_tempo"
                        type="date"
                        variant="outlined"
                        prepend-inner-icon="mdi-calendar-alert"
                        :rules="[rules.required]"
                        density="comfortable"
                        hide-details="auto"
                      ></v-text-field>
                    </div>
                  </v-col>
                </v-row>

                <!-- Status Modem Section -->
                <v-expand-transition>
                  <div v-if="editedItem.status === 'Aktif' || editedItem.status === 'Berhenti'" class="conditional-section">
                    <div class="field-group">
                      <label class="field-label">
                        Status Modem
                        <span class="field-hint">(Wajib diisi)</span>
                      </label>
                      <v-select
                        v-model="editedItem.status_modem"
                        :items="getStatusModemOptions(editedItem.status || '')"
                        item-title="title"
                        item-value="value"
                        variant="outlined"
                        prepend-inner-icon="mdi-wifi-router"
                        density="comfortable"
                        hide-details="auto"
                        class="select-field"
                      ></v-select>
                    </div>
                  </div>
                </v-expand-transition>

                <!-- Alasan Berhenti Section -->
                <v-expand-transition>
                  <div v-if="editedItem.status === 'Berhenti'" class="conditional-section">
                    <div class="field-group">
                      <label class="field-label">
                        Alasan Berhenti
                        <span class="field-hint">(Opsional)</span>
                      </label>
                      <v-textarea
                        v-model="editedItem.alasan_berhenti"
                        variant="outlined"
                        prepend-inner-icon="mdi-text-box-outline"
                        rows="3"
                        auto-grow
                        density="comfortable"
                        hide-details="auto"
                        placeholder="Contoh: Pindah rumah, tidak puas dengan layanan, alasan ekonomi, dll."
                        class="textarea-field"
                      ></v-textarea>
                    </div>
                  </div>
                </v-expand-transition>
              </div>
            </v-form>
          </v-card-text>

          <!-- Action Buttons -->
          <v-card-actions class="form-actions">
            <v-spacer></v-spacer>
            <v-btn
              variant="outlined"
              color="primary-darken-1"
              size="large"
              @click="$router.go(-1)"
              class="action-btn cancel-btn"
            >
              <v-icon start size="18">mdi-close</v-icon>
              Batal
            </v-btn>
            <v-btn
              color="primary"
              variant="flat"
              size="large"
              @click="saveLangganan"
              :loading="saving"
              :disabled="!isFormValid"
              class="action-btn save-btn"
            >
              <v-icon start size="18">mdi-content-save</v-icon>
              Simpan Perubahan
            </v-btn>
          </v-card-actions>
        </v-card>
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
  alasan_berhenti?: string | null;
  status_modem?: string | null;
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
const paketLoading = ref(true);

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

    paketLoading.value = false;
  } catch (error: any) {
    console.error("Gagal mengambil detail pelanggan:", error);
    filteredPaketLayanan.value = [];
    paketLoading.value = false;
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
  if (!pelangganId) return 'N/A';
  if (!Array.isArray(pelangganSelectList.value)) {
    return `ID ${pelangganId}`;
  }
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.nama || `ID ${pelangganId}`;
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
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 0;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  color: white;
  padding: 2rem 1.5rem;
  margin-bottom: 2rem;
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  pointer-events: none;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Header responsive adjustments */
@media (min-width: 1200px) {
  .header-content {
    max-width: 1700px;
    padding: 0 2rem;
  }
}

@media (min-width: 1400px) {
  .header-content {
    max-width: 1900px;
    padding: 0 2.5rem;
  }
}

@media (min-width: 1600px) {
  .header-content {
    max-width: 2100px;
    padding: 0 3rem;
  }
}

@media (min-width: 1920px) {
  .header-content {
    max-width: 2400px;
    padding: 0 4rem;
  }
}

@media (min-width: 2560px) {
  .header-content {
    max-width: 2800px;
    padding: 0 5rem;
  }
}

@media (min-width: 3840px) {
  .header-content {
    max-width: 3200px;
    padding: 0 6rem;
  }
}

.back-btn {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Desktop header icon improvements */
@media (min-width: 1200px) {
  .header-icon {
    padding: 1.3rem;
  }
}

@media (min-width: 1400px) {
  .header-icon {
    padding: 1.4rem;
  }
}

@media (min-width: 1600px) {
  .header-icon {
    padding: 1.5rem;
  }
}

.header-title {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.header-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
  line-height: 1.4;
  font-weight: 400;
}

/* Desktop header improvements */
@media (min-width: 1200px) {
  .header-title {
    font-size: 2.4rem;
  }

  .header-subtitle {
    font-size: 1.2rem;
  }
}

@media (min-width: 1400px) {
  .header-title {
    font-size: 2.6rem;
  }

  .header-subtitle {
    font-size: 1.25rem;
  }
}

@media (min-width: 1600px) {
  .header-title {
    font-size: 2.8rem;
  }

  .header-subtitle {
    font-size: 1.3rem;
  }
}

/* Content Wrapper */
.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem 2rem;
}

/* Desktop-specific layout */
@media (min-width: 1200px) {
  .content-wrapper {
    max-width: 1700px;
    padding: 0 2.5rem 2rem;
  }
}

@media (min-width: 1400px) {
  .content-wrapper {
    max-width: 1900px;
    padding: 0 3rem 2rem;
  }
}

/* Ultra-wide screens */
@media (min-width: 1600px) {
  .content-wrapper {
    max-width: 2100px;
    padding: 0 4rem 2rem;
  }
}

/* Super ultra-wide screens */
@media (min-width: 1920px) {
  .content-wrapper {
    max-width: 2400px;
    padding: 0 5rem 2rem;
  }
}

/* 4K screens */
@media (min-width: 2560px) {
  .content-wrapper {
    max-width: 2800px;
    padding: 0 6rem 2rem;
  }
}

/* Ultra-wide 4K+ screens */
@media (min-width: 3840px) {
  .content-wrapper {
    max-width: 3200px;
    padding: 0 8rem 2rem;
  }
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-content {
  text-align: center;
}

.loading-text {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1rem;
  font-weight: 500;
}

/* Error Alert */
.error-alert {
  margin-bottom: 2rem;
  border-radius: 16px;
}

/* Form */
.form-wrapper {
  width: 100%;
}

.form-card {
  border-radius: 20px;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  overflow: hidden;
}

.form-content {
  padding: 2.5rem;
}

/* Desktop-wide form layout */
@media (min-width: 1200px) {
  .form-content {
    padding: 3rem;
  }
}

@media (min-width: 1400px) {
  .form-content {
    padding: 3.5rem;
  }
}

/* Ultra-wide screen optimization */
@media (min-width: 1600px) {
  .form-content {
    padding: 4rem;
  }
}

/* Form Sections */
.form-section {
  margin-bottom: 2.5rem;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1);
}

.section-icon {
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 8px;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

/* Field Groups */
.field-group {
  margin-bottom: 1.5rem;
}

.field-group:last-child {
  margin-bottom: 0;
}

/* Desktop field spacing */
@media (min-width: 1200px) {
  .field-group {
    margin-bottom: 1.75rem;
  }
}

@media (min-width: 1400px) {
  .field-group {
    margin-bottom: 2rem;
  }
}

/* Ultra-wide field spacing */
@media (min-width: 1600px) {
  .field-group {
    margin-bottom: 2.25rem;
  }
}

.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.required-indicator {
  color: rgb(var(--v-theme-error));
  font-weight: 700;
  margin-left: 0.25rem;
}

.field-hint {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 400;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.field-row {
  margin: 0 -0.75rem;
}

.field-row .v-col {
  padding: 0 0.75rem;
}

/* Desktop field row optimization */
@media (min-width: 1200px) {
  .field-row {
    margin: 0 -1rem;
  }

  .field-row .v-col {
    padding: 0 1rem;
  }
}

@media (min-width: 1400px) {
  .field-row {
    margin: 0 -1.25rem;
  }

  .field-row .v-col {
    padding: 0 1.25rem;
  }
}

/* Ultra-wide screen field layout */
@media (min-width: 1600px) {
  .field-row {
    margin: 0 -1.5rem;
  }

  .field-row .v-col {
    padding: 0 1.5rem;
  }
}

/* Field Styling */
.readonly-field :deep(.v-field) {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.08) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%
  );
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.select-field :deep(.v-field),
.price-field :deep(.v-field),
.textarea-field :deep(.v-field) {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.select-field :deep(.v-field:hover),
.textarea-field :deep(.v-field:hover) {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
}

.price-field :deep(.v-field) {
  background: rgba(var(--v-theme-success), 0.05);
  border: 1px solid rgba(var(--v-theme-success), 0.2);
}

.price-field :deep(.v-field-input) {
  font-weight: 600;
  font-size: 1.1rem;
}

/* Package Item Styling */
.package-item {
  padding: 1rem;
  border-radius: 12px;
  margin: 0.25rem 0;
  transition: all 0.3s ease;
}

.package-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.package-avatar {
  margin-right: 0.75rem;
}

.package-name {
  font-weight: 600;
  font-size: 1rem;
}

.package-details {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Pricing Section */
.pricing-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.06) 0%,
    rgba(var(--v-theme-secondary), 0.03) 100%
  );
  border-radius: 16px;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.05);
}

/* Switch Group */
.switch-group {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.05) 0%,
    rgba(var(--v-theme-secondary), 0.03) 100%
  );
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.05);
}

/* Prorate Info */
.prorate-info {
  border-radius: 12px;
  margin-bottom: 1rem;
}

.info-content {
  line-height: 1.5;
}

.info-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.info-details {
  margin-left: 0.5rem;
}

.info-item {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

/* Conditional Sections */
.conditional-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.06) 0%,
    rgba(var(--v-theme-secondary), 0.03) 100%
  );
  border-radius: 16px;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.05);
}

/* Form Actions */
.form-actions {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.06) 100%
  );
  padding: 1.5rem 2.5rem;
  border-top: 1px solid rgba(var(--v-theme-primary), 0.2);
  box-shadow: 0 -2px 8px rgba(var(--v-theme-primary), 0.05);
}

/* Desktop form actions */
@media (min-width: 1200px) {
  .form-actions {
    padding: 2rem 3rem;
  }
}

@media (min-width: 1400px) {
  .form-actions {
    padding: 2.5rem 3.5rem;
  }
}

/* Ultra-wide form actions */
@media (min-width: 1600px) {
  .form-actions {
    padding: 3rem 4rem;
  }
}

.action-btn {
  min-width: 140px;
  height: 48px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.025em;
  transition: all 0.3s ease;
}

/* Desktop action buttons */
@media (min-width: 1200px) {
  .action-btn {
    min-width: 160px;
    height: 52px;
    font-size: 0.95rem;
  }
}

@media (min-width: 1400px) {
  .action-btn {
    min-width: 180px;
    height: 56px;
    font-size: 1rem;
  }
}

/* Ultra-wide action buttons */
@media (min-width: 1600px) {
  .action-btn {
    min-width: 200px;
    height: 60px;
    font-size: 1.05rem;
  }
}

.cancel-btn {
  margin-right: 1rem;
}

.cancel-btn:hover {
  background: rgba(var(--v-theme-error), 0.1);
  color: rgb(var(--v-theme-error));
  border-color: rgb(var(--v-theme-error));
}

.save-btn {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.3);
}

.save-btn:hover {
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.4);
  transform: translateY(-1px);
}

.save-btn:disabled {
  background: rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: none;
  transform: none;
}

/* Dark Theme */
.v-theme--dark .edit-langganan-container {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.v-theme--dark .form-card {
  background: #1e293b;
  border-color: #334155;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .pricing-section,
.v-theme--dark .conditional-section,
.v-theme--dark .switch-group {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.12) 0%,
    rgba(var(--v-theme-secondary), 0.08) 100%
  );
  border-color: rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .form-actions {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.18) 0%,
    rgba(var(--v-theme-secondary), 0.12) 100%
  );
  border-color: rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 -2px 8px rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .readonly-field :deep(.v-field) {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.06) 100%
  );
  border-color: rgba(var(--v-theme-primary), 0.2);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .content-wrapper {
    padding: 0 1rem 2rem;
  }
  
  .form-content {
    padding: 2rem;
  }
  
  .form-actions {
    padding: 1.25rem 2rem;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 1.5rem 1rem;
    margin-bottom: 1.5rem;
  }
  
  .header-title {
    font-size: 1.75rem;
  }
  
  .header-subtitle {
    font-size: 0.9rem;
  }
  
  .content-wrapper {
    padding: 0 0.75rem 1.5rem;
  }
  
  .form-content {
    padding: 1.5rem;
  }
  
  .form-actions {
    padding: 1rem 1.5rem;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .action-btn {
    width: 100%;
    margin: 0;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .field-row {
    margin: 0 -0.5rem;
  }
  
  .field-row .v-col {
    padding: 0 0.5rem;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 1.25rem 0.75rem;
  }
  
  .header-content {
    gap: 0.75rem;
  }
  
  .header-info {
    gap: 0.75rem;
  }
  
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 0.85rem;
  }
  
  .content-wrapper {
    padding: 0 0.5rem 1rem;
  }
  
  .form-content {
    padding: 1.25rem;
  }
  
  .form-actions {
    padding: 1rem 1.25rem;
  }
  
  .section-title {
    font-size: 1.1rem;
  }
  
  .form-section {
    margin-bottom: 2rem;
  }
  
  .pricing-section,
  .conditional-section,
  .switch-group {
    padding: 0.75rem;
  }
}

@media (max-width: 360px) {
  .page-header {
    padding: 1rem 0.5rem;
  }
  
  .header-title {
    font-size: 1.375rem;
  }
  
  .content-wrapper {
    padding: 0 0.25rem 0.75rem;
  }
  
  .form-content {
    padding: 1rem;
  }
  
  .form-actions {
    padding: 0.75rem 1rem;
  }
  
  .field-row {
    margin: 0 -0.25rem;
  }
  
  .field-row .v-col {
    padding: 0 0.25rem;
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