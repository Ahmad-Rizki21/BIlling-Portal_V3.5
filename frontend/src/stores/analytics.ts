// src/stores/analytics.ts
// Pinia store untuk AI Analytics

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import analyticsAPI from '@/services/analyticsAPI';
import type {
  RevenueAnalysisResponse,
  LatePaymentAnalysisResponse,
  CustomerBehaviorAnalysisResponse,
  ChatAnalyticsResponse,
  RevenueDataResponse,
  LatePaymentDataResponse,
  CustomerBehaviorDataResponse
} from '@/services/analyticsAPI';

export const useAnalyticsStore = defineStore('analytics', () => {
  // ====================================================================
  // STATE
  // ====================================================================

  // Loading states
  const isLoading = ref(false);
  const isChatLoading = ref(false);

  // Error state
  const error = ref<string | null>(null);

  // Current analysis type
  const currentAnalysisType = ref<'revenue' | 'late_payments' | 'customer_behavior' | null>(null);

  // Revenue analysis data
  const revenueInsights = ref<RevenueAnalysisResponse | null>(null);
  const revenueData = ref<RevenueDataResponse | null>(null);

  // Late payment analysis data
  const latePaymentInsights = ref<LatePaymentAnalysisResponse | null>(null);
  const latePaymentData = ref<LatePaymentDataResponse | null>(null);

  // Customer behavior analysis data
  const customerBehaviorInsights = ref<CustomerBehaviorAnalysisResponse | null>(null);
  const customerBehaviorData = ref<CustomerBehaviorDataResponse | null>(null);

  // Chat history
  interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  }

  const chatHistory = ref<ChatMessage[]>([]);
  const chatContext = ref<string | null>(null);

  // Filters
  const dateRange = ref({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    end: new Date()
  });

  const selectedBrand = ref<string | null>(null);

  // Cache timestamps
  const cacheTimestamps = ref<{
    revenue?: Date;
    latePayments?: Date;
    customerBehavior?: Date;
  }>({});

  // Cache TTL in milliseconds (1 hour)
  const CACHE_TTL = 60 * 60 * 1000;

  // ====================================================================
  // COMPUTED
  // ====================================================================

  const hasRevenueData = computed(() => !!revenueInsights.value);
  const hasLatePaymentData = computed(() => !!latePaymentInsights.value);
  const hasCustomerBehaviorData = computed(() => !!customerBehaviorInsights.value);

  const isDataStale = computed(() => (type: 'revenue' | 'latePayments' | 'customerBehavior') => {
    const timestamp = cacheTimestamps.value[type];
    if (!timestamp) return true;
    return Date.now() - timestamp.getTime() > CACHE_TTL;
  });

  // ====================================================================
  // ACTIONS - REVENUE ANALYSIS
  // ====================================================================

  async function fetchRevenueInsights(forceRefresh = false) {
    // Check cache
    if (!forceRefresh && !isDataStale.value('revenue') && revenueInsights.value) {
      return revenueInsights.value;
    }

    isLoading.value = true;
    error.value = null;
    currentAnalysisType.value = 'revenue';

    try {
      const response = await analyticsAPI.getRevenueInsights({
        query_type: 'revenue',
        start_date: formatDateForAPI(dateRange.value.start),
        end_date: formatDateForAPI(dateRange.value.end),
        brand: selectedBrand.value
      });

      revenueInsights.value = response;
      cacheTimestamps.value.revenue = new Date();
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan insight pendapatan';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchRevenueData() {
    try {
      const response = await analyticsAPI.getRevenueData({
        start_date: formatDateForAPI(dateRange.value.start),
        end_date: formatDateForAPI(dateRange.value.end),
        brand: selectedBrand.value
      });

      revenueData.value = response;
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan data pendapatan';
      throw err;
    }
  }

  // ====================================================================
  // ACTIONS - LATE PAYMENT ANALYSIS
  // ====================================================================

  async function fetchLatePaymentInsights(forceRefresh = false) {
    // Check cache
    if (!forceRefresh && !isDataStale.value('latePayments') && latePaymentInsights.value) {
      return latePaymentInsights.value;
    }

    isLoading.value = true;
    error.value = null;
    currentAnalysisType.value = 'late_payments';

    try {
      const response = await analyticsAPI.getLatePaymentInsights({
        query_type: 'late_payments',
        limit: 100
      });

      latePaymentInsights.value = response;
      cacheTimestamps.value.latePayments = new Date();
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan insight pembayaran telat';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchLatePaymentData() {
    try {
      const response = await analyticsAPI.getLatePaymentData({
        limit: 100
      });

      latePaymentData.value = response;
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan data pembayaran telat';
      throw err;
    }
  }

  // ====================================================================
  // ACTIONS - CUSTOMER BEHAVIOR ANALYSIS
  // ====================================================================

  async function fetchCustomerBehaviorInsights(forceRefresh = false) {
    // Check cache
    if (!forceRefresh && !isDataStale.value('customerBehavior') && customerBehaviorInsights.value) {
      return customerBehaviorInsights.value;
    }

    isLoading.value = true;
    error.value = null;
    currentAnalysisType.value = 'customer_behavior';

    try {
      const response = await analyticsAPI.getCustomerBehaviorInsights({
        query_type: 'customer_behavior',
        limit: 100
      });

      customerBehaviorInsights.value = response;
      cacheTimestamps.value.customerBehavior = new Date();
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan insight perilaku customer';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchCustomerBehaviorData() {
    try {
      const response = await analyticsAPI.getCustomerBehaviorData({
        limit: 100
      });

      customerBehaviorData.value = response;
      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mendapatkan data perilaku customer';
      throw err;
    }
  }

  // ====================================================================
  // ACTIONS - CHAT
  // ====================================================================

  async function sendChatMessage(question: string, contextType?: string) {
    isChatLoading.value = true;
    error.value = null;

    // Add user message to history
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    chatHistory.value.push(userMessage);

    try {
      const response = await analyticsAPI.chatAnalytics({
        question,
        context_type: contextType as any,
        context_params: contextType ? {
          limit: 50
        } : undefined
      });

      // Add assistant response to history
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      };
      chatHistory.value.push(assistantMessage);
      chatContext.value = response.context_used || null;

      return response;
    } catch (err: any) {
      error.value = err.message || 'Gagal mengirim pesan';
      // Add error message to history
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: 'Maaf, terjadi kesalahan. Silakan coba lagi.',
        timestamp: new Date()
      };
      chatHistory.value.push(errorMessage);
      throw err;
    } finally {
      isChatLoading.value = false;
    }
  }

  function clearChatHistory() {
    chatHistory.value = [];
    chatContext.value = null;
  }

  // ====================================================================
  // ACTIONS - UTILITIES
  // ====================================================================

  function setDateRange(start: Date, end: Date) {
    dateRange.value = { start, end };
    // Clear cache when date range changes
    cacheTimestamps.value = {};
  }

  function setBrand(brand: string | null) {
    selectedBrand.value = brand;
    // Clear cache when brand changes
    cacheTimestamps.value = {};
  }

  function clearCache() {
    cacheTimestamps.value = {};
  }

  function clearAllData() {
    revenueInsights.value = null;
    revenueData.value = null;
    latePaymentInsights.value = null;
    latePaymentData.value = null;
    customerBehaviorInsights.value = null;
    customerBehaviorData.value = null;
    chatHistory.value = [];
    chatContext.value = null;
    cacheTimestamps.value = {};
    error.value = null;
  }

  // ====================================================================
  // HELPERS
  // ====================================================================

  function formatDateForAPI(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // ====================================================================
  // RETURN
  // ====================================================================

  return {
    // State
    isLoading,
    isChatLoading,
    error,
    currentAnalysisType,
    revenueInsights,
    revenueData,
    latePaymentInsights,
    latePaymentData,
    customerBehaviorInsights,
    customerBehaviorData,
    chatHistory,
    chatContext,
    dateRange,
    selectedBrand,

    // Computed
    hasRevenueData,
    hasLatePaymentData,
    hasCustomerBehaviorData,

    // Actions - Revenue
    fetchRevenueInsights,
    fetchRevenueData,

    // Actions - Late Payments
    fetchLatePaymentInsights,
    fetchLatePaymentData,

    // Actions - Customer Behavior
    fetchCustomerBehaviorInsights,
    fetchCustomerBehaviorData,

    // Actions - Chat
    sendChatMessage,
    clearChatHistory,

    // Actions - Utilities
    setDateRange,
    setBrand,
    clearCache,
    clearAllData
  };
});
