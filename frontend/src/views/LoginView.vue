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
  <div class="ftth-login-wrapper">
    <!-- Enhanced Fiber Optic Background Animation -->
    <div class="fiber-bg">
      <div class="fiber-strand" v-for="i in 15" :key="i" :style="{
        left: Math.random() * 100 + '%',
        animationDelay: Math.random() * 3 + 's',
        animationDuration: (3 + Math.random() * 2) + 's'
      }"></div>
      <div class="light-pulse" v-for="i in 12" :key="`pulse-${i}`" :style="{
        left: Math.random() * 100 + '%',
        top: Math.random() * 100 + '%',
        animationDelay: Math.random() * 4 + 's'
      }"></div>
      
      <!-- Floating Particles -->
      <div class="floating-particles">
        <div class="particle" v-for="i in 20" :key="`particle-${i}`" :style="{
          left: Math.random() * 100 + '%',
          top: Math.random() * 100 + '%',
          animationDelay: Math.random() * 10 + 's',
          animationDuration: (8 + Math.random() * 4) + 's'
        }"></div>
      </div>
    </div>

    <!-- Main Container with 3D perspective -->
    <div class="main-container">
      <!-- Enhanced Branding Section -->
      <div class="branding-section">
        <div class="brand-container">
          <!-- Logo Section with 3D effects -->
          <div class="logo-section">
            <div class="logo-wrapper-3d">
              <div class="logo-container">
                <img src="@/assets/images/Jelantik 1.webp" alt="Artacom Logo" class="main-logo" />
                <div class="logo-reflection"></div>
                <div class="logo-glow-3d"></div>
              </div>
            </div>
            <div class="brand-text">
              <h1 class="brand-title">Artacom FTTH Portal</h1>
              <p class="brand-subtitle">Fiber To The Home Management</p>
              <div class="brand-underline"></div>
            </div>
          </div>

          <!-- Enhanced Features Grid with 3D cards -->
          <div class="features-grid">
            <div class="feature-card-3d">
              <div class="card-content">
                <div class="feature-icon fiber-icon">🌐</div>
                <h3>Network Management</h3>
                <p>Monitor dan kelola jaringan fiber optik secara real-time</p>
                <div class="card-glow"></div>
              </div>
            </div>
            <div class="feature-card-3d">
              <div class="card-content">
                <div class="feature-icon speed-icon">⚡</div>
                <h3>High-Speed Access</h3>
                <p>Akses cepat ke sistem monitoring bandwidth</p>
                <div class="card-glow"></div>
              </div>
            </div>
            <div class="feature-card-3d">
              <div class="card-content">
                <div class="feature-icon customer-icon">👥</div>
                <h3>Customer Portal</h3>
                <p>Manajemen pelanggan FTTH terintegrasi</p>
                <div class="card-glow"></div>
              </div>
            </div>
            <div class="feature-card-3d">
              <div class="card-content">
                <div class="feature-icon analytics-icon">📊</div>
                <h3>Analytics Dashboard</h3>
                <p>Laporan performa jaringan komprehensif</p>
                <div class="card-glow"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Enhanced 3D Login Section -->
      <div class="login-section">
        <div class="login-perspective">
          <div class="login-card-3d">
            <!-- Glass morphism overlay -->
            <div class="glass-overlay"></div>
            
            <!-- Mobile Brand (Hidden on desktop) -->
            <div class="mobile-brand">
              <div class="mobile-logo-3d">
                <img src="@/assets/images/Jelantik 1.webp" alt="Logo" class="mobile-logo" />
                <div class="mobile-logo-shadow"></div>
              </div>
              <h2>Artacom FTTH Portal</h2>
              <p>Fiber To The Home Management</p>
            </div>

            <!-- Login Form with 3D elements -->
            <div v-if="!showForgotPassword" class="auth-form">
              <div class="form-header-3d">
                <div class="header-decoration">
                  <div class="deco-line"></div>
                  <div class="deco-dot"></div>
                  <div class="deco-line"></div>
                </div>
                <h3>Portal Access</h3>
                <p>Masuk ke sistem manajemen FTTH</p>
                <div class="header-glow"></div>
              </div>

              <form @submit.prevent="handleLogin" class="form-3d">
                <div class="input-group-3d">
                  <div class="input-wrapper">
                    <div class="input-bg"></div>
                    <label class="input-label-3d">
                      <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                      </svg>
                      Email Address
                    </label>
                    <input 
                      type="email" 
                      v-model="email" 
                      required 
                      :disabled="loading"
                      placeholder="your.email@provider.com"
                      class="form-input-3d"
                    />
                    <div class="input-focus-effect"></div>
                  </div>
                </div>
                
                <div class="input-group-3d">
                  <div class="input-wrapper">
                    <div class="input-bg"></div>
                    <label class="input-label-3d">
                      <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Password
                    </label>
                    <input 
                      type="password" 
                      v-model="password" 
                      required 
                      :disabled="loading"
                      placeholder="••••••••••••"
                      class="form-input-3d"
                    />
                    <div class="input-focus-effect"></div>
                  </div>
                </div>
                
                <div v-if="error" class="alert-3d alert-error">
                  <div class="alert-content">
                    <svg class="alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    {{ error }}
                  </div>
                  <div class="alert-glow error-glow"></div>
                </div>
                
                <button type="submit" :disabled="loading" class="submit-btn-3d">
                  <div class="btn-content">
                    <span v-if="loading" class="spinner-3d"></span>
                    <svg v-if="!loading" class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    {{ loading ? 'Authenticating...' : 'Access Portal' }}
                  </div>
                  <div class="btn-glow"></div>
                  <div class="btn-ripple"></div>
                </button>
              </form>
            </div>

            <!-- Reset Password Form with 3D elements -->
            <div v-else class="auth-form reset-form">
              <div class="form-header-3d">
                <button @click="backToLogin" class="back-btn-3d">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  <div class="btn-ripple"></div>
                </button>
                <div class="header-decoration">
                  <div class="deco-line"></div>
                  <div class="deco-dot"></div>
                  <div class="deco-line"></div>
                </div>
                <h3>Reset Password</h3>
                <p>Atur ulang password akses portal</p>
                <div class="header-glow"></div>
              </div>

              <form @submit.prevent="handleResetPassword" class="form-3d">
                <div class="input-group-3d">
                  <div class="input-wrapper">
                    <div class="input-bg"></div>
                    <label class="input-label-3d">
                      <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                      </svg>
                      Email Address
                    </label>
                    <input 
                      type="email" 
                      v-model="resetEmail" 
                      required 
                      :disabled="loading"
                      placeholder="your.email@provider.com"
                      class="form-input-3d"
                    />
                    <div class="input-focus-effect"></div>
                  </div>
                </div>

                <div class="input-group-3d">
                  <div class="input-wrapper">
                    <div class="input-bg"></div>
                    <label class="input-label-3d">
                      <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                      </svg>
                      Password Baru
                    </label>
                    <input 
                      type="password" 
                      v-model="newPassword" 
                      required 
                      :disabled="loading"
                      placeholder="••••••••••••"
                      class="form-input-3d"
                    />
                    <div class="input-focus-effect"></div>
                  </div>
                </div>

                <div class="input-group-3d">
                  <div class="input-wrapper">
                    <div class="input-bg"></div>
                    <label class="input-label-3d">
                      <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      Reset Token
                    </label>
                    <input 
                      type="text" 
                      v-model="resetToken" 
                      required 
                      :disabled="loading"
                      placeholder="Masukkan token reset"
                      class="form-input-3d"
                    />
                    <div class="input-focus-effect"></div>
                  </div>
                </div>
                
                <div v-if="error" class="alert-3d alert-error">
                  <div class="alert-content">
                    <svg class="alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    {{ error }}
                  </div>
                  <div class="alert-glow error-glow"></div>
                </div>

                <div v-if="successMessage" class="alert-3d alert-success">
                  <div class="alert-content">
                    <svg class="alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {{ successMessage }}
                  </div>
                  <div class="alert-glow success-glow"></div>
                </div>
                
                <button type="submit" :disabled="loading" class="submit-btn-3d reset-btn">
                  <div class="btn-content">
                    <span v-if="loading" class="spinner-3d"></span>
                    <svg v-if="!loading" class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    {{ loading ? 'Processing...' : 'Reset Password' }}
                  </div>
                  <div class="btn-glow reset-glow"></div>
                  <div class="btn-ripple"></div>
                </button>

                <button type="button" @click="backToLogin" class="link-btn-3d">
                  <span>Kembali ke halaman login</span>
                  <div class="link-underline"></div>
                </button>
              </form>

              <!-- Enhanced Security Notice -->
              <div class="security-notice-3d">
                <div class="notice-content">
                  <svg class="notice-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <div>
                    <h4>Catatan Keamanan</h4>
                    <p>Password yang sudah diubah, harap diingat dengan baik karena tidak ada OTP saat login kembali.</p>
                  </div>
                </div>
                <div class="notice-glow"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Base Styles with enhanced 3D support - IMPROVED CONTRAST */
