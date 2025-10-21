<template>
  <div class="trouble-ticket-detail-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="goBack"
            class="back-btn"
            size="large"
          ></v-btn>
          <v-avatar color="primary" size="56" class="header-avatar">
            <v-icon size="28">mdi-ticket-confirmation-outline</v-icon>
          </v-avatar>
          <div class="header-info">
            <h1 class="page-title">Ticket Detail</h1>
            <p class="page-subtitle">{{ ticket?.ticket_number || 'Loading...' }}</p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="header-actions">
          <v-btn
            color="success"
            prepend-icon="mdi-cog-transfer"
            @click="goToTicketAction"
            :disabled="loading"
            variant="flat"
            size="large"
            class="action-btn"
            elevation="2"
          >
            <span class="btn-text">Manage Actions</span>
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-refresh"
            @click="refreshData"
            :loading="loading"
            variant="outlined"
            size="large"
            class="refresh-btn"
          >
            <span class="btn-text">Refresh</span>
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular
        indeterminate
        color="primary"
        size="64"
        width="6"
      ></v-progress-circular>
      <p class="loading-text">Loading ticket details...</p>
    </div>

    <!-- Error State -->
    <v-card v-else-if="error" class="error-card" elevation="0">
      <v-card-text class="error-content">
        <v-icon size="64" color="error" class="mb-4">mdi-alert-circle-outline</v-icon>
        <h3 class="error-title">Error Loading Ticket</h3>
        <p class="error-message">{{ error }}</p>
        <v-btn 
          color="primary" 
          @click="refreshData" 
          class="mt-4"
          variant="flat"
          size="large"
        >
          <v-icon start>mdi-refresh</v-icon>
          Try Again
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Ticket Details -->
    <div v-else-if="ticket" class="ticket-content">
      <!-- Main Information Card -->
      <v-card class="detail-card info-card mb-4 mb-md-6" elevation="2">
        <v-card-title class="card-title">
          <div class="title-wrapper">
            <v-icon class="title-icon" color="primary">mdi-information-outline</v-icon>
            <span>Ticket Information</span>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="card-content">
          <v-row>
            <!-- Ticket Number -->
            <v-col cols="12" sm="6" md="4" lg="3">
              <div class="detail-item">
                <label class="detail-label">Ticket Number</label>
                <v-chip 
                  color="primary" 
                  variant="outlined" 
                  prepend-icon="mdi-ticket"
                  size="default"
                  class="detail-chip"
                >
                  {{ ticket.ticket_number }}
                </v-chip>
              </div>
            </v-col>

            <!-- Status -->
            <v-col cols="12" sm="6" md="4" lg="3">
              <div class="detail-item">
                <label class="detail-label">Status</label>
                <v-chip
                  :color="getStatusColor(ticket.status)"
                  variant="flat"
                  class="status-chip"
                  size="default"
                >
                  <v-icon start size="small">{{ getStatusIcon(ticket.status) }}</v-icon>
                  {{ formatStatus(ticket.status) }}
                </v-chip>
              </div>
            </v-col>

            <!-- Priority -->
            <v-col cols="12" sm="6" md="4" lg="3">
              <div class="detail-item">
                <label class="detail-label">Priority</label>
                <v-chip
                  :color="getPriorityColor(ticket.priority)"
                  variant="outlined"
                  class="priority-chip"
                  size="default"
                >
                  <v-icon start size="small">{{ getPriorityIcon(ticket.priority) }}</v-icon>
                  {{ formatPriority(ticket.priority) }}
                </v-chip>
              </div>
            </v-col>

            <!-- Category -->
            <v-col cols="12" sm="6" md="4" lg="3">
              <div class="detail-item">
                <label class="detail-label">Category</label>
                <v-chip 
                  color="info" 
                  variant="tonal" 
                  prepend-icon="mdi-tag-outline"
                  size="default"
                  class="detail-chip"
                >
                  {{ formatCategory(ticket.category) }}
                </v-chip>
              </div>
            </v-col>

            <!-- Title & Description -->
            <v-col cols="12">
              <div class="detail-item">
                <label class="detail-label">Title</label>
                <div class="title-content">
                  <h3 class="ticket-title">{{ ticket.title }}</h3>
                  <p v-if="ticket.description" class="ticket-description">{{ ticket.description }}</p>
                </div>
              </div>
            </v-col>

            <!-- Created Date -->
            <v-col cols="12" sm="6" md="4">
              <div class="detail-item">
                <label class="detail-label">Created Date</label>
                <div class="date-info">
                  <div class="date-main">
                    <v-icon size="small" class="me-2">mdi-calendar</v-icon>
                    {{ formatDate(ticket.created_at) }}
                  </div>
                  <div class="date-time">
                    <v-icon size="small" class="me-2">mdi-clock-outline</v-icon>
                    {{ formatTime(ticket.created_at) }}
                  </div>
                </div>
              </div>
            </v-col>

            <!-- Assigned To -->
            <v-col cols="12" sm="6" md="4" v-if="ticket.assigned_user">
              <div class="detail-item">
                <label class="detail-label">Assigned To</label>
                <div class="assigned-user">
                  <v-avatar size="36" color="success" class="me-2">
                    <v-icon size="18">mdi-account</v-icon>
                  </v-avatar>
                  <div class="user-info">
                    <span class="user-name">{{ ticket.assigned_user.name }}</span>
                  </div>
                </div>
              </div>
            </v-col>

            <!-- Total Downtime -->
            <v-col cols="12" sm="6" md="4" v-if="ticket.total_downtime_minutes && ticket.total_downtime_minutes > 0">
              <div class="detail-item">
                <label class="detail-label">Total Downtime</label>
                <v-chip
                  :color="getDowntimeColorFromMinutes(ticket.total_downtime_minutes)"
                  variant="flat"
                  class="downtime-chip"
                  size="default"
                >
                  <v-icon start size="small">mdi-clock-alert</v-icon>
                  {{ formatDowntime(ticket.total_downtime_minutes) }}
                </v-chip>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Customer Information Card -->
      <v-card v-if="ticket.pelanggan" class="detail-card customer-card mb-4 mb-md-6" elevation="2">
        <v-card-title class="card-title">
          <div class="title-wrapper">
            <v-icon class="title-icon" color="info">mdi-account-outline</v-icon>
            <span>Customer Information</span>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="card-content">
          <div class="customer-info">
            <div class="customer-header">
              <v-avatar size="56" color="primary" class="customer-avatar">
                <v-icon size="28">mdi-account</v-icon>
              </v-avatar>
              <div class="customer-main-info">
                <h3 class="customer-name">{{ ticket.pelanggan.nama }}</h3>
                <p class="customer-address">
                  <v-icon size="small" class="me-1">mdi-map-marker</v-icon>
                  {{ ticket.pelanggan.alamat }}
                </p>
              </div>
            </div>

            <v-divider class="my-4"></v-divider>

            <div class="customer-details">
              <v-row dense>
                <v-col cols="12" sm="6" md="4" v-if="ticket.data_teknis?.ip_pelanggan">
                  <div class="detail-badge">
                    <v-icon size="20" color="primary" class="me-2">mdi-ip-network</v-icon>
                    <div>
                      <div class="badge-label">IP Address</div>
                      <div class="badge-value">{{ ticket.data_teknis.ip_pelanggan }}</div>
                    </div>
                  </div>
                </v-col>
                
                <v-col cols="12" sm="6" md="4" v-if="ticket.data_teknis?.id_pelanggan && !isIpAddress(ticket.data_teknis.id_pelanggan)">
                  <div class="detail-badge">
                    <v-icon size="20" color="success" class="me-2">mdi-identifier</v-icon>
                    <div>
                      <div class="badge-label">Customer ID</div>
                      <div class="badge-value">{{ ticket.data_teknis.id_pelanggan }}</div>
                    </div>
                  </div>
                </v-col>
                
                <v-col cols="12" sm="6" md="4" v-if="ticket.pelanggan.harga_layanan?.brand">
                  <div class="detail-badge">
                    <v-icon size="20" color="warning" class="me-2">mdi-domain</v-icon>
                    <div>
                      <div class="badge-label">Brand</div>
                      <div class="badge-value">{{ ticket.pelanggan.harga_layanan.brand }}</div>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Status Timeline -->
      <v-card class="detail-card timeline-card" elevation="2">
        <v-card-title class="card-title">
          <div class="title-wrapper">
            <v-icon class="title-icon" color="secondary">mdi-timeline-outline</v-icon>
            <span>Status Timeline</span>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="card-content">
          <div class="timeline-container">
            <!-- Ticket Created -->
            <div class="timeline-item">
              <div class="timeline-dot created">
                <v-icon size="14" color="white">mdi-plus</v-icon>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-content">
                <h4 class="timeline-title">Ticket Created</h4>
                <p class="timeline-text">
                  <v-icon size="small" class="me-1">mdi-calendar</v-icon>
                  {{ formatDate(ticket.created_at) }} 
                  <span class="mx-2">•</span>
                  <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                  {{ formatTime(ticket.created_at) }}
                </p>
              </div>
            </div>

            <!-- Status Updated -->
            <div v-if="ticket.status !== 'open'" class="timeline-item">
              <div class="timeline-dot" :class="ticket.status">
                <v-icon size="14" color="white">{{ getStatusIcon(ticket.status) }}</v-icon>
              </div>
              <div class="timeline-line" v-if="ticket.status === 'resolved' || ticket.status === 'closed'"></div>
              <div class="timeline-content">
                <h4 class="timeline-title">Status Updated to {{ formatStatus(ticket.status) }}</h4>
                <p class="timeline-text">
                  <v-icon size="small" class="me-1">mdi-calendar</v-icon>
                  {{ formatDate(ticket.updated_at) }} 
                  <span class="mx-2">•</span>
                  <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                  {{ formatTime(ticket.updated_at) }}
                </p>
              </div>
            </div>

            <!-- Resolution Completed -->
            <div v-if="ticket.status === 'resolved' || ticket.status === 'closed'" class="timeline-item">
              <div class="timeline-dot resolved">
                <v-icon size="14" color="white">mdi-check</v-icon>
              </div>
              <div class="timeline-content">
                <h4 class="timeline-title">Resolution Completed</h4>
                <p v-if="ticket.total_downtime_minutes" class="timeline-text">
                  <v-icon size="small" class="me-1">mdi-clock-alert</v-icon>
                  Total downtime: {{ formatDowntime(ticket.total_downtime_minutes) }}
                </p>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/services/api'

