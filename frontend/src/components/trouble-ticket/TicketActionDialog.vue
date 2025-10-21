<template>
  <v-dialog v-model="dialog" max-width="900" persistent scrollable>
    <v-card class="rounded-lg elevation-8">
      <!-- Header dengan gradient -->
      <v-card-title class="px-6 py-4 bg-gradient-primary">
        <div class="d-flex align-center justify-space-between w-100">
          <div class="d-flex align-center">
            <v-avatar color="white" size="40" class="me-3">
              <v-icon color="primary" size="24">mdi-cog-transfer</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold text-white">Update Ticket Action</div>
              <div class="text-caption text-white-70">Ticket #{{ ticketId }}</div>
            </div>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeDialog"
            class="text-white"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-6" style="max-height: 70vh;">
        <v-form ref="formRef" v-model="valid" lazy-validation>
          <!-- Status Section -->
          <div class="form-section mb-6">
            <div class="section-header mb-4">
              <v-icon color="primary" class="me-2">mdi-flag-variant</v-icon>
              <span class="text-subtitle-1 font-weight-bold">Status Update</span>
            </div>
            
            <v-select
              v-model="formData.status"
              label="New Status"
              :items="statusOptions"
              item-title="title"
              item-value="value"
              clearable
              variant="outlined"
              density="comfortable"
              hint="Leave empty if not changing status"
              persistent-hint
              prepend-inner-icon="mdi-swap-horizontal"
              color="primary"
            >
              <template v-slot:selection="{ item }">
                <v-chip 
                  :color="getStatusColor(item.value)" 
                  size="small"
                  class="font-weight-medium"
                >
                  {{ item.title }}
                </v-chip>
              </template>
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props">
                  <template v-slot:prepend>
                    <v-icon :color="getStatusColor(item.value)">
                      {{ getStatusIcon(item.value) }}
                    </v-icon>
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </div>

          <!-- Action Details Section -->
          <div class="form-section mb-6">
            <div class="section-header mb-4">
              <v-icon color="primary" class="me-2">mdi-text-box-outline</v-icon>
              <span class="text-subtitle-1 font-weight-bold">Action Details</span>
            </div>

            <v-textarea
              v-model="formData.action_description"
              label="Action Description"
              placeholder="Describe the action taken in detail..."
              rows="3"
              auto-grow
              clearable
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-text"
              color="primary"
              counter
            ></v-textarea>
          </div>

          <!-- Summary Section -->
          <div class="form-section mb-6">
            <div class="section-header mb-4">
              <v-icon color="primary" class="me-2">mdi-clipboard-text-outline</v-icon>
              <span class="text-subtitle-1 font-weight-bold">Summary</span>
            </div>

            <v-row>
              <v-col cols="12" md="6">
                <v-textarea
                  v-model="formData.summary_problem"
                  label="Summary Problem"
                  placeholder="Brief summary of the problem..."
                  rows="3"
                  auto-grow
                  clearable
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-alert-circle-outline"
                  color="primary"
                  counter
                  class="summary-field"
                ></v-textarea>
              </v-col>
              <v-col cols="12" md="6">
                <v-textarea
                  v-model="formData.summary_action"
                  label="Summary Action"
                  placeholder="Brief summary of the action taken..."
                  rows="3"
                  auto-grow
                  clearable
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-check-circle-outline"
                  color="primary"
                  counter
                  class="summary-field"
                ></v-textarea>
              </v-col>
            </v-row>
          </div>

          <!-- Notes Section -->
          <div class="form-section mb-6">
            <div class="section-header mb-4">
              <v-icon color="primary" class="me-2">mdi-note-text-outline</v-icon>
              <span class="text-subtitle-1 font-weight-bold">Additional Notes</span>
            </div>

            <v-textarea
              v-model="formData.notes"
              label="Notes"
              placeholder="Add any additional notes or comments..."
              rows="2"
              auto-grow
              clearable
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-pencil"
              color="primary"
              counter
            ></v-textarea>
          </div>

          <!-- Evidence Upload Section -->
          <div class="form-section">
            <div class="section-header mb-4">
              <v-icon color="primary" class="me-2">mdi-paperclip</v-icon>
              <span class="text-subtitle-1 font-weight-bold">Evidence Attachment</span>
            </div>

            <v-file-input
              v-model="file"
              label="Upload Evidence"
              placeholder="Choose files to upload..."
              prepend-icon=""
              prepend-inner-icon="mdi-cloud-upload"
              :accept="acceptedTypes"
              show-size
              counter
              multiple
              variant="outlined"
              density="comfortable"
              color="primary"
              chips
              class="mb-4"
            >
              <template v-slot:selection="{ fileNames }">
                <template v-for="(fileName, index) in fileNames" :key="fileName">
                  <v-chip
                    size="small"
                    color="primary"
                    class="me-2 mb-2"
                    closable
                    @click:close="removeFile(index)"
                  >
                    <v-icon start size="small">mdi-file</v-icon>
                    {{ fileName }}
                  </v-chip>
                </template>
              </template>
            </v-file-input>

            <!-- File Preview Grid -->
            <v-expand-transition>
              <div v-if="file && file.length > 0" class="preview-section">
                <div class="text-subtitle-2 mb-3 d-flex align-center">
                  <v-icon size="small" class="me-2">mdi-eye-outline</v-icon>
                  File Preview ({{ file.length }} file{{ file.length > 1 ? 's' : '' }})
                </div>
                <v-row>
                  <v-col 
                    v-for="(f, index) in file" 
                    :key="index" 
                    cols="6"
                    sm="4"
                    md="3"
                  >
                    <v-card 
                      class="file-preview-card elevation-2 hover-lift"
                      :ripple="false"
                    >
                      <div class="preview-container position-relative">
                        <!-- Image Preview -->
                        <div v-if="isImageFile(f)" class="preview-content">
                          <v-img 
                            :src="previewUrls[index]" 
                            aspect-ratio="1"
                            cover
                            class="rounded-t"
                          >
                            <template v-slot:placeholder>
                              <div class="d-flex align-center justify-center fill-height">
                                <v-progress-circular
                                  indeterminate
                                  color="primary"
                                ></v-progress-circular>
                              </div>
                            </template>
                          </v-img>
                          <div class="preview-overlay">
                            <v-icon color="white" size="32">mdi-image</v-icon>
                          </div>
                        </div>
                        
                        <!-- Video Preview -->
                        <div v-else-if="isVideoFile(f)" class="preview-content">
                          <video 
                            :src="previewUrls[index]" 
                            class="video-preview"
                          />
                          <div class="preview-overlay">
                            <v-icon color="white" size="32">mdi-video</v-icon>
                          </div>
                        </div>
                        
                        <!-- Other Files -->
                        <div v-else class="preview-content file-icon-preview">
                          <v-icon size="48" :color="getFileIconColor(f)">
                            {{ getFileIcon(f) }}
                          </v-icon>
                        </div>

                        <!-- Remove Button -->
                        <v-btn
                          icon
                          size="x-small"
                          color="error"
                          class="remove-btn"
                          @click="removeFile(index)"
                        >
                          <v-icon size="16">mdi-close</v-icon>
                        </v-btn>
                      </div>
                      
                      <v-card-text class="pa-2">
                        <div class="text-caption text-truncate" :title="f.name">
                          {{ f.name }}
                        </div>
                        <div class="text-caption text-grey">
                          {{ formatFileSize(f.size) }}
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-expand-transition>
          </div>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <!-- Footer Actions -->
      <v-card-actions class="px-6 py-4 bg-grey-lighten-5">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          color="grey-darken-1"
          @click="closeDialog"
          class="px-6"
          prepend-icon="mdi-close"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="submitForm"
          :loading="loading"
          :disabled="!valid"
          class="px-6 elevation-2"
          prepend-icon="mdi-check"
        >
          Update Ticket Action
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
  updated: []
}>()