.ftth-login-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
  overflow: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  perspective: 1000px;
}

/* Enhanced Fiber Optic Background Animation */
.fiber-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.fiber-strand {
  position: absolute;
  width: 2px;
  height: 100vh;
  background: linear-gradient(to bottom, transparent, #0ea5e9, #3b82f6, transparent);
  animation: fiberFlow infinite linear;
  opacity: 0.4;
  box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
}

.light-pulse {
  position: absolute;
  width: 6px;
  height: 6px;
  background: radial-gradient(circle, #0ea5e9, #3b82f6);
  border-radius: 50%;
  animation: lightPulse 4s infinite ease-in-out;
  box-shadow: 0 0 20px #0ea5e9, 0 0 40px rgba(14, 165, 233, 0.2);
}

.floating-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  animation: floatParticle infinite ease-in-out;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.5);
}

@keyframes fiberFlow {
  0% { transform: translateY(-100vh) scaleY(0) rotateZ(0deg); opacity: 0; }
  10% { opacity: 0.4; }
  90% { opacity: 0.4; }
  100% { transform: translateY(100vh) scaleY(1) rotateZ(5deg); opacity: 0; }
}

@keyframes lightPulse {
  0%, 100% { opacity: 0.3; transform: scale(1) rotateZ(0deg); }
  50% { opacity: 0.8; transform: scale(1.8) rotateZ(180deg); }
}

