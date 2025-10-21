import { defineStore } from 'pinia';
import apiClient from '@/services/api';

interface MaintenanceState {
  isActive: boolean;
  message: string;
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    maintenanceMode: {
      isActive: false,
      message: 'Sistem sedang dalam tahap maintenance.',
    } as MaintenanceState,
    isLoading: true,
  }),
  actions: {
    async fetchMaintenanceStatus() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/settings/maintenance_mode');
        const setting = response.data.value; // Format: "true|Pesan maintenance" atau "false"
        if (setting && typeof setting === 'string') {
          const [status, ...msgParts] = setting.split('|');
          this.maintenanceMode.isActive = status === 'true';
          this.maintenanceMode.message = msgParts.join('|') || 'Sistem sedang dalam tahap maintenance.';
        } else {
          this.maintenanceMode.isActive = false;
        }
      } catch (error) {
        console.error("Gagal mengambil status maintenance:", error);
        this.maintenanceMode.isActive = false; // Anggap tidak maintenance jika API gagal
      } finally {
        this.isLoading = false;
      }
    },
  },
});