// frontend/src/services/api.ts (atau di mana pun file ini berada)

import axios from 'axios';
import router from '@/router'; // 1. Impor router Vue Anda

// Konfigurasi instance axios
const apiClient = axios.create({
  // baseURL: import.meta.env.VITE_API_BASE_URL,
  // baseURL: '/api', // Jika ingin build lalu Upload ke Server
  baseURL: 'http://127.0.0.1:8000', // Local
  timeout: 30000,
});

// Interceptor untuk MENAMBAHKAN token ke setiap request (Ini sudah ada)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
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
// --- TAMBAHAN BARU: Interceptor untuk MEMERIKSA setiap response ---
// ==========================================================
apiClient.interceptors.response.use(
  (response) => {
    // Jika response sukses (status 2xx), lanjutkan seperti biasa
    return response;
  },
  (error) => {
    // Jika response dari server adalah error
    if (error.response && error.response.status === 401) {
      // 2. Cek apakah status errornya adalah 401 (Unauthorized)
      console.error("Sesi tidak valid atau telah berakhir. Mengarahkan ke halaman login.");
      
      // 3. Hapus token yang sudah tidak valid dari penyimpanan
      localStorage.removeItem('access_token');
      // Anda juga bisa membersihkan data user dari state management (Pinia) di sini jika perlu
      
      // 4. Arahkan pengguna ke halaman login
      router.push('/login');
    }
    
    // Kembalikan error agar bisa ditangani lebih lanjut jika ada logic lain
    return Promise.reject(error);
  }
);
// ==========================================================

export default apiClient;