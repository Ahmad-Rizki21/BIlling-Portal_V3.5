<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title class="pa-4 pb-2">
        <v-icon class="me-2" color="error">mdi-clock-alert-outline</v-icon>
        Update Downtime Tracking
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <v-form ref="formRef" v-model="valid">
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="formData.downtime_start"
                label="Downtime Start"
                type="datetime-local"
                :rules="[v => !!v || 'Start time is required']"
                hint="When the service issue began"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model="formData.downtime_end"
                label="Downtime End"
                type="datetime-local"
                :rules="[
                  v => !v || !formData.downtime_start || new Date(v) >= new Date(formData.downtime_start) || 'End time must be after start time'
                ]"
                hint="When the service issue was resolved (leave empty if still ongoing)"
                persistent-hint
                clearable
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Current downtime display -->
          <v-alert
            v-if="formData.downtime_start"
            type="info"
            variant="tonal"
            class="mt-4"
          >
            <div class="text-subtitle-2 mb-1">Calculated Downtime:</div>
            <div class="font-weight-medium">
              {{ calculateDowntime() }}
            </div>
          </v-alert>

          <!-- Current downtime info -->
          <v-card v-if="currentDowntime" variant="outlined" class="mt-4">
            <v-card-title class="text-subtitle-1 pa-3">
              <v-icon class="me-2" color="info">mdi-information-outline</v-icon>
              Current Downtime
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-3">
              <v-row dense>
                <v-col cols="12">
                  <div class="text-caption text-medium-emphasis">Start</div>
                  <div>{{ formatDateTime(currentDowntime.downtime_start) }}</div>
                </v-col>
                <v-col cols="12">
                  <div class="text-caption text-medium-emphasis">End</div>
                  <div>{{ currentDowntime.downtime_end ? formatDateTime(currentDowntime.downtime_end) : 'Still ongoing' }}</div>
                </v-col>
                <v-col cols="12" v-if="currentDowntime.total_downtime_minutes">
                  <div class="text-caption text-medium-emphasis">Total</div>
                  <v-chip
                    :color="getDowntimeColor(currentDowntime.total_downtime_minutes)"
                    size="small"
                    variant="flat"
                  >
                    {{ formatDowntime(currentDowntime.total_downtime_minutes) }}
                  </v-chip>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="closeDialog"
          :disabled="loading"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="handleSubmit"
          :loading="loading"
          :disabled="!valid"
        >
          <v-icon start>mdi-content-save</v-icon>
          Update Downtime
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
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
const formRef = ref()
const valid = ref(false)
const loading = ref(false)
const currentDowntime = ref<any>(null)

const formData = reactive({
  downtime_start: '',
  downtime_end: ''
})

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Methods
const fetchTicket = async () => {
  if (!props.ticketId) return

  try {
    const response = await apiClient.get(`/trouble-tickets/${props.ticketId}`)
    const ticket = response.data

    currentDowntime.value = {
      downtime_start: ticket.downtime_start,
      downtime_end: ticket.downtime_end,
      total_downtime_minutes: ticket.total_downtime_minutes
    }

    // Pre-fill form with current values
    if (ticket.downtime_start) {
      formData.downtime_start = formatDateTimeLocal(ticket.downtime_start)
    }
    if (ticket.downtime_end) {
      formData.downtime_end = formatDateTimeLocal(ticket.downtime_end)
    }
  } catch (error) {
    console.error('Failed to fetch ticket:', error)
  }
}

const calculateDowntime = () => {
  if (!formData.downtime_start) return '-'

  const start = new Date(formData.downtime_start)
  const end = formData.downtime_end ? new Date(formData.downtime_end) : new Date()

  if (end < start) return 'Invalid time range'

  const diff = end.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  return formatDowntime(minutes)
}

const handleSubmit = async () => {
  if (!formRef.value?.validate()) return

  loading.value = true
  try {
    const payload: any = {
      downtime_start: formData.downtime_start ? new Date(formData.downtime_start).toISOString() : null,
      downtime_end: formData.downtime_end ? new Date(formData.downtime_end).toISOString() : null
    }

    await apiClient.post(`/trouble-tickets/${props.ticketId}/downtime`, payload)

    emit('updated')
    closeDialog()
  } catch (error) {
    console.error('Failed to update downtime:', error)
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.downtime_start = ''
  formData.downtime_end = ''
  currentDowntime.value = null

  if (formRef.value) {
    formRef.value.resetValidation()
  }
}

// Utility functions
const getDowntimeColor = (minutes: number) => {
  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const formatDowntime = (minutes: number) => {
  if (minutes < 60) return `${minutes} minutes`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours} hour${hours > 1 ? 's' : ''}`
  return `${hours}h ${remainingMinutes}m`
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

const formatDateTimeLocal = (dateString: string) => {
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}`
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
    resetForm()
  }
})
</script>