<template>
  <v-dialog v-model="dialog" max-width="1400" persistent scrollable>
    <v-card v-if="ticketData" class="ticket-detail-dialog">
      <!-- Enhanced Header -->
      <v-card-title class="pa-6 pb-4 gradient-header">
        <div class="d-flex align-center justify-space-between w-100 flex-wrap gap-3">
          <div class="d-flex align-center">
            <v-avatar size="48" color="primary" class="me-4">
              <v-icon size="28" color="white">mdi-ticket-confirmation</v-icon>
            </v-avatar>
            <div>
              <div class="text-h5 text-md-h4 font-weight-bold text-white mb-1">
                {{ ticketData.ticket_number }}
              </div>
              <div class="text-caption text-md-body-2 text-white opacity-90">
                Ticket ID: #{{ ticketData.id }}
              </div>
            </div>
          </div>
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip
              :color="getStatusColor(ticketData.status)"
              variant="flat"
              size="default"
              class="status-chip"
            >
              <v-icon start size="small">{{ getStatusIcon(ticketData.status) }}</v-icon>
              {{ formatStatus(ticketData.status) }}
            </v-chip>
            <v-chip
              :color="getPriorityColor(ticketData.priority)"
              variant="elevated"
              size="default"
              class="priority-chip"
            >
              <v-icon start size="small">{{ getPriorityIcon(ticketData.priority) }}</v-icon>
              {{ formatPriority(ticketData.priority) }}
            </v-chip>
          </div>
        </div>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4 pa-md-6">
        <v-row>
          <!-- Left Column - Ticket Information -->
          <v-col cols="12" lg="8">
            <!-- Basic Information -->
            <v-card variant="elevated" class="mb-4 mb-md-6 info-card" elevation="2">
              <v-card-title class="pa-3 pa-md-4 pb-2 info-header">
                <div class="d-flex align-center">
                  <v-avatar color="primary" size="36" class="me-3">
                    <v-icon color="white" size="20">mdi-information-outline</v-icon>
                  </v-avatar>
                  <div>
                    <div class="text-subtitle-1 text-md-h6 font-weight-bold">Ticket Information</div>
                    <div class="text-caption text-medium-emphasis">Basic details about this ticket</div>
                  </div>
                </div>
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3 pa-md-4">
                <v-row>
                  <v-col cols="12" class="mb-3 mb-md-4">
                    <div class="field-label">Title</div>
                    <div class="field-value title-value">{{ ticketData.title }}</div>
                  </v-col>
                  <v-col cols="12" class="mb-3 mb-md-4">
                    <div class="field-label">Description</div>
                    <div class="field-value description-value">{{ ticketData.description }}</div>
                  </v-col>
                  <v-col cols="12" md="6" class="mb-3">
                    <div class="field-label">Category</div>
                    <v-chip
                      size="default"
                      color="info"
                      variant="tonal"
                      prepend-icon="mdi-tag-outline"
                      class="category-chip"
                    >
                      {{ formatCategory(ticketData.category) }}
                    </v-chip>
                  </v-col>
                  <v-col cols="12" md="6" class="mb-3">
                    <div class="field-label">Assigned To</div>
                    <div v-if="ticketData.assigned_user" class="d-flex align-center">
                      <v-avatar size="32" color="success" class="me-3">
                        <v-icon color="white" size="18">mdi-account</v-icon>
                      </v-avatar>
                      <div>
                        <div class="font-weight-medium">{{ ticketData.assigned_user.name }}</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ ticketData.assigned_user.role?.name || 'No role' }}
                        </div>
                      </div>
                    </div>
                    <div v-else class="d-flex align-center">
                      <v-chip
                        size="default"
                        color="grey"
                        variant="tonal"
                        prepend-icon="mdi-account-question"
                      >
                        Unassigned
                      </v-chip>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Customer Information -->
            <v-card v-if="ticketData.pelanggan" variant="outlined" class="mb-4 info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-5">
                <v-icon class="me-2" color="info">mdi-account-outline</v-icon>
                Customer Information
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <v-row dense>
                  <v-col cols="12" sm="6">
                    <div class="text-caption text-medium-emphasis mb-1">Name</div>
                    <div class="font-weight-medium">{{ ticketData.pelanggan.nama }}</div>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <div class="text-caption text-medium-emphasis mb-1">Address</div>
                    <div>{{ ticketData.pelanggan.alamat }}</div>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Phone</div>
                    <div>{{ ticketData.pelanggan.no_telp || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Email</div>
                    <div class="text-truncate">{{ ticketData.pelanggan.email || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Brand</div>
                    <v-chip
                      v-if="ticketData.pelanggan.harga_layanan?.brand"
                      size="small"
                      color="primary"
                      variant="outlined"
                    >
                      {{ ticketData.pelanggan.harga_layanan.brand }}
                    </v-chip>
                    <div v-else>-</div>
                  </v-col>
                  <v-col cols="6" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Block</div>
                    <div>{{ ticketData.pelanggan.blok || '-' }}</div>
                  </v-col>
                  <v-col cols="6" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Unit</div>
                    <div>{{ ticketData.pelanggan.unit || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <div class="text-caption text-medium-emphasis mb-1">Service</div>
                    <div>{{ ticketData.pelanggan.layanan || '-' }}</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Technical Data -->
            <v-card v-if="ticketData.data_teknis" variant="outlined" class="mb-4 info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-5">
                <v-icon class="me-2" color="success">mdi-network-outline</v-icon>
                Technical Data
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <v-row dense>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">IP Address</div>
                    <div class="font-weight-mono text-body-2">{{ ticketData.data_teknis.ip_pelanggan || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">PPPoE Password</div>
                    <div class="font-weight-mono text-body-2">{{ ticketData.data_teknis.password_pppoe || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">VLAN ID</div>
                    <div class="text-body-2">{{ ticketData.data_teknis.id_vlan || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">OLT</div>
                    <div class="text-body-2">{{ ticketData.data_teknis.olt || ticketData.data_teknis.olt_custom || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">PON</div>
                    <div class="text-body-2">{{ ticketData.data_teknis.pon || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">ODP Port</div>
                    <div class="text-body-2">{{ ticketData.data_teknis.port_odp || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">ONU Power</div>
                    <div class="text-body-2">{{ ticketData.data_teknis.onu_power || '-' }} dBm</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">Serial Number</div>
                    <div class="font-weight-mono text-body-2">{{ ticketData.data_teknis.sn || '-' }}</div>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">Customer ID</div>
                    <div class="font-weight-mono text-body-2">{{ ticketData.data_teknis?.id_pelanggan || `CUST-${ticketData.pelanggan?.id}` || '-' }}</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Evidence Section -->
            <v-card v-if="ticketData.evidence" variant="outlined" class="mb-4 info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-primary-lighten-5">
                <v-icon class="me-2" color="primary">mdi-attachment</v-icon>
                Evidence Files
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <div class="evidence-container">
                  <div v-for="(fileUrl, index) in parseEvidenceFiles(ticketData.evidence)" :key="index" class="evidence-item mb-2">
                    <v-btn
                      :href="fileUrl"
                      target="_blank"
                      variant="text"
                      color="primary"
                      size="small"
                      class="text-left"
                    >
                      <v-icon start>{{ getFileIconFromUrl(fileUrl) }}</v-icon>
                      <span class="truncate-text">{{ getFileNameFromUrl(fileUrl) }}</span>
                    </v-btn>
                  </div>
                </div>
              </v-card-text>
            </v-card>

            <!-- Resolution Information -->
            <v-card v-if="ticketData.status === 'resolved' || ticketData.status === 'closed'" variant="outlined" class="mb-4 info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-success-lighten-5">
                <v-icon class="me-2" color="success">mdi-check-circle-outline</v-icon>
                Resolution Information
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <v-row dense>
                  <v-col cols="12" sm="6">
                    <div class="text-caption text-medium-emphasis mb-1">Resolved At</div>
                    <div>{{ formatDateTime(ticketData.resolved_at) }}</div>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <div class="text-caption text-medium-emphasis mb-1">Total Downtime</div>
                    <div>
                      <v-chip
                        v-if="ticketData.total_downtime_minutes && ticketData.total_downtime_minutes > 0"
                        :color="getDowntimeColor(ticketData.total_downtime_minutes)"
                        size="small"
                        variant="flat"
                      >
                        {{ formatDowntime(ticketData.total_downtime_minutes) }}
                      </v-chip>
                      <div v-else>-</div>
                    </div>
                  </v-col>
                  <v-col cols="12" v-if="ticketData.resolution_notes">
                    <div class="text-caption text-medium-emphasis mb-1">Resolution Notes</div>
                    <div class="text-body-2 whitespace-pre-wrap">{{ ticketData.resolution_notes }}</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Right Column - Information Cards -->
          <v-col cols="12" lg="4">
            <!-- Downtime Information -->
            <v-card variant="outlined" class="mb-4 info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-error-lighten-5">
                <v-icon class="me-2" color="error">mdi-clock-alert-outline</v-icon>
                Downtime Information
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <v-row dense>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Downtime Start</div>
                    <div class="d-flex align-center">
                      <v-icon class="me-2" color="info" size="small">mdi-clock-start</v-icon>
                      <span class="text-body-2">{{ formatDateTime(ticketData.created_at) }}</span>
                    </div>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Downtime End</div>
                    <div v-if="ticketData.downtime_end" class="d-flex align-center">
                      <v-icon class="me-2" color="success" size="small">mdi-clock-end</v-icon>
                      <span class="text-body-2">{{ formatDateTime(ticketData.downtime_end) }}</span>
                    </div>
                    <div v-else-if="isTicketResolvedOrClosed()" class="d-flex align-center">
                      <v-icon class="me-2" color="success" size="small">mdi-check-circle</v-icon>
                      <span class="text-body-2">{{ formatDateTime(ticketData.resolved_at || ticketData.updated_at) }}</span>
                    </div>
                    <div v-else class="d-flex align-center">
                      <v-icon class="me-2" color="error" size="small">mdi-clock-fast</v-icon>
                      <span class="text-error font-weight-medium text-body-2">Still in progress</span>
                    </div>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Total Downtime</div>
                    <div v-if="!isTicketResolvedOrClosed() && ticketData.created_at" class="mb-2">
                      <v-chip
                        color="error"
                        size="small"
                        variant="flat"
                        class="downtime-chip animate-pulse"
                      >
                        <v-icon start size="x-small">mdi-clock-fast</v-icon>
                        <span class="timer-display">{{ liveDowntimeTimer }}</span>
                      </v-chip>
                    </div>
                    <div v-else-if="ticketData.total_downtime_minutes && ticketData.total_downtime_minutes > 0">
                      <v-chip
                        :color="getDowntimeColor(ticketData.total_downtime_minutes)"
                        size="small"
                        variant="flat"
                      >
                        <v-icon start size="x-small">mdi-check-circle</v-icon>
                        {{ formatDowntime(ticketData.total_downtime_minutes) }}
                      </v-chip>
                    </div>
                    <div v-else class="text-medium-emphasis text-body-2">No downtime recorded</div>
                  </v-col>
                </v-row>

                <!-- Timer Board -->
                <v-divider class="my-3"></v-divider>
                <div class="timer-board">
                  <div class="text-caption text-medium-emphasis mb-2">Live Timer</div>
                  <v-card
                    :color="isTicketResolvedOrClosed() ? 'grey-lighten-4' : 'error-lighten-5'"
                    variant="flat"
                    class="pa-3 text-center"
                  >
                    <div v-if="!isTicketResolvedOrClosed() && ticketData.created_at" class="timer-display">
                      <v-icon
                        :color="getTimerColor()"
                        size="large"
                        class="mb-2 animate-pulse"
                      >
                        mdi-timer-sand
                      </v-icon>
                      <div class="timer-text text-h6 text-md-h5 font-weight-bold" :class="'text-' + getTimerColor()">
                        {{ liveTimer }}
                      </div>
                      <div class="timer-label text-caption text-medium-emphasis mt-1">
                        {{ getTimerLabel() }}
                      </div>
                    </div>
                    <div v-else-if="isTicketResolvedOrClosed()" class="timer-display">
                      <v-icon color="success" size="large" class="mb-2">
                        mdi-timer-off
                      </v-icon>
                      <div class="text-subtitle-1 text-md-h6 font-weight-medium text-success">
                        Completed
                      </div>
                      <div class="text-caption text-medium-emphasis mt-1">
                        Total: {{ ticketData.total_downtime_minutes ? formatDowntime(ticketData.total_downtime_minutes) : 'N/A' }}
                      </div>
                    </div>
                    <div v-else class="text-center text-medium-emphasis">
                      <v-icon size="large" class="mb-2">mdi-clock-remove</v-icon>
                      <div class="text-body-2">No timer available</div>
                    </div>
                  </v-card>
                </div>
              </v-card-text>
            </v-card>

            <!-- Ticket Metadata -->
            <v-card variant="outlined" class="info-card" elevation="1">
              <v-card-title class="text-subtitle-1 pa-3 bg-info-lighten-5">
                <v-icon class="me-2" color="info">mdi-information</v-icon>
                Ticket Information
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-3">
                <v-row dense>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Created At</div>
                    <div class="text-body-2">{{ formatDateTime(ticketData.created_at) }}</div>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Last Updated</div>
                    <div class="text-body-2">{{ formatDateTime(ticketData.updated_at) }}</div>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">Customer Notified</div>
                    <v-chip
                      :color="ticketData.customer_notified ? 'success' : 'warning'"
                      size="small"
                      variant="flat"
                    >
                      {{ ticketData.customer_notified ? 'Yes' : 'No' }}
                    </v-chip>
                  </v-col>
                  <v-col cols="12" v-if="ticketData.last_customer_contact">
                    <div class="text-caption text-medium-emphasis mb-1">Last Customer Contact</div>
                    <div class="text-body-2">{{ formatDateTime(ticketData.last_customer_contact) }}</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-3 pa-md-4">
        <v-spacer></v-spacer>
        <!-- Hapus Ticket Button - dengan validasi status -->
        <v-btn
          v-if="canDeleteTicket"
          variant="elevated"
          color="error"
          @click="showDeleteConfirmation"
          size="default"
          class="delete-ticket-btn"
        >
          <v-icon start>mdi-delete</v-icon>
          Hapus Ticket
        </v-btn>

        <!-- Close Button -->
        <v-btn
          variant="elevated"
          color="primary"
          @click="closeDialog"
          size="default"
        >
          <v-icon start>mdi-close</v-icon>
          Close
        </v-btn>
      </v-card-actions>

      <!-- Delete Confirmation Dialog -->
      <v-dialog v-model="showDeleteDialog" max-width="500px" persistent>
        <v-card class="delete-dialog-card">
          <v-card-title class="pa-4 pb-2 delete-header">
            <v-icon class="me-2" color="error">mdi-delete-alert</v-icon>
            <span class="text-h6 font-weight-bold">Konfirmasi Hapus Ticket</span>
          </v-card-title>

          <v-divider></v-divider>

          <v-card-text class="pa-4">
            <div v-if="isTicketResolvedOrClosed()" class="delete-message">
              <p class="text-body-1 mb-4">
                Apakah Anda yakin ingin menghapus ticket <strong>{{ ticketData?.ticket_number }}</strong>?
              </p>
              <p class="text-medium-emphasis text-caption mb-4">
                Status ticket ini adalah <strong>{{ formatStatus(ticketData?.status) }}</strong>
              </p>
            </div>
            <div v-else class="delete-warning">
              <div class="d-flex align-center mb-4">
                <v-avatar color="warning" size="48" class="me-3">
                  <v-icon size="24" color="white">mdi-alert-circle</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold text-warning-darken-1">Ticket Belum Selesai</div>
                  <p class="text-body-2 mb-0">
                    Status: <strong>{{ formatStatus(ticketData?.status) }}</strong>
                  </p>
                </div>
              </div>
              <p class="text-body-1 mb-4">
                Ticket ini belum dapat dihapus karena statusnya belum "Resolved" atau "Closed".
                Silakan selesaikan ticket terlebih dahulu.
              </p>
            </div>

            <v-divider class="my-4"></v-divider>

            <div v-if="isTicketResolvedOrClosed()" class="d-flex justify-center gap-3">
              <v-btn
                color="error"
                variant="flat"
                @click="confirmDelete"
                :loading="deleting"
                class="delete-btn"
              >
                <v-icon start>mdi-delete</v-icon>
                Ya, Hapus
              </v-btn>
              <v-btn
                variant="outlined"
                @click="showDeleteDialog = false"
              >
                Batal
              </v-btn>
            </div>
            <div v-else class="d-flex justify-center gap-3">
              <v-btn
                color="grey"
                variant="flat"
                @click="showDeleteDialog = false"
              >
                Mengerti
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-dialog>
    </v-card>

    <!-- Loading State -->
    <v-card v-else>
      <v-card-text class="pa-8 text-center">
        <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
        <div class="mt-4 text-h6">Loading ticket details...</div>
      </v-card-text>
    </v-card>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="bottom"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import apiClient from '@/services/api'

// Props
interface Props {
  modelValue: boolean
  ticketId?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  ticketId: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'updated': []
}>()

// State
const ticketData = ref<any>(null)
const loading = ref(false)
const liveTimer = ref('00:00:00')
const liveDowntimeTimer = ref('00:00:00')
const timerInterval = ref<NodeJS.Timeout | null>(null)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleting = ref(false)

// Snackbar state
const snackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' | 'warning' })

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canDeleteTicket = computed(() => {
  return ticketData.value?.status === 'resolved' || ticketData.value?.status === 'closed'
})

// Methods
const fetchTicket = async () => {
  if (!props.ticketId) return

  loading.value = true
  try {
    const response = await apiClient.get(`/trouble-tickets/${props.ticketId}`)
    ticketData.value = response.data
  } catch (error) {
    console.error('Failed to fetch ticket:', error)
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  ticketData.value = null
}

const showDeleteConfirmation = () => {
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!props.ticketId || !ticketData.value) return

  deleting.value = true
  try {
    await apiClient.delete(`/trouble-tickets/${props.ticketId}`)
    showSnackbar('Ticket berhasil dihapus', 'success')
    closeDialog()
    emit('updated')
  } catch (error) {
    console.error('Failed to delete ticket:', error)
    showSnackbar('Gagal menghapus ticket', 'error')
  } finally {
    deleting.value = false
  }
}

const isTicketResolvedOrClosed = () => {
  return ticketData.value?.status === 'resolved' ||
         ticketData.value?.status === 'closed' ||
         ticketData.value?.status === 'cancelled'
}

const startLiveTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
  }

  if (!isTicketResolvedOrClosed() && ticketData.value?.created_at) {
    timerInterval.value = setInterval(() => {
      updateLiveTimer()
    }, 1000)
  }
}

const stopLiveTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

const updateLiveTimer = () => {
  if (!ticketData.value?.created_at || isTicketResolvedOrClosed()) {
    stopLiveTimer()
    return
  }

  const start = new Date(ticketData.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()

  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)

  const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`

  liveTimer.value = timeString
  liveDowntimeTimer.value = timeString
}

const getTimerColor = () => {
  if (!ticketData.value?.created_at) return 'grey'

  const start = new Date(ticketData.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const getTimerLabel = () => {
  if (!ticketData.value?.created_at) return 'No start time'

  const start = new Date(ticketData.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'Running normally'
  if (minutes < 240) return 'Attention needed'
  if (minutes < 1440) return 'Critical downtime'
  return 'Severe downtime'
}

// Utility functions
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'warning',
    in_progress: 'info',
    pending_customer: 'orange',
    pending_vendor: 'purple',
    resolved: 'success',
    closed: 'grey',
    cancelled: 'error'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    open: 'mdi-clock-outline',
    in_progress: 'mdi-progress-clock',
    pending_customer: 'mdi-account-clock',
    pending_vendor: 'mdi-truck-fast',
    resolved: 'mdi-check-circle',
    closed: 'mdi-archive',
    cancelled: 'mdi-cancel'
  }
  return icons[status] || 'mdi-help-circle'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'error',
    critical: 'red-darken-1'
  }
  return colors[priority] || 'grey'
}

const getPriorityIcon = (priority: string) => {
  const icons: Record<string, string> = {
    low: 'mdi-arrow-down',
    medium: 'mdi-minus',
    high: 'mdi-arrow-up',
    critical: 'mdi-fire'
  }
  return icons[priority] || 'mdi-help-circle'
}

const getDowntimeColor = (minutes: number) => {
  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const formatStatus = (status: string) => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatPriority = (priority: string) => {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

const formatCategory = (category: string) => {
  return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('id-ID', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDowntime = (minutes: number) => {
  if (minutes < 60) return `${minutes} minutes`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours} hour${hours > 1 ? 's' : ''}`
  return `${hours}h ${remainingMinutes}m`
}

const showSnackbar = (text: string, color: 'success' | 'error' | 'warning') => {
  snackbar.value = { show: true, text, color }
}

// Evidence-related methods
const parseEvidenceFiles = (evidenceJson: string) => {
  try {
    const evidenceArray = JSON.parse(evidenceJson)
    if (Array.isArray(evidenceArray)) {
      return evidenceArray
    }
    return []
  } catch (e) {
    console.error('Failed to parse evidence JSON:', e)
    return []
  }
}

const getFileNameFromUrl = (url: string) => {
  try {
    const path = new URL(url, window.location.origin).pathname
    return path.split('/').pop() || url
  } catch (e) {
    return url
  }
}

const getFileIconFromUrl = (url: string) => {
  const extension = url.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, string> = {
    'jpg': 'mdi-file-image',
    'jpeg': 'mdi-file-image',
    'png': 'mdi-file-image',
    'gif': 'mdi-file-image',
    'webp': 'mdi-file-image',
    'pdf': 'mdi-file-pdf',
    'doc': 'mdi-file-word',
    'docx': 'mdi-file-word',
    'xls': 'mdi-file-excel',
    'xlsx': 'mdi-file-excel',
    'txt': 'mdi-file-document',
    'zip': 'mdi-file-zip',
    'rar': 'mdi-file',
    'mp4': 'mdi-file-video',
    'avi': 'mdi-file-video',
    'mov': 'mdi-file-video',
    'mp3': 'mdi-file-music'
  }
  return iconMap[extension || ''] || 'mdi-file'
}

// Watchers
watch(() => props.ticketId, (newId) => {
  if (newId && props.modelValue) {
    fetchTicket()
  }
})

watch(() => props.modelValue, (newValue) => {
  if (newValue && props.ticketId) {
    fetchTicket()
  } else if (!newValue) {
    stopLiveTimer()
  }
})

watch(() => ticketData.value, (newData) => {
  if (newData && props.modelValue) {
    updateLiveTimer()
    if (!isTicketResolvedOrClosed()) {
      startLiveTimer()
    } else {
      stopLiveTimer()
    }
  }
}, { deep: true })

// Lifecycle hooks
onUnmounted(() => {
  stopLiveTimer()
})
</script>

<style scoped>
/* Gradient Header */
.gradient-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
}

/* Card Styling */
.info-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.info-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Field Styling */
.field-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.field-value {
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  line-height: 1.5;
}

.title-value {
  font-weight: 600;
  font-size: 1.1rem;
}

.description-value {
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Chips */
.status-chip,
.priority-chip,
.category-chip {
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* Monospace Font */
.font-weight-mono {
  font-family: 'Roboto Mono', monospace;
}

/* Timer Styling */
.timer-board {
  margin-top: 16px;
}

.timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.timer-text {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.05em;
}

.timer-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.downtime-chip {
  font-family: 'Roboto Mono', monospace;
  font-weight: 500;
  min-width: 100px;
}

/* Animations */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Whitespace */
.whitespace-pre-wrap {
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Background Colors for Headers */
.bg-grey-lighten-5 {
  background-color: rgb(var(--v-theme-surface-light));
}

.bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.05);
}

.bg-error-lighten-5 {
  background-color: rgba(var(--v-theme-error), 0.05);
}

.bg-info-lighten-5 {
  background-color: rgba(var(--v-theme-info), 0.05);
}

/* Dark Theme Adjustments */
.v-theme--dark .bg-grey-lighten-5 {
  background-color: rgba(255, 255, 255, 0.05);
}

.v-theme--dark .bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.1);
}

.v-theme--dark .bg-error-lighten-5 {
  background-color: rgba(var(--v-theme-error), 0.1);
}

.v-theme--dark .bg-info-lighten-5 {
  background-color: rgba(var(--v-theme-info), 0.1);
}

.v-theme--dark .info-card {
  border-color: rgba(255, 255, 255, 0.1);
}

/* Responsive Adjustments */
@media (max-width: 960px) {
  .gradient-header {
    padding: 16px !important;
  }
  
  .text-h4 {
    font-size: 1.5rem !important;
  }
  
  .timer-text {
    font-size: 1.25rem !important;
  }
}

@media (max-width: 600px) {
  .gradient-header {
    padding: 12px !important;
  }
  
  .status-chip,
  .priority-chip {
    font-size: 0.75rem;
    height: 24px;
  }
  
  .field-label {
    font-size: 0.7rem;
  }
  
  .field-value {
    font-size: 0.875rem;
  }
  
  .title-value {
    font-size: 1rem;
  }
  
  .timer-text {
    font-size: 1.1rem !important;
  }
  
  .info-card {
    margin-bottom: 12px !important;
  }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* Text Truncate */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Elevation on Hover */
.info-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.info-card:hover {
  transform: translateY(-2px);
}

/* Delete Dialog Styling */
.delete-dialog-card {
  border-radius: 12px;
  overflow: hidden;
}

.delete-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-error), 0.1) 0%, rgba(var(--v-theme-error), 0.05) 100%);
}

.delete-message {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.delete-warning {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.delete-ticket-btn {
  transition: all 0.3s ease;
}

.delete-ticket-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-error), 0.3);
}

.delete-btn {
  transition: all 0.3s ease;
}

.delete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-error), 0.3);
}

/* Print Styles */
@media print {
  .v-card-actions {
    display: none !important;
  }

  .gradient-header {
    background: white !important;
    color: black !important;
  }

  .info-card {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

/* Evidence Section Styles */
.evidence-container {
  max-height: 200px;
  overflow-y: auto;
  padding: 4px 0;
}

.evidence-item {
  border-left: 3px solid rgba(var(--v-theme-primary), 0.3);
  padding-left: 8px;
}

.truncate-text {
  max-width: calc(100% - 50px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>