<template>
  <v-dialog 
    v-model="dialog" 
    max-width="600"
    transition="dialog-bottom-transition"
    scrollable
  >
    <v-card class="rounded-lg" elevation="8">
      <!-- Header dengan Gradient -->
      <v-card-title class="pa-6 bg-gradient">
        <div class="d-flex align-center">
          <v-avatar color="white" size="40" class="me-3">
            <v-icon color="primary" size="24">mdi-account-transfer</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6 font-weight-bold">Assign Ticket</div>
            <div class="text-caption text-medium-emphasis">Transfer ticket to team member</div>
          </div>
        </div>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-6" style="max-height: 70vh;">
        <v-form ref="formRef" v-model="valid">
          <!-- Ticket Info Card - Prioritas Teratas -->
          <v-card 
            variant="tonal" 
            color="primary" 
            class="mb-6 rounded-lg"
            elevation="0"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon color="primary" class="me-2">mdi-ticket-outline</v-icon>
                <span class="text-subtitle-1 font-weight-bold">Ticket Information</span>
              </div>
              
              <v-row dense>
                <v-col cols="12" sm="6">
                  <div class="info-item">
                    <div class="text-caption text-medium-emphasis mb-1">Ticket Number</div>
                    <div class="font-weight-bold text-primary">
                      {{ ticketInfo?.ticket_number || `#${props.ticketId}` }}
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" sm="6" v-if="ticketInfo?.pelanggan">
                  <div class="info-item">
                    <div class="text-caption text-medium-emphasis mb-1">Customer</div>
                    <div class="font-weight-medium">{{ ticketInfo.pelanggan.nama }}</div>
                  </div>
                </v-col>
                <v-col cols="12">
                  <div class="info-item">
                    <div class="text-caption text-medium-emphasis mb-1">Title</div>
                    <div class="font-weight-medium">{{ ticketInfo?.title || 'Loading...' }}</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Current Assignment Alert -->
          <v-alert
            v-if="currentAssignment?.assigned_user"
            type="info"
            variant="tonal"
            class="mb-6 rounded-lg"
            border="start"
            elevation="0"
          >
            <template v-slot:prepend>
              <v-icon>mdi-information-outline</v-icon>
            </template>
            <div class="text-subtitle-2 font-weight-bold mb-2">Current Assignment</div>
            <div class="d-flex align-center">
              <v-avatar size="32" color="info" class="me-3">
                <v-icon size="18" color="white">mdi-account</v-icon>
              </v-avatar>
              <div>
                <div class="font-weight-medium">{{ currentAssignment.assigned_user.name }}</div>
                <div class="text-caption">{{ currentAssignment.assigned_user.role?.name || 'No role' }}</div>
              </div>
            </div>
          </v-alert>

          <v-alert
            v-else-if="currentAssignment"
            type="warning"
            variant="tonal"
            class="mb-6 rounded-lg"
            border="start"
            elevation="0"
          >
            <template v-slot:prepend>
              <v-icon>mdi-alert-circle-outline</v-icon>
            </template>
            <div class="font-weight-medium">This ticket is currently unassigned</div>
          </v-alert>

          <!-- Assignment Form -->
          <div class="form-section">
            <v-label class="text-subtitle-2 font-weight-bold mb-2 d-block">
              <v-icon size="20" class="me-1">mdi-account-arrow-right</v-icon>
              Assign To *
            </v-label>
            
            <v-select
              v-model="formData.assigned_to"
              :items="users"
              item-title="name"
              item-value="id"
              :loading="loadingUsers"
              :rules="[v => !!v || 'Please select a user to assign this ticket']"
              clearable
              return-object
              placeholder="Select team member"
              variant="outlined"
              density="comfortable"
              class="mb-4 rounded-lg"
            >
              <template v-slot:prepend-inner>
                <v-icon color="primary">mdi-account-search</v-icon>
              </template>
              
              <template v-slot:item="{ props, item }">
                <v-list-item 
                  v-bind="props"
                  class="my-1"
                  rounded="lg"
                >
                  <template v-slot:prepend>
                    <v-avatar size="40" color="primary" class="me-3">
                      <span class="text-h6 font-weight-bold">
                        {{ item.raw.name?.charAt(0).toUpperCase() }}
                      </span>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">
                    {{ item.raw.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip size="x-small" color="primary" variant="tonal">
                      {{ item.raw.role?.name || 'No role' }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
              </template>

              <template v-slot:selection="{ item }">
                <div class="d-flex align-center">
                  <v-avatar size="28" color="primary" class="me-2">
                    <span class="text-caption font-weight-bold">
                      {{ item.raw.name?.charAt(0).toUpperCase() }}
                    </span>
                  </v-avatar>
                  <span class="font-weight-medium">{{ item.raw.name }}</span>
                </div>
              </template>
            </v-select>

            <v-label class="text-subtitle-2 font-weight-bold mb-2 d-block">
              <v-icon size="20" class="me-1">mdi-note-text-outline</v-icon>
              Assignment Notes
              <span class="text-caption text-medium-emphasis font-weight-regular">(Optional)</span>
            </v-label>
            
            <v-textarea
              v-model="formData.notes"
              rows="3"
              auto-grow
              placeholder="Add any notes about this assignment..."
              counter="500"
              variant="outlined"
              density="comfortable"
              class="rounded-lg"
            >
              <template v-slot:prepend-inner>
                <v-icon color="primary">mdi-pencil</v-icon>
              </template>
            </v-textarea>
          </div>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <!-- Action Buttons -->
      <v-card-actions class="pa-6 bg-surface">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          size="large"
          @click="closeDialog"
          :disabled="loading"
          class="rounded-lg px-6"
        >
          <v-icon start>mdi-close</v-icon>
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          size="large"
          @click="handleSubmit"
          :loading="loading"
          :disabled="!valid || !formData.assigned_to"
          class="rounded-lg px-6 elevation-2"
        >
          <v-icon start>mdi-check-circle</v-icon>
          Assign Ticket
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
  'assigned': []
}>()

// Types
interface User {
  id: number
  name: string
  role?: {
    name: string
  }
}

// State
const formRef = ref()
const valid = ref(false)
const loading = ref(false)
const loadingUsers = ref(false)
const users = ref<User[]>([])
const currentAssignment = ref<any>(null)
const ticketInfo = ref<any>(null)

const formData = reactive({
  assigned_to: null as User | null,
  notes: ''
})

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Methods
const fetchUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await apiClient.get('/users?limit=1000')
    const rawData = response.data.data || response.data || []

    // Remove duplicates based on user ID first
    const uniqueUsersById = rawData.filter((user: any, index: number, self: any[]) =>
      index === self.findIndex((u: any) => u.id === user.id)
    )

    // Then remove duplicates based on name (keep the first occurrence)
    const seenNames = new Set()
    const uniqueUsers = uniqueUsersById.filter((user: any) => {
      const normalizedName = user.name?.trim().toLowerCase()
      if (normalizedName && seenNames.has(normalizedName)) {
        return false
      }
      if (normalizedName) {
        seenNames.add(normalizedName)
      }
      return true
    })

    // Sort users alphabetically by name
    users.value = uniqueUsers.sort((a: any, b: any) =>
      (a.name || '').localeCompare(b.name || '')
    )
  } catch (error) {
    console.error('Failed to fetch users:', error)
    users.value = []
  } finally {
    loadingUsers.value = false
  }
}