@keyframes floatParticle {
  0%, 100% { transform: translateY(0px) translateX(0px) scale(1); opacity: 0.4; }
  25% { transform: translateY(-20px) translateX(10px) scale(1.2); opacity: 0.8; }
  50% { transform: translateY(-10px) translateX(-5px) scale(0.8); opacity: 0.6; }
  75% { transform: translateY(-30px) translateX(15px) scale(1.1); opacity: 0.7; }
}

/* Enhanced Main Layout with 3D perspective */
.main-container {
  position: relative;
  display: flex;
  width: 100%;
  height: 100vh;
  z-index: 2;
  transform-style: preserve-3d;
}

.branding-section {
  flex: 1.2;
  background: rgba(15, 23, 42, 0.98);
  /* backdrop-filter: blur(15px); -- DIHAPUS untuk menghilangkan efek blur pada section ini */
  border-right: 2px solid rgba(14, 165, 233, 0.3);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 3rem;
  overflow-y: auto;
  position: relative;
  transform: translateZ(10px);
}

.branding-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.05) 0%, transparent 50%, rgba(59, 130, 246, 0.05) 100%);
  z-index: -1;
}

.brand-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Enhanced Logo Section with 3D effects */
.logo-section {
  text-align: center;
  margin-bottom: 3rem;
}

.logo-wrapper-3d {
  perspective: 500px;
  margin: 0 auto 2rem;
  width: 120px;
  height: 120px;
}

.logo-container {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  animation: logoFloat 6s ease-in-out infinite;
}

.main-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 28px;
  border: 3px solid rgba(14, 165, 233, 0.6);
  z-index: 3;
  position: relative;
  transform: translateZ(20px);
  box-shadow: 
    0 10px 30px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(14, 165, 233, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.logo-reflection {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  height: 50%;
  background: linear-gradient(to bottom, rgba(14, 165, 233, 0.15), transparent);
  border-radius: 0 0 28px 28px;
  transform: scaleY(-1) translateZ(-10px);
  opacity: 0.4;
}

.logo-glow-3d {
  position: absolute;
  top: -15px;
  left: -15px;
  right: -15px;
  bottom: -15px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.4) 0%, rgba(59, 130, 246, 0.2) 50%, transparent 70%);
  border-radius: 40px;
  animation: logoGlow3D 4s ease-in-out infinite alternate;
  transform: translateZ(-10px);
  filter: blur(8px);
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px) rotateY(0deg) rotateX(0deg); }
  25% { transform: translateY(-10px) rotateY(5deg) rotateX(2deg); }
  50% { transform: translateY(-5px) rotateY(0deg) rotateX(-2deg); }
  75% { transform: translateY(-15px) rotateY(-5deg) rotateX(2deg); }
}

@keyframes logoGlow3D {
  0% { opacity: 0.4; transform: translateZ(-10px) scale(1) rotateZ(0deg); }
  100% { opacity: 0.7; transform: translateZ(-10px) scale(1.1) rotateZ(5deg); }
}

.brand-text {
  color: white;
  transform: translateZ(5px);
}

.brand-title {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #ffffff 0%, #0ea5e9 30%, #3b82f6 70%, #1e40af 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 20px rgba(14, 165, 233, 0.3);
  animation: titleShimmer 3s ease-in-out infinite;
}

.brand-subtitle {
  font-size: 1.3rem;
  color: #cbd5e1;
  font-weight: 500;
  margin-bottom: 1rem;
}

.brand-underline {
  width: 60px;
  height: 3px;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  margin: 0 auto;
  border-radius: 2px;
  box-shadow: 0 0 20px rgba(14, 165, 233, 0.4);
  animation: underlineGlow 2s ease-in-out infinite alternate;
}

@keyframes titleShimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes underlineGlow {
  0% { box-shadow: 0 0 20px rgba(14, 165, 233, 0.4); }
  100% { box-shadow: 0 0 30px rgba(14, 165, 233, 0.7), 0 0 40px rgba(59, 130, 246, 0.3); }
}

/* Enhanced Features Grid with 3D cards - IMPROVED CONTRAST & BLUR REMOVED */
.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 2rem;
  perspective: 800px;
}

.feature-card-3d {
  position: relative;
  transform-style: preserve-3d;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.feature-card-3d:hover {
  transform: translateY(-8px) rotateX(3deg) rotateY(3deg) scale(1.02);
}

.card-content {
  background: rgba(41, 51, 65, 0.7); /* DIUBAH - Warna latar belakang diubah menjadi lebih solid */
  /* backdrop-filter: blur(8px); -- DIHAPUS untuk menghilangkan efek blur */
  border: 1px solid rgba(59, 130, 246, 0.5); /* DIUBAH - Border dibuat lebih terlihat */
  border-radius: 20px;
  padding: 1.8rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  transform: translateZ(0);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1), /* DIUBAH - Efek shadow disesuaikan */
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
}

