<template>
  <v-container fluid class="pa-6">
    <!-- Header Section -->
    <div class="dashboard-header mb-6">
      <h1 class="text-h4 font-weight-bold text-primary mb-2">Dashboard Monitoring Pelanggan</h1>
      <p class="text-subtitle-1 text-medium-emphasis">Pantau performa dan aktivitas pelanggan secara real-time</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      <p class="mt-4 text-h6">Memuat data statistik...</p>
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- Stats Cards Row -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card 
            rounded="xl" 
            class="stats-card active-customers" 
            elevation="2"
            hover
          >
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-2">
                <v-avatar color="primary" size="48" class="me-3">
                  <v-icon color="white" size="24">mdi-account-check</v-icon>
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-caption text-medium-emphasis">PELANGGAN AKTIF</div>
                  <div class="text-h4 font-weight-bold text-primary">{{ stats.pelanggan_aktif }}</div>
                </div>
              </div>
              <v-progress-linear 
                :model-value="(stats.pelanggan_aktif / (stats.pelanggan_aktif + stats.pelanggan_berhenti_bulan_ini)) * 100" 
                color="primary" 
                height="6" 
                rounded
                class="mt-2"
              ></v-progress-linear>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card 
            rounded="xl" 
            class="stats-card new-customers" 
            elevation="2"
            hover
          >
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-2">
                <v-avatar color="success" size="48" class="me-3">
                  <v-icon color="white" size="24">mdi-account-plus</v-icon>
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-caption text-medium-emphasis">PELANGGAN BARU</div>
                  <div class="text-h4 font-weight-bold text-success">{{ stats.pelanggan_baru_bulan_ini }}</div>
                </div>
              </div>
              <div class="text-caption text-success">
                <v-icon size="16" class="me-1">mdi-trending-up</v-icon>
                Bulan ini
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card 
            rounded="xl" 
            class="stats-card stopped-customers" 
            elevation="2"
            hover
          >
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-2">
                <v-avatar color="error" size="48" class="me-3">
                  <v-icon color="white" size="24">mdi-account-minus</v-icon>
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-caption text-medium-emphasis">BERHENTI</div>
                  <div class="text-h4 font-weight-bold text-error">{{ stats.pelanggan_berhenti_bulan_ini }}</div>
                </div>
              </div>
              <div class="text-caption text-error">
                <v-icon size="16" class="me-1">mdi-trending-down</v-icon>
                Bulan ini
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card 
            rounded="xl" 
            class="stats-card jakinet-customers" 
            elevation="2"
            hover
          >
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-2">
                <v-avatar color="info" size="48" class="me-3">
                  <v-icon color="white" size="24">mdi-wifi</v-icon>
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-caption text-medium-emphasis">JAKINET AKTIF</div>
                  <div class="text-h4 font-weight-bold text-info">{{ stats.pelanggan_jakinet_aktif }}</div>
                </div>
              </div>
              <v-progress-linear 
                :model-value="(stats.pelanggan_jakinet_aktif / stats.pelanggan_aktif) * 100" 
                color="info" 
                height="6" 
                rounded
                class="mt-2"
              ></v-progress-linear>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Revenue Card -->
      <v-row class="mb-6">
        <v-col cols="12">
          <v-card rounded="xl" elevation="3" class="revenue-card">
            <v-card-text class="pa-6">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <h3 class="text-h5 font-weight-bold mb-1">Pendapatan JakiNet</h3>
                  <p class="text-subtitle-2 text-medium-emphasis">Bulan ini</p>
                </div>
                <v-avatar color="success" size="56">
                  <v-icon color="white" size="28">mdi-cash-multiple</v-icon>
                </v-avatar>
              </div>
              
              <div class="revenue-amount mb-4">
                <span class="text-h3 font-weight-bold text-success">{{ formatCurrency(stats.pendapatan_jakinet_bulan_ini) }}</span>
              </div>

              <div class="d-flex align-center">
                <v-chip color="success" variant="tonal" size="small" class="me-2">
                  <v-icon start size="16">mdi-trending-up</v-icon>
                  Aktif
                </v-chip>
                <span class="text-caption text-medium-emphasis">
                  {{ ((stats.pelanggan_jakinet_aktif / stats.pelanggan_aktif) * 100).toFixed(1) }}% dari total pelanggan
                </span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Charts Section -->
      <v-row class="mb-6">
        <!-- Customer Distribution Pie Chart -->
        <v-col cols="12" md="6">
          <v-card rounded="xl" elevation="2" height="400">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="primary" class="me-2">mdi-chart-pie</v-icon>
                <span class="font-weight-bold">Distribusi Pelanggan</span>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <div class="chart-container" style="height: 280px; position: relative;">
                <canvas ref="pieChartCanvas" style="max-height: 280px;"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Customer Growth Trend -->
        <v-col cols="12" md="6">
          <v-card rounded="xl" elevation="2" height="400">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="info" class="me-2">mdi-chart-line</v-icon>
                <span class="font-weight-bold">Tren Pertumbuhan</span>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <div class="chart-container" style="height: 280px; position: relative;">
                <canvas ref="lineChartCanvas" style="max-height: 280px;"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Detailed Analytics Row -->
      <v-row class="mb-6">
        <!-- Customer Status Overview -->
        <v-col cols="12" md="8">
          <v-card rounded="xl" elevation="2" height="350">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center justify-space-between w-100">
                <div class="d-flex align-center">
                  <v-icon color="purple" class="me-2">mdi-chart-bar</v-icon>
                  <span class="font-weight-bold">Status Pelanggan Overview</span>
                </div>
                <v-chip color="purple" variant="tonal" size="small">
                  Real-time
                </v-chip>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <div class="chart-container" style="height: 250px; position: relative;">
                <canvas ref="barChartCanvas" style="max-height: 250px;"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Quick Stats Panel -->
        <v-col cols="12" md="4">
          <v-card rounded="xl" elevation="2" height="350">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="orange" class="me-2">mdi-speedometer</v-icon>
                <span class="font-weight-bold">Metrics Cepat</span>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <div class="quick-stats">
                <!-- Growth Rate -->
                <div class="stat-item mb-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-body-2 text-medium-emphasis">Growth Rate</span>
                    <v-chip :color="growthRate >= 0 ? 'success' : 'error'" variant="tonal" size="small">
                      {{ growthRate >= 0 ? '+' : '' }}{{ growthRate.toFixed(1) }}%
                    </v-chip>
                  </div>
                  <v-progress-linear 
                    :model-value="Math.abs(growthRate)" 
                    :color="growthRate >= 0 ? 'success' : 'error'" 
                    height="8" 
                    rounded
                  ></v-progress-linear>
                </div>

                <!-- JakiNet Penetration -->
                <div class="stat-item mb-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-body-2 text-medium-emphasis">JakiNet Penetration</span>
                    <span class="font-weight-bold">{{ jakiNetPenetration.toFixed(1) }}%</span>
                  </div>
                  <v-progress-linear 
                    :model-value="jakiNetPenetration" 
                    color="info" 
                    height="8" 
                    rounded
                  ></v-progress-linear>
                </div>

                <!-- Customer Retention -->
                <div class="stat-item mb-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-body-2 text-medium-emphasis">Customer Retention</span>
                    <span class="font-weight-bold text-success">{{ customerRetention.toFixed(1) }}%</span>
                  </div>
                  <v-progress-linear 
                    :model-value="customerRetention" 
                    color="success" 
                    height="8" 
                    rounded
                  ></v-progress-linear>
                </div>

                <!-- Average Revenue Per User -->
                <div class="stat-item">
                  <div class="text-center pa-4 bg-surface rounded-lg">
                    <div class="text-caption text-medium-emphasis">ARPU (Avg Revenue Per User)</div>
                    <div class="text-h5 font-weight-bold text-warning mt-1">
                      {{ formatCurrency(averageRevenuePerUser) }}
                    </div>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Additional Analytics Row -->
      <v-row>
        <!-- Monthly Revenue Trend -->
        <v-col cols="12" md="8">
          <v-card rounded="xl" elevation="2" height="400">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center justify-space-between w-100">
                <div class="d-flex align-center">
                  <v-icon color="success" class="me-2">mdi-chart-areaspline</v-icon>
                  <span class="font-weight-bold">Tren Pendapatan Bulanan</span>
                </div>
                <v-btn-toggle v-model="revenueTimeframe" color="primary" size="small" density="compact">
                  <v-btn value="3m" size="small">3M</v-btn>
                  <v-btn value="6m" size="small">6M</v-btn>
                  <v-btn value="1y" size="small">1Y</v-btn>
                </v-btn-toggle>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <div class="chart-container" style="height: 300px; position: relative;">
                <canvas ref="revenueChartCanvas" style="max-height: 300px;"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Activity Feed -->
        <v-col cols="12" md="4">
          <v-card rounded="xl" elevation="2" height="400">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="info" class="me-2">mdi-timeline-clock</v-icon>
                <span class="font-weight-bold">Aktivitas Terkini</span>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <v-timeline density="compact" class="timeline-custom">
                <v-timeline-item
                  v-for="(activity, index) in recentActivities"
                  :key="index"
                  :dot-color="activity.color"
                  size="small"
                  class="mb-2"
                >
                  <template v-slot:icon>
                    <v-icon size="16" color="white">{{ activity.icon }}</v-icon>
                  </template>
                  <div class="activity-content">
                    <div class="text-body-2 font-weight-medium">{{ activity.title }}</div>
                    <div class="text-caption text-medium-emphasis">{{ activity.description }}</div>
                    <div class="text-caption text-medium-emphasis">{{ activity.time }}</div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Performance Indicators -->
      <v-row class="mt-6">
        <v-col cols="12">
          <v-card rounded="xl" elevation="2">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="deep-purple" class="me-2">mdi-gauge</v-icon>
                <span class="font-weight-bold">Key Performance Indicators</span>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <v-row>
                <v-col cols="12" sm="6" md="3">
                  <div class="kpi-item text-center pa-4">
                    <v-progress-circular
                      :model-value="jakiNetPenetration"
                      :size="80"
                      :width="8"
                      color="info"
                      class="mb-3"
                    >
                      <span class="text-body-1 font-weight-bold">{{ jakiNetPenetration.toFixed(0) }}%</span>
                    </v-progress-circular>
                    <div class="text-body-2 font-weight-medium">JakiNet Adoption</div>
                  </div>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                  <div class="kpi-item text-center pa-4">
                    <v-progress-circular
                      :model-value="customerRetention"
                      :size="80"
                      :width="8"
                      color="success"
                      class="mb-3"
                    >
                      <span class="text-body-1 font-weight-bold">{{ customerRetention.toFixed(0) }}%</span>
                    </v-progress-circular>
                    <div class="text-body-2 font-weight-medium">Retention Rate</div>
                  </div>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                  <div class="kpi-item text-center pa-4">
                    <v-progress-circular
                      :model-value="Math.abs(growthRate) > 100 ? 100 : Math.abs(growthRate)"
                      :size="80"
                      :width="8"
                      :color="growthRate >= 0 ? 'success' : 'error'"
                      class="mb-3"
                    >
                      <span class="text-body-1 font-weight-bold">{{ Math.abs(growthRate).toFixed(0) }}%</span>
                    </v-progress-circular>
                    <div class="text-body-2 font-weight-medium">Growth Rate</div>
                  </div>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                  <div class="kpi-item text-center pa-4">
                    <div class="revenue-gauge mb-3">
                      <v-progress-circular
                        :model-value="(stats.pendapatan_jakinet_bulan_ini / 50000000) * 100"
                        :size="80"
                        :width="8"
                        color="warning"
                      >
                        <span class="text-caption font-weight-bold">TARGET</span>
                      </v-progress-circular>
                    </div>
                    <div class="text-body-2 font-weight-medium">Revenue Target</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue';
