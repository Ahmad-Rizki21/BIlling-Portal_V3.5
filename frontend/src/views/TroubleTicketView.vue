<template>
  <div class="trouble-ticket-container">
    <!-- Header Section with Modern Design -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <div class="d-flex align-center mb-2">
            <v-avatar 
              color="primary" 
              size="56" 
              class="me-4 header-avatar"
              elevation="4"
            >
              <v-icon size="32">mdi-ticket-confirmation-outline</v-icon>
            </v-avatar>
            <div>
              <h1 class="page-title">Trouble Ticket System</h1>
              <p class="page-subtitle">
                <v-icon size="16" class="me-1">mdi-information-outline</v-icon>
                Kelola laporan masalah dan tracking downtime pelanggan
              </p>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <v-btn
            color="primary"
            prepend-icon="mdi-plus-circle"
            @click="openCreateDialog"
            :disabled="loading"
            class="me-2 create-btn"
            variant="flat"
            size="large"
            elevation="2"
          >
            Buat Ticket Baru
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-refresh"
            @click="refreshData"
            :loading="loading"
            size="large"
            class="refresh-btn"
          >
            Refresh
          </v-btn>
        </div>
      </div>

      <!-- Enhanced Statistics Cards with Gradient -->
      <div class="statistics-grid">
        <v-card class="stat-card stat-total" elevation="0">
          <div class="stat-gradient"></div>
          <v-card-text class="stat-content">
            <div class="stat-icon-wrapper total">
              <v-icon size="32">mdi-ticket-outline</v-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics?.total_tickets || 0 }}</div>
              <div class="stat-label">Total Tickets</div>
              <div class="stat-trend">
                <v-icon size="14" color="success">mdi-trending-up</v-icon>
                <span class="trend-text">All time</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="stat-card stat-open" elevation="0">
          <div class="stat-gradient"></div>
          <v-card-text class="stat-content">
            <div class="stat-icon-wrapper open">
              <v-icon size="32">mdi-clock-outline</v-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics?.open_tickets || 0 }}</div>
              <div class="stat-label">Open</div>
              <div class="stat-trend">
                <v-chip size="x-small" color="warning" variant="flat">Active</v-chip>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="stat-card stat-progress" elevation="0">
          <div class="stat-gradient"></div>
          <v-card-text class="stat-content">
            <div class="stat-icon-wrapper progress">
              <v-icon size="32">mdi-progress-clock</v-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics?.in_progress_tickets || 0 }}</div>
              <div class="stat-label">In Progress</div>
              <div class="stat-trend">
                <v-chip size="x-small" color="info" variant="flat">Working</v-chip>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="stat-card stat-high" elevation="0">
          <div class="stat-gradient"></div>
          <v-card-text class="stat-content">
            <div class="stat-icon-wrapper high">
              <v-icon size="32">mdi-alert-circle-outline</v-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics?.high_priority_tickets || 0 }}</div>
              <div class="stat-label">High Priority</div>
              <div class="stat-trend">
                <v-chip size="x-small" color="error" variant="flat">Urgent</v-chip>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="stat-card stat-critical" elevation="0">
          <div class="stat-gradient"></div>
          <v-card-text class="stat-content">
            <div class="stat-icon-wrapper critical">
              <v-icon size="32">mdi-fire-alert</v-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics?.critical_priority_tickets || 0 }}</div>
              <div class="stat-label">Critical</div>
              <div class="stat-trend">
                <v-chip size="x-small" color="red-darken-2" variant="flat">
                  <v-icon start size="x-small">mdi-fire</v-icon>
                  Emergency
                </v-chip>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </div>
    </div>

    <!-- Enhanced Filters Section -->
    <!-- Enhanced Filters Section -->