.card-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  transition: left 0.6s ease;
}

.feature-card-3d:hover .card-content::before {
  left: 100%;
}

.card-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(59, 130, 246, 0.2));
  border-radius: 10px;
  opacity: 0;
  transition: opacity 0.4s ease;
  transform: translateZ(-5px);
  filter: blur(1px);
}

.feature-card-3d:hover .card-glow {
  opacity: 1;
  animation: cardGlowPulse 2s ease-in-out infinite;
}

@keyframes cardGlowPulse {
  0%, 100% { transform: translateZ(-5px) scale(1); }
  50% { transform: translateZ(-5px) scale(1.05); }
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  display: block;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0px) rotateZ(0deg); }
  50% { transform: translateY(-5px) rotateZ(3deg); }
}

/* DIUBAH - Menghapus text-shadow untuk menghilangkan blur pada ikon */
.fiber-icon { color: #0ea5e9; }
.speed-icon { color: #f59e0b; }
.customer-icon { color: #8b5cf6; }
.analytics-icon { color: #10b981; }

.card-content h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.8rem;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
}

.card-content p {
  font-size: 0.9rem;
  color: #f1f5f9;
  line-height: 1.5;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}


/* Enhanced 3D Login Section - MAJOR CONTRAST IMPROVEMENTS */
.login-section {
  flex: 1;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  min-height: 100vh;
  perspective: 1200px;
}

.login-perspective {
  width: 100%;
  max-width: 450px;
  transform-style: preserve-3d;
}

.login-card-3d {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 32px;
  padding: 3rem;
  position: relative;
  transform-style: preserve-3d;
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.8),
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
  animation: cardFloat 8s ease-in-out infinite;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.glass-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.08) 50%, 
    rgba(14, 165, 233, 0.02) 100%);
  border-radius: 32px;
  z-index: -1;
}

@keyframes cardFloat {
  0%, 100% { transform: translateY(0px) rotateX(0deg) rotateY(0deg); }
  25% { transform: translateY(-3px) rotateX(1deg) rotateY(0.5deg); }
  50% { transform: translateY(-1px) rotateX(0deg) rotateY(-0.5deg); }
  75% { transform: translateY(-5px) rotateX(-1deg) rotateY(0.5deg); }
}

/* Enhanced Mobile Brand - IMPROVED CONTRAST */
.mobile-brand {
  display: none;
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
  position: relative;
}

.mobile-logo-3d {
  position: relative;
  width: 90px;
  height: 90px;
  margin: 0 auto 1rem;
  perspective: 300px;
}

.mobile-logo {
  width: 100%;
  height: 100%;
  border-radius: 24px;
  border: 2px solid rgba(14, 165, 233, 0.4);
  transform: translateZ(10px);
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
}

.mobile-logo-shadow {
  position: absolute;
  top: 5px;
  left: 5px;
  width: 100%;
  height: 100%;
  background: rgba(14, 165, 233, 0.15);
  border-radius: 24px;
  transform: translateZ(-10px);
  filter: blur(10px);
}

