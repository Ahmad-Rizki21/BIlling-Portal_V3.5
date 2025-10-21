<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:modelValue="$emit('update:modelValue', $event)" 
    max-width="900px"
    :scrim="false"
    class="invoice-dialog"
  >
    <v-card v-if="invoice" class="invoice-detail-dialog elevation-0" rounded="xl">
      <!-- Header Section -->
      <v-card-title class="pa-0">
        <div class="header-section pa-6 position-relative overflow-hidden rounded-t-xl">
          <!-- Subtle background pattern -->
          <div class="header-pattern"></div>
          
          <div class="d-flex align-center position-relative">
            <div class="header-icon-wrapper me-4">
              <v-icon size="28" class="header-icon">mdi-receipt-text-check-outline</v-icon>
            </div>
            <div class="flex-grow-1">
              <h2 class="text-h5 font-weight-bold mb-1 header-title">Detail Invoice</h2>
              <p class="text-subtitle-1 mb-0 header-subtitle">{{ invoice.invoice_number }}</p>
            </div>
            <v-chip 
              :color="statusColor" 
              size="large"
              variant="elevated"
              class="font-weight-bold status-chip"
              prepend-icon="mdi-check-circle"
            >
              {{ invoice.status_invoice }}
            </v-chip>
          </div>
        </div>
      </v-card-title>

      <v-card-text class="pa-0">
        <!-- Main Content -->
        <div class="content-section pa-6">
          <v-row class="mb-6">
            <!-- Billing Information -->
            <v-col cols="12" md="6">
              <div class="info-card">
                <div class="card-header">
                  <div class="card-icon-wrapper">
                    <v-icon size="20" class="card-icon">mdi-file-document-outline</v-icon>
                  </div>
                  <h3 class="card-title">Informasi Tagihan</h3>
                </div>
                
                <div class="card-content">
                  <div class="info-row">
                    <span class="info-label">Tanggal Invoice</span>
                    <span class="info-value">{{ formatDate(invoice.tgl_invoice) }}</span>
                  </div>
                  
                  <div class="info-row">
                    <span class="info-label">Jatuh Tempo</span>
                    <span class="info-value">{{ formatDate(invoice.tgl_jatuh_tempo) }}</span>
                  </div>
                  
                  <div class="info-row highlight-row">
                    <span class="info-label">Total Tagihan</span>
                    <span class="info-value total-amount">{{ formatCurrency(invoice.total_harga) }}</span>
                  </div>
                  
                  <div v-if="invoice.paid_at" class="info-row paid-row">
                    <span class="info-label">Tanggal Lunas</span>
                    <span class="info-value paid-value">{{ formatDateTime(invoice.paid_at) }}</span>
                  </div>
                </div>
              </div>
            </v-col>
            
            <!-- Customer Information -->
            <v-col cols="12" md="6">
              <div class="info-card">
                <div class="card-header">
                  <div class="card-icon-wrapper secondary">
                    <v-icon size="20" class="card-icon">mdi-account-circle-outline</v-icon>
                  </div>
                  <h3 class="card-title">Informasi Pelanggan</h3>
                </div>
                
                <div class="card-content">
                  <div class="info-row">
                    <span class="info-label">ID PPPoE / ID Pelanggan</span>
                    <span class="info-value">{{ invoice.id_pelanggan }}</span>
                  </div>
                  
                  <div class="info-row">
                    <span class="info-label">Email</span>
                    <span class="info-value">{{ invoice.email }}</span>
                  </div>
                  
                  <div class="info-row">
                    <span class="info-label">No. Telepon</span>
                    <span class="info-value">{{ invoice.no_telp }}</span>
                  </div>
                </div>
              </div>
            </v-col>
          </v-row>
          
          <!-- Payment Information -->
          <div class="payment-section">
            <div class="card-header mb-4">
              <div class="card-icon-wrapper info">
                <v-icon size="20" class="card-icon">mdi-credit-card-outline</v-icon>
              </div>
              <h3 class="card-title">Informasi Pembayaran (Xendit)</h3>
            </div>
            
            <div class="payment-link-wrapper">
              <v-text-field
                :model-value="invoice.payment_link"
                label="Link Pembayaran"
                variant="outlined"
                density="comfortable"
                readonly
                class="payment-link-field"
                prepend-inner-icon="mdi-link-variant"
                color="primary"
              >
                <template v-slot:append-inner>
                  <v-btn
                    icon="mdi-content-copy"
                    size="small"
                    variant="text"
                    class="copy-btn"
                    @click="copyPaymentLink"
                  ></v-btn>
                </template>
              </v-text-field>
            </div>
          </div>
        </div>
      </v-card-text>

      <!-- Footer Actions -->
      <v-card-actions class="pa-6 pt-0">
        <v-spacer></v-spacer>
        <v-btn 
          variant="elevated"
          color="primary"
          size="large"
          class="close-btn"
          @click="$emit('update:modelValue', false)"
        >
          <v-icon start>mdi-close</v-icon>
          Tutup
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Invoice } from '@/interfaces/invoice';