<v-card class="filters-card" elevation="0">
  <v-card-text class="filters-content">
    <!-- Header Section -->
    <div class="filters-header">
      <div class="filters-header-left">
        <div class="filters-icon-wrapper">
          <v-icon size="24" color="white">mdi-filter-variant</v-icon>
        </div>
        <div class="filters-header-text">
          <h3 class="filters-title">Advanced Filters</h3>
          <p class="filters-subtitle">
            <v-icon size="14" class="me-1">mdi-tune</v-icon>
            Refine your ticket search with precision
          </p>
        </div>
      </div>
      <div class="filters-header-right">
        <v-chip
          v-if="hasActiveFilters"
          color="primary"
          variant="flat"
          size="small"
          class="me-2 active-count-chip"
        >
          <v-icon start size="16">mdi-filter-check</v-icon>
          {{ activeFilterCount }} Active
        </v-chip>
        <v-btn
          variant="tonal"
          prepend-icon="mdi-filter-remove-outline"
          @click="clearFilters"
          :disabled="!hasActiveFilters"
          size="small"
          color="error"
          class="clear-btn"
        >
          Clear All
        </v-btn>
      </div>
    </div>

    <v-divider class="my-5"></v-divider>

    <!-- Filters Grid -->
    <div class="filters-grid-enhanced">
      <!-- Status Filter -->
      <div class="filter-item">
        <div class="filter-label">
          <v-icon size="18" color="primary" class="me-2">mdi-format-list-bulleted</v-icon>
          <span>Status</span>
          <v-chip
            v-if="filters.status"
            size="x-small"
            color="primary"
            variant="flat"
            class="ms-2"
          >
            1
          </v-chip>
        </div>
        <v-select
          v-model="filters.status"
          :items="statusOptions"
          clearable
          @update:modelValue="applyFilters"
          hide-details
          variant="outlined"
          density="comfortable"
          placeholder="Select status"
          class="filter-select-enhanced"
        >
          <template v-slot:prepend-inner>
            <v-icon color="primary" size="20">mdi-circle-outline</v-icon>
          </template>
          <template v-slot:item="{ props, item }">
            <v-list-item v-bind="props" class="filter-list-item">
              <template v-slot:prepend>
                <v-icon :color="getStatusColor(item.value)" size="20">
                  {{ getStatusIcon(item.value) }}
                </v-icon>
              </template>
            </v-list-item>
          </template>
          <template v-slot:selection="{ item }">
            <div class="d-flex align-center">
              <v-icon :color="getStatusColor(item.value)" size="18" class="me-2">
                {{ getStatusIcon(item.value) }}
              </v-icon>
              <span>{{ item.title }}</span>
            </div>
          </template>
        </v-select>
      </div>

      <!-- Priority Filter -->
      <div class="filter-item">
        <div class="filter-label">
          <v-icon size="18" color="warning" class="me-2">mdi-flag-outline</v-icon>
          <span>Priority</span>
          <v-chip
            v-if="filters.priority"
            size="x-small"
            color="warning"
            variant="flat"
            class="ms-2"
          >
            1
          </v-chip>
        </div>
        <v-select
          v-model="filters.priority"
          :items="priorityOptions"
          clearable
          @update:modelValue="applyFilters"
          hide-details
          variant="outlined"
          density="comfortable"
          placeholder="Select priority"
          class="filter-select-enhanced"
        >
          <template v-slot:prepend-inner>
            <v-icon color="warning" size="20">mdi-flag</v-icon>
          </template>
          <template v-slot:item="{ props, item }">
            <v-list-item v-bind="props" class="filter-list-item">
              <template v-slot:prepend>
                <v-icon :color="getPriorityColor(item.value)" size="20">
                  {{ getPriorityIcon(item.value) }}
                </v-icon>
              </template>
            </v-list-item>
          </template>
          <template v-slot:selection="{ item }">
            <div class="d-flex align-center">
              <v-icon :color="getPriorityColor(item.value)" size="18" class="me-2">
                {{ getPriorityIcon(item.value) }}
              </v-icon>
              <span>{{ item.title }}</span>
            </div>
          </template>
        </v-select>
      </div>

      <!-- Category Filter -->
      <div class="filter-item">
        <div class="filter-label">
          <v-icon size="18" color="info" class="me-2">mdi-tag-outline</v-icon>
          <span>Category</span>
          <v-chip
            v-if="filters.category"
            size="x-small"
            color="info"
            variant="flat"
            class="ms-2"
          >
            1
          </v-chip>
        </div>
        <v-select
          v-model="filters.category"
          :items="categoryOptions"
          clearable
          @update:modelValue="applyFilters"
          hide-details
          variant="outlined"
          density="comfortable"
          placeholder="Select category"
          class="filter-select-enhanced"
          :menu-props="{ maxHeight: 400 }"
        >
          <template v-slot:prepend-inner>
            <v-icon color="info" size="20">mdi-tag</v-icon>
          </template>
          
          <!-- PERBAIKAN: Gunakan template yang konsisten -->
          <template v-slot:item="{ item, props }">
            <v-list-item
              v-bind="props"
              :title="item.title"
              rounded="lg"
              class="filter-list-item"
            >
              <template v-slot:prepend>
                <v-icon color="info" size="20" class="me-2">mdi-tag-outline</v-icon>
              </template>
            </v-list-item>
          </template>
        </v-select>
      </div>

      <!-- Brand Filter -->
      <div class="filter-item">
        <div class="filter-label">
          <v-icon size="18" color="success" class="me-2">mdi-domain</v-icon>
          <span>Brand</span>
          <v-chip
            v-if="filters.brand"
            size="x-small"
            color="success"
            variant="flat"
            class="ms-2"
          >
            1
          </v-chip>
        </div>
        <v-select
          v-model="filters.brand"
          :items="brandOptions"
          clearable
          @update:modelValue="applyFilters"
          hide-details
          variant="outlined"
          density="comfortable"
          placeholder="Select brand"
          class="filter-select-enhanced"
        >
          <template v-slot:prepend-inner>
            <v-icon color="success" size="20">mdi-office-building</v-icon>
          </template>
          <template v-slot:item="{ props, item }">
            <v-list-item v-bind="props" class="filter-list-item">
              <template v-slot:prepend>
                <v-avatar size="32" color="success" variant="tonal">
                  <span class="text-caption font-weight-bold">
                    {{ item.title.charAt(0) }}
                  </span>
                </v-avatar>
              </template>
            </v-list-item>
          </template>
          <template v-slot:selection="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="24" color="success" variant="tonal" class="me-2">
                <span class="text-caption font-weight-bold">
                  {{ item.title.charAt(0) }}
                </span>
              </v-avatar>
              <span>{{ item.title }}</span>
            </div>
          </template>
        </v-select>
      </div>
    </div>

    <!-- Search Field -->
    <div class="search-field-enhanced mt-5">
      <div class="filter-label mb-3">
        <v-icon size="18" color="secondary" class="me-2">mdi-magnify</v-icon>
        <span>Search Tickets</span>
        <v-chip
          v-if="filters.search"
          size="x-small"
          color="secondary"
          variant="flat"
          class="ms-2"
        >
          Active
        </v-chip>
      </div>
      <v-text-field
        v-model="filters.search"
        placeholder="Search by ticket number, title, customer name..."
        prepend-inner-icon="mdi-magnify"
        clearable
        @update:modelValue="debouncedSearch"
        hide-details
        variant="outlined"
        density="comfortable"
        class="search-input-enhanced"
      >
        <template v-slot:prepend-inner>
          <v-icon color="secondary" size="22">mdi-magnify</v-icon>
        </template>
        <template v-slot:append-inner>
          <v-fade-transition>
            <v-icon v-if="filters.search" color="success" size="20">
              mdi-check-circle
            </v-icon>
          </v-fade-transition>
        </template>
      </v-text-field>
    </div>

    <!-- Show/Hide Closed Tickets -->
    <div class="closed-tickets-filter mt-4">
      <v-card
        variant="outlined"
        class="pa-3"
        :color="filters.showClosed ? 'success' : 'grey-lighten-2'"
      >
        <div class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-icon
              :color="filters.showClosed ? 'success' : 'grey'"
              size="20"
              class="me-3"
            >
              {{ filters.showClosed ? 'mdi-eye-check' : 'mdi-eye-off' }}
            </v-icon>
            <span class="text-body-2 font-weight-medium">
              {{ filters.showClosed ? 'Showing Closed Tickets' : 'Hiding Closed Tickets' }}
            </span>
          </div>
          <v-switch
            v-model="filters.showClosed"
            color="success"
            hide-details
            density="compact"
            inset
            @update:modelValue="applyFilters"
            class="mt-0"
          >
            <template v-slot:label>
              <span class="text-caption">Show Closed</span>
            </template>
          </v-switch>
        </div>
        <v-expand-transition>
          <div v-if="filters.showClosed" class="mt-2">
            <v-chip
              size="x-small"
              color="success"
              variant="tonal"
              prepend-icon="mdi-information"
            >
              Closed tickets will be displayed in the list
            </v-chip>
          </div>
        </v-expand-transition>
      </v-card>
    </div>

    <!-- Active Filters Display -->
  

    <!-- Quick Filters (Optional) -->
    
  </v-card-text>
