<template>
  <v-container fluid class="pa-6">
    <div class="d-flex align-center mb-6">
      <v-avatar class="me-3" color="indigo" size="40">
        <v-icon color="white">mdi-router-network</v-icon>
      </v-avatar>
      <div>
        <h1 class="text-h4 font-weight-bold">OLT Management</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-0">Kelola perangkat OLT Anda</p>
      </div>
      <v-spacer></v-spacer>
      <v-btn color="primary" size="large" @click="openDialog()" prepend-icon="mdi-plus" class="text-none">
        Tambah OLT
      </v-btn>
    </div>

    <v-card elevation="2" rounded="lg">
      <v-card-title class="d-flex align-center pa-4 bg-grey-lighten-5">
        <v-icon start>mdi-table</v-icon>
        <span class="font-weight-bold">Daftar OLT</span>
      </v-card-title>
      <v-data-table
        :headers="headers"
        :items="olts"
        :loading="loading"
        item-value="id"
        loading-text="Memuat data OLT..."
        no-data-text="Belum ada data OLT"
      >
        <template v-slot:item.actions="{ item }">
          <div class="d-flex justify-center gap-2">
            <v-btn 
              size="small" 
              variant="tonal" 
              color="cyan" 
              @click="testConnection(item)"
              :loading="testingConnectionId === item.id"
              class="text-none"
            >
              <v-icon start size="16">mdi-lan-connect</v-icon> Test Koneksi
            </v-btn>
            <v-btn size="small" variant="tonal" color="primary" @click="openDialog(item)" class="text-none">
              <v-icon start size="16">mdi-pencil</v-icon> Edit
            </v-btn>
            <v-btn size="small" variant="tonal" color="error" @click="openDeleteDialog(item)" class="text-none">
              <v-icon start size="16">mdi-delete</v-icon> Hapus
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card rounded="lg">
        <v-form @submit.prevent="saveOLT">
          <v-card-title class="bg-primary">{{ formTitle }}</v-card-title>
          <v-card-text class="py-6">
            <v-text-field 
              v-model="editedItem.nama_olt" 
              label="Nama OLT (Contoh: OLT-Pusat)" 
              variant="outlined" 
              class="mb-4" 
              :rules="[rules.required]"
            ></v-text-field>
            <v-text-field 
              v-model="editedItem.ip_address" 
              label="IP Address" 
              variant="outlined" 
              class="mb-4" 
              :rules="[rules.required, rules.ip]"
            ></v-text-field>
            
            <v-select
              v-model="editedItem.mikrotik_server_id"
              :items="mikrotikList"
              item-title="name"
              item-value="id"
              label="Hubungkan ke Mikrotik Server"
              variant="outlined"
              class="mb-4"
              :loading="loadingMikrotiks"
              :rules="[rules.required]"
              no-data-text="Tidak ada server Mikrotik"
            ></v-select>

            <v-select 
              v-model="editedItem.tipe_olt" 
              :items="oltTypes" 
              label="Tipe OLT" 
              variant="outlined" 
              class="mb-4" 
              :rules="[rules.required]"
            ></v-select>
            <v-text-field 
              v-model="editedItem.username" 
              label="Username" 
              variant="outlined" 
              class="mb-4"
            ></v-text-field>
            <v-text-field 
              v-model="editedItem.password" 
              label="Password" 
              type="password" 
              variant="outlined" 
              :placeholder="isEditMode ? 'Kosongkan jika tidak ingin diubah' : ''"
              :rules="isEditMode ? [] : [rules.required]"
            ></v-text-field>
          </v-card-text>
          <v-card-actions class="pa-4 bg-grey-lighten-5">
            <v-spacer></v-spacer>
            <v-btn text @click="closeDialog">Batal</v-btn>
            <v-btn color="primary" type="submit" :loading="saving">Simpan</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="500px">
        <v-card rounded="lg">
            <v-card-title class="text-h5 text-center pt-8">Konfirmasi Hapus</v-card-title>
            <v-card-text class="text-center">
                Yakin ingin menghapus OLT <strong>{{ itemToDelete?.nama_olt }}</strong>?
            </v-card-text>
            <v-card-actions class="pa-4">
                <v-spacer></v-spacer>
                <v-btn text @click="closeDeleteDialog">Batal</v-btn>
                <v-btn color="error" @click="confirmDelete" :loading="deleting">Ya, Hapus</v-btn>
                <v-spacer></v-spacer>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      location="top right"
      variant="elevated"
      rounded="lg"
    >
      <div class="d-flex align-center">
        <v-icon
          :icon="snackbar.color === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'"
          class="me-3"
          size="24"
        ></v-icon>
        <span class="font-weight-bold">{{ snackbar.text }}</span>
      </div>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';

