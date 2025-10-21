<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section -->
    <div class="d-flex flex-column flex-sm-row align-start align-sm-center mb-6 mb-md-8">
      <div class="d-flex align-center mb-4 mb-sm-0">
        <v-avatar class="me-3 modern-avatar" color="deep-purple" size="48">
          <v-icon color="white" size="28">mdi-chart-line</v-icon>
        </v-avatar>
        <div>
          <h1 class="text-h4 text-sm-h3 font-weight-bold text-deep-purple mb-1">Laporan Pendapatan</h1>
          <p class="text-subtitle-1 text-body-2 text-medium-emphasis mb-0">Analisis pendapatan berdasarkan rentang tanggal</p>
        </div>
      </div>
    </div>

    <!-- Filter Controls Card -->
    <v-card class="mb-6 mb-md-8 modern-card" elevation="0" rounded="xl">
  <v-card-text class="pa-4 pa-md-6">
    <v-row align="center" class="ga-3">
      
      <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
        <v-menu v-model="menuStart" :close-on-content-click="false" location="bottom start" offset="8">
          <template v-slot:activator="{ props }">
            <v-text-field
              :model-value="formatDate(startDate)"
              label="Tanggal Awal"
              prepend-inner-icon="mdi-calendar"
              readonly
              v-bind="props"
              variant="outlined"
              density="comfortable"
              hide-details
              class="modern-input"
              color="deep-purple"
            ></v-text-field>
          </template>
          <v-date-picker 
            v-model="startDate" 
            @update:model-value="menuStart = false"
            color="deep-purple"
          ></v-date-picker>
        </v-menu>
      </v-col>
      
      <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
        <v-menu v-model="menuEnd" :close-on-content-click="false" location="bottom start" offset="8">
          <template v-slot:activator="{ props }">
            <v-text-field
              :model-value="formatDate(endDate)"
              label="Tanggal Akhir"
              prepend-inner-icon="mdi-calendar"
              readonly
              v-bind="props"
              variant="outlined"
              density="comfortable"
              hide-details
              class="modern-input"
              color="deep-purple"
            ></v-text-field>
          </template>
          <v-date-picker 
            v-model="endDate" 
            @update:model-value="menuEnd = false"
            color="deep-purple"
          ></v-date-picker>
        </v-menu>
      </v-col>
      
      <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
        <v-select
          v-model="selectedLocation"
          :items="locations"
          label="Filter Berdasarkan Lokasi"
          prepend-inner-icon="mdi-map-marker"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="modern-input"
          color="deep-purple"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
        <v-select
          v-model="selectedBrand"
          :items="brandOptions"
          item-title="brand"
          item-value="id_brand"
          label="Filter Berdasarkan Brand"
          prepend-inner-icon="mdi-tag"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="modern-input"
          color="deep-purple"
        ></v-select>
    </v-col>
    <v-col cols="12" sm="12" md="auto">
      </v-col>
      <v-col cols="12" sm="6" md="auto">
        <div class="d-flex ga-3">
          <v-btn
            color="deep-purple"
            @click="fetchReport"
            :loading="isReportLoading"
            size="large"
            class="text-none modern-btn"
            prepend-icon="mdi-magnify"
            rounded="lg"
          >
            Tampilkan
          </v-btn>
          
          <v-btn
            color="green-darken-1"
            @click="exportToExcel"
            :disabled="!reportSummary || reportSummary.total_invoices === 0 || exporting"
            size="large"
            class="text-none modern-btn"
            prepend-icon="mdi-microsoft-excel"
            rounded="lg"
            variant="outlined"
          >
            Ekspor
            <v-progress-circular v-if="exporting" indeterminate size="20" class="ms-2"></v-progress-circular>
          </v-btn>
        </div>
      </v-col>

        </v-row>
      </v-card-text>
    </v-card>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center pa-10 pa-md-16">
      <div class="loading-container">
        <v-progress-circular 
          indeterminate 
          color="deep-purple" 
          size="80" 
          width="4"
          class="mb-4"
        ></v-progress-circular>
        <h3 class="text-h6 text-medium-emphasis mb-2">Memuat data laporan...</h3>
        <p class="text-body-2 text-medium-emphasis">Harap tunggu sebentar</p>
      </div>
    </div>
    
    <!-- Report Data -->
    <div v-else-if="reportSummary" class="report-content">
      <!-- Revenue Summary Card -->
      <v-card class="mb-6 mb-md-8 revenue-card" elevation="0" rounded="xl">
        <div class="revenue-gradient pa-6 pa-md-8">
          <div class="d-flex flex-column flex-sm-row align-start align-sm-center">
            <div class="revenue-icon-container mb-4 mb-sm-0 me-sm-6">
              <v-icon color="white" size="48" class="revenue-icon">mdi-cash-multiple</v-icon>
            </div>
            <div class="revenue-content">
              <div class="text-caption text-white-50 mb-2 font-weight-medium text-uppercase tracking-wide">
                Total Pendapatan
              </div>
              <div class="text-subtitle-2 text-white-75 mb-3">
                {{ formatDate(startDate) }} - {{ formatDate(endDate) }}
              </div>
              <div class="revenue-amount text-white">
                {{ formatCurrency(reportSummary.total_pendapatan) }}
              </div>
            </div>
          </div>
        </div>
      </v-card>

      <!-- Invoice Details Table -->
      <v-card elevation="0" rounded="xl" class="modern-card">
        <v-card-title class="pa-4 pa-md-6 table-header">
          <div class="d-flex align-center">
            <v-icon start color="deep-purple" size="24">mdi-receipt-text-check</v-icon> 
            <span class="text-h6 font-weight-bold">Rincian Invoice Lunas</span>
          </div>
        </v-card-title>
        
        <v-divider class="mx-4 mx-md-6"></v-divider>
        
        <!-- Mobile Card View -->
        <div v-if="!$vuetify.display.mdAndUp">
          <div v-if="invoiceDetails.length === 0" class="text-center pa-8">
            <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-receipt-text-off</v-icon>
            <p class="text-body-1 text-medium-emphasis">Tidak ada data invoice untuk periode ini</p>
          </div>
          
          <div v-else class="pa-2">
            <v-card
              v-for="item in paginatedInvoices"
              :key="item.invoice_number"
              class="mb-3 mobile-invoice-card"
              elevation="1"
              rounded="lg"
            >
              <v-card-text class="pa-4">
                <div class="d-flex justify-space-between align-start mb-3">
                  <div>
                    <div class="text-subtitle-2 font-weight-bold text-deep-purple mb-1">
                      {{ item.invoice_number }}
                    </div>
                    <div class="text-body-2 text-medium-emphasis">
                      {{ item.pelanggan_nama }}
                    </div>
                  </div>
                  <v-chip 
                    color="success" 
                    variant="tonal" 
                    size="small"
                    class="font-weight-bold"
                  >
                    {{ formatCurrency(item.total_harga) }}
                  </v-chip>
                </div>
                
                <v-divider class="mb-3"></v-divider>
                
                <div class="invoice-details">
                  <div class="detail-row">
                    <v-icon size="16" color="grey-darken-1" class="me-2">mdi-map-marker</v-icon>
                    <span class="text-body-2">{{ item.alamat || 'Tidak ada alamat' }}</span>
                  </div>
                  
                  <div class="detail-row">
                    <v-icon size="16" color="grey-darken-1" class="me-2">mdi-tag</v-icon>
                    <span class="text-body-2">{{ item.id_brand || 'Tidak ada brand' }}</span>
                  </div>
                  
                  <div class="detail-row">
                    <v-icon size="16" color="grey-darken-1" class="me-2">mdi-calendar</v-icon>
                    <span class="text-body-2">{{ new Date(item.paid_at).toLocaleString('id-ID') }}</span>
                  </div>
                  
                  <div class="detail-row">
                    <v-icon size="16" color="grey-darken-1" class="me-2">mdi-credit-card</v-icon>
                    <span class="text-body-2">{{ item.metode_pembayaran || 'Tidak tercatat' }}</span>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </div>
          
          <!-- Mobile Pagination -->
          <div v-if="totalPages > 1" class="d-flex justify-center align-center pa-4">
            <v-pagination
              v-model="currentPage"
              :length="totalPages"
              :total-visible="5" 
              @update:model-value="handleMobilePageUpdate" 
            ></v-pagination>
          </div>
        </div>

        <!-- Desktop Table View -->
        <div v-if="$vuetify.display.mdAndUp">
          <v-data-table-server
            :headers="headers"
            :items="invoiceDetails"
            :items-length="reportSummary?.total_invoices || 0"
            :loading="isDetailsLoading"
            @update:options="handleTableOptionsUpdate"
            class="modern-table"
            :no-data-text="'Tidak ada data invoice untuk periode ini'"
          >
            <template v-slot:item.invoice_number="{ item }">
              <div class="font-weight-bold text-deep-purple">
                {{ (item as InvoiceReportItem).invoice_number }}
              </div>
            </template>
            
            <template v-slot:item.pelanggan_nama="{ item }">
              <div class="font-weight-medium">
                {{ (item as InvoiceReportItem).pelanggan_nama }}
              </div>
            </template>
            
            <template v-slot:item.alamat="{ item }">
              <div class="text-body-2 text-truncate" style="max-width: 200px;">
                {{ (item as InvoiceReportItem).alamat || 'Tidak ada alamat' }}
              </div>
            </template>
            
            <template v-slot:item.id_brand="{ item }">
              <v-chip 
                variant="tonal" 
                color="primary" 
                size="small"
                class="font-weight-medium"
              >
                {{ (item as InvoiceReportItem).id_brand || 'No Brand' }}
              </v-chip>
            </template>
            
            <template v-slot:item.total_harga="{ item }">
              <div class="font-weight-bold text-success">
                {{ formatCurrency((item as InvoiceReportItem).total_harga) }}
              </div>
            </template>
            
            <template v-slot:item.paid_at="{ item }">
              <div class="text-body-2">
                {{ new Date((item as InvoiceReportItem).paid_at).toLocaleString('id-ID') }}
              </div>
            </template>
            
            <template v-slot:item.metode_pembayaran="{ item }">
              <v-chip 
                variant="outlined" 
                size="small"
                :color="getPaymentMethodColor((item as InvoiceReportItem).metode_pembayaran)"
              >
                {{ (item as InvoiceReportItem).metode_pembayaran || 'Tidak tercatat' }}
              </v-chip>
            </template>
          </v-data-table-server>
        </div>
      </v-card>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state text-center pa-10 pa-md-16">
      <div class="empty-state-content">
        <v-icon size="80" color="grey-lighten-2" class="mb-6">mdi-chart-line-variant</v-icon>
        <h3 class="text-h6 mb-4 text-medium-emphasis">Belum ada data laporan</h3>
        <p class="text-body-1 text-medium-emphasis mb-6">
          Silakan pilih rentang tanggal dan klik "Tampilkan Laporan" untuk melihat data pendapatan.
        </p>
        <v-btn
          color="deep-purple"
          variant="tonal"
          size="large"
          rounded="lg"
          @click="fetchReport"
          class="text-none"
        >
          Mulai Analisis
        </v-btn>
      </div>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed} from 'vue';
