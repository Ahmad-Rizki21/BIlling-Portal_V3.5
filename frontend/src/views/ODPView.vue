<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <div class="d-flex align-center">
              <v-avatar class="me-4 elevation-4" color="primary" size="80">
                <v-icon color="white" size="40">mdi-home</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 font-weight-bold text-white mb-2">ODP Management</h1>
                <p class="header-subtitle mb-0">
                  Kelola infrastruktur Optical Distribution Point
                </p>
              </div>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              color="white"
              variant="elevated"
              size="large"
              elevation="4"
              @click="openDialog()"
              prepend-icon="mdi-plus-circle-outline"
              class="text-none font-weight-bold w-100 w-md-auto rounded-lg"
              style="color: #4338ca !important;"
            >
              Tambah ODP
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">

    <v-row class="mb-6">
      <v-col cols="6" md="3"><v-card rounded="lg" class="pa-4"><div class="text-caption">TOTAL ODP</div><div class="text-h5 font-weight-bold">{{ stats.totalOdp }}</div></v-card></v-col>
      <v-col cols="6" md="3"><v-card rounded="lg" class="pa-4"><div class="text-caption">TOTAL PORT</div><div class="text-h5 font-weight-bold">{{ stats.totalPorts }}</div></v-card></v-col>
      <v-col cols="6" md="3"><v-card rounded="lg" class="pa-4 text-warning"><div class="text-caption">PORT TERPAKAI</div><div class="text-h5 font-weight-bold">{{ stats.usedPorts }}</div></v-card></v-col>
      <v-col cols="6" md="3"><v-card rounded="lg" class="pa-4 text-success"><div class="text-caption">PORT TERSEDIA</div><div class="text-h5 font-weight-bold">{{ stats.availablePorts }}</div></v-card></v-col>
    </v-row>

    
    <v-card elevation="2" rounded="lg">
      <v-data-table
        :headers="headers"
        :items="odps"
        :loading="loading"
        loading-text="Memuat data ODP..."
        no-data-text="Belum ada data ODP"
      >
      <template v-slot:loading>
        <SkeletonLoader type="table" :rows="5" />
      </template>

       <template v-slot:item.kapasitas_port="{ item }">
        <v-progress-linear
            :model-value="(item.port_terpakai / item.kapasitas_port) * 100"
            :color="getCapacityColor(item.port_terpakai, item.kapasitas_port)"
            height="20"
            rounded
        >
            <strong class="text-white text-caption">{{ item.port_terpakai }} / {{ item.kapasitas_port }}</strong>
        </v-progress-linear>
        </template>
        <template v-slot:item.olt="{ item }">
          {{ item.olt.nama_olt }}
        </template>
        <template v-slot:item.actions="{ item }">
            <div class="d-flex gap-2 justify-end">
                
                <v-btn
                size="small"
                variant="tonal"
                color="teal"
                @click="viewTopology(item.olt_id)"
                prepend-icon="mdi-sitemap"
                >
                Topologi
                </v-btn>
                <v-btn
                size="small"
                variant="tonal"
                color="primary"
                @click="openDialog(item)"
                prepend-icon="mdi-pencil"
                >
                Edit
                </v-btn>
                <v-btn
                size="small"
                variant="tonal"
                color="error"
                @click="openDeleteDialog(item)"
                prepend-icon="mdi-delete"
                >
                Hapus
                </v-btn>
            </div>
        </template>
      </v-data-table>
    </v-card>

    <v-card elevation="2" rounded="lg" class="mt-6">
      <v-card-title>Peta Lokasi ODP</v-card-title>
      <v-card-text>
        <ODPMap :odps="odps" />
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card>
        <v-card-title class="bg-primary">{{ formTitle }}</v-card-title>
        <v-card-text class="py-4">
            <v-text-field v-model="editedItem.kode_odp" label="Kode ODP..." variant="outlined" class="mb-4"></v-text-field>
            <v-text-field v-model="editedItem.alamat" label="Alamat / Lokasi ODP" variant="outlined" class="mb-4"></v-text-field>
            <v-text-field v-model.number="editedItem.kapasitas_port" label="Kapasitas Port" type="number" variant="outlined" class="mb-4"></v-text-field>
            
            <v-row>
              <v-col cols="6">
                <v-text-field 
                  v-model.number="editedItem.latitude" 
                  label="Latitude" 
                  type="number" 
                  variant="outlined" 
                  class="mb-4"
                  hint="Contoh: -6.2383"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field 
                  v-model.number="editedItem.longitude" 
                  label="Longitude" 
                  type="number" 
                  variant="outlined" 
                  class="mb-4"
                  hint="Contoh: 106.9756"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>
            <v-select
                v-model="editedItem.olt_id"
                :items="oltsForSelect"
                item-title="nama_olt"
                item-value="id"
                label="Terhubung ke OLT"
                variant="outlined"
            ></v-select>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="closeDialog">Batal</v-btn>
            <v-btn color="primary" @click="saveOdp" :loading="saving">Simpan</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="500px">
    <v-card rounded="lg">
      <v-card-title class="text-h5 text-center pt-8">Konfirmasi Hapus</v-card-title>
      <v-card-text class="text-center">
          Yakin ingin menghapus ODP <strong>{{ itemToDelete?.kode_odp }}</strong>?
          <br>
          Tindakan ini tidak dapat dibatalkan.
      </v-card-text>
      <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDeleteDialog">Batal</v-btn>
          
          <v-btn color="error" @click="confirmDelete" :loading="deleting">Ya, Hapus</v-btn>
          
          <v-spacer></v-spacer>
      </v-card-actions>
    </v-card>
  </v-dialog>

    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/services/api';