// Constants
const acceptedTypes = 'image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip'

// State
const loading = ref(false)
const valid = ref(false)
const formRef = ref()
const file = ref<File[]>([])
const previewUrls = ref<string[]>([])
const evidenceUrls = ref<string[]>([])

// Form data
const formData = ref({
  status: '',
  action_description: '',
  summary_problem: '',
  summary_action: '',
  notes: ''
})

// Status options
const statusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending', value: 'pending' },
  { title: 'Closed', value: 'closed' },
]

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

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
    // Convert file URLs to array of URLs
    evidenceUrls.value = []
    if (file.value && file.value.length > 0) {
      evidenceUrls.value = file.value.map(f => URL.createObjectURL(f))
    }

    // Prepare API payload with evidence as JSON string
    const payload = {
      status: formData.value.status,
      notes: formData.value.notes,
      action_description: formData.value.action_description,
      summary_problem: formData.value.summary_problem,
      summary_action: formData.value.summary_action,
      evidence: evidenceUrls.value.length > 0 ? JSON.stringify(evidenceUrls.value) : null
    }

    // Check if status is being updated or just adding action
    if (formData.value.status) {
      // Update status with action details
      await apiClient.post(`/trouble-tickets/${props.ticketId}/status`, payload)
    } else {
      // Just add action without changing status
      const { status, ...actionPayload } = payload
      await apiClient.post(`/trouble-tickets/${props.ticketId}/action`, actionPayload)
    }

    emit('updated')
    closeDialog()
  } catch (error) {
    console.error('Failed to update ticket action:', error)
    alert('Failed to update ticket action')
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.value = {
    status: '',
    action_description: '',
    summary_problem: '',
    summary_action: '',
    notes: ''
  }
  file.value = []
  previewUrls.value = []

  // Clean up evidence URLs
  evidenceUrls.value.forEach(url => URL.revokeObjectURL(url))
  evidenceUrls.value = []
}