const route = useRoute()
const router = useRouter()

// Types
interface TroubleTicket {
  id: number
  ticket_number: string
  title: string
  description: string
  status: string
  priority: string
  category: string
  pelanggan?: {
    id: number
    nama: string
    alamat: string
    harga_layanan?: {
      brand: string
    }
  }
  data_teknis?: {
    id_pelanggan: string
    ip_pelanggan?: string
  }
  assigned_user?: {
    id: number
    name: string
  }
  total_downtime_minutes?: number
  created_at: string
  updated_at: string
}

// State
const loading = ref(false)
const error = ref<string | null>(null)
const ticket = ref<TroubleTicket | null>(null)
const refreshInterval = ref<NodeJS.Timeout | null>(null)

// Methods
const fetchTicketDetail = async () => {
  const ticketId = route.params.id
  if (!ticketId || typeof ticketId !== 'string') {
    error.value = 'Invalid ticket ID'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get(`/trouble-tickets/${ticketId}`, {
      params: { include_relations: true }
    })
    ticket.value = response.data
  } catch (err: any) {
    console.error('Failed to fetch ticket detail:', err)
    error.value = err.response?.data?.detail || 'Failed to load ticket details'
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchTicketDetail()
}

const goBack = () => {
  router.go(-1)
}

const goToTicketAction = () => {
  if (ticket.value) {
    router.push({ name: 'TicketAction', params: { id: ticket.value.id } })
  }
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

const getDowntimeColorFromMinutes = (minutes: number) => {
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

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString('id-ID', {
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

const isIpAddress = (str: string) => {
  const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipPattern.test(str)
}

// Lifecycle
onMounted(() => {
  fetchTicketDetail()
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
})
</script>

<style scoped>
/* ========================================
   CONTAINER & BASE STYLES
   ======================================== */
.trouble-ticket-detail-container {
  padding: 20px;
  background-color: rgb(var(--v-theme-background));
  min-height: 100vh;
}

/* ========================================
   HEADER SECTION
   ======================================== */
.page-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.08) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%);
  border-radius: 20px;
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.back-btn {
  flex-shrink: 0;
}

.header-avatar {
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 4px 0 0 0;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.action-btn,
.refresh-btn {
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: none;
}

.btn-text {
  display: inline;
}

/* ========================================
   LOADING & ERROR STATES
   ======================================== */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 20px;
}

.loading-text {
  font-size: 1.1rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  font-weight: 500;
}

.error-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-error), 0.2);
  margin-bottom: 24px;
}

