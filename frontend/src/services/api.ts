// frontend/src/services/api.ts (atau di mana pun file ini berada)

import axios from 'axios';
import router from '@/router'; // 1. Impor router Vue Anda
import { getEncryptedToken, removeEncryptedToken } from '@/utils/crypto';

// Konfigurasi instance axios
const apiClient = axios.create({
  // Gunakan environment variable untuk production
  baseURL: '/api', // Jika ingin build lalu Upload ke Server
  // baseURL: 'http://127.0.0.1:8000', // Local
  timeout: 30000,
});

// Interceptor untuk MENAMBAHKAN token ke setiap request (Ini sudah ada)
apiClient.interceptors.request.use(
  (config) => {
    const token = getEncryptedToken('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ==========================================================
// --- INTERCEPTOR UNTUK AUTO TOKEN REFRESH ---
// ==========================================================
apiClient.interceptors.response.use(
  (response) => {
    // Jika response sukses (status 2xx), lanjutkan seperti biasa
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Jika response dari server adalah error 401 (Unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Tandai request sudah pernah dicoba

      try {
        console.log('[API] Access token expired, attempting refresh...');

        // Ambil refresh token dari storage
        const refreshToken = getEncryptedToken('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Request token baru ke backend
        const response = await apiClient.post('/auth/refresh', {
          refresh_token: refreshToken
        });

        // Update tokens di storage dan header
        const { access_token, refresh_token } = response.data;

        // Gunakan fungsi enkripsi yang konsisten
        const { setEncryptedToken } = await import('@/utils/crypto');
        setEncryptedToken('access_token', access_token);
        if (refresh_token) {
          setEncryptedToken('refresh_token', refresh_token);
        }

        // Update Authorization header untuk request yang gagal
        originalRequest.headers.Authorization = `Bearer ${access_token}`;

        console.log('[API] Token refreshed successfully');

        // Retry request original dengan token baru
        return apiClient(originalRequest);

      } catch (refreshError) {
        console.error('[API] Token refresh failed:', refreshError);

        // Hapus semua token dan redirect ke login
        removeEncryptedToken('access_token');
        removeEncryptedToken('refresh_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        // Redirect ke halaman login
        router.push('/login');
        return Promise.reject(refreshError);
      }
    }

    // Kembalikan error agar bisa ditangani lebih lanjut jika ada logic lain
    return Promise.reject(error);
  }
);
// ==========================================================


// ==========================================================
// --- TROUBLE TICKET API METHODS ---
// ==========================================================

export const troubleTicketAPI = {
  // Get all tickets with pagination and filters
  getTickets: (params?: any) => apiClient.get('/trouble-tickets', { params }),

  // Get ticket by ID
  getTicket: (id: number) => apiClient.get(`/trouble-tickets/${id}`),

  // Create new ticket
  createTicket: (data: any) => apiClient.post('/trouble-tickets', data),

  // Update ticket
  updateTicket: (id: number, data: any) => apiClient.patch(`/trouble-tickets/${id}`, data),

  // Update ticket status
  updateStatus: (id: number, data: any) => apiClient.post(`/trouble-tickets/${id}/status`, data),

  // Update downtime
  updateDowntime: (id: number, data: any) => apiClient.post(`/trouble-tickets/${id}/downtime`, data),

  // Assign ticket
  assignTicket: (id: number, data: any) => apiClient.post(`/trouble-tickets/${id}/assign`, data),

  // Get ticket history
  getHistory: (id: number) => apiClient.get(`/trouble-tickets/${id}/history`),

  // Get statistics
  getStatistics: () => apiClient.get('/trouble-tickets/statistics/dashboard')
};

export default apiClient;