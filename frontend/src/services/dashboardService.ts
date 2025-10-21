// src/services/dashboardService.ts
import apiClient from './api';

export const getDashboardData = () => {
  return apiClient.get('/dashboard/');
};