const props = defineProps<{
  modelValue: boolean,
  invoice: Invoice | null
}>();

defineEmits(['update:modelValue']);

// Helper functions (bisa juga di-import dari file terpisah)
const statusColor = computed(() => {
  switch (props.invoice?.status_invoice) {
    case 'Lunas': return 'success';
    case 'Belum Dibayar': return 'warning';
    case 'Kadaluarsa': return 'error';
    default: return 'grey';
  }
});

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit', month: 'long', year: 'numeric'
  });
}

function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('id-ID', {
    day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

function formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'Rp 0';
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value);
}

async function copyPaymentLink() {
  if (!props.invoice?.payment_link) return;
  try {
    await navigator.clipboard.writeText(props.invoice.payment_link);
    // Bisa tambahkan notifikasi snackbar di sini jika diinginkan
    alert('Link pembayaran disalin!');
  } catch (err) {
    alert('Gagal menyalin link.');
  }
}
</script>

<style scoped>
/* Dialog Base - Light Mode */
.invoice-detail-dialog {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(20px);
}

/* Header Section - Light Mode */
.header-section {
  background: linear-gradient(135deg, 
    hsl(from rgb(var(--v-theme-primary)) h s l / 0.08) 0%, 
    hsl(from rgb(var(--v-theme-primary)) h s l / 0.04) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.08);
  position: relative;
}

.header-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 25% 25%, hsl(from rgb(var(--v-theme-primary)) h s l / 0.03) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, hsl(from rgb(var(--v-theme-secondary)) h s l / 0.02) 0%, transparent 50%);
}

.header-icon-wrapper {
  background: hsl(from rgb(var(--v-theme-primary)) h s l / 0.1);
  border: 1px solid hsl(from rgb(var(--v-theme-primary)) h s l / 0.15);
  border-radius: 12px;
  padding: 12px;
  transition: all 0.3s ease;
}

.header-icon {
  color: rgb(var(--v-theme-primary));
  transition: all 0.3s ease;
}

.header-title {
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  color: rgb(var(--v-theme-on-surface-variant));
  font-weight: 500;
}

.status-chip {
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Info Cards - Light Mode */
.info-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  border-radius: 16px;
  padding: 24px;
  height: 100%;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

/* Card Headers */
.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.card-icon-wrapper {
  background: hsl(from rgb(var(--v-theme-primary)) h s l / 0.1);
  border: 1px solid hsl(from rgb(var(--v-theme-primary)) h s l / 0.15);
  border-radius: 8px;
  padding: 8px;
  margin-right: 12px;
  transition: all 0.3s ease;
}

.card-icon-wrapper.secondary {
  background: hsl(from rgb(var(--v-theme-secondary)) h s l / 0.1);
  border-color: hsl(from rgb(var(--v-theme-secondary)) h s l / 0.15);
}

.card-icon-wrapper.info {
  background: hsl(from rgb(var(--v-theme-info)) h s l / 0.1);
  border-color: hsl(from rgb(var(--v-theme-info)) h s l / 0.15);
}

.card-icon {
  color: rgb(var(--v-theme-primary));
}

.card-icon-wrapper.secondary .card-icon {
  color: rgb(var(--v-theme-secondary));
}

.card-icon-wrapper.info .card-icon {
  color: rgb(var(--v-theme-info));
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

/* Card Content */
.card-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.08);
  transition: all 0.2s ease;
}

