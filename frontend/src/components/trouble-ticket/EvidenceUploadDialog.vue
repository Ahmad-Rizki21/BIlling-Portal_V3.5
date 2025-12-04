<template>
  <v-dialog v-model="dialog" max-width="600">
    <v-card>
      <v-card-title class="pa-4 pb-2">
        <v-icon class="me-2" color="info">mdi-file-upload</v-icon>
        Upload Evidence
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-6">
        <v-form ref="formRef" v-model="valid">
          <v-row>
            <v-col cols="12">
              <v-file-input
                v-model="file"
                label="Select Evidence File"
                placeholder="Choose a file..."
                prepend-icon="mdi-paperclip"
                :accept="acceptedTypes"
                :rules="fileRules"
                show-size
                counter
              ></v-file-input>
            </v-col>
          </v-row>

          <v-row v-if="previewUrl">
            <v-col cols="12">
              <div class="text-subtitle-2">Preview:</div>
              <div v-if="isImage" class="mt-2">
                <v-img
                  :src="previewUrl"
                  max-height="300"
                  contain
                  class="rounded border"
                  eager
                  loading="lazy"
                />
              </div>
              <div v-else-if="isVideo" class="mt-2">
                <video 
                  :src="previewUrl" 
                  controls 
                  style="max-width: 100%; max-height: 300px;"
                  class="rounded border"
                />
              </div>
              <div v-else class="mt-2">
                <v-icon size="48" color="info">mdi-file</v-icon>
                <div class="mt-2">{{ file && file.length > 0 ? file[0].name : 'No file selected' }}</div>
              </div>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="description"
                label="Description (Optional)"
                placeholder="Describe what this evidence shows..."
                rows="2"
                auto-grow
              ></v-textarea>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="submitForm"
          :loading="loading"
          :disabled="!valid || !file || file.length === 0"
        >
          Upload Evidence
        </v-btn>
      </v-card-actions>
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
const acceptedTypes = 'image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx'
const maxFileSize = 10 * 1024 * 1024 // 10MB

// State
const loading = ref(false)
const valid = ref(false)
const formRef = ref()
const file = ref<File[]>([]) // v-file-input returns an array
const description = ref('')
const previewUrl = ref<string | null>(null)

// Computed
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const fileRules = computed(() => [
  (files: File[]) => {
    if (!files || files.length === 0) return 'File is required'
    return true
  },
  (files: File[]) => {
    if (!files || files.length === 0) return true
    const file = files[0]
    if (file.size > maxFileSize) {
      return `File size must be less than ${Math.round(maxFileSize / 1024 / 1024)}MB`
    }
    return true
  }
])

const isImage = computed(() => {
  return file.value && file.value.length > 0 && file.value[0].type.startsWith('image/')
})

const isVideo = computed(() => {
  return file.value && file.value.length > 0 && file.value[0].type.startsWith('video/')
})

// Methods
const submitForm = async () => {
  if (!file.value || file.value.length === 0) {
    showSnackbar('Please select a file', 'error')
    return
  }

  if (!props.ticketId) {
    showSnackbar('Ticket ID is required', 'error')
    return
  }

  const selectedFile = file.value[0]

  if (!selectedFile) {
    showSnackbar('Please select a file to upload', 'error')
    return
  }

  loading.value = true
  try {
    // Create FormData for file upload
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('ticket_id', props.ticketId.toString())
    if (description.value) {
      formData.append('description', description.value)
    }

    // Upload file to server first
    const uploadResponse = await apiClient.post('/trouble-tickets/upload-evidence', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Then create action with the uploaded file URL
    await apiClient.post(`/trouble-tickets/${props.ticketId}/action`, {
      action_description: `Evidence uploaded: ${selectedFile.name}`,
      summary_problem: description.value || 'Evidence file uploaded',
      summary_action: 'Added evidence file to ticket',
      evidence: uploadResponse.data.file_url, // Use the URL returned from server
      notes: description.value
    })

    showSnackbar('Evidence uploaded successfully', 'success')
    emit('updated')
    closeDialog()
  } catch (error) {
    console.error('Failed to upload evidence:', error)
    showSnackbar('Failed to upload evidence', 'error')
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  resetForm()
}

const resetForm = () => {
  file.value = []
  description.value = ''
  previewUrl.value = null
}

// Snackbar state
const snackbar = ref({
  show: false,
  text: '',
  color: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Snackbar function
const showSnackbar = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
  snackbar.value = { show: true, text, color }
}

// Watchers
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})

watch(file, (newFile) => {
  if (newFile && newFile.length > 0) {
    // Create a preview URL for the selected file
    previewUrl.value = URL.createObjectURL(newFile[0])
  } else {
    previewUrl.value = null
  }
}, { deep: true })
</script>