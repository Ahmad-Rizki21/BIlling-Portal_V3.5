<template>
  <v-container class="pa-6">
    <h1 class="text-h4 font-weight-bold mb-4">Pengaturan Sistem</h1>
    <v-card rounded="xl" elevation="2">
      <v-card-title class="d-flex align-center">
        <v-icon color="warning" class="me-3">mdi-alert-decagram</v-icon>
        Mode Maintenance
      </v-card-title>
      <v-card-text>
        <p class="text-medium-emphasis mb-4">
          Aktifkan mode ini untuk menampilkan banner pemberitahuan di seluruh sistem. Berguna saat Anda sedang melakukan update atau perbaikan.
        </p>
        <v-switch
          v-model="maintenanceActive"
          label="Aktifkan Mode Maintenance"
          color="warning"
          inset
        ></v-switch>
        <v-text-field
          v-model="maintenanceMessage"
          label="Pesan Maintenance"
          :disabled="!maintenanceActive"
          variant="outlined"
          placeholder="Contoh: Sistem akan di-update pukul 23:00."
        ></v-text-field>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn 
          color="primary" 
          @click="saveSettings" 
          :loading="saving"
          size="large"
          class="text-none"
          prepend-icon="mdi-content-save"
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