import apiClient from '@/services/api';
import { Chart, ChartConfiguration, DoughnutController, ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, LineController, BarController } from 'chart.js';

// Register Chart.js components
Chart.register(
  DoughnutController,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  LineController,
  BarController,
  Title,
  Tooltip,
  Legend
);

const loading = ref(true);
const revenueTimeframe = ref('6m');
const stats = ref({
  pelanggan_aktif: 0,
  pelanggan_baru_bulan_ini: 0,
  pelanggan_berhenti_bulan_ini: 0,
  pelanggan_jakinet_aktif: 0, 
  pendapatan_jakinet_bulan_ini: 0,
});

// Chart refs
const pieChartCanvas = ref<HTMLCanvasElement>();
const lineChartCanvas = ref<HTMLCanvasElement>();
const barChartCanvas = ref<HTMLCanvasElement>();
const revenueChartCanvas = ref<HTMLCanvasElement>();

let pieChart: Chart | null = null;
let lineChart: Chart | null = null;
let barChart: Chart | null = null;
let revenueChart: Chart | null = null;

// Mock data for activities
const recentActivities = ref([
  {
    title: 'Pelanggan Baru Terdaftar',
    description: 'Ahmad Wijaya bergabung dengan paket JakiNet 50Mbps',
    time: '2 menit yang lalu',
    color: 'success',
    icon: 'mdi-account-plus'
  },
  {
    title: 'Pembayaran Diterima',
    description: 'Invoice #INV-2024-001 telah lunas',
    time: '15 menit yang lalu',
    color: 'info',
    icon: 'mdi-cash-check'
  },
  {
    title: 'Data Teknis Diperbarui',
    description: 'Konfigurasi ONU untuk pelanggan Sari Indah',
    time: '1 jam yang lalu',
    color: 'warning',
    icon: 'mdi-cog-sync'
  },
  {
    title: 'Langganan Ditangguhkan',
    description: 'Pelanggan Budi Santoso - Overdue payment',
    time: '2 jam yang lalu',
    color: 'error',
    icon: 'mdi-pause-circle'
  },
  {
    title: 'Upgrade Paket',
    description: 'Lisa Permata upgrade ke 100Mbps',
    time: '3 jam yang lalu',
    color: 'purple',
    icon: 'mdi-arrow-up-bold'
  }
]);

