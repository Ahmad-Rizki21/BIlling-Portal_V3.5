<template>
  <v-dialog 
    v-model="dialog" 
    max-width="700" 
    persistent
    class="modern-dialog"
    :fullscreen="$vuetify.display.mobile"
  >
    <v-card class="modern-modal-card" elevation="0">
      <!-- Header -->
      <div class="modal-header">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar color="warning" size="40" class="me-3">
              <v-icon size="20">mdi-state-machine</v-icon>
            </v-avatar>
            <div>
              <h2 class="modal-title">Update Ticket Status</h2>
              <p class="modal-subtitle">Change the status and add relevant information</p>
            </div>
          </div>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="closeDialog"
            class="close-btn"
          ></v-btn>
        </div>
      </div>

      <v-divider class="modal-divider"></v-divider>

      <!-- Content -->
      <v-card-text class="modal-content">
        <v-form ref="formRef" v-model="valid" lazy-validation>
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" class="me-2">mdi-format-list-bulleted</v-icon>
              <h3 class="section-title">Status Information</h3>
            </div>
            
            <v-select
              v-model="formData.status"
              label="New Status"
              :items="statusOptions"
              item-title="title"
              item-value="value"
              :rules="[v => !!v || 'Status is required']"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-flag"
              class="modern-select"
              :menu-props="{ contentClass: 'status-menu' }"
            >
              <template v-slot:selection="{ item }">
                <v-chip
                  :color="getStatusColor(item.value)"
                  size="small"
                  variant="flat"
                  class="status-chip"
                >
                  <v-icon start size="x-small">{{ getStatusIcon(item.value) }}</v-icon>
                  {{ item.title }}
                </v-chip>
              </template>
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" class="status-item">
                  <template v-slot:prepend>
                    <v-chip
                      :color="getStatusColor(item.value)"
                      size="small"
                      variant="flat"
                    >
                      <v-icon start size="x-small">{{ getStatusIcon(item.value) }}</v-icon>
                      {{ item.title }}
                    </v-chip>
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </div>

          <div class="form-section">
            <div class="section-header">
              <v-icon color="info" class="me-2">mdi-note-text</v-icon>
              <h3 class="section-title">Additional Information</h3>
            </div>
            
            <div class="form-grid">
              <v-textarea
                v-model="formData.notes"
                label="Notes"
                placeholder="Additional notes about status change..."
                rows="3"
                auto-grow
                clearable
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-note-outline"
                class="modern-textarea"
              ></v-textarea>

              <v-textarea
                v-model="formData.action_description"
                label="Action Description"
                placeholder="Describe the action taken that led to this status change..."
                rows="3"
                auto-grow
                clearable
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-cog-outline"
                class="modern-textarea"
              ></v-textarea>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <v-icon color="success" class="me-2">mdi-clipboard-text</v-icon>
              <h3 class="section-title">Summary</h3>
            </div>
            
            <div class="form-grid">
              <v-textarea
                v-model="formData.summary_problem"
                label="Summary Problem"
                placeholder="Brief summary of the problem..."
                rows="2"
                auto-grow
                clearable
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-alert-circle-outline"
                class="modern-textarea"
              ></v-textarea>

              <v-textarea
                v-model="formData.summary_action"
                label="Summary Action"
                placeholder="Brief summary of the action taken..."
                rows="2"
                auto-grow
                clearable
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-check-circle-outline"
                class="modern-textarea"
              ></v-textarea>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <v-icon color="purple" class="me-2">mdi-image</v-icon>
              <h3 class="section-title">Evidence</h3>
            </div>
            
            <v-text-field
              v-model="formData.evidence"
              label="Evidence URL"
              placeholder="URL to evidence (photo, document, etc.)"
              prepend-inner-icon="mdi-link"
              clearable
              variant="outlined"
              density="comfortable"
              class="modern-textfield"
            ></v-text-field>
          </div>
        </v-form>
      </v-card-text>

      <v-divider class="modal-divider"></v-divider>

      <!-- Actions -->
      <v-card-actions class="modal-actions">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          @click="closeDialog"
          size="large"
          class="cancel-btn"
        >
          <v-icon start>mdi-close</v-icon>
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="submitForm"
          :loading="loading"
          :disabled="!valid"
          size="large"
          variant="flat"
          class="submit-btn"
        >
          <v-icon start>mdi-check</v-icon>
          Update Status
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
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
  updated: []
}>()

// State
const loading = ref(false)
const valid = ref(false)
const formRef = ref()

// Form data
const formData = reactive({
  status: '',
  notes: '',
  action_description: '',
  summary_problem: '',
  summary_action: '',
  evidence: ''
})

// Status options
const statusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending Customer', value: 'pending_customer' },
  { title: 'Pending Vendor', value: 'pending_vendor' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Closed', value: 'closed' },
  { title: 'Cancelled', value: 'cancelled' }
]

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Utility functions for status styling
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

