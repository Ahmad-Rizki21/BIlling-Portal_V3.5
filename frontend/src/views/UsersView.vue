<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar class="me-4 elevation-4" color="primary" size="80">
              <v-icon color="white" size="40">mdi-account-group</v-icon>
            </v-avatar>
            <div>
              <h1 class="text-h4 font-weight-bold text-white mb-2">User Management</h1>
              <p class="header-subtitle mb-0">
                Kelola pengguna dan assign roles
              </p>
            </div>
            <v-spacer></v-spacer>
            <v-btn 
              color="primary" 
              size="large"
              elevation="2"
              @click="openDialog()"
              prepend-icon="mdi-account-plus"
              class="text-none rounded-lg"
            >
              Tambah User
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="success" variant="tonal">
          <v-icon size="32" color="success" class="mb-2">mdi-account-check</v-icon>
          <div class="text-h5 font-weight-bold">{{ users.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Total Users</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="primary" variant="tonal">
          <v-icon size="32" color="primary" class="mb-2">mdi-shield-account</v-icon>
          <div class="text-h5 font-weight-bold">{{ activeRolesCount }}</div>
          <div class="text-body-2 text-medium-emphasis">Active Roles</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="warning" variant="tonal">
          <v-icon size="32" color="warning" class="mb-2">mdi-account-alert</v-icon>
          <div class="text-h5 font-weight-bold">{{ usersWithoutRole }}</div>
          <div class="text-body-2 text-medium-emphasis">No Role Assigned</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2" color="info" variant="tonal">
          <v-icon size="32" color="info" class="mb-2">mdi-clock</v-icon>
          <div class="text-h5 font-weight-bold">{{ recentUsersCount }}</div>
          <div class="text-body-2 text-medium-emphasis">Recent Users</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Search and Filter Section -->
    <v-card class="mb-4" elevation="1">
      <v-card-text class="pa-4">
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              label="Cari user..."
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterRole"
              :items="roleFilterItems"
              label="Filter by Role"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" md="2">
            <v-btn
              variant="outlined"
              @click="clearFilters"
              class="text-none"
              block
            >
              <v-icon start>mdi-filter-remove</v-icon>
              Clear
            </v-btn>
          </v-col>
          <v-col cols="12" md="2">
            <v-btn
              variant="flat"
              color="primary"
              @click="refreshData"
              class="text-none"
              block
              :loading="loading"
            >
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Main Data Table Card -->
    <v-card elevation="3" class="rounded-lg">
      <v-card-title class="d-flex align-center pa-6 bg-grey-lighten-5">
        <v-icon start icon="mdi-account-multiple" color="success"></v-icon>
        <span class="text-h6 font-weight-bold">Daftar Users</span>
        <v-spacer></v-spacer>
        <v-chip color="success" variant="outlined" size="small">
          {{ filteredUsers.length }} users
        </v-chip>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="filteredUsers"
        :loading="loading"
        item-value="id"
        class="elevation-0"
        :items-per-page="10"
        loading-text="Memuat data users..."
        no-data-text="Tidak ada data users"
      >
        <template v-slot:loading>
          <SkeletonLoader type="table" :rows="5" />
        </template>

        <template v-slot:item.row_number="{ index }">
          <v-chip size="small" color="blue-grey" variant="outlined">
            {{ index + 1 }}
          </v-chip>
        </template>

        <template v-slot:item.user_info="{ item }">
          <div class="d-flex align-center py-2">
            <v-avatar size="40" :color="getAvatarColor(item.name)" class="me-3">
              <span class="text-white font-weight-bold">{{ getInitials(item.name) }}</span>
            </v-avatar>
            <div>
              <div class="font-weight-bold text-body-1">{{ item.name }}</div>
              <div class="text-body-2 text-medium-emphasis">{{ item.email }}</div>
            </div>
          </div>
        </template>

        <template v-slot:item.role="{ item }">
          <v-chip 
            :color="getRoleById(item.role_id) ? 'success' : 'warning'" 
            :variant="getRoleById(item.role_id) ? 'tonal' : 'outlined'"
            size="small"
            class="font-weight-bold"
          >
            <v-icon 
              start 
              size="14"
              :icon="getRoleById(item.role_id) ? 'mdi-shield-check' : 'mdi-shield-alert'"
            ></v-icon>
            {{ getRoleById(item.role_id)?.name || 'No Role' }}
          </v-chip>
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip 
            :color="getStatusColor(item)" 
            size="small"
            variant="tonal"
            class="font-weight-bold"
          >
            <v-icon start size="14">{{ getStatusIcon(item) }}</v-icon>
            {{ getStatusText(item) }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex justify-center ga-1">
            <v-btn 
              size="small" 
              variant="tonal" 
              color="primary" 
              @click="openDialog(item)"
              class="text-none"
            >
              <v-icon size="16">mdi-pencil</v-icon>
            </v-btn>
            <v-btn 
              size="small" 
              variant="tonal" 
              color="info" 
              @click="viewUserDetail(item)"
              class="text-none"
            >
              <v-icon size="16">mdi-eye</v-icon>
            </v-btn>
            <v-btn 
              size="small" 
              variant="tonal" 
              color="error" 
              @click="openDeleteDialog(item)"
              class="text-none"
            >
              <v-icon size="16">mdi-delete</v-icon>
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Enhanced Add/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="700px" persistent scrollable>
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center pa-6 bg-success text-white">
          <v-icon :icon="formTitle.icon" start class="me-3"></v-icon>
          <div>
            <div class="text-h5 font-weight-bold">{{ formTitle.text }}</div>
            <div class="text-body-2 text-white text-medium-emphasis">
              {{ editedIndex === -1 ? 'Tambahkan user baru ke sistem' : 'Ubah informasi user dan role' }}
            </div>
          </div>
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="closeDialog" color="white">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-6">
          <v-container fluid>
            <v-row>
              <!-- Personal Information Section -->
              <v-col cols="12">
                <div class="d-flex align-center mb-4">
                  <v-icon color="success" class="me-2">mdi-account-circle</v-icon>
                  <h3 class="text-h6 font-weight-bold text-success">Informasi Personal</h3>
                </div>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="editedItem.name" 
                  label="Nama Lengkap" 
                  variant="outlined"
                  prepend-inner-icon="mdi-account"
                  :rules="[v => !!v || 'Nama lengkap wajib diisi']"
                  required
                  placeholder="Masukkan nama lengkap"
                  hide-details="auto"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="editedItem.email" 
                  label="Email Address" 
                  type="email" 
                  variant="outlined"
                  prepend-inner-icon="mdi-email"
                  :rules="emailRules"
                  required
                  placeholder="user@example.com"
                  hide-details="auto"
                ></v-text-field>
              </v-col>

              <!-- Security Section -->
              <v-col cols="12" class="mt-4">
                <div class="d-flex align-center mb-4">
                  <v-icon color="warning" class="me-2">mdi-shield-key</v-icon>
                  <h3 class="text-h6 font-weight-bold text-warning">Keamanan</h3>
                </div>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedItem.password"
                  label="Password"
                  type="password"
                  variant="outlined"
                  prepend-inner-icon="mdi-lock"
                  :placeholder="editedIndex > -1 ? 'Kosongkan jika tidak ingin mengubah' : 'Contoh: MyPassword123!'"
                  :rules="passwordRules"
                  hide-details="auto"
                >
                  <template v-slot:append-inner v-if="editedIndex === -1">
                    <v-tooltip>
                      <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" color="info" size="20">mdi-information</v-icon>
                      </template>
                      <div>Password harus mengandung:</div>
                      <div>• Minimal 8 karakter</div>
                      <div>• Huruf kapital (A-Z)</div>
                      <div>• Huruf kecil (a-z)</div>
                      <div>• Angka (0-9)</div>
                      <div>• Karakter khusus (!@#$%^&*)</div>
                      <div>• Tanpa spasi</div>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-select
                  v-model="editedItem.role_id"
                  :items="roleSelectItems"
                  item-title="title"
                  item-value="value"
                  label="Assign Role"
                  variant="outlined"
                  prepend-inner-icon="mdi-shield-account"
                  placeholder="Pilih role untuk user"
                  hide-details="auto"
                  clearable
                >
                  <template v-slot:selection="{ item }">
                    <v-chip size="small" color="primary" variant="tonal">
                      <v-icon start size="14">mdi-shield</v-icon>
                      {{ item.title }}
                    </v-chip>
                  </template>
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props" :title="item.title">
                      <template v-slot:prepend>
                        <v-avatar size="32" color="primary">
                          <v-icon color="white" size="16">mdi-shield</v-icon>
                        </v-avatar>
                      </template>
                      <v-list-item-subtitle>Role ID: {{ item.value }}</v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>

              <!-- Preview Section for Edit -->
              <v-col cols="12" v-if="editedIndex > -1" class="mt-4">
                <div class="d-flex align-center mb-4">
                  <v-icon color="info" class="me-2">mdi-information</v-icon>
                  <h3 class="text-h6 font-weight-bold text-info">Preview</h3>
                </div>
                <v-card variant="outlined" color="info">
                  <v-card-text class="pa-4">
                    <div class="d-flex align-center">
                      <v-avatar size="40" :color="getAvatarColor(editedItem.name)" class="me-3">
                        <span class="text-white font-weight-bold">{{ getInitials(editedItem.name) }}</span>
                      </v-avatar>
                      <div>
                        <div class="font-weight-bold">{{ editedItem.name }}</div>
                        <div class="text-body-2 text-medium-emphasis">{{ editedItem.email }}</div>
                        <v-chip 
                          size="x-small" 
                          :color="editedItem.role_id ? 'success' : 'warning'"
                          variant="tonal"
                          class="mt-1"
                        >
                          {{ getRoleName(editedItem.role_id) || 'No Role' }}
                        </v-chip>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
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
            @click="saveUser"
            size="large"
            class="text-none"
            :loading="saving"
          >
            <v-icon start>mdi-content-save</v-icon>
            {{ editedIndex === -1 ? 'Buat User' : 'Simpan Perubahan' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Enhanced Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="rounded-lg">
        <v-card-title class="text-h5 text-center pt-8 text-error">
          <v-icon size="48" color="error" class="mb-4">mdi-account-remove</v-icon>
          <br>
          Konfirmasi Hapus User
        </v-card-title>
        <v-card-text class="text-center pa-6">
          <div v-if="itemToDelete" class="mb-4">
            <v-avatar size="60" :color="getAvatarColor(itemToDelete.name)" class="mb-3">
              <span class="text-h5 font-weight-bold text-white">{{ getInitials(itemToDelete.name) }}</span>
            </v-avatar>
            <p class="text-body-1 mb-2">
              Anda akan menghapus user:
            </p>
            <p class="text-h6 font-weight-bold text-error">{{ itemToDelete.name }}</p>
            <p class="text-body-2 text-medium-emphasis">{{ itemToDelete.email }}</p>
          </div>
          <v-alert type="warning" variant="tonal" class="text-start">
            <v-icon start>mdi-warning</v-icon>
            Tindakan ini tidak dapat dibatalkan dan akan menghapus semua data yang terkait dengan user ini.
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
            Ya, Hapus User
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- User Detail Dialog -->
    <v-dialog v-model="dialogDetail" max-width="600px">
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center pa-6 bg-info text-white">
          <v-icon start class="me-3">mdi-account-details</v-icon>
          <div>
            <div class="text-h5 font-weight-bold">Detail User</div>
            <div class="text-body-2 text-white text-medium-emphasis">
              Informasi lengkap user
            </div>
          </div>
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="dialogDetail = false" color="white">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-6" v-if="selectedUser">
          <div class="text-center mb-6">
            <v-avatar size="80" :color="getAvatarColor(selectedUser.name)" class="mb-3">
              <span class="text-h4 font-weight-bold text-white">{{ getInitials(selectedUser.name) }}</span>
            </v-avatar>
            <h2 class="text-h5 font-weight-bold">{{ selectedUser.name }}</h2>
            <p class="text-body-1 text-medium-emphasis">{{ selectedUser.email }}</p>
          </div>

          <v-divider class="mb-4"></v-divider>

          <v-row>
            <v-col cols="6">
              <v-card variant="outlined" class="pa-3">
                <div class="text-center">
                  <v-icon size="24" color="primary" class="mb-2">mdi-identifier</v-icon>
                  <div class="text-body-2 text-medium-emphasis">User ID</div>
                  <div class="text-h6 font-weight-bold">{{ selectedUser.id }}</div>
                </div>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card variant="outlined" class="pa-3">
                <div class="text-center">
                  <v-icon size="24" :color="getRoleById(selectedUser.role_id) ? 'success' : 'warning'" class="mb-2">
                    {{ getRoleById(selectedUser.role_id) ? 'mdi-shield-check' : 'mdi-shield-alert' }}
                  </v-icon>
                  <div class="text-body-2 text-medium-emphasis">Role</div>
                  <div class="text-h6 font-weight-bold">{{ getRoleById(selectedUser.role_id)?.name || 'No Role' }}</div>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <div v-if="getRoleById(selectedUser.role_id)?.permissions?.length" class="mt-4">
            <h4 class="text-h6 font-weight-bold mb-3">Permissions</h4>
            <div class="d-flex flex-wrap ga-2">
              <v-chip 
                v-for="permission in getRoleById(selectedUser.role_id).permissions" 
                :key="permission.id"
                size="small"
                color="primary"
                variant="outlined"
              >
                <v-icon start size="14">mdi-key-variant</v-icon>
                {{ formatPermissionName(permission.name) }}
              </v-chip>
            </div>
          </div>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            variant="outlined" 
            @click="dialogDetail = false"
            class="text-none"
          >
            Tutup
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import apiClient from '@/services/api';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

// --- State ---
const users = ref<any[]>([]);
const roles = ref<any[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const dialogDetail = ref(false);
const editedIndex = ref(-1);
const selectedUser = ref<any>(null);
const itemToDelete = ref<any>(null);
const searchQuery = ref('');
const filterRole = ref<string | null>(null);

const defaultItem = { id: null, name: '', email: '', password: '', role_id: null };
const editedItem = ref<{
  id: number | null;
  name: string;
  email: string;
  password: string;
  role_id: string | null;
}>({ ...defaultItem });

// --- Headers ---
const headers = [
  { title: 'No.', key: 'row_number', sortable: false, width: '80px', align: 'center' },
  { title: 'User Information', key: 'user_info', sortable: true },
  { title: 'Role', key: 'role', sortable: false, align: 'center', width: '150px' },
  { title: 'Status', key: 'status', sortable: false, align: 'center', width: '120px' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center', width: '150px' },
] as const;

// --- Computed Properties ---
const formTitle = computed(() => ({
  text: editedIndex.value === -1 ? 'Tambah User Baru' : 'Edit User',
  icon: editedIndex.value === -1 ? 'mdi-account-plus' : 'mdi-account-edit'
}));

const filteredUsers = computed(() => {
  let filtered = users.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(user =>
      user.name.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
    );
  }

  if (filterRole.value) {
    if (filterRole.value === 'no-role') {
      filtered = filtered.filter(user => !user.role_id);
    } else {
      filtered = filtered.filter(user => user.role_id?.toString() === filterRole.value);
    }
  }

  return filtered;
});

const roleFilterItems = computed(() => {
  const items = roles.value.map(role => ({
    title: role.name,
    value: role.id.toString()
  }));
  items.unshift({ title: 'No Role Assigned', value: 'no-role' });
  return items;
});

const roleSelectItems = computed(() => {
  return roles.value.map(role => ({
    title: role.name,
    value: role.id.toString()
  }));
});

const activeRolesCount = computed(() => {
  return roles.value.length;
});

const usersWithoutRole = computed(() => {
  return users.value.filter(user => !user.role_id).length;
});

const recentUsersCount = computed(() => {
  return Math.min(users.value.length, 5);
});

// --- Validation Rules ---
const emailRules = [
  (v: string) => !!v || 'Email wajib diisi',
  (v: string) => /.+@.+\..+/.test(v) || 'Email harus valid',
];

const passwordRules = computed(() => {
  const rules: ((v: string) => boolean | string)[] = [];

  // For new users, the password is required.
  if (editedIndex.value === -1) {
    rules.push((v: string) => !!v || 'Password wajib diisi untuk user baru');
  }

  // If a password is entered (for new or existing users), enforce complexity rules.
  if (editedItem.value.password) {
    rules.push((v: string) => v.length >= 8 || 'Password minimal 8 karakter');
    rules.push((v: string) => /[A-Z]/.test(v) || 'Password harus mengandung minimal 1 huruf kapital');
    rules.push((v: string) => /[a-z]/.test(v) || 'Password harus mengandung minimal 1 huruf kecil');
    rules.push((v: string) => /[0-9]/.test(v) || 'Password harus mengandung minimal 1 angka');
    rules.push((v: string) => /[!@#$%^&*(),.?":{}|<>]/.test(v) || 'Password harus mengandung minimal 1 karakter khusus');
    rules.push((v: string) => !/\s/.test(v) || 'Password tidak boleh mengandung spasi');
  }

  return rules;
});

// --- Helper Methods ---
function getRoleById(roleId: number | string | null): any | null {
  if (!roleId) return null;
  const idToFind = roleId.toString();
  return roles.value.find(r => r.id.toString() === idToFind) || null;
}

function getInitials(name: string): string {
  if (!name) return '';
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function getAvatarColor(name: string): string {
  if (!name) return 'grey';
  const colors = ['primary', 'success', 'info', 'warning', 'error', 'purple', 'teal', 'orange'];
  const index = name.length % colors.length;
  return colors[index];
}

function getStatusColor(user: any): string {
  if (!user.role_id) return 'warning';
  return 'success';
}

function getStatusIcon(user: any): string {
  if (!user.role_id) return 'mdi-account-alert';
  return 'mdi-account-check';
}

function getStatusText(user: any): string {
  if (!user.role_id) return 'Incomplete';
  return 'Active';
}

function getRoleName(roleId: string | number | null): string | null {
  const role = getRoleById(roleId);
  return role?.name || null;
}

function formatPermissionName(name: string): string {
  if (!name) return '';
  return name.split('_')[0].replace(/([A-Z])/g, ' $1').trim();
}

function clearFilters(): void {
  searchQuery.value = '';
  filterRole.value = null;
}

async function refreshData(): Promise<void> {
  // Force refresh dengan clear cache
  users.value = [];
  roles.value = [];
  await new Promise(resolve => setTimeout(resolve, 100));
  await fetchUsers();
  await fetchRoles();
}

// --- Lifecycle ---
onMounted(() => {
  fetchUsers();
  fetchRoles();
});

// --- API Methods ---
async function fetchUsers() {
  loading.value = true;
  try {
    // Fetch all users by setting a high limit
    const response = await apiClient.get('/users/', {
      params: {
        limit: 1000 // Get all users
      }
    });
    users.value = response.data;
  } catch (error) {
    console.error('Gagal mengambil data users:', error);
  } finally {
    loading.value = false;
  }
}

async function fetchRoles() {
  try {
    const response = await apiClient.get('/roles/');
    roles.value = response.data;
  } catch (error) {
    console.error('Gagal mengambil data roles:', error);
  }
}

// --- Dialog Methods ---
function openDialog(item?: any) {
  if (item) {
    editedIndex.value = users.value.findIndex(u => u.id === item.id);
    const roleIdAsString = item.role_id ? item.role_id.toString() : null;
    editedItem.value = { ...item, password: '', role_id: roleIdAsString };
  } else {
    editedIndex.value = -1;
    editedItem.value = { ...defaultItem };
  }
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  nextTick(() => {
    editedItem.value = { ...defaultItem };
    editedIndex.value = -1;
  });
}

function openDeleteDialog(item: any) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  itemToDelete.value = null;
  dialogDelete.value = false;
}

function viewUserDetail(item: any) {
  selectedUser.value = item;
  dialogDetail.value = true;
}

// --- CRUD Operations ---
async function saveUser() {
  saving.value = true;
  try {
    const payload: any = { ...editedItem.value };
    if (!payload.password) {
      delete payload.password;
    }

    if (payload.role_id) {
      payload.role_id = parseInt(payload.role_id, 10);
    } else {
      payload.role_id = null;
    }

    if (editedIndex.value > -1) {
      // Update existing user
      await apiClient.patch(`/users/${payload.id}`, payload);
    } else {
      // Create new user
      const createPayload = {
        name: payload.name,
        email: payload.email,
        password: payload.password,
        role_id: payload.role_id,
      };
      await apiClient.post('/users/', createPayload);
    }
    await fetchUsers();
    closeDialog();
  } catch (error: any) {
    console.error('Gagal menyimpan user:', error);

    // Handle specific error cases
    let errorMessage = 'Terjadi kesalahan saat menyimpan user.';

    if (error.response?.status === 422) {
      const errorData = error.response.data;

      if (errorData.error && errorData.error.includes('Password')) {
        errorMessage = 'Password tidak memenuhi syarat keamanan:\n' +
          '• Minimal 8 karakter\n' +
          '• Mengandung huruf kapital (A-Z)\n' +
          '• Mengandung huruf kecil (a-z)\n' +
          '• Mengandung angka (0-9)\n' +
          '• Mengandung karakter khusus (!@#$%^&*(),.?":{}|<>)\n' +
          '• Tidak boleh mengandung spasi';
      } else if (errorData.error && errorData.error.includes('email')) {
        errorMessage = 'Email sudah digunakan oleh user lain.';
      } else if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail);
      }
    } else if (error.response?.status === 409) {
      errorMessage = 'User dengan email tersebut sudah ada.';
    }

    alert(errorMessage);
  } finally {
    saving.value = false;
  }
}

async function confirmDelete() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/users/${itemToDelete.value.id}`);
    await fetchUsers();
  } catch (error) {
    console.error('Gagal menghapus user:', error);
  } finally {
    deleting.value = false;
    closeDeleteDialog();
  }
}
</script>

<style scoped>
/* Header Card styling - sama seperti halaman lain */
.header-card {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
  background: white;
}

/* Header content for memperbesar box */
.header-content {
  padding: 24px 32px;
}

.header-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.header-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="50" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="30" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
}

/* Header text styling */
.header-section h1 {
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 1.1rem;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  opacity: 0.95;
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

.v-avatar {
  transition: all 0.2s ease;
}

.v-avatar:hover {
  transform: scale(1.05);
}

.v-chip {
  transition: all 0.2s ease;
}

.v-text-field, .v-select {
  transition: all 0.2s ease;
}

.search-filters {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
