<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import axios, { type AxiosError } from 'axios';

// Definisikan tipe untuk respons error dari backend
interface ErrorResponse {
  detail?: string;
  message?: string;
}

const email = ref('');
const password = ref('');
const resetEmail = ref('');
const newPassword = ref('');
const error = ref('');
const successMessage = ref('');
const loading = ref(false);
const showForgotPassword = ref(false);
const router = useRouter();
const authStore = useAuthStore();
const resetToken = ref(''); // Untuk menyimpan token dari forgot password
const rememberMe = ref(false); // Untuk checkbox remember me
const showPassword = ref(false); // Untuk toggle password visibility

// Load remembered email on component mount
const rememberedEmail = localStorage.getItem('remember_email');
if (rememberedEmail) {
  email.value = rememberedEmail;
  rememberMe.value = true;
}

// Toggle password visibility
function togglePasswordVisibility() {
  showPassword.value = !showPassword.value;
}

// Handle image error fallback
function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement;
  target.src = '/src/assets/Jelantik 1.svg';
}

async function handleLogin() {
  if (!email.value || !password.value) {
    error.value = 'Email dan password harus diisi';
    return;
  }

  error.value = '';
  loading.value = true;

  try {
    const success = await authStore.login(email.value, password.value);
    if (success) {
      // Store remember me preference if checked
      if (rememberMe.value) {
        localStorage.setItem('remember_email', email.value);
      } else {
        localStorage.removeItem('remember_email');
      }
      router.push('/dashboard');
    } else {
      error.value = 'Email atau password salah!';
    }
  } catch (err) {
    const errorResponse = err as AxiosError<ErrorResponse>;
    console.error('Login error:', errorResponse.response?.data || errorResponse.message);
    error.value = errorResponse.response?.data?.detail || errorResponse.response?.data?.message || 'Terjadi kesalahan saat login';
  } finally {
    loading.value = false;
  }
}

async function handleResetPassword() {
  if (!resetEmail.value || !newPassword.value || !resetToken.value) {
    error.value = 'Email, password baru, dan token harus diisi';
    return;
  }

  error.value = '';
  successMessage.value = '';
  loading.value = true;

  try {
    // Use the configured API client instead of hardcoded URL
    const response = await axios.post<{ message: string }>('/users/reset-password', {
      email: resetEmail.value,
      new_password: newPassword.value,
      token: resetToken.value,
    }, {
      headers: { 'Content-Type': 'application/json' },
    });
    successMessage.value = response.data.message;
    showForgotPassword.value = false;
    setTimeout(() => router.push('/login'), 2000);
  } catch (err) {
    const errorResponse = err as AxiosError<ErrorResponse>;
    console.error('Reset password error:', errorResponse.response?.data || errorResponse.message);
    error.value = errorResponse.response?.data?.detail || errorResponse.response?.data?.message || 'Terjadi kesalahan saat reset password';
  } finally {
    loading.value = false;
  }
}

function backToLogin() {
  showForgotPassword.value = false;
  error.value = '';
  successMessage.value = '';
}
</script>