.error-content {
  padding: 60px 32px;
  text-align: center;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-error));
  margin: 16px 0 8px 0;
}

.error-message {
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  font-size: 1rem;
}

/* ========================================
   DETAIL CARDS
   ======================================== */
.detail-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.detail-card:hover {
  box-shadow: 0 8px 24px rgba(var(--v-theme-shadow), 0.12);
  transform: translateY(-2px);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  padding: 20px 24px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 24px;
}

.card-content {
  padding: 24px;
}

/* ========================================
   DETAIL ITEMS
   ======================================== */
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 4px;
}

.detail-chip {
  font-weight: 600;
  letter-spacing: 0.3px;
}

.status-chip,
.priority-chip {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.downtime-chip {
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
}

/* Title Content */
.title-content {
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  border-left: 4px solid rgb(var(--v-theme-primary));
}

.ticket-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.ticket-description {
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  line-height: 1.6;
  font-size: 0.95rem;
}

/* Date Info */
.date-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 10px;
}

.date-main,
.date-time {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9rem;
}

.date-time {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.85rem;
}

/* Assigned User */
.assigned-user {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(var(--v-theme-success), 0.08);
  border-radius: 10px;
  gap: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.95rem;
}

/* ========================================
   CUSTOMER INFORMATION
   ======================================== */