// Computed properties
const growthRate = computed(() => {
  const base = stats.value.pelanggan_aktif - stats.value.pelanggan_baru_bulan_ini;
  return base > 0 ? ((stats.value.pelanggan_baru_bulan_ini - stats.value.pelanggan_berhenti_bulan_ini) / base) * 100 : 0;
});

const jakiNetPenetration = computed(() => {
  return stats.value.pelanggan_aktif > 0 ? (stats.value.pelanggan_jakinet_aktif / stats.value.pelanggan_aktif) * 100 : 0;
});

const customerRetention = computed(() => {
  const totalCustomers = stats.value.pelanggan_aktif + stats.value.pelanggan_berhenti_bulan_ini;
  return totalCustomers > 0 ? (stats.value.pelanggan_aktif / totalCustomers) * 100 : 0;
});

const averageRevenuePerUser = computed(() => {
  return stats.value.pelanggan_jakinet_aktif > 0 ? stats.value.pendapatan_jakinet_bulan_ini / stats.value.pelanggan_jakinet_aktif : 0;
});



async function fetchStats() {
  loading.value = true;
  try {
    const response = await apiClient.get('/dashboard-pelanggan/statistik-utama');
    stats.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data statistik utama:", error);
  } finally {
    loading.value = false;
  }
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency', 
    currency: 'IDR', 
    minimumFractionDigits: 0
  }).format(value);
}

