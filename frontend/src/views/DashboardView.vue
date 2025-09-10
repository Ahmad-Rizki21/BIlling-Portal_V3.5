<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="dashboard-title">
            <v-icon class="title-icon">mdi-view-dashboard</v-icon>
            Dashboard
          </h1>
          <p class="dashboard-subtitle">Monitoring Customer Fiber To The Home Artacom Portal Systems</p>
        </div>
        <div class="header-actions">
          <v-chip class="status-chip" color="success" size="small">
            <v-icon start size="12">mdi-circle</v-icon>
            System Active
          </v-chip>
        </div>
      </div>
    </div>

    <div class="top-layout-grid mb-6">
      <div v-if="revenueData" class="revenue-widget-container">
        <v-skeleton-loader v-if="loading" type="card-avatar, article" class="fill-height"></v-skeleton-loader>
        <div v-else class="revenue-card">
          <div class="revenue-card-content">
            <div class="revenue-main">
              <div class="revenue-header">
                <p class="revenue-title">Piutang</p>
                <div class="revenue-icon-wrapper">
                  <v-icon color="white">mdi-cash-multiple</v-icon>
                </div>
              </div>
              <div class="revenue-body">
                <h2 class="revenue-value">{{ formatCurrency(revenueData.total) }}</h2>
                <p class="revenue-period">Periode {{ revenueData.periode }}</p>
              </div>
            </div>
            <div class="revenue-divider"></div>
            <div class="revenue-breakdown">
              <div v-for="item in revenueData.breakdown" :key="item.brand" class="breakdown-item">
                <div class="breakdown-header">
                  <p class="breakdown-title">{{ item.brand }}</p>
                  <v-icon size="20" class="breakdown-icon">
                    {{ getIconForBrand(item.brand) }}
                  </v-icon>
                </div>
                <p class="breakdown-value">{{ formatCurrency(item.revenue) }}</p>
                <p class="breakdown-period">PERIODE {{ revenueData.periode.toUpperCase() }}</p>
              </div>
            </div>
          </div>
          <div class="revenue-card-background"></div>
        </div>
      </div>

      <div v-if="customerStats && customerStats.length > 0" class="stats-subgrid">
        <div v-if="loading" v-for="n in 3" :key="`skel-stat-${n}`">
            <v-skeleton-loader type="list-item-avatar-two-line"></v-skeleton-loader>
        </div>
        <div v-else v-for="(stat, index) in customerStats" :key="stat.title" class="stat-card" :class="`card-${index % 4}`">
          <div class="stat-card-content">
            <div class="stat-header">
              <div class="stat-icon-container" :class="`icon-${index % 4}`">
                <v-icon :color="stat.color" size="20">{{ stat.icon }}</v-icon>
              </div>
            </div>
            <div class="stat-body">
              <h3 class="stat-value">{{ stat.value }}</h3>
              <p class="stat-title">{{ stat.title }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="serverStats && serverStats.length > 0" class="stats-grid mb-6">
      <v-skeleton-loader v-if="loading" v-for="n in 3" :key="`skel-srv-${n}`" type="list-item-avatar-two-line"></v-skeleton-loader>
      <div v-else v-for="(stat, index) in serverStats" :key="stat.title" class="stat-card" :class="`card-${(index + 3) % 4}`">
        <div class="stat-card-content">
          <div class="stat-header">
            <div class="stat-icon-container" :class="`icon-${(index + 3) % 4}`">
                <v-icon :color="stat.color" size="20">{{ stat.icon }}</v-icon>
            </div>
          </div>
          <div class="stat-body">
            <h3 class="stat-value">{{ stat.value }}</h3>
            <p class="stat-title">{{ stat.title }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="charts-section">
      <div class="charts-row">
        <div v-if="lokasiChartData" id="lokasi-chart-container" class="chart-card location-chart">
          <div class="chart-header">
            <div class="chart-title-section">
              <h3 class="chart-title">
                <v-icon class="chart-icon" color="primary">mdi-map-marker-radius</v-icon>
                Pelanggan per Alamat
              </h3>
              <p class="chart-subtitle">Distribusi pelanggan aktif di setiap lokasi</p>
            </div>
            <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('lokasi-chart-container', 'distribusi-lokasi.png')"></v-btn>
          </div>
          <div class="chart-container">
            <Chart v-if="!loading" type="bar" :data="lokasiChartData" :options="chartOptions" />
          </div>
        </div>

        <div v-if="paketChartData" id="paket-chart-container" class="chart-card package-chart">
          <div class="chart-header">
            <div class="chart-title-section">
              <h3 class="chart-title">
                <v-icon class="chart-icon" color="success">mdi-wifi</v-icon>
                Pelanggan per Paket Layanan
              </h3>
              <p class="chart-subtitle">Distribusi pelanggan berdasarkan paket</p>
            </div>
            <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('paket-chart-container', 'distribusi-paket.png')"></v-btn>
          </div>
          <div class="chart-container">
            <Chart v-if="!loading" type="bar" :data="paketChartData" :options="chartOptions" />
          </div>
        </div>
      </div>
      
      <div class="charts-row">
        <div v-if="growthChartData" id="growth-chart-container" class="chart-card growth-chart">
          <div class="chart-header">
            <div class="chart-title-section">
              <h3 class="chart-title">
                <v-icon class="chart-icon" color="pink">mdi-chart-line</v-icon>
                Pertumbuhan Pelanggan
              </h3>
              <p class="chart-subtitle">Jumlah pelanggan baru per bulan</p>
            </div>
            <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('growth-chart-container', 'pertumbuhan-pelanggan.png')"></v-btn>
          </div>
          <div class="chart-container">
            <Chart v-if="!loading" type="line" :data="growthChartData" :options="growthChartOptions" />
          </div>
        </div>

        <div v-if="invoiceChartData" id="invoice-chart-container" class="chart-card invoice-chart">
          <div class="chart-header">
            <div class="chart-title-section">
              <h3 class="chart-title">
                <v-icon class="chart-icon" color="indigo">mdi-file-chart</v-icon>
                Ringkasan Invoice
              </h3>
              <p class="chart-subtitle">Distribusi status invoice per bulan</p>
            </div>
            <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('invoice-chart-container', 'ringkasan-invoice.png')"></v-btn>
          </div>
          <div class="chart-container">
            <Chart v-if="!loading" type="bar" :data="invoiceChartData" :options="invoiceChartOptions" />
          </div>
        </div>
      </div>
    </div>

    <div class="charts-row">
      <div v-if="statusChartData" id="status-chart-container" class="chart-card">
        <div class="chart-header">
          <div class="chart-title-section">
            <h3 class="chart-title">
              <v-icon class="chart-icon" color="primary">mdi-account-details</v-icon>
              Status Langganan
            </h3>
            <p class="chart-subtitle">Distribusi status semua langganan</p>
          </div>
          <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('status-chart-container', 'status-langganan.png')"></v-btn>
        </div>
        <div class="chart-container donut-container">
          <Chart v-if="!loading" type="doughnut" :data="statusChartData" :options="donutChartOptions" />
          <div class="total-in-center">
            <h3>{{ totalSubscriptions }}</h3>
            <span>Total Langganan</span>
          </div>
        </div>
      </div>

      <div v-if="loyalitasChartData" id="loyalitas-chart-container" class="chart-card">
        <div class="chart-header">
          <div class="chart-title-section">
            <h3 class="chart-title">
              <v-icon class="chart-icon" color="success">mdi-account-star</v-icon>
              Loyalitas Pembayaran
            </h3>
            <p class="chart-subtitle">Distribusi pembayaran pelanggan aktif</p>
          </div>
          <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('loyalitas-chart-container', 'loyalitas-pembayaran.png')"></v-btn>
        </div>
        <div class="chart-container donut-container">
          <Chart v-if="!loading" type="doughnut" :data="loyalitasChartData" :options="loyalitasDonutOptions" />
          <div class="total-in-center">
            <h3>{{ totalActiveCustomers }}</h3>
            <span>Pelanggan Aktif</span>
          </div>
        </div>
      </div>



      <div v-if="alamatChartData" id="alamat-chart-container" class="chart-card">
        <div class="chart-header">
          <div class="chart-title-section">
            <h3 class="chart-title">
              <v-icon class="chart-icon" color="info">mdi-map-marker-radius</v-icon>
              Pelanggan Aktif per Alamat
            </h3>
            <p class="chart-subtitle">7 Lokasi dengan pelanggan aktif terbanyak</p>
          </div>
          <v-btn icon="mdi-download" size="small" variant="text" @click="downloadAsPNG('alamat-chart-container', 'pelanggan-per-alamat.png')"></v-btn>
        </div>
        <div class="chart-container">
          <Chart v-if="!loading" type="pie" :data="alamatChartData" :options="pieChartOptions" />
        </div>
      </div>
    </div>

    <v-dialog v-model="dialogPaketDetail" max-width="700px" persistent>
      <v-card class="package-detail-card elevation-12">
        <div class="dialog-header">
          <div class="header-gradient"></div>
          <div class="header-content">
            <div class="header-icon">
              <v-icon size="32" color="white">mdi-package-variant</v-icon>
            </div>
            <div class="header-text">
              <h2 class="dialog-title">{{ selectedPaketTitle }}</h2>
              <p class="dialog-subtitle">Detail distribusi pelanggan</p>
            </div>
          </div>
          <v-btn
            icon="mdi-close"
            variant="text"
            color="white"
            size="small"
            class="close-btn"
            @click="dialogPaketDetail = false"
          ></v-btn>
        </div>

        <v-card-text class="dialog-content" v-if="selectedPaketDetail">
          <div class="summary-section">
            <div class="summary-card">
              <div class="summary-icon">
                <v-icon color="primary">mdi-account-group</v-icon>
              </div>
              <div class="summary-content">
                <div class="summary-label">Total Pelanggan</div>
                <div class="summary-value">{{ selectedPaketDetail.total_pelanggan }}</div>
              </div>
            </div>
          </div>

          <div class="content-sections">
            <div class="detail-section">
              <div class="section-header">
                <div class="section-icon location-icon">
                  <v-icon size="20">mdi-map-marker-radius</v-icon>
                </div>
                <h3 class="section-title">Distribusi Lokasi</h3>
              </div>
              
              <div class="items-grid">
                <div 
                  v-for="item in selectedPaketDetail.breakdown_lokasi" 
                  :key="item.nama"
                  class="detail-item location-item"
                >
                  <div class="item-content">
                    <div class="item-icon">
                      <v-icon size="18" color="info">mdi-map-marker</v-icon>
                    </div>
                    <div class="item-info">
                      <div class="item-name">{{ item.nama }}</div>
                      <div class="item-subtitle">Lokasi</div>
                    </div>
                  </div>
                  <div class="item-value">
                    <v-chip 
                      color="info" 
                      variant="flat"
                      size="small"
                      class="value-chip"
                    >
                      {{ item.jumlah }}
                    </v-chip>
                  </div>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-header">
                <div class="section-icon brand-icon">
                  <v-icon size="20">mdi-tag-outline</v-icon>
                </div>
                <h3 class="section-title">Distribusi Brand</h3>
              </div>
              
              <div class="items-grid">
                <div 
                  v-for="item in selectedPaketDetail.breakdown_brand" 
                  :key="item.nama"
                  class="detail-item brand-item"
                >
                  <div class="item-content">
                    <div class="item-icon">
                      <v-icon size="18" color="success">mdi-tag</v-icon>
                    </div>
                    <div class="item-info">
                      <div class="item-name">{{ item.nama }}</div>
                      <div class="item-subtitle">Brand</div>
                    </div>
                  </div>
                  <div class="item-value">
                    <v-chip 
                      color="success" 
                      variant="flat"
                      size="small"
                      class="value-chip"
                    >
                      {{ item.jumlah }}
                    </v-chip>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>

            <v-card-actions class="dialog-footer">
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                variant="elevated"
                size="large"
                class="close-action-btn"
                @click="dialogPaketDetail = false"
              >
                <v-icon start>mdi-check</v-icon>
                Tutup
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-dialog v-model="dialogLoyalitas" max-width="800px" persistent>
          <v-card class="loyalitas-detail-card elevation-12">
            <div class="dialog-header">
              <div class="header-gradient"></div>
              <div class="header-content">
                <div class="header-icon">
                  <v-icon size="32" color="white">mdi-account-star</v-icon>
                </div>
                <div class="header-text">
                  <h2 class="dialog-title">{{ selectedLoyalitasSegmen }}</h2>
                  <p class="dialog-subtitle">Daftar pelanggan dalam kategori ini</p>
                </div>
              </div>
              <v-btn
                icon="mdi-close"
                variant="text"
                color="white"
                size="small"
                class="close-btn"
                @click="dialogLoyalitas = false"
              ></v-btn>
            </div>

            <v-card-text class="dialog-content">
              <!-- Loading State -->
              <div v-if="loadingLoyalitasDetail" class="loading-section">
                <v-progress-circular
                  indeterminate
                  color="primary"
                  size="60"
                  width="4"
                ></v-progress-circular>
                <p class="loading-text">Memuat data pelanggan...</p>
              </div>

              <!-- Content -->
              <div v-else>
                <!-- Summary Section -->
                <div class="summary-section">
                  <div class="summary-card">
                    <div class="summary-icon">
                      <v-icon color="primary">mdi-account-group</v-icon>
                    </div>
                    <div class="summary-content">
                      <div class="summary-label">Total Pelanggan</div>
                      <div class="summary-value">{{ loyalitasUserList.length }}</div>
                    </div>
                  </div>
                </div>

                <!-- User List -->
                <div class="users-section">
                  <div class="section-header">
                    <div class="section-icon">
                      <v-icon size="20" color="primary">mdi-account-details</v-icon>
                    </div>
                    <h3 class="section-title">Detail Pelanggan</h3>
                  </div>
                  
                  <!-- Empty State -->
                  <div v-if="loyalitasUserList.length === 0" class="empty-state">
                    <v-icon size="64" color="grey">mdi-account-off</v-icon>
                    <h3>Tidak ada data</h3>
                    <p>Tidak ada pelanggan dalam kategori ini</p>
                  </div>
                  
                  <!-- User Cards -->
                  <div v-else class="users-grid">
                    <div 
                      v-for="(user, index) in loyalitasUserList" 
                      :key="user.id || index"
                      class="user-card"
                    >
                      <div class="user-avatar">
                        <v-icon size="24" color="primary">mdi-account</v-icon>
                      </div>
                      <div class="user-info">
                        <h4 class="user-name">{{ user.nama || 'Nama tidak tersedia' }}</h4>
                        <div class="user-details">
                          <div class="detail-row">
                            <v-icon size="14" color="grey">mdi-identifier</v-icon>
                            <span>{{ user.id_pelanggan || 'ID tidak tersedia' }}</span>
                          </div>
                          <div class="detail-row" v-if="user.alamat">
                            <v-icon size="14" color="grey">mdi-map-marker</v-icon>
                            <span>{{ user.alamat }}</span>
                          </div>
                          <div class="detail-row" v-if="user.no_telp">
                            <v-icon size="14" color="grey">mdi-phone</v-icon>
                            <span>{{ user.no_telp }}</span>
                          </div>
                        </div>
                      </div>
                      <div class="user-badge">
                        <v-chip 
                          :color="getLoyaltyColor(selectedLoyalitasSegmen)" 
                          variant="flat"
                          size="small"
                          class="status-chip"
                        >
                          {{ getShortLabel(selectedLoyalitasSegmen) }}
                        </v-chip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </v-card-text>

            <v-card-actions class="dialog-footer">
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                variant="elevated"
                size="large"
                class="close-action-btn"
                @click="dialogLoyalitas = false"
              >
                <v-icon start>mdi-check</v-icon>
                Tutup
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
    
  </div>
</template>

// BAGIAN 2: PERBAIKAN SCRIPT SETUP
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Chart } from 'vue-chartjs';
import html2canvas from 'html2canvas';
import {
  Chart as ChartJS, 
  Title, 
  Tooltip, 
  Legend, 
  BarElement, 
  BarController,
  LineElement,
  LineController,
  PointElement,
  CategoryScale, 
  LinearScale, 
  Filler,
  ChartOptions,
  DoughnutController,
  ArcElement,
  PieController
} from 'chart.js';
import { useTheme } from 'vuetify';
import apiClient from '@/services/api';

ChartJS.register(
  Title, Tooltip, Legend, BarElement, BarController, LineElement, LineController, 
  PointElement, CategoryScale, LinearScale, Filler, DoughnutController, ArcElement, PieController
);

const theme = useTheme();
const loading = ref(true);

// Define interfaces for better TypeScript support
interface LoyalitasUser {
  id: number;
  nama: string;
  id_pelanggan: string;
  alamat?: string;
  no_telp?: string;
}

// --- State dengan tipe yang tepat ---
const revenueData = ref<any>(null);
const allStats = ref<any[]>([]);
const lokasiChartData = ref<any>(null);
const paketChartData = ref<any>(null);
const growthChartData = ref<any>(null);
const invoiceChartData = ref<any>(null);
const statusChartData = ref<any>(null);
const alamatChartData = ref<any>(null);
const loyalitasChartData = ref<any>(null);

const paketDetailData = ref<any>({});
const dialogPaketDetail = ref(false);
const selectedPaketTitle = ref('');
const selectedPaketDetail = ref<any>(null);

// PERBAIKAN: Tipe yang benar untuk loyalitas variables
const dialogLoyalitas = ref(false);
const loyalitasUserList = ref<LoyalitasUser[]>([]);
const loadingLoyalitasDetail = ref(false);
const selectedLoyalitasSegmen = ref('');

// --- Computed Properties ---
const customerStats = computed(() => 
  allStats.value.filter(s => s.title.toLowerCase().includes('pelanggan'))
);
const serverStats = computed(() => 
  allStats.value.filter(s => s.title.toLowerCase().includes('server'))
);
const totalSubscriptions = computed(() => {
  if (!statusChartData.value?.datasets[0]?.data) {
    return 0;
  }
  return statusChartData.value.datasets[0].data.reduce((sum: number, current: number) => sum + current, 0);
});

const totalActiveCustomers = computed(() => {
  if (!loyalitasChartData.value?.datasets[0]?.data) {
    return 0;
  }
  return loyalitasChartData.value.datasets[0].data.reduce((sum: number, current: number) => sum + current, 0);
});

// --- Methods ---
const formatCurrency = (value: number) => {
  if (typeof value !== 'number') return 'Rp 0';
  return new Intl.NumberFormat('id-ID', {
    style: 'currency', currency: 'IDR', minimumFractionDigits: 0
  }).format(value);
};

function handlePaketChartClick(_event: any, elements: any[]) {
  if (elements.length === 0) return;
  const chart = elements[0].element.$context.chart;
  const index = elements[0].index;
  const label = chart.data.labels[index];
  const detail = paketDetailData.value[label];
  if (detail) {
    selectedPaketTitle.value = `Rincian Paket: ${label}`;
    selectedPaketDetail.value = detail;
    dialogPaketDetail.value = true;
  }
}

function getIconForBrand(brandName: string) {
  const name = brandName.toLowerCase();
  if (name.includes('jakinet')) return 'mdi-account-network';
  if (name.includes('nagrak')) return 'mdi-home-group';
  if (name.includes('jelantik')) return 'mdi-account-group';
  return 'mdi-tag-outline';
}

async function fetchPaketDetails() {
  try {
    const response = await apiClient.get('/dashboard/paket-details');
    paketDetailData.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data detail paket:", error);
  }
}

// Fungsi loyalitas dengan error handling yang lebih baik
async function handleLoyalitasChartClick(_event: any, elements: any[]) {
  if (elements.length === 0) return;

  const chart = elements[0].element.$context.chart;
  const index = elements[0].index;
  const label = chart.data.labels[index];

  try {
    // Reset dan set state
    selectedLoyalitasSegmen.value = label;
    loyalitasUserList.value = [];
    loadingLoyalitasDetail.value = true;
    
    // Buka dialog dulu
    dialogLoyalitas.value = true;

    // Small delay untuk memastikan dialog ter-render
    await new Promise(resolve => setTimeout(resolve, 100));

    // API call
    const response = await apiClient.get(`/dashboard/loyalitas-users-by-segment?segmen=${encodeURIComponent(label)}`);
    
    // Pastikan response data sesuai dengan interface
    loyalitasUserList.value = response.data.map((user: any) => ({
      id: user.id,
      nama: user.nama,
      id_pelanggan: user.id_pelanggan,
      alamat: user.alamat,
      no_telp: user.no_telp
    }));

  } catch (error) {
    console.error("Gagal mengambil detail user loyalitas:", error);
    loyalitasUserList.value = [];
  } finally {
    loadingLoyalitasDetail.value = false;
  }
}

// Fungsi helper
function getLoyaltyColor(segmen: string): string {
  if (segmen === "Setia On-Time") return "success";
  if (segmen === "Lunas (Tapi Telat)") return "warning";
  if (segmen === "Menunggak") return "error";
  return "primary";
}

function getShortLabel(segmen: string): string {
  if (segmen === "Setia On-Time") return "Setia";
  if (segmen === "Lunas (Tapi Telat)") return "Telat";
  if (segmen === "Menunggak") return "Nunggak";
  return segmen;
}

// PERBAIKAN: Chart options dengan tipe yang benar
const chartAxisColor = computed(() => theme.global.current.value.dark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)');
const chartGridColor = computed(() => theme.global.current.value.dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)');

// PERBAIKAN: Loyalitas donut options dengan tipe yang tepat
const loyalitasDonutOptions = computed((): ChartOptions<'doughnut'> => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  onClick: handleLoyalitasChartClick,
  plugins: { 
    legend: { 
      position: 'bottom' as const, // PERBAIKAN: Explicit as const
      labels: { 
        color: chartAxisColor.value, 
        usePointStyle: true, 
        pointStyle: 'circle' as const, // PERBAIKAN: Explicit as const
        padding: 20,
        font: { size: 12, weight: 'bold' as const } 
      }
    }
  },
}));