</v-card>

    <!-- Enhanced Data Table -->
    <v-card class="table-card" elevation="0">
      <div class="table-header">
        <div class="table-title">
          <v-icon class="me-2" color="primary">mdi-table</v-icon>
          <span>Ticket List</span>
          <v-chip size="small" color="primary" variant="tonal" class="ms-3">
            {{ totalItems }} Total
          </v-chip>
        </div>
      </div>

      <v-divider></v-divider>

      <v-data-table-server
        v-model:items-per-page="itemsPerPage"
        :headers="headers"
        :items="tickets"
        :loading="loading"
        :items-length="totalItems"
        :page="currentPage"
        @update:page="handlePageChange"
        @update:items-per-page="handleItemsPerPageChange"
        class="modern-data-table"
        :loading-text="'Loading tickets...'"
        :no-data-text="'No tickets found'"
        hover
      >
        <!-- Loading slot -->
        <template v-slot:loading>
          <div class="loading-container">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
              width="6"
            ></v-progress-circular>
            <p class="loading-text mt-4">Loading tickets...</p>
            <p class="loading-subtext">Please wait a moment</p>
          </div>
        </template>

        <!-- Ticket Number -->
        <template v-slot:item.ticket_number="{ item }">
          <div class="ticket-number">
            <v-chip
              color="primary"
              variant="tonal"
              size="small"
              prepend-icon="mdi-ticket"
              class="font-weight-bold"
            >
              {{ item.ticket_number }}
            </v-chip>
          </div>
        </template>

        <!-- Title -->
        <template v-slot:item.title="{ item }">
          <div class="ticket-title">
            <div class="title-text">
              <v-icon size="16" class="me-1" color="primary">mdi-text</v-icon>
              {{ item.title }}
            </div>
            <div class="title-description" v-if="item.description">
              {{ item.description.substring(0, 60) }}{{ item.description.length > 60 ? '...' : '' }}
            </div>
          </div>
        </template>

        <!-- Customer Info -->
        <template v-slot:item.pelanggan="{ item }">
          <div v-if="item.pelanggan" class="customer-info">
            <div class="customer-header">
              <v-avatar size="36" color="primary" class="me-2" variant="tonal">
                <span class="text-subtitle-2 font-weight-bold">
                  {{ item.pelanggan.nama.charAt(0).toUpperCase() }}
                </span>
              </v-avatar>
              <div>
                <div class="customer-name">
                  <v-icon size="14" class="me-1">mdi-account</v-icon>
                  {{ item.pelanggan.nama }}
                </div>
                <div class="customer-address">
                  <v-icon size="12" class="me-1">mdi-map-marker</v-icon>
                  {{ item.pelanggan.alamat }}
                </div>
              </div>
            </div>
            
            <div class="customer-details mt-2">
              <v-chip
                v-if="item.data_teknis?.ip_pelanggan"
                size="x-small"
                variant="outlined"
                color="info"
                prepend-icon="mdi-ip-network"
                class="me-1 mb-1"
              >
                {{ item.data_teknis.ip_pelanggan }}
              </v-chip>
              <v-chip
                v-if="item.data_teknis?.id_pelanggan && !isIpAddress(item.data_teknis.id_pelanggan)"
                size="x-small"
                variant="outlined"
                color="secondary"
                prepend-icon="mdi-identifier"
                class="me-1 mb-1"
              >
                {{ item.data_teknis.id_pelanggan }}
              </v-chip>
            </div>

            <v-chip
              v-if="item.pelanggan.harga_layanan?.brand"
              size="small"
              color="success"
              variant="tonal"
              prepend-icon="mdi-domain"
              class="mt-2"
            >
              {{ item.pelanggan.harga_layanan.brand }}
            </v-chip>
          </div>
          <div v-else class="no-customer">
            <v-chip
              size="small"
              variant="outlined"
              color="grey"
              prepend-icon="mdi-account-off"
            >
              No customer data
            </v-chip>
          </div>
        </template>

        <!-- Status -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="flat"
            class="status-chip font-weight-bold"
          >
            <v-icon start size="16">{{ getStatusIcon(item.status) }}</v-icon>
            {{ formatStatus(item.status) }}
          </v-chip>
        </template>

        <!-- Priority -->
        <template v-slot:item.priority="{ item }">
          <v-chip
            :color="getPriorityColor(item.priority)"
            size="small"
            variant="flat"
            class="priority-chip font-weight-bold"
          >
            <v-icon start size="16">{{ getPriorityIcon(item.priority) }}</v-icon>
            {{ formatPriority(item.priority) }}
          </v-chip>
        </template>

        <!-- Category -->
        <template v-slot:item.category="{ item }">
          <v-chip
            size="small"
            variant="tonal"
            color="info"
            prepend-icon="mdi-tag-outline"
            class="font-weight-medium"
          >
            {{ formatCategory(item.category) }}
          </v-chip>
        </template>

        <!-- Assigned To -->
        <template v-slot:item.assigned_user="{ item }">
          <div v-if="item.assigned_user" class="assigned-user">
            <v-avatar size="32" color="success" class="me-2" variant="tonal">
              <span class="text-caption font-weight-bold">
                {{ item.assigned_user.name.charAt(0).toUpperCase() }}
              </span>
            </v-avatar>
            <span class="user-name">{{ item.assigned_user.name }}</span>
          </div>
          <div v-else class="unassigned">
            <v-chip
              size="small"
              variant="outlined"
              color="grey"
              prepend-icon="mdi-account-question"
            >
              Unassigned
            </v-chip>
          </div>
        </template>

        <!-- Downtime Timer -->
        <template v-slot:item.downtime="{ item }">
          <div class="downtime-container">
            <div v-if="item.status !== 'resolved' && item.status !== 'closed' && item.status !== 'cancelled'">
              <v-chip
                :color="getDowntimeColor(item.created_at)"
                size="small"
                variant="flat"
                class="downtime-timer font-weight-bold"
              >
                <v-icon start size="16">mdi-clock-fast</v-icon>
                {{ calculateTicketDowntime(item.created_at) }}
              </v-chip>
            </div>
            <div v-else-if="item.total_downtime_minutes && item.total_downtime_minutes > 0">
              <v-chip
                :color="getDowntimeColorFromMinutes(item.total_downtime_minutes)"
                size="small"
                variant="flat"
                class="downtime-resolved font-weight-bold"
              >
                <v-icon start size="16">mdi-check-circle</v-icon>
                {{ formatDowntime(item.total_downtime_minutes) }}
              </v-chip>
            </div>
            <div v-else class="no-downtime">
              <v-chip
                size="small"
                variant="outlined"
                color="success"
                prepend-icon="mdi-check"
              >
                No downtime
              </v-chip>
            </div>
          </div>
        </template>

        <!-- Created At -->
        <template v-slot:item.created_at="{ item }">
          <div class="created-date">
            <div class="date-main">
              <v-icon size="14" class="me-1">mdi-calendar</v-icon>
              {{ formatDate(item.created_at) }}
            </div>
            <div class="date-time">
              <v-icon size="12" class="me-1">mdi-clock-outline</v-icon>
              {{ formatTime(item.created_at) }}
            </div>
          </div>
        </template>

        <!-- Actions -->
        <template v-slot:item.actions="{ item }">
          <div class="actions-container">
            <v-tooltip text="View Details" location="top">
              <template v-slot:activator="{ props }">
                <v-btn
                  icon="mdi-eye"
                  variant="tonal"
                  size="small"
                  @click="viewTicket(item)"
                  color="primary"
                  v-bind="props"
                  class="action-btn"
                ></v-btn>
              </template>
            </v-tooltip>

            <v-tooltip text="Manage Actions" location="top">
              <template v-slot:activator="{ props }">
                <v-btn
                  icon="mdi-cog-transfer"
                  variant="tonal"
                  size="small"
                  @click="viewTicketAction(item)"
                  color="success"
                  v-bind="props"
                  class="action-btn"
                ></v-btn>
              </template>
            </v-tooltip>

            <v-tooltip text="Delete Ticket" location="top">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-if="canDeleteTicket(item)"
                  icon="mdi-delete"
                  variant="tonal"
                  size="small"
                  @click="confirmDeleteTicket(item)"
                  color="error"
                  v-bind="props"
                  class="action-btn"
                ></v-btn>
              </template>
            </v-tooltip>
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Dialogs -->
    <TroubleTicketForm
      v-model="showFormDialog"
      :ticket="selectedTicket"
      @saved="handleTicketSaved"
      @cancelled="closeFormDialog"
    />

    <!-- Enhanced Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="500" transition="dialog-bottom-transition">
      <v-card class="rounded-lg" elevation="8">
        <v-card-title class="pa-6 bg-error-gradient">
          <div class="d-flex align-center">
            <v-avatar color="error" size="48" class="me-3">
              <v-icon size="28">mdi-delete-alert</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">Konfirmasi Hapus Ticket</div>
              <div class="text-caption text-medium-emphasis">This action cannot be undone</div>
            </div>
          </div>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="pa-6">
          <v-alert
            type="warning"
            variant="tonal"
            border="start"
            class="mb-4"
          >
            <div class="text-subtitle-2 font-weight-bold mb-2">
              Apakah Anda yakin ingin menghapus ticket ini?
            </div>
            <div class="text-caption">
              Tindakan ini tidak dapat dibatalkan dan semua data terkait akan dihapus permanen.
            </div>
          </v-alert>

          <div v-if="ticketToDelete" class="ticket-delete-info">
            <v-card variant="outlined" class="pa-4">
              <div class="info-row">
                <span class="info-label">Ticket Number:</span>
                <v-chip size="small" color="primary" variant="tonal">
                  {{ ticketToDelete.ticket_number }}
                </v-chip>
              </div>
              <v-divider class="my-3"></v-divider>
              <div class="info-row">
                <span class="info-label">Judul:</span>
                <span class="info-value">{{ ticketToDelete.title }}</span>
              </div>
              <v-divider class="my-3"></v-divider>
              <div class="info-row">
                <span class="info-label">Status:</span>
                <v-chip 
                  size="small" 
                  :color="getStatusColor(ticketToDelete.status)" 
                  variant="flat"
                >
                  {{ formatStatus(ticketToDelete.status) }}
                </v-chip>
              </div>
            </v-card>
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-6 bg-surface">
          <v-spacer></v-spacer>
          <v-btn
            variant="outlined"
            @click="closeDeleteDialog"
            :disabled="deleting"
            size="large"
            class="px-6"
          >
            <v-icon start>mdi-close</v-icon>
            Batal
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="deleteTicket"
            :loading="deleting"
            size="large"
            class="px-6"
            elevation="2"
          >
            <v-icon start>mdi-delete</v-icon>
            Hapus Ticket
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
// Script tetap sama seperti sebelumnya - TIDAK ADA PERUBAHAN LOGIKA BISNIS
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { debounce } from 'lodash'
import { useRouter } from 'vue-router'
import apiClient from '@/services/api'
import TroubleTicketForm from '@/components/trouble-ticket/TroubleTicketForm.vue'