// Methods
const submitForm = async () => {
  if (!formRef.value) return

  const { valid: formValid } = await formRef.value.validate()
  if (!formValid) return

  if (!props.ticketId) {
    alert('Ticket ID is required')
    return
  }

  loading.value = true
  try {
    await apiClient.post(`/trouble-tickets/${props.ticketId}/status`, {
      status: formData.status,
      notes: formData.notes,
      action_description: formData.action_description,
      summary_problem: formData.summary_problem,
      summary_action: formData.summary_action,
      evidence: formData.evidence
    })
    
    emit('updated')
    closeDialog()
  } catch (error) {
    console.error('Failed to update status:', error)
    alert('Failed to update status')
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.status = ''
  formData.notes = ''
  formData.action_description = ''
  formData.summary_problem = ''
  formData.summary_action = ''
  formData.evidence = ''
}

// Watchers
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})
</script>

<style scoped>
.modern-dialog :deep(.v-overlay__content) {
  margin: 24px;
  width: calc(100% - 48px);
  max-width: 700px;
}

.modern-modal-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  overflow: hidden;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.modal-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.08) 0%, 
    rgba(var(--v-theme-secondary), 0.05) 100%);
  padding: 24px;
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.12);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
}

.modal-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 4px 0 0 0;
}

.close-btn {
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.3s ease;
}

.close-btn:hover {
  color: rgb(var(--v-theme-error));
  background-color: rgba(var(--v-theme-error), 0.1);
}

/* Content */
.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px !important;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.3) transparent;
}

.modal-content::-webkit-scrollbar {
  width: 6px;
}

.modal-content::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* Form Sections */
.form-section {
  margin-bottom: 32px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.08);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

/* Form Controls */
.modern-select,
.modern-textarea,
.modern-textfield {
  transition: all 0.3s ease;
}

.modern-select :deep(.v-field--focused),
.modern-textarea :deep(.v-field--focused),
.modern-textfield :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.modern-select :deep(.v-field__outline),
.modern-textarea :deep(.v-field__outline),
.modern-textfield :deep(.v-field__outline) {
  color: rgba(var(--v-theme-outline), 0.3);
}

.modern-select :deep(.v-field--focused .v-field__outline),
.modern-textarea :deep(.v-field--focused .v-field__outline),
.modern-textfield :deep(.v-field--focused .v-field__outline) {
  color: rgb(var(--v-theme-primary));
}

/* Status Chip in Select */
.status-chip {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-item {
  padding: 8px 16px;
}

/* Menu Styling */
.status-menu {
  background: rgb(var(--v-theme-surface)) !important;
  border: 1px solid rgba(var(--v-theme-outline), 0.12) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(var(--v-theme-shadow), 0.15) !important;
}

/* Dividers */
.modal-divider {
  border-color: rgba(var(--v-theme-outline), 0.08);
}

/* Actions */
.modal-actions {
  padding: 24px !important;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  gap: 12px;
}

.cancel-btn {
  border-color: rgba(var(--v-theme-outline), 0.3);
  color: rgba(var(--v-theme-on-surface), 0.8);
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  border-color: rgb(var(--v-theme-error));
  color: rgb(var(--v-theme-error));
  background-color: rgba(var(--v-theme-error), 0.05);
}

.submit-btn {
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s ease;
}

.submit-btn:hover {
  box-shadow: 0 6px 16px rgba(var(--v-theme-primary), 0.4);
  transform: translateY(-1px);
}

/* Dark Theme Adjustments */
.v-theme--dark .modal-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.15) 0%, 
    rgba(var(--v-theme-secondary), 0.1) 100%);
  border-bottom-color: rgba(var(--v-theme-outline), 0.2);
}

.v-theme--dark .modern-modal-card {
  background: rgb(var(--v-theme-surface-bright));
  border-color: rgba(var(--v-theme-outline), 0.2);
}

.v-theme--dark .section-header {
  border-bottom-color: rgba(var(--v-theme-outline), 0.15);
}

.v-theme--dark .modal-actions {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-top: 1px solid rgba(var(--v-theme-outline), 0.15);
}

.v-theme--dark .status-menu {
  background: rgb(var(--v-theme-surface-bright)) !important;
  border-color: rgba(var(--v-theme-outline), 0.2) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .modern-dialog :deep(.v-overlay__content) {
    margin: 0;
    width: 100%;
    max-width: none;
    height: 100vh;
  }
  
  .modern-modal-card {
    border-radius: 0;
    height: 100vh;
  }
  
  .modal-header {
    padding: 20px;
  }
  
  .modal-title {
    font-size: 1.25rem;
  }
  
  .modal-content {
    padding: 20px !important;
  }
  
  .form-section {
    margin-bottom: 24px;
  }
  
  .modal-actions {
    padding: 20px !important;
    flex-direction: column;
  }
  
  .cancel-btn,
  .submit-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .close-btn {
    align-self: flex-end;
  }
  
  .modal-header {
    padding: 16px;
  }
  
  .modal-content {
    padding: 16px !important;
  }
  
  .modal-actions {
    padding: 16px !important;
  }
}
</style>