<template>
  <div class="min-h-screen gradient-bg flex items-center justify-center p-6 md:p-12">
    <!-- Main Login Card -->
    <div class="w-full max-w-7xl flex rounded-3xl overflow-hidden login-card-enhanced relative z-10 mx-auto" style="width: 95vw; max-width: 1200px;">

      <!-- Login Form - Left Side (LoginForm.js) -->
      <div class="w-full lg:w-[60%] glass-effect px-4 sm:px-6 md:px-8 lg:px-12 py-6 sm:py-8 flex flex-col" data-name="login-form">
        <div class="w-full max-w-md mx-auto">
          <div class="logo-header mb-4">
            <h2 class="text-lg font-semibold text-black pb-1 border-b-2 border-gray-300 inline-block">
              {{ showForgotPassword ? 'Reset Password' : 'Login please' }}
            </h2>
            <div v-if="!showForgotPassword" class="logo-container">
              <img
                src="/src/assets/icon_dark.ico"
                alt="Jelantik Logo"
                class="h-20 w-auto object-contain"
                @error="handleImageError"
              />
            </div>
          </div>

          <!-- Login Form -->
          <form v-if="!showForgotPassword" @submit.prevent="handleLogin" class="mt-10">
            <!-- Email Input -->
            <div class="mb-6">
              <label class="form-label">
                Email Address
              </label>
              <div class="relative form-input input-group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i class="lucide lucide-mail text-base text-gray-400 input-icon"></i>
                </div>
                <input
                  type="email"
                  v-model="email"
                  placeholder="Enter your email address"
                  class="input-field w-full pl-10 pr-10 py-3"
                  :class="{ 'border-[var(--primary-color)]': email.length > 0 }"
                />
                <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <div
                    class="w-2 h-2 rounded-full bg-green-500 transition-all duration-200"
                    :class="email.length > 0 ? 'opacity-100' : 'opacity-0'"
                    :style="email.length > 0 ? 'box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);' : ''"
                  ></div>
                </div>
              </div>
              <div v-if="email && !email.includes('@')" class="mt-1 text-xs text-red-500">
                Please enter a valid email address
              </div>
            </div>

            <!-- Password Input -->
            <div class="mb-4">
              <label class="form-label">
                Password
              </label>
              <div class="relative form-input input-group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i class="lucide lucide-key text-base text-gray-400 input-icon"></i>
                </div>
                <input
                  :type="showPassword ? 'text' : 'password'"
                  v-model="password"
                  placeholder="Enter your password"
                  class="input-field w-full pl-10 pr-10 py-3"
                  :class="{ 'border-[var(--primary-color)]': password.length > 0 }"
                />
                <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    @click="togglePasswordVisibility"
                    class="text-gray-400 hover:text-[var(--primary-color)] focus:outline-none transition-colors duration-200"
                  >
                    <i :class="showPassword ? 'lucide lucide-eye-off' : 'lucide lucide-eye'" class="text-base"></i>
                  </button>
                </div>
              </div>
              <!-- Password Strength Indicator -->
              <div class="password-strength">
                <div
                  class="password-strength-bar"
                  :style="{ width: password.length > 0 ? Math.min((password.length / 8) * 100, 100) + '%' : '0%' }"
                ></div>
              </div>
              <div v-if="password.length > 0 && password.length < 6" class="mt-1 text-xs text-red-500">
                Password should be at least 6 characters
              </div>
            </div>

            <div class="flex items-center mb-6">
              <input
                type="checkbox"
                v-model="rememberMe"
                :disabled="loading"
                class="w-4 h-4 accent-[var(--primary-color)] cursor-pointer"
                id="remember"
              />
              <label for="remember" class="ml-2 text-sm text-black cursor-pointer">
                Remember me
              </label>
            </div>

            <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <div class="flex items-center">
                <i class="lucide lucide-alert-circle text-base mr-2"></i>
                {{ error }}
              </div>
            </div>

            <button
              type="submit"
              class="w-full rounded font-medium flex items-center justify-center"
              style="
                background: #0d2691;
                color: white;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 500;
                border: none;
                min-height: 48px;
                box-shadow: 0 4px 14px rgba(13, 38, 145, 0.3);
                transition: all 0.2s ease;
              "
              onmouseover="this.style.opacity='0.9'"
              onmouseout="this.style.opacity='1'"
            >
              LOG IN
            </button>
          </form>

          <!-- Reset Password Form -->
          <form v-else @submit.prevent="handleResetPassword" class="mt-10">
            <div class="mb-4">
              <button
                type="button"
                @click="backToLogin"
                class="flex items-center text-[var(--text-secondary)] hover:text-[var(--primary-color)] transition-colors text-sm"
              >
                <i class="lucide lucide-chevron-left text-base mr-1"></i>
                Back to login
              </button>
            </div>

            <div class="mb-5">
              <div class="flex items-center input-border bg-white rounded px-3 py-2.5 shadow-sm">
                <i class="lucide lucide-mail text-base text-gray-400 mr-3"></i>
                <input
                  type="email"
                  v-model="resetEmail"
                  placeholder="Your email address"
                  :disabled="loading"
                  class="flex-1 outline-none text-gray-700 bg-transparent placeholder-gray-400 text-sm"
                  required
                />
              </div>
            </div>

            <div class="mb-5">
              <div class="flex items-center input-border bg-white rounded px-3 py-2.5 shadow-sm">
                <i class="lucide lucide-key text-base text-gray-400 mr-3"></i>
                <input
                  type="password"
                  v-model="newPassword"
                  placeholder="New password"
                  :disabled="loading"
                  class="flex-1 outline-none text-gray-700 bg-transparent placeholder-gray-400 text-sm"
                  required
                />
              </div>
            </div>

            <div class="mb-5">
              <div class="flex items-center input-border bg-white rounded px-3 py-2.5 shadow-sm">
                <i class="lucide lucide-shield text-base text-gray-400 mr-3"></i>
                <input
                  type="text"
                  v-model="resetToken"
                  placeholder="Reset token"
                  :disabled="loading"
                  class="flex-1 outline-none text-gray-700 bg-transparent placeholder-gray-400 text-sm"
                  required
                />
              </div>
            </div>

            <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <div class="flex items-center">
                <i class="lucide lucide-alert-circle text-base mr-2"></i>
                {{ error }}
              </div>
            </div>

            <div v-if="successMessage" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              <div class="flex items-center">
                <i class="lucide lucide-check-circle text-base mr-2"></i>
                {{ successMessage }}
              </div>
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded font-medium transition-all flex items-center justify-center"
            >
              <i class="lucide lucide-refresh-cw text-base mr-2"></i>
              <span v-if="loading" class="inline-flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
              <span v-else>Reset Password</span>
            </button>
          </form>

          <!-- Security Notice for Reset Password -->
          <div v-if="showForgotPassword" class="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex">
              <i class="lucide lucide-info text-base text-blue-600 mr-2 flex-shrink-0 mt-0.5"></i>
              <div class="text-sm text-blue-800">
                <p class="font-medium mb-1">Security Notice</p>
                <p class="text-xs">Remember your new password well, as there is no OTP when logging back in.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Welcome Panel - Right Side (WelcomePanel.js) -->
      <div class="hidden lg:flex lg:w-[40%] blue-gradient-bg relative overflow-hidden items-center justify-center" data-name="welcome-panel">
        <div class="absolute inset-0">
          <div class="absolute -top-32 -right-32 w-[400px] h-[400px] bg-blue-400 rounded-full opacity-30 blur-3xl"></div>
          <div class="absolute top-20 right-20 w-[350px] h-[350px] bg-blue-500 rounded-full opacity-25 blur-3xl"></div>
          <div class="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-blue-600 rounded-full opacity-30 blur-3xl"></div>
          <div class="absolute bottom-32 right-10 w-[380px] h-[380px] bg-blue-400 rounded-full opacity-20 blur-3xl"></div>
        </div>

        <!-- Floating Logo in Welcome Panel -->
        <div class="welcome-panel-logo">
          <img
            src="/src/assets/icon_light.ico"
            alt="Jelantik Logo"
            @error="handleImageError"
          />
        </div>

        <div class="relative z-10 text-center text-white px-12">
          <h1 class="text-5xl font-bold mb-2 tracking-wide">WELCOME!</h1>
          <p class="text-base opacity-90 max-w-sm mx-auto leading-relaxed">
            PORTAL FTTH & BILLING AJNUSA V3.5
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* CSS Variables from template */
:root {
  --primary-color: #0d2691;
  --secondary-color: #1e40af;
  --accent-color: #3b82f6;
  --text-primary: #374151;
  --text-secondary: #6b7280;
  --bg-light: #f3f4f6;
  --card-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Template Base Styles */
.gradient-bg {
  background: #f0f2f5;
}

.glass-effect {
  background: #ffffff;
}

.input-border {
  border-left: 3px solid var(--primary-color);
}

.btn-primary {
  background: var(--primary-color) !important;
  color: #ffffff !important;
  height: auto;
  min-height: 48px;
  font-weight: 500;
  font-size: 16px;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 4px 12px rgba(13, 38, 145, 0.3);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  opacity: 0.9 !important;
  box-shadow: 0 6px 16px rgba(13, 38, 145, 0.4);
}

.blue-gradient-bg {
  background: linear-gradient(135deg, #0d47a1 0%, #2196f3 50%, #64b5f6 100%);
}

.card-shadow {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Enhanced base styles */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #e5e7eb;
}

/* Button visibility fix */
button[type="submit"] {
  position: relative !important;
  z-index: 10 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

/* Button text visibility fix */
button[type="submit"],
button[type="submit"] *,
button[type="submit"] i,
button[type="submit"] span,
button[type="submit"]::before,
button[type="submit"]::after {
  color: white !important;
  opacity: 1 !important;
  visibility: visible !important;
  text-shadow: none !important;
}

button[type="submit"] .lucide {
  color: white !important;
}

/* Global button fix */
* button {
  color: white !important;
}

/* Text inside button fix */
button * {
  color: inherit !important;
}

/* Enhanced Form Styling */
.form-input {
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
}

.form-input:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
}

.form-input:focus-within {
  transform: translateY(-3px);
  box-shadow:
    0 12px 24px rgba(13, 38, 145, 0.15),
    0 6px 12px rgba(13, 38, 145, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.9);
}

.input-group {
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border-radius: 12px;
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.05),
    inset 0 1px 2px rgba(255, 255, 255, 0.9);
  border: 2px solid #e5e7eb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-group:hover {
  border-color: #d1d5db;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08),
    inset 0 1px 2px rgba(255, 255, 255, 0.9),
    0 0 0 1px rgba(255, 255, 255, 0.5);
}

.input-group:focus-within {
  border-color: var(--primary-color);
  box-shadow:
    0 12px 24px rgba(13, 38, 145, 0.15),
    0 6px 12px rgba(13, 38, 145, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.9),
    0 0 0 3px rgba(13, 38, 145, 0.1);
}

.input-field {
  background: white !important;
  border: 3px solid #e5e7eb !important;
  border-radius: 12px !important;
  padding: 12px 16px !important;
  font-size: 14px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.06),
    0 4px 8px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.05) !important;
  position: relative !important;
}

