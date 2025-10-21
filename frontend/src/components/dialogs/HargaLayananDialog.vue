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
              {{ isEditMode ? 'mdi-pencil-outline' : 'mdi-plus-circle-outline' }}
            </v-icon>
          </v-avatar>
          <div>
            <h2 class="text-h5 font-weight-bold text-white mb-1">{{ formTitle }}</h2>
            <p class="text-body-2 text-white opacity-90 mb-0">
              {{ isEditMode ? 'Ubah informasi brand provider' : 'Tambahkan brand provider baru' }}
            </p>
          </div>
        </div>
      </v-card-title>

      <!-- Content dengan styling yang enhanced -->
      <v-card-text class="pa-6">
        <v-container fluid class="pa-0">
          <v-row dense>
            <!-- ID Brand Field -->
            <v-col cols="12">
              <div class="field-group mb-4">
                <label class="field-label">ID Brand</label>
                <v-text-field
                  v-model="localItem.id_brand"
                  :disabled="isEditMode"
                  placeholder="Contoh: jnt-01, art-02"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field"
                  :class="{ 'field-disabled': isEditMode }"
                  prepend-inner-icon="mdi-identifier"
                  hide-details="auto"
                >
                  <template v-slot:append-inner v-if="isEditMode">
                    <v-tooltip text="ID Brand tidak dapat diubah">
                      <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" color="grey-darken-1" size="small">mdi-lock</v-icon>
                      </template>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </div>
            </v-col>

            <!-- Brand Name Field -->
            <v-col cols="12">
              <div class="field-group mb-4">
                <label class="field-label">Nama Brand</label>
                <v-text-field
                  v-model="localItem.brand"
                  placeholder="Masukkan nama brand"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field"
                  prepend-inner-icon="mdi-domain"
                  hide-details="auto"
                />
              </div>
            </v-col>

            <!-- Tax Field -->
            <v-col cols="12" md="6">
              <div class="field-group mb-4">
                <label class="field-label">Pajak (%)</label>
                <v-text-field
                  v-model.number="localItem.pajak"
                  type="number"
                  placeholder="11.0"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field"
                  prepend-inner-icon="mdi-percent"
                  suffix="%"
                  hide-details="auto"
                />
              </div>
            </v-col>

            <!-- Xendit Key Field -->
            <v-col cols="12" md="6">
              <div class="field-group mb-4">
                <label class="field-label">Key Name Xendit</label>
                <v-text-field
                  v-model="localItem.xendit_key_name"
                  placeholder="Masukkan key Xendit"
                  variant="outlined"
                  density="comfortable"
                  class="custom-field"
                  prepend-inner-icon="mdi-key-variant"
                  hide-details="auto"
                />
              </div>
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
        >
          {{ isEditMode ? 'Update' : 'Simpan' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { HargaLayanan } from '@/interfaces/layanan';

const props = defineProps<{
  modelValue: boolean,
  editedItem: Partial<HargaLayanan>
}>();

const emit = defineEmits(['update:modelValue', 'save']);

const localItem = ref<Partial<HargaLayanan>>({});
const isEditMode = computed(() => !!localItem.value.id_brand);
const formTitle = computed(() => isEditMode.value ? 'Edit Brand Provider' : 'Tambah Brand Provider');

watch(() => props.editedItem, (newVal) => {
  localItem.value = { ...newVal };
}, { immediate: true, deep: true });

function submit() {
  emit('save', localItem.value);
  emit('update:modelValue', false);
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

.field-disabled :deep(.v-field) {
  background: rgba(0, 0, 0, 0.04) !important;
  opacity: 0.7;
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

.v-theme--dark .field-disabled :deep(.v-field) {
  background: rgba(255, 255, 255, 0.02) !important;
}

/* Responsive */
@media (max-width: 600px) {
  .dialog-header {
    padding: 1rem !important;
  }
  
  .field-label {
    font-size: 0.8rem;
  }
}
</style>