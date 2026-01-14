// src/services/analyticsAPI.ts
// API client untuk AI Analytics endpoints

import apiClient from './api';

// ====================================================================
// TYPES
// ====================================================================

// Request types
export interface RevenueAnalysisRequest {
  query_type: 'revenue';
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  brand?: string;
}

export interface LatePaymentAnalysisRequest {
  query_type: 'late_payments';
  start_date?: string; // YYYY-MM-DD
  end_date?: string;   // YYYY-MM-DD
  limit?: number;
}

export interface CustomerBehaviorAnalysisRequest {
  query_type: 'customer_behavior';
  limit?: number;
}

export interface ChatAnalyticsRequest {
  question: string;
  context_type?: 'revenue' | 'late_payments' | 'customer_behavior';
  context_params?: Record<string, any>;
}

// Response types
export interface AIInsightResponse {
  summary: string;
  data_snapshot: Record<string, any>;
  confidence?: number;
}

export interface RevenueAnalysisResponse extends AIInsightResponse {
  key_findings: string[];
  recommendations: string[];
  opportunities: string[];
  risks: string[];
}

export interface LatePaymentAnalysisResponse extends AIInsightResponse {
  risk_assessment: Record<string, any>;
  follow_up_strategy: string[];
  prevention_recommendations: string[];
  communication_template?: Record<string, string>;
}

export interface CustomerBehaviorAnalysisResponse extends AIInsightResponse {
  customer_insights: Record<string, any>;
  segment_analysis: Array<{
    segment: string;
    characteristics: string;
    strategy: string;
  }>;
  retention_strategies: string[];
  upsell_opportunities: string[];
}

export interface ChatAnalyticsResponse {
  answer: string;
  context_used?: string;
}

// Data response types (without AI analysis)
export interface RevenueDataResponse {
  period: {
    start: string;
    end: string;
    days: number;
  };
  total_revenue: number;
  paid_revenue: number;
  pending_revenue: number;
  collection_rate: number;
  daily_revenue: Array<{
    date: string;
    total: number;
    paid: number;
    pending: number;
  }>;
  monthly_revenue: Array<{
    month: string;
    total: number;
    count: number;
  }>;
  payment_methods: Array<{
    method: string;
    count: number;
    amount: number;
  }>;
  revenue_by_brand: Array<{
    brand: string;
    total: number;
    paid: number;
    count: number;
    collection_rate: number;
  }>;
  growth_rate: number;
  forecast_next_month: number;
  total_invoices: number;
  paid_invoices: number;
  pending_invoices: number;
}

export interface LatePaymentDataResponse {
  period: {
    start: string;
    end: string;
  };
  total_late_customers: number;
  total_outstanding: number;
  avg_days_late: number;
  late_customers: Array<{
    customer_id: number;
    nama: string;
    brand: string;
    no_telp: string;
    email: string;
    alamat: string;
    late_invoices: Array<{
      invoice_number: string;
      invoice_date: string;
      due_date: string;
      amount: number;
      days_late: number;
      status: string;
      brand: string;
    }>;
    total_outstanding: number;
    days_late_avg: number;
    risk_score: number;
  }>;
  risk_segments: {
    high_risk: number;
    medium_risk: number;
    low_risk: number;
  };
  follow_up_suggestions: Array<{
    priority: string;
    customer: string;
    no_telp: string;
    action: string;
    reason: string;
  }>;
}

export interface CustomerBehaviorDataResponse {
  period: {
    start: string;
    end: string;
  };
  total_customers_analyzed: number;
  customer_segments: Array<{
    segment: string;
    count: number;
    total_clv: number;
    avg_clv: number;
  }>;
  top_customers: Array<{
    customer_id: number;
    nama: string;
    brand: string;
    segment: string;
    total_invoices: number;
    payment_rate: number;
    total_spent: number;
    avg_monthly_spend: number;
    estimated_clv: number;
    avg_payment_days: number;
    late_payment_rate: number;
    loyalty_score: number;
    churn_risk: number;
    months_active: number;
  }>;
  churn_risk_analysis: {
    high_risk_count: number;
    medium_risk_count: number;
    high_risk_customers: Array<any>;
    avg_churn_risk: number;
  };
  loyalty_analysis: {
    avg_loyalty_score: number;
    loyal_customers: number;
  };
  payment_patterns: {
    avg_payment_days: number;
    avg_late_payment_rate: number;
  };
}

// ====================================================================
// API CLIENT
// ====================================================================

const analyticsAPI = {
  // --------------------------------------------------------------------
  // AI INSIGHTS ENDPOINTS
  // --------------------------------------------------------------------

  /**
   * Get revenue insights from AI
   */
  async getRevenueInsights(request: RevenueAnalysisRequest): Promise<RevenueAnalysisResponse> {
    const response = await apiClient.post('/analytics/insights/revenue', request);
    return response.data;
  },

  /**
   * Get late payment insights from AI
   */
  async getLatePaymentInsights(request: LatePaymentAnalysisRequest): Promise<LatePaymentAnalysisResponse> {
    const response = await apiClient.post('/analytics/insights/late-payments', request);
    return response.data;
  },

  /**
   * Get customer behavior insights from AI
   */
  async getCustomerBehaviorInsights(request: CustomerBehaviorAnalysisRequest): Promise<CustomerBehaviorAnalysisResponse> {
    const response = await apiClient.post('/analytics/insights/customer-behavior', request);
    return response.data;
  },

  // --------------------------------------------------------------------
  // RAW DATA ENDPOINTS (without AI)
  // --------------------------------------------------------------------

  /**
   * Get revenue data (without AI analysis)
   */
  async getRevenueData(params: {
    start_date: string;
    end_date: string;
    brand?: string;
  }): Promise<RevenueDataResponse> {
    const response = await apiClient.get('/analytics/data/revenue', { params });
    return response.data;
  },

  /**
   * Get late payment data (without AI analysis)
   */
  async getLatePaymentData(params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<LatePaymentDataResponse> {
    const response = await apiClient.get('/analytics/data/late-payments', { params });
    return response.data;
  },

  /**
   * Get customer behavior data (without AI analysis)
   */
  async getCustomerBehaviorData(params?: {
    limit?: number;
  }): Promise<CustomerBehaviorDataResponse> {
    const response = await apiClient.get('/analytics/data/customer-behavior', { params });
    return response.data;
  },

  // --------------------------------------------------------------------
  // CHAT ENDPOINT
  // --------------------------------------------------------------------

  /**
   * Send chat message to AI
   */
  async chatAnalytics(request: ChatAnalyticsRequest): Promise<ChatAnalyticsResponse> {
    const response = await apiClient.post('/analytics/chat', request);
    return response.data;
  },

  // --------------------------------------------------------------------
  // SUMMARY ENDPOINT
  // --------------------------------------------------------------------

  /**
   * Get analytics summary for dashboard
   */
  async getSummary(): Promise<{
    revenue: {
      total_revenue: number;
      paid_revenue: number;
      collection_rate: number;
      growth_rate: number;
      forecast_next_month: number;
    };
    late_payments: {
      total_late_customers: number;
      total_outstanding: number;
      avg_days_late: number;
      high_risk_count: number;
    };
    customers: {
      total_customers: number;
      avg_loyalty_score: number;
      avg_churn_risk: number;
      high_churn_risk_count: number;
    };
    last_updated: string;
  }> {
    const response = await apiClient.get('/analytics/summary');
    return response.data;
  }
};

export default analyticsAPI;