.input-field:hover {
  border-color: #d1d5db !important;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.06),
    0 8px 16px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-1px) !important;
}

.input-field:focus {
  border-color: var(--primary-color) !important;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.06),
    0 12px 24px rgba(13, 38, 145, 0.15),
    0 6px 12px rgba(13, 38, 145, 0.1),
    0 0 0 4px rgba(13, 38, 145, 0.1) !important;
  outline: none !important;
  transform: translateY(-2px) !important;
}

.input-icon {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  background: linear-gradient(145deg, #9ca3af, #6b7280);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.input-group:hover .input-icon {
  background: linear-gradient(145deg, var(--primary-color), #1e40af);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 4px 8px rgba(13, 38, 145, 0.3)) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  transform: scale(1.1);
}

.input-group:focus-within .input-icon {
  background: linear-gradient(145deg, var(--primary-color), #1e40af);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 6px 12px rgba(13, 38, 145, 0.4)) drop-shadow(0 3px 6px rgba(0, 0, 0, 0.3));
  transform: scale(1.15);
}

/* Remove background from icons in buttons */
button .input-icon,
button .lucide {
  background: none !important;
  -webkit-text-fill-color: unset !important;
  color: inherit !important;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2)) !important;
}

button:hover .input-icon,
button:hover .lucide {
  filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.3)) !important;
}

