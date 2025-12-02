// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '@/services/api';
import router from '@/router';
import { setEncryptedToken, getEncryptedToken, removeEncryptedToken } from '@/utils/crypto';

// Definisikan tipe data yang lebih spesifik
interface Permission {
  name: string;
}

interface Role {
  name: string;
  permissions: Permission[];
}

interface User {
  id: number;
  email: string;
  name: string;
  role: Role; // Pastikan role adalah objek
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getEncryptedToken('access_token'));
  const user = ref<User | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  // Fungsi PENTING untuk memeriksa hak akses dari komponen
  function hasPermission(permissionName: string): boolean {
    if (!user.value?.role?.permissions) {
      return false;
    }
    return user.value.role.permissions.some(p => p.name === permissionName);
  }

  function setToken(newToken: string) {
    setEncryptedToken('access_token', newToken);
    token.value = newToken;
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  }

  async function logout() {
    const refreshToken = getEncryptedToken('refresh_token');
    try {
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      console.error("Logout failed on backend, but proceeding with frontend logout:", error);
    } finally {
      removeEncryptedToken('access_token');
      removeEncryptedToken('refresh_token');
      token.value = null;
      user.value = null;
      delete apiClient.defaults.headers.common['Authorization'];
      router.push('/login');
    }
  }

  async function verifyToken(): Promise<boolean> {
    if (!token.value) return false;
    try {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
      const response = await apiClient.get<User>('/users/me');
      user.value = response.data;
      return true;
    } catch (error) {
      console.error('Token verification failed:', error);
      await logout();
      return false;
    }
  }

  async function login(email: string, password: string): Promise<boolean> {
    try {
      // Use URLSearchParams for proper form encoding
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiClient.post(
        '/auth/token',
        formData,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );
      
      // 1. Get tokens from response
      const { access_token, refresh_token } = response.data;

      // 2. Set tokens in store and local storage
      setToken(access_token);
      if (refresh_token) {
        setEncryptedToken('refresh_token', refresh_token);
      }

      // 3. Fetch user data using the new token
      // verifyToken will set the user state and return true on success
      return await verifyToken();

    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }

  async function refreshToken(): Promise<boolean> {
    try {
      const refreshToken = getEncryptedToken('refresh_token');
      if (!refreshToken) {
        return false;
      }

      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken
      });

      const { access_token, refresh_token } = response.data;

      // Update tokens
      setToken(access_token);
      if (refresh_token) {
        setEncryptedToken('refresh_token', refresh_token);
      }
      return true;
    } catch (error) {
      console.error('[Auth] Token refresh failed:', error);
      return false;
    }
  }

  async function initializeAuth() {
    if (token.value) {
      await verifyToken();
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    hasPermission, // Ekspor fungsi ini agar bisa dipakai
    setToken,
    logout,
    verifyToken,
    login,
    refreshToken, // Tambahkan refresh token function
    initializeAuth,
  };
});

// Also provide a default export to make imports that expect a default available
// This is a harmless addition that doesn't change runtime logic.
export default useAuthStore;