// Chart options lainnya
const chartOptions = computed((): ChartOptions<'bar'> => ({
  responsive: true,
  maintainAspectRatio: false,
  onClick: handlePaketChartClick,
  plugins: { 
    legend: { display: false },
    tooltip: {
      backgroundColor: theme.global.current.value.dark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
      titleColor: chartAxisColor.value,
      bodyColor: chartAxisColor.value,
      borderColor: chartGridColor.value,
      borderWidth: 1,
      cornerRadius: 8,
    }
  },
  scales: {
    y: { 
      beginAtZero: true, 
      grid: { color: chartGridColor.value },
      ticks: { color: chartAxisColor.value, font: { size: 12, weight: 'normal' as const } }
    },
    x: { 
      grid: { display: false },
      ticks: { color: chartAxisColor.value, font: { size: 12, weight: 'normal' as const } }
    },
  },
}));

const pieChartOptions = computed((): ChartOptions<'pie'> => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { 
      position: 'bottom' as const, 
      labels: { 
        color: chartAxisColor.value, 
        usePointStyle: true, 
        pointStyle: 'circle' as const, 
        padding: 20,
        font: { size: 12, weight: 'bold' as const } 
      }
    },
    tooltip: {
      backgroundColor: theme.global.current.value.dark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
      titleColor: chartAxisColor.value,
      bodyColor: chartAxisColor.value,
      borderColor: chartGridColor.value,
      borderWidth: 1,
      cornerRadius: 8,
    }
  },
}));

