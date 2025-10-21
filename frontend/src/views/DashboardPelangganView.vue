<template>
  <v-container fluid class="pa-6">
    <!-- Header Section -->
    <div class="dashboard-header mb-6">
      <h1 class="text-h4 font-weight-bold text-primary mb-2">Dashboard Monitoring Pelanggan Jakinet</h1>
      <p class="text-subtitle-1 text-medium-emphasis">Pantau performa dan aktivitas pelanggan JakiNet secara real-time</p>
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
          <v-card rounded="xl" elevation="2" height="400" class="chart-card">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="primary" class="me-2">mdi-chart-pie</v-icon>
                <span class="font-weight-bold">Distribusi Pelanggan JakiNet</span>
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
          <v-card rounded="xl" elevation="2" height="400" class="chart-card">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center">
                <v-icon color="info" class="me-2">mdi-chart-line</v-icon>
                <span class="font-weight-bold">Tren Pertumbuhan Kumulatif</span>
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
          <v-card rounded="xl" elevation="2" height="350" class="chart-card">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center justify-space-between w-100">
                <div class="d-flex align-center">
                  <v-icon color="purple" class="me-2">mdi-chart-bar</v-icon>
                  <span class="font-weight-bold">Pelanggan Baru vs Berhenti (Bulan Ini)</span>
                </div>
                <v-chip color="purple" variant="tonal" size="small">
                  Bulan Ini
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
                    <span class="text-body-2 text-medium-emphasis">Growth Rate (Bulan ini)</span>
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
                    <div class="text-caption text-medium-emphasis">ARPU (JakiNet Bulan Ini)</div>
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
        <v-col cols="12">
          <v-card rounded="xl" elevation="2" height="400" class="chart-card">
            <v-card-title class="pa-6 pb-2">
              <div class="d-flex align-center justify-space-between w-100">
                <div class="d-flex align-center">
                  <v-icon color="success" class="me-2">mdi-chart-areaspline</v-icon>
                  <span class="font-weight-bold">Tren Pendapatan Bulanan JakiNet</span>
                </div>
                <v-btn-toggle v-model="revenueTimeframe" color="primary" size="small" density="compact">
                  <v-btn value="3m" size="small">3M</v-btn>
                  <v-btn value="6m" size="small">6M</v-btn>
                  <v-btn value="1y" size="small">1Y</v-btn>
                </v-btn-toggle>
              </div>
            </v-card-title>
            <v-card-text class="pa-6 pt-2">
              <!-- Conditional rendering for the chart -->
              <div v-if="hasRevenueData" class="chart-container" style="height: 300px; position: relative;">
                <canvas ref="revenueChartCanvas" style="max-height: 300px;"></canvas>
              </div>
              <!-- Message for when there is no data -->
              <div v-else class="d-flex align-center justify-center flex-column text-center fill-height">
                <v-icon size="64" color="grey-lighten-1">mdi-chart-bar-off</v-icon>
                <h4 class="text-h6 mt-4 text-medium-emphasis">Tidak Ada Data Pendapatan</h4>
                <p class="text-body-1 text-medium-emphasis">Tidak ada pendapatan yang tercatat untuk periode waktu yang dipilih.</p>
              </div>
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

// --- State untuk menyimpan data dari API ---
const stats = ref({
  pelanggan_aktif: 0,
  pelanggan_baru_bulan_ini: 0,
  pelanggan_berhenti_bulan_ini: 0,
  pelanggan_jakinet_aktif: 0,
  pendapatan_jakinet_bulan_ini: 0,
});
const growthChartData = ref({ labels: [] as string[], data: [] as number[] });
const revenueChartData = ref({ labels: [] as string[], data: [] as number[] });


// Chart refs
const pieChartCanvas = ref<HTMLCanvasElement>();
const lineChartCanvas = ref<HTMLCanvasElement>();
const barChartCanvas = ref<HTMLCanvasElement>();
const revenueChartCanvas = ref<HTMLCanvasElement>();

let pieChart: Chart | null = null;
let lineChart: Chart | null = null;
let barChart: Chart | null = null;
let revenueChart: Chart | null = null;