.customer-info {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.customer-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 12px;
}

.customer-avatar {
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.customer-main-info {
  flex: 1;
  min-width: 0;
}

.customer-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 6px 0;
}

.customer-address {
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 0.95rem;
}

.customer-details {
  padding: 0;
}

.detail-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.detail-badge:hover {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  transform: translateX(4px);
}

.badge-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.badge-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-family: 'Roboto Mono', monospace;
}

/* ========================================
   TIMELINE
   ======================================== */
.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  padding: 8px 0;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  padding: 16px 0;
}

.timeline-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 2;
  border: 3px solid rgb(var(--v-theme-surface));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: relative;
}

.timeline-line {
  position: absolute;
  left: 15px;
  top: 48px;
  bottom: -16px;
  width: 2px;
  background: linear-gradient(180deg, 
    rgba(var(--v-theme-primary), 0.3) 0%, 
    rgba(var(--v-theme-primary), 0.1) 100%);
  z-index: 1;
}

.timeline-dot.created {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.timeline-dot.open {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.timeline-dot.in_progress {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.timeline-dot.resolved {
  background: linear-gradient(135deg, #10b981, #059669);
}

.timeline-dot.closed {
  background: linear-gradient(135deg, #6b7280, #4b5563);
}

.timeline-content {
  flex: 1;
  padding: 8px 0;
}

.timeline-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 6px 0;
}

.timeline-text {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

/* ========================================
   ANIMATIONS
   ======================================== */
.detail-card {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.detail-card:nth-child(1) { animation-delay: 0.1s; }
.detail-card:nth-child(2) { animation-delay: 0.2s; }
.detail-card:nth-child(3) { animation-delay: 0.3s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========================================
   DARK THEME
   ======================================== */
.v-theme--dark .page-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.12) 0%,
    rgba(var(--v-theme-secondary), 0.08) 100%);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .detail-card {
  border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .card-title {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.v-theme--dark .title-content {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.v-theme--dark .customer-header {
  background: rgba(var(--v-theme-primary), 0.1);
}

.v-theme--dark .detail-badge {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.v-theme--dark .detail-badge:hover {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

/* ========================================
   RESPONSIVE DESIGN
   ======================================== */

/* Tablet (768px - 959px) */
@media (max-width: 959px) {
  .trouble-ticket-detail-container {
    padding: 16px;
  }

  .page-header {
    padding: 20px 24px;
    margin-bottom: 20px;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .header-left {
    width: 100%;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.9rem;
  }

  .card-content {
    padding: 20px;
  }
}

/* Mobile (600px - 767px) */
@media (max-width: 767px) {
  .trouble-ticket-detail-container {
    padding: 12px;
  }

  .page-header {
    padding: 16px 20px;
    border-radius: 16px;
  }

  .header-left {
    gap: 12px;
  }

  .header-avatar {
    width: 48px !important;
    height: 48px !important;
  }

  .page-title {
    font-size: 1.35rem;
  }

  .page-subtitle {
    font-size: 0.85rem;
  }

  .header-actions {
    flex-direction: column;
    gap: 8px;
  }

  .action-btn,
  .refresh-btn {
    width: 100%;
  }

  .detail-card {
    border-radius: 16px;
    margin-bottom: 16px !important;
  }

  .card-title {
    font-size: 1.1rem;
    padding: 16px 20px;
  }

  .title-icon {
    font-size: 20px;
  }

  .card-content {
    padding: 16px;
  }

  .ticket-title {
    font-size: 1.1rem;
  }

  .customer-header {
    flex-direction: row;
    text-align: left;
  }

  .customer-avatar {
    width: 48px !important;
    height: 48px !important;
  }

  .customer-name {
    font-size: 1.1rem;
  }

  .timeline-dot {
    width: 28px;
    height: 28px;
  }

  .timeline-line {
    left: 13px;
  }

  .timeline-title {
    font-size: 0.95rem;
  }

  .timeline-text {
    font-size: 0.85rem;
  }
}

/* Small Mobile (< 600px) */
@media (max-width: 599px) {
  .btn-text {
    display: none;
  }

  .action-btn .v-icon,
  .refresh-btn .v-icon {
    margin: 0 !important;
  }

  .header-actions {
    flex-direction: row;
    gap: 8px;
  }

  .action-btn,
  .refresh-btn {
    width: auto;
    flex: 1;
  }

  .detail-badge {
    padding: 12px;
  }

  .badge-label {
    font-size: 0.7rem;
  }

  .badge-value {
    font-size: 0.85rem;
  }
}

/* Extra Small Mobile (< 400px) */
@media (max-width: 399px) {
  .page-header {
    padding: 12px 16px;
  }

  .header-left {
    gap: 8px;
  }

  .back-btn {
    width: 40px !important;
    height: 40px !important;
  }

  .header-avatar {
    width: 40px !important;
    height: 40px !important;
  }

  .page-title {
    font-size: 1.2rem;
  }

  .page-subtitle {
    font-size: 0.8rem;
  }

  .card-title {
    font-size: 1rem;
    padding: 14px 16px;
  }

  .card-content {
    padding: 14px;
  }
}

/* Print Styles */
@media print {
  .page-header,
  .header-actions,
  .back-btn {
    display: none !important;
  }

  .detail-card {
    break-inside: avoid;
    page-break-inside: avoid;
    box-shadow: none !important;
    border: 1px solid #ddd !important;
  }

  .trouble-ticket-detail-container {
    padding: 0;
  }
}
</style>