// --- INTERFACES ---
interface OLT {
  id: number;
  nama_olt: string;
  ip_address: string;
  tipe_olt: string;
  username?: string;
  mikrotik_server_id?: number | null; // Izinkan null untuk form
}

interface MikrotikSelectItem {
  id: number;
  name: string;
}

// --- STATE MANAGEMENT ---
const olts = ref<OLT[]>([]);
const mikrotikList = ref<MikrotikSelectItem[]>([]);
const loading = ref(true);
const loadingMikrotiks = ref(false);
const saving = ref(false);
const deleting = ref(false);
const testingConnectionId = ref<number | null>(null);

const dialog = ref(false);
const dialogDelete = ref(false);

const editedItem = ref<Partial<OLT> & { password?: string }>({});
const itemToDelete = ref<OLT | null>(null);
const snackbar = ref({ show: false, text: '', color: 'success' });

// --- COMPUTED PROPERTIES ---
const isEditMode = computed(() => !!editedItem.value.id);
const formTitle = computed(() => isEditMode.value ? 'Edit OLT' : 'Tambah OLT Baru');

// --- DATA & CONFIGURATION ---
const headers = [
  { title: 'Nama OLT', key: 'nama_olt', sortable: true },
  { title: 'IP Address', key: 'ip_address', sortable: true },
  { title: 'Tipe', key: 'tipe_olt', sortable: true },
  { title: 'Username', key: 'username', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, width: '380px', align: 'center' as const },
];

const oltTypes = ['HSGQ', 'ZTE', 'Huawei', 'Fiberhome', 'Lainnya'];

const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi.',
  ip: (value: string) => /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(value) || 'Format IP tidak valid.',
};

// --- LIFECYCLE HOOKS ---
onMounted(() => {
  fetchOLTs();
  fetchMikrotiks();
});

// --- FUNCTIONS ---
async function fetchOLTs() {
  loading.value = true;
  try {
    const response = await apiClient.get('/olt/');
    olts.value = response.data;
  } catch (error) {
    showSnackbar("Gagal memuat data OLT", "error");
  } finally {
    loading.value = false;
  }
}

async function fetchMikrotiks() {
  loadingMikrotiks.value = true;
  try {
    const response = await apiClient.get('/mikrotik_servers/'); // Menggunakan garis bawah
    mikrotikList.value = response.data;
  } catch (error) {
    showSnackbar("Gagal memuat daftar Mikrotik Server", "error");
  } finally {
    loadingMikrotiks.value = false;
  }
}

function openDialog(item?: OLT) {
  editedItem.value = item ? { ...item, password: '' } : { tipe_olt: 'HSGQ' };
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = {};
}

async function saveOLT() {
  saving.value = true;
  const payload = { ...editedItem.value };
  
  // Jangan kirim password kosong saat mengedit
  if (isEditMode.value && !payload.password) {
    delete payload.password;
  }

  try {
    if (isEditMode.value) {
      await apiClient.patch(`/olt/${payload.id}`, payload);
    } else {
      await apiClient.post('/olt/', payload);
    }
    fetchOLTs();
    closeDialog();
    showSnackbar(`OLT berhasil ${isEditMode.value ? 'diperbarui' : 'ditambahkan'}`, 'success');
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail?.[0]?.msg || "Gagal menyimpan data OLT";
    showSnackbar(errorMsg, 'error');
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: OLT) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  itemToDelete.value = null;
}

async function confirmDelete() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/olt/${itemToDelete.value.id}`);
    fetchOLTs();
    showSnackbar('OLT berhasil dihapus', 'success');
  } catch (error) {
    showSnackbar('Gagal menghapus OLT', 'error');
  } finally {
    deleting.value = false;
    closeDeleteDialog();
  }
}

async function testConnection(item: OLT) {
  testingConnectionId.value = item.id;
  try {
    const response = await apiClient.post(`/olt/${item.id}/test-connection`);
    showSnackbar(response.data.message || 'Koneksi berhasil!', 'success');
  } catch (error: any) {
    const message = error.response?.data?.message || "Koneksi gagal, terjadi error.";
    showSnackbar(message, 'error');
  } finally {
    testingConnectionId.value = null;
  }
}

function showSnackbar(text: string, color: 'success' | 'error' | 'info') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}
</script>

<style scoped>
/* Menambahkan sedikit jarak antar tombol aksi */
.gap-2 {
  gap: 8px;
}
</style>