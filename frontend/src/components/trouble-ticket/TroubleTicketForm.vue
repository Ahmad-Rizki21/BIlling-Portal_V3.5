<template>
  <v-dialog v-model="dialog" max-width="1000" persistent scrollable>
    <v-card class="modern-form-card" elevation="0" rounded="xl">
      <!-- Modern Header with Gradient -->
      <div class="modern-header">
        <div class="header-content">
          <div class="header-icon-wrapper">
            <v-avatar :color="isEdit ? 'amber-darken-2' : 'primary'" size="56" class="elevation-4">
              <v-icon :color="'white'" size="32">
                {{ isEdit ? 'mdi-pencil-box' : 'mdi-ticket-confirmation' }}
              </v-icon>
            </v-avatar>
          </div>
          <div class="header-text">
            <h2 class="header-title">
              {{ isEdit ? 'Edit Trouble Ticket' : 'Create New Trouble Ticket' }}
            </h2>
            <p class="header-subtitle">
              {{ isEdit ? 'Update ticket information and track progress' : 'Report and track technical issues efficiently' }}
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
        <v-form ref="formRef" @submit.prevent="handleSubmit" v-model="valid">
          
          <!-- Customer & Technical Data Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-account-network</v-icon>
              <span class="section-title">Customer Information</span>
            </div>
            
            <v-row>
              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="formData.pelanggan_id"
                  label="Customer"
                  :items="uniqueCustomers"
                  item-title="nama"
                  item-value="id"
                  :loading="loadingCustomers"
                  :rules="[v => !!v || 'Customer is required']"
                  clearable
                  @update:modelValue="handleCustomerChange"
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  hide-no-data
                  no-data-text="No customers available"
                  placeholder="Search customer..."
                  auto-select-first
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="primary" size="20">mdi-account-circle</v-icon>
                  </template>
                  <template v-slot:append-inner>
                    <v-chip v-if="formData.pelanggan_id" size="x-small" color="success" variant="flat">
                      <v-icon start size="12">mdi-check</v-icon>
                      Selected
                    </v-chip>
                  </template>
                </v-autocomplete>
              </v-col>

              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="formData.data_teknis_id"
                  label="Technical Data (Optional)"
                  :items="uniqueTechnicalData"
                  item-title="display_name"
                  item-value="id"
                  :loading="loadingTechnicalData"
                  :disabled="!formData.pelanggan_id"
                  clearable
                  :hint="formData.pelanggan_id ? 'Select technical data if available' : 'Select customer first'"
                  persistent-hint
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  placeholder="Search technical data..."
                  auto-select-first
                  hide-no-data
                  no-data-text="No technical data available"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="info" size="20">mdi-server-network</v-icon>
                  </template>
                  
                  <template v-slot:item="{ item, props }">
                    <v-list-item
                      v-bind="props"
                      :title="item.raw.display_name"
                      :subtitle="`OLT: ${item.raw.olt || item.raw.olt_custom || 'N/A'} • PON: ${item.raw.pon || 'N/A'}`"
                      rounded="lg"
                      class="modern-list-item"
                    >
                      <template v-slot:prepend>
                        <v-avatar size="36" color="info" variant="tonal">
                          <v-icon size="18">mdi-network</v-icon>
                        </v-avatar>
                      </template>
                    </v-list-item>
                  </template>
                </v-autocomplete>
              </v-col>
            </v-row>
          </div>

          <!-- Ticket Details Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-text-box</v-icon>
              <span class="section-title">Ticket Details</span>
            </div>

            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="formData.title"
                  label="Title"
                  :rules="[
                    v => !!v || 'Title is required',
                    v => (v && v.length >= 3) || 'Title must be at least 3 characters',
                    v => (v && v.length <= 200) || 'Title must be less than 200 characters'
                  ]"
                  counter="200"
                  placeholder="Brief description of the issue..."
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="primary" size="20">mdi-format-title</v-icon>
                  </template>
                </v-text-field>
              </v-col>

              <v-col cols="12">
                <v-textarea
                  v-model="formData.description"
                  label="Description"
                  :rules="[
                    v => !!v || 'Description is required',
                    v => (v && v.length >= 10) || 'Description must be at least 10 characters'
                  ]"
                  rows="4"
                  auto-grow
                  placeholder="Provide detailed information about the issue..."
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="primary" size="20">mdi-text-box-outline</v-icon>
                  </template>
                </v-textarea>
              </v-col>
            </v-row>
          </div>

          <!-- Classification Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-cog</v-icon>
              <span class="section-title">Classification</span>
            </div>

            <v-row>
              <v-col cols="12" sm="6" md="4">
                <v-select
                  v-model="formData.category"
                  label="Category"
                  :items="categoryOptions"
                  item-title="title"
                  item-value="value"
                  :rules="[v => !!v || 'Category is required']"
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="info" size="20">mdi-tag</v-icon>
                  </template>
                </v-select>
              </v-col>

              <v-col cols="12" sm="6" md="4">
                <v-select
                  v-model="formData.priority"
                  label="Priority"
                  :items="priorityOptions"
                  item-title="title"
                  item-value="value"
                  :rules="[v => !!v || 'Priority is required']"
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon :color="getPriorityColor(formData.priority)" size="20">
                      {{ getPriorityIcon(formData.priority) }}
                    </v-icon>
                  </template>
                  
                  <template v-slot:item="{ item, props }">
                    <v-list-item
                      v-bind="props"
                      :title="item.title"
                      rounded="lg"
                      class="modern-list-item"
                    >
                      <template v-slot:prepend>
                        <v-icon :color="getPriorityColor(item.value)" size="20">
                          {{ getPriorityIcon(item.value) }}
                        </v-icon>
                      </template>
                    </v-list-item>
                  </template>

                  <template v-slot:selection="{ item }">
                    <v-chip :color="getPriorityColor(item.value)" size="small" variant="flat">
                      <v-icon start size="16">{{ getPriorityIcon(item.value) }}</v-icon>
                      {{ item.title }}
                    </v-chip>
                  </template>
                </v-select>
              </v-col>

              <v-col cols="12" sm="12" md="4">
                <v-select
                  v-model="formData.assigned_to"
                  label="Assigned To (Optional)"
                  :items="users"
                  item-title="name"
                  item-value="id"
                  :loading="loadingUsers"
                  clearable
                  hint="Assign to specific user"
                  persistent-hint
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  class="modern-input"
                >
                  <template v-slot:prepend-inner>
                    <v-icon color="primary" size="20">mdi-account-arrow-right</v-icon>
                  </template>
                  
                  <template v-slot:item="{ item, props }">
                    <v-list-item
                      v-bind="props"
                      :title="item.raw.name"
                      :subtitle="item.raw.role?.name || 'No role'"
                      rounded="lg"
                      class="modern-list-item"
                    >
                      <template v-slot:prepend>
                        <v-avatar size="36" color="primary" class="text-white">
                          <span class="text-caption font-weight-bold">{{ getInitials(item.raw.name) }}</span>
                        </v-avatar>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>
            </v-row>
          </div>

          <!-- Evidence Upload Section -->
          <div class="form-section">
            <div class="section-header">
              <v-icon color="primary" size="20">mdi-file-upload</v-icon>
              <span class="section-title">Evidence Upload</span>
              <v-chip size="x-small" color="grey" variant="tonal" class="ml-2">Optional</v-chip>
            </div>

            <v-card variant="outlined" rounded="xl" class="evidence-card">
              <v-card-text class="pa-4">
                <v-file-input
                  v-model="evidenceFiles"
                  label="Select evidence files"
                  multiple
                  accept="image/*,.pdf,.doc,.docx,.txt"
                  prepend-icon="mdi-paperclip"
                  variant="outlined"
                  density="comfortable"
                  rounded="lg"
                  show-size
                  counter
                  hint="Upload screenshots, photos, or documents"
                  persistent-hint
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <v-icon color="info">mdi-paperclip</v-icon>
                  </template>
                </v-file-input>

                <!-- File Preview -->
                <div v-if="evidenceFiles.length > 0" class="mt-4">
                  <div class="d-flex align-center justify-space-between mb-3">
                    <div class="text-subtitle-2 font-weight-bold">
                      <v-icon color="primary" size="18" class="me-1">mdi-file-multiple</v-icon>
                      {{ evidenceFiles.length }} file(s) selected
                    </div>
                    <v-btn
                      size="small"
                      variant="text"
                      color="error"
                      @click="evidenceFiles = []"
                    >
                      Clear All
                    </v-btn>
                  </div>

                  <div class="file-preview-grid">
                    <v-card
                      v-for="(file, index) in evidenceFiles"
                      :key="index"
                      variant="tonal"
                      rounded="lg"
                      class="file-preview-item"
                    >
                      <v-card-text class="pa-3">
                        <div class="d-flex align-center">
                          <v-avatar :color="getFileIconColor(file)" size="40" class="me-3">
                            <v-icon color="white" size="20">{{ getFileIcon(file) }}</v-icon>
                          </v-avatar>
                          <div class="flex-grow-1 text-truncate">
                            <div class="text-body-2 font-weight-medium text-truncate" :title="file.name">
                              {{ file.name }}
                            </div>
                            <div class="text-caption text-medium-emphasis">
                              {{ formatFileSize(file.size) }}
                            </div>
                          </div>
                          <v-btn
                            icon="mdi-close"
                            size="x-small"
                            variant="text"
                            color="error"
                            @click="removeFile(index)"
                          ></v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </div>

          <!-- Customer Information Preview -->
          <v-expand-transition>
            <div v-if="selectedCustomer" class="form-section">
              <div class="section-header">
                <v-icon color="primary" size="20">mdi-information</v-icon>
                <span class="section-title">Customer Preview</span>
              </div>

              <v-card variant="tonal" rounded="xl" class="info-card">
                <v-card-text class="pa-4">
                  <v-row dense>
                    <v-col cols="12" sm="6" md="3">
                      <div class="info-item">
                        <div class="info-label">
                          <v-icon size="14" class="me-1">mdi-account</v-icon>
                          Name
                        </div>
                        <div class="info-value">{{ selectedCustomer.nama }}</div>
                      </div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                      <div class="info-item">
                        <div class="info-label">
                          <v-icon size="14" class="me-1">mdi-map-marker</v-icon>
                          Address
                        </div>
                        <div class="info-value">{{ selectedCustomer.alamat }}</div>
                      </div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                      <div class="info-item">
                        <div class="info-label">
                          <v-icon size="14" class="me-1">mdi-phone</v-icon>
                          Phone
                        </div>
                        <div class="info-value">{{ selectedCustomer.no_telp || '-' }}</div>
                      </div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                      <div class="info-item">
                        <div class="info-label">
                          <v-icon size="14" class="me-1">mdi-tag</v-icon>
                          Brand
                        </div>
                        <v-chip
                          v-if="selectedCustomer.harga_layanan?.brand"
                          size="small"
                          :color="getBrandColor(selectedCustomer.harga_layanan.brand)"
                          variant="flat"
                          rounded="lg"
                        >
                          {{ selectedCustomer.harga_layanan.brand }}
                        </v-chip>
                        <div v-else class="info-value">-</div>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Technical Data Preview -->
                  <div v-if="selectedTechnicalData" class="mt-4 pt-4 border-t">
                    <div class="text-subtitle-2 font-weight-bold mb-3">
                      <v-icon color="info" size="18" class="me-2">mdi-server-network</v-icon>
                      Technical Information
                    </div>
                    <v-row dense>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-ip-network</v-icon>
                            IP Address
                          </div>
                          <div class="info-value font-mono">{{ selectedTechnicalData.ip_pelanggan || '-' }}</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-identifier</v-icon>
                            Customer ID
                          </div>
                          <div class="info-value font-mono">{{ selectedTechnicalData.id_pelanggan || '-' }}</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-server</v-icon>
                            OLT
                          </div>
                          <div class="info-value">{{ selectedTechnicalData.olt || selectedTechnicalData.olt_custom || '-' }}</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-network</v-icon>
                            PON
                          </div>
                          <div class="info-value">{{ selectedTechnicalData.pon || '-' }}</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-lan</v-icon>
                            ODP Port
                          </div>
                          <div class="info-value">{{ selectedTechnicalData.port_odp || '-' }}</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="info-item">
                          <div class="info-label">
                            <v-icon size="14" class="me-1">mdi-barcode</v-icon>
                            Serial Number
                          </div>
                          <div class="info-value font-mono">{{ selectedTechnicalData.sn || '-' }}</div>
                        </div>
                      </v-col>
                    </v-row>
                  </div>

                  <!-- Hint for available technical data -->
                  <v-alert
                    v-if="technicalData.length > 0 && !selectedTechnicalData"
                    type="info"
                    variant="tonal"
                    density="compact"
                    class="mt-4"
                    rounded="lg"
                  >
                    <template v-slot:prepend>
                      <v-icon size="20">mdi-information</v-icon>
                    </template>
                    Technical data available. Select from dropdown to view details.
                  </v-alert>
                </v-card-text>
              </v-card>
            </div>
          </v-expand-transition>
        </v-form>
      </v-card-text>

      <v-divider class="divider-gradient"></v-divider>

      <!-- Modern Action Buttons -->
      <v-card-actions class="action-footer">
        <v-spacer></v-spacer>
        <v-btn
          variant="outlined"
          @click="closeDialog"
          :disabled="loading"
          rounded="xl"
          size="large"
          class="px-6"
        >
          <v-icon start>mdi-close</v-icon>
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="handleSubmit"
          :loading="loading"
          :disabled="!valid"
          rounded="xl"
          size="large"
          class="px-8 elevation-2"
        >
          <v-icon start>{{ isEdit ? 'mdi-content-save' : 'mdi-plus' }}</v-icon>
          {{ isEdit ? 'Update Ticket' : 'Create Ticket' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import apiClient from '@/services/api'

// Props
interface Props {
  modelValue: boolean
  ticket?: any
}

const props = withDefaults(defineProps<Props>(), {
  ticket: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
  'cancelled': []
}>()

// Types
interface Customer {
  id: number
  nama: string
  alamat: string
  no_telp?: string
  harga_layanan?: {
    brand: string
  }
}

interface TechnicalData {
  id: number
  ip_pelanggan: string
  password_pppoe: string
  id_vlan: string
  olt: string
  olt_custom: string
  pon: string
  port_odp: string
  onu_power: number
  sn: string
  id_pelanggan: string
  display_name: string
}

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
const loadingCustomers = ref(false)
const loadingTechnicalData = ref(false)
const loadingUsers = ref(false)

const customers = ref<Customer[]>([])
const technicalData = ref<TechnicalData[]>([])
const users = ref<User[]>([])
const selectedCustomer = ref<Customer | null>(null)
const selectedTechnicalData = ref<TechnicalData | null>(null)

const formData = reactive({
  pelanggan_id: null as number | null,
  data_teknis_id: null as number | null,
  title: '',
  description: '',
  category: '',
  priority: 'medium',
  assigned_to: null as number | null,
  evidence: null as string | null
})

const evidenceFiles = ref<File[]>([])
const snackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' | 'warning' | 'info' })

// Options
const categoryOptions = [
  { title: 'No Connection', value: 'no_connection' },
  { title: 'Slow Connection', value: 'slow_connection' },
  { title: 'Intermittent Connection', value: 'intermittent' },
  { title: 'Hardware Issue', value: 'hardware_issue' },
  { title: 'Cable Issue', value: 'cable_issue' },
  { title: 'ONU Issue', value: 'onu_issue' },
  { title: 'OLT Issue', value: 'olt_issue' },
  { title: 'Mikrotik Issue', value: 'mikrotik_issue' },
  { title: 'Other', value: 'other' }
]

const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Critical', value: 'critical' }
]

// Computed
const dialog= computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.ticket)

// Ensure unique customers for dropdown
const uniqueCustomers = computed(() => {
  const seen = new Set()
  return customers.value.filter(customer => {
    const identifier = `${customer.id}-${customer.nama}`
    if (seen.has(identifier)) {
      return false
    }
    seen.add(identifier)
    return true
  }).sort((a, b) => a.nama.localeCompare(b.nama))
})

// Ensure unique technical data for dropdown
const uniqueTechnicalData = computed(() => {
  const uniqueMap = new Map()
  
  technicalData.value.forEach(item => {
    if (!uniqueMap.has(item.id)) {
      uniqueMap.set(item.id, item)
    }
  })
  
  return Array.from(uniqueMap.values())
})

// Methods
const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

const getBrandColor = (brand: string) => {
  const colors: Record<string, string> = {
    'JAKINET': 'blue',
    'JELANTIK': 'green',
    'JELANTIK NAGRAK': 'purple'
  }
  return colors[brand] || 'primary'
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

const getFileIconColor = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const colorMap: Record<string, string> = {
    'jpg': 'blue',
    'jpeg': 'blue',
    'png': 'blue',
    'gif': 'blue',
    'pdf': 'red',
    'doc': 'indigo',
    'docx': 'indigo',
    'txt': 'grey'
  }
  return colorMap[extension || ''] || 'grey'
}

const fetchCustomers = async () => {
  loadingCustomers.value = true
  try {
    const response = await apiClient.get('/pelanggan?limit=1000&include_relations=true')
    const rawData = response.data.data || response.data || []

    const uniqueCustomers = rawData.reduce((acc: Customer[], current: Customer) => {
      const exists = acc.find(customer => customer.id === current.id)
      if (!exists) {
        acc.push(current)
      }
      return acc
    }, [])

    customers.value = uniqueCustomers
  } catch (error) {
    console.error('Failed to fetch customers:', error)
    customers.value = []
  } finally {
    loadingCustomers.value = false
  }
}

const fetchTechnicalData = async (pelangganId: number) => {
  loadingTechnicalData.value = true
  try {
    const response = await apiClient.get(`/data_teknis/by-pelanggan/${pelangganId}`)
    const rawData = response.data || []

    const uniqueTechnicalData = rawData.reduce((acc: TechnicalData[], current: any) => {
      const exists = acc.find(item => item.id === current.id)
      if (!exists) {
        acc.push({
          ...current,
          display_name: `${current.ip_pelanggan || 'No IP'} - ${current.olt || current.olt_custom || 'No OLT'}`
        })
      }
      return acc
    }, [])

    technicalData.value = uniqueTechnicalData
  } catch (error) {
    console.error('Failed to fetch technical data:', error)
    technicalData.value = []
  } finally {
    loadingTechnicalData.value = false
  }
}

const fetchUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await apiClient.get('/users?limit=1000')
    const rawData = response.data.data || response.data || []

    const uniqueUsersById = rawData.filter((user: any, index: number, self: any[]) =>
      index === self.findIndex((u: any) => u.id === user.id)
    )

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

const handleCustomerChange = (customerId: number | null) => {
  const customer = customerId ? uniqueCustomers.value.find(c => c.id === customerId) || null : null
  selectedCustomer.value = customer
  selectedTechnicalData.value = null
  formData.data_teknis_id = null

  if (customer) {
    fetchTechnicalData(customer.id)
  } else {
    technicalData.value = []
    selectedTechnicalData.value = null
  }
}

const resetForm = () => {
  formData.pelanggan_id = null
  formData.data_teknis_id = null
  formData.title = ''
  formData.description = ''
  formData.category = ''
  formData.priority = 'medium'
  formData.assigned_to = null
  formData.evidence = null

  selectedCustomer.value = null
  selectedTechnicalData.value = null
  technicalData.value = []
  evidenceFiles.value = []

  if (formRef.value) {
    formRef.value.resetValidation()
  }
}

const loadTicketData = () => {
  if (props.ticket) {
    Object.keys(formData).forEach(key => {
      if (key in props.ticket) {
        (formData as any)[key] = (props.ticket as any)[key]
      }
    })

    if (props.ticket.evidence) {
      try {
        const evidenceUrls = JSON.parse(props.ticket.evidence)
        if (Array.isArray(evidenceUrls)) {
          // For editing, we can't recreate File objects from URLs
        }
      } catch (e) {
        console.error('Failed to parse evidence from ticket:', e)
        formData.evidence = props.ticket.evidence
      }
    }

    if (props.ticket.pelanggan) {
      selectedCustomer.value = props.ticket.pelanggan
      fetchTechnicalData(props.ticket.pelanggan.id)
    }

    if (props.ticket.data_teknis) {
      selectedTechnicalData.value = props.ticket.data_teknis
    }
  } else {
    resetForm()
  }
}

const handleSubmit = async () => {
  if (!formRef.value?.validate()) return

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

    const payload: Record<string, any> = {
      ...formData,
      pelanggan_id: typeof formData.pelanggan_id === 'object'
        ? (formData.pelanggan_id as any).id
        : formData.pelanggan_id
    }

    payload.evidence = evidenceUrls.length > 0 ? JSON.stringify(evidenceUrls) : null

    if (isEdit.value) {
      await apiClient.patch(`/trouble-tickets/${props.ticket.id}`, payload)
    } else {
      const response = await apiClient.post('/trouble-tickets', payload)
      console.log('Ticket created with evidence:', response.data)
    }

    emit('saved')
    closeDialog()
  } catch (error) {
    console.error('Failed to save ticket:', error)
    showSnackbar('Failed to save ticket', 'error')
  } finally {
    loading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  emit('cancelled')
}

const removeFile = (index: number) => {
  evidenceFiles.value.splice(index, 1)
}

const getFileIcon = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, string> = {
    'jpg': 'mdi-image',
    'jpeg': 'mdi-image',
    'png': 'mdi-image',
    'gif': 'mdi-image',
    'pdf': 'mdi-file-pdf',
    'doc': 'mdi-file-word',
    'docx': 'mdi-file-word',
    'txt': 'mdi-file-document'
  }
  return iconMap[extension || ''] || 'mdi-file'
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
  if (newValue) {
    loadTicketData()
  }
})

