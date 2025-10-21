<template>
  <v-dialog v-model="dialog" max-width="800" scrollable>
    <v-card>
      <v-card-title class="pa-4 pb-2">
        <v-icon class="me-2" color="info">mdi-history</v-icon>
        Ticket History - {{ ticketNumber }}
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4" style="max-height: 600px;">
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="status_history">Status History</v-tab>
          <v-tab value="action_taken">Action Taken</v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- Status History Tab -->
          <v-window-item value="status_history">
            <div v-if="loading && activeTab === 'status_history'" class="text-center py-8">
              <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
              <div class="mt-4">Loading status history...</div>
            </div>

            <v-timeline v-else-if="statusHistory.length > 0" density="compact">
              <v-timeline-item
                v-for="item in statusHistory"
                :key="item.id"
                :dot-color="getStatusColor(item.new_status)"
                size="small"
              >
                <template v-slot:icon>
                  <v-icon size="16">{{ getStatusIcon(item.new_status) }}</v-icon>
                </template>

                <div class="d-flex align-center justify-space-between mb-1">
                  <div class="font-weight-medium">
                    {{ formatStatus(item.new_status) }}
                    <span v-if="item.old_status" class="text-medium-emphasis">
                      (from {{ formatStatus(item.old_status) }})
                    </span>
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ formatDateTime(item.created_at) }}
                  </div>
                </div>

                <div v-if="item.changed_user" class="text-caption text-medium-emphasis mb-2">
                  by {{ item.changed_user.name }}
                </div>

                <div v-if="item.notes" class="text-body-2 bg-grey-lighten-4 pa-2 rounded">
                  {{ item.notes }}
                </div>
              </v-timeline-item>
            </v-timeline>

            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" color="grey-lighten-1">mdi-history</v-icon>
              <div class="mt-2">No status history available</div>
            </div>
          </v-window-item>

          <!-- Action Taken Tab -->
          <v-window-item value="action_taken">
            <div v-if="loading && activeTab === 'action_taken'" class="text-center py-8">
              <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
              <div class="mt-4">Loading action history...</div>
            </div>

            <v-timeline v-else-if="actionHistory.length > 0" density="compact">
              <v-timeline-item
                v-for="item in actionHistory"
                :key="item.id"
                dot-color="primary"
                size="small"
              >
                <template v-slot:icon>
                  <v-icon size="16">mdi-cog-transfer</v-icon>
                </template>

                <div class="d-flex align-center justify-space-between mb-1">
                  <div class="font-weight-medium">Action Taken</div>
                  <div class="text-caption text-medium-emphasis">
                    {{ formatDateTime(item.created_at) }}
                  </div>
                </div>

                <div v-if="item.taken_user" class="text-caption text-medium-emphasis mb-2">
                  by {{ item.taken_user.name }}
                </div>

                <!-- Action Description -->
                <div v-if="item.action_description" class="mb-2">
                  <div class="text-caption text-medium-emphasis">Action Description:</div>
                  <div class="text-body-2 bg-grey-lighten-4 pa-2 rounded">{{ item.action_description }}</div>
                </div>

                <!-- Summary Problem -->
                <div v-if="item.summary_problem" class="mb-2">
                  <div class="text-caption text-medium-emphasis">Summary Problem:</div>
                  <div class="text-body-2 bg-blue-lighten-5 pa-2 rounded">{{ item.summary_problem }}</div>
                </div>

                <!-- Summary Action -->
                <div v-if="item.summary_action" class="mb-2">
                  <div class="text-caption text-medium-emphasis">Summary Action:</div>
                  <div class="text-body-2 bg-green-lighten-5 pa-2 rounded">{{ item.summary_action }}</div>
                </div>

                <!-- Evidence -->
                <div v-if="item.evidence" class="mb-2">
                  <div class="text-caption text-medium-emphasis">Evidence:</div>
                  <div class="pa-2 rounded">
                    <v-img 
                      :src="item.evidence" 
                      max-height="200" 
                      cover 
                      class="rounded border"
                      @click="viewEvidence(item.evidence)"
                      style="cursor: pointer;"
                    />
                  </div>
                </div>

                <!-- Notes -->
                <div v-if="item.notes" class="mb-2">
                  <div class="text-caption text-medium-emphasis">Notes:</div>
                  <div class="text-body-2 bg-grey-lighten-4 pa-2 rounded">{{ item.notes }}</div>
                </div>
              </v-timeline-item>
            </v-timeline>

            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" color="grey-lighten-1">mdi-history</v-icon>
              <div class="mt-2">No action history available</div>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
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
}>()

// State
const loading = ref(false)
const statusHistory = ref<any[]>([])
const actionHistory = ref<any[]>([])
const ticketNumber = ref('')
const activeTab = ref('action_taken')  // Default to action taken

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Methods
const fetchHistory = async () => {
  if (!props.ticketId) return

  loading.value = true
  try {
    // Fetch both status history and action history
    const [statusResponse, actionResponse, ticketResponse] = await Promise.all([
      apiClient.get(`/trouble-tickets/${props.ticketId}/history`),
      apiClient.get(`/trouble-tickets/${props.ticketId}/actions`),
      apiClient.get(`/trouble-tickets/${props.ticketId}`)
    ])

    statusHistory.value = statusResponse.data
    actionHistory.value = actionResponse.data
    ticketNumber.value = ticketResponse.data.ticket_number
  } catch (error) {
    console.error('Failed to fetch history:', error)
    statusHistory.value = []
    actionHistory.value = []
    
    // Fallback to ticket ID if can't fetch details
    ticketNumber.value = `#${props.ticketId}`
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  statusHistory.value = []
  actionHistory.value = []
  ticketNumber.value = ''
  activeTab.value = 'action_taken'
}



const viewEvidence = (evidenceUrl: string) => {
  window.open(evidenceUrl, '_blank')
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

const formatStatus = (status: string) => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Watchers
watch(() => props.ticketId, (newId) => {
  if (newId && props.modelValue) {
    fetchHistory()
  }
})

watch(() => props.modelValue, (newValue) => {
  if (newValue && props.ticketId) {
    fetchHistory()
  }
})
</script>