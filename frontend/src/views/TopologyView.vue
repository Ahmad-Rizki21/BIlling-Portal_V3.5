<template>
  <v-container fluid class="pa-6">
    <div class="d-flex align-center mb-6">
      <v-avatar class="me-3" color="primary" size="40">
        <v-icon color="white">mdi-sitemap</v-icon>
      </v-avatar>
      <div>
        <h1 class="text-h4 font-weight-bold">Topologi Jaringan OLT</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-0">Visualisasi hierarki infrastruktur</p>
      </div>
      <v-spacer></v-spacer>
      <v-btn color="primary" variant="outlined" @click="refreshTopology" :loading="loading">
        <v-icon start>mdi-refresh</v-icon>
        Refresh
      </v-btn>
    </div>

    <v-row>
      <v-col cols="12" :md="selectedNode ? 8 : 12" class="transition-swing">
        <v-card rounded="xl" elevation="4">
          <v-card-text class="pa-2 pa-sm-4">
            <div v-if="loading" class="text-center py-16">
              <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
              <p class="mt-4 text-medium-emphasis">Memuat data topologi...</p>
            </div>
            <div v-else>
              <div class="mb-4 d-flex flex-wrap gap-4 pa-2">
                <div v-for="(color, type) in deviceColors" :key="type" class="d-flex align-center">
                  <div class="legend-symbol me-2" :style="{ backgroundColor: color }"></div>
                  <span class="text-body-2">{{ type }}</span>
                </div>
              </div>
              
              <v-chart
                class="chart"
                :option="chartOption"
                autoresize
                @click="onNodeClick"
              />
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" v-if="selectedNode">
        <v-card rounded="xl" elevation="4">
          <v-card-title class="d-flex align-center">
            <v-icon :color="deviceColors[selectedNode.type]" class="me-3">{{ getDeviceIcon(selectedNode.type) }}</v-icon>
            Detail Perangkat
            <v-spacer></v-spacer>
            <v-btn icon size="small" variant="text" @click="selectedNode = null">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          
          <v-divider></v-divider>

          <v-card-text>
            <v-list density="compact">
              <v-list-item title="Nama" :subtitle="selectedNode.name"></v-list-item>
              <v-list-item v-if="selectedNode.ip" title="IP Address" :subtitle="selectedNode.ip"></v-list-item>
              <v-list-item v-if="selectedNode.mac" title="MAC Address" :subtitle="selectedNode.mac"></v-list-item>
              <v-list-item title="Tipe" :subtitle="selectedNode.type"></v-list-item>

              <v-list-item title="Status">
                <template v-slot:subtitle>
                  <v-chip :color="selectedNode.status === 'Up' ? 'success' : 'error'" size="small" variant="flat">
                    {{ selectedNode.status }}
                  </v-chip>
                </template>
              </v-list-item>

              <v-list-item v-if="selectedNode.inbound" title="Inbound" :subtitle="selectedNode.inbound" class="text-success"></v-list-item>
              <v-list-item v-if="selectedNode.outbound" title="Outbound" :subtitle="selectedNode.outbound" class="text-warning"></v-list-item>
              <v-list-item v-if="selectedNode.kapasitas" title="Kapasitas" :subtitle="selectedNode.kapasitas"></v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { TreeChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import apiClient from '@/services/api';
import { useRoute } from 'vue-router';

// Inisialisasi ECharts
use([CanvasRenderer, TreeChart, TitleComponent, TooltipComponent, LegendComponent]);

// Definisi Tipe Data
interface NodeData {
  name: string;
  type: string;
  status?: string;
  ip?: string;
  mac?: string;
  kapasitas?: string;
  inbound?: string;
  outbound?: string;
  children?: NodeData[];
  [key: string]: any;
}

const route = useRoute();
const loading = ref(true);
const chartOption = ref({});
const selectedNode = ref<NodeData | null>(null);

// Konfigurasi visual untuk setiap tipe perangkat
const deviceIcons: Record<string, string> = {
  'Server Router Core': 'mdi-server-network',
  'OLT': 'mdi-router-network',
  'ODP': 'mdi-briefcase-outline',
  'OKN': 'mdi-access-point-network',
  'Pelanggan': 'mdi-account-circle-outline'
};

const deviceColors: Record<string, string> = {
  'Server Router Core': '#1976D2',
  'OLT': '#4CAF50',
  'ODP': '#FF9800',
  'OKN': '#795548',
  'Pelanggan': '#607D8B'
};

// Fungsi untuk memproses data dari API/dummy menjadi format yang kaya untuk ECharts
function processTopologyData(node: NodeData): NodeData {
  node.itemStyle = {
    color: deviceColors[node.type] || '#ccc',
    borderColor: '#fff',
    borderWidth: 2,
  };
  // Tambahkan properti lain yang dibutuhkan ECharts jika ada
  if (node.children && node.children.length > 0) {
    node.children.forEach(processTopologyData);
  }
  return node;
}

// Data Dummy yang meniru struktur topologi di TikTok
function generateDemoData(): NodeData {
  return {
    name: "Server Router Core", type: "Server Router Core", status: "Up", ip: "192.168.1.1",
    children: [
      { name: "OLT-HSGQ-TAMBUN", type: "OLT", status: "Up", ip: "192.168.100.1",
        children: [
          { name: "ODP-TIANG-1", type: "ODP", status: "Up",
            children: [
              { name: "OKN-PERUMWASANA", type: "OKN", status: "Up" },
              { name: "OKN-LULUKISRAWIRAW", type: "OKN", status: "Up" },
            ]
          },
          { name: "ODP-TIANG-2", type: "ODP", status: "Down",
            children: [
              { name: "OKN-HANINDRAYUDIST", type: "OKN", status: "Down" },
            ]
          },
          { name: "ODP-TIANG-3", type: "ODP", status: "Up",
            children: [
              { name: "OKN-TATIRUSMIATY", type: "OKN", status: "Up", ip: "10.10.6.253", mac: "9C:E9:1C:5A:D7:D9", inbound: "50.50 Mbps", outbound: "4.98 Mbps" },
              { name: "OKN-PURBO", type: "OKN", status: "Up" }
            ]
          }
        ]
      }
    ]
  };
}

function onNodeClick(params: any) {
  if (params.data) {
    selectedNode.value = params.data as NodeData;
  }
}

onMounted(async () => {
  try {
    const oltId = route.params.olt_id;
    // Panggil API yang mengembalikan format { nodes, links, categories }
    const response = await apiClient.get(`/topology/olt/${oltId}`);
    const graphData = response.data;

    chartOption.value = {
      tooltip: {},
      legend: [{
        // Mengambil data kategori dari API untuk ditampilkan sebagai legenda
        data: graphData.categories.map((a: any) => a.name)
      }],
      series: [
        {
          type: 'graph', // Ganti tipe menjadi 'graph'
          layout: 'force', // Gunakan layout simulasi fisika
          data: graphData.nodes,
          links: graphData.links,
          categories: graphData.categories,
          roam: true, // Izinkan pengguna untuk menggeser dan zoom
          label: {
            show: true,
            position: 'right'
          },
          force: {
            repulsion: 100, // Atur seberapa jauh node saling mendorong
            edgeLength: 50 // Atur panjang garis koneksi
          }
        }
      ]
    };

  } catch (error) {
    console.error("Gagal memuat data topologi:", error);
  } finally {
    loading.value = false;
  }
});

async function loadTopologyData() {
  loading.value = true;
  selectedNode.value = null; // Tutup panel detail saat refresh
  try {
    let data: NodeData;
    
    // Coba ambil dari API, jika gagal, gunakan data dummy
    try {
      const oltId = route.params.olt_id;
      const response = await apiClient.get(`/topology/olt/${oltId}`);
      data = response.data;
    } catch (apiError) {
      console.warn("API Gagal, menggunakan data dummy untuk demo.", apiError);
      data = generateDemoData();
    }

    const processedData = processTopologyData(data);

    chartOption.value = {
      tooltip: { trigger: 'item', triggerOn: 'mousemove' },
      series: [
        {
          type: 'tree',
          data: [processedData],
          top: '5%', left: '5%', bottom: '5%', right: '15%',
          symbol: 'circle',
          symbolSize: 15,
          orient: 'LR', // Orientasi Kiri ke Kanan
          edgeShape: 'polyline', // Bentuk garis siku
          initialTreeDepth: 5, // Tampilkan semua level
          
          label: {
            position: 'right',
            verticalAlign: 'middle',
            align: 'left',
            fontSize: 12,
            distance: 10,
          },
          lineStyle: {
            width: 2,
            color: '#ccc'
          },
          emphasis: {
            focus: 'descendant'
          },
          expandAndCollapse: true,
          animationDuration: 550,
        }
      ]
    };

  } catch (error) {
    console.error("Gagal memproses data topologi:", error);
  } finally {
    loading.value = false;
  }
}

// Wrapper untuk memanggil loadTopologyData (berguna untuk tombol refresh)
function refreshTopology() {
  loadTopologyData();
}

function getDeviceIcon(type: string): string {
  return deviceIcons[type] || 'mdi-help-circle';
}

onMounted(loadTopologyData);
</script>

<style scoped>
.chart {
  height: 75vh;
}
.legend-symbol {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.v-card {
  transition: all 0.3s ease-in-out;
}
</style>