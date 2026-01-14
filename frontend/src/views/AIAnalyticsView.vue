<!-- src/views/AIAnalyticsView.vue -->
<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar class="me-4 elevation-4" color="purple" size="80">
              <v-icon color="white" size="40">mdi-brain</v-icon>
            </v-avatar>
            <div>
              <h1 class="text-h4 font-weight-bold text-white mb-2">AI Analytics</h1>
              <p class="header-subtitle mb-0">
                Insight cerdas berpowered oleh Artacom AI Model
              </p>
            </div>
          </div>
          <v-spacer></v-spacer>
        </div>
      </div>
    </div>

    <!-- Filter Controls Card -->
    <v-card class="mb-4 mb-md-6 modern-card" elevation="0" rounded="xl">
      <v-card-text class="pa-3 pa-md-4">
        <v-row align="center" class="ga-3">
          <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
            <v-menu v-model="menuStart" :close-on-content-click="false" location="bottom start" offset="8">
              <template v-slot:activator="{ props }">
                <v-text-field
                  :model-value="formatDate(dateRange.start)"
                  label="Tanggal Awal"
                  prepend-inner-icon="mdi-calendar"
                  readonly
                  v-bind="props"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  class="modern-input"
                  color="purple"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateRange.start"
                @update:model-value="menuStart = false"
                color="purple"
              ></v-date-picker>
            </v-menu>
          </v-col>

          <v-col cols="12" sm="6" md="auto" class="flex-grow-1">
            <v-menu v-model="menuEnd" :close-on-content-click="false" location="bottom start" offset="8">
              <template v-slot:activator="{ props }">
                <v-text-field
                  :model-value="formatDate(dateRange.end)"
                  label="Tanggal Akhir"
                  prepend-inner-icon="mdi-calendar"
                  readonly
                  v-bind="props"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  class="modern-input"
                  color="purple"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateRange.end"
                @update:model-value="menuEnd = false"
                color="purple"
              ></v-date-picker>
            </v-menu>
          </v-col>

          <v-col cols="12" sm="12" md="auto">
            <div class="d-flex ga-3">
              <v-btn
                color="purple"
                @click="fetchAllInsights"
                :loading="store.isLoading"
                size="large"
                class="text-none modern-btn"
                prepend-icon="mdi-refresh"
                rounded="lg"
              >
                Refresh
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Loading State -->
    <div v-if="store.isLoading && !store.hasRevenueData" class="text-center pa-10 pa-md-16">
      <div class="loading-container">
        <v-progress-circular
          indeterminate
          color="purple"
          size="80"
          width="4"
          class="mb-4"
        ></v-progress-circular>
        <h3 class="text-h6 text-medium-emphasis mb-2">Menganalisis data...</h3>
        <p class="text-body-2 text-medium-emphasis">AI sedang memproses data Anda</p>
      </div>
    </div>

    <!-- Analytics Content -->
    <div v-else class="analytics-content">
      <!-- Insight Cards Grid -->
      <v-row class="mb-6">
        <!-- Revenue Analysis Card -->
        <v-col cols="12" md="4">
          <v-card
            class="modern-card insight-card revenue-card"
            elevation="0"
            rounded="xl"
            :loading="store.isLoading && store.currentAnalysisType === 'revenue'"
            @click="activeTab = 'revenue'"
            :class="{ 'active-card': activeTab === 'revenue' }"
            clickable
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-avatar color="purple-lighten-4" class="me-3">
                  <v-icon color="purple">mdi-chart-line</v-icon>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold">Pendapatan</h3>
                  <p class="text-caption text-medium-emphasis">Revenue Analysis</p>
                </div>
              </div>
              <div v-if="store.revenueInsights" class="insight-preview">
                <p class="text-body-2 mb-0">{{ store.revenueInsights.summary.substring(0, 100) }}...</p>
                <div class="mt-3 d-flex align-center">
                  <v-chip size="small" color="purple" variant="outlined">
                    {{ store.revenueInsights.key_findings?.length || 0 }} insights
                  </v-chip>
                </div>
              </div>
              <div v-else class="text-center pa-4">
                <v-btn
                  color="purple"
                  variant="outlined"
                  size="small"
                  @click.stop="fetchRevenueInsights"
                >
                  Analisis
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Late Payment Analysis Card -->
        <v-col cols="12" md="4">
          <v-card
            class="modern-card insight-card late-payment-card"
            elevation="0"
            rounded="xl"
            :loading="store.isLoading && store.currentAnalysisType === 'late_payments'"
            @click="activeTab = 'late_payments'"
            :class="{ 'active-card': activeTab === 'late_payments' }"
            clickable
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-avatar color="orange-lighten-4" class="me-3">
                  <v-icon color="orange">mdi-clock-alert</v-icon>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold">Pembayaran Telat</h3>
                  <p class="text-caption text-medium-emphasis">Late Payment Analysis</p>
                </div>
              </div>
              <div v-if="store.latePaymentInsights" class="insight-preview">
                <p class="text-body-2 mb-0">{{ store.latePaymentInsights.summary.substring(0, 100) }}...</p>
                <div class="mt-3 d-flex align-center">
                  <v-chip size="small" color="orange" variant="outlined">
                    {{ store.latePaymentInsights.follow_up_strategy?.length || 0 }} strategies
                  </v-chip>
                </div>
              </div>
              <div v-else class="text-center pa-4">
                <v-btn
                  color="orange"
                  variant="outlined"
                  size="small"
                  @click.stop="fetchLatePaymentInsights"
                >
                  Analisis
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Customer Behavior Card -->
        <v-col cols="12" md="4">
          <v-card
            class="modern-card insight-card customer-card"
            elevation="0"
            rounded="xl"
            :loading="store.isLoading && store.currentAnalysisType === 'customer_behavior'"
            @click="activeTab = 'customer_behavior'"
            :class="{ 'active-card': activeTab === 'customer_behavior' }"
            clickable
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-avatar color="blue-lighten-4" class="me-3">
                  <v-icon color="blue">mdi-account-group</v-icon>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold">Customer Behavior</h3>
                  <p class="text-caption text-medium-emphasis">Behavior Analysis</p>
                </div>
              </div>
              <div v-if="store.customerBehaviorInsights" class="insight-preview">
                <p class="text-body-2 mb-0">{{ store.customerBehaviorInsights.summary.substring(0, 100) }}...</p>
                <div class="mt-3 d-flex align-center">
                  <v-chip size="small" color="blue" variant="outlined">
                    {{ store.customerBehaviorInsights.segment_analysis?.length || 0 }} segments
                  </v-chip>
                </div>
              </div>
              <div v-else class="text-center pa-4">
                <v-btn
                  color="blue"
                  variant="outlined"
                  size="small"
                  @click.stop="fetchCustomerBehaviorInsights"
                >
                  Analisis
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Detailed Analysis Section -->
      <v-row>
        <v-col cols="12" lg="8">
          <!-- Revenue Analysis Detail -->
          <v-card v-if="activeTab === 'revenue' && store.revenueInsights" class="mb-4 modern-card" elevation="0" rounded="xl">
            <v-card-title class="pa-4 bg-purple-lighten-5">
              <v-icon start color="purple">mdi-chart-line</v-icon>
              <span class="text-h6 font-weight-bold">Analisis Pendapatan</span>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-4">
              <p class="text-body-1 mb-4">{{ store.revenueInsights.summary }}</p>

              <v-divider class="my-4"></v-divider>

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Temuan Utama</h4>
              <v-list>
                <v-list-item v-for="(finding, i) in store.revenueInsights.key_findings" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="purple" class="me-2">mdi-lightbulb</v-icon>
                  </template>
                  <v-list-item-title>{{ finding }}</v-list-item-title>
                </v-list-item>
              </v-list>

              <v-divider class="my-4"></v-divider>

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Rekomendasi</h4>
              <v-list>
                <v-list-item v-for="(rec, i) in store.revenueInsights.recommendations" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="green" class="me-2">mdi-check-circle</v-icon>
                  </template>
                  <v-list-item-title>{{ rec }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Late Payment Analysis Detail -->
          <v-card v-if="activeTab === 'late_payments' && store.latePaymentInsights" class="mb-4 modern-card" elevation="0" rounded="xl">
            <v-card-title class="pa-4 bg-orange-lighten-5">
              <v-icon start color="orange">mdi-clock-alert</v-icon>
              <span class="text-h6 font-weight-bold">Analisis Pembayaran Telat</span>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-4">
              <p class="text-body-1 mb-4">{{ store.latePaymentInsights.summary }}</p>

              <v-alert v-if="store.latePaymentInsights.risk_assessment" type="warning" class="mb-4" variant="tonal">
                <template v-slot:title>
                  Risk Assessment: {{ store.latePaymentInsights.risk_assessment.overall_risk }}
                </template>
              </v-alert>

              <v-divider class="my-4"></v-divider>

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Strategi Follow-Up</h4>
              <v-list>
                <v-list-item v-for="(strategy, i) in store.latePaymentInsights.follow_up_strategy" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="orange" class="me-2">mdi-phone-forward</v-icon>
                  </template>
                  <v-list-item-title>{{ strategy }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Customer Behavior Detail -->
          <v-card v-if="activeTab === 'customer_behavior' && store.customerBehaviorInsights" class="mb-4 modern-card" elevation="0" rounded="xl">
            <v-card-title class="pa-4 bg-blue-lighten-5">
              <v-icon start color="blue">mdi-account-group</v-icon>
              <span class="text-h6 font-weight-bold">Analisis Perilaku Customer</span>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-4">
              <p class="text-body-1 mb-4">{{ store.customerBehaviorInsights.summary }}</p>

              <v-divider class="my-4"></v-divider>

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Segmentasi Customer</h4>
              <v-list>
                <v-list-item v-for="(segment, i) in store.customerBehaviorInsights.segment_analysis" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="blue" class="me-2">mdi-account-box</v-icon>
                  </template>
                  <v-list-item-title>{{ segment.segment }}</v-list-item-title>
                  <v-list-item-subtitle>{{ segment.strategy }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <v-divider class="my-4"></v-divider>

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Strategi Retensi</h4>
              <v-list>
                <v-list-item v-for="(strategy, i) in store.customerBehaviorInsights.retention_strategies" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="green" class="me-2">mdi-heart</v-icon>
                  </template>
                  <v-list-item-title>{{ strategy }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Chat Interface -->
        <v-col cols="12" lg="4">
          <v-card class="chat-card modern-card" elevation="0" rounded="xl">
            <v-card-title class="pa-4 bg-purple-lighten-5">
              <v-icon start color="purple">mdi-chat</v-icon>
              <span class="text-h6 font-weight-bold">Chat dengan AI</span>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-4 chat-messages" style="max-height: 400px; overflow-y: auto;">
              <div v-if="store.chatHistory.length === 0" class="text-center pa-4">
                <v-icon size="48" color="purple-lighten-1" class="mb-2">mdi-robot</v-icon>
                <p class="text-body-2 text-medium-emphasis">Tanyakan apa saja tentang data analytics Anda</p>
                <v-chip group class="mt-3">
                  <v-chip
                    size="small"
                    variant="outlined"
                    @click="askQuickQuestion('Bagaimana tren pendapatan bulan ini?')"
                  >
                    Tren Pendapatan
                  </v-chip>
                  <v-chip
                    size="small"
                    variant="outlined"
                    @click="askQuickQuestion('Customer mana yang paling berisiko?')"
                  >
                    Customer Berisiko
                  </v-chip>
                </v-chip>
              </div>
              <div v-else>
                <div
                  v-for="msg in store.chatHistory"
                  :key="msg.id"
                  :class="['chat-message', msg.role === 'user' ? 'user-message' : 'ai-message']"
                  class="mb-3"
                >
                  <v-avatar :size="32" :color="msg.role === 'user' ? 'purple' : 'grey'" class="mb-2">
                    <v-icon size="20" color="white">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-robot' }}
                    </v-icon>
                  </v-avatar>
                  <div class="message-bubble">
                    <div class="text-body-2 mb-0 markdown-content" v-html="renderMarkdown(msg.content)"></div>
                  </div>
                </div>
                <div v-if="store.isChatLoading" class="text-center pa-2">
                  <v-progress-circular indeterminate size="24" color="purple"></v-progress-circular>
                </div>
              </div>
            </v-card-text>
            <v-divider></v-divider>
            <v-card-text class="pa-3">
              <v-text-field
                v-model="chatQuestion"
                placeholder="Tanya sesuatu..."
                variant="outlined"
                density="comfortable"
                hide-details
                @keyup.enter="sendChatMessage"
                :disabled="store.isChatLoading"
              >
                <template v-slot:append-inner>
                  <v-btn
                    icon="mdi-send"
                    color="purple"
                    variant="text"
                    :disabled="!chatQuestion.trim() || store.isChatLoading"
                    @click="sendChatMessage"
                  ></v-btn>
                </template>
              </v-text-field>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useAnalyticsStore } from '@/stores/analytics';
import { storeToRefs } from 'pinia';

const store = useAnalyticsStore();
const { dateRange } = storeToRefs(store);

// UI State
const activeTab = ref<'revenue' | 'late_payments' | 'customer_behavior'>('revenue');
const menuStart = ref(false);
const menuEnd = ref(false);
const chatQuestion = ref('');

// Simple Markdown to HTML converter
const renderMarkdown = (text: string): string => {
  if (!text) return '';

  let html = text;

  // Escape HTML first to prevent XSS
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (but skip processing inside them)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Tables - parse markdown tables to HTML
  const tableRegex = /\|(.+)\|\n\|[-|\s]+\|\n((?:\|.+\|\n?)+)/g;
  html = html.replace(tableRegex, (match, header, body) => {
    const headers = header.split('|').filter(h => h.trim()).map(h => `<th>${h.trim()}</th>`).join('');
    const rows = body.trim().split('\n').map(row => {
      const cells = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
      return `<tr>${cells}</tr>`;
    }).join('');
    return `<table class="markdown-table"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
  });

  // Unordered lists (with - or *)
  html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\n<ul>/g, '\n');

  // Ordered lists (1. 2. 3.)
  html = html.replace(/^\d+\. (.+)$/gm, '<oli>$1</oli>');
  html = html.replace(/(<oli>.*<\/oli>)/s, '<ol>$1</ol>'.replace(/oli/g, 'li'));
  html = html.replace(/<\/ol>\n<ol>/g, '\n');

  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');

  // Wrap in paragraphs
  html = `<p>${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p>(<table[^>]*>)/g, '$1');
  html = html.replace(/(<\/table>)<\/p>/g, '$1');
  html = html.replace(/<p>(<h[1-6]>)/g, '$1');
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
  html = html.replace(/<p>(<ul>)/g, '$1');
  html = html.replace(/(<\/ul>)<\/p>/g, '$1');
  html = html.replace(/<p>(<ol>)/g, '$1');
  html = html.replace(/(<\/ol>)<\/p>/g, '$1');
  html = html.replace(/<p>(<pre>)/g, '$1');
  html = html.replace(/(<\/pre>)<\/p>/g, '$1');

  return html;
};

// Methods
const formatDate = (date: Date) => {
  return date.toISOString().split('T')[0];
};

const fetchAllInsights = async () => {
  try {
    await Promise.all([
      store.fetchRevenueInsights(true),
      store.fetchLatePaymentInsights(true),
      store.fetchCustomerBehaviorInsights(true)
    ]);
  } catch (error) {
    console.error('Error fetching insights:', error);
  }
};

const fetchRevenueInsights = async () => {
  try {
    await store.fetchRevenueInsights(true);
  } catch (error) {
    console.error('Error fetching revenue insights:', error);
  }
};

const fetchLatePaymentInsights = async () => {
  try {
    await store.fetchLatePaymentInsights(true);
  } catch (error) {
    console.error('Error fetching late payment insights:', error);
  }
};

const fetchCustomerBehaviorInsights = async () => {
  try {
    await store.fetchCustomerBehaviorInsights(true);
  } catch (error) {
    console.error('Error fetching customer behavior insights:', error);
  }
};

const askQuickQuestion = (question: string) => {
  chatQuestion.value = question;
  sendChatMessage();
};

const sendChatMessage = async () => {
  const question = chatQuestion.value.trim();
  if (!question) return;

  try {
    // Jangan kirim context_type, biarkan backend auto-detect dari pertanyaan
    await store.sendChatMessage(question, undefined);
    chatQuestion.value = '';
  } catch (error) {
    console.error('Error sending chat message:', error);
  }
};

// Lifecycle
onMounted(() => {
  // Auto-fetch insights if not cached
  if (!store.hasRevenueData) {
    fetchRevenueInsights();
  }
  if (!store.hasLatePaymentData) {
    fetchLatePaymentInsights();
  }
  if (!store.hasCustomerBehaviorData) {
    fetchCustomerBehaviorInsights();
  }
});

// Watch date range changes
watch(dateRange, () => {
  store.clearCache();
}, { deep: true });
</script>

<style scoped>
.header-card {
  border-radius: 16px;
  overflow: hidden;
}

.header-section {
  background: linear-gradient(135deg, #9C27B0 0%, #6200EA 100%);
  padding: 24px;
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.modern-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.modern-input :deep(.v-field) {
  border-radius: 12px;
}

.insight-card {
  transition: all 0.3s ease;
  cursor: pointer;
  height: 100%;
}

.insight-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
}

.insight-card.active-card {
  border: 2px solid #9C27B0;
}

.insight-preview p {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chat-card {
  height: calc(100% - 16px);
}

.chat-messages {
  display: flex;
  flex-direction: column;
}

.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-bubble {
  background: #9C27B0;
  color: white;
  border-radius: 12px 12px 0 12px;
}

.ai-message .message-bubble {
  background: #F5F5F5;
  color: #333;
  border-radius: 12px 12px 12px 0;
}

.message-bubble {
  padding: 10px 14px;
  max-width: 80%;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

@media (max-width: 960px) {
  .header-section {
    padding: 16px;
  }

  .chat-card {
    height: auto;
  }
}

/* Markdown Content Styles */
.markdown-content {
  line-height: 1.6;
  word-wrap: break-word;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
}

.markdown-content h1 {
  font-size: 1.25rem;
}

.markdown-content h2 {
  font-size: 1.1rem;
}

.markdown-content h3 {
  font-size: 1rem;
}

.markdown-content p {
  margin-bottom: 8px;
}

.markdown-content ul,
.markdown-content ol {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin-bottom: 4px;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content code.inline-code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background: rgba(0, 0, 0, 0.05);
  padding: 8px 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content pre code {
  font-family: monospace;
  font-size: 0.9em;
}

/* Markdown Table Styles */
.markdown-content table.markdown-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.9rem;
}

.markdown-content table.markdown-table th,
.markdown-content table.markdown-table td {
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content table.markdown-table th {
  background: rgba(156, 39, 176, 0.1);
  font-weight: 600;
}

.markdown-content table.markdown-table tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

.user-message .markdown-content table.markdown-table th {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.user-message .markdown-content table.markdown-table td {
  border-color: rgba(255, 255, 255, 0.3);
}

.user-message .markdown-content table.markdown-table tr:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-message .markdown-content code.inline-code {
  background: rgba(255, 255, 255, 0.2);
}

.user-message .markdown-content strong {
  font-weight: 600;
}
</style>