const donutChartOptions = computed((): ChartOptions<'doughnut'> => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: { 
    legend: { 
      position: 'bottom' as const, 
      labels: { 
        color: chartAxisColor.value, 
        usePointStyle: true, 
        pointStyle: 'circle' as const, 
        padding: 20,
        font: { size: 12, weight: 'bold' as const } 
      }
    }
  },
}));

const growthChartOptions = computed((): ChartOptions<'line'> => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' as const },
  plugins: { 
    legend: { 
      display: true, position: 'top' as const,
      labels: { color: chartAxisColor.value, usePointStyle: true, pointStyle: 'circle' as const, font: { size: 12, weight: 'bold' as const } }
    },
    tooltip: {
      backgroundColor: theme.global.current.value.dark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
      borderColor: 'rgb(236, 72, 153)',
      borderWidth: 2,
    }
  },
  scales: {
    y: { 
      beginAtZero: true, 
      grid: { color: chartGridColor.value },
      ticks: { color: chartAxisColor.value },
      title: { display: true, text: 'Jumlah Pelanggan Baru', color: chartAxisColor.value }
    },
    x: { 
      grid: { display: false },
      ticks: { color: chartAxisColor.value },
      title: { display: true, text: 'Periode', color: chartAxisColor.value }
    },
  },
}));

