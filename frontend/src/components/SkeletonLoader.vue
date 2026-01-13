<template>
  <!-- Table Skeleton -->
  <div v-if="type === 'table'" class="skeleton-table">
    <div class="skeleton-header">
      <v-skeleton-loader type="heading" width="200" class="mb-2"></v-skeleton-loader>
      <v-skeleton-loader type="text" width="300" height="40"></v-skeleton-loader>
    </div>
    <v-skeleton-loader
      v-for="n in rows"
      :key="n"
      type="table-row"
      class="skeleton-row"
    ></v-skeleton-loader>
  </div>

  <!-- Card Grid Skeleton -->
  <div v-else-if="type === 'card-grid'" class="skeleton-card-grid">
    <v-skeleton-loader
      v-for="n in cards"
      :key="n"
      type="card-avatar, article"
      class="skeleton-card"
    ></v-skeleton-loader>
  </div>

  <!-- List Skeleton -->
  <div v-else-if="type === 'list'" class="skeleton-list">
    <v-skeleton-loader
      v-for="n in items"
      :key="n"
      type="list-item-avatar-two-line"
      class="skeleton-list-item"
    ></v-skeleton-loader>
  </div>

  <!-- Chart Skeleton -->
  <div v-else-if="type === 'chart'" class="skeleton-chart">
    <div class="skeleton-chart-wrapper">
      <div class="skeleton-chart-header">
        <div class="skeleton-header-left">
          <v-skeleton-loader type="avatar" width="24" height="24" class="skeleton-icon"></v-skeleton-loader>
          <v-skeleton-loader type="text" width="180" class="skeleton-title"></v-skeleton-loader>
        </div>
        <v-skeleton-loader type="avatar" width="32" height="32" class="skeleton-action"></v-skeleton-loader>
      </div>
      <v-skeleton-loader type="image" height="250" class="skeleton-chart-body"></v-skeleton-loader>
    </div>
  </div>

  <!-- Form Skeleton -->
  <div v-else-if="type === 'form'" class="skeleton-form">
    <div class="skeleton-form-header">
      <v-skeleton-loader type="heading" width="300" class="mb-2"></v-skeleton-loader>
      <v-skeleton-loader type="text" width="400"></v-skeleton-loader>
    </div>
    <div class="skeleton-form-body">
      <v-skeleton-loader type="text" height="40" class="mb-4"></v-skeleton-loader>
      <v-skeleton-loader type="text" height="40" class="mb-4"></v-skeleton-loader>
      <v-skeleton-loader type="text" height="40" class="mb-4"></v-skeleton-loader>
      <v-skeleton-loader type="text" height="100" class="mb-4"></v-skeleton-loader>
      <v-skeleton-loader type="button" width="120" class="mt-4"></v-skeleton-loader>
    </div>
  </div>

  <!-- Dashboard Skeleton -->
  <div v-else-if="type === 'dashboard'" class="skeleton-dashboard">
    <!-- Stats Cards -->
    <div class="skeleton-stats-grid">
      <v-skeleton-loader
        v-for="n in 4"
        :key="`stat-${n}`"
        type="list-item-avatar-two-line"
        class="skeleton-stat-card"
      ></v-skeleton-loader>
    </div>

    <!-- Charts Row 1 -->
    <div class="skeleton-charts-row">
      <v-skeleton-loader
        type="card-heading, image"
        class="skeleton-chart-card"
      ></v-skeleton-loader>
      <v-skeleton-loader
        type="card-heading, image"
        class="skeleton-chart-card"
      ></v-skeleton-loader>
    </div>

    <!-- Charts Row 2 -->
    <div class="skeleton-charts-row">
      <v-skeleton-loader
        type="card-heading, image"
        class="skeleton-chart-card"
      ></v-skeleton-loader>
      <v-skeleton-loader
        type="card-heading, image"
        class="skeleton-chart-card"
      ></v-skeleton-loader>
      <v-skeleton-loader
        type="card-heading, image"
        class="skeleton-chart-card"
      ></v-skeleton-loader>
    </div>
  </div>

  <!-- Default Skeleton -->
  <div v-else class="skeleton-default">
    <v-skeleton-loader
      v-for="n in (items || 3)"
      :key="n"
      type="article"
      class="skeleton-item"
    ></v-skeleton-loader>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'table' | 'card-grid' | 'list' | 'chart' | 'form' | 'dashboard' | 'default'
  rows?: number
  cards?: number
  items?: number
}

withDefaults(defineProps<Props>(), {
  type: 'default',
  rows: 5,
  cards: 4,
  items: 3
})
</script>

<style scoped>
.skeleton-table {
  width: 100%;
}

.skeleton-header {
  margin-bottom: 1rem;
}

.skeleton-row {
  margin-bottom: 0.5rem;
}

.skeleton-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  width: 100%;
}

.skeleton-card {
  width: 100%;
}

.skeleton-list {
  width: 100%;
}

.skeleton-list-item {
  margin-bottom: 0.5rem;
}

.skeleton-chart {
  width: 100%;
  height: 320px;
}

.skeleton-chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.skeleton-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.skeleton-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.skeleton-icon {
  flex-shrink: 0;
}

.skeleton-title {
  flex-shrink: 0;
}

.skeleton-action {
  flex-shrink: 0;
}

.skeleton-chart-body {
  width: 100%;
  flex: 1;
  min-height: 250px;
  border-radius: 8px;
}

.skeleton-form {
  width: 100%;
  max-width: 600px;
}

.skeleton-form-header {
  margin-bottom: 2rem;
}

.skeleton-form-body {
  width: 100%;
}

.skeleton-dashboard {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.skeleton-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.skeleton-charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.5rem;
}

.skeleton-chart-card {
  width: 100%;
  height: 320px;
}

.skeleton-stat-card {
  width: 100%;
}

.skeleton-default {
  width: 100%;
}

.skeleton-item {
  margin-bottom: 1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .skeleton-card-grid {
    grid-template-columns: 1fr;
  }

  .skeleton-charts-row {
    grid-template-columns: 1fr;
  }

  .skeleton-stats-grid {
    grid-template-columns: 1fr;
  }

  .skeleton-chart {
    height: 280px;
  }

  .skeleton-chart-card {
    height: 280px;
  }
}

/* Animation for skeleton loading */
@keyframes skeleton-pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* Shimmer effect for skeleton */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton-table,
.skeleton-card-grid,
.skeleton-list,
.skeleton-chart,
.skeleton-form,
.skeleton-dashboard,
.skeleton-default {
  animation: skeleton-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Apply shimmer effect to skeleton loaders */
.skeleton-table :deep(.v-skeleton-loader__bone),
.skeleton-card-grid :deep(.v-skeleton-loader__bone),
.skeleton-list :deep(.v-skeleton-loader__bone),
.skeleton-chart :deep(.v-skeleton-loader__bone),
.skeleton-form :deep(.v-skeleton-loader__bone),
.skeleton-dashboard :deep(.v-skeleton-loader__bone),
.skeleton-default :deep(.v-skeleton-loader__bone) {
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-surface-variant), 0.3) 0%,
    rgba(var(--v-theme-surface-variant), 0.5) 50%,
    rgba(var(--v-theme-surface-variant), 0.3) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

/* Smooth transitions */
.skeleton-chart-wrapper,
.skeleton-chart-header,
.skeleton-chart-body {
  transition: all 0.3s ease;
}
</style>