// frontend/src/services/api.ts (atau di mana pun file ini berada)

import axios from 'axios';
import router from '@/router'; 
import { getEncryptedToken, removeEncryptedToken, setEncryptedToken } from '@/utils';
import { errorStorage, networkErrorRateLimit } from './errorStorage';

// Konfigurasi instance axios
const apiClient = axios.create({
  // Gunakan environment variable untuk production
  // baseURL: '/api', // Jika ingin build lalu Upload ke Server
  baseURL: 'http://127.0.0.1:8000', // Local
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
// --- NETWORK ERROR INTERCEPTOR ---
// ==========================================================
apiClient.interceptors.response.use(
  (response) => response, // Success: just return response
  async (error) => {
    const originalRequest = error.config;

    // Skip if it's already a network error request
    if (originalRequest.headers?.['X-Skip-Network-Interceptor']) {
      return Promise.reject(error);
    }

    // Rate limiting check
    if (!networkErrorRateLimit.canRedirect()) {
      console.warn('[Rate Limit] Too many network error redirects');
      return Promise.reject(error);
    }

    // Handle network-related errors
    if (!error.response && error.code === 'NETWORK_ERROR') {
      console.error('[Network Error] Connection failed:', error.message);
      const errorId = errorStorage.storeError('network', 0, originalRequest.url, originalRequest.method?.toUpperCase(), error.message);

      router.push({
        name: 'network-error',
        query: { errorId }
      });
      return Promise.reject(error);
    }

    // Handle timeout errors
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('[Timeout Error] Request timed out:', error.message);
      const errorId = errorStorage.storeError('timeout', 0, originalRequest.url, originalRequest.method?.toUpperCase(), 'Request timeout - server took too long to respond');

      router.push({
        name: 'network-error',
        query: { errorId }
      });
      return Promise.reject(error);
    }

    // Handle server unavailable (5xx errors)
    if (error.response?.status >= 500) {
      console.error('[Server Error] Server error:', error.response.status);

      // Don't redirect for auth errors (let the auth interceptor handle it)
      if (error.response.status === 401) {
        return Promise.reject(error);
      }

      const errorId = errorStorage.storeError('server', error.response.status, originalRequest.url, originalRequest.method?.toUpperCase(), `Server error: ${error.response.status} ${error.response.statusText}`);

      router.push({
        name: 'network-error',
        query: { errorId }
      });
      return Promise.reject(error);
    }

    // Handle connection refused / server down
    if (
      error.code === 'ERR_NETWORK' ||
      error.code === 'ERR_CONNECTION_REFUSED' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('fetch failed')
    ) {
      console.error('[Connection Error] Server unreachable:', error.message);
      const errorId = errorStorage.storeError('network', 0, originalRequest.url, originalRequest.method?.toUpperCase(), 'Cannot connect to server - server may be down');

      router.push({
        name: 'network-error',
        query: { errorId }
      });
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Health check function
export const checkServerHealth = async () => {
  try {
    const response = await apiClient.get('/health', {
      headers: { 'X-Skip-Network-Interceptor': 'true' }, // Skip network interceptor for health check
      timeout: 5000
    });
    return { success: true, status: response.status, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Health check failed',
      code: error.code || 'UNKNOWN'
    };
  }
};

// Retry mechanism for failed requests
export const retryRequest = async (originalRequest: any, maxRetries = 3) => {
  let retryCount = 0;

  while (retryCount < maxRetries) {
    try {
      const response = await apiClient({
        ...originalRequest,
        headers: {
          ...originalRequest.headers,
          'X-Skip-Network-Interceptor': 'true' // Skip network interceptor for retries
        }
      });
      return response;
    } catch (error) {
      retryCount++;
      console.warn(`[Retry] Attempt ${retryCount}/${maxRetries} failed:`, error.message);

      if (retryCount >= maxRetries) {
        throw error;
      }

      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
    }
  }
};

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