const fetchTicket = async () => {
  if (!props.ticketId) return

  try {
    const response = await apiClient.get(`/trouble-tickets/${props.ticketId}`)
    ticketInfo.value = response.data
    currentAssignment.value = {
      assigned_user: response.data.assigned_user
    }
  } catch (error) {
    console.error('Failed to fetch ticket:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value?.validate()) return

  loading.value = true
  try {
    const payload = {
      assigned_to: formData.assigned_to?.id,
      notes: formData.notes
    }

    await apiClient.post(`/trouble-tickets/${props.ticketId}/assign`, payload)

    emit('assigned')
    closeDialog()
  } catch (error) {
    console.error('Failed to assign ticket:', error)
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.assigned_to = null
  formData.notes = ''
  currentAssignment.value = null
  ticketInfo.value = null

  if (formRef.value) {
    formRef.value.resetValidation()
  }
}

// Watchers
watch(() => props.ticketId, (newId) => {
  if (newId && props.modelValue) {
    fetchTicket()
  }
})

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    fetchUsers()
    if (props.ticketId) {
      fetchTicket()
    }
  } else {
    resetForm()
  }
})
</script>

<style scoped>
.bg-gradient {
  background: linear-gradient(135deg, rgb(var(--v-theme-surface)) 0%, rgb(var(--v-theme-primary), 0.05) 100%);
}

.bg-surface {
  background-color: rgb(var(--v-theme-surface));
}

.info-item {
  padding: 8px 0;
}

.form-section {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive adjustments */
@media (max-width: 600px) {
  :deep(.v-card-title) {
    padding: 16px !important;
  }
  
  :deep(.v-card-text) {
    padding: 16px !important;
  }
  
  :deep(.v-card-actions) {
    padding: 16px !important;
    flex-direction: column;
    gap: 8px;
  }
  
  :deep(.v-card-actions .v-btn) {
    width: 100%;
  }
  
  :deep(.v-spacer) {
    display: none;
  }
}

/* Smooth transitions */
:deep(.v-select),
:deep(.v-textarea) {
  transition: all 0.2s ease;
}

:deep(.v-select:hover),
:deep(.v-textarea:hover) {
  transform: translateY(-1px);
}

/* Custom scrollbar */
:deep(.v-card-text) {
  scrollbar-width: thin;
  scrollbar-color: rgb(var(--v-theme-primary)) transparent;
}

:deep(.v-card-text::-webkit-scrollbar) {
  width: 6px;
}

:deep(.v-card-text::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.v-card-text::-webkit-scrollbar-thumb) {
  background-color: rgb(var(--v-theme-primary));
  border-radius: 3px;
}
</style>