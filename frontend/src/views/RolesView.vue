<template>
  <v-container fluid class="pa-6">
    <!-- Header Section -->
    <div class="d-flex align-center mb-6">
      <div class="d-flex align-center">
        <v-avatar class="me-3" color="primary" size="40">
          <v-icon color="white">mdi-shield-account</v-icon>
        </v-avatar>
        <div>
          <h1 class="text-h4 font-weight-bold text-primary">Role Management</h1>
          <p class="text-subtitle-1 text-medium-emphasis mb-0">Kelola roles dan permissions sistem</p>
        </div>
      </div>
      <v-spacer></v-spacer>
      <v-btn 
        color="primary" 
        size="large"
        elevation="2"
        @click="openDialog()"
        prepend-icon="mdi-plus"
        class="text-none"
      >
        Tambah Role
      </v-btn>
    </div>

    <!-- Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="primary" variant="tonal">
          <v-icon size="32" color="primary" class="mb-2">mdi-shield-check</v-icon>
          <div class="text-h5 font-weight-bold">{{ roles.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Total Roles</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="success" variant="tonal">
          <v-icon size="32" color="success" class="mb-2">mdi-key</v-icon>
          <div class="text-h5 font-weight-bold">{{ allPermissions.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Total Permissions</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Main Data Table Card -->
    <v-card elevation="3" class="rounded-lg">
      <v-card-title class="d-flex align-center pa-6 bg-grey-lighten-5">
        <v-icon start icon="mdi-format-list-bulleted-square" color="primary"></v-icon>
        <span class="text-h6 font-weight-bold">Daftar Roles</span>
        <v-spacer></v-spacer>
        <v-chip color="primary" variant="outlined" size="small">
          {{ roles.length }} roles
        </v-chip>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="roles"
        :loading="loading"
        item-value="id"
        class="elevation-0"
        :items-per-page="10"
        loading-text="Memuat data roles..."
        no-data-text="Tidak ada data roles"
      >
        <template v-slot:loading>
          <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
        </template>

        <template v-slot:item.row_number="{ index }">
          <v-chip size="small" color="blue-grey" variant="outlined">
            {{ index + 1 }}
          </v-chip>
        </template>

        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <v-avatar size="32" color="primary" class="me-3">
              <v-icon color="white" size="18">mdi-shield</v-icon>
            </v-avatar>
            <div>
              <div class="font-weight-bold">{{ item.name }}</div>
              <div class="text-caption text-medium-emphasis">Role ID: {{ item.id }}</div>
            </div>
          </div>
        </template>
        
        <template v-slot:item.permissions_count="{ item }">
          <v-chip 
            size="small" 
            :color="item.permissions.length > 5 ? 'success' : item.permissions.length > 2 ? 'warning' : 'error'"
            variant="tonal"
            class="font-weight-bold"
          >
            <v-icon start size="16">mdi-key-variant</v-icon>
            {{ item.permissions.length }} Permissions
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex justify-center ga-2">
            <v-btn 
              size="small" 
              variant="tonal" 
              color="primary" 
              @click="openDialog(item)"
              class="text-none"
            >
              <v-icon start size="16">mdi-pencil</v-icon>
              Edit
            </v-btn>
            <v-btn 
              size="small" 
              variant="tonal" 
              color="error" 
              @click="openDeleteDialog(item)"
              class="text-none"
            >
              <v-icon start size="16">mdi-delete</v-icon>
              Hapus
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Enhanced Add/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="900px" persistent scrollable>
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center pa-6 bg-primary text-white">
          <v-icon :icon="formTitle.icon" start class="me-3"></v-icon>
          <div>
            <div class="text-h5 font-weight-bold">{{ formTitle.text }}</div>
            <div class="text-body-2 text-white text-medium-emphasis">
              {{ editedIndex === -1 ? 'Buat role baru dengan permissions' : 'Ubah informasi role dan permissions' }}
            </div>
          </div>
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="closeDialog" color="white">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-6">
          <v-container fluid>
            <!-- Role Name Input -->
            <div class="mb-6">
              <v-text-field
                v-model="editedItem.name"
                label="Nama Role"
                variant="outlined"
                :rules="[v => !!v || 'Nama role tidak boleh kosong']"
                required
                prepend-inner-icon="mdi-shield"
                placeholder="Masukkan nama role"
                class="mb-4"
                hide-details="auto"
              ></v-text-field>
            </div>

            <!-- Permissions Section -->
            <div class="mb-4">
              <div class="d-flex align-center mb-4">
                <v-icon color="primary" class="me-2">mdi-key-variant</v-icon>
                <h3 class="text-h6 font-weight-bold text-primary">Hak Akses (Permissions)</h3>
                <v-spacer></v-spacer>
                <v-chip size="small" color="primary" variant="outlined">
                  {{ selectedPermissions.length }} dipilih
                </v-chip>
              </div>
              
              <div v-if="!allPermissions.length && loading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
                <p class="mt-4 text-body-1">Memuat permissions...</p>
              </div>

              <div v-else>
                <!-- Select All Controls -->
                <div class="mb-4 pa-4 bg-grey-lighten-5 rounded">
                  <div class="d-flex align-center">
                    <v-checkbox
                      :model-value="selectedPermissions.length === allPermissions.length"
                      :indeterminate="selectedPermissions.length > 0 && selectedPermissions.length < allPermissions.length"
                      @update:model-value="toggleAllPermissions"
                      label="Pilih Semua Permissions"
                      density="compact"
                      color="primary"
                      hide-details
                    ></v-checkbox>
                    <v-spacer></v-spacer>
                    <v-btn 
                      size="small" 
                      variant="text" 
                      color="error" 
                      @click="clearAllPermissions"
                      class="text-none"
                    >
                      <v-icon start size="16">mdi-close</v-icon>
                      Clear All
                    </v-btn>
                  </div>
                </div>

                <!-- Permissions Grid -->
                <v-row>
                  <v-col 
                    v-for="(permissions, groupName) in groupedPermissions" 
                    :key="groupName" 
                    cols="12" 
                    md="6" 
                    lg="4"
                  >
                    <v-card 
                      class="permission-group pa-4 h-100" 
                      variant="outlined"
                      :color="getGroupColor(permissions, selectedPermissions)"
                    >
                      <div class="d-flex align-center mb-3">
                        <v-icon :color="getGroupColor(permissions, selectedPermissions)" class="me-2">
                          {{ getGroupIcon(String(groupName)) }}
                        </v-icon>
                        <h4 class="text-subtitle-1 font-weight-bold text-capitalize">
                          {{ String(groupName).replace('_', ' ') }}
                        </h4>
                        <v-spacer></v-spacer>
                        <v-chip size="x-small" variant="outlined">
                          {{ getSelectedInGroup(permissions, selectedPermissions) }}/{{ permissions.length }}
                        </v-chip>
                      </div>
                      
                      <div class="permission-list">
                        <v-checkbox
                          v-for="permission in permissions"
                          :key="permission.id"
                          v-model="selectedPermissions"
                          :label="formatPermissionName(permission.name)"
                          :value="permission.id"
                          density="compact"
                          color="primary"
                          hide-details
                          class="mb-1"
                        ></v-checkbox>
                      </div>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </div>
          </v-container>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-6">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            @click="closeDialog"
            size="large"
            class="text-none me-3"
          >
            Batal
          </v-btn>
          <v-btn 
            color="primary" 
            variant="flat" 
            @click="saveRole"
            size="large"
            class="text-none"
            :loading="saving"
          >
            <v-icon start>mdi-content-save</v-icon>
            {{ editedIndex === -1 ? 'Buat Role' : 'Simpan Perubahan' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Enhanced Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="rounded-lg">
        <v-card-title class="text-h5 text-center pt-8 text-error">
          <v-icon size="48" color="error" class="mb-4">mdi-alert-circle</v-icon>
          <br>
          Konfirmasi Hapus
        </v-card-title>
        <v-card-text class="text-center pa-6">
          <p class="text-body-1 mb-4">
            Anda akan menghapus role <strong class="text-error">{{ itemToDelete?.name }}</strong>
          </p>
          <v-alert type="warning" variant="tonal" class="text-start">
            <v-icon start>mdi-warning</v-icon>
            Tindakan ini tidak dapat dibatalkan dan akan menghapus semua permission yang terkait.
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-6">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            @click="closeDeleteDialog"
            size="large"
            class="text-none me-3"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmDelete"
            size="large"
            class="text-none"
            :loading="deleting"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus Role
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';

// --- State ---
const roles = ref<any[]>([]);
const allPermissions = ref<any[]>([]);
const selectedPermissions = ref<number[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const editedIndex = ref(-1);
const editedItem = ref<{id: number | null, name: string}>({ id: null, name: '' });
const itemToDelete = ref<any>(null);

// --- Headers ---
const headers = [
  { title: 'No.', key: 'row_number', sortable: false, width: '80px', align: 'center' },
  { title: 'Role Information', key: 'name', sortable: true },
  { title: 'Permissions', key: 'permissions_count', sortable: false, align: 'center', width: '180px' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center', width: '200px' },
] as const;

// --- Computed Properties ---
const formTitle = computed(() => {
  return editedIndex.value === -1 
    ? { text: 'Tambah Role Baru', icon: 'mdi-shield-plus' }
    : { text: 'Edit Role', icon: 'mdi-shield-edit' };
});

const groupedPermissions = computed(() => {
  return allPermissions.value.reduce((groups, permission) => {
    const groupName = permission.name.split('_').pop() || 'lainnya';
    if (!groups[groupName]) {
      groups[groupName] = [];
    }
    groups[groupName].push(permission);
    return groups;
  }, {} as Record<string, any[]>);
});

// --- Helper Methods ---
function formatPermissionName(name: string): string {
  return name.split('_')[0].replace(/([A-Z])/g, ' $1').trim();
}

function getGroupIcon(groupName: string): string {
  const iconMap: Record<string, string> = {
    'users': 'mdi-account-group',
    'roles': 'mdi-shield-account',
    'permissions': 'mdi-key-variant',
    'dashboard': 'mdi-view-dashboard',
    'settings': 'mdi-cog',
    'lainnya': 'mdi-dots-horizontal'
  };
  return iconMap[groupName.toLowerCase()] || 'mdi-key';
}

function getGroupColor(permissions: any[], selectedPermissions: number[]): string {
  const selectedInGroup = permissions.filter(p => selectedPermissions.includes(p.id)).length;
  if (selectedInGroup === permissions.length) return 'success';
  if (selectedInGroup > 0) return 'warning';
  return 'grey';
}

function getSelectedInGroup(permissions: any[], selectedPermissions: number[]): number {
  return permissions.filter(p => selectedPermissions.includes(p.id)).length;
}

function toggleAllPermissions(value: boolean | null) {
  // Logika ini sudah benar, karena jika value adalah null, akan dianggap false.
  selectedPermissions.value = value ? allPermissions.value.map(p => p.id) : [];
}

function clearAllPermissions() {
  selectedPermissions.value = [];
}

// --- Lifecycle ---
onMounted(() => {
  fetchRoles();
  fetchAllPermissions();
});

// --- Methods: API ---
async function fetchRoles() {
  loading.value = true;
  try {
    const response = await apiClient.get('/roles/');
    roles.value = response.data;
  } catch (error) { 
    console.error('Gagal mengambil data roles:', error); 
  } finally { 
    loading.value = false; 
  }
}

async function fetchAllPermissions() {
  try {
    const response = await apiClient.get('/permissions/');
    allPermissions.value = response.data;
  } catch (error) { 
    console.error('Gagal mengambil data permissions:', error); 
  }
}

// --- Methods: Dialog Tambah/Edit ---
function openDialog(item?: any) {
  if (item) {
    editedIndex.value = roles.value.indexOf(item);
    editedItem.value = { ...item };
    selectedPermissions.value = item.permissions.map((p: any) => p.id);
  } else {
    editedIndex.value = -1;
    editedItem.value = { id: null, name: '' };
    selectedPermissions.value = [];
  }
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedIndex.value = -1;
  editedItem.value = { id: null, name: '' };
  selectedPermissions.value = [];
}

async function saveRole() {
  saving.value = true;
  const payload = {
    name: editedItem.value.name,
    permission_ids: selectedPermissions.value,
  };

  try {
    if (editedIndex.value > -1) {
      await apiClient.patch(`/roles/${editedItem.value.id}`, payload);
    } else {
      await apiClient.post('/roles/', payload);
    }
    fetchRoles();
    closeDialog();
  } catch (error) { 
    console.error('Gagal menyimpan role:', error); 
  } finally {
    saving.value = false;
  }
}

// --- Methods: Dialog Hapus ---
function openDeleteDialog(item: any) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  itemToDelete.value = null;
  dialogDelete.value = false;
}

async function confirmDelete() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/roles/${itemToDelete.value.id}`);
    fetchRoles();
  } catch (error) {
    console.error('Gagal menghapus role:', error);
  } finally {
    deleting.value = false;
    closeDeleteDialog();
  }
}
</script>

<style scoped>
.permission-group {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px !important;
}

.permission-group:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.permission-list {
  max-height: 200px;
  overflow-y: auto;
}

.permission-list::-webkit-scrollbar {
  width: 4px;
}

.permission-list::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 2px;
}

.permission-list::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 2px;
}

.permission-list::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.v-data-table ::v-deep(.v-data-table__wrapper) {
  border-radius: 0 0 12px 12px;
}

.v-card {
  transition: all 0.3s ease;
}

.v-btn {
  transition: all 0.2s ease;
}

.v-btn:hover {
  transform: translateY(-1px);
}
</style>