<!-- ====================================================================
TRAFFIC MONITORING DASHBOARD VIEW - MODERN & ELEGANT
====================================================================
Real-time Mikrotik PPPoE Traffic Monitoring
Features: Modern UI, Dark/Light Mode, Responsive, Lightweight
==================================================================== -->
<template>
  <div class="traffic-monitoring" :class="{ 'dark-mode': isDarkMode }">
    <!-- Theme Toggle -->
    <button class="theme-toggle" @click="toggleTheme" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
      <i :class="isDarkMode ? 'fas fa-sun' : 'fas fa-moon'"></i>
    </button>

    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="icon-wrapper">
            <i class="fas fa-chart-line"></i>
          </div>
          <div>
            <h1 class="page-title">Traffic Monitoring</h1>
            <p class="page-subtitle">Real-time PPPoE bandwidth monitoring from Mikrotik</p>
          </div>
        </div>
        
        <div class="action-buttons">
          <button
            class="btn btn-refresh"
            @click="refreshData"
            :disabled="loading"
            :class="{ 'loading': loading }"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span>Refresh</span>
          </button>

          <button
            class="btn btn-collect"
            @click="triggerCollection"
            :disabled="collecting"
            :class="{ 'collecting': collecting }"
          >
            <i class="fas fa-play" :class="{ 'fa-spin': collecting }"></i>
            <span>{{ collecting ? 'Collecting...' : 'Collect Data' }}</span>
          </button>

          <div class="auto-refresh-toggle">
            <input
              type="checkbox"
              id="autoRefresh"
              v-model="autoRefresh"
              @change="toggleAutoRefresh"
            >
            <label for="autoRefresh">
              <span class="toggle-slider"></span>
              <span class="toggle-label">Auto Refresh</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Collection Status Banner -->
    <transition name="slide-down">
      <div v-if="collectionStatus" class="status-banner">
        <div class="status-content">
          <i class="fas fa-info-circle"></i>
          <div class="status-text">
            <strong>Last Collection:</strong>
            <span>{{ formatTimestamp(collectionStatus?.last_collection || 'Never') }}</span>
          </div>
          <span v-if="!collectionStatus.collection_active" class="status-warning">
            <i class="fas fa-exclamation-triangle"></i>
            Collection Inactive
          </span>
        </div>
        <button class="status-close" @click="collectionStatus = null as any">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </transition>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card card-primary">
        <div class="stat-icon">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-content">
          <div class="stat-label">Active Users</div>
          <div class="stat-value">{{ dashboardData.total_active_users || 0 }}</div>
        </div>
        <div class="stat-trend">
          <i class="fas fa-arrow-up"></i>
        </div>
      </div>

      <div class="stat-card card-success">
        <div class="stat-icon">
          <i class="fas fa-tachometer-alt"></i>
        </div>
        <div class="stat-content">
          <div class="stat-label">Total Bandwidth</div>
          <div class="stat-value">{{ formatMbps(dashboardData.total_bandwidth_usage || 0) }}</div>
        </div>
        <div class="stat-trend">
          <i class="fas fa-arrow-up"></i>
        </div>
      </div>

      <div class="stat-card card-info">
        <div class="stat-icon">
          <i class="fas fa-server"></i>
        </div>
        <div class="stat-content">
          <div class="stat-label">Active Servers</div>
          <div class="stat-value">{{ dashboardData.server_summary?.length || 0 }}</div>
        </div>
        <div class="stat-trend">
          <i class="fas fa-check"></i>
        </div>
      </div>

      <div class="stat-card card-warning">
        <div class="stat-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-label">Last Updated</div>
          <div class="stat-value stat-time">{{ formatTime(dashboardData.last_updated) }}</div>
        </div>
        <div class="stat-trend">
          <i class="fas fa-sync-alt"></i>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Top Consumers Section -->
      <div class="main-panel">
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-trophy"></i>
              <h3>Top Bandwidth Consumers</h3>
            </div>
            
            <div class="panel-filters">
              <div class="filter-group">
                <i class="fas fa-server"></i>
                <select
                  v-model="selectedServer"
                  @change="loadLatestData"
                  class="filter-select"
                >
                  <option value="">All Servers</option>
                  <option v-for="server in servers" :key="server.id" :value="server.id">
                    {{ server.name }}
                  </option>
                </select>
              </div>

              <div class="filter-group">
                <i class="fas fa-network-wired"></i>
                <select
                  v-model="selectedOLT"
                  @change="loadLatestData"
                  class="filter-select"
                >
                  <option value="">All OLTs</option>
                  <option v-for="olt in availableOLTs" :key="olt" :value="olt">
                    {{ olt }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div class="panel-body">
            <!-- Loading State -->
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner">
                <div class="spinner"></div>
              </div>
              <p>Loading traffic data...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!trafficData.length" class="empty-state">
              <div class="empty-icon">
                <i class="fas fa-chart-line"></i>
              </div>
              <h4>No Traffic Data Available</h4>
              <p>Start traffic collection to see real-time data</p>
              <button class="btn btn-collect" @click="triggerCollection">
                <i class="fas fa-play"></i>
                Start Collection
              </button>
            </div>

            <!-- Traffic Data Table -->
            <div v-else class="traffic-table-wrapper">
              <table class="traffic-table">
                <thead>
                  <tr>
                    <th class="col-rank">#</th>
                    <th class="col-customer">Customer</th>
                    <th class="col-username">Username</th>
                    <th class="col-ip">IP Address</th>
                    <th class="col-download">
                      <i class="fas fa-download"></i> Download
                    </th>
                    <th class="col-upload">
                      <i class="fas fa-upload"></i> Upload
                    </th>
                    <th class="col-total">Total</th>
                    <th class="col-uptime">Uptime</th>
                    <th class="col-server">Server</th>
                    <th class="col-status">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(user, index) in trafficData" :key="user.id" class="table-row">
                    <td class="col-rank">
                      <div class="rank-badge" :class="getRankClass(index)">
                        {{ index + 1 }}
                      </div>
                    </td>
                    <td class="col-customer">
                      <div class="customer-info">
                        <div class="customer-name">{{ user.pelanggan_name || 'N/A' }}</div>
                        <div class="customer-olt">
                          <i class="fas fa-network-wired"></i>
                          {{ user.olt || 'N/A' }}
                        </div>
                      </div>
                    </td>
                    <td class="col-username">
                      <code class="username-code">{{ user.username_pppoe }}</code>
                    </td>
                    <td class="col-ip">
                      <code class="ip-code">{{ user.ip_address }}</code>
                    </td>
                    <td class="col-download">
                      <div class="bandwidth-value download">
                        <i class="fas fa-arrow-down"></i>
                        {{ formatMbps(user.rx_mbps) }}
                      </div>
                    </td>
                    <td class="col-upload">
                      <div class="bandwidth-value upload">
                        <i class="fas fa-arrow-up"></i>
                        {{ formatMbps(user.tx_mbps) }}
                      </div>
                    </td>
                    <td class="col-total">
                      <div class="bandwidth-total" :class="getBandwidthClass(user.total_mbps)">
                        {{ formatMbps(user.total_mbps) }}
                      </div>
                    </td>
                    <td class="col-uptime">
                      <div class="uptime-value">
                        <i class="fas fa-clock"></i>
                        {{ user.uptime_formatted }}
                      </div>
                    </td>
                    <td class="col-server">
                      <div class="server-badge">
                        {{ user.server_name || 'N/A' }}
                      </div>
                    </td>
                    <td class="col-status">
                      <div class="status-badge" :class="user.is_active ? 'active' : 'inactive'">
                        <span class="status-dot"></span>
                        {{ user.is_active ? 'Active' : 'Inactive' }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar Panels -->
      <div class="sidebar-panel">
        <!-- Server Summary -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-server"></i>
              <h3>Server Summary</h3>
            </div>
          </div>
          
          <div class="panel-body">
            <div v-if="!dashboardData.server_summary?.length" class="empty-state-small">
              <i class="fas fa-server"></i>
              <p>No server data</p>
            </div>

            <div v-else class="server-list">
              <div
                v-for="server in dashboardData.server_summary"
                :key="server.server_id"
                class="server-item"
              >
                <div class="server-header">
                  <div class="server-name">
                    <i class="fas fa-server"></i>
                    {{ server.server_name }}
                  </div>
                  <div class="server-load" :class="getLoadClass(server.load_percentage)">
                    {{ server.load_percentage.toFixed(1) }}%
                  </div>
                </div>

                <div class="server-progress">
                  <div
                    class="progress-bar"
                    :class="getLoadClass(server.load_percentage)"
                    :style="{ width: `${Math.min(server.load_percentage, 100)}%` }"
                  ></div>
                </div>

                <div class="server-stats">
                  <div class="stat-item">
                    <i class="fas fa-users"></i>
                    <span>{{ server.active_users }} users</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-tachometer-alt"></i>
                    <span>{{ formatMbps(server.total_mbps) }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-chart-line"></i>
                    <span>Avg: {{ formatMbps(server.avg_mbps) }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-arrow-up"></i>
                    <span>Max: {{ formatMbps(server.max_mbps) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Statistics Card -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-chart-pie"></i>
              <h3>Statistics (24h)</h3>
            </div>
          </div>
          
          <div class="panel-body">
            <div v-if="loadingStats" class="loading-state-small">
              <div class="spinner-small"></div>
              <span>Loading...</span>
            </div>

            <div v-else-if="statsData" class="stats-list">
              <div class="stats-item">
                <div class="stats-label">
                  <i class="fas fa-users"></i>
                  Unique Users
                </div>
                <div class="stats-value">{{ statsData.unique_users }}</div>
              </div>

              <div class="stats-item">
                <div class="stats-label">
                  <i class="fas fa-chart-line"></i>
                  Avg Bandwidth
                </div>
                <div class="stats-value">{{ formatMbps(statsData.avg_bandwidth_mbps) }}</div>
              </div>

              <div class="stats-item highlight">
                <div class="stats-label">
                  <i class="fas fa-fire"></i>
                  Peak Bandwidth
                </div>
                <div class="stats-value">{{ formatMbps(statsData.max_bandwidth_mbps) }}</div>
              </div>

              <div v-if="statsData.top_olts?.length" class="top-olts">
                <h4 class="section-title">
                  <i class="fas fa-network-wired"></i>
                  Top OLTs
                </h4>
                <div
                  v-for="(olt, index) in statsData.top_olts.slice(0, 5)"
                  :key="olt.olt"
                  class="olt-item"
                >
                  <div class="olt-rank">{{ index + 1 }}</div>
                  <div class="olt-info">
                    <div class="olt-name">{{ olt.olt }}</div>
                    <div class="olt-details">
                      <span>{{ olt.user_count }} users</span>
                      <span class="separator">•</span>
                      <span>{{ formatMbps(olt.total_bandwidth) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import {
  getLatestTrafficData,
  getDashboardSummary,
  getTrafficStatistics,
  triggerTrafficCollection,
  formatMbps,
  formatTimestamp,
  type TrafficData,
  type DashboardSummary,
  type TrafficStats
} from '@/services/trafficMonitoringAPI';

// Theme Management
const isDarkMode = ref(localStorage.getItem('theme') === 'dark');

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
};

// Reactive data
const loading = ref(false);
const collecting = ref(false);
const loadingStats = ref(false);
const autoRefresh = ref(false);
const refreshInterval = ref<NodeJS.Timeout | null>(null);

const trafficData = ref<TrafficData[]>([]);
const dashboardData = reactive<DashboardSummary>({
  total_active_users: 0,
  total_bandwidth_usage: 0,
  top_consumers: [],
  server_summary: [],
  last_updated: ''
});

const statsData = ref<TrafficStats | null>(null);
const collectionStatus = ref(dashboardData.collection_status || undefined);
const selectedServer = ref('');
const selectedOLT = ref('');
const servers = ref<any[]>([]);
const availableOLTs = ref<string[]>([]);

// ============================================
// HELPER METHODS
// ============================================

/**
 * Get rank class based on position
 */
const getRankClass = (index: number): string => {
  if (index === 0) return 'rank-gold';
  if (index === 1) return 'rank-silver';
  if (index === 2) return 'rank-bronze';
  return '';
};

/**
 * Get bandwidth class based on Mbps value
 */
const getBandwidthClass = (mbps: number): string => {
  if (mbps > 50) return 'high';
  if (mbps > 20) return 'medium';
  return 'low';
};

/**
 * Get load class based on percentage
 */
const getLoadClass = (percentage: number): string => {
  if (percentage >= 80) return 'high';
  if (percentage >= 50) return 'medium';
  return 'low';
};

/**
 * Format time from timestamp
 */
const formatTime = (timestamp: string): string => {
  if (!timestamp) return '--:--';
  return new Date(timestamp).toLocaleTimeString('id-ID', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

// ============================================
// DATA LOADING METHODS
// ============================================

/**
 * Refresh all data
 */
const refreshData = async (): Promise<void> => {
  await Promise.all([
    loadLatestData(),
    loadDashboardData(),
    loadStatistics()
  ]);
};

/**
 * Load latest traffic data
 */
const loadLatestData = async (): Promise<void> => {
  try {
    loading.value = true;
    const data = await getLatestTrafficData(
      50,
      selectedServer.value ? parseInt(selectedServer.value) : undefined,
      selectedOLT.value || undefined
    );
    trafficData.value = data;

    // Extract unique OLTs for filter
    const olts = [...new Set(data
      .map(item => item.olt)
      .filter((olt): olt is string => olt !== undefined && olt !== null)
    )];
    availableOLTs.value = olts;

  } catch (error) {
    console.error('Error loading latest traffic data:', error);
  } finally {
    loading.value = false;
  }
};

/**
 * Load dashboard summary data
 */
const loadDashboardData = async (): Promise<void> => {
  try {
    const data = await getDashboardSummary();
    Object.assign(dashboardData, data);
    collectionStatus.value = data.collection_status;
  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
};

/**
 * Load statistics data
 */
const loadStatistics = async (): Promise<void> => {
  try {
    loadingStats.value = true;
    const data = await getTrafficStatistics(24);
    statsData.value = data;
  } catch (error) {
    console.error('Error loading statistics:', error);
  } finally {
    loadingStats.value = false;
  }
};

/**
 * Trigger manual traffic collection
 */
const triggerCollection = async (): Promise<void> => {
  try {
    collecting.value = true;
    const result = await triggerTrafficCollection();
    console.log('Collection started:', result.message);

    // Auto refresh after collection completes
    setTimeout(() => {
      refreshData();
      collecting.value = false;
    }, 5000);

  } catch (error) {
    console.error('Error triggering collection:', error);
    collecting.value = false;
  }
};

/**
 * Toggle auto refresh
 */
const toggleAutoRefresh = (): void => {
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(refreshData, 30000); // 30 seconds
  } else {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value);
      refreshInterval.value = null;
    }
  }
};

// ============================================
// LIFECYCLE HOOKS
// ============================================

onMounted(async () => {
  // Load initial data
  await refreshData();
  
  // Apply saved theme
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark-mode');
  }
});

onUnmounted(() => {
  // Cleanup auto refresh interval
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
});
</script>

<style scoped>
/* ============================================
   CSS VARIABLES & THEME SYSTEM
============================================ */
.traffic-monitoring {
  --primary: #3b82f6;
  --primary-light: #60a5fa;
  --primary-dark: #2563eb;
  
  --success: #10b981;
  --success-light: #34d399;
  --success-dark: #059669;
  
  --info: #06b6d4;
  --info-light: #22d3ee;
  --info-dark: #0891b2;
  
  --warning: #f59e0b;
  --warning-light: #fbbf24;
  --warning-dark: #d97706;
  
  --danger: #ef4444;
  --danger-light: #f87171;
  --danger-dark: #dc2626;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-tertiary: #94a3b8;
  
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  
  padding: 1.5rem;
  min-height: 100vh;
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

/* Dark Mode Theme */
.traffic-monitoring.dark-mode {
  --primary: #60a5fa;
  --primary-light: #93c5fd;
  --primary-dark: #3b82f6;
  
  --success: #34d399;
  --success-light: #6ee7b7;
  --success-dark: #10b981;
  
  --info: #22d3ee;
  --info-light: #67e8f9;
  --info-dark: #06b6d4;
  
  --warning: #fbbf24;
  --warning-light: #fcd34d;
  --warning-dark: #f59e0b;
  
  --danger: #f87171;
  --danger-light: #fca5a5;
  --danger-dark: #ef4444;
  
  --bg-primary: #1e293b;
  --bg-secondary: #0f172a;
  --bg-tertiary: #334155;
  
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-tertiary: #64748b;
  
  --border-color: #334155;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
}

/* ============================================
   THEME TOGGLE BUTTON
============================================ */
.theme-toggle {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 1000;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  border: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  transform: scale(1.1) rotate(15deg);
  box-shadow: var(--shadow-xl);
}

.theme-toggle:active {
  transform: scale(0.95);
}

/* ============================================
   PAGE HEADER
============================================ */
.page-header {
  margin-bottom: 2rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.icon-wrapper {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  box-shadow: var(--shadow-md);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.page-subtitle {
  margin: 0.25rem 0 0 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* ============================================
   ACTION BUTTONS
============================================ */
.action-buttons {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  border: none;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-refresh {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-refresh:hover:not(:disabled) {
  background: var(--bg-tertiary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-collect {
  background: linear-gradient(135deg, var(--success), var(--success-dark));
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-collect:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-collect.collecting {
  background: linear-gradient(135deg, var(--warning), var(--warning-dark));
}

/* Auto Refresh Toggle */
.auto-refresh-toggle {
  display: flex;
  align-items: center;
}

.auto-refresh-toggle input[type="checkbox"] {
  display: none;
}

.auto-refresh-toggle label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;
}

.toggle-slider {
  position: relative;
  width: 3rem;
  height: 1.5rem;
  background: var(--border-color);
  border-radius: 1rem;
  transition: all 0.3s ease;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  top: 0.125rem;
  left: 0.125rem;
  width: 1.25rem;
  height: 1.25rem;
  background: white;
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}

input:checked + label .toggle-slider {
  background: var(--success);
}

input:checked + label .toggle-slider::before {
  transform: translateX(1.5rem);
}

.toggle-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

/* ============================================
   STATUS BANNER
============================================ */
.status-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
}

.status-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.status-content > i {
  font-size: 1.25rem;
  color: var(--info);
}

.status-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.status-text strong {
  color: var(--text-primary);
}

.status-text span {
  color: var(--text-secondary);
}

.status-warning {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.75rem;
  background: rgba(245, 158, 11, 0.1);
  border-radius: var(--radius-sm);
  color: var(--warning);
  font-size: 0.75rem;
  font-weight: 500;
}

.status-close {
  width: 2rem;
  height: 2rem;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.status-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-primary);
}

/* Slide Down Animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-1rem);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-1rem);
}

/* ============================================
   STATS GRID
============================================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card.card-primary::before {
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
}

.stat-card.card-success::before {
  background: linear-gradient(90deg, var(--success), var(--success-light));
}

.stat-card.card-info::before {
  background: linear-gradient(90deg, var(--info), var(--info-light));
}

.stat-card.card-warning::before {
  background: linear-gradient(90deg, var(--warning), var(--warning-light));
}

.stat-icon {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.card-primary .stat-icon {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.2));
  color: var(--primary);
}

.card-success .stat-icon {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.2));
  color: var(--success);
}

.card-info .stat-icon {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(6, 182, 212, 0.2));
  color: var(--info);
}

.card-warning .stat-icon {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.2));
  color: var(--warning);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-value.stat-time {
  font-size: 1.25rem;
}

.stat-trend {
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
}

/* ============================================
   CONTENT GRID
============================================ */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 1.5rem;
}

/* ============================================
   PANEL CARD
============================================ */
.panel-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: all 0.3s ease;
}

.panel-card:hover {
  box-shadow: var(--shadow-lg);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
}

.panel-title i {
  font-size: 1.25rem;
  color: var(--primary);
}

.panel-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.panel-body {
  padding: 1.5rem;
}

/* ============================================
   PANEL FILTERS
============================================ */
.panel-filters {
  display: flex;
  gap: 0.75rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.filter-group i {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.filter-select {
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  min-width: 150px;
}

.filter-select option {
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* ============================================
   LOADING & EMPTY STATES
============================================ */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.loading-spinner {
  margin-bottom: 1.5rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.empty-state p {
  color: var(--text-secondary);
  margin: 0.5rem 0 0 0;
}

.empty-icon {
  width: 5rem;
  height: 5rem;
  border-radius: 50%;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.empty-icon i {
  font-size: 2.5rem;
  color: var(--text-tertiary);
}

.empty-state h4 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

/* ============================================
   TRAFFIC TABLE
============================================ */
.traffic-table-wrapper {
  overflow-x: auto;
  margin: -0.5rem;
  padding: 0.5rem;
}

.traffic-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.traffic-table thead {
  position: sticky;
  top: 0;
  z-index: 10;
}

.traffic-table thead tr {
  background: var(--bg-secondary);
}

.traffic-table th {
  padding: 1rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

.traffic-table th i {
  margin-right: 0.25rem;
}

.traffic-table tbody tr {
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.traffic-table tbody tr:hover {
  background: var(--bg-secondary);
  transform: scale(1.01);
  box-shadow: var(--shadow-sm);
}

.traffic-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.875rem;
}

/* Rank Badge */
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-weight: 700;
  font-size: 0.875rem;
}

.rank-badge.rank-gold {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #7c5e10;
  box-shadow: 0 4px 8px rgba(255, 215, 0, 0.3);
}

.rank-badge.rank-silver {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #4a4a4a;
  box-shadow: 0 4px 8px rgba(192, 192, 192, 0.3);
}

.rank-badge.rank-bronze {
  background: linear-gradient(135deg, #cd7f32, #e8a87c);
  color: #5c3a1a;
  box-shadow: 0 4px 8px rgba(205, 127, 50, 0.3);
}

/* Customer Info */
.customer-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.customer-name {
  font-weight: 600;
  color: var(--text-primary);
}

.customer-olt {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.customer-olt i {
  font-size: 0.625rem;
}

/* Code Elements */
.username-code,
.ip-code {
  padding: 0.25rem 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: var(--text-primary);
}

/* Bandwidth Values */
.bandwidth-value {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 600;
}

.bandwidth-value.download {
  color: var(--success);
}

.bandwidth-value.upload {
  color: var(--info);
}

.bandwidth-value i {
  font-size: 0.75rem;
}

.bandwidth-total {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-sm);
  font-weight: 700;
  font-size: 0.875rem;
}

.bandwidth-total.low {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.bandwidth-total.medium {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.bandwidth-total.high {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

/* Uptime Value */
.uptime-value {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.uptime-value i {
  font-size: 0.625rem;
}

/* Server Badge */
.server-badge {
  display: inline-flex;
  padding: 0.25rem 0.625rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.status-badge.inactive {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ============================================
   SERVER LIST
============================================ */
.server-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.server-item {
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: all 0.2s ease;
}

.server-item:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-sm);
}

.server-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.server-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.server-name i {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.server-load {
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 700;
}

.server-load.low {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.server-load.medium {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.server-load.high {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.server-progress {
  height: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.3s ease;
}

.progress-bar.low {
  background: linear-gradient(90deg, var(--success), var(--success-light));
}

.progress-bar.medium {
  background: linear-gradient(90deg, var(--warning), var(--warning-light));
}

.progress-bar.high {
  background: linear-gradient(90deg, var(--danger), var(--danger-light));
}

.server-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.server-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.server-stats .stat-item i {
  font-size: 0.625rem;
  color: var(--text-tertiary);
}

/* ============================================
   STATISTICS LIST
============================================ */
.stats-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stats-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.stats-item:hover {
  border-color: var(--primary);
}

.stats-item.highlight {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(239, 68, 68, 0.1));
  border-color: var(--danger);
}

.stats-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.stats-label i {
  font-size: 0.75rem;
}

.stats-value {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
}

/* Top OLTs */
.top-olts {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.section-title i {
  font-size: 0.75rem;
  color: var(--primary);
}

.olt-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;
}

.olt-item:hover {
  background: var(--bg-tertiary);
  transform: translateX(4px);
}

.olt-rank {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: var(--radius-sm);
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.olt-info {
  flex: 1;
}

.olt-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.olt-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.separator {
  color: var(--text-tertiary);
}

/* ============================================
   LOADING STATE SMALL
============================================ */
.loading-state-small {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.spinner-small {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Empty State Small */
.empty-state-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  text-align: center;
}

.empty-state-small i {
  font-size: 2rem;
  color: var(--text-tertiary);
}

.empty-state-small p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* ============================================
   RESPONSIVE DESIGN
============================================ */
@media (max-width: 1280px) {
  .content-grid {
    grid-template-columns: 1fr 350px;
  }
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .sidebar-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .traffic-monitoring {
    padding: 1rem;
  }
  
  .theme-toggle {
    top: 1rem;
    right: 1rem;
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .action-buttons {
    width: 100%;
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .stat-card {
    padding: 1.25rem;
  }
  
  .stat-icon {
    width: 3rem;
    height: 3rem;
    font-size: 1.25rem;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
  
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .panel-filters {
    width: 100%;
    flex-direction: column;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .traffic-table-wrapper {
    overflow-x: scroll;
  }
  
  .traffic-table {
    min-width: 1200px;
  }
  
  .sidebar-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.5rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 1rem;
  }
}

/* ============================================
   PRINT STYLES
============================================ */
@media print {
  .theme-toggle,
  .action-buttons,
  .panel-filters {
    display: none !important;
  }
  
  .traffic-monitoring {
    background: white;
    color: black;
  }
  
  .panel-card {
    break-inside: avoid;
    box-shadow: none;
    border: 1px solid #ddd;
  }
}

/* ============================================
   ACCESSIBILITY
============================================ */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Focus Styles */
button:focus-visible,
select:focus-visible,
input:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  .traffic-monitoring {
    --border-color: currentColor;
  }
  
  .panel-card {
    border: 2px solid currentColor;
  }
}
</style>