const invoiceChartOptions = computed((): ChartOptions<'bar'> => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { 
      position: 'top' as const, 
      labels: { color: chartAxisColor.value, usePointStyle: true, pointStyle: 'circle' as const, font: { size: 12, weight: 'bold' as const } }
    },
  },
  scales: {
    y: { 
      stacked: true, 
      beginAtZero: true, 
      grid: { color: chartGridColor.value },
      ticks: { color: chartAxisColor.value }
    },
    x: { 
      stacked: true, 
      grid: { display: false },
      ticks: { color: chartAxisColor.value }
    },
  },
}));

// Helper functions for stats
function getIconForStat(title: string) {
  if (title.toLowerCase().includes('jakinet')) return 'mdi-account-network';
  if (title.toLowerCase().includes('jelantik')) return 'mdi-account-group';
  if (title.toLowerCase().includes('nagrak')) return 'mdi-home-group';
  if (title.toLowerCase().includes('total servers')) return 'mdi-server';
  if (title.toLowerCase().includes('online')) return 'mdi-check-circle';
  if (title.toLowerCase().includes('offline')) return 'mdi-close-circle';
  return 'mdi-chart-box';
}

function getColorForStat(title: string) {
  if (title.toLowerCase().includes('jakinet')) return 'primary';
  if (title.toLowerCase().includes('jelantik')) return 'success';
  if (title.toLowerCase().includes('nagrak')) return 'warning';
  if (title.toLowerCase().includes('total servers')) return 'error';
  if (title.toLowerCase().includes('online')) return 'success';
  if (title.toLowerCase().includes('offline')) return 'error';
  return 'primary';
}

