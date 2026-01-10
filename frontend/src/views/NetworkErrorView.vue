<template>
  <v-container fluid class="fill-height">
    <v-row justify="center" align="center" class="pa-4">
      <v-col cols="12" md="8" lg="6" xl="4">
        <!-- Main Network Error Card -->
        <v-card
          class="elevation-12 rounded-xl"
          :class="isDark ? 'bg-gray-900' : 'bg-white'"
        >
          <v-card-text class="pa-8 text-center">
            <!-- Error Icon with Animation -->
            <div class="mb-6">
              <v-icon
                size="120"
                color="error"
                class="mb-4 pulse-animation"
              >
                mdi-server-network-off
              </v-icon>
            </div>

            <!-- Error Status -->
            <h1
              class="text-h2 font-weight-bold mb-2 error-text"
              :class="isDark ? 'text-red-lighten-1' : 'text-red-darken-1'"
            >
              {{ errorStatus }}
            </h1>

            <!-- Error Title -->
            <h2 class="text-h5 font-weight-medium mb-3">
              {{ errorTitle }}
            </h2>

            <!-- Error Description -->
            <p class="text-body-1 text-medium-emphasis mb-6">
              {{ errorMessage }}
            </p>

            <!-- Technical Details (Admin Only) -->
            <v-expansion-panels class="mb-6" v-if="showTechnicalDetails && showAdminPanel">
              <v-expansion-panel>
                <v-expansion-panel-title class="text-caption">
                  <v-icon class="mr-2">mdi-shield-key-outline</v-icon>
                  Detail Teknis (Admin)
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left">
                  <div class="text-caption font-mono">
                    <div class="mb-2">
                      <strong>URL:</strong> {{ errorDetails?.url || 'Tidak diketahui' }}
                    </div>
                    <div class="mb-2">
                      <strong>Method:</strong> {{ errorDetails?.method || 'Tidak diketahui' }}
                    </div>
                    <div class="mb-2">
                      <strong>Status:</strong> {{ errorDetails?.status || 'Tidak diketahui' }}
                    </div>
                    <div class="mb-2">
                      <strong>Waktu:</strong> {{ currentTime }}
                    </div>
                    <div class="mb-2">
                      <strong>Error ID:</strong> {{ errorId }}
                    </div>
                    <div v-if="errorDetails?.message" class="mb-2">
                      <strong>Message:</strong> {{ errorDetails.message }}
                    </div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <!-- Actions -->
            <div class="d-flex flex-wrap gap-4 justify-center">
              <!-- Retry Button -->
              <v-btn
                color="primary"
                size="large"
                prepend-icon="mdi-refresh"
                class="text-none me-4"
                @click="retryConnection"
                :loading="isRetrying"
              >
                {{ isRetrying ? 'Menghubungkan...' : 'Coba Lagi' }}
              </v-btn>

              <!-- Refresh Page -->
              <v-btn
                variant="outlined"
                size="large"
                prepend-icon="mdi-refresh-circle"
                class="text-none"
                @click="refreshPage"
              >
                Refresh Halaman
              </v-btn>

              <!-- Report Issue -->
              <v-btn
                variant="text"
                size="large"
                prepend-icon="mdi-bug-outline"
                class="text-none"
                @click="reportIssue"
              >
                Laporkan Masalah
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Network Tips Card -->
        <v-card
          class="mt-4 rounded-xl elevation-4"
          :class="isDark ? 'bg-gray-800' : 'bg-grey-lighten-5'"
        >
          <v-card-text class="pa-4">
            <h3 class="text-h6 font-weight-medium mb-3">
              <v-icon class="mr-2">mdi-lightbulb-outline</v-icon>
              Solusi Cepat:
            </h3>

            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="small" class="mr-2">mdi-wifi-check</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Periksa koneksi internet Anda
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="small" class="mr-2">mdi-clock-outline</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Tunggu beberapa saat lalu coba lagi
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="small" class="mr-2">mdi-router-wireless</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Restart router/modem jika perlu
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="small" class="mr-2">mdi-phone</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Hubungi IT Support jika masalah berlanjut
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        </v-col>
    </v-row>

    <!-- Report Issue Dialog -->
    <v-dialog v-model="showReportDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-bug</v-icon>
          Laporkan Masalah Jaringan
        </v-card-title>

        <v-card-text>
          <v-textarea
            v-model="issueReport"
            label="Deskripsi Masalah"
            placeholder="Jelaskan masalah yang Anda alami..."
            rows="4"
            auto-grow
            variant="outlined"
          ></v-textarea>

          <v-checkbox
            v-model="includeTechnicalDetails"
            label="Sertakan detail teknis dalam laporan"
            hide-details
          ></v-checkbox>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showReportDialog = false">
            Batal
          </v-btn>
          <v-btn color="primary" @click="submitReport">
            Kirim Laporan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { getEncryptedToken } from '@/utils/crypto'

