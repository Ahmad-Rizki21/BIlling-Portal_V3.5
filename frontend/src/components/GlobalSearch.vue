<template>
  <v-menu
    v-model="menu"
    :close-on-content-click="false"
    location="bottom end"
    max-width="620"
    transition="scale-transition"
    persistent
  >
    <template v-slot:activator="{ props }">
      <v-text-field
        v-model="searchQuery"
        v-bind="props"
        placeholder="🔍 Cari pelanggan, pengguna, invoice, dll..."
        variant="solo"
        density="comfortable"
        prepend-inner-icon="mdi-magnify"
        clearable
        hide-details
        single-line
        class="global-search-field"
        :loading="loading"
        @click:clear="clearSearch"
        @keyup.enter="() => performSearch()"
        @update:model-value="handleSearchInput"
        ref="searchField"
        bg-color="white"
        rounded="pill"
        elevation="0"
      >
        <template v-slot:append-inner>
          <v-tooltip location="bottom" text="Ctrl+K">
            <template v-slot:activator="{ props: tooltipProps }">
              <v-chip
                v-bind="tooltipProps"
                size="x-small"
                variant="tonal"
                color="primary"
                class="search-kbd"
              >
                ⌘K
              </v-chip>
            </template>
          </v-tooltip>
        </template>
      </v-text-field>
    </template>

    <!-- Search Results Card -->
    <v-card class="global-search-card" elevation="12">
      <!-- Search Header -->
      <div class="search-header pa-4 pb-3">
        <div class="d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-2">
            <div class="search-icon-wrapper">
              <v-icon color="primary" size="18">mdi-magnify</v-icon>
            </div>
            <span class="text-subtitle-2 font-weight-medium text-grey-darken-2">
              {{ searchQuery ? `"${searchQuery}"` : 'Pencarian Global' }}
            </span>
          </div>
          <v-chip
            v-if="searchQuery && totalResults > 0"
            size="small"
            color="primary"
            variant="tonal"
            class="results-badge"
          >
            {{ totalResults }} hasil
          </v-chip>
        </div>
      </div>

      <v-divider v-if="searchQuery && !loading"></v-divider>

      <!-- Search Results -->
      <v-card-text v-if="searchQuery && !loading" class="search-results pa-0 pt-2">
        <template v-if="results.length > 0">
          <!-- Group results by category -->
          <template v-for="(category, categoryName, index) in groupedResults" :key="String(categoryName)">
            <div class="search-category">
              <!-- Category Header - CLEAN VERSION -->
              <div class="category-header px-4 py-3">
                <div class="d-flex align-center gap-2">
                  <v-icon :color="category.iconColor" size="18">{{ category.icon }}</v-icon>
                  <span class="text-caption font-weight-bold text-uppercase" :style="{ color: `rgb(var(--v-theme-${category.iconColor}))` }">
                    {{ getCategoryTitle(String(categoryName)) }}
                  </span>
                  <span class="text-caption text-grey-lighten-1">
                    ({{ category.items.length }})
                  </span>
                </div>
              </div>

              <!-- Results List -->
              <v-list density="compact" class="category-list py-0 px-2">
                <v-list-item
                  v-for="item in category.items.slice(0, maxItemsPerCategory)"
                  :key="item.id"
                  @click="handleItemClick(item, String(categoryName))"
                  class="search-result-item"
                  rounded="lg"
                  ripple
                  :value="item.id"
                >
                  <template v-slot:prepend>
                    <v-avatar :color="`${category.iconColor}`" size="36" variant="tonal">
                      <v-icon :color="category.iconColor" size="18">
                        {{ getItemIcon(item, String(categoryName)) }}
                      </v-icon>
                    </v-avatar>
                  </template>

                  <v-list-item-title class="text-body-2 font-weight-medium text-grey-darken-3">
                    {{ getItemTitle(item, String(categoryName)) }}
                  </v-list-item-title>
                  
                  <v-list-item-subtitle class="text-caption text-grey-darken-1">
                    {{ getItemSubtitle(item, String(categoryName)) }}
                  </v-list-item-subtitle>

                  <template v-slot:append>
                    <v-chip
                      v-if="getItemBadge(item, String(categoryName))"
                      size="x-small"
                      :color="getItemBadgeColor(item, String(categoryName))"
                      variant="flat"
                      class="item-badge"
                    >
                      {{ getItemBadge(item, String(categoryName)) }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </div>

            <!-- Divider between categories -->
            <v-divider 
              v-if="index < Object.keys(groupedResults).length - 1" 
              class="my-2"
            ></v-divider>
          </template>

          <!-- Show More Link -->
          <div v-if="results.length > displayLimit" class="show-more-section pa-4 text-center">
            <v-btn
              variant="tonal"
              color="primary"
              size="small"
              rounded="pill"
              @click="showAllResults"
              prepend-icon="mdi-arrow-right"
            >
              Lihat {{ results.length - displayLimit }} hasil lainnya
            </v-btn>
          </div>
        </template>

        <!-- No Results -->
        <div v-else class="no-results pa-10 text-center">
          <div class="empty-state-icon mb-4">
            <v-icon size="56" color="grey-lighten-2">mdi-file-search-outline</v-icon>
          </div>
          <div class="text-h6 font-weight-medium mb-2">Tidak ada hasil</div>
          <div class="text-body-2 text-grey">
            Coba kata kunci lain atau periksa ejaan
          </div>
        </div>
      </v-card-text>

      <!-- Loading State -->
      <v-card-text v-if="loading" class="pa-10 text-center">
        <v-progress-circular 
          indeterminate 
          color="primary" 
          size="40"
          width="3"
        ></v-progress-circular>
        <div class="mt-4 text-body-2 text-grey">
          Mencari...
        </div>
      </v-card-text>

      <!-- Search Tips (when no query) -->
      <v-card-text v-if="!searchQuery && !loading" class="search-tips pa-5">
        <div class="text-caption text-grey-darken-1 mb-3 font-weight-bold">
          💡 Tips pencarian cepat:
        </div>
        <div class="tips-grid">
          <div class="tip-card">
            <v-icon size="16" color="primary">mdi-account</v-icon>
            <span class="text-caption">Nama pelanggan</span>
          </div>
          <div class="tip-card">
            <v-icon size="16" color="success">mdi-receipt</v-icon>
            <span class="text-caption">Nomor invoice</span>
          </div>
          <div class="tip-card">
            <v-icon size="16" color="warning">mdi-wifi</v-icon>
            <span class="text-caption">Status langganan</span>
          </div>
          <div class="tip-card">
            <v-icon size="16" color="error">mdi-lifebuoy</v-icon>
            <span class="text-caption">Trouble tickets</span>
          </div>
        </div>
      </v-card-text>

      <!-- Footer Actions -->
      <div v-if="searchQuery && !loading && results.length > 0" class="search-footer pa-3">
        <v-btn
          variant="text"
          size="small"
          color="grey-darken-1"
          @click="clearSearch"
          block
          rounded="lg"
        >
          <v-icon start size="18">mdi-close-circle-outline</v-icon>
          Bersihkan pencarian
        </v-btn>
      </div>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
// ... (script tetap sama, tidak ada perubahan)
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import apiClient from '@/services/api'

interface SearchResult {
  id: string | number
  type: string
  title: string
  subtitle?: string
  url?: string
  data?: any
}

interface GroupedResults {
  [categoryName: string]: {
    icon: string
    iconColor: string
    items: SearchResult[]
  }
}

const props = defineProps<{
  placeholder?: string
}>()

const router = useRouter()
const theme = useTheme()
const menu = ref(false)
const searchQuery = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const searchField = ref<any>(null)

const displayLimit = 20
const maxItemsPerCategory = 3
const searchDebounceTime = 300
const minSearchLength = 2

let searchTimeout: NodeJS.Timeout | null = null

const totalResults = computed(() => results.value.length)

const groupedResults = computed<GroupedResults>(() => {
  const grouped: GroupedResults = {}

  results.value.forEach(result => {
    if (!grouped[result.type]) {
      grouped[result.type] = {
        icon: getCategoryIcon(result.type),
        iconColor: getCategoryColor(result.type),
        items: []
      }
    }
    grouped[result.type].items.push(result)
  })

  return grouped
})

const getCategoryIcon = (categoryName: string): string => {
  const icons: Record<string, string> = {
    pelanggan: 'mdi-account-group',
    langganan: 'mdi-wifi',
    invoices: 'mdi-receipt-text',
    tickets: 'mdi-lifebuoy',
    activity_logs: 'mdi-history',
    users: 'mdi-account-cog',
    mikrotik: 'mdi-server-network',
    inventory: 'mdi-archive'
  }
  return icons[categoryName] || 'mdi-file'
}

const getCategoryColor = (categoryName: string): string => {
  const colors: Record<string, string> = {
    pelanggan: 'primary',
    langganan: 'success',
    invoices: 'warning',
    tickets: 'error',
    activity_logs: 'info',
    users: 'purple',
    mikrotik: 'indigo',
    inventory: 'teal'
  }
  return colors[categoryName] || 'grey'
}

const getCategoryTitle = (categoryName: string): string => {
  const titles: Record<string, string> = {
    pelanggan: 'Pelanggan',
    langganan: 'Langganan',
    invoices: 'Invoice',
    tickets: 'Trouble Tickets',
    activity_logs: 'Activity Log',
    users: 'Pengguna',
    mikrotik: 'Mikrotik Server',
    inventory: 'Inventaris'
  }
  return titles[categoryName] || categoryName
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

const getItemTitle = (item: SearchResult, category: string): string => {
  return item.title
}

const getItemSubtitle = (item: SearchResult, category: string): string => {
  if (category === 'pelanggan') {
    return `${item.data?.email || ''} ${item.data?.no_telp ? `• ${item.data.no_telp}` : ''}`
  }
  if (category === 'langganan') {
    return `${item.data?.paket_layanan || 'Unknown Package'} • Status: ${item.data?.status || 'Unknown'}`
  }
  if (category === 'invoices') {
    return `Rp ${Number(item.data?.jumlah || 0).toLocaleString()} • ${item.data?.status || 'Unknown'}`
  }
  if (category === 'tickets') {
    return `Priority: ${item.data?.priority || 'Normal'} • Status: ${item.data?.status || 'Unknown'}`
  }
  return item.subtitle || ''
}

const getItemBadge = (item: SearchResult, category: string): string | null => {
  if (category === 'langganan') {
    return String(item.data?.status === 'suspended' ? 'Suspended' : item.data?.status || '')
  }
  if (category === 'invoices') {
    return String(item.data?.status === 'unpaid' ? 'Belum Bayar' : item.data?.status || '')
  }
  if (category === 'tickets') {
    return String(item.data?.status || '')
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

const performSearch = async (query: string = searchQuery.value) => {
  if (query.length < minSearchLength) {
    results.value = []
    return
  }

  loading.value = true

  try {
    const response = await apiClient.get('/global-search', {
      params: { q: query, limit: displayLimit }
    })

    if (response.data && response.data.results) {
      const allResults: any[] = []
      Object.keys(response.data.results).forEach((category: string) => {
        const categoryResults = response.data.results[category]
        if (Array.isArray(categoryResults)) {
          allResults.push(...categoryResults)
        }
      })

      results.value = allResults.map((item: any) => ({
        id: item.id,
        type: item.type,
        title: item.title,
        subtitle: item.subtitle,
        url: item.url,
        data: item.data
      }))
    } else {
      results.value = []
    }
  } catch (error) {
    console.error('[GlobalSearch] Search failed:', error)
    results.value = []
  } finally {
    loading.value = false
  }
}

const handleSearchInput = (value: string) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  searchTimeout = setTimeout(() => {
    if (value.length >= minSearchLength) {
      performSearch(value)
    } else {
      results.value = []
    }
  }, searchDebounceTime)
}

const handleItemClick = (item: SearchResult, category: string) => {
  menu.value = false

  if (item.url) {
    router.push(item.url)
  } else {
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

  clearSearch()
}

const clearSearch = () => {
  searchQuery.value = ''
  results.value = []
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
}

const showAllResults = () => {
  menu.value = false
  router.push({
    name: 'GlobalSearchResults',
    query: { q: searchQuery.value }
  })
}

const handleKeyboardShortcut = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    searchField.value?.focus()
    menu.value = true
  }

  if (event.key === 'Escape' && menu.value) {
    menu.value = false
  }
}

watch(menu, (newMenu) => {
  if (newMenu) {
    nextTick(() => {
      searchField.value?.focus()
    })
  } else {
    clearSearch()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeyboardShortcut)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboardShortcut)
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<style scoped>
/* Main Search Field */
.global-search-field {
  max-width: 420px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.global-search-field :deep(.v-field) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.global-search-field:hover :deep(.v-field) {
  border-color: rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.global-search-field :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.2);
}

/* Keyboard Shortcut Badge */
.search-kbd {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 2px 6px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.global-search-field:hover .search-kbd {
  opacity: 1;
}

/* Search Results Card */
.global-search-card {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: white;
}

/* Search Header */
.search-header {
  background: white;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.search-icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.results-badge {
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Category Section - CLEAN! NO GREY BACKGROUND! */
.search-category {
  transition: all 0.2s ease;
}

.category-header {
  background: transparent !important;
  /* Removed all grey backgrounds */
}

/* Search Result Items */
.search-result-item {
  min-height: 64px !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  margin: 2px 0;
  border: 1px solid transparent;
}

.search-result-item:hover {
  background: rgba(var(--v-theme-primary), 0.04) !important;
  border-color: rgba(var(--v-theme-primary), 0.1);
  transform: translateX(4px);
}

.search-result-item :deep(.v-list-item__prepend) {
  margin-right: 14px;
}

.item-badge {
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

/* No Results */
.no-results {
  background: white;
}

.empty-state-icon {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

/* Search Tips */
.search-tips {
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.tip-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: white;
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  cursor: default;
}

.tip-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: rgba(var(--v-theme-primary), 0.02);
}

/* Footer */
.search-footer {
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* Show More Section */
.show-more-section {
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* Dark Theme */
.v-theme--dark .global-search-field :deep(.v-field) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .global-search-card {
  background: #1e1e1e;
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .search-header,
.v-theme--dark .search-tips,
.v-theme--dark .search-footer,
.v-theme--dark .show-more-section,
.v-theme--dark .no-results {
  background: #1e1e1e;
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .tip-card {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .tip-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .search-icon-wrapper {
  background: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .search-result-item:hover {
  background: rgba(var(--v-theme-primary), 0.1) !important;
}

/* Animations */
.global-search-card {
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.search-result-item {
  animation: fadeInUp 0.3s ease-out backwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger animation for list items */
.search-result-item:nth-child(1) { animation-delay: 0.05s; }
.search-result-item:nth-child(2) { animation-delay: 0.1s; }
.search-result-item:nth-child(3) { animation-delay: 0.15s; }

/* Responsive */
@media (max-width: 600px) {
  .global-search-field {
    max-width: 100%;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
}

/* Loading Animation */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.v-progress-circular {
  animation: pulse 2s ease-in-out infinite;
}

/* Smooth scrolling */
.search-results {
  max-height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
}

.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>