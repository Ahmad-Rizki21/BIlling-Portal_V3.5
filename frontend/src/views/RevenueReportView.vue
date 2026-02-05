<template>
  <v-container fluid class="pa-4 pa-md-6 bg-grey-lighten-4 fill-height align-start">
    <div class="w-100">
      <!-- Header Section with Gradient Background -->
      <div class="header-card mb-6">
        <div class="header-section">
          <div class="header-content">
            <div class="d-flex align-center">
              <v-avatar class="me-4 elevation-4" color="rgba(255,255,255,0.2)" size="72">
                <v-icon color="white" size="36">mdi-chart-line</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-1">Laporan Keuangan</h1>
                <p class="header-subtitle mb-0">
                  Monitoring detail pendapatan, tagihan & pajak
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filter Controls -->
      <v-card class="mb-6 modern-card border-none" elevation="0" rounded="xl">
        <v-card-text class="pa-3 pa-md-4">
          <v-row align="center" class="ga-3" no-gutters>
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
                    density="compact"
                    hide-details
                    class="bg-white"
                    color="primary"
                  ></v-text-field>
                </template>
                <v-date-picker v-model="startDate" @update:model-value="menuStart = false" color="primary"></v-date-picker>
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
                    density="compact"
                    hide-details
                    class="bg-white"
                    color="primary"
                  ></v-text-field>
                </template>
                <v-date-picker v-model="endDate" @update:model-value="menuEnd = false" color="primary"></v-date-picker>
              </v-menu>
            </v-col>
            <v-col cols="12" sm="4" md="auto" class="flex-grow-1">
              <v-select
                v-model="selectedLocation"
                :items="locations"
                label="Wilayah"
                prepend-inner-icon="mdi-map-marker"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                class="bg-white"
                color="primary"
              ></v-select>
            </v-col>
            <!-- Brand Filter Removed as requested -->
            <v-col cols="auto">
              <v-btn
                color="primary"
                @click="fetchReport"
                :loading="isReportLoading"
                height="40"
                class="text-none px-6"
                prepend-icon="mdi-filter"
                rounded="lg"
                elevation="1"
              >
                Tampilkan
              </v-btn>
            </v-col>
             <v-col cols="auto">
               <v-btn
                color="green-darken-1"
                @click="exportToExcel"
                :disabled="!reportSummary || reportSummary.total_invoices === 0 || exporting"
                 height="40"
                class="text-none px-6 text-white"
                prepend-icon="mdi-microsoft-excel"
                rounded="lg"
                variant="flat"
               >
                 Export
                  <v-progress-circular v-if="exporting" indeterminate size="20" class="ms-2"></v-progress-circular>
               </v-btn>
             </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Loading State -->
      <div v-if="isLoading && !reportSummary" class="text-center pa-10">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <p class="mt-4 text-grey">Memuat data...</p>
      </div>

       <!-- DASHBOARD CONTENT -->
      <div v-if="reportSummary" class="fade-enter-active">
        
        <!-- 1. RINGKASAN KEUANGAN (Financial Summary) -->
        <div class="mb-4">
          <div class="d-flex align-center mb-2">
            <v-icon color="grey-darken-2" class="me-2">mdi-wallet-outline</v-icon>
            <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Ringkasan Keuangan</span>
          </div>
          <v-row>
            <!-- 1. TOTAL PEMASUKAN (Cash Flow) -->
            <v-col cols="12" md="4">
              <v-card class="stats-card border-top-success h-100" elevation="0">
                <v-card-text>
                  <div class="text-caption text-grey mb-1">Total Pemasukan</div>
                  <div class="text-h5 font-weight-bold text-success">
                    {{ formatCurrency(reportSummary.financial_summary?.total_pemasukan || 0) }}
                  </div>
                   <div class="text-caption text-grey mt-2">
                    Uang yang diterima sistem
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 2. TOTAL TAGIHAN (Invoiced) -->
             <v-col cols="12" md="4">
              <v-card class="stats-card border-top-primary h-100" elevation="0">
                 <v-card-text>
                  <div class="text-caption text-grey mb-1">Total Tagihan Dicetak</div>
                  <div class="text-h5 font-weight-bold text-primary">
                    {{ formatCurrency(reportSummary.billing_summary?.total_tagihan?.total || 0) }}
                  </div>
                  <div class="text-caption text-grey mt-2">
                    Nilai invoice yang diterbitkan
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 3. BELUM TERBAYAR (Outstanding) -->
            <v-col cols="12" md="4">
              <v-card class="stats-card border-top-warning h-100" elevation="0">
                 <v-card-text>
                  <div class="text-caption text-grey mb-1">Belum Terbayar</div>
                  <div class="text-h5 font-weight-bold text-warning darken-2">
                    {{ formatCurrency((reportSummary.billing_summary?.pending?.total || 0) + (reportSummary.billing_summary?.telat?.total || 0)) }}
                  </div>
                   <div class="text-caption text-grey mt-2">
                    Potensi pendapatan (Pending + Telat)
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- 2. RINGKASAN TAGIHAN (Billing Summary) -->
        <div class="mb-4 mt-6">
           <div class="d-flex align-center mb-2">
            <v-icon color="grey-darken-2" class="me-2">mdi-invoice-text-outline</v-icon>
            <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Ringkasan Tagihan</span>
            <v-chip size="x-small" class="ms-2" variant="flat" color="grey-lighten-3">
              {{ formatDate(startDate) }} - {{ formatDate(endDate) }}
            </v-chip>
          </div>
          
          <v-row>
            <!-- Total Tagihan -->
             <v-col cols="12" sm="6" md="3">
               <v-card class="stats-card h-100" elevation="0">
                 <v-card-text>
                   <div class="text-subtitle-2 text-grey-darken-1 mb-2">Total Tagihan</div>
                   <div class="text-h4 font-weight-black mb-4">{{ reportSummary.billing_summary?.total_tagihan?.count || 0 }}</div>
                   
                   <div class="stats-detail-row">
                      <span>Nominal:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.total_tagihan?.nominal || 0) }}</span>
                   </div>
                   <div class="stats-detail-row text-error">
                      <span>Diskon:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.total_tagihan?.diskon || 0) }}</span>
                   </div>
                   <div class="stats-detail-row">
                      <span>Biaya Pasang:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.total_tagihan?.biaya_pasang || 0) }}</span>
                   </div>
                   <div class="stats-detail-row total mt-2 pt-2 border-t">
                      <span>Total:</span>
                      <span class="font-weight-bold text-grey-darken-3">{{ formatCurrency(reportSummary.billing_summary?.total_tagihan?.total || 0) }}</span>
                   </div>
                 </v-card-text>
               </v-card>
             </v-col>

              <!-- Lunas -->
             <v-col cols="12" sm="6" md="3">
               <v-card class="stats-card h-100" elevation="0">
                 <v-card-text>
                   <div class="text-subtitle-2 text-success mb-2">Lunas</div>
                   <div class="text-h4 font-weight-black text-success mb-4">{{ reportSummary.billing_summary?.lunas?.count || 0 }}</div>
                   
                   <div class="stats-detail-row">
                      <span>Nominal:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.lunas?.nominal || 0) }}</span>
                   </div>
                   <div class="stats-detail-row text-error">
                      <span>Diskon:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.lunas?.diskon || 0) }}</span>
                   </div>
                    <div class="stats-detail-row">
                      <span>Biaya Pasang:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.lunas?.biaya_pasang || 0) }}</span>
                   </div>
                   <div class="stats-detail-row total mt-2 pt-2 border-t text-success">
                      <span>Total:</span>
                      <span class="font-weight-bold">{{ formatCurrency(reportSummary.billing_summary?.lunas?.total || 0) }}</span>
                   </div>
                 </v-card-text>
               </v-card>
             </v-col>

              <!-- Pending -->
             <v-col cols="12" sm="6" md="3">
               <v-card class="stats-card h-100" elevation="0">
                 <v-card-text>
                   <div class="text-subtitle-2 text-warning darken-2 mb-2">Pending</div>
                   <div class="text-h4 font-weight-black text-warning darken-2 mb-4">{{ reportSummary.billing_summary?.pending?.count || 0 }}</div>
                   
                   <div class="stats-detail-row">
                      <span>Nominal:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.pending?.nominal || 0) }}</span>
                   </div>
                   <div class="stats-detail-row text-error">
                      <span>Diskon:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.pending?.diskon || 0) }}</span>
                   </div>
                    <div class="stats-detail-row">
                      <span>Biaya Pasang:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.pending?.biaya_pasang || 0) }}</span>
                   </div>
                   <div class="stats-detail-row total mt-2 pt-2 border-t text-warning darken-2">
                      <span>Total:</span>
                      <span class="font-weight-bold">{{ formatCurrency(reportSummary.billing_summary?.pending?.total || 0) }}</span>
                   </div>
                 </v-card-text>
               </v-card>
             </v-col>

             <!-- Telat -->
             <v-col cols="12" sm="6" md="3">
               <v-card class="stats-card h-100" elevation="0">
                 <v-card-text>
                   <div class="text-subtitle-2 text-error mb-2">Telat</div>
                   <div class="text-h4 font-weight-black text-error mb-4">{{ reportSummary.billing_summary?.telat?.count || 0 }}</div>
                   
                   <div class="stats-detail-row">
                      <span>Nominal:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.telat?.nominal || 0) }}</span>
                   </div>
                   <div class="stats-detail-row text-error">
                      <span>Diskon:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.telat?.diskon || 0) }}</span>
                   </div>
                    <div class="stats-detail-row">
                      <span>Biaya Pasang:</span>
                      <span class="font-weight-medium">{{ formatCurrency(reportSummary.billing_summary?.telat?.biaya_pasang || 0) }}</span>
                   </div>
                   <div class="stats-detail-row total mt-2 pt-2 border-t text-error">
                      <span>Total:</span>
                      <span class="font-weight-bold">{{ formatCurrency(reportSummary.billing_summary?.telat?.total || 0) }}</span>
                   </div>
                 </v-card-text>
               </v-card>
             </v-col>
          </v-row>
        </div>

        <!-- 3. INFORMASI PAJAK & METODE PEMBAYARAN -->
        <v-row class="mb-4">
          <!-- Informasi Pajak -->
          <v-col cols="12" md="8">
             <v-card class="stats-card h-100" elevation="0">
              <v-card-title class="text-subtitle-1 font-weight-bold text-grey-darken-3 px-4 pt-4 pb-2">
                Informasi Pajak
              </v-card-title>
              <v-card-text class="pa-0">
                <v-table density="compact" class="text-caption">
                  <thead>
                    <tr>
                      <th class="text-left font-weight-bold">Status</th>
                      <th class="text-right">PPN</th>
                      <th class="text-right">BHP</th>
                      <th class="text-right">USO</th>
                      <th class="text-right font-weight-bold">Total Pajak</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td class="font-weight-medium">Lunas</td>
                      <td class="text-right text-success">{{ formatCurrency(reportSummary.tax_summary?.lunas?.ppn || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.lunas?.bhp || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.lunas?.uso || 0) }}</td>
                      <td class="text-right font-weight-bold text-success">{{ formatCurrency(reportSummary.tax_summary?.lunas?.total_pajak || 0) }}</td>
                    </tr>
                    <tr>
                      <td class="font-weight-medium">Pending</td>
                       <td class="text-right text-warning">{{ formatCurrency(reportSummary.tax_summary?.pending?.ppn || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.pending?.bhp || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.pending?.uso || 0) }}</td>
                      <td class="text-right font-weight-bold text-warning">{{ formatCurrency(reportSummary.tax_summary?.pending?.total_pajak || 0) }}</td>
                    </tr>
                     <tr>
                      <td class="font-weight-medium">Telat</td>
                       <td class="text-right text-error">{{ formatCurrency(reportSummary.tax_summary?.telat?.ppn || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.telat?.bhp || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.telat?.uso || 0) }}</td>
                      <td class="text-right font-weight-bold text-error">{{ formatCurrency(reportSummary.tax_summary?.telat?.total_pajak || 0) }}</td>
                    </tr>
                     <tr class="bg-grey-lighten-4 font-weight-bold">
                      <td>TOTAL</td>
                       <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.total?.ppn || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.total?.bhp || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.total?.uso || 0) }}</td>
                      <td class="text-right">{{ formatCurrency(reportSummary.tax_summary?.total?.total_pajak || 0) }}</td>
                    </tr>
                  </tbody>
                </v-table>
                 <div class="px-4 py-2 text-caption text-grey">Harga sudah termasuk pajak</div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Metode Pembayaran -->
          <v-col cols="12" md="4">
            <v-card class="stats-card h-100" elevation="0">
              <v-card-title class="text-subtitle-1 font-weight-bold text-grey-darken-3 px-4 pt-4 pb-2">
                Ringkasan per Metode Bayar
              </v-card-title>
              <v-card-text class="pa-0 overflow-y-auto" style="max-height: 250px;">
                <v-list density="compact">
                  <v-list-item v-for="method in reportSummary.payment_methods" :key="method.method" class="border-bottom">
                    <template v-slot:prepend>
                      <v-avatar size="32" color="grey-lighten-4" class="me-3">
                         <span class="text-caption font-weight-bold">{{ method.count }}x</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="text-caption font-weight-bold">
                      {{ method.method }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                       Total: {{ formatCurrency(method.total_amount) }}
                    </v-list-item-subtitle>
                  </v-list-item>
                   <v-list-item v-if="reportSummary.payment_methods.length === 0">
                      <v-list-item-title class="text-caption text-center text-grey">
                        Belum ada data pembayaran
                      </v-list-item-title>
                   </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

         <!-- 4. DATA TABLE (Keeping existing table but styled cleaner) -->
         <v-card elevation="0" rounded="lg" class="modern-card mt-6">
            <v-card-title class="pa-4 text-subtitle-1 font-weight-bold text-grey-darken-3 border-b">
              Data Tagihan (Detail)
            </v-card-title>
             <v-data-table-server
              v-model:page="currentPage"
              v-model:items-per-page="itemsPerPage"
              :headers="headers"
              :items="invoiceDetails"
              :items-length="reportSummary?.total_invoices || 0"
              :loading="isDetailsLoading"
              @update:options="handleTableOptionsUpdate"
              class="text-caption"
              density="compact"
            >
             <template v-slot:item.total_harga="{ item }">
                <span class="font-weight-medium">{{ formatCurrency(item.total_harga) }}</span>
             </template>
             <template v-slot:item.paid_at="{ item }">
                {{ item.paid_at ? new Date(item.paid_at).toLocaleString('id-ID') : '-' }}
             </template>
             <template v-slot:item.id_brand="{ item }">
                <v-chip size="x-small" variant="tonal" color="primary">{{ item.id_brand }}</v-chip>
             </template>
            </v-data-table-server>
         </v-card>

      </div>
       <!-- Empty State -->
      <div v-else-if="!isLoading && !reportSummary" class="empty-state text-center pa-10">
         <v-icon size="64" color="grey-lighten-2" class="mb-4">mdi-chart-box-outline</v-icon>
         <p class="text-grey">Silakan klik "Tampilkan" untuk melihat laporan.</p>
      </div>

    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useDisplay } from 'vuetify';