function createPieChart() {
  if (!pieChartCanvas.value) return;
  
  const ctx = pieChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (pieChart) {
    pieChart.destroy();
  }

  const config: ChartConfiguration<'doughnut'> = {
    type: 'doughnut',
    data: {
      labels: ['JakiNet Aktif', 'Non-JakiNet', 'Berhenti'],
      datasets: [{
        data: [
          stats.value.pelanggan_jakinet_aktif,
          stats.value.pelanggan_aktif - stats.value.pelanggan_jakinet_aktif,
          stats.value.pelanggan_berhenti_bulan_ini
        ],
        backgroundColor: [
          'rgb(33, 150, 243)',
          'rgb(156, 163, 175)',
          'rgb(244, 67, 54)'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            font: {
              size: 12,
              weight: 500
            }
          }
        }
      }
    }
  };

  pieChart = new Chart(ctx, config);
}

function createLineChart() {
  if (!lineChartCanvas.value) return;
  
  const ctx = lineChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (lineChart) {
    lineChart.destroy();
  }

  // Mock data for growth trend
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'];
  const customerGrowth = [45, 52, 48, 61, 58, stats.value.pelanggan_aktif];
  const jakiNetGrowth = [20, 28, 32, 38, 42, stats.value.pelanggan_jakinet_aktif];

  const config: ChartConfiguration<'line'> = {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Total Pelanggan',
          data: customerGrowth,
          borderColor: 'rgb(33, 150, 243)',
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 6,
          pointHoverRadius: 8
        },
        {
          label: 'JakiNet',
          data: jakiNetGrowth,
          borderColor: 'rgb(76, 175, 80)',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 6,
          pointHoverRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        }
      }
    }
  };

  lineChart = new Chart(ctx, config);
}