// Computed properties
const growthRate = computed(() => {
  const base = stats.value.pelanggan_aktif - stats.value.pelanggan_baru_bulan_ini;
  if (base <= 0) return stats.value.pelanggan_baru_bulan_ini > 0 ? 100 : 0;
  return ((stats.value.pelanggan_baru_bulan_ini - stats.value.pelanggan_berhenti_bulan_ini) / base) * 100;
});

const jakiNetPenetration = computed(() => {
  // Karena dashboard ini khusus Jakinet, penetrasinya selalu 100% dari data yang ditampilkan
  // Ini mungkin perlu dihitung terhadap total pelanggan semua brand jika data itu tersedia
  return stats.value.pelanggan_aktif > 0 ? (stats.value.pelanggan_jakinet_aktif / stats.value.pelanggan_aktif) * 100 : 100;
});

const customerRetention = computed(() => {
  const startOfMonth = stats.value.pelanggan_aktif - stats.value.pelanggan_baru_bulan_ini + stats.value.pelanggan_berhenti_bulan_ini;
  if (startOfMonth <= 0) return 0;
  const retained = startOfMonth - stats.value.pelanggan_berhenti_bulan_ini;
  return (retained / startOfMonth) * 100;
});

const averageRevenuePerUser = computed(() => {
  return stats.value.pelanggan_jakinet_aktif > 0 ? stats.value.pendapatan_jakinet_bulan_ini / stats.value.pelanggan_jakinet_aktif : 0;
});

const hasRevenueData = computed(() => {
  if (!revenueChartData.value || !revenueChartData.value.data) {
    return false;
  }
  return revenueChartData.value.data.some(value => value > 0);
});