const router = useRouter()

// Types
interface TroubleTicket {
  id: number
  ticket_number: string
  title: string
  description: string
  status: string
  priority: string
  category: string
  pelanggan?: {
    id: number
    nama: string
    alamat: string
    harga_layanan?: {
      brand: string
    }
  }
  data_teknis?: {
    id_pelanggan: string
    ip_pelanggan?: string
  }
  assigned_user?: {
    id: number
    name: string
  }
  total_downtime_minutes?: number
  created_at: string
  updated_at: string
}

interface Statistics {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  resolved_tickets: number
  closed_tickets: number
  high_priority_tickets: number
  critical_priority_tickets: number
  avg_resolution_time_hours: number | null
  tickets_this_month: number
  unresolved_over_24h: number
}

// State
const loading = ref(false)
const tickets = ref<TroubleTicket[]>([])
const statistics = ref<Statistics | null>(null)
const totalItems = ref(0)
const currentPage = ref(1)
const itemsPerPage = ref(15)
const refreshInterval = ref<NodeJS.Timeout | null>(null)
const currentTime = ref(new Date())

// Dialog states
const showFormDialog = ref(false)
const showDeleteDialog = ref(false)
const deleting = ref(false)

// Selected items
const selectedTicket = ref<TroubleTicket | null>(null)
const ticketToDelete = ref<TroubleTicket | null>(null)

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.status) count++
  if (filters.priority) count++
  if (filters.category) count++
  if (filters.brand) count++
  if (filters.search) count++
  if (filters.showClosed) count++ // Count showClosed as active filter when true
  return count
})


