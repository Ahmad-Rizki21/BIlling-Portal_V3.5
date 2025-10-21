<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:modelValue="$emit('update:modelValue', $event)" 
    max-width="650px" 
    persistent
    transition="dialog-bottom-transition"
  >
    <v-card class="dialog-card" elevation="24">
      <!-- Header dengan gradient dan icon -->
      <v-card-title class="dialog-header pa-6">
        <div class="d-flex align-center">
          <v-avatar class="me-4" color="rgba(255,255,255,0.2)" size="48">
            <v-icon color="white" size="24">
              {{ isEditMode ? 'mdi-package-variant' : 'mdi-package-variant-plus' }}
            </v-icon>
          </v-avatar>
          <div>
            <h2 class="text-h5 font-weight-bold text-white mb-1">{{ formTitle }}</h2>
            <p class="text-body-2 text-white opacity-90 mb-0">
              {{ isEditMode ? 'Ubah detail paket layanan' : 'Buat paket layanan baru' }}
            </p>
          </div>
        </div>
      </v-card-title>

      <!-- Content dengan styling yang enhanced -->
      <v-card-text class="pa-6">
        <v-container fluid class="pa-0">
          <v-row dense>
            <!-- Package Name Field -->
            <v-col cols="12">
              <div class="field-group mb-4">
                <label class="field-label">Nama Paket</label>
                <v-text-field
                  v-model="localItem.nama_paket"
                  placeholder="Contoh: Paket Home Premium, Business Pro"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field"
                  prepend-inner-icon="mdi-package-variant-closed"
                  hide-details="auto"
                />
              </div>
            </v-col>

            <!-- Speed Field -->
            <v-col cols="12" md="6">
              <div class="field-group mb-4">
                <label class="field-label">Kecepatan Internet</label>
                <v-text-field
                  v-model.number="localItem.kecepatan"
                  type="number"
                  placeholder="100"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field speed-field"
                  prepend-inner-icon="mdi-speedometer"
                  suffix="Mbps"
                  hide-details="auto"
                >
                  <template v-slot:append-inner>
                    <div class="speed-indicator">
                      <v-chip 
                        :color="getSpeedColor(localItem.kecepatan)" 
                        size="x-small" 
                        variant="flat"
                        class="speed-chip"
                      >
                        {{ getSpeedLabel(localItem.kecepatan) }}
                      </v-chip>
                    </div>
                  </template>
                </v-text-field>
              </div>
            </v-col>

            <!-- Price Field -->
            <v-col cols="12" md="6">
              <div class="field-group mb-4">
                <label class="field-label">Harga Paket</label>
                <v-text-field
                  v-model.number="localItem.harga"
                  type="number"
                  placeholder="299000"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field price-field"
                  prepend-inner-icon="mdi-currency-usd"
                  prefix="Rp"
                  hide-details="auto"
                >
                  <template v-slot:append-inner v-if="localItem.harga">
                    <div class="price-formatted text-caption text-success">
                      {{ formatCurrency(localItem.harga) }}
                    </div>
                  </template>
                </v-text-field>
              </div>
            </v-col>

            <!-- Package Summary Card -->
            <v-col cols="12" v-if="localItem.nama_paket || localItem.kecepatan || localItem.harga">
              <v-card class="package-preview" variant="outlined">
                <v-card-text class="pa-4">
                  <div class="d-flex align-center mb-2">
                    <v-icon color="teal" class="me-2">mdi-eye-outline</v-icon>
                    <span class="text-subtitle-2 font-weight-bold text-teal">Preview Paket</span>
                  </div>
                  
                  <div class="preview-content">
                    <div class="d-flex align-center justify-space-between mb-2">
                      <span class="text-body-2 text-medium-emphasis">Nama:</span>
                      <span class="font-weight-bold">{{ localItem.nama_paket || '-' }}</span>
                    </div>
                    <div class="d-flex align-center justify-space-between mb-2">
                      <span class="text-body-2 text-medium-emphasis">Kecepatan:</span>
                      <div class="d-flex align-center">
                        <span class="font-weight-bold me-2">{{ localItem.kecepatan || 0 }} Mbps</span>
                        <v-chip 
                          v-if="localItem.kecepatan"
                          :color="getSpeedColor(localItem.kecepatan)" 
                          size="x-small" 
                          variant="flat"
                        >
                          {{ getSpeedLabel(localItem.kecepatan) }}
                        </v-chip>
                      </div>
                    </div>
                    <div class="d-flex align-center justify-space-between">
                      <span class="text-body-2 text-medium-emphasis">Harga:</span>
                      <span class="text-h6 font-weight-bold text-success">
                        {{ localItem.harga ? formatCurrency(localItem.harga) : 'Rp 0' }}
                      </span>
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <!-- Actions dengan styling enhanced -->
      <v-card-actions class="pa-6 pt-2">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          color="grey-darken-1"
          class="text-none me-3 action-btn"
          size="large"
          @click="$emit('update:modelValue', false)"
          prepend-icon="mdi-close"
        >
          Batal
        </v-btn>
        <v-btn
          color="teal"
          class="text-none action-btn"
          size="large"
          elevation="2"
          @click="submit"
          prepend-icon="mdi-content-save"
          :disabled="!isFormValid"
        >
          {{ isEditMode ? 'Update' : 'Simpan' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { PaketLayanan } from '@/interfaces/layanan';

const props = defineProps<{
  modelValue: boolean,
  editedItem: Partial<PaketLayanan>,
  brandId?: string
}>();

const emit = defineEmits(['update:modelValue', 'save']);

const localItem = ref<Partial<PaketLayanan>>({});
const isEditMode = computed(() => !!localItem.value.id);
const formTitle = computed(() => isEditMode.value ? 'Edit Paket Layanan' : 'Tambah Paket Layanan');

const isFormValid = computed(() => {
  return localItem.value.nama_paket && 
         localItem.value.kecepatan && 
         localItem.value.harga;
});

watch(() => props.editedItem, (newVal) => {
  localItem.value = { ...newVal };
}, { immediate: true, deep: true });

// Set id_brand from brandId prop when creating new package
watch(() => props.brandId, (newBrandId) => {
  if (newBrandId && !localItem.value.id_brand) {
    localItem.value.id_brand = newBrandId;
  }
}, { immediate: true });

function submit() {
  emit('save', localItem.value);
  emit('update:modelValue', false);
}

function getSpeedColor(speed: number | undefined): string {
  if (!speed) return 'grey';
  if (speed < 25) return 'orange';
  if (speed < 100) return 'blue';
  if (speed < 500) return 'green';
  return 'purple';
}

function getSpeedLabel(speed: number | undefined): string {
  if (!speed) return '';
  if (speed < 25) return 'Basic';
  if (speed < 100) return 'Fast';
  if (speed < 500) return 'Ultra';
  return 'Extreme';
}

function formatCurrency(value: number | undefined): string {
  if (!value || isNaN(value)) return "Rp 0";
  return new Intl.NumberFormat('id-ID', { 
    style: 'currency', 
    currency: 'IDR', 
    minimumFractionDigits: 0 
  }).format(value);
}
</script>

<style scoped>
.dialog-card {
  border-radius: 16px !important;
  overflow: hidden;
}

.dialog-header {
  background: linear-gradient(135deg, #00695c 0%, #00897b 50%, #26a69a 100%);
  position: relative;
}

.dialog-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='m36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.field-group {
  position: relative;
}

.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #424242;
  margin-bottom: 8px;
  position: relative;
}

.field-label::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 24px;
  height: 2px;
  background: linear-gradient(90deg, #00695c, #26a69a);
  border-radius: 1px;
}

.custom-field :deep(.v-field) {
  border-radius: 12px !important;
  transition: all 0.3s ease;
  background: rgba(0, 105, 92, 0.02);
}

.custom-field :deep(.v-field:hover) {
  background: rgba(0, 105, 92, 0.04);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 105, 92, 0.1);
}

