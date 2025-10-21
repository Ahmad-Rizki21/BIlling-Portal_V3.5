<template>
  <v-dialog v-model="dialog" max-width="900" persistent scrollable>
    <v-card class="modern-action-card" elevation="0" rounded="xl">
      <!-- Modern Header -->
      <div class="modern-header">
        <div class="header-content">
          <div class="header-icon-wrapper">
            <v-avatar color="white" size="56" class="elevation-4">
              <v-icon color="primary" size="32">mdi-history</v-icon>
            </v-avatar>
          </div>
          <div class="header-text">
            <h2 class="header-title">Add Action History</h2>
            <p class="header-subtitle">
              Document the actions taken to resolve this ticket
            </p>
          </div>
        </div>
        <v-btn
          icon
          variant="text"
          class="close-btn"
          @click="closeDialog"
          :disabled="loading"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </div>

      <v-divider class="divider-gradient"></v-divider>

      <v-card-text class="form-content">
        <v-form ref="formRef" v-model="valid">
          
          <!-- Action Description Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-text-box</v-icon>
              <span class="section-title">Action Description</span>
              <v-chip size="x-small" color="primary" variant="tonal" class="ml-2">Primary</v-chip>
            </div>

            <v-card variant="tonal" rounded="xl" class="input-card">
              <v-card-text class="pa-4">
                <v-textarea
                  v-model="formData.action_description"
                  placeholder="Provide detailed description of the action taken to resolve the issue..."
                  rows="4"
                  auto-grow
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  hide-details="auto"
                  class="modern-textarea"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="primary" size="20">mdi-format-text</v-icon>
                  </template>
                </v-textarea>
              </v-card-text>
            </v-card>
          </div>

          <!-- Problem & Action Summary Grid -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-format-list-bulleted</v-icon>
              <span class="section-title">Summary</span>
            </div>

            <v-row>
              <v-col cols="12" md="6">
                <v-card variant="tonal" rounded="xl" class="summary-card problem-card">
                  <v-card-text class="pa-4">
                    <div class="summary-header">
                      <v-avatar color="warning" size="36" class="elevation-2">
                        <v-icon color="white" size="18">mdi-alert-circle</v-icon>
                      </v-avatar>
                      <div class="ml-3">
                        <h3 class="summary-title">Summary Problem</h3>
                        <p class="summary-subtitle">Brief problem description</p>
                      </div>
                    </div>
                    <v-textarea
                      v-model="formData.summary_problem"
                      placeholder="Brief summary of the problem encountered..."
                      rows="3"
                      auto-grow
                      variant="outlined"
                      density="comfortable"
                      rounded="lg"
                      hide-details="auto"
                      class="mt-3 modern-textarea"
                    >
                      <template v-slot:prepend-inner>
                        <v-icon color="warning" size="18">mdi-help-circle</v-icon>
                      </template>
                    </v-textarea>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12" md="6">
                <v-card variant="tonal" rounded="xl" class="summary-card action-card">
                  <v-card-text class="pa-4">
                    <div class="summary-header">
                      <v-avatar color="success" size="36" class="elevation-2">
                        <v-icon color="white" size="18">mdi-check-circle</v-icon>
                      </v-avatar>
                      <div class="ml-3">
                        <h3 class="summary-title">Summary Action</h3>
                        <p class="summary-subtitle">Brief action description</p>
                      </div>
                    </div>
                    <v-textarea
                      v-model="formData.summary_action"
                      placeholder="Brief summary of the action implemented..."
                      rows="3"
                      auto-grow
                      variant="outlined"
                      density="comfortable"
                      rounded="lg"
                      hide-details="auto"
                      class="mt-3 modern-textarea"
                    >
                      <template v-slot:prepend-inner>
                        <v-icon color="success" size="18">mdi-check</v-icon>
                      </template>
                    </v-textarea>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>

          <!-- Evidence Upload Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-file-upload</v-icon>
              <span class="section-title">Upload Evidence</span>
              <v-chip size="x-small" color="grey" variant="tonal" class="ml-2">Optional</v-chip>
            </div>

            <v-card variant="outlined" rounded="xl" class="evidence-upload-card">
              <div class="evidence-header">
                <div class="d-flex align-center">
                  <v-avatar color="info" size="40" class="elevation-2">
                    <v-icon color="white" size="22">mdi-cloud-upload</v-icon>
                  </v-avatar>
                  <div class="ml-3 flex-grow-1">
                    <h3 class="evidence-title">Attach Evidence Files</h3>
                    <p class="evidence-subtitle">
                      Photos, videos, or documents as proof of work completed
                    </p>
                  </div>
                </div>
              </div>

              <v-card-text class="pa-4">
                <!-- Drag & Drop Area -->
                <div
                  class="drop-zone"
                  :class="{ 'drop-zone-active': isDragging }"
                  @dragover.prevent="isDragging = true"
                  @dragleave.prevent="isDragging = false"
                  @drop.prevent="handleDrop"
                  @click="triggerFileInput"
                >
                  <v-icon size="56" :color="isDragging ? 'primary' : 'grey'" class="drop-icon">
                    mdi-cloud-upload-outline
                  </v-icon>
                  <div class="drop-title">
                    {{ isDragging ? 'Drop files here' : 'Drag & Drop Files Here' }}
                  </div>
                  <div class="drop-subtitle">
                    or click to browse from your device
                  </div>
                  <div class="file-types">
                    <v-chip size="small" variant="tonal" color="grey">
                      <v-icon start size="14">mdi-image</v-icon>
                      Images
                    </v-chip>
                    <v-chip size="small" variant="tonal" color="grey">
                      <v-icon start size="14">mdi-video</v-icon>
                      Videos
                    </v-chip>
                    <v-chip size="small" variant="tonal" color="grey">
                      <v-icon start size="14">mdi-file-document</v-icon>
                      Documents
                    </v-chip>
                  </div>
                </div>

                <!-- Hidden file input -->
                <input
                  ref="fileInputRef"
                  type="file"
                  multiple
                  accept="image/*,video/*,.pdf,.doc,.docx,.txt"
                  style="display: none;"
                  @change="handleFileSelect"
                />

                <!-- File Preview -->
                <v-expand-transition>
                  <div v-if="evidenceFiles.length > 0" class="file-preview-section">
                    <div class="preview-header">
                      <div class="preview-title">
                        <v-icon color="primary" size="20" class="mr-2">mdi-paperclip</v-icon>
                        <span class="font-weight-bold">{{ evidenceFiles.length }} file(s) selected</span>
                      </div>
                      <v-btn
                        size="small"
                        variant="text"
                        color="error"
                        @click="clearAllFiles"
                        prepend-icon="mdi-delete"
                      >
                        Clear All
                      </v-btn>
                    </div>

                    <div class="file-list">
                      <v-card
                        v-for="(file, index) in evidenceFiles"
                        :key="index"
                        variant="tonal"
                        rounded="lg"
                        class="file-item"
                      >
                        <v-card-text class="pa-3">
                          <div class="d-flex align-center">
                            <v-avatar :color="getFileIconColor(file)" size="44" class="mr-3">
                              <v-icon color="white" size="22">{{ getFileIcon(file) }}</v-icon>
                            </v-avatar>
                            <div class="flex-grow-1 file-info">
                              <div class="file-name" :title="file.name">
                                {{ file.name }}
                              </div>
                              <div class="file-meta">
                                {{ formatFileSize(file.size) }} • {{ getFileType(file) }}
                              </div>
                            </div>
                            <v-btn
                              icon="mdi-close"
                              size="small"
                              variant="text"
                              color="error"
                              @click="removeFile(index)"
                            ></v-btn>
                          </div>
                        </v-card-text>
                      </v-card>
                    </div>
                  </div>
                </v-expand-transition>
              </v-card-text>
            </v-card>
          </div>

          <!-- Additional Notes Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-note-text</v-icon>
              <span class="section-title">Additional Notes</span>
              <v-chip size="x-small" color="grey" variant="tonal" class="ml-2">Optional</v-chip>
            </div>

            <v-card variant="tonal" rounded="xl" class="notes-card">
              <v-card-text class="pa-4">
                <v-textarea
                  v-model="formData.notes"
                  placeholder="Add any additional notes, follow-up tasks, or important information..."
                  rows="3"
                  auto-grow
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  hide-details="auto"
                  class="modern-textarea"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="grey-darken-1" size="20">mdi-note-edit</v-icon>
                  </template>
                </v-textarea>
              </v-card-text>
            </v-card>
          </div>
        </v-form>
      </v-card-text>

      <v-divider class="divider-gradient"></v-divider>

      <!-- Action Footer -->
      <v-card-actions class="action-footer">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          @click="closeDialog"
          :disabled="loading"
          prepend-icon="mdi-close"
          rounded="xl"
          size="large"
          class="px-6"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="submitForm"
          :loading="loading"
          :disabled="loading || (!formData.action_description && !formData.summary_problem && !formData.summary_action && evidenceFiles.length === 0)"
          prepend-icon="mdi-content-save"
          rounded="xl"
          size="large"
          class="px-8 elevation-2"
        >
          Save Action
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
  saved: []
}>()