import { debounce } from 'lodash-es';
import apiClient from '@/services/api';
import * as XLSX from 'xlsx';

// --- Interface Definition ---
interface InvoiceReportItem {
  invoice_number: string;
  pelanggan_nama: string;
  paid_at: string;
  total_harga: number;
  metode_pembayaran?: string;
  alamat?: string;           
  id_brand?: string;
}

// --- Reactive Data ---
const startDate = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
const endDate = ref(new Date());
const menuStart = ref(false);
const menuEnd = ref(false);
const isReportLoading = ref(false);
const isDetailsLoading = ref(false);
const isLoading = computed(() => isReportLoading.value || isDetailsLoading.value);
// --- PERBAIKAN STATE: Pisahkan summary dan details ---
const reportSummary = ref<{
  total_pendapatan: number;
  total_invoices: number;
} | null>(null);
const invoiceDetails = ref<InvoiceReportItem[]>([]);
// ----------------------------------------------------

// Mobile pagination
const currentPage = ref(1); // Halaman saat ini
const itemsPerPage = ref(10); // Item per halaman, cocokkan dengan v-data-table

const selectedLocation = ref<string | null>(null);
const locations = ref<string[]>([]);

const selectedBrand = ref<string | null>(null);
const brandOptions = ref<any[]>([]); // Untuk menampung { id_brand, brand }
const exporting = ref(false);