.custom-field :deep(.v-field--focused) {
  background: rgba(0, 105, 92, 0.06);
  box-shadow: 0 0 0 2px rgba(0, 105, 92, 0.2);
  transform: translateY(-1px);
}

.speed-indicator {
  margin-left: 8px;
}

.speed-chip {
  font-size: 0.7rem !important;
  height: 20px !important;
}

.price-formatted {
  max-width: 80px;
  font-size: 0.7rem;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.package-preview {
  background: linear-gradient(145deg, rgba(0, 105, 92, 0.02), rgba(38, 166, 154, 0.05));
  border: 2px solid rgba(0, 105, 92, 0.1) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.package-preview:hover {
  background: linear-gradient(145deg, rgba(0, 105, 92, 0.04), rgba(38, 166, 154, 0.08));
  border-color: rgba(0, 105, 92, 0.2) !important;
}

.preview-content {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  padding: 12px;
}

.action-btn {
  border-radius: 12px !important;
  font-weight: 600;
  text-transform: none;
  min-width: 100px;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  transform: none !important;
  box-shadow: none !important;
}

/* Animation untuk dialog */
:deep(.dialog-bottom-transition-enter-active),
:deep(.dialog-bottom-transition-leave-active) {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

:deep(.dialog-bottom-transition-enter-from) {
  opacity: 0;
  transform: translateY(50px) scale(0.95);
}

:deep(.dialog-bottom-transition-leave-to) {
  opacity: 0;
  transform: translateY(50px) scale(0.95);
}

/* ===== PERBAIKAN UNTUK MODE GELAP (DARK MODE FIX) ===== */
.v-theme--dark .field-label {
  color: rgba(255, 255, 255, 0.75);
}

.v-theme--dark .custom-field :deep(.v-field) {
  background: rgba(255, 255, 255, 0.04);
}

.v-theme--dark .custom-field :deep(.v-field:hover) {
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.v-theme--dark .custom-field :deep(.v-field--focused) {
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 3px rgba(38, 166, 154, 0.4);
}

.v-theme--dark .package-preview {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border-color: rgba(255, 255, 255, 0.15) !important;
}

.v-theme--dark .package-preview:hover {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.05));
  border-color: rgba(255, 255, 255, 0.25) !important;
}

.v-theme--dark .preview-content {
  background: rgba(0, 0, 0, 0.2);
}

.v-theme--dark .package-preview .text-medium-emphasis {
    color: rgba(255, 255, 255, 0.7) !important;
}

.v-theme--dark .package-preview .font-weight-bold:not(.text-teal):not(.text-success) {
    color: rgba(255, 255, 255, 0.95) !important;
}

/* Responsive */
@media (max-width: 600px) {
  .dialog-header {
    padding: 1rem !important;
  }
  
  .field-label {
    font-size: 0.8rem;
  }
  
  .price-formatted {
    max-width: 60px;
    font-size: 0.65rem;
  }
}
</style>