// Filters
const filters = reactive({
  status: '',
  priority: '',
  category: '',
  brand: '',
  search: '',
  showClosed: false
})

// Options
const statusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending', value: 'pending' },
  { title: 'Closed', value: 'closed' },
]

const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Critical', value: 'critical' }
]

const categoryOptions = [
  { title: 'No Connection', value: 'no_connection' },
  { title: 'Slow Connection', value: 'slow_connection' },
  { title: 'Intermittent', value: 'intermittent' },
  { title: 'Hardware Issue', value: 'hardware_issue' },
  { title: 'Cable Issue', value: 'cable_issue' },
  { title: 'ONU Issue', value: 'onu_issue' },
  { title: 'OLT Issue', value: 'olt_issue' },
  { title: 'Mikrotik Issue', value: 'mikrotik_issue' },
  { title: 'Other', value: 'other' }
]

const brandOptions = [
  { title: 'JAKINET', value: 'JAKINET' },
  { title: 'JELANTIK', value: 'JELANTIK' },
  { title: 'JELANTIK NAGRAK', value: 'JELANTIK NAGRAK' }
]

// Table headers
const headers = [
  { title: 'Ticket #', key: 'ticket_number', sortable: false },
  { title: 'Title', key: 'title', sortable: false },
  { title: 'Customer', key: 'pelanggan', sortable: false },
  { title: 'Status', key: 'status', sortable: false },
  { title: 'Priority', key: 'priority', sortable: false },
  { title: 'Category', key: 'category', sortable: false },
  { title: 'Assigned To', key: 'assigned_user', sortable: false },
  { title: 'Downtime', key: 'downtime', sortable: false },
  { title: 'Created', key: 'created_at', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, width: 140 }
]

// Computed
const hasActiveFilters = computed(() => {
  return Object.values(filters).some(value => value !== '')
})

// Methods (semua method tetap sama seperti sebelumnya)
const fetchTickets = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * itemsPerPage.value,
      limit: itemsPerPage.value,
      include_relations: true
    }

      Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        if (key === 'brand') {
          params[key] = value
        } else if (key === 'search') {
          params.search = value
        } else if (key === 'showClosed') {
          // showClosed akan dihandle client-side, tidak perlu dikirim ke backend
        } else {
          params[key] = value
        }
      }
    })

    // Debug: Log parameters yang dikirim (d komentar untuk production)
    // console.log('Filter params:', params)
    // console.log('showClosed value:', filters.showClosed)

    const response = await apiClient.get('/trouble-tickets', { params })
    let allTickets = response.data.data

    // Client-side filtering untuk closed tickets
    if (!filters.showClosed) {
      allTickets = allTickets.filter((ticket: any) => ticket.status !== 'closed')
    }

    tickets.value = allTickets
    // Jika filter showClosed aktif, adjust totalItems untuk refleksi filter client-side
    if (!filters.showClosed) {
      // Hitung jumlah closed tickets yang di-filter
      const closedCount = response.data.data.filter((ticket: any) => ticket.status === 'closed').length
      totalItems.value = response.data.pagination.totalItems - closedCount
    } else {
      totalItems.value = response.data.pagination.totalItems
    }
  } catch (error) {
    console.error('Failed to fetch tickets:', error)
  } finally {
    loading.value = false
  }
}


