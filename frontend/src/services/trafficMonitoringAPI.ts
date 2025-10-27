// ====================================================================
// TRAFFIC MONITORING API SERVICE
// ====================================================================
// Service ini menangani semua komunikasi dengan backend traffic monitoring API.
// Menggunakan axios instance yang sudah dikonfigurasi dengan auth token.

import apiClient from './api';

// ====================================================================
// TRAFFIC MONITORING INTERFACES
// ====================================================================

export interface TrafficData {
  id: number;
  data_teknis_id: number;
  username_pppoe: string;
  ip_address: string;
  rx_mbps: number;
  tx_mbps: number;
  total_mbps: number;
  uptime_formatted: string;
  is_active: boolean;
  timestamp: string;
  pelanggan_name?: string;
  server_name?: string;
  olt?: string;
}

export interface TrafficHistory {
  timestamp: string;
  rx_mbps: number;
  tx_mbps: number;
  total_mbps: number;
  uptime_formatted: string;
}

export interface TrafficSummary {
  server_id: number;
  server_name: string;
  active_users: number;
  avg_mbps: number;
  max_mbps: number;
  total_mbps: number;
  load_percentage: number;
}

export interface DashboardSummary {
  total_active_users: number;
  total_bandwidth_usage: number;
  top_consumers: TrafficData[];
  server_summary: TrafficSummary[];
  collection_status?: {
    last_collection?: string;
    collection_active: boolean;
    collection_interval: string;
  };
  last_updated: string;
}

export interface TrafficStats {
  period_hours: number;
  total_records: number;
  unique_users: number;
  avg_bandwidth_mbps: number;
  max_bandwidth_mbps: number;
  total_bandwidth_mbps: number;
  top_olts: Array<{
    olt: string;
    user_count: number;
    total_bandwidth: number;
  }>;
  analysis_timestamp: string;
}

export interface CollectionResponse {
  status: string;
  message: string;
  data: {
    collection_interval: string;
    estimated_completion: string;
  };
}

// ====================================================================
// TRAFFIC MONITORING API FUNCTIONS
// ====================================================================

/**
 * Get latest traffic data untuk dashboard
 * @param limit - Maximum number of records (default: 100)
 * @param server_id - Filter by Mikrotik server (optional)
 * @param olt_filter - Filter by OLT (optional)
 */
export const getLatestTrafficData = async (
  limit: number = 100,
  server_id?: number,
  olt_filter?: string
): Promise<TrafficData[]> => {
  try {
    const params: any = { limit };
    if (server_id) params.server_id = server_id;
    if (olt_filter) params.olt_filter = olt_filter;

    const response = await apiClient.get('/traffic/monitoring/latest', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching latest traffic data:', error);
    throw error;
  }
};

/**
 * Get traffic history untuk user tertentu
 * @param data_teknis_id - User ID
 * @param hours - Hours of history to fetch (default: 24, max: 168)
 */
export const getUserTrafficHistory = async (
  data_teknis_id: number,
  hours: number = 24
): Promise<TrafficHistory[]> => {
  try {
    const response = await apiClient.get(
      `/traffic/monitoring/user/${data_teknis_id}`,
      { params: { hours } }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching user traffic history:', error);
    throw error;
  }
};

/**
 * Get traffic summary untuk server tertentu
 * @param server_id - Server ID
 * @param hours - Hours of data to analyze (default: 24, max: 168)
 */
export const getServerTrafficSummary = async (
  server_id: number,
  hours: number = 24
): Promise<TrafficSummary[]> => {
  try {
    const response = await apiClient.get(
      `/traffic/monitoring/server/${server_id}`,
      { params: { hours } }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching server traffic summary:', error);
    throw error;
  }
};

/**
 * Get dashboard summary data
 * @param hours - Hours of data to analyze (default: 24, max: 168)
 */
export const getDashboardSummary = async (
  hours: number = 24
): Promise<DashboardSummary> => {
  try {
    const response = await apiClient.get('/traffic/monitoring/dashboard', {
      params: { hours }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    throw error;
  }
};

/**
 * Trigger manual traffic collection
 */
export const triggerTrafficCollection = async (): Promise<CollectionResponse> => {
  try {
    const response = await apiClient.post('/traffic/monitoring/collect');
    return response.data;
  } catch (error) {
    console.error('Error triggering traffic collection:', error);
    throw error;
  }
};

/**
 * Get traffic statistics untuk analisis
 * @param hours - Hours of data to analyze (default: 24, max: 168)
 */
export const getTrafficStatistics = async (
  hours: number = 24
): Promise<TrafficStats> => {
  try {
    const response = await apiClient.get('/traffic/monitoring/stats', {
      params: { hours }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching traffic statistics:', error);
    throw error;
  }
};

// ====================================================================
// UTILITY FUNCTIONS
// ====================================================================

/**
 * Format bytes ke human readable format
 */
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format Mbps ke human readable format
 */
export const formatMbps = (mbps: number): string => {
  if (mbps < 1) {
    return `${(mbps * 1000).toFixed(1)} Kbps`;
  }
  if (mbps >= 1000) {
    return `${(mbps / 1000).toFixed(2)} Gbps`;
  }
  return `${mbps.toFixed(2)} Mbps`;
};

/**
 * Get color class based on bandwidth usage
 */
export const getBandwidthColor = (mbps: number): string => {
  if (mbps < 10) return 'success';    // Green
  if (mbps < 50) return 'warning';    // Yellow
  if (mbps < 100) return 'info';      // Blue
  return 'danger';                   // Red
};

/**
 * Get server load color based on percentage
 */
export const getLoadColor = (percentage: number): string => {
  if (percentage < 50) return 'success';
  if (percentage < 75) return 'warning';
  if (percentage < 90) return 'info';
  return 'danger';
};

/**
 * Format timestamp ke local time
 */
export const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

/**
 * Calculate percentage
 */
export const calculatePercentage = (value: number, total: number): number => {
  if (total === 0) return 0;
  return Math.min((value / total) * 100, 100);
};