import { debounce } from 'lodash-es';
import apiClient from '@/services/api';

// --- Interfaces ---
interface InvoiceReportItem {
  invoice_number: string;
  pelanggan_nama: string;
  paid_at: string;
  total_harga: number;
  metode_pembayaran?: string;
  alamat?: string;
  id_brand?: string;
}

interface BillStat {
  count: number;
  nominal: number;
  diskon: number;
  biaya_pasang: number;
  total: number;
}

interface TaxStat {
  ppn: number;
  bhp: number;
  uso: number;
  total_pajak: number;
}

interface PaymentMethodStat {
  method: string;
  count: number;
  total_amount: number;
  pajak: number;
  diskon: number;
}

interface RevenueReportResponse {
  total_pendapatan: number;
  total_invoices: number;
  financial_summary: {
    total_pemasukan: number;
    total_pengeluaran: number;
    saldo_akhir: number;
  };
  billing_summary: {
    total_tagihan: BillStat;
    lunas: BillStat;
    pending: BillStat;
    telat: BillStat;
  };
  tax_summary: {
    total: TaxStat;
    lunas: TaxStat;
    pending: TaxStat;
    telat: TaxStat;
  };
  payment_methods: PaymentMethodStat[];
  rincian_invoice: InvoiceReportItem[];
}

