<template>
  <v-container fluid class="pa-4 pa-sm-6">
    <div class="invoice-header mb-8 pa-6 rounded-xl">
      <div class="d-flex flex-column flex-md-row align-start align-md-center gap-4">
        <div class="header-content d-flex align-center">
          <div class="icon-container me-4">
            <v-icon size="32" color="white">mdi-receipt-text-outline</v-icon>
          </div>
          <div>
            <h1 class="text-h4 text-md-h3 font-weight-bold text-white mb-1">Invoices</h1>
            <p class="text-subtitle-1 text-white text-opacity-90 mb-0">
              Kelola tagihan dan pembayaran
            </p>
          </div>
        </div>
        <v-spacer class="d-none d-md-block"></v-spacer>
        <v-btn
          v-if="auth.hasPermission('create_invoices')"
          color="white"
          variant="elevated"
          size="large"
          elevation="4"
          @click="openGenerateDialog"
          prepend-icon="mdi-plus-circle-outline"
          class="text-none font-weight-bold w-100 w-md-auto rounded-lg"
          style="color: #4338ca !important;"
        >
          Buat Invoice Manual
        </v-btn>
      </div>
    </div>

    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="stats-card pa-4" elevation="2">
          <div class="d-flex align-center">
            <div class="stats-icon success me-3">
              <v-icon color="success">mdi-check-circle</v-icon>
            </div>
            <div>
              <div class="text-h6 font-weight-bold">{{ getPaidCount() }}</div>
              <div class="text-caption text-medium-emphasis">Invoice Lunas</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="stats-card pa-4" elevation="2">
          <div class="d-flex align-center">
            <div class="stats-icon warning me-3">
              <v-icon color="warning">mdi-clock-outline</v-icon>
            </div>
            <div>
              <div class="text-h6 font-weight-bold">{{ getPendingCount() }}</div>
              <div class="text-caption text-medium-emphasis">Belum Dibayar</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="stats-card pa-4" elevation="2">
          <div class="d-flex align-center">
            <div class="stats-icon error me-3">
              <v-icon color="error">mdi-alert-circle</v-icon>
            </div>
            <div>
              <div class="text-h6 font-weight-bold">{{ getOverdueCount() }}</div>
              <div class="text-caption text-medium-emphasis">Kadaluarsa</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="stats-card pa-4" elevation="2">
          <div class="d-flex align-center">
            <div class="stats-icon primary me-3">
              <v-icon color="primary">mdi-receipt-text</v-icon>
            </div>
            <div>
              <div class="text-h6 font-weight-bold">
                {{ totalCount > invoices.length ? `${invoices.length}/${totalCount}` : invoices.length }}
              </div>
              <div class="text-caption text-medium-emphasis">Total Invoice</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="filter-card mb-6" elevation="0">
      <div class="d-flex flex-wrap align-center gap-4 pa-4">
        <v-text-field
          v-model="searchQuery"
          label="Cari (No. Invoice, Nama, ID)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          class="flex-grow-1"
          style="min-width: 250px;"
        ></v-text-field>

        <v-select
          v-model="selectedStatus"
          :items="statusOptions"
          label="Filter Status"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 180px;"
        ></v-select>

        <v-text-field
          v-model="startDate"
          label="Dari Tanggal"
          type="date"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 180px;"
        ></v-text-field>
        
        <v-text-field
          v-model="endDate"
          label="Sampai Tanggal"
          type="date"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 180px;"
        ></v-text-field>

        <v-switch
          v-model="showPaidInvoices"
          color="success"
          label="Tampilkan Lunas & Kadaluarsa"
          hide-details
          density="comfortable"
          class="flex-grow-0 ms-md-4"
        ></v-switch>
        <v-select
          v-model="selectedLimit"
          :items="limitOptions"
          item-title="title"
          item-value="value"
          label="Tampilkan"
          variant="outlined"
          density="comfortable"
          hide-details
          class="flex-grow-0"
          style="min-width: 120px;"
        ></v-select>

        <v-btn
            variant="text"
            @click="resetFilters"
            class="text-none"
        >
          Reset Filter
        </v-btn>

      </div>
    </v-card>

    <v-card class="invoice-table-card" elevation="3">
      <div class="table-header pa-4 pa-sm-6">
        <div class="d-flex flex-column flex-sm-row align-start align-sm-center gap-4">
          <div>
            <h2 class="text-h6 text-sm-h5 font-weight-bold mb-1">Daftar Tagihan</h2>
            <p class="text-body-2 text-medium-emphasis mb-0">
              Kelola dan pantau status pembayaran
            </p>
          </div>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="elevated"
            @click="exportPaymentLinksExcel"
            prepend-icon="mdi-file-excel"
            class="text-none font-weight-bold"
          >
            Export Payment Links
          </v-btn>
        </div>
      </div>

      <v-expand-transition>
        <div v-if="selectedInvoices.length > 0" class="selection-toolbar">
          <span class="font-weight-bold text-primary">{{ selectedInvoices.length }} invoice terpilih</span>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete-sweep"
            @click="dialogBulkDelete = true"
          >
            Hapus
          </v-btn>
        </div>
      </v-expand-transition>
      
      <!-- PERUBAHAN DIMULAI DI SINI -->
      
      <!-- Tampilan Tabel untuk Desktop (Medium ke atas) -->
      <div class="responsive-table-container d-none d-md-block">
        <v-data-table
            v-model="selectedInvoices"
            :headers="headers"
            :items="filteredInvoices" 
            :loading="loading"
            item-value="id"
            class="invoice-table"
            :items-per-page="15"
            :loading-text="'Memuat data invoice...'"
            :no-data-text="'Tidak ada data invoice'"
            show-select
            return-object
          >
          <template v-slot:loading>
            <SkeletonLoader type="table" :rows="10" />
          </template>

          <template v-slot:item.invoice_number="{ item }">
            <div class="invoice-number-cell" style="min-width: 180px;">
              <div class="font-weight-bold text-primary">{{ item.invoice_number }}</div>
              <div class="text-caption text-medium-emphasis">
                <v-icon size="12" class="me-1">mdi-calendar</v-icon>
                {{ formatDate(item.tgl_invoice) }}
              </div>
            </div>
          </template>

          <template v-slot:item.pelanggan_id="{ item }">
            <div class="customer-cell" style="min-width: 220px;">
              <div class="d-flex align-center">
                <v-avatar size="32" color="primary" class="me-2">
                  <v-icon color="white" size="16">mdi-account</v-icon>
                </v-avatar>
                <div>
                  <div class="font-weight-medium">{{ getPelangganName(item.pelanggan_id) }}</div>
                  <div class="text-caption text-medium-emphasis">
                    <v-icon size="12" class="me-1">mdi-identifier</v-icon>
                    ID: {{ item.id_pelanggan }}
                  </div>
                </div>
              </div>
            </div>
          </template>
          
          <template v-slot:item.total_harga="{ item }">
            <div class="amount-cell" style="min-width: 150px;">
              <span class="text-h6 font-weight-bold text-success">
                {{ formatCurrency(item.total_harga) }}
              </span>
            </div>
          </template>

          <template v-slot:item.status_invoice="{ item }">
            <v-chip
              :color="getStatusColor(item.payment_link_status || item.status_invoice)"
              variant="elevated"
              size="small"
              class="font-weight-bold status-chip"
              :prepend-icon="getStatusIcon(item.payment_link_status || item.status_invoice)"
            >
              {{ item.payment_link_status || item.status_invoice }}
            </v-chip>
          </template>

          <template v-slot:item.tgl_jatuh_tempo="{ item }">
            <div class="due-date-cell" style="min-width: 150px;">
              <div class="font-weight-medium">{{ formatDate(item.tgl_jatuh_tempo) }}</div>
              <div
                v-if="item.status_invoice !== 'Lunas'"
                class="text-caption"
                :class="item.status_invoice === 'Kadaluarsa' ? 'text-error' : 'text-warning'"
              >
                {{ getDueDateLabel(item) }}
              </div>
            </div>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="action-buttons" style="min-width: 180px;">
              <v-tooltip location="top">
                <template v-slot:activator="{ props }">
                  <v-btn 
                    icon
                    v-bind="props"
                    variant="text" 
                    size="small" 
                    color="primary" 
                    @click="copyPaymentLink(item.payment_link)"
                    :disabled="!item.payment_link"
                    class="action-btn"
                  >
                    <v-icon>mdi-content-copy</v-icon>
                  </v-btn>
                </template>
                <span>Salin Link</span>
              </v-tooltip>

              <v-tooltip location="top">
                <template v-slot:activator="{ props }">
                  <v-btn 
                    icon="mdi-whatsapp" 
                    v-bind="props"
                    variant="text" 
                    size="small" 
                    color="green" 
                    @click="sendWhatsAppReminder(item)"
                    :disabled="!item.payment_link || !item.no_telp"
                  ></v-btn>
                </template>
                <span>Kirim Pengingat WhatsApp</span>
              </v-tooltip>
              
              <v-tooltip location="top">
                <template v-slot:activator="{ props }">
                  <v-btn 
                    icon="mdi-eye" 
                    v-bind="props"
                    variant="text" 
                    size="small" 
                    
                    @click="openDetailDialog(item)"
                  ></v-btn>
                </template>
                <span>Lihat Detail</span>
              </v-tooltip>

              <v-tooltip location="top">
                <template v-slot:activator="{ props }">
                  <v-btn 
                    v-if="auth.hasPermission('delete_invoices')"
                    icon="mdi-delete" 
                    v-bind="props"
                    variant="text" 
                    size="small" 
                    color="error" 
                    @click="openDeleteDialog(item)"
                    class="action-btn"
                  ></v-btn>
                </template>
                <span>Hapus</span>
              </v-tooltip>

              <v-tooltip location="top" v-if="auth.hasPermission('edit_invoices')">
                  <template v-slot:activator="{ props }">
                    <v-btn 
                      v-if="item.status_invoice !== 'Lunas'"
                      icon="mdi-check-decagram" 
                      v-bind="props"
                      variant="text" 
                      size="small" 
                      color="success" 
                      @click="openMarkAsPaidDialog(item)"
                    ></v-btn>
                  </template>
                  <span>Tandai Lunas</span>
                </v-tooltip>

            </div>
          </template>
        </v-data-table>
      </div>

      <!-- Tampilan Kartu untuk Mobile (Small ke bawah) -->
      <div class="d-md-none pa-4">
        <!-- Loading State -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <p class="mt-4 text-medium-emphasis">Memuat data invoice...</p>
        </div>

        <!-- No Data State -->
        <div v-else-if="!filteredInvoices.length" class="text-center py-8">
          <v-icon size="48" class="text-disabled mb-4">mdi-receipt-text-remove-outline</v-icon>
          <p class="text-medium-emphasis">Tidak ada data invoice ditemukan</p>
        </div>

        <!-- Invoice Cards -->
        <div v-else>
          <v-card
            v-for="item in filteredInvoices"
            :key="item.id"
            class="invoice-card-mobile mb-4"
            elevation="2"
          >
            <!-- Card Header with Checkbox and Status -->
            <div class="d-flex align-center pa-2">
              <v-checkbox-btn
                v-model="selectedInvoices"
                :value="item"
                multiple
                hide-details
                class="flex-grow-0"
              ></v-checkbox-btn>
              <div class="ms-2 flex-grow-1" @click="openDetailDialog(item)">
                <div class="font-weight-bold text-primary">{{ item.invoice_number }}</div>
                <div class="text-caption text-medium-emphasis">{{ getPelangganName(item.pelanggan_id) }}</div>
              </div>
              <v-chip
                :color="getStatusColor(item.payment_link_status || item.status_invoice)"
                variant="elevated"
                size="small"
                class="font-weight-bold ms-2 me-2"
                label
              >
                {{ item.payment_link_status || item.status_invoice }}
              </v-chip>
            </div>
            <v-divider></v-divider>

            <!-- Card Body with details -->
            <v-list density="compact" class="py-2 px-4">
              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="success" class="me-4">mdi-cash-multiple</v-icon>
                </template>
                <v-list-item-title>Total Tagihan</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-bold text-success">{{ formatCurrency(item.total_harga) }}</span>
                </template>
              </v-list-item>
              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey" class="me-4">mdi-calendar-start</v-icon>
                </template>
                <v-list-item-title>Tgl. Invoice</v-list-item-title>
                <template v-slot:append>
                  <span>{{ formatDate(item.tgl_invoice) }}</span>
                </template>
              </v-list-item>
              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon :color="item.status_invoice === 'Kadaluarsa' ? 'error' : 'warning'" class="me-4">mdi-calendar-alert</v-icon>
                </template>
                <v-list-item-title>Jatuh Tempo</v-list-item-title>
                <template v-slot:append>
                  <div class="text-right">
                    <div>{{ formatDate(item.tgl_jatuh_tempo) }}</div>
                    <div v-if="item.status_invoice !== 'Lunas'" class="text-caption" :class="item.status_invoice === 'Kadaluarsa' ? 'text-error' : 'text-warning'">
                      {{ getDueDateLabel(item) }}
                    </div>
                  </div>
                </template>
              </v-list-item>
            </v-list>
            <v-divider></v-divider>

            <!-- Card Actions -->
            <v-card-actions class="justify-space-between pa-1">
              <v-tooltip text="Salin Link">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="small" color="primary" @click="copyPaymentLink(item.payment_link)" :disabled="!item.payment_link"><v-icon>mdi-content-copy</v-icon></v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Kirim WA">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="small" color="green" @click="sendWhatsAppReminder(item)" :disabled="!item.payment_link || !item.no_telp"><v-icon>mdi-whatsapp</v-icon></v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Lihat Detail">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="small" @click="openDetailDialog(item)"><v-icon>mdi-eye</v-icon></v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Tandai Lunas" v-if="auth.hasPermission('edit_invoices') && item.status_invoice !== 'Lunas'">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="small" color="success" @click="openMarkAsPaidDialog(item)"><v-icon>mdi-check-decagram</v-icon></v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Hapus" v-if="auth.hasPermission('delete_invoices')">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="small" color="error" @click="openDeleteDialog(item)"><v-icon>mdi-delete</v-icon></v-btn>
                </template>
              </v-tooltip>
            </v-card-actions>
          </v-card>
        </div>
      </div>
      <!-- PERUBAHAN SELESAI DI SINI -->

    </v-card>

    <v-dialog v-model="dialogMarkAsPaid" max-width="500px" persistent>
      <v-card>
        <v-card-title class="text-h5">Tandai Lunas?</v-card-title>
        <v-card-text>
          <p>Anda akan menandai invoice <strong>{{ itemToMark?.invoice_number }}</strong> sebagai lunas.</p>
          <v-select
            v-model="paymentMethod"
            :items="['Cash', 'Bank Transfer', 'Lainnya']"
            label="Metode Pembayaran"
            variant="outlined"
            density="compact"
            class="mt-4"
          ></v-select>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeMarkAsPaidDialog">Batal</v-btn>
          <v-btn 
            color="success" 
            @click="confirmMarkAsPaid"
            :loading="markingAsPaid"
          >
            Konfirmasi
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="500px" persistent>
      <v-card>
        <v-card-title class="text-h5">Konfirmasi Hapus</v-card-title>
        <v-card-text>
          Anda yakin ingin menghapus invoice <strong>{{ itemToDelete?.invoice_number }}</strong> secara permanen?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDeleteDialog">Batal</v-btn>
          <v-btn 
            color="error" 
            :loading="deleting"
            @click="confirmDelete"
          >
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogGenerate" max-width="600px" persistent>
      <v-card class="generate-dialog">
        <div class="dialog-header pa-6">
          <h2 class="text-h5 font-weight-bold text-white mb-1">Buat Invoice Manual</h2>
          <p class="text-body-2 text-white text-opacity-90 mb-0">
            Pilih langganan pelanggan untuk membuat invoice baru
          </p>
        </div>
        <v-card-text class="pa-6">
          <div class="mb-4">
            <v-icon color="info" class="me-2">mdi-information</v-icon>
            <span class="text-body-2 text-medium-emphasis">
              Pilih langganan pelanggan yang ingin dibuatkan invoice-nya sekarang.
            </span>
          </div>
          <v-autocomplete
            v-model="selectedLanggananId"
            :items="langgananForSelect"
            item-title="title"
            item-value="id"
            label="Pilih Langganan Pelanggan"
            placeholder="Ketik nama pelanggan atau ID langganan..."
            variant="outlined"
            density="comfortable"
            clearable
            :prepend-inner-icon="'mdi-account-search'"
            class="mb-4"
            no-data-text="Tidak ada data langganan ditemukan"
          >
          </v-autocomplete>
          <v-expand-transition>
            <div v-if="selectedLanggananDetails">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    :model-value="formatCurrency(selectedLanggananDetails.harga_awal || 0)"
                    label="Harga Sesuai Langganan"
                    variant="outlined"
                    readonly
                    prepend-inner-icon="mdi-cash"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    :model-value="formatDate(selectedLanggananDetails.tgl_jatuh_tempo)"
                    label="Jatuh Tempo"
                    variant="outlined"
                    readonly
                    prepend-inner-icon="mdi-calendar-end"
                  ></v-text-field>
                </v-col>
              </v-row>
              <p class="text-caption text-medium-emphasis mt-n2">
                * Total tagihan akhir akan ditambahkan pajak sesuai brand.
              </p>
            </div>
            <div v-else-if="selectedLanggananId">
              <v-alert
                type="warning"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                Detail langganan tidak tersedia. Silakan pilih langganan lain.
              </v-alert>
            </div>
          </v-expand-transition>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            @click="closeDialog"
            size="large"
            class="text-none"
          >
            Batal
          </v-btn>
          <v-btn 
            color="primary" 
            @click="generateManualInvoice"
            :loading="generating"
            :disabled="!selectedLanggananId"
            variant="elevated"
            size="large"
            class="text-none font-weight-bold"
          >
            <v-icon class="me-2">mdi-plus</v-icon>
            Buat Invoice
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogBulkDelete" max-width="500px" persistent>
      <v-card class="rounded-xl">
        <v-card-title class="text-h5 d-flex align-center bg-error">
          <v-icon start>mdi-delete-alert</v-icon>
          Konfirmasi Hapus Massal
        </v-card-title>
        <v-card-text class="pt-6">
          Anda yakin ingin menghapus <strong>{{ selectedInvoices.length }} invoice</strong> yang dipilih? Tindakan ini tidak dapat dibatalkan.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialogBulkDelete = false">Batal</v-btn>
          <v-btn 
            color="error" 
            variant="flat"
            @click="confirmBulkDelete" 
            :loading="deleting"
          >
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar 
      v-model="snackbar.show" 
      :color="snackbar.color" 
      :timeout="4000"
      location="top right"
      variant="elevated"
      class="custom-snackbar"
    >
      <div class="d-flex align-center">
        <v-icon class="me-2">{{ getSnackbarIcon(snackbar.color) }}</v-icon>
        {{ snackbar.text }}
      </div>
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
          icon="mdi-close"
          size="small"
        ></v-btn>
      </template>
    </v-snackbar>

    <InvoiceDetailDialog 
      v-model="dialogDetail" 
      :invoice="selectedInvoice"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import apiClient from '@/services/api';