// --- Computed Properties ---
const paginatedInvoices = computed(() => invoiceDetails.value || []);

const totalPages = computed(() => {
  if (!reportSummary.value?.total_invoices) return 0;
  return Math.ceil(reportSummary.value.total_invoices / itemsPerPage.value);
});

async function fetchLocations() {
  try {
    const response = await apiClient.get('/pelanggan/lokasi/unik');
    locations.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil daftar lokasi:", error);
  }
}

async function fetchBrandOptions() {
  try {
    // Asumsi Anda punya endpoint untuk mengambil daftar brand/harga_layanan
    const response = await apiClient.get('/harga_layanan'); 
    brandOptions.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil daftar brand:", error);
  }
} 
function handleMobilePageUpdate(newPage: number) {
  fetchInvoiceDetails({ page: newPage, itemsPerPage: itemsPerPage.value, sortBy: [] });
}
// --- Table Headers ---
const headers = [
  { title: 'No. Invoice', key: 'invoice_number', width: '200px', sortable: true },
  { title: 'Nama Pelanggan', key: 'pelanggan_nama', sortable: true },
  { title: 'Alamat', key: 'alamat', sortable: false }, 
  { title: 'Brand', key: 'id_brand', sortable: true },
  { title: 'Tanggal Bayar', key: 'paid_at', sortable: true },
  { title: 'Metode Bayar', key: 'metode_pembayaran', sortable: true }, 
  { title: 'Jumlah', key: 'total_harga', align: 'end', sortable: true },
] as const; 

