<template>
  <v-container fluid class="calculator-container">
    <!-- Header Section -->
    <div class="page-header mb-6">
      <div class="header-content">
        <div class="header-icon-wrapper">
          <v-icon size="32">mdi-calculator</v-icon>
        </div>
        <div>
          <h1 class="page-title">Simulasi Harga</h1>
          <p class="page-subtitle">Simulasi perhitungan harga prorate untuk layanan FTTH</p>
        </div>
      </div>
    </div>

    <v-row>
      <!-- Form Section -->
      <v-col cols="12" lg="5" md="6">
        <v-card class="calculator-form-card" elevation="0">
          <v-card-title class="form-card-header">
            <v-icon class="me-2" color="primary">mdi-form-select</v-icon>
            Form Kalkulasi
          </v-card-title>
          
          <v-card-text class="form-content">
            <!-- Brand Selection -->
            <div class="input-group mb-6">
              <label class="input-label">
                <v-icon size="18" class="me-2">mdi-domain</v-icon>
                Pilih Brand
              </label>
              <v-select
                v-model="selectedBrand"
                :items="brandList"
                item-title="brand"
                item-value="id_brand"
                return-object
                variant="outlined"
                density="comfortable"
                class="modern-select"
                placeholder="Pilih brand layanan"
                :prepend-inner-icon="selectedBrand ? 'mdi-check-circle' : 'mdi-circle-outline'"
                :color="selectedBrand ? 'success' : 'primary'"
              ></v-select>
            </div>

            <!-- Package Selection -->
            <div class="input-group mb-6">
              <label class="input-label">
                <v-icon size="18" class="me-2">mdi-package-variant</v-icon>
                Pilih Paket Layanan
              </label>
              <v-select
                v-model="selectedPaket"
                :items="filteredPaketList"
                item-title="nama_paket"
                item-value="id"
                variant="outlined"
                density="comfortable"
                class="modern-select"
                :disabled="!selectedBrand"
                placeholder="Pilih paket layanan"
                :prepend-inner-icon="selectedPaket ? 'mdi-check-circle' : 'mdi-circle-outline'"
                :color="selectedPaket ? 'success' : 'primary'"
                :loading="!selectedBrand"
              ></v-select>
            </div>

            <!-- Date Selection -->
            <div class="input-group mb-4">
              <label class="input-label">
                <v-icon size="18" class="me-2">mdi-calendar</v-icon>
                Tanggal Mulai Layanan
              </label>
              <v-text-field
                v-model="startDate"
                type="date"
                variant="outlined"
                density="comfortable"
                class="modern-input"
                :disabled="!selectedPaket"
                :prepend-inner-icon="startDate ? 'mdi-check-circle' : 'mdi-circle-outline'"
                :color="startDate ? 'success' : 'primary'"
              ></v-text-field>
            </div>
            
            <!-- Include Next Month Toggle -->
            <div class="input-group mb-4">
              <label class="input-label">
                <v-icon size="18" class="me-2">mdi-calendar-plus</v-icon>
                Opsi Harga
              </label>
              <v-switch
                v-model="includeNextMonth"
                label="Termasuk harga bulan depan (dengan PPN)"
                color="primary"
                inset
                class="mt-2"
                hide-details
              ></v-switch>
            </div>

            <!-- Progress Indicator -->
            <div class="progress-section">
              <div class="progress-header mb-3">
                <span class="progress-title">Progress Pengisian</span>
                <span class="progress-percentage">{{ completionPercentage }}%</span>
              </div>
              <v-progress-linear
                :model-value="completionPercentage"
                color="primary"
                height="6"
                rounded
                class="progress-bar"
              ></v-progress-linear>
              <div class="progress-steps mt-3">
                <div class="step" :class="{ active: selectedBrand }">
                  <v-icon size="16" :color="selectedBrand ? 'success' : 'grey'">
                    {{ selectedBrand ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Brand</span>
                </div>
                <div class="step" :class="{ active: selectedPaket }">
                  <v-icon size="16" :color="selectedPaket ? 'success' : 'grey'">
                    {{ selectedPaket ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Paket</span>
                </div>
                <div class="step" :class="{ active: startDate }">
                  <v-icon size="16" :color="startDate ? 'success' : 'grey'">
                    {{ startDate ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Tanggal</span>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Result Section -->
      <v-col cols="12" lg="7" md="6">
        <v-card class="result-card" elevation="0">
          <v-card-title class="result-card-header">
            <v-icon class="me-2" color="success">mdi-calculator-variant</v-icon>
            Hasil Simulasi
          </v-card-title>
          
          <v-card-text class="result-content">
            <!-- Empty State -->
            <div v-if="!calculationResult" class="empty-state">
              <div class="empty-illustration">
                <v-icon size="80" color="grey-lighten-1">mdi-calculator-variant-outline</v-icon>
              </div>
              <h3 class="empty-title">Siap Menghitung!</h3>
              <p class="empty-description">
                Lengkapi form di sebelah kiri untuk melihat simulasi harga prorate
              </p>
              <div class="empty-checklist mt-4">
                <div class="checklist-item" :class="{ completed: selectedBrand }">
                  <v-icon size="18" :color="selectedBrand ? 'success' : 'grey'">
                    {{ selectedBrand ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Pilih Brand</span>
                </div>
                <div class="checklist-item" :class="{ completed: selectedPaket }">
                  <v-icon size="18" :color="selectedPaket ? 'success' : 'grey'">
                    {{ selectedPaket ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Pilih Paket Layanan</span>
                </div>
                <div class="checklist-item" :class="{ completed: startDate }">
                  <v-icon size="18" :color="startDate ? 'success' : 'grey'">
                    {{ startDate ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Pilih Tanggal Mulai</span>
                </div>
              </div>
            </div>

            <!-- Result Display -->
            <div v-else class="result-display">
              <!-- Header Info -->
              <div class="result-header mb-4">
                <v-chip color="success" variant="tonal" size="small" class="mb-2">
                  <v-icon start>mdi-check-circle</v-icon>
                  Kalkulasi Berhasil
                </v-chip>
                <div class="selected-info">
                  <p class="selected-brand">{{ selectedBrand?.brand }}</p>
                  <p class="selected-package">{{ filteredPaketList.find(p => p.id === selectedPaket)?.nama_paket }}</p>
                </div>
              </div>

              <!-- Calculation Details -->
              <div class="calculation-grid">
                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="info">mdi-calendar-range</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Periode Tagihan</div>
                    <div class="calc-value">{{ calculationResult.periode_hari }} hari</div>
                  </div>
                </div>

                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="primary">mdi-cash</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Harga Dasar (Prorate)</div>
                    <div class="calc-value">{{ formatCurrency(calculationResult.harga_dasar_prorate) }}</div>
                  </div>
                </div>

                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="warning">mdi-percent</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Pajak ({{ selectedBrand?.pajak || 0 }}%)</div>
                    <div class="calc-value">{{ formatCurrency(calculationResult.pajak) }}</div>
                  </div>
                </div>
              </div>

              <!-- Total Section -->
              <v-divider class="my-4"></v-divider>
              <div class="total-section">
                <div class="total-wrapper">
                  <div class="total-icon">
                    <v-icon size="24" color="success">mdi-calculator</v-icon>
                  </div>
                  <div class="total-content">
                    <div class="total-label">Total Tagihan</div>
                    <div class="total-amount">{{ formatCurrency(calculationResult.total_harga_prorate) }}</div>
                  </div>
                </div>
                
                <!-- Next Month Price with PPN -->
                <div v-if="includeNextMonth && calculationResult.total_bulan_depan_dengan_ppn !== null" class="next-month-section mt-4">
                  <div class="d-flex align-center justify-space-between">
                    <div class="next-month-info">
                      <div class="next-month-label text-medium-emphasis">Harga Bulan Depan + PPN</div>
                      <div class="next-month-amount">{{ formatCurrency(calculationResult.total_bulan_depan_dengan_ppn || 0) }}</div>
                    </div>
                    <v-chip color="success" size="small" variant="tonal">
                      <v-icon start>mdi-percent</v-icon>
                      Dengan PPN
                    </v-chip>
                  </div>

                  <!-- PPN Breakdown -->
                  <div v-if="calculationResult.ppn_bulan_depan" class="ppn-breakdown mt-3">
                    <div class="d-flex justify-space-between mb-1">
                      <span class="text-medium-emphasis">Harga Dasar Bulan Depan:</span>
                      <span>{{ formatCurrency(calculationResult.harga_bulan_depan || 0) }}</span>
                    </div>
                    <div class="d-flex justify-space-between mb-2">
                      <span class="text-medium-emphasis">PPN ({{ selectedBrand?.pajak || 0 }}%):</span>
                      <span class="text-success">{{ formatCurrency(calculationResult.ppn_bulan_depan) }}</span>
                    </div>
                  </div>

                  <v-divider class="my-3"></v-divider>
                  <div class="d-flex align-center justify-space-between">
                    <div class="grand-total-label">Total Keseluruhan</div>
                    <div class="grand-total-amount font-weight-bold text-h6">
                      {{ formatCurrency(calculationResult.total_keseluruhan || 0) }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="result-actions mt-4">
                <v-btn
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-refresh"
                  @click="resetCalculation"
                  class="me-2"
                >
                  Hitung Ulang
                </v-btn>
                <v-btn
                  color="success"
                  variant="tonal"
                  prepend-icon="mdi-content-copy"
                  @click="copyResult"
                >
                  Salin Hasil
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import apiClient from '@/services/api';
import { debounce } from 'lodash-es';

// Interfaces
interface Brand { id_brand: string; brand: string; pajak: number; }
interface Paket { id: number; id_brand: string; nama_paket: string; harga: number; }
interface ProrateResult {
  harga_dasar_prorate: number;
  pajak: number;
  total_harga_prorate: number;
  periode_hari: number;
  harga_bulan_depan?: number | null;
  ppn_bulan_depan?: number | null;
  total_bulan_depan_dengan_ppn?: number | null;
  total_keseluruhan?: number | null;
}

// State
const brandList = ref<Brand[]>([]);
const paketList = ref<Paket[]>([]);
const selectedBrand = ref<Brand | null>(null);
const selectedPaket = ref<number | null>(null);
const startDate = ref(new Date().toISOString().split('T')[0]);
const calculationResult = ref<ProrateResult | null>(null);
const includeNextMonth = ref(false);
const fullMonthlyPrice = ref<number | null>(null);

// Computed
const filteredPaketList = computed(() => {
  if (!selectedBrand.value) return [];
  return paketList.value.filter(p => p.id_brand === selectedBrand.value?.id_brand);
});

const completionPercentage = computed(() => {
  let completed = 0;
  if (selectedBrand.value) completed += 33.33;
  if (selectedPaket.value) completed += 33.33;
  if (startDate.value) completed += 33.34;
  return Math.round(completed);
});


// Watcher to trigger calculation
watch([selectedBrand, selectedPaket, startDate, includeNextMonth], debounce(async () => {
  if (selectedBrand.value && selectedPaket.value && startDate.value) {
    try {
      const response = await apiClient.post('/calculator/prorate', {
        id_brand: selectedBrand.value.id_brand,
        paket_layanan_id: selectedPaket.value,
        tgl_mulai: startDate.value,
        include_ppn_next_month: includeNextMonth.value,
      });
      calculationResult.value = response.data;
    } catch (error) {
      console.error("Gagal melakukan kalkulasi:", error);
      calculationResult.value = null;
    }
  } else {
    calculationResult.value = null;
  }
}, 500));

// Watcher to update full monthly price when selectedPaket changes
watch(selectedPaket, () => {
  if (selectedPaket.value) {
    const paket = paketList.value.find(p => p.id === selectedPaket.value);
    if (paket) {
      fullMonthlyPrice.value = paket.harga;
    } else {
      fullMonthlyPrice.value = null;
    }
  } else {
    fullMonthlyPrice.value = null;
  }
});

// Reset form when brand changes
watch(selectedBrand, () => {
  selectedPaket.value = null;
  calculationResult.value = null;
});

// Methods
async function fetchBrands() {
  const response = await apiClient.get('/harga_layanan/');
  brandList.value = response.data;
}

async function fetchPaket() {
  const response = await apiClient.get('/paket_layanan/');
  paketList.value = response.data;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value);
}

function resetCalculation() {
  selectedBrand.value = null;
  selectedPaket.value = null;
  startDate.value = new Date().toISOString().split('T')[0];
  calculationResult.value = null;
  includeNextMonth.value = false;
}

async function copyResult() {
  if (!calculationResult.value) return;

  let resultText = `
Hasil Kalkulasi Harga Prorate:
Brand: ${selectedBrand.value?.brand}
Paket: ${filteredPaketList.value.find(p => p.id === selectedPaket.value)?.nama_paket}
Periode: ${calculationResult.value.periode_hari} hari
Harga Dasar: ${formatCurrency(calculationResult.value.harga_dasar_prorate)}
Pajak: ${formatCurrency(calculationResult.value.pajak)}
Total: ${formatCurrency(calculationResult.value.total_harga_prorate)}
`;

  // Add next month info if included
  if (includeNextMonth.value && calculationResult.value.total_bulan_depan_dengan_ppn !== null) {
    resultText += `
Harga Bulan Depan (Dengan PPN):
- Harga Dasar: ${formatCurrency(calculationResult.value.harga_bulan_depan || 0)}
- PPN (${selectedBrand.value?.pajak || 0}%): ${formatCurrency(calculationResult.value.ppn_bulan_depan || 0)}
- Total Bulan Depan: ${formatCurrency(calculationResult.value.total_bulan_depan_dengan_ppn || 0)}
Total Keseluruhan: ${formatCurrency(calculationResult.value.total_keseluruhan || 0)}
`;
  }

  try {
    await navigator.clipboard.writeText(resultText.trim());
    // You can add a toast notification here
    console.log('Hasil berhasil disalin ke clipboard');
  } catch (error) {
    console.error('Gagal menyalin hasil:', error);
  }
}

onMounted(() => {
  fetchBrands();
  fetchPaket();
});
</script>

<style scoped>
.calculator-container {
  background: rgb(var(--v-theme-background));
  min-height: calc(100vh - 120px);
  padding: 1.5rem;
  transition: background-color 0.3s ease;
}

/* Header Styles */
.page-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, rgba(var(--v-theme-secondary), 0.05) 100%);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon-wrapper {
  background: rgb(var(--v-theme-primary));
  color: white;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  height: 64px;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 1rem;
  margin: 0;
}

/* Card Styles */
.calculator-form-card,
.result-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  height: fit-content;
  transition: all 0.3s ease;
}

.calculator-form-card:hover,
.result-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.form-card-header,
.result-card-header {
  background: rgba(var(--v-theme-primary), 0.05);
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
  font-size: 1.1rem;
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-radius: 16px 16px 0 0;
  display: flex;
  align-items: center;
}

.result-card-header {
  background: rgba(var(--v-theme-success), 0.05);
}

.form-content,
.result-content {
  padding: 1.5rem;
}

/* Input Styles */
.input-group {
  margin-bottom: 1.5rem;
}

.input-label {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.75rem;
}

.modern-select :deep(.v-field),
.modern-input :deep(.v-field) {
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.8);
  border: 1px solid rgba(var(--v-border-color), 0.2);
  transition: all 0.3s ease;
}

.modern-select :deep(.v-field:hover),
.modern-input :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4);
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.1);
}

.modern-select :deep(.v-field--focused),
.modern-input :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.select-item {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin: 0.25rem;
  transition: all 0.2s ease;
}

.select-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

/* Progress Styles */
.progress-section {
  background: rgba(var(--v-theme-primary), 0.02);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-title {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.progress-percentage {
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
  font-size: 0.9rem;
}

.progress-bar :deep(.v-progress-linear__background) {
  background: rgba(var(--v-theme-primary), 0.1);
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.3s ease;
}

.step.active {
  color: rgb(var(--v-theme-success));
  font-weight: 600;
}

/* Empty State Styles */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
}

.empty-illustration {
  margin-bottom: 2rem;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.5rem;
}

.empty-description {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: 0;
}

.empty-checklist {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
  max-width: 250px;
  margin: 0 auto;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.3s ease;
}

.checklist-item.completed {
  color: rgb(var(--v-theme-success));
  font-weight: 600;
}

/* Result Display Styles */
.result-display {
  padding: 0;
}

.result-header {
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
}

.selected-info {
  margin-top: 0.5rem;
}

.selected-brand {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
  margin: 0;
}

.selected-package {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0.25rem 0 0 0;
}

.calculation-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1.5rem 0;
}

.calc-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  transition: all 0.3s ease;
}

.calc-item:hover {
  background: rgba(var(--v-theme-primary), 0.02);
  transform: translateX(4px);
}

.calc-icon-wrapper {
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 0.75rem;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 48px;
}

.calc-content {
  flex: 1;
}

.calc-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 0.25rem;
}

.calc-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.total-section {
  background: linear-gradient(135deg, rgba(var(--v-theme-success), 0.05) 0%, rgba(var(--v-theme-primary), 0.05) 100%);
  padding: 1.5rem;
  border-radius: 16px;
  border: 2px solid rgba(var(--v-theme-success), 0.1);
}

.total-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.total-icon {
  background: rgb(var(--v-theme-success));
  color: white;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 56px;
}

.total-content {
  flex: 1;
}

.total-label {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 0.25rem;
}

.total-amount {
  font-size: 1.75rem;
  font-weight: 800;
  color: rgb(var(--v-theme-success));
  line-height: 1.2;
}

/* PPN Breakdown Styles */
.ppn-breakdown {
  background: rgba(var(--v-theme-success), 0.05);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-success), 0.1);
  font-size: 0.9rem;
}

.ppn-breakdown .text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.ppn-breakdown .text-success {
  color: rgb(var(--v-theme-success));
  font-weight: 600;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

/* Dark Theme Adjustments */
.v-theme--dark .page-header {
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
}

.v-theme--dark .calculator-form-card,
.v-theme--dark .result-card {
  background: #1e293b;
  border-color: #334155;
}

.v-theme--dark .calculator-form-card:hover,
.v-theme--dark .result-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .calculator-container {
    padding: 1rem;
  }
  
  .page-header {
    padding: 1.5rem;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 0.9rem;
  }
  
  .form-content,
  .result-content {
    padding: 1rem;
  }
  
  .progress-steps {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .empty-state {
    padding: 2rem 1rem;
  }
  
  .total-wrapper {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .total-amount {
    font-size: 1.5rem;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .result-actions .v-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .calculator-container {
    padding: 0.75rem;
  }
  
  .page-header {
    padding: 1rem;
  }
  
  .page-title {
    font-size: 1.25rem;
  }
  
  .calculation-grid {
    gap: 0.75rem;
  }
  
  .calc-item {
    padding: 0.75rem;
    gap: 0.75rem;
  }
  
  .calc-icon-wrapper {
    min-width: 40px;
    height: 40px;
    padding: 0.5rem;
  }
  
  .total-section {
    padding: 1rem;
  }
  
  .total-icon {
    min-width: 48px;
    height: 48px;
    padding: 0.75rem;
  }
}

@media (max-width: 360px) {
  .header-icon-wrapper {
    min-width: 48px;
    height: 48px;
    padding: 0.75rem;
  }
  
  .empty-title {
    font-size: 1.25rem;
  }
  
  .empty-description {
    font-size: 0.9rem;
  }
  
  .calc-value {
    font-size: 1rem;
  }
  
  .total-amount {
    font-size: 1.25rem;
  }
  
  .input-label {
    font-size: 0.85rem;
  }
}

/* Loading and Transition States */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* High contrast mode adjustments */
@media (prefers-contrast: high) {
  .calculator-form-card,
  .result-card {
    border-width: 2px;
  }
  
  .calc-item {
    border-width: 2px;
  }
  
  .total-section {
    border-width: 3px;
  }
}

/* Reduced motion adjustments */
@media (prefers-reduced-motion: reduce) {
  .calculator-form-card,
  .result-card,
  .calc-item,
  .step,
  .checklist-item {
    transition: none;
  }
  
  .calculator-form-card:hover,
  .result-card:hover {
    transform: none;
  }
  
  .calc-item:hover {
    transform: none;
  }
}

/* Print styles */
@media print {
  .calculator-container {
    background: white;
    color: black;
  }
  
  .page-header,
  .calculator-form-card,
  .result-card {
    background: white;
    border: 1px solid #ccc;
    box-shadow: none;
  }
  
  .result-actions {
    display: none;
  }
}
</style>