// State
const loading = ref(false)
const valid = ref(true)
const formRef = ref()
const fileInputRef = ref<HTMLInputElement | null>(null)

// Form data
const formData = reactive({
  action_description: '',
  summary_problem: '',
  summary_action: '',
  evidence: '',
  notes: ''
})

const evidenceFiles = ref<File[]>([])
const snackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' | 'warning' | 'info' })
const isDragging = ref(false)

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Methods
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(target.files)
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  if (!props.ticketId) {
    showSnackbar('Ticket ID is required', 'error')
    return
  }

  if (!formData.action_description && !formData.summary_problem && !formData.summary_action && evidenceFiles.value.length === 0) {
    showSnackbar('At least one field must be filled', 'error')
    return
  }

  loading.value = true
  try {
    let evidenceUrls: string[] = []
    if (evidenceFiles.value.length > 0) {
      for (const file of evidenceFiles.value) {
        try {
          const formDataUpload = new FormData()
          formDataUpload.append('file', file)

          const uploadResponse = await apiClient.post('/uploads/evidence/', formDataUpload, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })

          evidenceUrls.push(uploadResponse.data.file_url)
        } catch (uploadError) {
          console.error('Failed to upload evidence file:', uploadError)
          showSnackbar(`Failed to upload evidence file: ${file.name}`, 'error')
          return
        }
      }
    }

    await apiClient.post(`/trouble-tickets/${props.ticketId}/action`, {
      action_description: formData.action_description,
      summary_problem: formData.summary_problem,
      summary_action: formData.summary_action,
      evidence: evidenceUrls.length > 0 ? JSON.stringify(evidenceUrls) : null,
      notes: formData.notes
    })

    showSnackbar('Action added successfully', 'success')
    emit('saved')
    closeDialog()
  } catch (error) {
    console.error('Failed to add action:', error)
    showSnackbar('Failed to add action', 'error')
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.action_description = ''
  formData.summary_problem = ''
  formData.summary_action = ''
  formData.evidence = ''
  formData.notes = ''
  evidenceFiles.value = []
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const removeFile = (index: number) => {
  evidenceFiles.value.splice(index, 1)
}

const clearAllFiles = () => {
  evidenceFiles.value = []
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    addFiles(files)
  }
}