// --- Data ---
const display = useDisplay();
const startDate = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
const endDate = ref(new Date());
const menuStart = ref(false);
const menuEnd = ref(false);
const isReportLoading = ref(false);
const isDetailsLoading = ref(false);
const isLoading = computed(() => isReportLoading.value || isDetailsLoading.value);

const reportSummary = ref<RevenueReportResponse | null>(null);
const invoiceDetails = ref<InvoiceReportItem[]>([]);

const currentPage = ref(1);
const itemsPerPage = ref(10);
const selectedLocation = ref<string | null>(null);
const locations = ref<string[]>([]);
const selectedBrand = ref<string | null>(null);
const brandOptions = ref<any[]>([]);
const exporting = ref(false);

// --- Table Headers ---
const headers = [
  { title: 'No. Invoice', key: 'invoice_number' },
  { title: 'Pelanggan', key: 'pelanggan_nama' },
  { title: 'Brand', key: 'id_brand' },
  { title: 'Alamat', key: 'alamat' },
  { title: 'Tgl Bayar', key: 'paid_at' },
  { title: 'Metode', key: 'metode_pembayaran' },
  { title: 'Total', key: 'total_harga', align: 'end' },
] as const;

// --- Methods ---
function formatDate(date: Date): string {
  return date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency', currency: 'IDR', minimumFractionDigits: 0,
  }).format(value);
};