const fetchStatistics = async () => {
  try {
    const response = await apiClient.get('/trouble-tickets/statistics/dashboard')
    statistics.value = response.data
  } catch (error) {
    console.error('Failed to fetch statistics:', error)
  }
}

const refreshData = () => {
  fetchTickets()
  fetchStatistics()
}

const applyFilters = () => {
  currentPage.value = 1
  fetchTickets()
}

const clearFilters = () => {
  filters.status = ''
  filters.priority = ''
  filters.category = ''
  filters.brand = ''
  filters.search = ''
  filters.showClosed = false
  currentPage.value = 1
  fetchTickets()
}

const debouncedSearch = debounce(() => {
  currentPage.value = 1
  fetchTickets()
}, 500)

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchTickets()
}

const handleItemsPerPageChange = (items: number) => {
  itemsPerPage.value = items
  currentPage.value = 1
  fetchTickets()
}

const openCreateDialog = () => {
  selectedTicket.value = null
  showFormDialog.value = true
}

const closeFormDialog = () => {
  showFormDialog.value = false
  selectedTicket.value = null
}

const viewTicket = (ticket: TroubleTicket) => {
  router.push({ name: 'TroubleTicketDetail', params: { id: ticket.id } })
}

const viewTicketAction = (ticket: TroubleTicket) => {
  router.push({ name: 'TicketAction', params: { id: ticket.id } });
}

const handleTicketSaved = () => {
  closeFormDialog()
  refreshData()
}

const canDeleteTicket = (ticket: TroubleTicket) => {
  return ticket.status === 'resolved' || ticket.status === 'closed' || ticket.status === 'cancelled'
}

const confirmDeleteTicket = (ticket: TroubleTicket) => {
  ticketToDelete.value = ticket
  showDeleteDialog.value = true
}

const closeDeleteDialog = () => {
  showDeleteDialog.value = false
  ticketToDelete.value = null
}

const deleteTicket = async () => {
  if (!ticketToDelete.value) return

  deleting.value = true
  try {
    await apiClient.delete(`/trouble-tickets/${ticketToDelete.value.id}`)
    closeDeleteDialog()
    refreshData()
    fetchStatistics()
  } catch (error) {
    console.error('Failed to delete ticket:', error)
    alert('Gagal menghapus ticket. Silakan coba lagi.')
  } finally {
    deleting.value = false
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'warning',
    in_progress: 'info',
    pending: 'orange',
    closed: 'success',
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    open: 'mdi-clock-outline',
    in_progress: 'mdi-progress-clock',
    pending: 'mdi-account-clock',
    closed: 'mdi-archive',
  }
  return icons[status] || 'mdi-help-circle'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'error',
    critical: 'red-darken-1'
  }
  return colors[priority] || 'grey'
}

const getPriorityIcon = (priority: string) => {
  const icons: Record<string, string> = {
    low: 'mdi-arrow-down',
    medium: 'mdi-minus',
    high: 'mdi-arrow-up',
    critical: 'mdi-fire'
  }
  return icons[priority] || 'mdi-help-circle'
}