const addFiles = (files: FileList) => {
  const newFiles = Array.from(files)
  evidenceFiles.value = [...evidenceFiles.value, ...newFiles]
}

const getFileIcon = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, string> = {
    'jpg': 'mdi-image',
    'jpeg': 'mdi-image',
    'png': 'mdi-image',
    'gif': 'mdi-image',
    'webp': 'mdi-image',
    'bmp': 'mdi-image',
    'mp4': 'mdi-video',
    'avi': 'mdi-video',
    'mov': 'mdi-video',
    'wmv': 'mdi-video',
    'flv': 'mdi-video',
    'mkv': 'mdi-video',
    'webm': 'mdi-video',
    'pdf': 'mdi-file-pdf',
    'doc': 'mdi-file-word',
    'docx': 'mdi-file-word',
    'txt': 'mdi-file-document'
  }
  return iconMap[extension || ''] || 'mdi-file'
}

const getFileIconColor = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const colorMap: Record<string, string> = {
    'jpg': 'blue',
    'jpeg': 'blue',
    'png': 'blue',
    'gif': 'blue',
    'webp': 'blue',
    'bmp': 'blue',
    'mp4': 'purple',
    'avi': 'purple',
    'mov': 'purple',
    'wmv': 'purple',
    'flv': 'purple',
    'mkv': 'purple',
    'webm': 'purple',
    'pdf': 'red',
    'doc': 'indigo',
    'docx': 'indigo',
    'txt': 'grey'
  }
  return colorMap[extension || ''] || 'grey'
}

const getFileType = (file: File) => {
  const extension = file.name.split('.').pop()?.toUpperCase()
  return extension || 'FILE'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const showSnackbar = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
  snackbar.value = { show: true, text, color };
}

// Watchers
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})
</script>

<style scoped>
/* Modern Card Styling */
.modern-action-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  overflow: hidden;
}

/* Modern Header */
.modern-header {
  position: relative;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-info)) 100%);
  padding: 24px 32px;
  color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon-wrapper {
  flex-shrink: 0;
}

.header-text {
  flex: 1;
}

.header-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.header-subtitle {
  font-size: 0.95rem;
  opacity: 0.95;
  margin: 0;
  font-weight: 400;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  color: white !important;
}

/* Gradient Divider */
.divider-gradient {
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(var(--v-theme-primary), 0.3) 50%, 
    transparent 100%
  );
  border: none;
}