interface ErrorDetails {
  url?: string
  method?: string
  status?: number
  message?: string
}

const router = useRouter()
const theme = useTheme()

// Props untuk menerima error details
const props = defineProps<{
  errorStatus?: number
  errorType?: 'network' | 'server' | 'timeout' | 'unknown'
  errorDetails?: ErrorDetails
}>()

// State
const showReportDialog = ref(false)
const issueReport = ref('')
const includeTechnicalDetails = ref(false)
const isRetrying = ref(false)
const errorId = ref('')

// Computed
const isDark = computed(() => theme.global.name.value === 'dark')

const errorTitle = computed(() => {
  switch (props.errorType) {
    case 'network':
      return 'Koneksi Jaringan Gagal'
    case 'server':
      return 'Server Tidak Responsif'
    case 'timeout':
      return 'Koneksi Timeout'
    default:
      return 'Terjadi Kesalahan Koneksi'
  }
})

const errorMessage = computed(() => {
  switch (props.errorType) {
    case 'network':
      return 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda dan coba lagi.'
    case 'server':
      return 'Server sedang tidak responsif atau sedang dalam perbaikan. Silakan coba lagi nanti.'
    case 'timeout':
      return 'Server terlalu lama merespons. Silakan refresh halaman atau coba lagi.'
    default:
      return 'Terjadi masalah dengan koneksi ke server. Silakan coba lagi atau hubungi IT Support.'
  }
})

const showTechnicalDetails = computed(() => {
  return props.errorDetails && Object.keys(props.errorDetails).length > 0
})

const showAdminPanel = computed(() => {
  // Check if user is authenticated (has valid token)
  try {
    const token = getEncryptedToken('access_token');
    return !!token;
  } catch {
    return false;
  }
})

const currentTime = computed(() => {
  return new Date().toLocaleString('id-ID', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Jakarta'
  })
})

// Methods
const retryConnection = async () => {
  isRetrying.value = true
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000)

  try {
    // Try to ping the backend
    const response = await fetch('/api/health', {
      method: 'GET',
      signal: controller.signal
    })

    if (response.ok) {
      // Redirect to dashboard
      setTimeout(() => {
        router.push('/dashboard')
      }, 1000)
    }
  } catch (error) {
    console.error('Retry failed:', error)
  } finally {
    clearTimeout(timeoutId)
    isRetrying.value = false
  }
}

const refreshPage = () => {
  window.location.reload()
}

const reportIssue = () => {
  showReportDialog.value = true
}

const submitReport = async () => {
  try {
    const reportData = {
      issue: issueReport.value,
      errorType: props.errorType || 'unknown',
      errorStatus: props.errorStatus || 0,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      errorId: errorId.value,
      errorDetails: includeTechnicalDetails.value ? props.errorDetails : null
    }

    // Try to send report, but don't fail if network is down
    try {
      await fetch('/api/error-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData)
      })
    } catch (networkError) {
      // Store report locally for later sending
      localStorage.setItem(`network_error_report_${Date.now()}`, JSON.stringify(reportData))
    }

    alert('Terima kasih! Laporan Anda telah tersimpan dan akan dikirim saat koneksi pulih.')
    showReportDialog.value = false
    issueReport.value = ''
    includeTechnicalDetails.value = false
  } catch (error) {
    console.error('Failed to submit report:', error)
    alert('Gagal menyimpan laporan. Silakan hubungi IT Support langsung.')
  }
}

// Lifecycle
onMounted(() => {
  errorId.value = 'NET-' + Date.now().toString(36).toUpperCase()
})
</script>

<style scoped>
.v-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Pulse animation for error icon */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.pulse-animation {
  animation: pulse 3s ease-in-out infinite;
}

/* Error text styling */
.error-text {
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Dark theme adjustments */
.v-theme--dark .v-container {
  background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
}

.v-theme--dark .pulse-animation {
  animation: pulse 3s ease-in-out infinite;
}
</style>