// --- Methods ---
function formatDate(date: Date): string {
  return date.toLocaleDateString('id-ID', {
    day: '2-digit', month: 'long', year: 'numeric'
  });
}

function getPaymentMethodColor(method?: string): string {
  if (!method) return 'grey';
  const lowerMethod = method.toLowerCase();
  if (lowerMethod.includes('cash')) return 'success';
  if (lowerMethod.includes('transfer')) return 'info';
  if (lowerMethod.includes('kredit')) return 'warning';
  return 'primary';
}

async function exportToExcel() {
  if (!reportSummary.value || reportSummary.value.total_invoices === 0) {
    alert("Tidak ada data untuk diekspor!");
    return;
  }

  exporting.value = true;
  try {
    // Siapkan parameter filter tanpa paginasi
    const params = {
      start_date: toISODateString(startDate.value),
      end_date: toISODateString(endDate.value),
      alamat: selectedLocation.value || undefined,
      id_brand: selectedBrand.value || undefined,
      // PENTING: jangan sertakan 'skip' dan 'limit' agar API mengembalikan semua data
    };

    // Panggil API untuk mendapatkan SEMUA data yang difilter
    const response = await apiClient.get<InvoiceReportItem[]>('/reports/revenue/details', { params });
    const allFilteredData = response.data;

    if (!allFilteredData || allFilteredData.length === 0) {
      alert("Tidak ada data yang cocok dengan filter untuk diekspor.");
      return;
    }

    const dataToExport = allFilteredData.map((item: InvoiceReportItem) => ({
      "Nomor Invoice": item.invoice_number,
      "Nama Pelanggan": item.pelanggan_nama,
      "Alamat": item.alamat || "",
      "Nama Brand": item.id_brand || "",
      "Tanggal Bayar": new Date(item.paid_at),
      "Metode Pembayaran": item.metode_pembayaran || "",
      "Jumlah (Rp)": item.total_harga
    }));

    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Laporan Pendapatan");
    
    // Atur lebar kolom agar lebih rapi
    worksheet["!cols"] = [
        { wch: 25 }, { wch: 30 }, { wch: 40 }, { wch: 15 }, 
        { wch: 20 }, { wch: 15 }, { wch: 15 }
    ];

    // Format kolom mata uang
    if (worksheet['!ref']) {
      const range = XLSX.utils.decode_range(worksheet['!ref']);
      const amountColumnIndex = 6; // Kolom "Jumlah (Rp)" adalah kolom ke-7 (indeks 6)
      
      for (let rowNum = range.s.r + 1; rowNum <= range.e.r; rowNum++) {
        const cellAddress = XLSX.utils.encode_cell({ r: rowNum, c: amountColumnIndex });
        const cell = worksheet[cellAddress];
        if (cell && cell.t === 'n') { // Pastikan sel ada dan tipenya adalah angka
          cell.z = '"Rp" #,##0'; // Format mata uang Rupiah tanpa desimal
        }
      }
    }

    const start = toISODateString(startDate.value);
    const end = toISODateString(endDate.value);
    const fileName = `Laporan_Pendapatan_${start}_sampai_${end}.xlsx`;

    XLSX.writeFile(workbook, fileName);
  } catch (error) {
    console.error("Gagal mengekspor data:", error);
    alert("Terjadi kesalahan saat mencoba mengekspor data.");
  } finally {
    exporting.value = false;
  }
}