//Download gambar untuk Chart
function downloadAsPNG(elementId: string, filename: string) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Elemen dengan ID '${elementId}' tidak ditemukan.`);
        return;
    }

    html2canvas(element, {
        useCORS: true, // Penting jika ada gambar atau elemen eksternal
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = filename;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }).catch(error => {
        console.error("Gagal men-download gambar:", error);
    });
}

// onMounted tetap sama seperti sebelumnya
onMounted(async () => {
  loading.value = true;
  try {
    const response = await apiClient.get('/dashboard/');
    const data = response.data;

    revenueData.value = data.revenue_summary;
    
    allStats.value = (data.stat_cards || []).map((card: any) => ({
      ...card,
      icon: getIconForStat(card.title),
      color: getColorForStat(card.title)
    }));
    
    // Setup chart data...
    if (data.lokasi_chart) {
      lokasiChartData.value = {
        labels: data.lokasi_chart.labels,
        datasets: [{
          label: 'Jumlah Pelanggan',
          data: data.lokasi_chart.data,
          backgroundColor: 'rgba(99, 102, 241, 0.8)',
          borderRadius: 8,
        }]
      };
    }

    if (data.paket_chart) {
      paketChartData.value = {
        labels: data.paket_chart.labels,
        datasets: [{
          label: 'Jumlah Pelanggan',
          data: data.paket_chart.data,
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderRadius: 8,
        }]
      };
    }

    if (data.growth_chart) {
      growthChartData.value = {
        labels: data.growth_chart.labels,
        datasets: [{
          label: 'Pelanggan Baru',
          data: data.growth_chart.data,
          borderColor: 'rgb(236, 72, 153)',
          backgroundColor: 'rgba(236, 72, 153, 0.1)',
          tension: 0.4,
          fill: true,
        }]
      };
    }
    
    if (data.invoice_summary_chart) {
      invoiceChartData.value = {
        labels: data.invoice_summary_chart.labels,
        datasets: [
            { type: 'line', label: 'Total Invoice', data: data.invoice_summary_chart.total, borderColor: 'rgb(168, 85, 247)', tension: 0.4, fill: true },
            { type: 'bar', label: 'Lunas', data: data.invoice_summary_chart.lunas, backgroundColor: 'rgba(34, 197, 94, 0.8)', stack: 'Stack 0' },
            { type: 'bar', label: 'Menunggu', data: data.invoice_summary_chart.menunggu, backgroundColor: 'rgba(251, 191, 36, 0.8)', stack: 'Stack 0' },
            { type: 'bar', label: 'Kadaluarsa', data: data.invoice_summary_chart.kadaluarsa, backgroundColor: 'rgba(239, 68, 68, 0.8)', stack: 'Stack 0' },
        ]
      };
    }

    if (data.status_langganan_chart) {
      statusChartData.value = {
        labels: data.status_langganan_chart.labels,
        datasets: [{
            data: data.status_langganan_chart.data,
            backgroundColor: ['#22c55e', '#ef4444', '#f59e0b'], 
            borderColor: theme.global.current.value.dark ? '#1E1E1E' : '#FFFFFF',
            borderWidth: 4,
        }]
      };
    }

    if (data.loyalitas_pembayaran_chart) {
      loyalitasChartData.value = {
        labels: data.loyalitas_pembayaran_chart.labels,
        datasets: [{
            data: data.loyalitas_pembayaran_chart.data,
            backgroundColor: ['#22c55e', '#f97316', '#ef4444'], 
            borderColor: theme.global.current.value.dark ? '#1E1E1E' : '#FFFFFF',
            borderWidth: 4,
        }]
      };
    }

    if (data.pelanggan_per_alamat_chart) {
      alamatChartData.value = {
        labels: data.pelanggan_per_alamat_chart.labels,
        datasets: [{
            data: data.pelanggan_per_alamat_chart.data,
            backgroundColor: [
              '#6366f1', '#22c55e', '#f97316', '#3b82f6', 
              '#ec4899', '#f59e0b', '#10b981'
            ], 
            borderColor: theme.global.current.value.dark ? '#1E1E1E' : '#FFFFFF',
            borderWidth: 4,
        }]
      };
    }

    fetchPaketDetails();

  } catch (error) {
    console.error("Failed to fetch dashboard data:", error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* Base Styling */
.dashboard-container {
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02) 0%, rgba(34, 197, 94, 0.02) 100%);
  min-height: 100vh;
  animation: fadeIn 0.6s ease-out;
}

/* === STYLING BARU UNTUK LAYOUT ATAS === */
.top-layout-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

@media (min-width: 960px) {
  .top-layout-grid {
    grid-template-columns: 1.5fr 2fr; /* Widget pendapatan lebih besar */
  }
}

/* === MODIFIKASI CSS UNTUK WIDGET PENDAPATAN === */
.revenue-widget-container { min-height: 220px; }

.revenue-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  color: white;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.2);
  transition: all 0.3s ease-in-out;
  height: 100%;
}

.donut-container {
  position: relative;
}

.total-in-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none; /* Agar tidak mengganggu tooltip chart */
}

.total-in-center h3 {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.2;
}

.total-in-center span {
  font-size: 0.8rem;
  font-weight: 500;
  opacity: 0.7;
}

/* Gunakan flexbox untuk membagi kartu menjadi dua bagian */
.revenue-card-content {
  z-index: 2;
  position: relative;
  display: flex;
  height: 100%;
  padding: 0; /* Hapus padding lama */
}

/* Bagian utama (kiri) untuk total pendapatan */
.revenue-main {
  flex: 1.2; /* Beri ruang lebih besar untuk total */
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Garis pemisah di tengah */
.revenue-divider {
  width: 1px;
  background: rgba(255, 255, 255, 0.25);
  margin: 1.5rem 0;
}

/* Bagian rincian (kanan) untuk brand */
.revenue-breakdown {
  flex: 1; /* Ruang lebih kecil */
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  justify-content: space-around; /* Beri jarak antar item */
  background: rgba(0, 0, 0, 0.1);
}

.breakdown-item {
  text-align: left;
}

.breakdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breakdown-title {
  font-size: 0.9rem; /* Sedikit lebih kecil */
  font-weight: 600;
  opacity: 0.9;
}

.breakdown-icon {
  opacity: 0.8;
}

.breakdown-value {
  font-size: 1.5rem; /* Lebih kecil dari total utama */
  font-weight: 700;
  line-height: 1.2;
  margin: 0.25rem 0;
}
.revenue-breakdown {
  justify-content: center; /* Mengubah dari space-around agar lebih rapi */
  gap: 0.5rem; /* Menambahkan sedikit jarak */
}

.breakdown-value {
  font-size: 1.35rem; /* Sedikit lebih kecil agar muat */
}

.breakdown-title {
  font-size: 0.85rem; /* Sedikit lebih kecil agar muat */
}
.breakdown-period {
  font-size: 0.7rem; /* Sangat kecil */
  font-weight: 500;
  opacity: 0.7;
  letter-spacing: 0.5px;
}


.revenue-card:hover { transform: translateY(-5px); box-shadow: 0 15px 25px rgba(59, 130, 246, 0.3); }

.revenue-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.revenue-title { font-size: 1rem; font-weight: 600; opacity: 0.9; }
.revenue-icon-wrapper { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.2); }
.revenue-body { text-align: left; }
.revenue-value { font-size: 2.5rem; font-weight: 800; line-height: 1.2; margin: 0 0 0.25rem 0; }
.revenue-period { font-size: 0.875rem; font-weight: 500; opacity: 0.8; }

.stats-subgrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.5rem;
}

/* Header Section - Improved Responsive Layout */
.dashboard-header {
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.title-section {
  flex: 1;
  min-width: 0; /* Prevents flex item from overflowing */
}

.dashboard-title {
  color: rgb(var(--v-theme-on-background));
  font-weight: 800;
  font-size: 2rem;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, #6366f1 0%, #22c55e 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

.title-icon {
  background: linear-gradient(135deg, #6366f1 0%, #22c55e 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  flex-shrink: 0;
}

.dashboard-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
}

/* Header Actions - Improved Layout */
.header-actions {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
}

.status-chip {
  font-weight: 600;
  font-size: 0.75rem;
  height: 32px;
  white-space: nowrap;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
  transition: all 0.2s ease;
}

.status-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

@media (min-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .revenue-card-content {
    flex-direction: row; /* Kembali ke row di layar besar */
  }
  .revenue-divider {
    width: 1px;
    height: auto;
    margin: 1.5rem 0;
  }
}

/* Stat Cards */
.stat-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card.card-0::before { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.stat-card.card-1::before { background: linear-gradient(90deg, #22c55e, #10b981); }
.stat-card.card-2::before { background: linear-gradient(90deg, #f59e0b, #f97316); }
.stat-card.card-3::before { background: linear-gradient(90deg, #ef4444, #ec4899); }

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  border-color: rgba(99, 102, 241, 0.3);
}

.stat-card-content {
  padding: 1.25rem;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.stat-icon-container {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(99, 102, 241, 0.05));
  transition: all 0.2s ease;
}

.stat-card:hover .stat-icon-container {
  transform: scale(1.1);
}

.stat-icon-container.icon-0 { background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.05)); }
.stat-icon-container.icon-1 { background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.05)); }
.stat-icon-container.icon-2 { background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(249, 115, 22, 0.05)); }
.stat-icon-container.icon-3 { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(236, 72, 153, 0.05)); }

.stat-body {
  margin-bottom: 1rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-title {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.stat-description {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.4;
}

.progress-bar {
  height: 3px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  width: 75%;
  animation: progressFill 1.5s ease-out;
}

.progress-fill.progress-0 { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.progress-fill.progress-1 { background: linear-gradient(90deg, #22c55e, #10b981); }
.progress-fill.progress-2 { background: linear-gradient(90deg, #f59e0b, #f97316); }
.progress-fill.progress-3 { background: linear-gradient(90deg, #ef4444, #ec4899); }

/* Charts Section */
.charts-section {
  display: flex;
  flex-direction: column;
  gap: 3rem;
  margin-bottom: 2rem; 
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.chart-title-section {
  flex: 1;
}

.chart-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(99, 102, 241, 0.05));
  transition: all 0.2s ease;
}

.chart-card:hover .chart-icon-wrapper {
  transform: scale(1.1);
}

.chart-icon {
  color: rgb(var(--v-theme-primary));
  font-size: 16px;
}

.chart-subtitle {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

.chart-container {
  height: 250px;
  position: relative;
}

.large-chart {
  height: 350px;
}

/* Animations */
@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

@keyframes progressFill {
  from { width: 0; }
  to { width: 75%; }
}

/* Dark Theme */
.v-theme--dark .dashboard-header,
.v-theme--dark .stat-card,
.v-theme--dark .chart-card {
  background: rgba(30, 30, 30, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .dashboard-container {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(34, 197, 94, 0.05) 100%);
}

.v-theme--dark .status-chip {
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
}

.stat-card-skeleton {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* Responsive Design */
@media (max-width: 1200px) {
    .revenue-card-content {
    flex-direction: column;
  }
  .revenue-divider {
    width: auto;
    height: 1px;
    margin: 0 1.5rem;
  }
  .revenue-main, .revenue-breakdown {
    flex: none; /* Hapus flex-grow */
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1rem;
  }
  
  .dashboard-header {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .dashboard-title {
    font-size: 1.75rem;
  }
  
  .dashboard-subtitle {
    font-size: 0.9rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 0.875rem;
  }
  
  .charts-row {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    padding: 0.75rem;
  }
  
  .dashboard-header {
    padding: 0.875rem;
    margin-bottom: 1rem;
  }
  
  .dashboard-title {
    font-size: 1.5rem;
    gap: 0.5rem;
  }
  
  .dashboard-subtitle {
    font-size: 0.85rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .stat-card-content {
    padding: 1rem;
  }
  
  .chart-card {
    padding: 1rem;
  }
  
  .status-chip {
    font-size: 0.7rem;
    height: 28px;
  }
}

@media (max-width: 360px) {
  .header-content {
    gap: 0.75rem;
  }
  
  .dashboard-title {
    font-size: 1.375rem;
  }
  
  .dashboard-subtitle {
    font-size: 0.8rem;
  }
  
  .status-chip {
    font-size: 0.65rem;
    height: 26px;
  }
}

/* Improved Mobile Layout for System Active */
@media (max-width: 640px) {
  .header-content {
    align-items: stretch;
  }
  
  .header-actions {
    margin-top: 0.5rem;
    justify-content: flex-end;
  }
  
  .status-chip {
    align-self: flex-start;
  }
}

/* Dialog Card Styling */
.package-detail-card {
  border-radius: 20px !important;
  overflow: hidden;
  position: relative;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
}

/* Header Section */
.dialog-header {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.header-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  opacity: 0.95;
}

.header-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem 2rem;
  color: white;
}

.header-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.header-text {
  flex: 1;
}

.dialog-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: white;
  line-height: 1.2;
}

.dialog-subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0.25rem 0 0 0;
  font-weight: 500;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 3;
  background: rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(10px);
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
}

/* Dialog Content */
.dialog-content {
  padding: 2rem !important;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.8) 0%, rgba(255, 255, 255, 0.9) 100%);
}

/* Summary Section */
.summary-section {
  margin-bottom: 2rem;
}

.summary-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
}

.summary-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
}

.summary-label {
  font-size: 0.9rem;
  color: rgba(99, 102, 241, 0.8);
  font-weight: 600;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 2rem;
  font-weight: 800;
  color: rgb(99, 102, 241);
  line-height: 1;
}

/* Content Sections */
.content-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.detail-section {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.detail-section:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

/* Section Headers */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.section-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.location-icon {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(33, 150, 243, 0.08) 100%);
  color: rgb(33, 150, 243);
}

.brand-icon {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(76, 175, 80, 0.08) 100%);
  color: rgb(76, 175, 80);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

/* Items Grid */
.items-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: rgba(248, 250, 252, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.detail-item:hover {
  background: rgba(248, 250, 252, 0.9);
  transform: translateX(4px);
  border-color: rgba(99, 102, 241, 0.2);
}

.item-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.item-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 0.125rem;
}

.item-subtitle {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.item-value {
  flex-shrink: 0;
}

.value-chip {
  font-weight: 700;
  min-width: 48px;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Dialog Footer */
.dialog-footer {
  padding: 1.5rem 2rem !important;
  background: rgba(248, 250, 252, 0.6);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.close-action-btn {
  border-radius: 12px;
  font-weight: 600;
  padding: 0 2rem;
  height: 44px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
  text-transform: none;
  letter-spacing: 0.25px;
}

.close-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}

/* Dark Theme Support */
.v-theme--dark .package-detail-card {
  background: rgba(30, 30, 30, 0.98);
}

.v-theme--dark .dialog-content {
  background: linear-gradient(180deg, rgba(18, 18, 18, 0.8) 0%, rgba(30, 30, 30, 0.9) 100%);
}

.v-theme--dark .summary-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%);
  border-color: rgba(99, 102, 241, 0.2);
}

.v-theme--dark .detail-section {
  background: rgba(40, 40, 40, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .detail-item {
  background: rgba(50, 50, 50, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .detail-item:hover {
  background: rgba(50, 50, 50, 0.8);
  border-color: rgba(99, 102, 241, 0.3);
}

.v-theme--dark .item-icon {
  background: rgba(60, 60, 60, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .dialog-footer {
  background: rgba(25, 25, 25, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

/* Responsive Design */
@media (max-width: 768px) {
  .package-detail-card {
    margin: 1rem;
    max-width: calc(100vw - 2rem) !important;
  }

  .header-content {
    padding: 1.25rem 1.5rem;
  }

  .dialog-content {
    padding: 1.5rem !important;
  }

  .content-sections {
    gap: 1.5rem;
  }

  .detail-section {
    padding: 1.25rem;
  }

  .summary-card {
    padding: 1.25rem;
  }

  .dialog-title {
    font-size: 1.25rem;
  }

  .summary-value {
    font-size: 1.75rem;
  }

  .close-btn {
    top: 0.75rem;
    right: 0.75rem;
  }

  .dialog-footer {
    padding: 1.25rem 1.5rem !important;
  }
}

@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem 1.25rem 1.25rem;
  }

  .header-text {
    text-align: center;
  }

  .dialog-content {
    padding: 1.25rem !important;
  }

  .summary-card {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
    padding: 1rem;
  }

  .content-sections {
    gap: 1.25rem;
  }

  .detail-section {
    padding: 1rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    text-align: left;
  }

  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
  }

  .item-content {
    width: 100%;
  }

  .item-value {
    align-self: flex-end;
  }
}

/* Loading Section */
.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
}

.loading-text {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-weight: 500;
}

/* Users Section */
.users-section {
  margin-top: 2rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.section-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  gap: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Users Grid */
.users-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(248, 250, 252, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.user-card:hover {
  background: rgba(248, 250, 252, 1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 0.5rem 0;
  line-height: 1.2;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.user-badge {
  flex-shrink: 0;
}

.status-chip {
  font-weight: 600;
  font-size: 0.75rem;
}

/* Dark Theme */
.v-theme--dark .user-card {
  background: rgba(50, 50, 50, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .user-card:hover {
  background: rgba(50, 50, 50, 0.8);
  border-color: rgba(99, 102, 241, 0.3);
}

.v-theme--dark .user-avatar {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.25);
}

/* Responsive */
@media (max-width: 640px) {
  .user-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
  }

  .user-badge {
    align-self: flex-end;
  }
  
  .users-grid {
    gap: 0.75rem;
  }
}

</style>