/* Elegant Gradient Background - Logo Theme */
.gradient-bg {
  background: linear-gradient(
    135deg,
    #0d2691 0%,
    #1e40af 30%,
    #2563eb 60%,
    #3b82f6 100%
  );
  background-size: 100% 100%;
  position: relative;
}

.gradient-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(
      circle at 20% 30%,
      rgba(13, 38, 145, 0.4),
      transparent 50%
    ),
    radial-gradient(
      circle at 80% 70%,
      rgba(59, 130, 246, 0.3),
      transparent 50%
    ),
    radial-gradient(
      circle at 50% 90%,
      rgba(37, 99, 235, 0.2),
      transparent 40%
    );
  z-index: 1;
  opacity: 0.8;
}

/* Enhanced Login Card with Glassmorphism */
.login-card-enhanced {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 100px rgba(120, 119, 198, 0.1),
    inset 0 1px 3px rgba(255, 255, 255, 0.6) !important;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.98) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
}


/* Password strength indicator */
.password-strength {
  height: 4px;
  border-radius: 2px;
  overflow: hidden;
  background: #e5e7eb;
  margin-top: 8px;
}

.password-strength-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
  transition: width 0.3s ease;
  border-radius: 2px;
}

/* Floating label effect */
.form-label {
  color: #374151 !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  margin-bottom: 8px !important;
  display: block !important;
}

