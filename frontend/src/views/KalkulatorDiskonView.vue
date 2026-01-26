<template>
  <v-container fluid class="calculator-container">
    <!-- Header Section -->
    <div class="page-header mb-6">
      <div class="header-content">
        <div class="header-icon-wrapper">
          <v-icon size="32">mdi-percent-outline</v-icon>
        </div>
        <div>
          <h1 class="page-title">Kalkulator Diskon</h1>
          <p class="page-subtitle">Simulasi perhitungan harga dengan diskon untuk layanan FTTH</p>
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

            <!-- Discount Percentage -->
            <div class="input-group mb-4">
              <label class="input-label">
                <v-icon size="18" class="me-2">mdi-percent</v-icon>
                Persentase Diskon
              </label>
              <v-text-field
                v-model="persentaseDiskon"
                type="number"
                variant="outlined"
                density="comfortable"
                class="modern-input"
                :disabled="!selectedPaket"
                placeholder="Contoh: 20"
                min="0"
                max="100"
                step="1"
                :prepend-inner-icon="persentaseDiskon ? 'mdi-check-circle' : 'mdi-circle-outline'"
                :color="persentaseDiskon ? 'success' : 'primary'"
                suffix="%"
              >
                <template v-slot:append-inner>
                  <v-slider
                    v-model="persentaseDiskon"
                    :disabled="!selectedPaket"
                    min="0"
                    max="100"
                    step="1"
                    color="primary"
                    track-color="grey-lighten-2"
                    thumb-color="primary"
                    thumb-label
                    style="width: 120px; margin-top: -4px;"
                  ></v-slider>
                </template>
              </v-text-field>
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
                <div class="step" :class="{ active: persentaseDiskon > 0 }">
                  <v-icon size="16" :color="persentaseDiskon > 0 ? 'success' : 'grey'">
                    {{ persentaseDiskon > 0 ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Diskon</span>
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
                <v-icon size="80" color="grey-lighten-1">mdi-percent-outline</v-icon>
              </div>
              <h3 class="empty-title">Siap Menghitung Diskon!</h3>
              <p class="empty-description">
                Lengkapi form di sebelah kiri untuk melihat simulasi harga dengan diskon
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
                <div class="checklist-item" :class="{ completed: persentaseDiskon > 0 }">
                  <v-icon size="18" :color="persentaseDiskon > 0 ? 'success' : 'grey'">
                    {{ persentaseDiskon > 0 ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span>Masukkan Persentase Diskon</span>
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
                  <p class="selected-brand">{{ calculationResult.nama_brand }}</p>
                  <p class="selected-package">{{ calculationResult.nama_paket }}</p>
                </div>
              </div>

              <!-- Calculation Details -->
              <div class="calculation-grid">
                <!-- Harga Paket -->
                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="info">mdi-package-variant</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Harga Paket</div>
                    <div class="calc-value">{{ formatCurrency(calculationResult.harga_paket) }}</div>
                  </div>
                </div>

                <!-- Pajak -->
                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="warning">mdi-percent</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Pajak ({{ calculationResult.pajak_persen }}%)</div>
                    <div class="calc-value">{{ formatCurrency(calculationResult.pajak_amount) }}</div>
                  </div>
                </div>

                <!-- Subtotal -->
                <div class="calc-item">
                  <div class="calc-icon-wrapper">
                    <v-icon color="primary">mdi-cash</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Subtotal</div>
                    <div class="calc-value">{{ formatCurrency(calculationResult.subtotal_sebelum_diskon) }}</div>
                  </div>
                </div>

                <!-- Diskon -->
                <div class="calc-item discount-item">
                  <div class="calc-icon-wrapper discount-icon">
                    <v-icon color="error">mdi-tag-off</v-icon>
                  </div>
                  <div class="calc-content">
                    <div class="calc-label">Diskon ({{ calculationResult.persentase_diskon }}%)</div>
                    <div class="calc-value discount-value">-{{ formatCurrency(calculationResult.diskon_amount) }}</div>
                  </div>
                </div>
              </div>

              <!-- Total Section -->
              <v-divider class="my-4"></v-divider>
              <div class="total-section">
                <div class="total-wrapper">
                  <div class="total-icon">
                    <v-icon size="24" color="success">mdi-check-circle</v-icon>
                  </div>
                  <div class="total-content">
                    <div class="total-label">Harga Final</div>
                    <div class="total-amount">{{ formatCurrency(calculationResult.harga_final) }}</div>
                  </div>
                </div>

                <!-- Hemat Section -->
                <div class="hemat-section mt-3">
                  <v-alert color="success" variant="tonal" density="comfortable" class="hemat-alert">
                    <div class="d-flex align-center">
                      <v-icon color="success" class="me-2">mdi-piggy-bank</v-icon>
                      <div>
                        <div class="text-caption">Anda hemat</div>
                        <div class="text-h6 font-weight-bold">{{ formatCurrency(calculationResult.diskon_amount) }}</div>
                      </div>
                    </div>
                  </v-alert>
                </div>
              </div>

              <!-- Detail Perhitungan (Collapsible) -->
              <v-expansion-panels class="mt-4" variant="accordion">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <v-icon class="me-2" color="info">mdi-information-outline</v-icon>
                    Detail Perhitungan
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <pre class="detail-perhitungan">{{ calculationResult.detail_perhitungan }}</pre>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

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
interface DiskonResult {
  nama_paket: string;
  nama_brand: string;
  harga_paket: number;
  pajak_persen: number;
  pajak_amount: number;
  subtotal_sebelum_diskon: number;
  persentase_diskon: number;
  diskon_amount: number;
  harga_final: number;
  detail_perhitungan: string;
}

// State
const brandList = ref<Brand[]>([]);
const paketList = ref<Paket[]>([]);
const selectedBrand = ref<Brand | null>(null);
const selectedPaket = ref<number | null>(null);
const persentaseDiskon = ref<number>(0);
const calculationResult = ref<DiskonResult | null>(null);

// Computed
const filteredPaketList = computed(() => {
  if (!selectedBrand.value) return [];
  return paketList.value.filter(p => p.id_brand === selectedBrand.value?.id_brand);
});

const completionPercentage = computed(() => {
  let completed = 0;
  if (selectedBrand.value) completed += 33.33;
  if (selectedPaket.value) completed += 33.33;
  if (persentaseDiskon.value > 0) completed += 33.34;
  return Math.round(completed);
});

// Watcher to trigger calculation
watch([selectedBrand, selectedPaket, persentaseDiskon], debounce(async () => {
  if (selectedBrand.value && selectedPaket.value && persentaseDiskon.value > 0) {
    try {
      const response = await apiClient.post('/calculator/diskon', {
        id_brand: selectedBrand.value.id_brand,
        paket_layanan_id: selectedPaket.value,
        persentase_diskon: persentaseDiskon.value,
      });
      calculationResult.value = response.data;
    } catch (error) {
      console.error("Gagal melakukan kalkulasi diskon:", error);
      calculationResult.value = null;
    }
  } else {
    calculationResult.value = null;
  }
}, 500));

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
  persentaseDiskon.value = 0;
  calculationResult.value = null;
}

async function copyResult() {
  if (!calculationResult.value) return;

  const resultText = calculationResult.value.detail_perhitungan;

  try {
    await navigator.clipboard.writeText(resultText.trim());
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
  max-width: 280px;
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

.calc-item.discount-item {
  background: rgba(var(--v-theme-error), 0.05);
  border-color: rgba(var(--v-theme-error), 0.2);
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

.calc-icon-wrapper.discount-icon {
  background: rgba(var(--v-theme-error), 0.1);
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

.calc-value.discount-value {
  color: rgb(var(--v-theme-error));
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

.hemat-alert {
  border-radius: 12px;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.detail-perhitungan {
  background: rgba(var(--v-theme-surface), 0.8);
  padding: 1rem;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  color: rgb(var(--v-theme-on-surface));
  border: 1px solid rgba(var(--v-border-color), 0.1);
  line-height: 1.6;
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

.v-theme--dark .detail-perhitungan {
  background: #0f172a;
  border-color: #334155;
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