import type { Invoice, PelangganSelectItem } from '@/interfaces/invoice';
import InvoiceDetailDialog from '@/components/dialogs/InvoiceDetailDialog.vue';
import { debounce } from 'lodash-es';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

import { useAuthStore } from '@/stores/auth';
const auth = useAuthStore();

// --- State ---
const invoices = ref<Invoice[]>([]);
const invoicesForExistingUserCheck = ref<Invoice[]>([]); // Khusus untuk cek existing user
const pelangganList = ref<PelangganSelectItem[]>([]);
const langgananList = ref<any[]>([]);
const loading = ref(true);
// const customerList = ref([]);
const generating = ref(false);
const searchQuery = ref('');
const dialogGenerate = ref(false);
const selectedLanggananId = ref<number | null>(null);
const dialogDetail = ref(false);
const selectedInvoice = ref<Invoice | null>(null);
const snackbar = ref({ show: false, text: '', color: 'success' });
const dialogDelete = ref(false);
const deleting = ref(false);
const itemToDelete = ref<Invoice | null>(null);
const selectedInvoices = ref<Invoice[]>([]);
const dialogBulkDelete = ref(false);
const dialogMarkAsPaid = ref(false);
const markingAsPaid = ref(false);
const itemToMark = ref<Invoice | null>(null);
const paymentMethod = ref('Cash');
const selectedStatus = ref<string | null>(null);
const startDate = ref<string | null>(null);
const endDate = ref<string | null>(null);
const statusOptions = ref(['Lunas', 'Belum Dibayar', 'Kadaluarsa']);
const showPaidInvoices = ref(false);
const selectedLimit = ref(100);
const limitOptions = ref([
  { title: '50 item', value: 50 },
  { title: '100 item', value: 100 },
  { title: '200 item', value: 200 },
  { title: 'Semua', value: 1000 }
]);
const totalCount = ref(0);