async function fetchLocations() {
  try {
    const response = await apiClient.get('/pelanggan/lokasi/unik');
    locations.value = response.data;
  } catch (err) { console.error(err); }
}

async function fetchBrandOptions() {
  try {
    const response = await apiClient.get('/harga_layanan');
    brandOptions.value = response.data;
  } catch (err) { console.error(err); }
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
  invoiceDetails.value = [];
  currentPage.value = 1;
  try {
    const params = {
      start_date: toISODateString(startDate.value),
      end_date: toISODateString(endDate.value),
      ...(selectedLocation.value && { alamat: selectedLocation.value }),
      ...(selectedBrand.value && { id_brand: selectedBrand.value }),
    };

    const response = await apiClient.get<RevenueReportResponse>('/reports/revenue', { params });
    reportSummary.value = response.data;

    await fetchInvoiceDetails({ page: 1, itemsPerPage: itemsPerPage.value, sortBy: [] });

  } catch (error) {
    console.error("Fetch report failed", error);
  } finally {
    isReportLoading.value = false;
  }
}

const lastParams = ref({});
const debouncedFetchInvoiceDetails = debounce(async (options: { page: number, itemsPerPage: number, sortBy: any[] }) => {
  if (!reportSummary.value || reportSummary.value.total_invoices === 0) return;

  const params = {
    start_date: toISODateString(startDate.value),
    end_date: toISODateString(endDate.value),
    alamat: selectedLocation.value || undefined,
    id_brand: selectedBrand.value || undefined,
    skip: (options.page - 1) * options.itemsPerPage,
    limit: options.itemsPerPage,
  };

  const paramsKey = JSON.stringify(params);
  if (paramsKey === JSON.stringify(lastParams.value) && invoiceDetails.value.length > 0) return;
  lastParams.value = { ...params };

  isDetailsLoading.value = true;
  try {
    const response = await apiClient.get('/reports/revenue/details', { params });
    invoiceDetails.value = response.data;
  } catch (error) {
    console.error(error);
    lastParams.value = {};
  } finally {
    isDetailsLoading.value = false;
  }
}, 300);