import { useRouter } from 'vue-router';
import ODPMap from '@/components/ODPMap.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';


// --- Interface untuk tipe data ---
interface ODP {
  id: number;
  kode_odp: string;
  alamat: string;
  kapasitas_port: number;
  olt_id: number;
  port_terpakai: number;
  olt: {
    id: number;
    nama_olt: string;
  };

  latitude?: number;
  longitude?: number;
  parent_odp_id?: number | null; // Bisa null jika tidak punya induk
  parent_odp?: { // Untuk menampilkan data induk dari API
    id: number;
    kode_odp: string;
  } | null;
}

interface OLTSelectItem {
  id: number;
  nama_olt: string;
}

// --- State Management ---
const odps = ref<ODP[]>([]);
const oltsForSelect = ref<OLTSelectItem[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const router = useRouter();

const dialog = ref(false);
const dialogDelete = ref(false);

const editedItem = ref<Partial<ODP>>({});
const itemToDelete = ref<ODP | null>(null);

// --- Computed Properties ---
const isEditMode = computed(() => !!editedItem.value.id);
const formTitle = computed(() => isEditMode.value ? 'Edit ODP' : 'Tambah ODP Baru');

const stats = computed(() => {
  const totalOdp = odps.value.length;
  const totalPorts = odps.value.reduce((sum, odp) => sum + odp.kapasitas_port, 0);
  const usedPorts = odps.value.reduce((sum, odp) => sum + odp.port_terpakai, 0);
  return {
    totalOdp,
    totalPorts,
    usedPorts,
    availablePorts: totalPorts - usedPorts,
  };
});

function viewTopology(oltId: number) {
  router.push({ name: 'TopologyView', params: { olt_id: oltId } });
}

// --- Table Headers ---
const headers = [
  { title: 'Kode ODP', key: 'kode_odp' },
  { title: 'Alamat', key: 'alamat' },
  { title: 'Kapasitas (Terpakai/Total)', key: 'kapasitas_port', align: 'center' as const },
  { title: 'Terhubung ke OLT', key: 'olt.nama_olt' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const },
];

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchOdps();
  fetchOltsForSelect();
});

// --- Functions ---
async function fetchOdps() {
  loading.value = true;
  try {
    const response = await apiClient.get<ODP[]>('/odp/');
    odps.value = response.data;
  } catch(error) {
    console.error("Gagal mengambil data ODP:", error);
  } finally {
    loading.value = false;
  }
}

async function fetchOltsForSelect() {
    try {
        const response = await apiClient.get<OLTSelectItem[]>('/olt/');
        oltsForSelect.value = response.data;
    } catch (error) {
        console.error("Gagal mengambil daftar OLT:", error);
    }
}

async function saveOdp() {
    saving.value = true;
    try {
        if (isEditMode.value) {
            await apiClient.patch(`/odp/${editedItem.value.id}`, editedItem.value);
        } else {
            await apiClient.post('/odp/', editedItem.value);
        }
        closeDialog();
        fetchOdps();
    } catch (error) {
        console.error("Gagal menyimpan ODP:", error);
    } finally {
        saving.value = false;
    }
}

async function confirmDelete() {
    if (!itemToDelete.value) return;
    deleting.value = true;
    try {
        await apiClient.delete(`/odp/${itemToDelete.value.id}`);
        closeDeleteDialog();
        fetchOdps();
    } catch (error) {
        console.error("Gagal menghapus ODP:", error);
    } finally {
        deleting.value = false;
    }
}

function openDialog(item?: ODP) {
  // Jika 'item' ada, kita sedang mengedit.
  // Jika tidak, kita membuat baru dengan nilai default.
  editedItem.value = item ? { ...item } : { kapasitas_port: 8 };
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = {};
}

function openDeleteDialog(item: ODP) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  setTimeout(() => { itemToDelete.value = null }, 300);
}

function getCapacityColor(used: number, total: number) {
  const percentage = (used / total) * 100;
  if (percentage >= 90) return 'error';
  if (percentage >= 70) return 'warning';
  return 'success';
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

/* Header content untuk memperbesar box */
.header-content {
  padding: 24px 32px;
}

/* Content section - sama seperti halaman lain */
.content-section {
  width: 100%;
}

/* Header Section styling - sama seperti halaman lain */
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
</style>