// const newInvoice = ref({
//   pelanggan_id: null,
// });

// --- Table Headers ---
const headers = [
  { title: 'Nomor Invoice', key: 'invoice_number', width: '200px' },
  { title: 'Pelanggan', key: 'pelanggan_id', width: '250px' },
  { title: 'Total Tagihan', key: 'total_harga', align: 'end' as const, width: '150px' },
  { title: 'Status', key: 'status_invoice', align: 'center' as const, width: '130px' },
  { title: 'Jatuh Tempo', key: 'tgl_jatuh_tempo', align: 'center' as const, width: '150px' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' as const, width: '120px' },
];




// --- Computed Properties ---
const langgananForSelect = computed(() => {
  if (!langgananList.value || loading.value) return [];

  // Filter langganan yang valid untuk invoice generation
  return langgananList.value
    .filter(langganan => {
      // Hanya tampilkan langganan dengan status aktif
      if (langganan.status === 'Berhenti' || langganan.status === 'Tidak Aktif') {
        return false;
      }
      return true;
    })
    .map(langganan => {
      // Cari pelanggan yang sesuai dengan langganan ini
      const pelanggan = pelangganList.value?.find(p => p.id === langganan.pelanggan_id);

      // Handle kasus ketika pelanggan tidak ditemukan
      if (!pelanggan) {
        console.error(`❌ Data tidak konsisten: Langganan ID ${langganan.id} mereferensikan pelanggan_id ${langganan.pelanggan_id} yang tidak ada di database pelanggan.`);
        // Tampilkan dengan informasi error yang jelas
        return {
          id: langganan.id,
          title: `❌ ERROR: ID ${langganan.id} - Pelanggan ID ${langganan.pelanggan_id} tidak ditemukan`,
          raw: {
            ...langganan,
            pelanggan: null,
            is_new_user: false,
            has_error: true,
            error_message: `Pelanggan ID ${langganan.pelanggan_id} tidak ditemukan di database`
          },
          disabled: true // Non-aktifkan pilihan ini
        };
      }

      // Check apakah user sudah existing (pernah ada invoice)
      // Gabungkan data dari invoices.value (current) dan invoicesForExistingUserCheck.value (history)
      const allInvoicesForCheck = [
        ...(invoices.value || []),
        ...(invoicesForExistingUserCheck.value || [])
      ];

      const existingInvoices = allInvoicesForCheck.filter(inv => inv.pelanggan_id === pelanggan.id);
      const hasHistoryInvoices = existingInvoices.length > 0;

      
      // NEW USER hanya untuk user yang benar-benar baru (belum pernah ada invoice sama sekali)
      const isNewUser = !hasHistoryInvoices;

      
      // Buat title dengan format yang diinginkan
      const pelangganName = pelanggan.nama || `ID: ${pelanggan.id}`;

      // Build title dengan format yang diinginkan
      const title = isNewUser
        ? `${pelangganName} - (User Baru)`
        : pelangganName;

      return {
        // properti 'id' diperlukan untuk item-value
        id: langganan.id,

        // Properti 'title' dengan format yang lebih informatif
        title: title,

        
        // Objek item mentah (raw item) untuk diakses di template slot
        raw: {
          ...langganan,
          pelanggan: pelanggan,
          // Hitung NEW USER secara client-side (lebih akurat)
          is_new_user: isNewUser,
          has_error: false
        }
      };
    })
    .filter(item => item !== null); // Filter out null items (jika ada)
});

const selectedLanggananDetails = computed(() => {
  if (!selectedLanggananId.value || !langgananList.value) return null;
  const langganan = langgananList.value.find(lang => lang.id === selectedLanggananId.value);
  
  // Tambahkan pengecekan tambahan
  if (!langganan) return null;
  
  // Tambahkan data pelanggan jika tersedia
  const pelanggan = pelangganList.value?.find(p => p.id === langganan.pelanggan_id) || null;
  
  // Pastikan semua field yang dibutuhkan tersedia
  return {
    ...langganan,
    pelanggan: pelanggan,
    harga_awal: langganan.harga_awal || 0,
    tgl_jatuh_tempo: langganan.tgl_jatuh_tempo || new Date()
  };
});

// --- REVISI UTAMA DIMULAI DI SINI ---

// --- Stats Methods --- (Menjadi lebih sederhana)
const getPaidCount = () => {
  if (!invoices.value) return 0;
  return invoices.value.filter(inv => inv.status_invoice === 'Lunas').length;
};
const getPendingCount = () => {
  if (!invoices.value) return 0;
  // Hitung berdasarkan status link pembayaran yang aktif
  return invoices.value.filter(inv => inv.payment_link_status === 'Belum Dibayar').length;
};
const getOverdueCount = () => {
  if (!invoices.value) return 0;
  // Hitung berdasarkan status invoice yang kadaluarsa
  return invoices.value.filter(inv => inv.status_invoice === 'Kadaluarsa').length;
};

// --- Helper Functions --- (Menjadi lebih sederhana)
function getPelangganName(pelangganId: number): string {
  if (!pelangganList.value) return `ID: ${pelangganId}`;
  const pelanggan = pelangganList.value.find(p => p.id === pelangganId);
  return pelanggan?.nama || `ID: ${pelangganId}`;
}

/**
 * Fungsi sederhana untuk mendapatkan warna chip berdasarkan status dari API.
 * TIDAK ADA LAGI PERHITUNGAN TANGGAL.
 */
function getStatusColor(status: string): string {
  switch (status) {
    case 'Lunas': return 'success';
    case 'Kadaluarsa': return 'error';
    case 'Expired': return 'error';  // Status Expired menggunakan warna merah
    case 'Belum Dibayar': return 'warning';
    default: return 'grey';
  }
}

const filteredInvoices = computed(() => {
  // Optimasi: Data sudah difilter di server, jadi tidak perlu filter client-side lagi
  // showPaidInvoices.value = false -> data sudah difilter show_active_only di backend
  // showPaidInvoices.value = true -> data lengkap (tapi dengan limit)
  return invoices.value;
});

/**
 * Fungsi sederhana untuk mendapatkan ikon berdasarkan status dari API.
 * TIDAK ADA LAGI PERHITUNGAN TANGGAL.
 */
function getStatusIcon(status: string): string {
  switch (status) {
    case 'Lunas': return 'mdi-check-circle';
    case 'Kadaluarsa': return 'mdi-alert-circle';
    case 'Expired': return 'mdi-timer-off';  // Icon untuk link expired
    case 'Belum Dibayar': return 'mdi-clock-outline';
    default: return 'mdi-help-circle';
  }
}

/**
 * Menampilkan label sisa waktu atau keterlambatan.
 * Fungsi ini tidak lagi menentukan status 'Kadaluarsa'.
 */
function getDueDateLabel(item: Invoice): string {
  if (item.status_invoice === 'Lunas') return '';

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDate = new Date(item.tgl_jatuh_tempo);
  dueDate.setHours(0, 0, 0, 0);

  const timeDiff = dueDate.getTime() - today.getTime();
  const daysRemaining = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
  
  if (daysRemaining < 0) return `${Math.abs(daysRemaining)} hari terlambat`;
  if (daysRemaining === 0) return 'Jatuh tempo hari ini';
  if (daysRemaining === 1) return 'Jatuh tempo besok';
  return `${daysRemaining} hari lagi`;
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit', month: 'long', year: 'numeric'
  });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value);
}