const formatStatus = (status: string) => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatPriority = (priority: string) => {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

const formatCategory = (category: string) => {
  return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('id-ID')
}

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString('id-ID', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const calculateTicketDowntime = (created_at: string) => {
  const start = new Date(created_at)
  const now = currentTime.value
  const diff = now.getTime() - start.getTime()

  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

const getDowntimeColor = (created_at: string) => {
  const start = new Date(created_at)
  const now = currentTime.value
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const getDowntimeColorFromMinutes = (minutes: number) => {
  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const formatDowntime = (minutes: number) => {
  if (minutes < 60) return `${minutes} minutes`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours} hour${hours > 1 ? 's' : ''}`
  return `${hours}h ${remainingMinutes}m`
}

const isIpAddress = (str: string) => {
  const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipPattern.test(str)
}

watch(filters, () => {
  currentPage.value = 1
  fetchTickets()
}, { deep: true })

onMounted(() => {
  refreshData()
  refreshInterval.value = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
})
</script>

<style scoped>
/* ===== CONTAINER ===== */
.trouble-ticket-container {
  padding: 28px;
  background: linear-gradient(135deg, 
    rgb(var(--v-theme-background)) 0%, 
    rgba(var(--v-theme-surface), 0.5) 100%);
  min-height: 100vh;
}

/* ===== HEADER SECTION ===== */
.page-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.08) 0%, 
    rgba(var(--v-theme-secondary), 0.05) 100%);
  border-radius: 24px;
  padding: 36px;
  margin-bottom: 32px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  box-shadow: 0 4px 24px rgba(var(--v-theme-shadow), 0.08);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(var(--v-theme-primary), 0.1) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 36px;
  gap: 24px;
  position: relative;
  z-index: 1;
}

.header-avatar {
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.3);
}

.page-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 8px 0 0 0;
  font-weight: 400;
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.create-btn {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.4);
}

.refresh-btn {
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: rotate(180deg);
}

/* ===== STATISTICS GRID ===== */
.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  position: relative;
  z-index: 1;
}

.stat-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
}

.stat-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, 
    rgb(var(--v-theme-primary)) 0%, 
    rgb(var(--v-theme-secondary)) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(var(--v-theme-shadow), 0.18);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.stat-card:hover .stat-gradient {
  opacity: 1;
}

.stat-card:hover .stat-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 28px !important;
  gap: 20px;
}

.stat-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-icon-wrapper.total {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.stat-icon-wrapper.open {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stat-icon-wrapper.progress {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
}

.stat-icon-wrapper.resolved {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stat-icon-wrapper.high {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.stat-icon-wrapper.critical {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  color: white;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-number {
  font-size: 2.25rem;
  font-weight: 800;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
  margin-bottom: 6px;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
}

.trend-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

/* ===== ENHANCED FILTERS SECTION ===== */
.filters-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 24px;
  border: 1px solid rgba(var(--v-theme-outline), 0.08);
  margin-bottom: 24px;
  box-shadow: 0 4px 24px rgba(var(--v-theme-shadow), 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.filters-card:hover {
  box-shadow: 0 8px 32px rgba(var(--v-theme-shadow), 0.12);
  border-color: rgba(var(--v-theme-primary), 0.15);
}

.filters-content {
  padding: 32px !important;
}

/* Header */
.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.filters-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.filters-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s ease;
}

.filters-card:hover .filters-icon-wrapper {
  transform: rotate(10deg) scale(1.05);
}

.filters-header-text {
  flex: 1;
}

.filters-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  letter-spacing: -0.3px;
  line-height: 1.2;
}

.filters-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
  margin: 6px 0 0 0;
  font-weight: 400;
  display: flex;
  align-items: center;
}

.filters-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.active-count-chip {
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.clear-btn {
  transition: all 0.3s ease;
  font-weight: 600;
}

.clear-btn:hover {
  transform: scale(1.05);
}

/* Filters Grid */
.filters-grid-enhanced {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.9375rem;
  color: rgb(var(--v-theme-on-surface));
  letter-spacing: 0.2px;
}

.filter-select-enhanced {
  transition: all 0.3s ease;
}

.filter-select-enhanced:hover {
  transform: translateY(-2px);
}

.filter-select-enhanced :deep(.v-field) {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.filter-select-enhanced :deep(.v-field:hover) {
  box-shadow: 0 4px 12px rgba(var(--v-theme-shadow), 0.1);
}

.filter-select-enhanced :deep(.v-field--focused) {
  box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

.filter-list-item {
  transition: all 0.2s ease;
  border-radius: 8px;
  margin: 2px 8px;
}

.filter-list-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  transform: translateX(4px);
}

/* Closed Tickets Filter */
.closed-tickets-filter {
  animation: fadeInUp 0.6s ease-out 0.3s both;
}

.closed-tickets-filter .v-card {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.closed-tickets-filter .v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--v-theme-shadow), 0.12);
}

.closed-tickets-filter .v-switch {
  transform: scale(0.9);
}

.closed-tickets-filter .v-switch :deep(.v-switch__track) {
  border-radius: 12px;
}

/* Search Field */
.search-field-enhanced {
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

.search-input-enhanced {
  transition: all 0.3s ease;
}

.search-input-enhanced :deep(.v-field) {
  border-radius: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  transition: all 0.3s ease;
}

.search-input-enhanced:hover :deep(.v-field) {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(var(--v-theme-shadow), 0.12);
}

.search-input-enhanced :deep(.v-field--focused) {
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 0 0 3px rgba(var(--v-theme-secondary), 0.12);
}

/* Active Filters Section */
.active-filters-section {
  padding: 20px;
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.04) 0%, 
    rgba(var(--v-theme-secondary), 0.02) 100%);
  border-radius: 16px;
  border: 2px dashed rgba(var(--v-theme-primary), 0.2);
  animation: fadeInUp 0.4s ease-out;
}

.active-filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.active-filters-title {
  font-weight: 700;
  font-size: 1rem;
  color: rgb(var(--v-theme-on-surface));
  letter-spacing: 0.3px;
}

.active-filters-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-chip {
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
}

.filter-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-shadow), 0.15);
}

.filter-summary {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(var(--v-theme-info), 0.08);
  border-radius: 8px;
  border-left: 3px solid rgb(var(--v-theme-info));
}

/* Quick Filters */
.quick-filters-section {
  padding-top: 20px;
  border-top: 1px dashed rgba(var(--v-theme-outline), 0.2);
  animation: fadeInUp 0.6s ease-out 0.3s both;
}

.quick-filters-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.9375rem;
  color: rgb(var(--v-theme-on-surface));
}

.quick-filters-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-filter-chip {
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
}

.quick-filter-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-shadow), 0.15);
}

/* Responsive */
@media (max-width: 960px) {
  .filters-content {
    padding: 24px !important;
  }

  .filters-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-header-right {
    justify-content: space-between;
  }

  .filters-grid-enhanced {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

@media (max-width: 600px) {
  .filters-content {
    padding: 20px !important;
  }

  .filters-icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .filters-title {
    font-size: 1.25rem;
  }

  .filters-subtitle {
    font-size: 0.8125rem;
  }

  .active-filters-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .quick-filters-chips {
    flex-direction: column;
  }

  .quick-filter-chip {
    width: 100%;
    justify-content: flex-start;
  }
}

/* Dark Theme */
.v-theme--dark .filters-card {
  background: rgb(var(--v-theme-surface-bright));
  border-color: rgba(var(--v-theme-outline), 0.15);
}

.v-theme--dark .active-filters-section {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.08) 0%, 
    rgba(var(--v-theme-secondary), 0.04) 100%);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.v-theme--dark .search-input-enhanced :deep(.v-field) {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== TABLE CARD ===== */
.table-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.08);
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(var(--v-theme-shadow), 0.06);
}

.table-header {
  padding: 24px 28px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.08);
}

.table-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  align-items: center;
}

.modern-data-table {
  --v-table-header-height: 64px;
  --v-table-row-height: auto;
}

.modern-data-table :deep(.v-data-table__thead) {
  background: rgba(var(--v-theme-surface-variant), 0.4);
}

.modern-data-table :deep(.v-data-table__th) {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.8px;
  color: rgba(var(--v-theme-on-surface), 0.8) !important;
  border-bottom: 2px solid rgba(var(--v-theme-outline), 0.12);
  padding: 20px 16px !important;
}

.modern-data-table :deep(.v-data-table__td) {
  padding: 20px 16px !important;
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.06);
  vertical-align: top;
}

.modern-data-table :deep(.v-data-table__tr) {
  transition: all 0.2s ease;
}

.modern-data-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.04) !important;
  transform: scale(1.001);
}

/* ===== LOADING ===== */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
}

.loading-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.loading-subtext {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

/* ===== TABLE CELLS ===== */
.ticket-number {
  min-width: 130px;
}

.ticket-title {
  max-width: 280px;
}

.title-text {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  line-height: 1.4;
  display: flex;
  align-items: center;
}

.title-description {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.5;
}

.customer-info {
  max-width: 300px;
}

.customer-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.customer-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9375rem;
  line-height: 1.4;
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.customer-address {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.4;
  display: flex;
  align-items: center;
}

.customer-details {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.status-chip,
.priority-chip {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.2s ease;
}

.status-chip:hover,
.priority-chip:hover {
  transform: scale(1.05);
}

.assigned-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.downtime-container {
  min-width: 130px;
}

.downtime-timer,
.downtime-resolved {
  font-family: 'Roboto Mono', monospace;
  font-weight: 700;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.downtime-timer:hover,
.downtime-resolved:hover {
  transform: scale(1.08);
}

.created-date {
  min-width: 120px;
}

.date-main {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.date-time {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  align-items: center;
}

.actions-container {
  display: flex;
  gap: 6px;
}

.action-btn {
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.1);
}

/* ===== DELETE DIALOG ===== */
.bg-error-gradient {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-error), 0.08) 0%, 
    rgba(var(--v-theme-error), 0.04) 100%);
}

.ticket-delete-info {
  margin-top: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.info-label {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-size: 0.875rem;
}

.info-value {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  text-align: right;
  flex: 1;
}

/* ===== DARK THEME ===== */
.v-theme--dark .page-header {
  background: linear-gradient(135deg, 
    rgba(var(--v-theme-primary), 0.15) 0%, 
    rgba(var(--v-theme-secondary), 0.1) 100%);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .stat-card {
  background: rgb(var(--v-theme-surface-bright));
  border-color: rgba(var(--v-theme-outline), 0.15);
}

.v-theme--dark .filters-card,
.v-theme--dark .table-card {
  background: rgb(var(--v-theme-surface-bright));
  border-color: rgba(var(--v-theme-outline), 0.15);
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1400px) {
  .statistics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1200px) {
  .statistics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .stat-number {
    font-size: 2rem;
  }
}

@media (max-width: 960px) {
  .trouble-ticket-container {
    padding: 20px;
  }
  
  .page-header {
    padding: 28px;
    margin-bottom: 24px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 20px;
    margin-bottom: 28px;
  }
  
  .header-actions {
    justify-content: flex-start;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .statistics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .trouble-ticket-container {
    padding: 16px;
  }
  
  .page-header {
    padding: 24px;
    border-radius: 20px;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .statistics-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .stat-content {
    padding: 24px !important;
  }
  
  .stat-icon-wrapper {
    width: 56px;
    height: 56px;
  }
  
  .stat-number {
    font-size: 1.75rem;
  }
  
  .filters-content {
    padding: 24px !important;
  }
  
  .table-header {
    padding: 20px 24px;
  }
}

@media (max-width: 600px) {
  .header-actions {
    flex-direction: column;
  }
  
  .header-actions .v-btn {
    width: 100%;
  }
  
  .filters-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .stat-content {
    padding: 20px !important;
    gap: 16px;
  }
  
  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
  }
  
  .stat-number {
    font-size: 1.5rem;
  }
  
  .modern-data-table :deep(.v-data-table__th),
  .modern-data-table :deep(.v-data-table__td) {
    padding: 16px 12px !important;
  }
}

@media (max-width: 480px) {
  .trouble-ticket-container {
    padding: 12px;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .stat-content {
    padding: 16px !important;
    gap: 12px;
  }
  
  .stat-icon-wrapper {
    width: 44px;
    height: 44px;
  }
  
  .stat-number {
    font-size: 1.375rem;
  }
  
  .stat-label {
    font-size: 0.75rem;
  }
}

/* ===== ANIMATIONS ===== */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.page-header {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.15s; }
.stat-card:nth-child(3) { animation-delay: 0.2s; }
.stat-card:nth-child(4) { animation-delay: 0.25s; }
.stat-card:nth-child(5) { animation-delay: 0.3s; }
.stat-card:nth-child(6) { animation-delay: 0.35s; }

.filters-card {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.4s both;
}

.table-card {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.5s both;
}

/* ===== SCROLLBAR ===== */
.modern-data-table :deep(.v-table__wrapper) {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-primary), 0.3) transparent;
}

.modern-data-table :deep(.v-table__wrapper)::-webkit-scrollbar {
  height: 10px;
  width: 10px;
}

.modern-data-table :deep(.v-table__wrapper)::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 5px;
}

.modern-data-table :deep(.v-table__wrapper)::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 5px;
  transition: background 0.3s ease;
}

.modern-data-table :deep(.v-table__wrapper)::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* ===== FOCUS STATES ===== */
.v-btn:focus-visible {
  outline: 3px solid rgba(var(--v-theme-primary), 0.4);
  outline-offset: 2px;
}

:deep(.v-field--focused) {
  box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}
</style>