function createBarChart() {
  if (!barChartCanvas.value) return;
  
  const ctx = barChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (barChart) {
    barChart.destroy();
  }

  const config: ChartConfiguration<'bar'> = {
    type: 'bar',
    data: {
      labels: ['Aktif', 'Baru', 'Berhenti', 'JakiNet'],
      datasets: [{
        label: 'Jumlah Pelanggan',
        data: [
          stats.value.pelanggan_aktif,
          stats.value.pelanggan_baru_bulan_ini,
          stats.value.pelanggan_berhenti_bulan_ini,
          stats.value.pelanggan_jakinet_aktif
        ],
        backgroundColor: [
          'rgba(33, 150, 243, 0.8)',
          'rgba(76, 175, 80, 0.8)',
          'rgba(244, 67, 54, 0.8)',
          'rgba(156, 39, 176, 0.8)'
        ],
        borderColor: [
          'rgb(33, 150, 243)',
          'rgb(76, 175, 80)',
          'rgb(244, 67, 54)',
          'rgb(156, 39, 176)'
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  };

  barChart = new Chart(ctx, config);
}

function createRevenueChart() {
  if (!revenueChartCanvas.value) return;
  
  const ctx = revenueChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (revenueChart) {
    revenueChart.destroy();
  }

  // Mock revenue data based on timeframe
  const getRevenueData = () => {
    const currentRevenue = stats.value.pendapatan_jakinet_bulan_ini;
    switch (revenueTimeframe.value) {
      case '3m':
        return {
          labels: ['Apr', 'Mei', 'Jun'],
          data: [currentRevenue * 0.8, currentRevenue * 0.9, currentRevenue]
        };
      case '6m':
        return {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'],
          data: [
            currentRevenue * 0.6, 
            currentRevenue * 0.7, 
            currentRevenue * 0.75, 
            currentRevenue * 0.8, 
            currentRevenue * 0.9, 
            currentRevenue
          ]
        };
      case '1y':
        return {
          labels: ['Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'],
          data: [
            currentRevenue * 0.4, currentRevenue * 0.45, currentRevenue * 0.5,
            currentRevenue * 0.55, currentRevenue * 0.6, currentRevenue * 0.65,
            currentRevenue * 0.6, currentRevenue * 0.7, currentRevenue * 0.75,
            currentRevenue * 0.8, currentRevenue * 0.9, currentRevenue
          ]
        };
      default:
        return { labels: [], data: [] };
    }
  };

  const revenueData = getRevenueData();

  const config: ChartConfiguration<'line'> = {
    type: 'line',
    data: {
      labels: revenueData.labels,
      datasets: [{
        label: 'Pendapatan (IDR)',
        data: revenueData.data,
        borderColor: 'rgb(76, 175, 80)',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointBackgroundColor: 'rgb(76, 175, 80)',
        pointBorderColor: 'white',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return new Intl.NumberFormat('id-ID', {
                style: 'currency',
                currency: 'IDR',
                minimumFractionDigits: 0
              }).format(value as number);
            }
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Pendapatan: ${new Intl.NumberFormat('id-ID', {
                style: 'currency',
                currency: 'IDR',
                minimumFractionDigits: 0
              }).format(context.parsed.y)}`;
            }
          }
        }
      }
    }
  };

  revenueChart = new Chart(ctx, config);
}

function initializeCharts() {
  nextTick(() => {
    createPieChart();
    createLineChart();
    createBarChart();
    createRevenueChart();
  });
}

// Watch for timeframe changes
watch(revenueTimeframe, () => {
  createRevenueChart();
});

onMounted(async () => {
  await fetchStats();
  initializeCharts();
});
</script>

<style scoped>
.dashboard-header {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(156, 39, 176, 0.1) 100%);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.stats-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}

.revenue-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(33, 150, 243, 0.05) 100%);
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.revenue-amount {
  position: relative;
}

.revenue-amount::before {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, rgb(76, 175, 80) 0%, rgb(33, 150, 243) 100%);
  border-radius: 2px;
}

.chart-container {
  position: relative;
}

.quick-stats .stat-item {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.kpi-item {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.kpi-item:hover {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
}

.timeline-custom {
  max-height: 300px;
  overflow-y: auto;
}

.timeline-custom::-webkit-scrollbar {
  width: 4px;
}

.timeline-custom::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 2px;
}

.timeline-custom::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.4);
  border-radius: 2px;
}

.activity-content {
  padding-left: 8px;
}

/* Dark theme adjustments */
.v-theme--dark .dashboard-header {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(156, 39, 176, 0.15) 100%);
}

.v-theme--dark .revenue-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(33, 150, 243, 0.1) 100%);
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.v-theme--dark .stats-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .dashboard-header {
    padding: 16px;
    margin-bottom: 16px;
  }
  
  .dashboard-header h1 {
    font-size: 1.5rem !important;
  }
  
  .stats-card .v-card-text {
    padding: 16px !important;
  }
  
  .stats-card .text-h4 {
    font-size: 1.8rem !important;
  }
  
  .revenue-card .v-card-text {
    padding: 20px !important;
  }
  
  .chart-container {
    height: 220px !important;
  }
  
  .kpi-item .v-progress-circular {
    width: 60px !important;
    height: 60px !important;
  }
}

@media (max-width: 480px) {
  .pa-6 {
    padding: 12px !important;
  }
  
  .stats-card .text-h4 {
    font-size: 1.5rem !important;
  }
  
  .revenue-amount .text-h3 {
    font-size: 1.8rem !important;
  }
  
  .chart-container {
    height: 200px !important;
  }
  
  .timeline-custom {
    max-height: 250px;
  }
}

/* Animation classes */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-card {
  animation: fadeInUp 0.6s ease-out;
}

.stats-card:nth-child(1) { animation-delay: 0.1s; }
.stats-card:nth-child(2) { animation-delay: 0.2s; }
.stats-card:nth-child(3) { animation-delay: 0.3s; }
.stats-card:nth-child(4) { animation-delay: 0.4s; }

/* Custom scrollbar for timeline */
.timeline-custom {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.4) transparent;
}
</style>