// --- REVISI UTAMA SELESAI DI SINI ---



// --- Methods --- (Tidak ada perubahan di bawah ini, biarkan seperti semula)
onMounted(() => {
  fetchInvoices();
  fetchPelangganForSelect();
  fetchLanggananForSelect();
  fetchAllInvoicesForExistingUserCheck(); // Load history invoice untuk accurate NEW user detection
  window.addEventListener('new-notification', handleNewNotification);
});

onUnmounted(() => {
  window.removeEventListener('new-notification', handleNewNotification);
});

async function fetchInvoices() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) params.append('search', searchQuery.value);
    if (selectedStatus.value) params.append('status_invoice', selectedStatus.value);
    if (startDate.value) params.append('start_date', startDate.value);
    if (endDate.value) params.append('end_date', endDate.value);

    // Optimasi: Jika switch "Tampilkan Lunas & Kadaluarsa" tidak aktif,
    // filter hanya invoice yang belum dibayar
    if (!showPaidInvoices.value) {
      if (!selectedStatus.value) {  // Jika tidak ada filter status spesifik
        params.append('status_invoice', 'Belum Dibayar');
      }
      // Gunakan limit yang dipilih oleh user
      params.append('limit', selectedLimit.value.toString());
    }

    const response = await apiClient.get<Invoice[]>(`/invoices/?${params.toString()}`);
    invoices.value = response.data.sort((a, b) => b.id - a.id);

    // Ambil total count dari header response atau dari data
    if (response.headers['x-total-count']) {
      totalCount.value = parseInt(response.headers['x-total-count']);
    } else {
      // Fallback: fetch total count jika tidak ada header
      await fetchTotalCount();
    }

      } catch (error) {
    console.error('Error fetching invoices:', error);
    showSnackbar('Gagal memuat data invoice. Silakan coba lagi.', 'error');
  } finally {
    loading.value = false;
  }
}