// --- Fungsi utama untuk mengambil semua data dashboard ---
async function fetchDashboardData(timespan: string = '6m') {
  loading.value = true;
  try {
    const response = await apiClient.get('/dashboard-pelanggan/', {
      params: { timespan }
    });
    const data = response.data;
    stats.value = data.main_stats;
    growthChartData.value = data.growth_chart;
    revenueChartData.value = data.revenue_chart;
    
    // Re-initialize charts with new data
    initializeCharts();

  } catch (error) {
    console.error("Gagal mengambil data dashboard pelanggan:", error);
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

  if (pieChart) pieChart.destroy();

  const activeExisting = stats.value.pelanggan_jakinet_aktif - stats.value.pelanggan_baru_bulan_ini;

  const config: ChartConfiguration<'doughnut'> = {
    type: 'doughnut',
    data: {
      labels: ['Pelanggan Aktif (Lama)', 'Pelanggan Baru (Bulan Ini)', 'Pelanggan Berhenti (Bulan Ini)'],
      datasets: [{
        data: [
          activeExisting > 0 ? activeExisting : 0,
          stats.value.pelanggan_baru_bulan_ini,
          stats.value.pelanggan_berhenti_bulan_ini
        ],
        backgroundColor: [
          'rgba(33, 150, 243, 0.8)',
          'rgba(76, 175, 80, 0.8)',
          'rgba(244, 67, 54, 0.8)'
        ],
        borderColor: [
          'rgb(33, 150, 243)',
          'rgb(76, 175, 80)',
          'rgb(244, 67, 54)'
        ],
        hoverBackgroundColor: [
          'rgba(33, 150, 243, 1)',
          'rgba(76, 175, 80, 1)',
          'rgba(244, 67, 54, 1)'
        ],
        borderWidth: 2
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
            font: { size: 12, weight: 500 } 
          }
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: 'rgb(33, 33, 33)',
          bodyColor: 'rgb(33, 33, 33)',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          callbacks: {
            label: (context) => {
              const label = context.label || '';
              const value = context.parsed;
              return `${label}: ${value} (${((value / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1)}%)`;
            }
          }
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 1000,
        easing: 'easeOutQuart'
      }
    }
  };
  pieChart = new Chart(ctx, config);
}

function createLineChart() {
  if (!lineChartCanvas.value) return;
  const ctx = lineChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (lineChart) lineChart.destroy();

  const config: ChartConfiguration<'line'> = {
    type: 'line',
    data: {
      labels: growthChartData.value.labels,
      datasets: [
        {
          label: 'Total Pelanggan JakiNet',
          data: growthChartData.value.data,
          borderColor: 'rgba(76, 175, 80, 1)',
          backgroundColor: 'rgba(76, 175, 80, 0.2)',
          pointBackgroundColor: 'rgba(76, 175, 80, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(76, 175, 80, 1)',
          pointRadius: 4,
          pointHoverRadius: 6,
          borderWidth: 3,
          tension: 0.4,
          fill: true,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { 
        y: { 
          beginAtZero: false,
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
            padding: 20,
            font: { size: 12, weight: 500 }
          } 
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: 'rgb(33, 33, 33)',
          bodyColor: 'rgb(33, 33, 33)',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: (context) => {
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      },
      elements: {
        line: {
          borderWidth: 3
        },
        point: {
          borderWidth: 2
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

  if (barChart) barChart.destroy();

  const config: ChartConfiguration<'bar'> = {
    type: 'bar',
    data: {
      labels: ['Pelanggan Bulan Ini'],
      datasets: [
        {
          label: 'Baru',
          data: [stats.value.pelanggan_baru_bulan_ini],
          backgroundColor: 'rgba(76, 175, 80, 0.7)',
          borderColor: 'rgb(76, 175, 80)',
          hoverBackgroundColor: 'rgba(76, 175, 80, 0.9)',
          hoverBorderColor: 'rgb(76, 175, 80)',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
        {
          label: 'Berhenti',
          data: [stats.value.pelanggan_berhenti_bulan_ini],
          backgroundColor: 'rgba(244, 67, 54, 0.7)',
          borderColor: 'rgb(244, 67, 54)',
          hoverBackgroundColor: 'rgba(244, 67, 54, 0.9)',
          hoverBorderColor: 'rgb(244, 67, 54)',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
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
          display: true, 
          position: 'top',
          labels: { 
            usePointStyle: true, 
            padding: 20,
            font: { size: 12, weight: 500 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: 'rgb(33, 33, 33)',
          bodyColor: 'rgb(33, 33, 33)',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          displayColors: true
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      }
    }
  };
  barChart = new Chart(ctx, config);
}

function createRevenueChart() {
  if (!revenueChartCanvas.value) return;
  const ctx = revenueChartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (revenueChart) revenueChart.destroy();

  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(76, 175, 80, 0.4)');
  gradient.addColorStop(1, 'rgba(76, 175, 80, 0.05)');

  const config: ChartConfiguration<'line'> = {
    type: 'line',
    data: {
      labels: revenueChartData.value.labels,
      datasets: [{
        label: 'Pendapatan (IDR)',
        data: revenueChartData.value.data,
        borderColor: 'rgb(76, 175, 80)',
        backgroundColor: gradient,
        pointBackgroundColor: 'rgb(76, 175, 80)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(76, 175, 80)',
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 3,
        tension: 0.4,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value as number)
          },
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
          display: false,
          labels: { 
            usePointStyle: true, 
            padding: 20,
            font: { size: 12, weight: 500 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: 'rgb(33, 33, 33)',
          bodyColor: 'rgb(33, 33, 33)',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: (context) => `Pendapatan: ${formatCurrency(context.parsed.y)}`
          }
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      },
      elements: {
        line: {
          borderWidth: 3
        },
        point: {
          borderWidth: 2
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
    // Hanya render chart pendapatan jika ada data
    if (hasRevenueData.value) {
      createRevenueChart();
    }
  });
}

watch(revenueTimeframe, (newTimeframe) => {
  fetchDashboardData(newTimeframe);
});

onMounted(() => {
  fetchDashboardData(revenueTimeframe.value);
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

.chart-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(245, 245, 245, 0.1) 100%);
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  overflow: hidden;
  position: relative;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, rgba(33, 150, 243, 0.8), rgba(76, 175, 80, 0.8), rgba(244, 67, 54, 0.8));
  z-index: 1;
}

.chart-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
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

.v-theme--dark .chart-card {
  background: linear-gradient(135deg, rgba(30, 30, 40, 0.3) 0%, rgba(50, 50, 60, 0.3) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.v-theme--dark .chart-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
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
  
  .chart-card::before {
    display: none;
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