function toISODateString(date: Date): string {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}

async function fetchReport() {
  isReportLoading.value = true;
  reportSummary.value = null;
  invoiceDetails.value = []; // Kosongkan detail saat filter baru
  currentPage.value = 1; // Reset pagination
  try {
    const params = {
      start_date: toISODateString(startDate.value),
      end_date: toISODateString(endDate.value),
      ...(selectedLocation.value && { alamat: selectedLocation.value }),
      ...(selectedBrand.value && { id_brand: selectedBrand.value }),
    };

    const response = await apiClient.get('/reports/revenue', { params });
    reportSummary.value = response.data;

  } catch (error) {
    console.error("Gagal mengambil data laporan:", error);
  } finally {
    isReportLoading.value = false;
  }
}

// State untuk mencegah permintaan berulang saat loading
const lastParams = ref({});

// Debounced version untuk mencegah multiple rapid calls
const debouncedFetchInvoiceDetails = debounce(async (options: { page: number, itemsPerPage: number, sortBy: any[] }) => {
  // Jangan fetch jika summary belum ada atau tidak ada data sama sekali
  if (!reportSummary.value) return;

  // Jangan fetch jika total_invoices adalah 0 (tidak ada data)
  if (reportSummary.value.total_invoices === 0) return;

  // Buat parameter untuk cek duplikat
  const params = {
    start_date: toISODateString(startDate.value),
    end_date: toISODateString(endDate.value),
    alamat: selectedLocation.value || undefined,
    id_brand: selectedBrand.value || undefined,
    skip: (options.page - 1) * options.itemsPerPage,
    limit: options.itemsPerPage,
  };

  // Cek apakah ini permintaan duplikat
  const paramsKey = JSON.stringify(params);
  if (paramsKey === JSON.stringify(lastParams.value) && invoiceDetails.value.length > 0) {
    return; // Jangan kirim permintaan yang sama jika data sudah dimuat
  }

  // Simpan parameter terakhir
  lastParams.value = { ...params };

  isDetailsLoading.value = true;
  try {
    const response = await apiClient.get('/reports/revenue/details', { params });
    currentPage.value = options.page;
    itemsPerPage.value = options.itemsPerPage;
    invoiceDetails.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil rincian invoice:", error);
    // Reset lastParams jika terjadi error agar bisa dicoba lagi
    lastParams.value = {};
  } finally {
    isDetailsLoading.value = false;
  }
}, 300); // 300ms debounce

async function fetchInvoiceDetails(options: { page: number, itemsPerPage: number, sortBy: any[] }) {
  await debouncedFetchInvoiceDetails(options);
}

// Fungsi baru untuk menangani perubahan opsi tabel dengan cek tambahan
async function handleTableOptionsUpdate(options: { page: number, itemsPerPage: number, sortBy: any[] }) {
  // Hanya panggil jika tidak sedang loading dan report summary tersedia
  if (!isDetailsLoading.value && reportSummary.value) {
    await fetchInvoiceDetails(options);
  }
}

const formatCurrency = (value: number) => {
  if (typeof value !== 'number') return 'Rp 0';
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(value);
};