// Fungsi untuk mendapatkan total count invoice
async function fetchTotalCount() {
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) params.append('search', searchQuery.value);
    if (selectedStatus.value) params.append('status_invoice', selectedStatus.value);
    if (startDate.value) params.append('start_date', startDate.value);
    if (endDate.value) params.append('end_date', endDate.value);

    const response = await apiClient.get(`/invoices/count?${params.toString()}`);
    totalCount.value = response.data || 0;
  } catch (error) {
    console.error('Error fetching total count:', error);
  }
}

// TAMBAHAN: Fungsi khusus untuk fetch semua invoice tanpa filter untuk keperluan cek existing user
async function fetchAllInvoicesForExistingUserCheck() {
  try {
    const params = new URLSearchParams();
    params.append('limit', '1000'); // Load banyak invoice untuk akurasi
    params.append('status_invoice', 'Lunas'); // Prioritaskan invoice lunas untuk history

    const response = await apiClient.get<Invoice[]>(`/invoices/?${params.toString()}`);
    const allInvoices = response.data;

    // Update state untuk existing user check
    if (!invoicesForExistingUserCheck.value) {
      invoicesForExistingUserCheck.value = [];
    }

    // Hanya tambahkan invoice yang belum ada di list
    const newInvoices = allInvoices.filter(inv =>
      !invoicesForExistingUserCheck.value.some(existing => existing.id === inv.id)
    );

    invoicesForExistingUserCheck.value.push(...newInvoices);

      } catch (error) {
    console.error('Error fetching all invoices for existing user check:', error);
  }
}