async function fetchInvoiceDetails(options: { page: number, itemsPerPage: number, sortBy: any[] }) {
  await debouncedFetchInvoiceDetails(options);
}

async function handleTableOptionsUpdate(options: { page: number, itemsPerPage: number, sortBy: any[] }) {
  if (!isDetailsLoading.value && reportSummary.value) {
    await fetchInvoiceDetails(options);
  }
}

async function exportToExcel() {
    if (!reportSummary.value) return;
    exporting.value = true;
    try {
        const XLSX = await import('xlsx');
        
        // Export Logic from Invoice Details
         const params = {
            start_date: toISODateString(startDate.value),
            end_date: toISODateString(endDate.value),
            alamat: selectedLocation.value || undefined,
            id_brand: selectedBrand.value || undefined,
        };

        const response = await apiClient.get<InvoiceReportItem[]>('/reports/revenue/details', { params });
        const allData = response.data;
        
         const dataToExport = allData.map((item: any) => ({
          "Nomor Invoice": item.invoice_number,
          "Nama Pelanggan": item.pelanggan_nama,
          "Brand": item.id_brand || "",
          "Alamat": item.alamat || "",
          "Tanggal Bayar": item.paid_at ? new Date(item.paid_at).toLocaleString() : '-',
          "Metode Pembayaran": item.metode_pembayaran || "",
          "Jumlah (Rp)": item.total_harga
        }));

        const worksheet = XLSX.utils.json_to_sheet(dataToExport);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Laporan");
        XLSX.writeFile(workbook, "Laporan_Keuangan.xlsx");
    } catch(e) {
        console.error(e);
        alert("Gagal export data");
    } finally {
        exporting.value = false;
    }
}

onMounted(async () => {
  await Promise.all([fetchLocations(), fetchBrandOptions(), fetchReport()]);
});
</script>

<style scoped>
/* Header Card Styles */
.header-card {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  background: white;
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
  opacity: 0.4;
}

.header-content {
  padding: 32px;
  position: relative;
  z-index: 1;
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 1rem;
  opacity: 0.9;
}

.modern-card {
  border: 1px solid #e0e0e0;
  background-color: white;
}

.stats-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: white;
  transition: box-shadow 0.2s;
}
.stats-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.border-top-success { border-top: 4px solid #4CAF50; }
.border-top-error { border-top: 4px solid #F44336; }
.border-top-primary { border-top: 4px solid #1976D2; }

.stats-detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #616161;
  margin-bottom: 4px;
}

.stats-detail-row.total {
  font-size: 0.9rem;
}

/* Optional: Scrollbar for payment methods */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1; 
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #bdbdbd; 
  border-radius: 4px;
}
</style>