/* Input field styling fix */
input[type="text"],
input[type="password"],
input[type="email"] {
  background-color: white !important;
  border: 2px solid #e5e7eb !important;
  outline: none !important;
}

/* Tailwind-like utilities for compatibility */
.min-h-screen {
  min-height: 100vh;
}

.flex {
  display: flex;
}

.flex-col {
  flex-direction: column;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.w-full {
  width: 100%;
}

.max-w-4xl {
  max-width: 56rem;
}

.max-w-6xl {
  max-width: 72rem;
}

.max-w-7xl {
  max-width: 80rem;
}

.rounded-3xl {
  border-radius: 1.5rem;
}

.rounded-t-2xl {
  border-top-left-radius: 1rem;
  border-top-right-radius: 1rem;
}

.rounded-b-3xl {
  border-bottom-left-radius: 1.5rem;
  border-bottom-right-radius: 1.5rem;
}

.overflow-hidden {
  overflow: hidden;
}

.bg-white {
  background-color: #ffffff;
}

.hidden {
  display: none;
}

.lg\:flex {
  display: flex;
}

.lg\:w-\[60\%\] {
  width: 60%;
}

.lg\:w-\[55\%\] {
  width: 55%;
}

.lg\:w-\[45\%\] {
  width: 45%;
}

.lg\:w-\[40\%\] {
  width: 40%;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.top-4 {
  top: 1rem;
}

.right-4 {
  right: 1rem;
}

.z-10 {
  z-index: 10;
}

.absolute {
  position: absolute;
}

.inset-0 {
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.z-10 {
  z-index: 10;
}

.text-center {
  text-align: center;
}

.text-white {
  color: #ffffff;
}

.px-12 {
  padding-left: 3rem;
  padding-right: 3rem;
}

.px-8 {
  padding-left: 2rem;
  padding-right: 2rem;
}

.px-3 {
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

.pr-4 {
  padding-right: 1rem;
}

.pr-10 {
  padding-right: 2.5rem;
}


.py-2\.5 {
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
}

.py-16 {
  padding-top: 4rem;
  padding-bottom: 4rem;
}

.py-3 {
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

.mb-5 {
  margin-bottom: 1.25rem;
}

.mb-8 {
  margin-bottom: 2rem;
}

.mb-3 {
  margin-bottom: 0.75rem;
}

.mb-1 {
  margin-bottom: 0.25rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mb-6 {
  margin-bottom: 1.5rem;
}

.mr-2 {
  margin-right: 0.5rem;
}

.mr-3 {
  margin-right: 0.75rem;
}

.ml-2 {
  margin-left: 0.5rem;
}

.mt-10 {
  margin-top: 2.5rem;
}

.mt-6 {
  margin-top: 1.5rem;
}

.max-w-sm {
  max-width: 24rem;
}

.max-w-md {
  max-width: 28rem;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.text-xl {
  font-size: 1.25rem;
  line-height: 1.75rem;
}

.text-base {
  font-size: 1rem;
  line-height: 1.5rem;
}

.text-5xl {
  font-size: 3rem;
  line-height: 2;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

.font-semibold {
  font-weight: 600;
}

.font-bold {
  font-weight: 700;
}

.font-medium {
  font-weight: 500;
}

.tracking-wide {
  letter-spacing: 0.05em;
}

.opacity-90 {
  opacity: 0.9;
}

.rounded {
  border-radius: 0.25rem;
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.text-gray-700 {
  color: #374151;
}

.text-gray-400 {
  color: #9ca3af;
}

.bg-red-50 {
  background-color: #fef2f2;
}

.bg-green-50 {
  background-color: #f0fdf4;
}

.bg-blue-50 {
  background-color: #eff6ff;
}

.text-red-700 {
  color: #b91c1c;
}

.text-green-700 {
  color: #15803d;
}

.text-blue-700 {
  color: #1d4ed8;
}

.text-blue-800 {
  color: #1e40af;
}

.text-blue-600 {
  color: #2563eb;
}

.border-b-2 {
  border-bottom-width: 2px;
}

.border-gray-300 {
  border-color: #d1d5db;
}

.border-red-200 {
  border-color: #fecaca;
}

.border-green-200 {
  border-color: #bbf7d0;
}

.border-blue-200 {
  border-color: #bfdbfe;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.inline-block {
  display: inline-block;
}

.transition-colors {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.hover\:opacity-90:hover {
  opacity: 0.9;
}

.hover\:bg-green-700:hover {
  background-color: #15803d;
}

.hover\:text-\[var\(--primary-color\)\]:hover {
  color: var(--primary-color);
}

.focus\:outline-none:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.disabled\:cursor-not-allowed:disabled {
  cursor: not-allowed;
}

.cursor-pointer {
  cursor: pointer;
}

.flex-1 {
  flex: 1 1 0%;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

.mt-0\.5 {
  margin-top: 0.125rem;
}

.font-medium {
  font-weight: 500;
}

.inline-flex {
  display: inline-flex;
}

.-ml-1 {
  margin-left: -0.25rem;
}

.h-4 {
  height: 1rem;
}

.h-10 {
  height: 4.5rem;
}

.w-4 {
  width: 1rem;
}

.w-14 {
  width: 3.5rem;
}

.h-14 {
  height: 3.5rem;
}

.rounded-xl {
  border-radius: 0.75rem;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

/* Additional utility classes for responsive design */
.sm\:px-6 {
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

.md\:px-8 {
  padding-left: 2rem;
  padding-right: 2rem;
}

.py-6 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

/* Logo header styles */
.logo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 1rem;
}

.logo-header h2 {
  flex: 1;
  margin: 0;
}

.logo-container {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.logo-container img {
  transition: all 0.3s ease;
  max-height: 5rem;
  width: auto;
}

.logo-container:hover img {
  transform: scale(1.05);
}

/* Hide logo on desktop (min-width: 1024px) */
@media (min-width: 1024px) {
  .logo-container {
    display: none;
  }

  .logo-header {
    justify-content: flex-start;
  }
}

/* Desktop enhancements (min-width: 1024px) */
@media (min-width: 1024px) {
  .logo-container {
    display: none;
  }

  .logo-header {
    justify-content: flex-start;
    margin-bottom: 16px;
  }

  /* Floating logo animation for welcome panel */
  .welcome-panel-logo {
    position: absolute;
    top: 25%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation: floating 3s ease-in-out infinite;
    z-index: 5;
  }

  /* Floating animation for logo */
  @keyframes floating {
    0%, 100% {
      transform: translate(-50%, -50%) translateY(0px);
    }
    50% {
      transform: translate(-50%, -50%) translateY(-15px);
    }
  }

  /* Logo glow effect on desktop */
  .welcome-panel-logo img {
    filter: drop-shadow(0 15px 30px rgba(255, 255, 255, 0.5));
    animation: glow 2s ease-in-out infinite alternate;
    height: 150px !important;
    width: auto;
    transition: all 0.3s ease;
  }

  .welcome-panel-logo:hover img {
    transform: scale(1.1) !important;
    filter: drop-shadow(0 25px 50px rgba(255, 255, 255, 0.8));
  }

  @keyframes glow {
    0% {
      filter: drop-shadow(0 15px 30px rgba(255, 255, 255, 0.5));
    }
    100% {
      filter: drop-shadow(0 25px 40px rgba(255, 255, 255, 0.7));
    }
  }

  /* Enlarge form container on desktop */
  .max-w-md {
    max-width: 700px !important;
  }

  /* Enlarge form inputs on desktop */
  .input-field {
    padding: 18px 20px !important;
    font-size: 18px !important;
    min-height: 56px !important;
  }

  .input-group {
    padding: 8px !important;
  }

  /* Enlarge form labels on desktop */
  .form-label {
    font-size: 16px !important;
    font-weight: 600 !important;
    margin-bottom: 12px !important;
  }

  /* Enlarge form heading on desktop */
  .logo-header h2 {
    font-size: 24px !important;
    margin-bottom: 8px !important;
  }

  /* Enlarge button on desktop */
  button[type="submit"] {
    padding: 16px 32px !important;
    font-size: 18px !important;
    min-height: 56px !important;
    font-weight: 600 !important;
  }

  /* Increase spacing on desktop */
  .mb-4 {
    margin-bottom: 24px !important;
  }

  .mb-6 {
    margin-bottom: 32px !important;
  }

  .mt-10 {
    margin-top: 40px !important;
  }

  /* Enlarge icons on desktop */
  .input-icon {
    font-size: 20px !important;
  }

  /* Increase container padding on desktop */
  .glass-effect {
    padding: 48px !important;
  }
}

/* Show logo on mobile and tablets only */
@media (max-width: 1023px) {
  .w-full {
    width: 100% !important;
  }

  .logo-container {
    display: flex;
    position: relative;
    top: auto;
    left: auto;
    transform: none;
    animation: none;
  }

  .logo-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 16px;
  }

  .logo-container img {
    height: 4.5rem !important;
    filter: none;
    animation: none;
    transition: all 0.3s ease;
  }

  .logo-container:hover img {
    transform: scale(1.05);
    filter: none;
  }
}

@media (max-width: 768px) {
  .logo-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .logo-container img {
    height: 4rem !important;
  }
}

@media (max-width: 640px) {
  .logo-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .logo-container img {
    height: 3.5rem !important;
  }

  .logo-header h2 {
    flex: 1;
    margin: 0;
  }
}

.bg-\[var\(--secondary-color\)\] {
  background-color: var(--secondary-color);
}

.text-\[var\(--primary-color\)\] {
  color: var(--primary-color);
}

.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
}

/* Loading spinner */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Responsive styles */
@media (min-width: 1024px) {
  .hidden {
    display: block;
  }

  .lg\:flex {
    display: flex;
  }

  .lg\:w-\[55\%\] {
    width: 55%;
  }

  .lg\:w-\[45\%\] {
    width: 45%;
  }
}

@media (max-width: 1023px) {
  /* Hide welcome panel on tablets and smaller */
  .lg\:flex {
    display: none;
  }

  /* Make form container more compact on smaller screens */
  .login-card-enhanced {
    width: 95vw !important;
    max-width: 95vw !important;
    border-radius: 1.5rem !important;
    min-height: auto !important;
    height: auto;
    margin: 0 auto;
  }

  /* Adjust form section to be full width on mobile */
  .glass-effect {
    width: 100% !important;
    border-right: none !important;
    padding: 2rem 1.5rem !important;
  }

  /* Center form better on mobile */
  .max-w-md {
    max-width: 90%;
  }
}

@media (max-width: 768px) {
  .px-12 {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .py-16 {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }

  .px-8 {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  /* Additional mobile optimizations */
  .gradient-bg {
    padding: 1rem;
  }

  .login-card-enhanced {
    width: 95vw !important;
    max-width: 95vw !important;
    border-radius: 1.5rem !important;
    height: auto !important;
    min-height: auto !important;
  }

  .glass-effect {
    padding: 1.5rem 1rem !important;
  }
}

@media (max-width: 640px) {
  .gradient-bg {
    padding: 0.5rem;
  }

  .glass-effect {
    padding: 1rem 0.75rem !important;
  }

  .max-w-md {
    max-width: 95%;
  }

  .login-card-enhanced {
    width: 98vw !important;
    max-width: 98vw !important;
    border-radius: 1rem !important;
    height: auto !important;
    min-height: auto !important;
  }
}
</style>