.info-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-row:hover {
  background: hsl(from rgb(var(--v-theme-primary)) h s l / 0.02);
  margin: 0 -16px;
  padding: 12px 16px;
  border-radius: 8px;
}

.info-label {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 0.9rem;
}

.info-value {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  text-align: right;
  margin-left: 16px;
  font-size: 0.9rem;
}

/* Highlight Row */
.highlight-row {
  background: linear-gradient(135deg, 
    hsl(from rgb(var(--v-theme-primary)) h s l / 0.06) 0%, 
    hsl(from rgb(var(--v-theme-primary)) h s l / 0.03) 100%);
  border: 1px solid hsl(from rgb(var(--v-theme-primary)) h s l / 0.15);
  border-radius: 12px;
  padding: 16px !important;
  margin: 8px -16px;
}

.highlight-row:hover {
  margin: 8px -16px;
  padding: 16px !important;
}

.total-amount {
  font-size: 1.2rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

/* Paid Row */
.paid-row {
  background: linear-gradient(135deg, 
    hsl(from rgb(var(--v-theme-success)) h s l / 0.06) 0%, 
    hsl(from rgb(var(--v-theme-success)) h s l / 0.03) 100%);
  border: 1px solid hsl(from rgb(var(--v-theme-success)) h s l / 0.15);
  border-radius: 12px;
  padding: 16px !important;
  margin: 8px -16px;
}

.paid-row:hover {
  margin: 8px -16px;
  padding: 16px !important;
}

.paid-value {
  color: rgb(var(--v-theme-success));
  font-weight: 700;
}

/* Payment Section - Light Mode */
.payment-section {
  background: linear-gradient(135deg, 
    hsl(from rgb(var(--v-theme-info)) h s l / 0.04) 0%, 
    hsl(from rgb(var(--v-theme-info)) h s l / 0.02) 100%);
  border: 1px solid hsl(from rgb(var(--v-theme-info)) h s l / 0.12);
  border-radius: 16px;
  padding: 24px;
  margin-top: 24px;
}

.payment-link-field :deep(.v-field) {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
}

.payment-link-field :deep(.v-field__outline) {
  border-color: rgba(var(--v-theme-outline), 0.2);
}

.payment-link-field:hover :deep(.v-field__outline) {
  border-color: rgba(var(--v-theme-primary), 0.4);
}

.copy-btn {
  color: rgb(var(--v-theme-primary));
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: hsl(from rgb(var(--v-theme-primary)) h s l / 0.1);
  transform: scale(1.05);
}

/* Close Button */
.close-btn {
  border-radius: 12px;
  padding: 0 32px;
  height: 44px;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

/* DARK MODE - Perbaikan untuk tampilan yang sesuai */
.v-theme--dark .invoice-detail-dialog {
  background: rgb(24, 26, 32); /* Dark background yang tepat */
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
}

.v-theme--dark .header-section {
  background: linear-gradient(135deg, 
    rgba(96, 165, 250, 0.15) 0%, 
    rgba(96, 165, 250, 0.08) 100%);
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .header-title {
  color: rgba(255, 255, 255, 0.95);
}

.v-theme--dark .header-subtitle {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .info-card {
  background: rgb(30, 33, 39); /* Card background yang lebih gelap */
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .info-card:hover {
  background: rgb(35, 38, 44);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  border-color: rgba(96, 165, 250, 0.3);
}

.v-theme--dark .card-title {
  color: rgba(255, 255, 255, 0.95);
}

.v-theme--dark .info-label {
  color: rgba(255, 255, 255, 0.6);
}

.v-theme--dark .info-value {
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .info-row {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.v-theme--dark .info-row:hover {
  background: rgba(96, 165, 250, 0.05);
}

.v-theme--dark .highlight-row {
  background: linear-gradient(135deg, 
    rgba(96, 165, 250, 0.15) 0%, 
    rgba(96, 165, 250, 0.08) 100%);
  border-color: rgba(96, 165, 250, 0.3);
}

.v-theme--dark .paid-row {
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.15) 0%, 
    rgba(34, 197, 94, 0.08) 100%);
  border-color: rgba(34, 197, 94, 0.3);
}

.v-theme--dark .payment-section {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.12) 0%, 
    rgba(59, 130, 246, 0.06) 100%);
  border-color: rgba(59, 130, 246, 0.2);
}

.v-theme--dark .payment-link-field :deep(.v-field) {
  background: rgb(30, 33, 39);
  color: rgba(255, 255, 255, 0.9);
}

.v-theme--dark .payment-link-field :deep(.v-field__outline) {
  border-color: rgba(255, 255, 255, 0.15);
}

.v-theme--dark .payment-link-field :deep(.v-field-label) {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .payment-link-field :deep(.v-field__input) {
  color: rgba(255, 255, 255, 0.9);
}

/* Light Mode - Perbaikan styling untuk tampilan terang */
.v-theme--light .invoice-detail-dialog {
  background: rgb(255, 255, 255);
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
}

.v-theme--light .header-section {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.06) 0%, 
    rgba(59, 130, 246, 0.03) 100%);
  border-bottom-color: rgba(0, 0, 0, 0.05);
}

.v-theme--light .header-title {
  color: rgb(33, 37, 41);
}

.v-theme--light .header-subtitle {
  color: rgb(108, 117, 125);
}

.v-theme--light .info-card {
  background: rgb(255, 255, 255);
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.v-theme--light .info-card:hover {
  background: rgb(255, 255, 255);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.v-theme--light .card-title {
  color: rgb(33, 37, 41);
}

.v-theme--light .info-label {
  color: rgb(108, 117, 125);
}

.v-theme--light .info-value {
  color: rgb(33, 37, 41);
}

.v-theme--light .info-row {
  border-bottom-color: rgba(0, 0, 0, 0.05);
}

.v-theme--light .info-row:hover {
  background: rgba(59, 130, 246, 0.03);
}

.v-theme--light .highlight-row {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.08) 0%, 
    rgba(59, 130, 246, 0.04) 100%);
  border-color: rgba(59, 130, 246, 0.2);
}

.v-theme--light .paid-row {
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.08) 0%, 
    rgba(34, 197, 94, 0.04) 100%);
  border-color: rgba(34, 197, 94, 0.2);
}