const removeFile = (index: number) => {
  file.value.splice(index, 1)
  URL.revokeObjectURL(previewUrls.value[index])
  previewUrls.value.splice(index, 1)
}

// File preview utilities
const isImageFile = (file: File) => {
  return file.type.startsWith('image/')
}

const isVideoFile = (file: File) => {
  return file.type.startsWith('video/')
}

const getFileIcon = (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, string> = {
    pdf: 'mdi-file-pdf-box',
    doc: 'mdi-file-word',
    docx: 'mdi-file-word',
    xls: 'mdi-file-excel',
    xlsx: 'mdi-file-excel',
    txt: 'mdi-file-document',
    zip: 'mdi-folder-zip'
  }
  return iconMap[ext || ''] || 'mdi-file'
}

const getFileIconColor = (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase()
  const colorMap: Record<string, string> = {
    pdf: 'error',
    doc: 'info',
    docx: 'info',
    xls: 'success',
    xlsx: 'success',
    txt: 'grey',
    zip: 'warning'
  }
  return colorMap[ext || ''] || 'grey'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    open: 'info',
    in_progress: 'warning',
    pending: 'orange',
    closed: 'success',
  }
  return colorMap[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const iconMap: Record<string, string> = {
    open: 'mdi-email-open',
    in_progress: 'mdi-progress-clock',
    pending: 'mdi-account-clock',
    closed: 'mdi-close-circle',
  }
  return iconMap[status] || 'mdi-help-circle'
}

// Watchers
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})

watch(file, (newFiles) => {
  // Clean up previous preview URLs
  previewUrls.value.forEach(url => URL.revokeObjectURL(url))
  previewUrls.value = []
  
  // Create new preview URLs
  if (newFiles && newFiles.length > 0) {
    newFiles.forEach(f => {
      const url = URL.createObjectURL(f)
      previewUrls.value.push(url)
    })
  }
}, { deep: true })
</script>

<style scoped>
/* Gradient Background */
.bg-gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.text-white-70 {
  opacity: 0.7;
}

/* Form Sections */
.form-section {
  border-left: 3px solid rgb(var(--v-theme-primary));
  padding-left: 16px;
  transition: all 0.3s ease;
}

.form-section:hover {
  border-left-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.02);
  border-radius: 4px;
}

.section-header {
  display: flex;
  align-items: center;
  color: rgb(var(--v-theme-primary));
  font-size: 1rem;
}

/* File Preview Cards */
.file-preview-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  background: white;
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
}

.preview-container {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: #f5f5f5;
}

.preview-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-icon-preview {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.file-preview-card:hover .preview-overlay {
  opacity: 1;
}

.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.file-preview-card:hover .remove-btn {
  opacity: 1;
}

.preview-section {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px dashed #dee2e6;
}

/* Summary Fields */
.summary-field :deep(.v-field) {
  background-color: #fafafa;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .section-header {
    font-size: 0.9rem;
  }
  
  .form-section {
    padding-left: 12px;
  }
}

/* Smooth transitions */
* {
  transition: background-color 0.2s ease, border-color 0.2s ease;
}
</style>