<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Modern Header with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar class="me-4 elevation-4" color="primary" size="80">
              <v-icon color="white" size="40">mdi-cog</v-icon>
            </v-avatar>
            <div>
              <h1 class="text-h4 font-weight-bold text-white mb-2">Pengaturan Sistem</h1>
              <p class="header-subtitle mb-0">
                Kelola konfigurasi dan pengaturan sistem secara global
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <v-card rounded="xl" elevation="2" class="settings-card">
      <!-- Card Header with Gradient -->
      <div class="maintenance-header">
        <v-card-title class="d-flex align-center pa-6">
          <div class="header-icon-wrapper me-3">
            <v-icon color="warning" size="28">mdi-alert-decagram</v-icon>
          </div>
          <div>
            <h2 class="text-h6 font-weight-bold mb-0">Mode Maintenance</h2>
            <p class="text-caption text-medium-emphasis mb-0">
              Kontrol status maintenance sistem dan pesan pemberitahuan
            </p>
          </div>
        </v-card-title>
      </div>

      <v-divider></v-divider>

      <v-card-text class="pa-6">
        <!-- Description Section -->
        <div class="description-section mb-6">
          <p class="text-body-1 text-medium-emphasis mb-4">
            Aktifkan mode ini untuk menampilkan banner pemberitahuan di seluruh sistem. Berguna saat Anda sedang melakukan update atau perbaikan.
          </p>
        </div>

        <!-- Form Controls -->
        <div class="form-section">
          <!-- Maintenance Switch -->
          <div class="form-group mb-6">
            <v-switch
              v-model="maintenanceActive"
              label="Aktifkan Mode Maintenance"
              color="warning"
              inset
              hide-details="auto"
              class="maintenance-switch"
            >
              <template v-slot:prepend>
                <v-icon
                  :color="maintenanceActive ? 'warning' : 'grey-lighten-1'"
                  :icon="maintenanceActive ? 'mdi-tools' : 'mdi-power-standby'"
                  class="me-2"
                ></v-icon>
              </template>
            </v-switch>
          </div>

          <!-- Maintenance Message -->
          <div class="form-group">
            <v-text-field
              v-model="maintenanceMessage"
              label="Pesan Maintenance"
              :disabled="!maintenanceActive"
              variant="outlined"
              placeholder="Contoh: Sistem akan di-update pukul 23:00."
              prepend-inner-icon="mdi-message-text"
              hide-details="auto"
              class="message-field"
              :bg-color="maintenanceActive ? 'warning-lighten-5' : 'grey-lighten-4'"
            >
              <template v-slot:append-inner>
                <v-icon
                  v-if="maintenanceActive"
                  color="warning"
                  size="20"
                  class="animate-pulse"
                >
                  mdi-bell
                </v-icon>
              </template>
            </v-text-field>
          </div>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <!-- Card Actions -->
      <v-card-actions class="pa-6">
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          @click="saveSettings"
          :loading="saving"
          size="large"
          class="text-none font-weight-bold"
          prepend-icon="mdi-content-save"
          elevation="2"
        >
          Simpan Pengaturan
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="top right"
    >
      {{ snackbar.text }}
    </v-snackbar>

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useSettingsStore } from '@/stores/settings';
import apiClient from '@/services/api';

const settingsStore = useSettingsStore();
const maintenanceActive = ref(false);
const maintenanceMessage = ref('');
const saving = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });

// Saat halaman dimuat, isi form dengan data dari store
onMounted(() => {
  maintenanceActive.value = settingsStore.maintenanceMode.isActive;
  maintenanceMessage.value = settingsStore.maintenanceMode.message;
});

// Fungsi untuk menyimpan perubahan ke backend
async function saveSettings() {
  saving.value = true;
  try {
    // Format value: "true|Pesan" atau "false|Pesan"
    const valueToSave = `${maintenanceActive.value}|${maintenanceMessage.value}`;
    
    await apiClient.put('/settings/maintenance_mode', { value: valueToSave });
    
    // Perbarui status di store agar banner di layout langsung update
    await settingsStore.fetchMaintenanceStatus();
    
    showSnackbar('Pengaturan berhasil disimpan!', 'success');
  } catch (error) {
    console.error("Gagal menyimpan pengaturan:", error);
    showSnackbar('Gagal menyimpan pengaturan.', 'error');
  } finally {
    saving.value = false;
  }
}

