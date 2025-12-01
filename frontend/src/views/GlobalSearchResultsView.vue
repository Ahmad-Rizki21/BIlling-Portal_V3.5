<template>
  <v-container class="global-search-results" fluid>
    <!-- Search Header -->
    <v-card class="search-header-card mb-6" elevation="2">
      <v-card-text class="pa-4">
        <div class="d-flex align-center gap-4">
          <v-icon color="primary" size="24">mdi-magnify</v-icon>
          <div class="flex-grow-1">
            <h1 class="text-h5 font-weight-bold mb-1">
              Hasil Pencarian Global
            </h1>
            <p class="text-body-2 text-grey-lighten-1">
              Menampilkan {{ totalResults }} hasil untuk "{{ searchQuery }}"
            </p>
          </div>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-arrow-left"
            @click="$router.go(-1)"
          >
            Kembali
          </v-btn>
        </div>

        <!-- Quick Filters -->
        <div class="d-flex gap-2 mt-4" v-if="availableCategories.length > 1">
          <v-chip
            v-for="category in availableCategories"
            :key="category"
            :color="activeCategories.includes(category) ? getCategoryColor(category) : 'grey-lighten-2'"
            :variant="activeCategories.includes(category) ? 'flat' : 'outlined'"
            clickable
            @click="toggleCategory(category)"
            class="filter-chip"
          >
            <v-icon start :size="16">{{ getCategoryIcon(category) }}</v-icon>
            {{ getCategoryTitle(category) }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular
        indeterminate
        color="primary"
        size="48"
        class="mb-4"
      ></v-progress-circular>
      <div class="text-h6 font-weight-medium">Mencari...</div>
      <div class="text-body-2 text-grey-lighten-1">
        Sedang mencari di seluruh sistem
      </div>
    </div>

    <!-- Search Results -->
    <div v-else-if="hasResults">
      <!-- Results by Category -->
      <template v-for="(results, category) in categorizedResults" :key="category">
        <v-card class="category-card mb-6" elevation="1" v-if="results.length > 0">
          <v-card-title class="category-title">
            <div class="d-flex align-center gap-2">
              <v-icon :color="getCategoryColor(category)" :size="20">
                {{ getCategoryIcon(category) }}
              </v-icon>
              <span>{{ getCategoryTitle(category) }}</span>
              <v-spacer></v-spacer>
              <v-chip size="small" color="grey-lighten-1" variant="flat">
                {{ results.length }} hasil
              </v-chip>
            </div>
          </v-card-title>

          <v-divider></v-divider>

          <v-card-text class="pa-0">
            <v-list density="compact">
              <v-list-item
                v-for="item in paginatedResults[category]"
                :key="item.id"
                @click="handleItemClick(item, category)"
                class="result-item"
                :prepend-icon="getItemIcon(item, category)"
                :title="item.title"
                :subtitle="item.subtitle"
                ripple
              >
                <template v-slot:append>
                  <v-chip
                    v-if="getItemBadge(item, category)"
                    size="x-small"
                    :color="getItemBadgeColor(item, category)"
                    variant="flat"
                  >
                    {{ getItemBadge(item, category) }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <!-- Pagination for this category -->
            <v-pagination
              v-if="getCategoryPageCount(category) > 1"
              v-model="categoryPages[category]"
              :length="getCategoryPageCount(category)"
              :total-visible="5"
              class="pa-4"
              size="small"
            ></v-pagination>
          </v-card-text>
        </v-card>
      </template>

      <!-- Show More -->
      <v-card class="show-more-card" elevation="1" v-if="hasMoreResults">
        <v-card-actions class="justify-center pa-4">
          <v-btn
            variant="outlined"
            color="primary"
            prepend-icon="mdi-dots-horizontal"
            @click="loadMoreResults"
            :loading="loadingMore"
          >
            Tampilkan Lebih Banyak
          </v-btn>
        </v-card-actions>
      </v-card>
    </div>

    <!-- No Results -->
    <v-card v-else class="no-results-card" elevation="1">
      <v-card-text class="text-center pa-8">
        <v-icon size="64" color="grey-lighten-2" class="mb-4">
          mdi-magnify-close
        </v-icon>
        <div class="text-h6 font-weight-medium mb-2">Tidak Ada Hasil</div>
        <div class="text-body-2 text-grey-lighten-1 mb-4">
          Tidak ada hasil yang ditemukan untuk "{{ searchQuery }}"
        </div>
        <div class="suggestions">
          <div class="text-caption font-weight-bold text-grey-darken-1 mb-2">
            Saran:
          </div>
          <ul class="text-left text-body-2">
            <li>Periksa ejaan kata kunci</li>
            <li>Coba dengan kata kunci yang lebih umum</li>
            <li>Gunakan filter kategori untuk mempersempit pencarian</li>
            <li>Pastikan Anda memiliki izin untuk melihat data tersebut</li>
          </ul>
        </div>
      </v-card-text>
    </v-card>

    <!-- Search History (Optional) -->
    <v-card v-if="searchHistory.length > 0" class="history-card mt-6" elevation="1">
      <v-card-title class="text-body-1 font-weight-medium">
        <v-icon start color="grey-darken-1">mdi-history</v-icon>
        Pencarian Terbaru
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-2">
        <v-chip
          v-for="(historyItem, index) in searchHistory"
          :key="index"
          size="small"
          variant="outlined"
          clickable
          @click="searchHistoryItem(historyItem)"
          class="ma-1"
        >
          <v-icon start size="14">mdi-magnify</v-icon>
          {{ historyItem }}
        </v-chip>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/services/api'

// Interfaces
interface SearchResult {
  id: string | number
  type: string
  title: string
  subtitle?: string
  url?: string
  data?: any
}

interface SearchResults {
  query: string
  categories: string[]
  results: Record<string, SearchResult[]>
  total_count: number
  search_time: string
}

// Router
const route = useRoute()
const router = useRouter()

// State
const loading = ref(true)
const loadingMore = ref(false)
const searchQuery = ref('')
const searchResults = ref<SearchResults | null>(null)
const activeCategories = ref<string[]>([])
const categoryPages = ref<Record<string, number>>({})
const searchHistory = ref<string[]>([])
const itemsPerPage = 20

// Computed
const totalResults = computed(() => searchResults.value?.total_count || 0)

const availableCategories = computed(() => {
  return searchResults.value?.categories || []
})

const hasResults = computed(() => {
  return totalResults.value > 0
})

const hasMoreResults = computed(() => {
  return totalResults.value > itemsPerPage * Object.keys(categoryPages.value).length
})

const categorizedResults = computed(() => {
  if (!searchResults.value) return {}

  const results: Record<string, SearchResult[]> = {}
  const active = activeCategories.value.length > 0
    ? activeCategories.value
    : availableCategories.value

  active.forEach(category => {
    results[category] = searchResults.value?.results[category] || []
  })

  return results
})

const paginatedResults = computed(() => {
  const results: Record<string, SearchResult[]> = {}

  Object.entries(categorizedResults.value).forEach(([category, items]) => {
    const page = categoryPages.value[category] || 1
    const startIndex = (page - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage

    results[category] = items.slice(startIndex, endIndex)
  })

  return results
})

// Methods
const getCategoryIcon = (category: string): string => {
  const icons: Record<string, string> = {
    pelanggan: 'mdi-account-group',
    langganan: 'mdi-wifi',
    invoices: 'mdi-receipt-text',
    tickets: 'mdi-lifebuoy',
    activity_logs: 'mdi-history'
  }
  return icons[category] || 'mdi-file'
}

const getCategoryColor = (category: string): string => {
  const colors: Record<string, string> = {
    pelanggan: 'primary',
    langganan: 'success',
    invoices: 'warning',
    tickets: 'error',
    activity_logs: 'info'
  }
  return colors[category] || 'grey'
}

const getCategoryTitle = (category: string): string => {
  const titles: Record<string, string> = {
    pelanggan: 'Pelanggan',
    langganan: 'Langganan',
    invoices: 'Invoice',
    tickets: 'Trouble Tickets',
    activity_logs: 'Activity Log'
  }
  return titles[category] || category
}

const getItemIcon = (item: SearchResult, category: string): string => {
  if (category === 'pelanggan') return 'mdi-account'
  if (category === 'langganan') {
    return item.data?.status === 'active' ? 'mdi-wifi' : 'mdi-wifi-off'
  }
  if (category === 'invoices') return 'mdi-receipt'
  if (category === 'tickets') return 'mdi-ticket-outline'
  if (category === 'activity_logs') return 'mdi-clock-outline'
  return getCategoryIcon(category)
}

const getItemBadge = (item: SearchResult, category: string): string | null => {
  if (category === 'langganan') {
    return item.data?.status === 'suspended' ? 'Suspended' : item.data?.status
  }
  if (category === 'invoices') {
    return item.data?.status === 'unpaid' ? 'Belum Bayar' : item.data?.status
  }
  if (category === 'tickets') {
    return item.data?.status
  }
  return null
}

const getItemBadgeColor = (item: SearchResult, category: string): string => {
  if (category === 'langganan') {
    switch (item.data?.status) {
      case 'active': return 'success'
      case 'suspended': return 'warning'
      case 'stopped': return 'error'
      default: return 'grey'
    }
  }
  if (category === 'invoices') {
    return item.data?.status === 'unpaid' ? 'warning' : 'success'
  }
  if (category === 'tickets') {
    switch (item.data?.priority) {
      case 'high': return 'error'
      case 'medium': return 'warning'
      default: return 'info'
    }
  }
  return 'grey'
}

const getCategoryPageCount = (category: string): number => {
  const itemCount = categorizedResults.value[category]?.length || 0
  return Math.ceil(itemCount / itemsPerPage)
}

const toggleCategory = (category: string) => {
  const index = activeCategories.value.indexOf(category)
  if (index > -1) {
    activeCategories.value.splice(index, 1)
    delete categoryPages.value[category]
  } else {
    activeCategories.value.push(category)
    categoryPages.value[category] = 1
  }
}

const handleItemClick = (item: SearchResult, category: string) => {
  // Navigate to item
  if (item.url) {
    router.push(item.url)
  } else {
    // Default routing based on category
    switch (category) {
      case 'pelanggan':
        router.push(`/pelanggan?search=${item.id}`)
        break
      case 'langganan':
        router.push(`/langganan?search=${item.id}`)
        break
      case 'invoices':
        router.push(`/invoices?search=${item.id}`)
        break
      case 'tickets':
        router.push(`/trouble-tickets/${item.id}`)
        break
      case 'activity_logs':
        router.push(`/activity-logs?search=${item.id}`)
        break
      default:
        console.log('Unknown category:', category, 'Item:', item)
    }
  }

  // Add to search history
  addToSearchHistory(searchQuery.value)
}

const loadMoreResults = async () => {
  if (!searchQuery.value || loadingMore.value) return

  loadingMore.value = true
  try {
    const currentLimit = totalResults.value
    const response = await apiClient.get('/global-search', {
      params: {
        q: searchQuery.value,
        limit: itemsPerPage,
        offset: currentLimit,
        categories: activeCategories.value.join(',')
      }
    })

    if (response.data && response.data.results) {
      // Append new results to existing results
      Object.entries(response.data.results).forEach(([category, newItems]) => {
        if (searchResults.value?.results[category]) {
          searchResults.value.results[category].push(...newItems)
        }
      })
      searchResults.value.total_count = response.data.total_count
    }
  } catch (error) {
    console.error('[GlobalSearch] Failed to load more results:', error)
  } finally {
    loadingMore.value = false
  }
}

const searchHistoryItem = (query: string) => {
  searchQuery.value = query
  performSearch(query)
}

const addToSearchHistory = (query: string) => {
  if (!query || query.length < 2) return

  // Remove existing entry
  const index = searchHistory.value.indexOf(query)
  if (index > -1) {
    searchHistory.value.splice(index, 1)
  }

  // Add to beginning
  searchHistory.value.unshift(query)

  // Keep only last 10 searches
  if (searchHistory.value.length > 10) {
    searchHistory.value = searchHistory.value.slice(0, 10)
  }

  // Save to localStorage
  localStorage.setItem('search_history', JSON.stringify(searchHistory.value))
}

const loadSearchHistory = () => {
  try {
    const history = localStorage.getItem('search_history')
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('[GlobalSearch] Failed to load search history:', error)
  }
}

const performSearch = async (query: string) => {
  if (!query || query.length < 2) return

  loading.value = true
  try {
    const response = await apiClient.get('/global-search', {
      params: {
        q: query,
        limit: itemsPerPage,
        offset: 0,
        categories: activeCategories.value.join(',')
      }
    })

    if (response.data) {
      searchResults.value = response.data
      // Initialize category pages
      availableCategories.value.forEach(category => {
        if (!categoryPages.value[category]) {
          categoryPages.value[category] = 1
        }
      })
    }
  } catch (error) {
    console.error('[GlobalSearch] Search failed:', error)
    searchResults.value = null
  } finally {
    loading.value = false
  }
}

// Watchers
watch(() => route.query.q, (newQuery) => {
  if (newQuery && typeof newQuery === 'string') {
    searchQuery.value = newQuery
    performSearch(newQuery)
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  loadSearchHistory()

  // Get search query from route
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    performSearch(query)
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.global-search-results {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}

.search-header-card {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.05) 0%,
    rgba(var(--v-theme-secondary), 0.02) 100%
  );
}

.category-title {
  font-weight: 600;
  font-size: 1.125rem;
}

.result-item {
  transition: all 0.2s ease;
  cursor: pointer;
}

.result-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.filter-chip {
  transition: all 0.2s ease;
}

.filter-chip:hover {
  transform: translateY(-1px);
}

.no-results-card,
.category-card,
.show-more-card,
.history-card {
  border-radius: 16px;
  overflow: hidden;
}

.loading-container {
  text-align: center;
  padding: 64px 24px;
}

.suggestions {
  max-width: 400px;
  margin: 0 auto;
}

.suggestions ul {
  list-style: none;
  padding: 0;
}

.suggestions li {
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.suggestions li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Dark theme adjustments */
.v-theme--dark .search-header-card {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%
  );
}

.v-theme--dark .category-card,
.v-theme--dark .show-more-card,
.v-theme--dark .history-card {
  background: rgba(var(--v-theme-surface-variant), 0.8);
  border: 1px solid rgba(var(--v-border-color), 0.2);
}

/* Animations */
.category-card {
  animation: slideInUp 0.3s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive design */
@media (max-width: 960px) {
  .global-search-results {
    padding: 8px;
  }

  .search-header-card .v-card-text {
    padding: 16px;
  }

  .suggestions {
    max-width: 100%;
  }
}

@media (max-width: 600px) {
  .search-header-card .v-card-text {
    padding: 12px;
  }

  .category-title {
    font-size: 1rem;
  }

  .filter-chip {
    font-size: 0.75rem;
  }
}
</style>