function sendWhatsAppReminder(invoice: Invoice) {
  let phone = invoice.no_telp || '';
  if (phone.startsWith('0')) {
    phone = '62' + phone.substring(1);
  }
  phone = phone.replace(/[^0-9]/g, '');
  const paymentLink = invoice.payment_link;
  const templateText = `Link Pembayaran Internet dengan Link berikut: ${paymentLink}`;
  const encodedText = encodeURIComponent(templateText);
  const whatsappUrl = `https://wa.me/${phone}?text=${encodedText}`;
  window.open(whatsappUrl, '_blank');
}

const applyFilters = debounce(() => {
  fetchInvoices();
});

watch([searchQuery, selectedStatus, startDate, endDate, selectedLimit], () => {
  applyFilters();
});

watch(showPaidInvoices, () => {
  applyFilters();
});

function resetFilters() {
  searchQuery.value = '';
  selectedStatus.value = null;
  startDate.value = null;
  endDate.value = null;
}

const handleNewNotification = (event: Event) => {
  const customEvent = event as CustomEvent;
  const notificationData = customEvent.detail;
  if (notificationData.type === 'new_payment') {
    // Force refresh invoices dengan sedikit delay untuk memastikan backend sudah update
    setTimeout(() => {
      fetchInvoices();
    }, 1000);
  }
};