.mobile-brand h2 {
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.25rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mobile-brand p {
  color: #475569;
  font-size: 0.95rem;
  font-weight: 500;
}

/* Enhanced 3D Form Styles - MAJOR IMPROVEMENTS */
.auth-form {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}

.reset-form {
  animation: slideInRight3D 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideInRight3D {
  from { 
    opacity: 0; 
    transform: translateX(30px) rotateY(-10deg) translateZ(-50px); 
  }
  to { 
    opacity: 1; 
    transform: translateX(0) rotateY(0deg) translateZ(0); 
  }
}

.form-header-3d {
  text-align: center;
  margin-bottom: 2.5rem;
  position: relative;
  transform: translateZ(10px);
}

.header-decoration {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.deco-line {
  width: 40px;
  height: 2px;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  border-radius: 1px;
  box-shadow: 0 0 8px rgba(14, 165, 233, 0.4);
}

.deco-dot {
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, #0ea5e9, #3b82f6);
  border-radius: 50%;
  box-shadow: 0 0 12px rgba(14, 165, 233, 0.6);
  animation: dotPulse 2s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

.back-btn-3d {
  position: absolute;
  left: 0;
  top: 0;
  width: 45px;
  height: 45px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  color: #475569;
  box-shadow: 
    0 4px 15px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transform: translateZ(5px);
  position: relative;
  overflow: hidden;
}

.back-btn-3d:hover {
  background: rgba(14, 165, 233, 0.15);
  transform: translateX(-3px) translateZ(10px);
  box-shadow: 0 8px 25px rgba(14, 165, 233, 0.2);
  border-color: rgba(14, 165, 233, 0.5);
  color: #0f172a;
}

.back-btn-3d svg {
  width: 22px;
  height: 22px;
  z-index: 2;
}

.form-header-3d h3 {
  font-size: 2rem;
  color: #0f172a;
  font-weight: 800;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.form-header-3d p {
  color: #475569;
  font-size: 1.1rem;
  font-weight: 500;
}

.header-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 200px;
  height: 100px;
  background: radial-gradient(ellipse, rgba(14, 165, 233, 0.08) 0%, transparent 70%);
  transform: translateX(-50%) translateY(-50%) translateZ(-20px);
  border-radius: 50%;
  animation: headerGlow 4s ease-in-out infinite;
}

@keyframes headerGlow {
  0%, 100% { opacity: 0.3; transform: translateX(-50%) translateY(-50%) translateZ(-20px) scale(1); }
  50% { opacity: 0.6; transform: translateX(-50%) translateY(-50%) translateZ(-20px) scale(1.1); }
}

.form-3d {
  margin-bottom: 1.5rem;
  transform-style: preserve-3d;
}

/* Enhanced 3D Input Groups - MAJOR CONTRAST IMPROVEMENTS */
.input-group-3d {
  margin-bottom: 1rem;
  transform-style: preserve-3d;
}

.input-wrapper {
  position: relative;
  transform-style: preserve-3d;
}

.input-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9) 0%, rgba(241, 245, 249, 0.95) 100%);
  border-radius: 18px;
  transform: translateZ(-5px);
  transition: all 0.4s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.input-label-3d {
  display: flex;
  align-items: center;
  justify-content: center; /* Center the label content */
  gap: 0.4rem;
  margin-bottom: 1rem;
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
  transform: translateZ(5px);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  text-align: center; /* Additional centering */
}

.input-label-3d-alternative {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.4rem;
  margin-bottom: 1rem;
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
  transform: translateZ(5px);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.input-icon {
  width: 20px; /* Fixed width instead of 50px */
  height: 20px;
  color: #334155;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
  flex-shrink: 0; /* Prevent icon from shrinking */
}

.form-input-3d {
  width: 100%;
  padding: 1.2rem 1.5rem;
  border: 2px solid rgba(71, 85, 105, 0.3);
  border-radius: 18px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  color: #0f172a;
  font-weight: 500;
  box-sizing: border-box;
  position: relative;
  z-index: 2;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateZ(5px);
}

.form-input-3d::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

.form-input-3d:focus {
  outline: none;
  border-color: #0ea5e9;
  background: rgba(255, 255, 255, 1);
  color: #0f172a;
  box-shadow: 
    0 8px 25px rgba(14, 165, 233, 0.15),
    0 0 0 4px rgba(14, 165, 233, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  transform: translateY(-2px) translateZ(10px);
}

.input-focus-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid transparent;
  border-radius: 18px;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6) border-box;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.4s ease;
  transform: translateZ(1px);
}

.form-input-3d:focus + .input-focus-effect {
  opacity: 1;
  animation: focusRipple 0.6s ease-out;
}

@keyframes focusRipple {
  0% { transform: translateZ(1px) scale(0.95); opacity: 0; }
  50% { transform: translateZ(1px) scale(1.02); opacity: 1; }
  100% { transform: translateZ(1px) scale(1); opacity: 1; }
}

.form-input-3d:disabled {
  background-color: rgba(241, 245, 249, 0.9);
  border-color: rgba(203, 213, 225, 0.8);
  color: #64748b;
  cursor: not-allowed;
  opacity: 0.8;
  transform: translateZ(0px);
}

/* Enhanced 3D Alert Messages - IMPROVED CONTRAST */
.alert-3d {
  position: relative;
  margin-bottom: 2rem;
  border-radius: 16px;
  padding: 1.2rem;
  transform: translateZ(5px);
  transform-style: preserve-3d;
  overflow: hidden;
  animation: alertSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.alert-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  position: relative;
  z-index: 2;
  font-size: 0.95rem;
  line-height: 1.5;
  font-weight: 500;
}

.alert-error {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.95);
  border: 1px solid rgba(239, 68, 68, 0.4);
  box-shadow: 
    0 8px 25px rgba(239, 68, 68, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.alert-success {
  color: #047857;
  background: rgba(220, 252, 231, 0.95);
  border: 1px solid rgba(16, 185, 129, 0.4);
  box-shadow: 
    0 8px 25px rgba(16, 185, 129, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.alert-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 18px;
  opacity: 0.4;
  transform: translateZ(-5px);
  filter: blur(6px);
  animation: alertGlow 2s ease-in-out infinite alternate;
}

.error-glow {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.15));
}

.success-glow {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(5, 150, 105, 0.15));
}

@keyframes alertSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(-20px) translateZ(-10px) rotateX(-10deg); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) translateZ(5px) rotateX(0deg); 
  }
}

@keyframes alertGlow {
  0% { opacity: 0.4; transform: translateZ(-5px) scale(1); }
  100% { opacity: 0.7; transform: translateZ(-5px) scale(1.02); }
}

.alert-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  margin-top: 2px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