/* Form Content */
.form-content {
  padding: 32px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

/* Form Sections */
.form-section {
  margin-bottom: 32px;
  animation: fadeInUp 0.4s ease-out;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  letter-spacing: -0.3px;
}

/* Input Cards */
.input-card,
.summary-card,
.notes-card {
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.input-card:hover,
.summary-card:hover,
.notes-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Modern Textarea */
.modern-textarea :deep(.v-field) {
  background: rgb(var(--v-theme-surface));
  transition: all 0.3s ease;
}

.modern-textarea :deep(.v-field:hover) {
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.08);
}

.modern-textarea :deep(.v-field--focused) {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
}

/* Summary Cards */
.summary-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.summary-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgb(var(--v-theme-on-surface));
}

.summary-subtitle {
  font-size: 0.8rem;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.problem-card {
  background: rgba(var(--v-theme-warning), 0.05);
}

.action-card {
  background: rgba(var(--v-theme-success), 0.05);
}

/* Evidence Upload Card */
.evidence-upload-card {
  border: 2px solid rgba(var(--v-theme-primary), 0.1);
  transition: all 0.3s ease;
}

.evidence-upload-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.evidence-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-info), 0.08) 0%, 
    rgba(var(--v-theme-primary), 0.08) 100%
  );
  border-bottom: 1px solid rgba(var(--v-theme-surface-variant), 0.2);
}

.evidence-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgb(var(--v-theme-on-surface));
}

.evidence-subtitle {
  font-size: 0.85rem;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Drop Zone */
.drop-zone {
  border: 3px dashed rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(var(--v-theme-surface-variant), 0.05);
}

.drop-zone:hover {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.05);
  transform: translateY(-2px);
}

.drop-zone-active {
  border-color: rgba(var(--v-theme-primary), 0.6);
  background: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.02);
}

.drop-icon {
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.drop-zone:hover .drop-icon {
  transform: translateY(-4px);
}

.drop-title {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-on-surface));
}

.drop-subtitle {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 20px;
}

.file-types {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* File Preview Section */
.file-preview-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(var(--v-theme-surface-variant), 0.2);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.preview-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: rgb(var(--v-theme-on-surface));
}

.file-list {
  display: grid;
  gap: 12px;
}

.file-item {
  transition: all 0.2s ease;
  animation: slideIn 0.3s ease-out;
}

.file-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.file-info {
  min-width: 0;
}

.file-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 2px;
}

/* Action Footer */
.action-footer {
  padding: 20px 32px;
  background: rgba(var(--v-theme-surface-variant), 0.05);
  border-top: 1px solid rgba(var(--v-theme-surface-variant), 0.2);
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Responsive Design */
@media (max-width: 960px) {
  .form-content {
    padding: 24px 20px;
  }

  .modern-header {
    padding: 20px 24px;
  }

  .header-title {
    font-size: 1.5rem;
  }

  .header-subtitle {
    font-size: 0.875rem;
  }

  .section-title {
    font-size: 1rem;
  }

  .evidence-header {
    padding: 16px 20px;
  }

  .drop-zone {
    padding: 36px 20px;
  }

  .action-footer {
    padding: 16px 20px;
  }
}

@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .form-content {
    padding: 20px 16px;
  }

  .modern-header {
    padding: 16px 20px;
  }

  .header-title {
    font-size: 1.25rem;
  }

  .close-btn {
    top: 12px;
    right: 12px;
  }

  .drop-zone {
    padding: 28px 16px;
  }

  .drop-title {
    font-size: 1rem;
  }

  .drop-subtitle {
    font-size: 0.85rem;
  }

  .action-footer {
    flex-direction: column;
    gap: 12px;
  }

  .action-footer .v-btn {
    width: 100%;
  }
}

/* Dark Mode Enhancements */
.v-theme--dark .modern-action-card {
  border-color: rgba(var(--v-theme-primary), 0.15);
}

.v-theme--dark .modern-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.9) 0%, 
    rgba(var(--v-theme-info), 0.9) 100%
  );
}

.v-theme--dark .evidence-upload-card {
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .drop-zone {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-color: rgba(var(--v-theme-surface-variant), 0.4);
}

.v-theme--dark .drop-zone:hover {
  background: rgba(var(--v-theme-primary), 0.1);
}

.v-theme--dark .action-footer {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-top-color: rgba(var(--v-theme-surface-variant), 0.3);
}

/* Smooth Scrollbar */
.form-content::-webkit-scrollbar {
  width: 8px;
}

.form-content::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 10px;
}

.form-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 10px;
}

.form-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}
</style>