async function fetchPelangganForSelect() {
  try {
    // FIX: Gunakan parameter for_invoice_selection=true untuk menghilangkan limit
    const response = await apiClient.get<any>('/pelanggan/?for_invoice_selection=true');

    // Handle response format yang benar (PelangganListResponse has 'data' field)
    let data: any[] = [];
    if (response.data && Array.isArray(response.data.data)) {
      data = response.data.data;
    } else if (Array.isArray(response.data)) {
      data = response.data;
    } else {
      console.error("❌ Unexpected response format:", response.data);
      pelangganList.value = [];
      showSnackbar('Format data pelanggan tidak valid.', 'error');
      return;
    }

    pelangganList.value = data;

      } catch (error) {
    console.error('❌ Error fetching pelanggan list:', error);
    showSnackbar('Gagal memuat daftar pelanggan.', 'error');
  }
}

async function fetchLanggananForSelect() {
  try {
    // QUICK FIX: Tambahkan limit besar untuk memastikan semua data ter-load
    const response = await apiClient.get<any>(
      '/langganan/?for_invoice_selection=true&limit=1000'
    );
    const data = Array.isArray(response.data) ? response.data : response.data.data;

    if (Array.isArray(data)) {
      langgananList.value = data;
          } else {
      console.error("❌ Fetched langgananList is not an array:", response.data);
      langgananList.value = []; // Fallback to empty array
      showSnackbar('Format data langganan tidak valid.', 'warning');
    }
  } catch (error) {
    console.error('❌ Error fetching langganan:', error);
    showSnackbar('Gagal memuat daftar langganan.', 'warning');
  }
}

function openDetailDialog(item: Invoice) {
  selectedInvoice.value = item;
  dialogDetail.value = true;
}

function openGenerateDialog() {
  selectedLanggananId.value = null;
  dialogGenerate.value = true;
}

async function generateManualInvoice() {
  if (!selectedLanggananId.value) return;

  // Validasi tambahan untuk mencegah error
  const selectedLangganan = langgananForSelect.value.find(item => item.id === selectedLanggananId.value);
  if (!selectedLangganan) {
    showSnackbar('Langganan yang dipilih tidak valid.', 'error');
    return;
  }

  // Cek apakah langganan memiliki error
  if (selectedLangganan.raw?.has_error) {
    showSnackbar(selectedLangganan.raw.error_message || 'Data langganan tidak konsisten. Hubungi admin.', 'error');
    return;
  }

  // Cek apakah pelanggan tersedia
  if (!selectedLangganan.raw?.pelanggan) {
    showSnackbar('Data pelanggan tidak lengkap. Hubungi admin untuk perbaikan data.', 'error');
    return;
  }

  generating.value = true;
  try {
    await apiClient.post('/invoices/generate', {
      langganan_id: selectedLanggananId.value
    });
    showSnackbar(`Invoice berhasil dibuat untuk ${selectedLangganan.raw.pelanggan.nama}!`, 'success');
    fetchInvoices();
    closeDialog();
  } catch (error: any) {
    const detail = error.response?.data?.detail || 'Gagal membuat invoice.';

    // Handle error spesifik untuk data tidak konsisten
    if (detail.includes('tidak ditemukan')) {
      showSnackbar('⚠️ Data tidak konsisten! Silakan refresh halaman atau hubungi admin.', 'error');
      // Refresh data untuk memperbarui tampilan
      await Promise.all([
        fetchLanggananForSelect(),
        fetchPelangganForSelect()
      ]);
    } else {
      showSnackbar(detail, 'error');
    }
  } finally {
    generating.value = false;
  }
}

function closeDialog() {
  dialogGenerate.value = false;
  selectedLanggananId.value = null;
}

async function copyPaymentLink(link: string | null | undefined) {
  if (!link) {
    showSnackbar('Tidak ada link pembayaran', 'warning');
    return;
  }
  try {
    await navigator.clipboard.writeText(link);
    showSnackbar('Link pembayaran berhasil disalin!', 'success');
  } catch (err) {
    showSnackbar('Gagal menyalin link', 'error');
  }
}

function showSnackbar(text: string, color: string) {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

function getSnackbarIcon(color: string): string {
  switch (color) {
    case 'success': return 'mdi-check-circle';
    case 'error': return 'mdi-alert-circle';
    case 'warning': return 'mdi-alert';
    default: return 'mdi-information';
  }
}

function openDeleteDialog(item: Invoice) {
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
    await apiClient.delete(`/invoices/${itemToDelete.value.id}`);
    showSnackbar('Invoice berhasil dihapus', 'success');
    fetchInvoices();
    closeDeleteDialog();
  } catch (error: any) {
    const detail = error.response?.data?.detail || 'Gagal menghapus invoice.';
    showSnackbar(detail, 'error');
  } finally {
    deleting.value = false;
  }
}

async function confirmBulkDelete() {
  const itemsToDelete = [...selectedInvoices.value];
  if (itemsToDelete.length === 0) return;
  deleting.value = true;
  try {
    const deletePromises = itemsToDelete.map(invoice =>
      apiClient.delete(`/invoices/${invoice.id}`)
    );
    await Promise.all(deletePromises);
    showSnackbar(`${itemsToDelete.length} invoice berhasil dihapus.`, 'success');
    fetchInvoices();
    selectedInvoices.value = [];
  } catch (error) {
    showSnackbar('Terjadi kesalahan saat menghapus data.', 'error');
  } finally {
    deleting.value = false;
    dialogBulkDelete.value = false;
  }
}

function openMarkAsPaidDialog(item: Invoice) {
  itemToMark.value = item;
  paymentMethod.value = 'Cash';
  dialogMarkAsPaid.value = true;
}