watch(() => formData.data_teknis_id, (newId) => {
  if (newId) {
    selectedTechnicalData.value = uniqueTechnicalData.value.find(t => t.id === newId) || null
  } else {
    selectedTechnicalData.value = null
  }
})

// Lifecycle
onMounted(() => {
  fetchCustomers()
  fetchUsers()
})
</script>

<style scoped>
/* Modern Card Styling */
.modern-form-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  overflow: hidden;
}

/* Modern Header */
.modern-header {
  position: relative;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
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

/* Modern Input Styling */
.modern-input :deep(.v-field) {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-input :deep(.v-field:hover) {
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.08);
}

.modern-input :deep(.v-field--focused) {
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.15);
  transform: translateY(-1px);
}

/* Modern List Items */
.modern-list-item {
  margin: 4px 8px;
  transition: all 0.2s ease;
}

.modern-list-item:hover {
  background: rgba(var(--v-theme-primary), 0.08) !important;
  transform: translateX(4px);
}

/* Evidence Card */
.evidence-card {
  border: 2px dashed rgba(var(--v-theme-primary), 0.2);
  transition: all 0.3s ease;
}

.evidence-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.02);
}

/* File Preview Grid */
.file-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.file-preview-item {
  transition: all 0.2s ease;
  animation: slideIn 0.3s ease-out;
}

.file-preview-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Info Card */
.info-card {
  background: rgba(var(--v-theme-primary), 0.03);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
}

.info-item {
  padding: 8px 0;
}

.info-label {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 6px;
}

.info-value {
  font-size: 0.95rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  word-break: break-word;
}

.font-mono {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-size: 0.9rem;
}

.border-t {
  border-top: 1px solid rgba(var(--v-theme-surface-variant), 0.3);
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

  .file-preview-grid {
    grid-template-columns: 1fr;
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

  .action-footer {
    flex-direction: column;
    gap: 12px;
  }

  .action-footer .v-btn {
    width: 100%;
  }
}

/* Dark Mode Enhancements */
.v-theme--dark .modern-form-card {
  border-color: rgba(var(--v-theme-primary), 0.15);
}

.v-theme--dark .modern-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.9) 0%, 
    rgba(var(--v-theme-secondary), 0.9) 100%
  );
}

.v-theme--dark .evidence-card {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.v-theme--dark .info-card {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.2);
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