function showSnackbar(text: string, color: 'success' | 'error') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}
</script>

<style scoped>
/* Header Card styling - sama seperti halaman lain */
.header-card {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
  background: white;
}

/* Header content untuk memperbesar box */
.header-content {
  padding: 24px 32px;
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
}

/* Header text styling */
.header-section h1 {
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 1.1rem;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  opacity: 0.95;
}

/* Settings Card */
.settings-card {
  border-radius: 20px !important;
  border: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.settings-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

/* Maintenance Header */
.maintenance-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.header-icon-wrapper {
  width: 48px;
  height: 48px;
  background: rgba(251, 191, 36, 0.1); /* warning-400 with opacity */
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.header-icon-wrapper:hover {
  background: rgba(251, 191, 36, 0.15);
  transform: scale(1.05);
}

/* Form Sections */
.description-section {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.form-section {
  max-width: 600px;
}

.form-group {
  transition: all 0.3s ease;
}

.form-group:hover {
  transform: translateX(4px);
}

/* Maintenance Switch Styling */
.maintenance-switch :deep(.v-switch__thumb) {
  transition: all 0.3s ease;
}

.maintenance-switch :deep(.v-switch__track) {
  transition: all 0.3s ease;
}

.maintenance-switch:hover :deep(.v-switch__thumb) {
  transform: scale(1.1);
}

/* Message Field Styling */
.message-field :deep(.v-field) {
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.message-field:hover :deep(.v-field) {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.1);
}

.message-field.v-input--is-disabled :deep(.v-field) {
  opacity: 0.6;
}

/* Button Styling */
.v-btn--variant-elevated {
  transition: all 0.3s ease;
}

.v-btn--variant-elevated:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(124, 58, 237, 0.3) !important;
}

/* Animations */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}

/* Responsive Design */
@media (max-width: 960px) {
  .header-content {
    padding: 20px;
  }

  .header-section h1 {
    font-size: 1.5rem;
  }

  .header-subtitle {
    font-size: 0.95rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 16px;
  }

  .form-section {
    max-width: 100%;
  }

  .description-section {
    padding: 16px;
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .v-card-actions {
    padding: 20px !important;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 12px;
  }

  .header-section h1 {
    font-size: 1.25rem;
  }

  .header-subtitle {
    font-size: 0.85rem;
  }

  .description-section {
    padding: 12px;
  }

  .v-card-actions {
    flex-direction: column;
    gap: 12px;
  }

  .v-btn {
    width: 100%;
  }
}

/* Dark mode adjustments */
.v-theme--dark .header-card {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .settings-card {
  background: rgba(var(--v-theme-surface), 0.95);
  border: 1px solid rgba(var(--v-border-color), 0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
}

.v-theme--dark .maintenance-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.4) 0%, rgba(var(--v-theme-surface-variant), 0.2) 100%);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.2);
}

.v-theme--dark .description-section {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left-color: rgb(var(--v-theme-warning));
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

.v-theme--dark .header-icon-wrapper {
  background: rgba(251, 191, 36, 0.25);
  border: 1px solid rgba(251, 191, 36, 0.2);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.1);
}

.v-theme--dark .header-icon-wrapper:hover {
  background: rgba(251, 191, 36, 0.35);
  box-shadow: 0 6px 20px rgba(251, 191, 36, 0.2);
}

.v-theme--dark .form-group:hover {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 8px;
  padding: 12px;
  margin: -12px;
  margin-bottom: 8px;
}

.v-theme--dark .message-field :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8);
  border-color: rgba(var(--v-border-color), 0.3);
}

.v-theme--dark .message-field:hover :deep(.v-field) {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.15);
  background: rgba(var(--v-theme-surface), 0.95);
}

.v-theme--dark .message-field.v-input--is-disabled :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.4);
  border-color: rgba(var(--v-border-color), 0.2);
  opacity: 0.7;
}

.v-theme--dark .maintenance-switch :deep(.v-switch__track) {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border: 1px solid rgba(var(--v-border-color), 0.2);
}

.v-theme--dark .v-divider {
  border-color: rgba(var(--v-border-color), 0.15);
}

.v-theme--dark .v-card-actions {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}
</style>