function closeMarkAsPaidDialog() {
  dialogMarkAsPaid.value = false;
  itemToMark.value = null;
}

async function confirmMarkAsPaid() {
  if (!itemToMark.value) return;
  markingAsPaid.value = true;
  try {
    await apiClient.post(`/invoices/${itemToMark.value.id}/mark-as-paid`, {
      metode_pembayaran: paymentMethod.value
    });
    showSnackbar('Invoice berhasil ditandai lunas', 'success');
    fetchInvoices();
    closeMarkAsPaidDialog();
  } catch (error: any) {
    const detail = error.response?.data?.detail || 'Gagal menandai lunas.';
    showSnackbar(detail, 'error');
  } finally {
    markingAsPaid.value = false;
  }
}

function exportPaymentLinksExcel() {
  try {
    // Bangun URL dengan parameter filter
    let url = '/invoices/export-payment-links-excel';
    const params = new URLSearchParams();
    
    if (searchQuery.value) params.append('search', searchQuery.value);
    if (selectedStatus.value) params.append('status_invoice', selectedStatus.value);
    if (startDate.value) params.append('start_date', startDate.value);
    if (endDate.value) params.append('end_date', endDate.value);
    
    // Jika switch "Tampilkan Lunas & Kadaluarsa" tidak aktif dan tidak ada filter status spesifik,
    // maka kita hanya ingin mengekspor invoice yang belum dibayar
    if (!showPaidInvoices.value && !selectedStatus.value) {
      params.append('status_invoice', 'Belum Dibayar');
    }
    
    if (params.toString()) {
      url += '?' + params.toString();
    }
    
    // Unduh file
    window.open(apiClient.defaults.baseURL + url, '_blank');
    showSnackbar('File Excel sedang diunduh...', 'success');
  } catch (error) {
    console.error('Error exporting payment links:', error);
    showSnackbar('Gagal mengunduh file Excel', 'error');
  }
}
</script>

<style scoped>
/* MENAMBAHKAN STYLE BARU UNTUK KARTU MOBILE */
.invoice-card-mobile {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;
}
.invoice-card-mobile:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
.invoice-card-mobile .v-list-item {
  min-height: auto;
  padding-top: 8px;
  padding-bottom: 8px;
}
.invoice-card-mobile .v-list-item-title {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
}
.invoice-card-mobile .v-list-item__append {
  font-size: 0.9rem;
  font-weight: 500;
}
/* ------------------------------------------- */

.responsive-table-container {
  overflow-x: auto;
  width: 100%;
}

/* Main Header with gradient */
.invoice-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.theme--dark .invoice-header {
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
}

.icon-container {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
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

.selection-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.15);
}

.filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(var(--v-theme-shadow), 0.12),
    0 2px 6px rgba(var(--v-theme-shadow), 0.16);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

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

.filter-card .d-flex {
  padding: 28px 32px !important;
  gap: 20px !important;
}

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

.filter-card .v-field :deep(.v-field__label) {
  color: rgba(var(--v-theme-on-surface), 0.7) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
}

.filter-card .v-field--focused :deep(.v-field__label) {
  color: rgb(var(--v-theme-primary)) !important;
}

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

@media (max-width: 1280px) {
  .filter-card .d-flex {
    flex-direction: column !important;
  }
}

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

.filter-card .v-field--loading :deep(.v-field) {
  opacity: 0.7;
}

.filter-card * {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-field--focused :deep(.v-field__outline) {
  border-width: 2px !important;
  border-color: rgb(var(--v-theme-primary)) !important;
}

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

/* Stats Cards */
.stats-card {
  border-radius: 16px;
  transition: all 0.3s ease;
  border: 1px solid rgba(0,0,0,0.05);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
}

.theme--dark .stats-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-icon.success { background: rgba(76, 175, 80, 0.1); }
.stats-icon.warning { background: rgba(255, 152, 0, 0.1); }
.stats-icon.error { background: rgba(244, 67, 54, 0.1); }
.stats-icon.primary { background: rgba(103, 58, 183, 0.1); }

/* Invoice Table Card */
.invoice-table-card {
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.05);
}

.theme--dark .invoice-table-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.table-header {
  border-bottom: 1px solid rgba(0,0,0,0.08);
}

.theme--dark .table-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-field :deep(.v-field) {
  border-radius: 12px;
}

.invoice-table :deep(.v-data-table__td) {
  padding: 16px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.theme--dark .invoice-table :deep(.v-data-table__td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.invoice-table :deep(.v-data-table__tr:hover) {
  background: rgba(103, 58, 183, 0.04) !important;
}

.theme--dark .invoice-table :deep(.v-data-table__tr:hover) {
  background: rgba(103, 58, 183, 0.1) !important;
}

/* Cell Styling */
.invoice-number-cell,
.customer-cell,
.amount-cell,
.due-date-cell {
  padding: 4px 0;
}

.status-chip {
  min-width: 100px;
  border-radius: 12px !important;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.action-btn {
  border-radius: 8px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(103, 58, 183, 0.1);
  transform: scale(1.05);
}

/* Dialog Styling */
.generate-dialog {
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.dialog-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.theme--dark .dialog-header {
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
}

.custom-snackbar {
  border-radius: 12px;
}

/* NEW USER Chip Styling */
:deep(.v-list-item .v-chip) {
  font-weight: 600;
  font-size: 11px;
}

:deep(.v-list-item .v-chip .v-chip__prepend) {
  margin-right: 4px;
}

.new-user-badge {
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(76, 175, 80, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
  }
}

/* Enhanced Autocomplete styling for better NEW USER visibility */
:deep(.v-autocomplete .v-field__input) {
  font-weight: 500;
}
</style>