/* Enhanced 3D Buttons - MAJOR CONTRAST IMPROVEMENTS */
.submit-btn-3d {
  width: 100%;
  padding: 1.4rem;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 50%, #1e40af 100%);
  color: #ffffff;
  border: none;
  border-radius: 18px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 12px 35px rgba(14, 165, 233, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  transform: translateZ(10px);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  position: relative;
  z-index: 3;
}

.btn-glow {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -10px;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  border-radius: 22px;
  opacity: 0;
  transition: opacity 0.4s ease;
  transform: translateZ(-5px);
  filter: blur(12px);
}

.btn-ripple {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transform: translateX(-100%) translateZ(1px);
  transition: transform 0.6s ease;
  border-radius: 18px;
}

.submit-btn-3d:hover:not(:disabled) {
  background: linear-gradient(135deg, #0284c7 0%, #2563eb 50%, #1d4ed8 100%);
  transform: translateY(-4px) translateZ(15px) rotateX(2deg);
  box-shadow: 
    0 20px 50px rgba(14, 165, 233, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.submit-btn-3d:hover:not(:disabled) .btn-glow {
  opacity: 1;
  animation: btnGlowPulse 1.5s ease-in-out infinite;
}

.submit-btn-3d:hover:not(:disabled) .btn-ripple {
  transform: translateX(100%) translateZ(1px);
}

@keyframes btnGlowPulse {
  0%, 100% { opacity: 1; transform: translateZ(-5px) scale(1); }
  50% { opacity: 0.8; transform: translateZ(-5px) scale(1.05); }
}

.submit-btn-3d:active:not(:disabled) {
  transform: translateY(-1px) translateZ(8px) rotateX(1deg);
}

.submit-btn-3d:disabled {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  color: #ffffff;
  cursor: not-allowed;
  transform: translateZ(5px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  opacity: 0.7;
}

.reset-btn {
  background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%);
}

.reset-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #047857 0%, #065f46 50%, #064e3b 100%);
}

.reset-btn .btn-glow {
  background: linear-gradient(135deg, #059669, #047857);
}

.reset-glow {
  background: linear-gradient(135deg, #059669, #047857);
}

.btn-icon {
  width: 22px;
  height: 22px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.submit-btn-3d:hover .btn-icon {
  transform: translateX(3px) rotateZ(5deg);
}

.spinner-3d {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid #ffffff;
  border-radius: 50%;
  animation: spin3D 1s linear infinite;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

@keyframes spin3D {
  0% { transform: rotate(0deg) rotateY(0deg); }
  100% { transform: rotate(360deg) rotateY(180deg); }
}

/* Enhanced 3D Link Button - IMPROVED CONTRAST */
.link-btn-3d {
  display: block;
  width: 100%;
  text-align: center;
  background: none;
  border: none;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  padding: 1rem;
  margin-top: 1.5rem;
  border-radius: 14px;
  position: relative;
  color: #475569;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateZ(5px);
  overflow: hidden;
}

.link-btn-3d span {
  position: relative;
  z-index: 2;
}

.link-underline {
  position: absolute;
  bottom: 8px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  transform: translateX(-50%);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 1px;
  box-shadow: 0 0 8px rgba(14, 165, 233, 0.4);
}

.link-btn-3d:hover {
  color: #0ea5e9;
  background: rgba(14, 165, 233, 0.08);
  transform: translateY(-2px) translateZ(8px);
  text-shadow: 0 0 8px rgba(14, 165, 233, 0.2);
}

.link-btn-3d:hover .link-underline {
  width: 60%;
}

/* Enhanced Security Notice - IMPROVED CONTRAST */
.security-notice-3d {
  margin-top: 2rem;
  position: relative;
  border-radius: 18px;
  overflow: hidden;
  transform: translateZ(5px);
  transition: transform 0.4s ease;
}

.security-notice-3d:hover {
  transform: translateZ(10px) rotateX(1deg);
}

.notice-content {
  padding: 1.5rem;
  background: rgba(219, 234, 254, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 18px;
  display: flex;
  gap: 1.2rem;
  align-items: flex-start;
  position: relative;
  z-index: 2;
  box-shadow: 
    0 8px 25px rgba(14, 165, 233, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.notice-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(59, 130, 246, 0.1));
  border-radius: 20px;
  opacity: 0.5;
  transform: translateZ(-5px);
  filter: blur(10px);
  animation: noticeGlow 3s ease-in-out infinite alternate;
}

@keyframes noticeGlow {
  0% { opacity: 0.5; transform: translateZ(-5px) scale(1); }
  100% { opacity: 0.8; transform: translateZ(-5px) scale(1.02); }
}

.notice-icon {
  width: 26px;
  height: 26px;
  color: #0ea5e9;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(14, 165, 233, 0.3));
  animation: iconGlow 2s ease-in-out infinite alternate;
}

@keyframes iconGlow {
  0% { filter: drop-shadow(0 2px 4px rgba(14, 165, 233, 0.3)); }
  100% { filter: drop-shadow(0 4px 8px rgba(14, 165, 233, 0.5)); }
}

.notice-content h4 {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.6rem;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.notice-content p {
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.6;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
}

/* Enhanced Responsive Styles */
@media (max-width: 1024px) {
  .main-container {
    flex-direction: column;
  }
  
  .branding-section {
    flex: 0 0 45vh;
    padding: 2rem 1.5rem;
    transform: translateZ(0);
  }
  
  .brand-title {
    font-size: 2.5rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
  }
  
  .card-content {
    padding: 1.5rem;
  }
  
  .login-section {
    flex: 1;
    padding: 1.5rem;
  }
  
  .login-card-3d {
    padding: 2.5rem;
  }
}

@media (max-width: 768px) {
  .input-label-3d {
    justify-content: center;
    text-align: center;
  }

  .branding-section {
    display: none;
  }
  
  .mobile-brand {
    display: block;
  }
  
  .login-section {
    flex: 1;
    padding: 1rem;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    perspective: 800px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 50%, #cbd5e1 100%);
  }
  
  .login-card-3d {
    margin: 0;
    padding: 2.5rem 2rem;
    border-radius: 28px;
    max-width: 100%;
    width: 100%;
    animation: cardFloatMobile 6s ease-in-out infinite;
    background: rgba(255, 255, 255, 0.98);
    border: 1px solid rgba(203, 213, 225, 0.6);
  }

  @keyframes cardFloatMobile {
    0%, 100% { transform: translateY(0px) rotateX(0deg); }
    50% { transform: translateY(-2px) rotateX(0.5deg); }
  }
  
  .form-header-3d h3 {
    font-size: 1.8rem;
    color: #0f172a;
  }
  
  .form-header-3d p {
    font-size: 1rem;
    color: #475569;
  }

  .input-group-3d {
    margin-bottom: 1.8rem;
  }

  .form-input-3d {
    padding: 1.3rem;
    background: rgba(255, 255, 255, 0.98);
    border: 2px solid rgba(71, 85, 105, 0.25);
    color: #0f172a;
  }

  .input-label-3d {
    color: #0f172a;
  }
}

@media (max-width: 480px) {
  .login-section {
    padding: 0.75rem;
    perspective: 600px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  }
  
  .login-card-3d {
    padding: 2rem 1.5rem;
    border-radius: 24px;
    margin: 0;
    background: rgba(255, 255, 255, 0.98);
  }
  
  .mobile-brand {
    margin-bottom: 1.8rem;
    padding-bottom: 1.8rem;
  }
  
  .mobile-logo-3d {
    width: 80px;
    height: 80px;
  }
  
  .mobile-brand h2 {
    font-size: 1.5rem;
    color: #0f172a;
  }

  .mobile-brand p {
    color: #475569;
  }
  
  .form-header-3d h3 {
    font-size: 1.6rem;
    color: #0f172a;
  }

  .form-header-3d p {
    color: #475569;
  }
  
  .form-input-3d {
    padding: 1.2rem;
    font-size: 16px; /* Prevents zoom on iOS */
    background: rgba(255, 255, 255, 0.98);
    color: #0f172a;
  }
  
  .submit-btn-3d {
    padding: 1.3rem;
    font-size: 1rem;
  }
  
  .security-notice-3d {
    margin-top: 1.8rem;
  }

  .notice-content {
    padding: 1.2rem;
    background: rgba(219, 234, 254, 0.95);
  }
  
  .notice-content h4 {
    font-size: 0.95rem;
    color: #0f172a;
  }
  
  .notice-content p {
    font-size: 0.85rem;
    color: #334155;
  }

  .input-label-3d {
    justify-content: center;
    text-align: center;
    font-size: 0.95rem;
  }
  
  .input-icon {
    width: 18px;
    height: 18px;
  }

  .input-label-3d {
    color: #0f172a;
  }

  .input-icon {
    color: #475569;
  }

  /* Reduce 3D effects on small screens for performance */
  .feature-card-3d:hover {
    transform: translateY(-4px) scale(1.01);
  }

  .login-card-3d {
    animation: cardFloatMobile 8s ease-in-out infinite;
  }
}

/* Enhanced Landscape orientation on mobile */
@media (max-height: 600px) and (orientation: landscape) {
  .login-section {
    align-items: flex-start;
    padding-top: 1rem;
    padding-bottom: 1rem;
    perspective: 500px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  }
  
  .mobile-brand {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
  }
  
  .mobile-logo-3d {
    width: 60px;
    height: 60px;
    margin-bottom: 0.8rem;
  }
  
  .mobile-brand h2 {
    font-size: 1.3rem;
    margin-bottom: 0.2rem;
    color: #0f172a;
  }
  
  .mobile-brand p {
    font-size: 0.85rem;
    color: #475569;
  }
  
  .form-header-3d {
    margin-bottom: 1.8rem;
  }

  .form-header-3d h3 {
    color: #0f172a;
  }

  .form-header-3d p {
    color: #475569;
  }
  
  .input-group-3d {
    margin-bottom: 1.2rem;
  }
  
  .security-notice-3d {
    margin-top: 1.2rem;
  }

  .login-card-3d {
    animation: none; /* Disable animation in landscape for performance */
    background: rgba(255, 255, 255, 0.98);
  }

  .input-label-3d {
    color: #0f172a;
  }

  .form-input-3d {
    background: rgba(255, 255, 255, 0.98);
    color: #0f172a;
  }

  .notice-content {
    background: rgba(219, 234, 254, 0.95);
  }

  .notice-content h4 {
    color: #0f172a;
  }

  .notice-content p {
    color: #334155;
  }
}

/* Performance optimizations for high DPI displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .main-logo,
  .mobile-logo {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }

  /* Reduce particle count on high DPI for performance */
  .particle:nth-child(n+11) {
    display: none;
  }
}

/* Reduced motion for accessibility */
@media (prefers-reduced-motion: reduce) {
  .fiber-strand,
  .light-pulse,
  .particle,
  .logo-container,
  .logo-glow-3d,
  .spinner-3d,
  .login-card-3d,
  .dotPulse,
  .titleShimmer,
  .underlineGlow,
  .cardGlowPulse,
  .iconFloat,
  .headerGlow,
  .btnGlowPulse,
  .alertGlow,
  .noticeGlow,
  .iconGlow {
    animation: none;
  }
  
  .form-input-3d:focus,
  .submit-btn-3d:hover:not(:disabled),
  .feature-card-3d:hover,
  .login-card-3d,
  .back-btn-3d:hover,
  .link-btn-3d:hover,
  .security-notice-3d:hover {
    transform: none;
  }
  
  .reset-form {
    animation: none;
  }

  /* Keep minimal transform for 3D feel without motion */
  .login-card-3d {
    transform: translateZ(5px);
  }

  .form-input-3d:focus {
    transform: translateZ(8px);
  }

  .submit-btn-3d {
    transform: translateZ(10px);
  }
}

/* Enhanced Focus styles for accessibility - IMPROVED CONTRAST */
.submit-btn-3d:focus-visible,
.back-btn-3d:focus-visible,
.link-btn-3d:focus-visible {
  outline: 3px solid #0ea5e9;
  outline-offset: 3px;
  box-shadow: 
    0 0 0 6px rgba(14, 165, 233, 0.2),
    0 12px 35px rgba(14, 165, 233, 0.4);
}

.form-input-3d:focus-visible {
  outline: 3px solid #0ea5e9;
  outline-offset: -3px;
}

/* Enhanced Print styles */
@media print {
  .fiber-bg,
  .floating-particles,
  .glass-overlay,
  .logo-glow-3d,
  .card-glow,
  .btn-glow,
  .alert-glow,
  .notice-glow,
  .header-glow {
    display: none;
  }
  
  .ftth-login-wrapper {
    background: white;
  }
  
  .branding-section {
    background: white;
    color: black;
    transform: none;
  }

  .login-card-3d,
  .feature-card-3d,
  .submit-btn-3d,
  .back-btn-3d {
    transform: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

/* Dark mode support - IMPROVED CONTRAST */
@media (prefers-color-scheme: dark) {
  .login-section {
    background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
  }

  .login-card-3d {
    background: rgba(30, 41, 59, 0.98);
    color: #ffffff;
    border: 1px solid rgba(71, 85, 105, 0.4);
  }

  .form-input-3d {
    background: rgba(51, 65, 85, 0.95);
    border-color: rgba(71, 85, 105, 0.6);
    color: #f8fafc;
  }

  .form-input-3d::placeholder {
    color: #94a3b8;
  }

 .input-label-3d {
    color: #020202; /* Light color for dark mode */
  }

  .input-icon {
    color: #000000; /* Light icon for dark mode */
  }

  .form-header-3d h3 {
    color: #f8fafc;
  }

  .form-header-3d p {
    color: #cbd5e1;
  }

  .mobile-brand h2 {
    color: #f8fafc;
  }

  .mobile-brand p {
    color: #cbd5e1;
  }

  .notice-content {
    background: rgba(51, 65, 85, 0.95);
    border-color: rgba(14, 165, 233, 0.4);
  }

  .notice-content h4 {
    color: #f8fafc;
  }

  .notice-content p {
    color: #cbd5e1;
  }

  .link-btn-3d {
    color: #cbd5e1;
  }

  .link-btn-3d:hover {
    color: #0ea5e9;
  }

  .alert-error {
    background: rgba(127, 29, 29, 0.2);
    color: #fca5a5;
    border-color: rgba(239, 68, 68, 0.4);
  }

  .alert-success {
    background: rgba(6, 78, 59, 0.2);
    color: #86efac;
    border-color: rgba(16, 185, 129, 0.4);
  }
}

/* Hardware acceleration for better performance */
.login-card-3d,
.feature-card-3d,
.submit-btn-3d,
.form-input-3d,
.back-btn-3d,
.logo-container {
  will-change: transform;
  transform-style: preserve-3d;
}

/* Custom scrollbar for webkit browsers */
.branding-section::-webkit-scrollbar {
  width: 6px;
}

.branding-section::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.branding-section::-webkit-scrollbar-thumb {
  background: rgba(14, 165, 233, 0.3);
  border-radius: 3px;
}

.branding-section::-webkit-scrollbar-thumb:hover {
  background: rgba(14, 165, 233, 0.5);
}
</style>