// --- Lifecycle ---
onMounted(async () => {
  // Load semua data secara paralel untuk faster initial load
  await Promise.all([
    fetchLocations(),
    fetchBrandOptions(),
    fetchReport()
  ]);
});
</script>

<style scoped>
/* Modern Design System */
.modern-avatar {
  background: linear-gradient(135deg, rgb(var(--v-theme-deep-purple)) 0%, rgb(var(--v-theme-purple)) 100%);
  box-shadow: 0 4px 16px rgba(var(--v-theme-deep-purple), 0.3);
}

.modern-card {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.modern-input {
  transition: all 0.3s ease;
}

.modern-input :deep(.v-field__outline) {
  --v-field-border-width: 1px;
  transition: all 0.3s ease;
}

.modern-input :deep(.v-field--focused .v-field__outline) {
  --v-field-border-width: 2px;
}

.modern-btn {
  box-shadow: 0 2px 8px rgba(var(--v-theme-deep-purple), 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: none;
  font-weight: 600;
}

.modern-btn:hover {
  box-shadow: 0 4px 16px rgba(var(--v-theme-deep-purple), 0.3);
  transform: translateY(-1px);
}

/* Revenue Card Styles */
.revenue-card {
  overflow: hidden;
  position: relative;
}

.revenue-gradient {
  background: linear-gradient(135deg, #2e7d32 0%, #388e3c 50%, #4caf50 100%);
  position: relative;
  overflow: hidden;
}

.revenue-gradient::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  opacity: 0.3;
}

.revenue-icon-container {
  position: relative;
  z-index: 1;
}

.revenue-icon {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.revenue-content {
  position: relative;
  z-index: 1;
}

.revenue-amount {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tracking-wide {
  letter-spacing: 0.05em;
}

.text-white-50 {
  color: rgba(255, 255, 255, 0.5) !important;
}

.text-white-75 {
  color: rgba(255, 255, 255, 0.75) !important;
}

/* Table Styles */
.table-header {
  background: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.modern-table :deep(.v-data-table__tr) {
  transition: all 0.2s ease;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.modern-table :deep(.v-data-table-header) {
  background-color: rgba(var(--v-theme-surface), 0.8);
}

.modern-table :deep(.v-data-table-header__content) {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

/* Mobile Card Styles */
.mobile-invoice-card {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  transition: all 0.3s ease;
}

.mobile-invoice-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.invoice-details {
  margin-top: 4px;
}

/* Loading and Empty States */
.loading-container {
  max-width: 300px;
  margin: 0 auto;
}

.empty-state-content {
  max-width: 400px;
  margin: 0 auto;
}

/* Dark Theme Adjustments */
.v-theme--dark .modern-card {
  background: rgb(var(--v-theme-surface-variant));
  border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .table-header {
  background: rgba(var(--v-theme-surface-variant), 0.8);
}

.v-theme--dark .modern-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .mobile-invoice-card {
  background: rgb(var(--v-theme-surface-variant));
  border-color: rgba(255, 255, 255, 0.08);
}

/* Responsive Design */
@media (max-width: 960px) {
  .revenue-amount {
    font-size: 2rem;
  }
  
  .revenue-gradient {
    padding: 1.5rem !important;
  }
}

@media (max-width: 600px) {
  .revenue-amount {
    font-size: 1.75rem;
  }
  
  .modern-card {
    margin-bottom: 1rem !important;
  }
  
  .revenue-gradient {
    padding: 1rem !important;
  }
  
  .detail-row {
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .revenue-amount {
    font-size: 1.5rem;
  }
  
  .pa-4 {
    padding: 0.75rem !important;
  }
  
  .mobile-invoice-card .v-card-text {
    padding: 0.75rem !important;
  }
}

/* Smooth transitions for theme switching */
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
}

/* Print styles */
@media print {
  .modern-btn, .v-menu, .v-pagination {
    display: none !important;
  }
  
  .modern-card {
    box-shadow: none !important;
    border: 1px solid #ccc !important;
  }
  
  .revenue-gradient {
    background: #4caf50 !important;
    color: white !important;
  }
}
</style>