.v-theme--light .payment-section {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.04) 0%, 
    rgba(59, 130, 246, 0.02) 100%);
  border-color: rgba(59, 130, 246, 0.12);
}

.v-theme--light .payment-link-field :deep(.v-field) {
  background: rgb(255, 255, 255);
  color: rgb(33, 37, 41);
}

.v-theme--light .payment-link-field :deep(.v-field__outline) {
  border-color: rgba(0, 0, 0, 0.12);
}

.v-theme--light .payment-link-field :deep(.v-field-label) {
  color: rgb(108, 117, 125);
}

.v-theme--light .payment-link-field :deep(.v-field__input) {
  color: rgb(33, 37, 41);
}


/* Responsive Design */
@media (max-width: 768px) {
  .header-section {
    padding: 20px !important;
  }
  
  .content-section {
    padding: 20px !important;
  }
  
  .info-card {
    padding: 20px;
  }
  
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 16px 0;
  }
  
  .info-value {
    text-align: left;
    margin-left: 0;
  }
  
  .highlight-row,
  .paid-row {
    margin: 8px 0;
    padding: 16px !important;
  }
  
  .highlight-row:hover,
  .paid-row:hover {
    margin: 8px 0;
    padding: 16px !important;
  }
  
  .payment-section {
    padding: 20px;
  }
}

/* Smooth Animations */
.invoice-dialog :deep(.v-dialog) {
  animation: modalSlideIn 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translate3d(0, 20px, 0) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}

/* Micro Interactions */
.card-icon-wrapper:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
}

.status-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Focus States */
.copy-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.close-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}
</style>