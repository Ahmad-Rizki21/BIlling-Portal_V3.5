<template>
  <v-container fluid class="pa-4 pa-md-6">
    <!-- Header Section with Gradient Background -->
    <div class="header-card mb-4 mb-md-6">
      <div class="header-section">
        <div class="header-content">
          <div class="d-flex align-center">
            <v-avatar class="me-4 elevation-4" color="primary" size="80">
              <v-icon color="white" size="40">mdi-archive-outline</v-icon>
            </v-avatar>
            <div>
              <h1 class="text-h4 font-weight-bold text-white mb-2">Manajemen Inventaris</h1>
              <p class="header-subtitle mb-0">
                Kelola perangkat, tipe, dan status inventaris
              </p>
            </div>
            <v-spacer></v-spacer>
            <!-- Action buttons bisa ditambahkan di sini -->
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">

    <!-- Main Card with Modern Design -->
    <v-card class="inventory-card" elevation="0">
      <!-- Modern Tabs -->
      <v-tabs 
        v-model="tab" 
        class="modern-tabs"
        color="primary"
        grow
        slider-color="primary"
        :mobile-breakpoint="600"
      >
        <v-tab value="items" class="tab-item">
          <v-icon start size="22">mdi-package-variant-closed</v-icon>
          <span class="tab-text">Daftar Perangkat</span>
        </v-tab>
        <v-tab value="types" class="tab-item">
          <v-icon start size="22">mdi-shape-outline</v-icon>
          <span class="tab-text">Kelola Tipe Item</span>
        </v-tab>
        <v-tab value="statuses" class="tab-item">
          <v-icon start size="22">mdi-tag-outline</v-icon>
          <span class="tab-text">Kelola Status</span>
        </v-tab>
        <v-tab value="history" class="tab-item">
          <v-icon start size="22">mdi-history</v-icon>
          <span class="tab-text">History Pergerakan</span>
        </v-tab>
      </v-tabs>

      <v-divider></v-divider>

      <!-- Tab Content Windows -->
      <v-window v-model="tab" class="tab-window">
        
        <!-- Items Tab -->
        <v-window-item value="items" class="tab-content">
           <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Daftar Perangkat</h2>
              <p class="content-subtitle">Kelola semua perangkat inventaris</p>
            </div>
            <div class="d-flex flex-wrap align-center gap-3">
              <v-btn
                variant="tonal"
                color="teal"
                @click="exportToExcel"
                prepend-icon="mdi-file-excel"
                class="add-btn secondary-action-btn me-2"
                elevation="0"
              >
                <span class="btn-text">Export to Excel</span>
              </v-btn>
              <v-btn
                variant="tonal"
                color="purple"
                @click="openMultipleScanner"
                prepend-icon="mdi-barcode-multiple"
                class="add-btn secondary-action-btn me-2"
                elevation="0"
              >
                <span class="btn-text">Multi Scan</span>
              </v-btn>
              <v-btn
                variant="tonal"
                color="teal"
                @click="downloadTemplate"
                prepend-icon="mdi-microsoft-excel"
                class="add-btn secondary-action-btn me-2"
                elevation="0"
              >
                <span class="btn-text">Download Template</span>
              </v-btn>
              <v-btn
                variant="tonal"
                color="orange"
                @click="openBulkImportDialog"
                prepend-icon="mdi-upload-multiple"
                class="add-btn secondary-action-btn me-2"
                elevation="0"
              >
                <span class="btn-text">Bulk Import</span>
              </v-btn>
              <v-btn
                color="primary"
                class="add-btn ms-1"
                elevation="2"
                @click="openItemDialog()"
              >
                <v-icon start>mdi-plus</v-icon>
                <span class="btn-text">Tambah Item</span>
              </v-btn>
            </div>
          </div>

          <!-- Filter Card -->
          <v-card class="filter-card mb-6" elevation="0">
            <div class="d-flex flex-wrap align-center gap-4 pa-4">
              <v-text-field
                v-model="searchQuery"
                label="Cari (SN, MAC, Lokasi)"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="comfortable"
                hide-details
                class="flex-grow-1"
                style="min-width: 250px;"
              ></v-text-field>
              <v-select
                v-model="selectedType"
                :items="itemTypes"
                item-title="name"
                item-value="id"
                label="Filter Tipe Item"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                class="flex-grow-1"
                style="min-width: 200px;"
              ></v-select>
              <v-select
                v-model="selectedStatus"
                :items="statuses"
                item-title="name"
                item-value="id"
                label="Filter Status Perangkat"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                class="flex-grow-1"
                style="min-width: 200px;"
                prepend-inner-icon="mdi-tag-outline"
              ></v-select>
              <v-btn variant="text" @click="resetFilters" class="text-none">
                Reset Filter
              </v-btn>
            </div>
          </v-card>

          <div class="table-container">
            <!-- Desktop Table View -->
            <div class="d-none d-md-block">
              <v-data-table
                :headers="itemHeaders"
                :items="filteredInventoryItems"
                :loading="loading"
                class="modern-table elegant-table"
                :items-per-page="15"
                :mobile-breakpoint="768"
              >
                <template v-slot:loading>
                  <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
                </template>

                <template v-slot:item.status="{ item }">
                  <v-chip
                    :color="getStatusColor(item.status.name)"
                    size="default"
                    variant="elevated"
                    class="status-chip"
                  >
                    {{ item.status.name }}
                  </v-chip>
                </template>

                <template v-slot:item.item_type="{ item }">
                  <div class="type-wrapper">
                    <v-icon size="18" class="me-2 text-medium-emphasis">mdi-package-variant</v-icon>
                    {{ item.item_type.name }}
                  </div>
                </template>

                <template v-slot:item.serial_number="{ item }">
                  <div class="serial-wrapper">
                    <code class="serial-code">{{ item.serial_number }}</code>
                  </div>
                </template>

                <template v-slot:item.mac_address="{ item }">
                  <div class="mac-wrapper">
                    <code v-if="item.mac_address" class="mac-code">{{ item.mac_address }}</code>
                    <span v-else class="text-medium-emphasis">-</span>
                  </div>
                </template>

                <template v-slot:item.location="{ item }">
                  <div class="location-wrapper">
                    <v-icon v-if="item.location" size="16" class="me-1 text-medium-emphasis">mdi-map-marker</v-icon>
                    <span>{{ item.location || '-' }}</span>
                  </div>
                </template>

                <template v-slot:item.purchase_date="{ item }">
                  <div class="date-wrapper">
                    <v-icon v-if="item.purchase_date" size="16" class="me-1 text-medium-emphasis">mdi-calendar</v-icon>
                    <span v-if="item.purchase_date">
                      {{ new Date(item.purchase_date).toLocaleDateString('id-ID', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                      }) }}
                    </span>
                    <span v-else class="text-medium-emphasis">-</span>
                  </div>
                </template>

                <template v-slot:item.actions="{ item }">
                  <div class="action-buttons justify-center">
                    <v-tooltip text="History">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          color="info"
                          class="action-btn-small"
                          v-bind="props"
                          @click="showHistory(item)"
                        >
                          <v-icon size="18">mdi-history</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>

                    <v-tooltip text="Edit">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          color="primary"
                          class="action-btn-small"
                          v-bind="props"
                          @click="openItemDialog(item)"
                        >
                          <v-icon size="18">mdi-pencil</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>

                    <v-tooltip text="Hapus">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          color="error"
                          class="action-btn-small"
                          v-bind="props"
                          @click="deleteItem(item)"
                        >
                          <v-icon size="18">mdi-delete</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </template>

                <template v-slot:no-data>
                  <div class="no-data-wrapper">
                    <v-icon size="64" class="text-medium-emphasis mb-3">mdi-package-variant-closed-remove</v-icon>
                    <p class="text-medium-emphasis no-data-text">Belum ada perangkat inventaris</p>
                  </div>
                </template>
              </v-data-table>
            </div>

            <!-- Mobile Card View -->
            <div class="d-block d-md-none">
              <div v-if="loading" class="px-4 py-4">
                <SkeletonLoader type="list" :items="5" />
              </div>

              <div v-else-if="filteredInventoryItems.length === 0" class="no-data-wrapper">
                <v-icon size="64" color="surface-variant">mdi-package-variant-closed-remove</v-icon>
                <div class="no-data-text">Belum ada perangkat inventaris</div>
                <p class="text-medium-emphasis mt-2">Mulai dengan menambahkan perangkat pertama Anda</p>
                <v-btn
                  color="primary"
                  variant="elevated"
                  @click="openItemDialog()"
                  class="mt-6 text-none"
                  prepend-icon="mdi-plus"
                >
                  Tambah Item
                </v-btn>
              </div>

              <div v-else class="mobile-cards-container">
                <v-card
                  v-for="item in filteredInventoryItems"
                  :key="item.id"
                  class="mobile-inventory-card mb-3"
                  elevation="2"
                >
                  <v-card-text class="pa-4">
                    <!-- Header dengan Serial Number dan Status -->
                    <div class="d-flex align-center mb-3">
                      <div class="flex-grow-1">
                        <div class="d-flex align-center mb-1">
                          <v-icon size="16" class="me-2 text-primary">mdi-fingerprint</v-icon>
                          <h3 class="mobile-inventory-title">{{ item.serial_number }}</h3>
                        </div>
                        <div v-if="item.mac_address" class="d-flex align-center">
                          <v-icon size="14" class="me-2 text-medium-emphasis">mdi-network-outline</v-icon>
                          <code class="mobile-mac-code">{{ item.mac_address }}</code>
                        </div>
                      </div>
                      <v-chip
                        :color="getStatusColor(item.status.name)"
                        size="small"
                        variant="elevated"
                        class="mobile-status-chip"
                      >
                        <v-icon start size="12">mdi-tag</v-icon>
                        {{ item.status.name }}
                      </v-chip>
                    </div>

                    <!-- Device Details -->
                    <div class="mobile-inventory-details">
                      <div class="detail-row">
                        <v-icon size="small" class="me-2 text-medium-emphasis">mdi-shape-outline</v-icon>
                        <span class="detail-label">Tipe:</span>
                        <span class="detail-value">{{ item.item_type.name }}</span>
                      </div>

                      <div v-if="item.location" class="detail-row">
                        <v-icon size="small" class="me-2 text-medium-emphasis">mdi-map-marker</v-icon>
                        <span class="detail-label">Lokasi:</span>
                        <span class="detail-value">{{ item.location }}</span>
                      </div>

                      <div v-if="item.purchase_date" class="detail-row">
                        <v-icon size="small" class="me-2 text-medium-emphasis">mdi-calendar</v-icon>
                        <span class="detail-label">Beli:</span>
                        <span class="detail-value">{{ formatDate(item.purchase_date) }}</span>
                      </div>

                      <div v-if="item.notes" class="detail-row">
                        <v-icon size="small" class="me-2 text-medium-emphasis">mdi-note-text</v-icon>
                        <span class="detail-label">Catatan:</span>
                        <span class="detail-value text-truncate">{{ item.notes }}</span>
                      </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="d-flex gap-2 mt-4">
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="info"
                        @click="showHistory(item)"
                        prepend-icon="mdi-history"
                        class="flex-grow-1"
                      >
                        History
                      </v-btn>
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="primary"
                        @click="openItemDialog(item)"
                        prepend-icon="mdi-pencil"
                        class="flex-grow-1"
                      >
                        Edit
                      </v-btn>
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="error"
                        @click="deleteItem(item)"
                        prepend-icon="mdi-delete"
                        class="flex-grow-1"
                      >
                        Hapus
                      </v-btn>
                    </div>
                  </v-card-text>
                </v-card>
              </div>
            </div>
          </div>
        </v-window-item>

        <!-- Types Tab -->
        <v-window-item value="types" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Tipe Item yang Tersedia</h2>
              <p class="content-subtitle">Kelola kategori perangkat inventaris</p>
            </div>
            <v-btn
              color="primary"
              class="add-btn"
              elevation="2"
              @click="openTypeDialog()"
            >
              <v-icon start>mdi-plus</v-icon>
              <span class="btn-text">Tambah Tipe Baru</span>
            </v-btn>
          </div>

          <!-- Desktop Table View for Types -->
          <div class="d-none d-md-block table-container">
            <v-data-table
              :headers="typeHeaders"
              :items="itemTypes"
              :loading="loading"
              class="modern-table elegant-table"
              :items-per-page="15"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>

              <template v-slot:item.name="{ item }">
                <div class="type-name-wrapper">
                  <v-icon size="18" class="me-2 text-primary">mdi-shape</v-icon>
                  <span class="type-name">{{ item.name }}</span>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="action-buttons justify-center">
                  <v-tooltip text="Edit">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="small"
                        variant="text"
                        color="primary"
                        class="action-btn-small"
                        v-bind="props"
                        @click="openTypeDialog(item)"
                      >
                        <v-icon size="18">mdi-pencil</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>

                  <v-tooltip text="Hapus">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="small"
                        variant="text"
                        color="error"
                        class="action-btn-small"
                        v-bind="props"
                        @click="deleteType(item)"
                      >
                        <v-icon size="18">mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </template>

              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-shape-outline</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada tipe item</p>
                </div>
              </template>
            </v-data-table>
          </div>

          <!-- Mobile Card View for Types -->
          <div class="d-block d-md-none">
            <div v-if="loading" class="px-4 py-4">
              <SkeletonLoader type="list" :items="5" />
            </div>

            <div v-else-if="itemTypes.length === 0" class="no-data-wrapper">
              <v-icon size="64" color="surface-variant">mdi-shape-outline</v-icon>
              <div class="no-data-text">Belum ada tipe item</div>
              <p class="text-medium-emphasis mt-2">Mulai dengan menambahkan tipe item pertama Anda</p>
              <v-btn
                color="primary"
                variant="elevated"
                @click="openTypeDialog()"
                class="mt-6 text-none"
                prepend-icon="mdi-plus"
              >
                Tambah Tipe
              </v-btn>
            </div>

            <div v-else class="mobile-cards-container">
              <v-card
                v-for="item in itemTypes"
                :key="item.id"
                class="mobile-type-card mb-3"
                elevation="2"
              >
                <v-card-text class="pa-4">
                  <!-- Header dengan Icon dan Nama -->
                  <div class="d-flex align-center mb-3">
                    <div class="flex-grow-1">
                      <div class="d-flex align-center mb-1">
                        <v-avatar size="40" color="primary" variant="tonal" class="me-3">
                          <v-icon size="20">mdi-shape</v-icon>
                        </v-avatar>
                        <h3 class="mobile-type-title">{{ item.name }}</h3>
                      </div>
                    </div>
                    <v-chip
                      size="small"
                      color="primary"
                      variant="tonal"
                      class="mobile-type-chip"
                    >
                      <v-icon start size="12">mdi-tag</v-icon>
                      ID: {{ item.id }}
                    </v-chip>
                  </div>

                  <!-- Action Buttons -->
                  <div class="d-flex gap-2">
                    <v-btn
                      size="small"
                      variant="tonal"
                      color="primary"
                      @click="openTypeDialog(item)"
                      prepend-icon="mdi-pencil"
                      class="flex-grow-1"
                    >
                      Edit
                    </v-btn>
                    <v-btn
                      size="small"
                      variant="tonal"
                      color="error"
                      @click="deleteType(item)"
                      prepend-icon="mdi-delete"
                      class="flex-grow-1"
                    >
                      Hapus
                    </v-btn>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </div>
        </v-window-item>

        <!-- Statuses Tab -->
        <v-window-item value="statuses" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">Status Inventaris yang Tersedia</h2>
              <p class="content-subtitle">Kelola status kondisi perangkat</p>
            </div>
            <v-btn
              color="primary"
              class="add-btn"
              elevation="2"
              @click="openStatusDialog()"
            >
              <v-icon start>mdi-plus</v-icon>
              <span class="btn-text">Tambah Status Baru</span>
            </v-btn>
          </div>

          <!-- Desktop Table View for Statuses -->
          <div class="d-none d-md-block table-container">
            <v-data-table
              :headers="statusHeaders"
              :items="statuses"
              :loading="loading"
              class="modern-table elegant-table"
              :items-per-page="15"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>

              <template v-slot:item.name="{ item }">
                <div class="status-name-wrapper">
                  <v-chip
                    :color="getStatusColor(item.name)"
                    size="default"
                    variant="elevated"
                    class="status-preview-chip"
                  >
                    {{ item.name }}
                  </v-chip>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="action-buttons justify-center">
                  <v-tooltip text="Edit">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="small"
                        variant="text"
                        color="primary"
                        class="action-btn-small"
                        v-bind="props"
                        @click="openStatusDialog(item)"
                      >
                        <v-icon size="18">mdi-pencil</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>

                  <v-tooltip text="Hapus">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon
                        size="small"
                        variant="text"
                        color="error"
                        class="action-btn-small"
                        v-bind="props"
                        @click="deleteStatus(item)"
                      >
                        <v-icon size="18">mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </template>

              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-tag-outline</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada status inventaris</p>
                </div>
              </template>
            </v-data-table>
          </div>

          <!-- Mobile Card View for Statuses -->
          <div class="d-block d-md-none">
            <div v-if="loading" class="px-4 py-4">
              <SkeletonLoader type="list" :items="5" />
            </div>

            <div v-else-if="statuses.length === 0" class="no-data-wrapper">
              <v-icon size="64" color="surface-variant">mdi-tag-outline</v-icon>
              <div class="no-data-text">Belum ada status inventaris</div>
              <p class="text-medium-emphasis mt-2">Mulai dengan menambahkan status pertama Anda</p>
              <v-btn
                color="primary"
                variant="elevated"
                @click="openStatusDialog()"
                class="mt-6 text-none"
                prepend-icon="mdi-plus"
              >
                Tambah Status
              </v-btn>
            </div>

            <div v-else class="mobile-cards-container">
              <v-card
                v-for="item in statuses"
                :key="item.id"
                class="mobile-status-card mb-3"
                elevation="2"
              >
                <v-card-text class="pa-4">
                  <!-- Header dengan Icon dan Nama Status -->
                  <div class="d-flex align-center mb-3">
                    <div class="flex-grow-1">
                      <div class="d-flex align-center mb-1">
                        <v-avatar size="40" color="primary" variant="tonal" class="me-3">
                          <v-icon size="20">mdi-tag</v-icon>
                        </v-avatar>
                        <h3 class="mobile-status-title">{{ item.name }}</h3>
                      </div>
                    </div>
                    <v-chip
                      :color="getStatusColor(item.name)"
                      size="small"
                      variant="elevated"
                      class="mobile-status-preview-chip"
                    >
                      <v-icon start size="12">mdi-tag</v-icon>
                      ID: {{ item.id }}
                    </v-chip>
                  </div>

                  <!-- Status Preview -->
                  <div class="mobile-status-preview-section">
                    <label class="field-label mb-2">Preview Status</label>
                    <div class="status-preview-wrapper">
                      <div class="preview-label">Tampilan pada tabel:</div>
                      <v-chip
                        :color="getStatusColor(item.name)"
                        size="large"
                        variant="elevated"
                        class="status-preview-display"
                      >
                        <v-icon start size="16">mdi-tag</v-icon>
                        {{ item.name }}
                      </v-chip>
                    </div>
                  </div>

                  <!-- Action Buttons -->
                  <div class="d-flex gap-2 mt-4">
                    <v-btn
                      size="small"
                      variant="tonal"
                      color="primary"
                      @click="openStatusDialog(item)"
                      prepend-icon="mdi-pencil"
                      class="flex-grow-1"
                    >
                      Edit
                    </v-btn>
                    <v-btn
                      size="small"
                      variant="tonal"
                      color="error"
                      @click="deleteStatus(item)"
                      prepend-icon="mdi-delete"
                      class="flex-grow-1"
                    >
                      Hapus
                    </v-btn>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </div>
        </v-window-item>

        <!-- History Pergerakan Tab -->
        <v-window-item value="history" class="tab-content">
          <div class="content-header">
            <div class="content-title-wrapper">
              <h2 class="content-title">History Pergerakan Perangkat</h2>
              <p class="content-subtitle">Lihat semua pergerakan dan perubahan status perangkat</p>
            </div>
          </div>

          <!-- Global History Filter -->
          <v-card class="filter-card mb-6" elevation="0">
            <div class="d-flex flex-wrap align-center gap-4 pa-4">
              <v-text-field
                v-model="historySearchQuery"
                label="Cari (SN, Lokasi, Aksi)"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="comfortable"
                hide-details
                class="flex-grow-1"
                style="min-width: 250px;"
              ></v-text-field>
              <v-select
                v-model="selectedHistoryType"
                :items="historyActionTypes"
                item-title="label"
                item-value="value"
                label="Filter Tipe Aksi"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                class="flex-grow-1"
                style="min-width: 200px;"
              ></v-select>
              <v-btn variant="text" @click="resetHistoryFilters" class="text-none">
                Reset Filter
              </v-btn>
            </div>
          </v-card>

          <div class="table-container">
            <v-data-table
              :headers="globalHistoryHeaders"
              :items="filteredGlobalHistory"
              :loading="globalHistoryLoading"
              class="modern-table elegant-table"
              :items-per-page="20"
              :mobile-breakpoint="768"
            >
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@5"></v-skeleton-loader>
              </template>

              <template v-slot:item.timestamp="{ item }">
                <div class="timestamp-wrapper">
                  <v-icon size="14" class="me-1 text-medium-emphasis">mdi-clock</v-icon>
                  <span>{{ new Date(item.timestamp).toLocaleString('id-ID', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) }}</span>
                </div>
              </template>

              <template v-slot:item.serial_number="{ item }">
                <div class="serial-wrapper">
                  <code class="serial-code">{{ item.serial_number }}</code>
                </div>
              </template>

              <template v-slot:item.action="{ item }">
                <div class="action-wrapper">
                  <v-chip
                    :color="getActionColor(item.action)"
                    size="small"
                    variant="elevated"
                    class="action-chip"
                  >
                    {{ getActionType(item.action) }}
                  </v-chip>
                  <div class="action-details mt-1 text-caption">
                    {{ getActionDetails(item.action) }}
                  </div>
                </div>
              </template>

              <template v-slot:item.user="{ item }">
                <div class="user-wrapper">
                  <v-avatar size="24" class="me-2" color="primary">
                    <v-icon size="14" color="white">mdi-account</v-icon>
                  </v-avatar>
                  <span class="text-body-2">{{ item.user?.name || 'System' }}</span>
                </div>
              </template>

              <template v-slot:no-data>
                <div class="no-data-wrapper">
                  <v-icon size="64" class="text-medium-emphasis mb-3">mdi-history</v-icon>
                  <p class="text-medium-emphasis no-data-text">Belum ada history pergerakan perangkat</p>
                </div>
              </template>
            </v-data-table>
          </div>
        </v-window-item>
      </v-window>
    </v-card>
  </div>

    <!-- Item Dialog -->
    <v-dialog v-model="itemDialog" :max-width="isMobile ? '95vw' : '800px'" persistent>
      <v-card class="modern-dialog-card">
        <!-- Enhanced Header -->
        <div class="dialog-modern-header">
          <div class="header-gradient-bg">
            <div class="header-content">
              <div class="dialog-header-left">
                <div class="dialog-avatar-wrapper">
                  <v-avatar size="56" class="dialog-avatar">
                    <v-icon size="32" color="white">mdi-package-variant-closed-plus</v-icon>
                  </v-avatar>
                </div>
                <div class="dialog-title-section">
                  <h2 class="dialog-main-title">{{ formItemTitle }}</h2>
                  <p class="dialog-subtitle">
                    {{ editedItem.id ? 'Edit informasi perangkat yang sudah ada' : 'Tambahkan perangkat baru ke sistem inventaris' }}
                  </p>
                </div>
              </div>
              <div class="dialog-header-right">
                <v-btn
                  icon
                  variant="text"
                  size="large"
                  @click="closeItemDialog"
                  class="close-btn-modern"
                >
                  <v-icon size="24" color="white">mdi-close</v-icon>
                </v-btn>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Content -->
        <v-card-text class="dialog-modern-content pa-0">
          <!-- Device Identification Section -->
          <div class="form-section">
            <div class="section-header-modern">
              <div class="section-icon-wrapper primary-section">
                <v-icon size="20" color="white">mdi-fingerprint</v-icon>
              </div>
              <div class="section-content">
                <h3 class="section-title">Identifikasi Perangkat</h3>
                <p class="section-description">Informasi unik untuk identifikasi perangkat</p>
              </div>
            </div>

            <v-row class="mt-4">
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">Serial Number <span class="required-star">*</span></label>
                  <div class="scanner-field-wrapper">
                    <v-text-field
                      v-model="editedItem.serial_number"
                      placeholder="Masukkan serial number perangkat"
                      variant="outlined"
                      density="comfortable"
                      prepend-inner-icon="mdi-identifier"
                      class="modern-text-field"
                      hide-details
                    ></v-text-field>
                    <v-btn
                      @click="openSerialScanner"
                      class="scanner-action-btn"
                      variant="tonal"
                      color="primary"
                      size="default"
                    >
                      <v-icon>mdi-barcode-scan</v-icon>
                    </v-btn>
                  </div>
                  <div class="field-hint">Scan barcode atau ketik manual</div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">MAC Address</label>
                  <div class="scanner-field-wrapper">
                    <v-text-field
                      v-model="editedItem.mac_address"
                      placeholder="AA:BB:CC:DD:EE:FF"
                      variant="outlined"
                      density="comfortable"
                      prepend-inner-icon="mdi-network-outline"
                      class="modern-text-field"
                      hide-details
                    ></v-text-field>
                    <v-btn
                      @click="openMacScanner"
                      class="scanner-action-btn"
                      variant="tonal"
                      color="primary"
                      size="default"
                    >
                      <v-icon>mdi-barcode-scan</v-icon>
                    </v-btn>
                  </div>
                  <div class="field-hint">Format: AA:BB:CC:DD:EE:FF (opsional)</div>
                </div>
              </v-col>
            </v-row>
          </div>

          <!-- Device Classification Section -->
          <div class="form-section">
            <div class="section-header-modern">
              <div class="section-icon-wrapper secondary-section">
                <v-icon size="20" color="white">mdi-shape-outline</v-icon>
              </div>
              <div class="section-content">
                <h3 class="section-title">Klasifikasi Perangkat</h3>
                <p class="section-description">Kategori dan status perangkat</p>
              </div>
            </div>

            <v-row class="mt-4">
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">Tipe Item <span class="required-star">*</span></label>
                  <v-select
                    v-model="editedItem.item_type_id"
                    :items="itemTypes"
                    item-title="name"
                    item-value="id"
                    placeholder="Pilih tipe perangkat"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-shape"
                    class="modern-select"
                    hide-details
                  ></v-select>
                  <div class="field-hint">Pilih kategori perangkat yang sesuai</div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">Status <span class="required-star">*</span></label>
                  <v-select
                    v-model="editedItem.status_id"
                    :items="statuses"
                    item-title="name"
                    item-value="id"
                    placeholder="Pilih status perangkat"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-tag"
                    class="modern-select"
                    hide-details
                  ></v-select>
                  <div class="field-hint">Status kondisi perangkat saat ini</div>
                </div>
              </v-col>
            </v-row>
          </div>

          <!-- Location & Details Section -->
          <div class="form-section">
            <div class="section-header-modern">
              <div class="section-icon-wrapper accent-section">
                <v-icon size="20" color="white">mdi-map-marker-multiple</v-icon>
              </div>
              <div class="section-content">
                <h3 class="section-title">Lokasi & Detail</h3>
                <p class="section-description">Informasi lokasi dan detail tambahan</p>
              </div>
            </div>

            <v-row class="mt-4">
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">Lokasi</label>
                  <v-text-field
                    v-model="editedItem.location"
                    placeholder="Masukkan lokasi perangkat"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-map-marker"
                    class="modern-text-field"
                    hide-details
                  ></v-text-field>
                  <div class="field-hint">Lokasi penyimpanan atau pemasangan</div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="field-group">
                  <label class="field-label">Tanggal Pembelian</label>
                  <v-text-field
                    v-model="editedItem.purchase_date"
                    type="date"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-calendar"
                    class="modern-text-field"
                    hide-details
                  ></v-text-field>
                  <div class="field-hint">Tanggal pembelian perangkat (opsional)</div>
                </div>
              </v-col>
              <v-col cols="12">
                <div class="field-group">
                  <label class="field-label">Catatan Tambahan</label>
                  <v-textarea
                    v-model="editedItem.notes"
                    placeholder="Tambahkan catatan atau informasi tambahan tentang perangkat ini..."
                    rows="3"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-note-text"
                    class="modern-textarea"
                    hide-details
                    auto-grow
                  ></v-textarea>
                  <div class="field-hint">Informasi tambahan yang relevan (opsional)</div>
                </div>
              </v-col>
            </v-row>
          </div>
        </v-card-text>

        <v-divider></v-divider>
        
        <!-- Enhanced Actions -->
        <v-card-actions class="dialog-modern-actions">
          <div class="actions-left">
            <v-btn
              variant="text"
              color="medium-emphasis"
              @click="closeItemDialog"
              class="modern-cancel-btn"
              prepend-icon="mdi-close-circle"
            >
              Batal
            </v-btn>
          </div>
          <div class="actions-right">
            <v-btn
              color="primary"
              variant="elevated"
              @click="saveItem"
              :loading="saving"
              class="modern-save-btn"
              prepend-icon="mdi-content-save"
              size="large"
            >
              {{ editedItem.id ? 'Perbarui Item' : 'Tambah Item' }}
            </v-btn>
          </div>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Type Dialog -->
    <v-dialog v-model="typeDialog" :max-width="isMobile ? '95vw' : '600px'" persistent>
      <v-card class="modern-dialog-card">
        <!-- Enhanced Header -->
        <div class="dialog-modern-header">
          <div class="header-gradient-bg">
            <div class="header-content">
              <div class="dialog-header-left">
                <div class="dialog-avatar-wrapper">
                  <v-avatar size="56" class="dialog-avatar">
                    <v-icon size="32" color="white">mdi-shape-plus</v-icon>
                  </v-avatar>
                </div>
                <div class="dialog-title-section">
                  <h2 class="dialog-main-title">{{ formTypeTitle }}</h2>
                  <p class="dialog-subtitle">
                    {{ editedType.id ? 'Edit kategori perangkat yang sudah ada' : 'Tambahkan kategori baru untuk perangkat inventaris' }}
                  </p>
                </div>
              </div>
              <div class="dialog-header-right">
                <v-btn
                  icon
                  variant="text"
                  size="large"
                  @click="closeTypeDialog"
                  class="close-btn-modern"
                >
                  <v-icon size="24" color="white">mdi-close</v-icon>
                </v-btn>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Content -->
        <v-card-text class="dialog-modern-content pa-0">
          <!-- Category Information Section -->
          <div class="form-section">
            <div class="section-header-modern">
              <div class="section-icon-wrapper secondary-section">
                <v-icon size="20" color="white">mdi-shape-outline</v-icon>
              </div>
              <div class="section-content">
                <h3 class="section-title">Informasi Kategori</h3>
                <p class="section-description">Detail kategori untuk perangkat inventaris</p>
              </div>
            </div>

            <div class="mt-4">
              <div class="field-group">
                <label class="field-label">Nama Tipe Item <span class="required-star">*</span></label>
                <v-text-field
                  v-model="editedType.name"
                  placeholder="Masukkan nama kategori perangkat"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-shape"
                  class="modern-text-field"
                  hide-details
                ></v-text-field>
                <div class="field-hint">
                  Contoh: ONT, Router, Switch, Access Point, dll.
                </div>
              </div>

              <!-- Additional Info Cards -->
              <div class="info-cards-grid mt-6">
                <div class="info-card-item">
                  <div class="info-icon-wrapper">
                    <v-icon size="20" color="primary">mdi-information-outline</v-icon>
                  </div>
                  <div class="info-content">
                    <div class="info-title">Penting</div>
                    <div class="info-text">Nama tipe akan digunakan untuk mengelompokkan perangkat dalam sistem inventaris</div>
                  </div>
                </div>

                <div class="info-card-item">
                  <div class="info-icon-wrapper">
                    <v-icon size="20" color="success">mdi-lightbulb-outline</v-icon>
                  </div>
                  <div class="info-content">
                    <div class="info-title">Tips</div>
                    <div class="info-text">Gunakan nama yang deskriptif dan mudah dipahami oleh tim teknis</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>

        <!-- Enhanced Actions -->
        <v-card-actions class="dialog-modern-actions">
          <div class="actions-left">
            <v-btn
              variant="text"
              color="medium-emphasis"
              @click="closeTypeDialog"
              class="modern-cancel-btn"
              prepend-icon="mdi-close-circle"
            >
              Batal
            </v-btn>
          </div>
          <div class="actions-right">
            <v-btn
              color="primary"
              variant="elevated"
              @click="saveType"
              :loading="saving"
              class="modern-save-btn"
              prepend-icon="mdi-content-save"
              size="large"
            >
              {{ editedType.id ? 'Perbarui Tipe' : 'Tambah Tipe' }}
            </v-btn>
          </div>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Status Dialog -->
    <v-dialog v-model="statusDialog" :max-width="isMobile ? '95vw' : '600px'" persistent>
      <v-card class="modern-dialog-card">
        <!-- Enhanced Header -->
        <div class="dialog-modern-header">
          <div class="header-gradient-bg">
            <div class="header-content">
              <div class="dialog-header-left">
                <div class="dialog-avatar-wrapper">
                  <v-avatar size="56" class="dialog-avatar">
                    <v-icon size="32" color="white">mdi-tag-plus</v-icon>
                  </v-avatar>
                </div>
                <div class="dialog-title-section">
                  <h2 class="dialog-main-title">{{ formStatusTitle }}</h2>
                  <p class="dialog-subtitle">
                    {{ editedStatus.id ? 'Edit status kondisi perangkat yang sudah ada' : 'Tambahkan status baru untuk kondisi perangkat' }}
                  </p>
                </div>
              </div>
              <div class="dialog-header-right">
                <v-btn
                  icon
                  variant="text"
                  size="large"
                  @click="closeStatusDialog"
                  class="close-btn-modern"
                >
                  <v-icon size="24" color="white">mdi-close</v-icon>
                </v-btn>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Content -->
        <v-card-text class="dialog-modern-content pa-0">
          <!-- Status Information Section -->
          <div class="form-section">
            <div class="section-header-modern">
              <div class="section-icon-wrapper accent-section">
                <v-icon size="20" color="white">mdi-tag-outline</v-icon>
              </div>
              <div class="section-content">
                <h3 class="section-title">Informasi Status</h3>
                <p class="section-description">Detail status kondisi perangkat inventaris</p>
              </div>
            </div>

            <div class="mt-4">
              <div class="field-group">
                <label class="field-label">Nama Status <span class="required-star">*</span></label>
                <v-text-field
                  v-model="editedStatus.name"
                  placeholder="Masukkan nama status perangkat"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-tag"
                  class="modern-text-field"
                  hide-details
                ></v-text-field>
                <div class="field-hint">
                  Contoh: Terpasang, Rusak, Gudang, Dalam Perbaikan, dll.
                </div>
              </div>

              <!-- Status Preview -->
              <div class="status-preview-section mt-6">
                <label class="field-label mb-3">Preview Status</label>
                <div class="status-preview-wrapper">
                  <div class="preview-label">Tampilan pada tabel:</div>
                  <v-chip
                    :color="getStatusColor(editedStatus.name || 'Status')"
                    size="large"
                    variant="elevated"
                    class="status-preview-chip"
                  >
                    <v-icon start size="20">mdi-tag</v-icon>
                    {{ editedStatus.name || 'Nama Status' }}
                  </v-chip>
                </div>
              </div>

              <!-- Additional Info Cards -->
              <div class="info-cards-grid mt-6">
                <div class="info-card-item">
                  <div class="info-icon-wrapper">
                    <v-icon size="20" color="warning">mdi-alert-outline</v-icon>
                  </div>
                  <div class="info-content">
                    <div class="info-title">Perhatian</div>
                    <div class="info-text">Status akan mempengaruhi tampilan dan filter perangkat dalam sistem</div>
                  </div>
                </div>

                <div class="info-card-item">
                  <div class="info-icon-wrapper">
                    <v-icon size="20" color="info">mdi-help-circle-outline</v-icon>
                  </div>
                  <div class="info-content">
                    <div class="info-title">Bantuan</div>
                    <div class="info-text">Gunakan status yang jelas dan konsisten dengan workflow tim</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>

        <!-- Enhanced Actions -->
        <v-card-actions class="dialog-modern-actions">
          <div class="actions-left">
            <v-btn
              variant="text"
              color="medium-emphasis"
              @click="closeStatusDialog"
              class="modern-cancel-btn"
              prepend-icon="mdi-close-circle"
            >
              Batal
            </v-btn>
          </div>
          <div class="actions-right">
            <v-btn
              color="primary"
              variant="elevated"
              @click="saveStatus"
              :loading="saving"
              class="modern-save-btn"
              prepend-icon="mdi-content-save"
              size="large"
            >
              {{ editedStatus.id ? 'Perbarui Status' : 'Tambah Status' }}
            </v-btn>
          </div>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- History Dialog -->
    <v-dialog v-model="historyDialog" :max-width="isMobile ? '95vw' : '900px'" persistent>
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon class="me-3" color="info">mdi-history</v-icon>
          <span>Riwayat Pergerakan Perangkat</span>
          <v-spacer></v-spacer>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="historyDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="dialog-content pa-6">
          <!-- Device Info Card -->
          <v-card class="device-info-card mb-6" elevation="2">
            <v-card-text class="pa-4">
              <div class="device-header">
                <div class="device-avatar-wrapper">
                  <v-avatar size="48" color="primary" class="elevated-avatar">
                    <v-icon size="28" color="white">mdi-package-variant-closed</v-icon>
                  </v-avatar>
                </div>
                <div class="device-info">
                  <h3 class="device-title">
                    {{ selectedItemForHistory?.serial_number }}
                  </h3>
                  <div class="device-subtitle text-medium-emphasis">
                    Riwayat Pergerakan Perangkat
                  </div>
                </div>
                <div class="flex-grow-1"></div>
                <v-chip
                  :color="getStatusColor(selectedItemForHistory?.status?.name || '')"
                  variant="elevated"
                  class="status-chip-large"
                >
                  <v-icon start size="16">mdi-tag</v-icon>
                  {{ selectedItemForHistory?.status?.name || '-' }}
                </v-chip>
              </div>

              <v-divider class="my-3"></v-divider>

              <div class="device-details-grid">
                <div class="detail-item">
                  <div class="detail-icon-wrapper">
                    <v-icon size="16" color="primary">mdi-shape-outline</v-icon>
                  </div>
                  <div class="detail-content">
                    <div class="detail-label">Tipe Perangkat</div>
                    <div class="detail-value">{{ selectedItemForHistory?.item_type?.name || '-' }}</div>
                  </div>
                </div>

                <div class="detail-item">
                  <div class="detail-icon-wrapper">
                    <v-icon size="16" color="success">mdi-map-marker</v-icon>
                  </div>
                  <div class="detail-content">
                    <div class="detail-label">Lokasi Saat Ini</div>
                    <div class="detail-value">{{ selectedItemForHistory?.location || '-' }}</div>
                  </div>
                </div>

                <div class="detail-item" v-if="selectedItemForHistory?.mac_address">
                  <div class="detail-icon-wrapper">
                    <v-icon size="16" color="info">mdi-network-outline</v-icon>
                  </div>
                  <div class="detail-content">
                    <div class="detail-label">MAC Address</div>
                    <div class="detail-value">{{ selectedItemForHistory?.mac_address }}</div>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- History Timeline Section -->
          <div class="history-section">
            <div class="section-header">
              <div class="section-title-wrapper">
                <v-icon class="section-icon" color="primary">mdi-timeline</v-icon>
                <div>
                  <h4 class="section-title">Timeline Pergerakan</h4>
                  <p class="section-subtitle">Semua aktivitas perubahan status dan lokasi perangkat</p>
                </div>
              </div>
              <v-chip
                v-if="historyLogs.length > 0"
                color="primary"
                variant="tonal"
                size="small"
              >
                {{ historyLogs.length }} aktivitas
              </v-chip>
            </div>

            <v-data-table
              :headers="historyHeaders"
              :items="historyLogs"
              :loading="historyLoading"
              class="modern-table elegant-table history-table"
              density="compact"
              :items-per-page="10"
              :mobile-breakpoint="768"
            >
            <template v-slot:loading>
              <v-skeleton-loader type="table-row@3"></v-skeleton-loader>
            </template>

            <template v-slot:item.timestamp="{ item }">
              <div class="timestamp-cell">
                <div class="timestamp-icon-wrapper">
                  <v-icon size="16" color="primary">mdi-clock-outline</v-icon>
                </div>
                <div class="timestamp-content">
                  <div class="timestamp-date">
                    {{ new Date(item.timestamp).toLocaleDateString('id-ID', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric'
                    }) }}
                  </div>
                  <div class="timestamp-time text-medium-emphasis">
                    {{ new Date(item.timestamp).toLocaleTimeString('id-ID', {
                      hour: '2-digit',
                      minute: '2-digit'
                    }) }}
                  </div>
                </div>
              </div>
            </template>

            <template v-slot:item.action="{ item }">
              <div class="action-cell">
                <v-chip
                  :color="getActionColor(item.action)"
                  size="small"
                  variant="elevated"
                  class="action-type-chip mb-1"
                >
                  <v-icon start size="12">{{ getActionIcon(item.action) }}</v-icon>
                  {{ getActionType(item.action) }}
                </v-chip>
                <div class="action-details text-caption text-medium-emphasis">
                  {{ getActionDetails(item.action) }}
                </div>
              </div>
            </template>

            <template v-slot:item.user="{ item }">
              <div class="user-cell">
                <v-avatar size="28" class="user-avatar" :color="getAvatarColor(item.user?.name)">
                  <v-icon size="16" color="white">
                    {{ item.user?.name ? 'mdi-account' : 'mdi-robot' }}
                  </v-icon>
                </v-avatar>
                <div class="user-content">
                  <div class="user-name">{{ item.user?.name || 'System' }}</div>
                  <div class="user-role text-caption text-medium-emphasis">
                    {{ item.user?.role || 'Automated' }}
                  </div>
                </div>
              </div>
            </template>

            <template v-slot:no-data>
              <div class="no-data-wrapper pa-6">
                <v-icon size="64" class="text-medium-emphasis mb-3">mdi-timeline-help</v-icon>
                <h5 class="text-h6 font-weight-medium mb-2">Belum Ada Riwayat</h5>
                <p class="text-medium-emphasis text-center">Perangkat ini belum memiliki riwayat perubahan status atau lokasi</p>
              </div>
            </template>
          </v-data-table>
        </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            color="grey-darken-1"
            @click="historyDialog = false"
            class="cancel-btn"
          >
            Tutup
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bulk Import Dialog -->
    <v-dialog v-model="bulkImportDialog" :max-width="isMobile ? '95vw' : '600px'" persistent>
      <v-card class="modern-dialog-card">
        <!-- Enhanced Header -->
        <div class="dialog-modern-header">
          <div class="header-gradient-bg">
            <div class="header-content">
              <v-icon class="me-3" color="white" size="28">mdi-upload-multiple</v-icon>
              <div>
                <h3 class="text-h6 font-weight-bold text-white mb-1">Bulk Import Inventaris</h3>
                <p class="text-body-2 text-white opacity-90 mb-0">Import data inventaris dari file Excel/CSV</p>
              </div>
              <v-spacer></v-spacer>
              <v-btn
                icon
                variant="text"
                color="white"
                @click="closeBulkImportDialog"
                :disabled="bulkImportLoading"
              >
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
        </div>

        <v-card-text class="pa-6">
          <!-- File Upload Section -->
          <div class="mb-4">
            <v-label class="text-subtitle-2 font-weight-medium mb-2 d-block">
              Pilih File Import
            </v-label>

            <v-file-input
              v-model="bulkImportFile"
              label="Pilih file Excel atau CSV"
              accept=".xlsx,.xls,.csv"
              prepend-icon="mdi-file-excel"
              variant="outlined"
              density="comfortable"
              :loading="bulkImportLoading"
              :disabled="bulkImportLoading"
              show-size
              hide-details
              class="mb-3"
            ></v-file-input>
          </div>

          <!-- Error Message -->
          <v-alert
            v-if="bulkImportError"
            type="error"
            variant="tonal"
            class="mb-4"
            density="compact"
            :text="bulkImportError"
          ></v-alert>

          <!-- Success Result -->
          <v-alert
            v-if="bulkImportResult?.success"
            type="success"
            variant="tonal"
            class="mb-4"
            density="compact"
            :text="bulkImportResult?.message"
          >
            <template v-slot:append>
              <div class="text-end">
                <div class="text-caption opacity-75">Berhasil:</div>
                <div class="text-body-2 font-weight-medium">{{ bulkImportResult?.success_count }} item</div>
              </div>
            </template>
          </v-alert>

          <!-- Partial Success with Errors -->
          <v-alert
            v-if="bulkImportResult?.success && bulkImportResult?.error_count && bulkImportResult.error_count > 0"
            type="warning"
            variant="tonal"
            class="mb-4"
            density="compact"
          >
            <template v-slot:title>
              Import Selesai dengan Beberapa Error
            </template>
            <template v-slot:text>
              <div class="mb-2">
                Berhasil: {{ bulkImportResult?.success_count || 0 }} item,
                Gagal: {{ bulkImportResult?.error_count || 0 }} item
              </div>
              <div v-if="bulkImportResult?.errors && bulkImportResult.errors.length > 0" class="mt-2">
                <v-btn
                  size="small"
                  variant="outlined"
                  color="warning"
                  @click="showImportErrors = !showImportErrors"
                >
                  {{ showImportErrors ? 'Sembunyikan' : 'Tampilkan' }} Detail Error
                </v-btn>
              </div>
            </template>
          </v-alert>

          <!-- Error Details -->
          <v-expand-transition>
            <div v-show="showImportErrors && bulkImportResult?.errors && bulkImportResult.errors.length > 0">
              <v-card variant="outlined" class="mt-2" max-height="200">
                <v-card-text class="pa-3">
                  <div class="text-caption">
                    <div
                      v-for="(error, index) in (bulkImportResult?.errors || []).slice(0, 10)"
                      :key="index"
                      class="mb-1"
                    >
                      <v-icon size="12" color="error" class="me-1">mdi-alert-circle</v-icon>
                      {{ error }}
                    </div>
                    <div v-if="bulkImportResult?.errors && bulkImportResult.errors.length > 10" class="mt-2 font-weight-medium">
                      ... dan {{ bulkImportResult.errors.length - 10 }} error lainnya
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </v-expand-transition>

          <!-- Help Text -->
          <div class="text-caption text-medium-emphasis mt-3">
            <v-icon size="14" class="me-1">mdi-information-outline</v-icon>
            Pastikan file memiliki kolom: serial_number, item_type_id, status_id.
            Download template untuk contoh format yang benar.
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="outlined"
            color="medium-emphasis"
            @click="closeBulkImportDialog"
            :disabled="bulkImportLoading"
          >
            Batal
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="handleBulkImport"
            :loading="bulkImportLoading"
            :disabled="!bulkImportFile || bulkImportLoading"
          >
            <v-icon start>mdi-upload</v-icon>
            Import Data
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Barcode Scanner Dialogs -->
    <BarcodeScanner
      v-model="isSerialScannerOpen"
      scan-type="serial"
      @detected="handleSerialDetected"
    />

    <BarcodeScanner
      v-model="isMacScannerOpen"
      scan-type="mac"
      @detected="handleMacDetected"
    />

    <BarcodeScanner
      v-model="isMultipleScannerOpen"
      scan-type="multiple"
      @multiple-detected="handleMultipleDetected"
    />

  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useDisplay } from 'vuetify';
// XLSX akan di-import secara dinamis saat fungsi export dipanggil
import apiClient from '@/services/api';
import BarcodeScanner from '@/components/BarcodeScanner.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';
import { useBarcodeScanner } from '@/composables/useBarcodeScanner';

// --- INTERFACES ---
interface ItemType { id: number; name: string; }
interface Status { id: number; name: string; }
interface InventoryItem {
  id: number;
  serial_number: string;
  mac_address: string | null;
  location: string | null;
  notes: string | null;
  purchase_date: string | null;
  item_type_id: number;
  status_id: number;
  item_type: ItemType;
  status: Status;
}

// --- COMPOSABLES ---
const { mobile } = useDisplay();
const isMobile = computed(() => mobile.value);

// --- STATE ---
const tab = ref('items');
const loading = ref(true);
const saving = ref(false);

// --- Barcode Scanner State ---
const {
  isSerialScannerOpen,
  isMacScannerOpen,
  openSerialScanner,
  openMacScanner,
  handleSerialDetected,
  handleMacDetected,
} = useBarcodeScanner({
  onSerialDetected: (serial: string) => {
    editedItem.value.serial_number = serial;
  },
  onMacDetected: (mac: string) => {
    editedItem.value.mac_address = mac;
  }
});

// Multiple scanner state
const isMultipleScannerOpen = ref(false);

function openMultipleScanner() {
  // Open item dialog first if not open
  if (!itemDialog.value) {
    openItemDialog();
  }
  // Then open multiple scanner
  isMultipleScannerOpen.value = true;
}

function handleMultipleDetected(results: { en?: string; serial?: string; mac?: string }) {
  // Auto-fill the dialog with scanned results
  if (results.serial) {
    editedItem.value.serial_number = results.serial;
  }
  if (results.mac) {
    editedItem.value.mac_address = results.mac;
  }
  // Note: EN is not used in current inventory model, but we could store it in notes
  if (results.en) {
    editedItem.value.notes = editedItem.value.notes
      ? `${editedItem.value.notes}\nEN: ${results.en}`
      : `EN: ${results.en}`;
  }

  // Show success message
  console.log('Multiple barcode scanned:', results);
}

// --- Filter & Search State ---
const searchQuery = ref('');
const selectedType = ref<number | null>(null);
const selectedStatus = ref<number | null>(null);

const historyDialog = ref(false);
const historyLoading = ref(false);
const historyLogs = ref<any[]>([]);
const selectedItemForHistory = ref<InventoryItem | null>(null);
const historyHeaders = [
  { title: 'Waktu', key: 'timestamp', width: '160px' },
  { title: 'Aksi', key: 'action', sortable: false, width: '150px' },
  { title: 'Oleh', key: 'user', width: '120px' },
];

// Global History State
const globalHistoryLoading = ref(false);
const globalHistoryLogs = ref<any[]>([]);
const historySearchQuery = ref('');
const selectedHistoryType = ref<string | null>(null);
const historyActionTypes = [
  { label: 'Semua Aksi', value: null },
  { label: 'Dibuat', value: 'created' },
  { label: 'Diubah', value: 'updated' },
  { label: 'Dihapus', value: 'deleted' },
];

const globalHistoryHeaders = [
  { title: 'Waktu', key: 'timestamp', width: '160px' },
  { title: 'Serial Number', key: 'serial_number', width: '140px' },
  { title: 'Aksi', key: 'action', sortable: false, width: '150px' },
  { title: 'Oleh', key: 'user', width: '120px' },
];



// State for Inventory Items
const inventoryItems = ref<InventoryItem[]>([]);
const itemDialog = ref(false);
const editedItem = ref<Partial<InventoryItem>>({});
const itemHeaders = [
  { title: 'Serial Number', key: 'serial_number', width: '140px' },
  { title: 'MAC Address', key: 'mac_address', width: '120px' },
  { title: 'Tipe', key: 'item_type.name', width: '100px' },
  { title: 'Status', key: 'status.name', width: '100px' },
  { title: 'Lokasi', key: 'location', width: '120px' },
  { title: 'Tanggal Pembelian', key: 'purchase_date', width: '120px' },
  { title: 'Aksi', key: 'actions', sortable: false, width: '100px', align: 'center' as const },
];

// State for Item Types
const itemTypes = ref<ItemType[]>([]);
const typeDialog = ref(false);
const editedType = ref<Partial<ItemType>>({});
const typeHeaders = [
  { title: 'ID', key: 'id', width: '60px', align: 'center' as const },
  { title: 'Nama Tipe', key: 'name', width: '200px' },
  { title: 'Aksi', key: 'actions', sortable: false, width: '100px', align: 'center' as const }
];

// State for Statuses
const statuses = ref<Status[]>([]);
const statusDialog = ref(false);
const editedStatus = ref<Partial<Status>>({});
const statusHeaders = [
  { title: 'ID', key: 'id', width: '60px', align: 'center' as const },
  { title: 'Nama Status', key: 'name', width: '200px' },
  { title: 'Aksi', key: 'actions', sortable: false, width: '100px', align: 'center' as const }
];

// --- Computed Titles ---
const formItemTitle = computed(() => editedItem.value.id ? 'Edit Item' : 'Tambah Item Baru');
const formTypeTitle = computed(() => editedType.value.id ? 'Edit Tipe Item' : 'Tambah Tipe Baru');
const formStatusTitle = computed(() => editedStatus.value.id ? 'Edit Status' : 'Tambah Status Baru');

const filteredInventoryItems = computed(() => {
  let items = inventoryItems.value;

  if (searchQuery.value) {
    const lowerQuery = searchQuery.value.toLowerCase();
    items = items.filter(item =>
      item.serial_number.toLowerCase().includes(lowerQuery) ||
      (item.mac_address && item.mac_address.toLowerCase().includes(lowerQuery)) ||
      (item.location && item.location.toLowerCase().includes(lowerQuery))
    );
  }

  if (selectedType.value) {
    items = items.filter(item => item.item_type_id === selectedType.value);
  }

  if (selectedStatus.value) {
    items = items.filter(item => item.status_id === selectedStatus.value);
  }

  return items;
});

const filteredGlobalHistory = computed(() => {
  let logs = globalHistoryLogs.value;

  if (historySearchQuery.value) {
    const lowerQuery = historySearchQuery.value.toLowerCase();
    logs = logs.filter(log =>
      log.serial_number.toLowerCase().includes(lowerQuery) ||
      log.action.toLowerCase().includes(lowerQuery)
    );
  }

  if (selectedHistoryType.value) {
    logs = logs.filter(log =>
      log.action.toLowerCase().includes(selectedHistoryType.value!)
    );
  }

  return logs;
});


// --- METHODS ---
async function fetchData() {
  loading.value = true;
  try {
    const [itemsRes, typesRes, statusesRes] = await Promise.all([
      apiClient.get('/inventory/'),
      apiClient.get('/inventory-types/'),
      apiClient.get('/inventory-statuses/'),
    ]);
    inventoryItems.value = itemsRes.data;
    itemTypes.value = typesRes.data;
    statuses.value = statusesRes.data;

    // Also fetch global history
    await fetchGlobalHistory();
  } catch (error) { console.error("Gagal mengambil data:", error); }
  finally { loading.value = false; }
}

async function fetchGlobalHistory() {
  globalHistoryLoading.value = true;
  try {
    // Use the new efficient endpoint
    const response = await apiClient.get('/inventory/history/all');
    globalHistoryLogs.value = response.data;
  } catch (error) {
    console.error("Error fetching global history:", error);
  } finally {
    globalHistoryLoading.value = false;
  }
}

function resetHistoryFilters() {
  historySearchQuery.value = '';
  selectedHistoryType.value = null;
}

// Methods for Inventory Items
function openItemDialog(item: InventoryItem | null = null) {
  editedItem.value = item ? { ...item } : {};
  itemDialog.value = true;
}
function closeItemDialog() {
  itemDialog.value = false;
}
async function saveItem() {
  saving.value = true;
  try {
    const payload = { ...editedItem.value };
    const itemId = payload.id;

    // Remove id from payload for update requests
    if (itemId) {
      delete payload.id;
      // Also remove any nested objects that shouldn't be sent
      delete payload.item_type;
      delete payload.status;

      await apiClient.patch(`/inventory/${itemId}`, payload);
    } else {
      await apiClient.post('/inventory/', payload);
    }
    // console.log('🔧 Frontend: Starting fetchData after update...');
    await fetchData();
    // console.log('🔧 Frontend: fetchData completed, closing dialog...');
    closeItemDialog();
  } catch (e) {
    // console.error('🔧 Frontend: Error in saveItem:', e);
    showSnackbar('Gagal menyimpan perubahan. Silakan refresh halaman.', 'error');
  } finally { saving.value = false; }
}
async function deleteItem(item: InventoryItem) {
  if (confirm(`Hapus item SN: ${item.serial_number}?`)) {
    await apiClient.delete(`/inventory/${item.id}`);
    await fetchData();
  }
}

// Methods for Item Types
function openTypeDialog(item: ItemType | null = null) {
  editedType.value = item ? { ...item } : {};
  typeDialog.value = true;
}
function closeTypeDialog() {
  typeDialog.value = false;
}
async function saveType() {
  saving.value = true;
  try {
    const payload = { name: editedType.value.name };
    if (editedType.value.id) {
      await apiClient.patch(`/inventory-types/${editedType.value.id}`, payload);
    } else {
      await apiClient.post('/inventory-types/', payload);
    }
    await fetchData();
    closeTypeDialog();
  } catch (e) { console.error(e); } 
  finally { saving.value = false; }
}
async function deleteType(item: ItemType) {
  if (confirm(`Hapus tipe: ${item.name}?`)) {
    await apiClient.delete(`/inventory-types/${item.id}`);
    await fetchData();
  }
}

// Methods for Statuses
function openStatusDialog(item: Status | null = null) {
  editedStatus.value = item ? { ...item } : {};
  statusDialog.value = true;
}
function closeStatusDialog() {
  statusDialog.value = false;
}
async function saveStatus() {
  saving.value = true;
  try {
    const payload = { name: editedStatus.value.name };
    if (editedStatus.value.id) {
      await apiClient.patch(`/inventory-statuses/${editedStatus.value.id}`, payload);
    } else {
      await apiClient.post('/inventory-statuses/', payload);
    }
    await fetchData();
    closeStatusDialog();
  } catch (e) { console.error(e); } 
  finally { saving.value = false; }
}
async function deleteStatus(item: Status) {
  if (confirm(`Hapus status: ${item.name}?`)) {
    await apiClient.delete(`/inventory-statuses/${item.id}`);
    await fetchData();
  }
}

function getStatusColor(statusName: string = '') {
  const name = statusName.toLowerCase();
  if (name === 'terpasang') return 'success';
  if (name === 'rusak') return 'error';
  if (name === 'dalam perbaikan') return 'warning';
  if (name === 'perbaikan') return 'warning';
  if (name === 'gudang') return 'info';
  if (name === 'hilang') return 'error';
  if (name === 'dismantle') return 'grey-darken-1';
  return 'primary';
}

async function exportToExcel() {
  // Dynamic import XLSX hanya saat dibutuhkan
  const XLSX = await import('xlsx');

  const dataToExport = filteredInventoryItems.value.map(item => ({
    'Serial Number': item.serial_number,
    'MAC Address': item.mac_address || '-',
    'Tipe': item.item_type.name,
    'Status': item.status.name,
    'Lokasi': item.location || '-',
    'Catatan': item.notes || '-',
  }));

  const worksheet = XLSX.utils.json_to_sheet(dataToExport);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Daftar Inventaris');

  // Auto-size columns
  const cols = Object.keys(dataToExport[0] || {}).map(key => ({ wch: Math.max(key.length, ...dataToExport.map(row => String(row[key as keyof typeof row] || '').length)) + 2 }));
  worksheet['!cols'] = cols;

  XLSX.writeFile(workbook, `inventaris_perangkat_${new Date().toISOString().split('T')[0]}.xlsx`);
}

function resetFilters() {
  searchQuery.value = '';
  selectedType.value = null;
  selectedStatus.value = null;
}

function downloadTemplate() {
  // Create template data for Excel import
  const templateData = [
    {
      'Serial Number': 'SN001234567890',
      'MAC Address': 'AA:BB:CC:DD:EE:FF',
      'Tipe': 'ONT',
      'Status': 'Gudang',
      'Lokasi': 'Gudang Utama',
      'Catatan': 'Contoh catatan'
    }
  ];

  // Import XLSX dynamically
  import('xlsx').then(XLSX => {
    const worksheet = XLSX.utils.json_to_sheet(templateData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Template Inventaris');

    // Auto-size columns
    const cols = Object.keys(templateData[0] || {}).map(key => ({
      wch: Math.max(key.length, 15)
    }));
    worksheet['!cols'] = cols;

    XLSX.writeFile(workbook, `template_inventaris_${new Date().toISOString().split('T')[0]}.xlsx`);
  }).catch(error => {
    console.error('Error downloading template:', error);
    // Fallback: create a simple CSV
    const csvContent = 'Serial Number,MAC Address,Tipe,Status,Lokasi,Catatan\nSN001234567890,AA:BB:CC:DD:EE:FF,ONT,Gudang,Gudang Utama,Contoh catatan';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `template_inventaris_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  });
}

const bulkImportDialog = ref(false);
const bulkImportFile = ref<File | null>(null);
const bulkImportLoading = ref(false);
const bulkImportResult = ref<any>(null);
const bulkImportError = ref<string | null>(null);
const showImportErrors = ref(false);

function openBulkImportDialog() {
  bulkImportDialog.value = true;
  bulkImportFile.value = null;
  bulkImportResult.value = null;
  bulkImportError.value = null;
  showImportErrors.value = false;
}

function closeBulkImportDialog() {
  bulkImportDialog.value = false;
  bulkImportFile.value = null;
  bulkImportResult.value = null;
  bulkImportError.value = null;
  showImportErrors.value = false;
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    bulkImportFile.value = target.files[0];
  }
}

async function handleBulkImport() {
  if (!bulkImportFile.value) {
    bulkImportError.value = 'Silakan pilih file terlebih dahulu';
    return;
  }

  bulkImportLoading.value = true;
  bulkImportError.value = null;
  bulkImportResult.value = null;

  try {
    const formData = new FormData();
    formData.append('file', bulkImportFile.value);

    const response = await apiClient.post('/inventory/bulk-import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    bulkImportResult.value = response.data;

    // Refresh data setelah import berhasil
    await fetchData();

    // Auto tutup dialog setelah 2 detik jika berhasil
    setTimeout(() => {
      closeBulkImportDialog();
    }, 2000);

  } catch (error: any) {
    console.error('Bulk import error:', error);
    bulkImportError.value = error.response?.data?.detail || 'Gagal mengimport file. Silakan coba lagi.';
  } finally {
    bulkImportLoading.value = false;
  }
}

// History functions
async function showHistory(item: InventoryItem) {
  selectedItemForHistory.value = item;
  historyLoading.value = true;
  historyDialog.value = true;

  try {
    const response = await apiClient.get(`/inventory/${item.id}/history`);
    historyLogs.value = response.data;
  } catch (error) {
    console.error('Error fetching history:', error);
    // TODO: Show error notification
  } finally {
    historyLoading.value = false;
  }
}

function getActionType(action: string) {
  if (action.toLowerCase().includes('created')) return 'Dibuat';
  if (action.toLowerCase().includes('updated')) return 'Diubah';
  if (action.toLowerCase().includes('deleted')) return 'Dihapus';
  return 'Lainnya';
}

function getActionColor(action: string) {
  if (action.toLowerCase().includes('created')) return 'success';
  if (action.toLowerCase().includes('updated')) return 'warning';
  if (action.toLowerCase().includes('deleted')) return 'error';
  return 'grey';
}

function getActionDetails(action: string) {
  // Extract details after the main action type
  const match = action.match(/^(Created|Updated|Deleted) item - (.+)$/);
  if (match) {
    return match[2];
  }
  return action;
}

function getActionIcon(action: string) {
  if (action.toLowerCase().includes('created')) return 'mdi-plus-circle';
  if (action.toLowerCase().includes('updated')) return 'mdi-pencil-circle';
  if (action.toLowerCase().includes('deleted')) return 'mdi-delete-circle';
  return 'mdi-information';
}

function getAvatarColor(userName?: string) {
  if (!userName) return 'grey';

  const colors = ['blue', 'green', 'purple', 'orange', 'teal', 'indigo', 'pink', 'amber'];
  const index = userName.charCodeAt(0) % colors.length;
  return colors[index];
}

// Format date helper function for mobile cards
function formatDate(date: string | Date | null): string {
  if (!date) return '-';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  const offset = d.getTimezoneOffset();
  const correctedDate = new Date(d.getTime() + (offset * 60 * 1000));
  return correctedDate.toLocaleDateString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Format datetime helper function for mobile history cards
function formatDateTime(timestamp: string | Date): string {
  if (!timestamp) return '-';
  const d = new Date(timestamp);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

onMounted(fetchData);
</script>

<style scoped>
/* === CONTAINER & LAYOUT === */
.inventory-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 32px;
}

/* === PAGE HEADER === */
.page-header {
  margin-bottom: 40px;
}

.header-content {
  display: flex;
  align-items: center;
  padding: 24px 32px;
}

.header-avatar {
  margin-right: 20px;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 1.125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
  font-weight: 400;
}

/* Header Card styling - sama seperti halaman lain */
.header-card {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
  background: white;
}

/* Header content for memperbesar box */
.header-content {
  padding: 24px 32px;
}

.header-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.header-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="50" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="30" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
}

/* Header text styling */
.header-section h1 {
  color: white !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 1.1rem;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  opacity: 0.95;
}

/* === MAIN CARD === */
.inventory-card {
  border-radius: 16px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

/* === MODERN TABS === */
.modern-tabs {
  background: rgb(var(--v-theme-surface));
}

.modern-tabs :deep(.v-tab) {
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0.5px;
  min-height: 72px;
  font-size: 1rem;
  transition: all 0.3s ease;
  padding: 0 24px;
}

.modern-tabs :deep(.v-tab--selected) {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-secondary), 0.1) 100%);
  color: rgb(var(--v-theme-primary));
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tab-text {
  font-size: 1rem;
  font-weight: 500;
}

/* === TAB CONTENT === */
.tab-window {
  min-height: 500px;
}

.tab-content {
  padding: 32px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 20px;
}

.content-title-wrapper {
  flex: 1;
}

.content-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  line-height: 1.3;
}

.content-subtitle {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
}

.add-btn {
  border-radius: 12px;
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0.5px;
  padding: 0 28px;
  height: 48px;
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.25);
  transition: all 0.3s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.35);
}

.btn-text {
  font-size: 1rem;
}

.secondary-action-btn {
  box-shadow: none !important;
  background: rgba(var(--v-theme-teal), 0.1);
  color: rgb(var(--v-theme-teal));
}

.secondary-action-btn {
  margin-right: 8px !important;
  padding: 0 20px !important;
}

.secondary-action-btn:hover {
  background: rgba(var(--v-theme-teal), 0.15) !important;
  transform: translateY(-2px);
}

.add-btn.ms-1 {
  margin-left: 4px !important;
  padding: 0 24px !important;
}

/* === FILTER CARD === */
.filter-card {
  border-radius: 16px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  background: rgba(var(--v-theme-surface), 0.5);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.filter-card .v-text-field :deep(.v-field),
.filter-card .v-select :deep(.v-field) {
  border-radius: 12px;
}

/* === TABLE STYLING === */
.table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.modern-table {
  background: rgb(var(--v-theme-surface));
}

.modern-table :deep(.v-data-table__wrapper) {
  border-radius: 12px;
}

.modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-primary), 0.05);
}

.modern-table :deep(.v-data-table-header th) {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  font-size: 0.875rem;
  letter-spacing: 0.5px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1);
  padding: 16px 12px;
  height: auto;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04);
}

.modern-table :deep(.v-data-table__td) {
  padding: 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.5);
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Elegant Table Styling - Consistent with PelangganView */
.elegant-table {
  background: transparent !important;
}

.elegant-table :deep(th) {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  opacity: 0.8;
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
  padding: 16px 12px !important;
  height: auto !important;
}

.elegant-table :deep(td) {
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
  padding: 12px !important;
  font-size: 0.875rem !important;
}

.elegant-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04) !important;
}

/* === TABLE CELL CONTENT === */
.status-chip {
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-size: 0.85rem;
  padding: 8px 12px;
}

.type-wrapper,
.serial-wrapper,
.mac-wrapper,
.location-wrapper,
.date-wrapper {
  display: flex;
  align-items: center;
}

.serial-code,
.mac-code {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

/* === TABLE STYLING === */
.table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.modern-table {
  background: rgb(var(--v-theme-surface));
}

.modern-table :deep(.v-data-table__wrapper) {
  border-radius: 12px;
}

.modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-primary), 0.05);
}

.modern-table :deep(.v-data-table-header th) {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  font-size: 0.875rem;
  letter-spacing: 0.5px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.1);
  padding: 16px 12px;
  height: auto;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04);
}

.modern-table :deep(.v-data-table__td) {
  padding: 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.5);
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Elegant Table Styling - Consistent with PelangganView */
.elegant-table {
  background: transparent !important;
}

.elegant-table :deep(th) {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  opacity: 0.8;
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
  padding: 16px 12px !important;
  height: auto !important;
}

.elegant-table :deep(td) {
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
  padding: 12px !important;
  font-size: 0.875rem !important;
}

.elegant-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04) !important;
}

/* === TABLE CELL CONTENT === */
.status-chip {
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-size: 0.85rem;
  padding: 8px 12px;
}

.type-wrapper,
.serial-wrapper,
.mac-wrapper,
.location-wrapper,
.date-wrapper {
  display: flex;
  align-items: center;
}

.serial-code,
.mac-code {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.type-name-wrapper {
  display: flex;
  align-items: center;
}

.type-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.status-name-wrapper {
  display: flex;
  align-items: center;
}

.status-preview-chip {
  font-weight: 500;
  border-radius: 8px;
  font-size: 0.85rem;
  padding: 8px 12px;
}

/* === ACTION BUTTONS === */
.action-buttons {
  display: flex;
  gap: 4px;
}

.action-buttons.justify-center {
  justify-content: center;
}

.action-btn-small {
  border-radius: 6px;
  transition: all 0.3s ease;
  min-width: 32px;
  min-height: 32px;
  width: 32px;
  height: 32px;
}

.action-btn-small:hover {
  transform: scale(1.1);
}

/* === NO DATA STATE === */
.no-data-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
}

.no-data-text {
  font-size: 1rem;
  margin-top: 8px;
}

/* === MODERN DIALOG STYLING === */

/* Main Dialog Card */
.modern-dialog-card {
  border-radius: 20px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

/* Modern Header */
.dialog-modern-header {
  position: relative;
  overflow: hidden;
}

.header-gradient-bg {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  position: relative;
}

.header-gradient-bg::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 40%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="modern-pattern" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="white" opacity="0.1"/><circle cx="5" cy="5" r="0.5" fill="white" opacity="0.05"/><circle cx="15" cy="15" r="0.5" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23modern-pattern)"/></svg>');
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32px 32px 32px 32px;
  position: relative;
  z-index: 1;
}

.dialog-header-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.dialog-avatar-wrapper {
  position: relative;
}

.dialog-avatar {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 3px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.dialog-title-section {
  flex: 1;
}

.dialog-main-title {
  color: white !important;
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 4px;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dialog-subtitle {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 0.95rem;
  margin: 0;
  font-weight: 400;
  opacity: 0.9;
}

.close-btn-modern {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.close-btn-modern:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  transform: scale(1.1);
}

/* Modern Content */
.dialog-modern-content {
  background: rgb(var(--v-theme-surface));
  max-height: 70vh;
  overflow-y: auto;
}

/* Form Sections */
.form-section {
  padding: 24px 32px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
  transition: all 0.3s ease;
}

.form-section:last-child {
  border-bottom: none;
}

.form-section:hover {
  background: rgba(var(--v-theme-primary), 0.01);
}

.section-header-modern {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 4px;
}

.section-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.primary-section {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary), 0.8) 100%);
}

.secondary-section {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.accent-section {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.section-header-modern:hover .section-icon-wrapper {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.section-content {
  flex: 1;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
  line-height: 1.3;
}

.section-description {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
  line-height: 1.4;
}

/* Modern Form Fields */
.field-group {
  margin-bottom: 20px;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.required-star {
  color: rgb(var(--v-theme-error));
  font-weight: 700;
  font-size: 0.9rem;
}

.modern-text-field :deep(.v-field),
.modern-select :deep(.v-field),
.modern-textarea :deep(.v-field) {
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.6);
  border: 2px solid rgba(var(--v-border-color), 0.2);
  transition: all 0.3s ease;
}

.modern-text-field :deep(.v-field:hover),
.modern-select :deep(.v-field:hover),
.modern-textarea :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-surface), 0.8);
}

.modern-text-field :deep(.v-field--focused),
.modern-select :deep(.v-field--focused),
.modern-textarea :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary));
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 0 0 4px rgba(var(--v-theme-primary), 0.1);
}

.scanner-field-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scanner-field-wrapper .modern-text-field {
  flex: 1;
}

.scanner-action-btn {
  height: 56px !important;
  min-width: 56px !important;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.scanner-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.field-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 6px;
  font-style: italic;
  line-height: 1.3;
}

/* Info Cards Grid */
.info-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.info-card-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--v-theme-surface), 0.6);
  border: 1px solid rgba(var(--v-border-color), 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.info-card-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.info-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(var(--v-theme-surface), 0.8);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.info-card-item:hover .info-icon-wrapper {
  transform: scale(1.1);
}

.info-content {
  flex: 1;
  min-width: 0;
}

.info-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 4px;
  line-height: 1.2;
}

.info-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.4;
}

/* Status Preview Section */
.status-preview-section {
  padding: 20px;
  background: rgba(var(--v-theme-surface), 0.4);
  border: 1px solid rgba(var(--v-border-color), 0.08);
  border-radius: 12px;
  margin-top: 24px;
}

.status-preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
}

.status-preview-chip {
  font-weight: 600;
  font-size: 1rem;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.status-preview-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* Modern Actions */
.dialog-modern-actions {
  padding: 24px 32px;
  background: linear-gradient(to bottom, rgba(var(--v-theme-surface), 0.5), rgba(var(--v-theme-surface), 0.8));
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modern-cancel-btn {
  border-radius: 12px;
  text-transform: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0 20px;
  height: 48px;
  transition: all 0.3s ease;
}

.modern-cancel-btn:hover {
  background: rgba(var(--v-theme-error), 0.08);
  transform: translateY(-1px);
}

.modern-save-btn {
  border-radius: 12px;
  text-transform: none;
  font-weight: 600;
  font-size: 1rem;
  padding: 0 28px;
  height: 48px;
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s ease;
}

.modern-save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(var(--v-theme-primary), 0.4);
}

/* Legacy Dialog Compatibility */
.dialog-card {
  border-radius: 16px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.dialog-header {
  background: rgba(var(--v-theme-primary), 0.05);
  padding: 24px 28px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  font-size: 1.35rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.dialog-content {
  padding: 28px;
}

.dialog-actions {
  padding: 20px 28px;
  background: rgba(var(--v-theme-surface), 0.5);
}

.form-field {
  margin-bottom: 12px;
}

.form-field :deep(.v-field__outline) {
  border-radius: 12px;
}

.form-field :deep(.v-field--focused .v-field__outline) {
  border-width: 2px;
}

.form-field :deep(.v-field__input) {
  font-size: 0.95rem;
  padding: 16px;
}

.form-field :deep(.v-field__prepend-inner) {
  padding-inline-start: 12px;
}

.scanner-btn {
  border-radius: 8px;
  min-width: 40px !important;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.scanner-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.cancel-btn {
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0 20px;
  height: 44px;
}

.save-btn {
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0 24px;
  height: 44px;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
}

/* === DARK MODE STYLES === */
.v-theme--dark .inventory-card {
  background: #1e293b;
  border: 1px solid #334155;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .modern-table {
  background: #1e293b;
}

.v-theme--dark .modern-table :deep(.v-data-table-header) {
  background: rgba(var(--v-theme-primary), 0.15);
}

.v-theme--dark .filter-card {
  background: rgba(30, 41, 59, 0.5);
  border-color: #334155;
}

.v-theme--dark .modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.08);
}

.v-theme--dark .dialog-card {
  background: #1e293b;
}

.v-theme--dark .dialog-header {
  background: rgba(var(--v-theme-primary), 0.15);
  border-bottom: 1px solid #334155;
}

.v-theme--dark .dialog-actions {
  background: rgba(#0f172a, 0.5);
}

.v-theme--dark .serial-code,
.v-theme--dark .mac-code {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
}

.v-theme--dark .mobile-inventory-card {
  background: #1e293b;
  border-color: #334155;
}

.v-theme--dark .mobile-inventory-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .mobile-mac-code {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
}

/* === DESKTOP OPTIMIZATIONS === */
@media (min-width: 1024px) {
  .inventory-container {
    padding: 40px 48px;
  }
  
  .page-title {
    font-size: 2.75rem;
  }
  
  .page-subtitle {
    font-size: 1.2rem;
  }
  
  .header-avatar {
    size: 64px;
  }
  
  .content-title {
    font-size: 2rem;
  }
  
  .content-subtitle {
    font-size: 1.1rem;
  }
  
  .tab-content {
    padding: 40px;
  }
  
  .modern-table :deep(.v-data-table-header th) {
    font-size: 1rem;
    padding: 24px 20px;
    height: 64px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 24px 20px;
    font-size: 0.95rem;
  }
  
  .status-chip {
    font-size: 0.9rem;
    padding: 10px 16px;
  }
  
  .status-preview-chip {
    font-size: 0.9rem;
    padding: 10px 16px;
  }
  
  .serial-code,
  .mac-code {
    padding: 8px 16px;
    font-size: 0.9rem;
  }
  
  .type-name {
    font-size: 0.95rem;
  }
  
  .no-data-wrapper {
    padding: 80px 32px;
  }
  
  .no-data-text {
    font-size: 1.1rem;
  }
}

@media (min-width: 1440px) {
  .inventory-container {
    padding: 48px 64px;
  }
  
  .page-title {
    font-size: 3rem;
  }
  
  .page-subtitle {
    font-size: 1.25rem;
  }
  
  .content-title {
    font-size: 2.125rem;
  }
  
  .content-subtitle {
    font-size: 1.125rem;
  }
  
  .tab-content {
    padding: 48px;
  }
  
  .modern-table :deep(.v-data-table-header th) {
    font-size: 1.05rem;
    padding: 28px 24px;
    height: 68px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 28px 24px;
    font-size: 1rem;
  }
  
  .status-chip {
    font-size: 0.95rem;
    padding: 12px 18px;
  }
  
  .status-preview-chip {
    font-size: 0.95rem;
    padding: 12px 18px;
  }
  
  .serial-code,
  .mac-code {
    padding: 10px 18px;
    font-size: 0.95rem;
  }
  
  .type-name {
    font-size: 1rem;
  }
}

/* === MOBILE CARD STYLING === */
/* Mobile Cards Container */
.mobile-cards-container {
  padding: 16px;
}

.mobile-inventory-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-outline-variant), 0.5);
}

.mobile-inventory-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-shadow), 0.15);
}

.mobile-inventory-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
  line-height: 1.2;
}

.mobile-mac-code {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 2px 6px;
  border-radius: 4px;
}

.mobile-status-chip {
  font-weight: 600;
  font-size: 0.8rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Mobile Inventory Details */
.mobile-inventory-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

/* Mobile Type Cards */
.mobile-type-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-outline-variant), 0.5);
}

.mobile-type-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-shadow), 0.15);
}

.mobile-type-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
  line-height: 1.2;
}

.mobile-type-chip {
  font-weight: 600;
  font-size: 0.8rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Mobile Status Cards */
.mobile-status-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-outline-variant), 0.5);
}

.mobile-status-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-shadow), 0.15);
}

.mobile-status-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
  line-height: 1.2;
}

.mobile-status-preview-chip {
  font-weight: 600;
  font-size: 0.8rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mobile-status-preview-section {
  padding: 16px;
  background: rgba(var(--v-theme-surface), 0.4);
  border: 1px solid rgba(var(--v-border-color), 0.08);
  border-radius: 12px;
  margin-top: 12px;
}

.preview-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
  margin-bottom: 8px;
}

.status-preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-display {
  font-weight: 600;
  font-size: 1rem;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.preview-display:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* Mobile History Cards */
.mobile-history-cards-container {
  padding: 16px;
}

.mobile-history-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-outline-variant), 0.5);
}

.mobile-history-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-shadow), 0.15);
}

.mobile-history-title {
  font-size: 1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 4px;
  line-height: 1.2;
}

.mobile-history-serial {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 2px 6px;
  border-radius: 4px;
  word-break: break-all;
}

.mobile-history-action-chip {
  font-weight: 600;
  font-size: 0.75rem;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mobile-history-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-outline-variant), 0.2);
}

.mobile-history-user-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.mobile-history-user-role {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-top: 2px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  font-size: 0.875rem;
  line-height: 1.4;
}

.detail-label {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-left: 8px;
  margin-right: 8px;
  min-width: 60px;
  flex-shrink: 0;
}

.detail-value {
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex: 1;
  word-break: break-word;
}

.text-truncate {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === RESPONSIVE DESIGN === */

/* Tablet (768px and below) */
@media (max-width: 768px) {
  .inventory-container {
    padding: 16px;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .page-subtitle {
    font-size: 0.9rem;
  }
  
  .content-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .content-title {
    font-size: 1.25rem;
  }
  
  .content-subtitle {
    font-size: 0.85rem;
  }
  
  .add-btn {
    width: 100%;
    height: 48px;
  }
  
  .tab-content {
    padding: 16px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 12px 8px;
  }
  
  .dialog-content {
    padding: 20px;
  }
  
  /* Hide some columns on mobile */
  .modern-table :deep(.v-data-table__th:nth-child(2)),
  .modern-table :deep(.v-data-table__td:nth-child(2)) {
    display: none;
  }

  /* Mobile Card Optimizations */
  .mobile-inventory-card {
    margin-bottom: 16px;
  }

  .mobile-inventory-card .v-card-text {
    padding: 16px !important;
  }

  .mobile-inventory-title {
    font-size: 1rem;
  }

  .detail-row {
    font-size: 0.8rem;
  }

  .detail-label {
    min-width: 55px;
    font-size: 0.8rem;
  }

  .mobile-status-chip {
    font-size: 0.75rem;
  }
}

/* Mobile (600px and below) */
@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-avatar {
    margin-right: 0;
    margin-bottom: 8px;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 0.85rem;
  }
  
  .tab-text {
    display: none;
  }
  
  .modern-tabs :deep(.v-tab) {
    min-width: 80px;
    padding: 0 12px;
  }
  
  .content-title {
    font-size: 1.1rem;
  }
  
  .content-subtitle {
    font-size: 0.8rem;
  }
  
  .btn-text {
    display: none;
  }
  
  .add-btn {
    min-width: 56px;
    width: auto;
    padding: 0 16px;
  }
  
  /* Further hide columns on small mobile */
  .modern-table :deep(.v-data-table__th:nth-child(3)),
  .modern-table :deep(.v-data-table__td:nth-child(3)) {
    display: none;
  }

  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }

  /* Extra small mobile card optimizations */
  .mobile-inventory-title {
    font-size: 0.95rem;
  }

  .mobile-mac-code {
    font-size: 0.75rem;
  }

  .detail-row {
    font-size: 0.75rem;
  }

  .detail-label {
    min-width: 50px;
    font-size: 0.75rem;
  }

  .mobile-status-chip {
    font-size: 0.7rem;
  }
}

/* Small Mobile (480px and below) */
@media (max-width: 480px) {
  .inventory-container {
    padding: 12px;
  }
  
  .page-header {
    margin-bottom: 20px;
  }
  
  .page-title {
    font-size: 1.35rem;
  }
  
  .tab-content {
    padding: 12px;
  }
  
  .content-header {
    gap: 12px;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 8px 6px;
    font-size: 0.85rem;
  }
  
  .dialog-content {
    padding: 16px;
  }
  
  .dialog-header {
    padding: 16px 20px;
    font-size: 1.1rem;
  }
  
  .dialog-actions {
    padding: 12px 20px;
  }
}

/* Extra Small Mobile (360px and below) */
@media (max-width: 360px) {
  .inventory-container {
    padding: 8px;
  }
  
  .page-title {
    font-size: 1.25rem;
  }
  
  .page-subtitle {
    font-size: 0.8rem;
  }
  
  .tab-content {
    padding: 8px;
  }
  
  .content-title {
    font-size: 1rem;
  }
  
  .modern-table :deep(.v-data-table__td) {
    padding: 6px 4px;
    font-size: 0.8rem;
  }
  
  /* Show only essential columns on very small screens */
  .modern-table :deep(.v-data-table__th:nth-child(4)),
  .modern-table :deep(.v-data-table__td:nth-child(4)),
  .modern-table :deep(.v-data-table__th:nth-child(5)),
  .modern-table :deep(.v-data-table__td:nth-child(5)) {
    display: none;
  }

  /* Extra small mobile card optimizations */
  .mobile-inventory-title {
    font-size: 0.9rem;
  }

  .mobile-mac-code {
    font-size: 0.7rem;
    padding: 1px 4px;
  }

  .detail-row {
    font-size: 0.7rem;
  }

  .detail-label {
    min-width: 45px;
    font-size: 0.7rem;
  }

  .mobile-status-chip {
    font-size: 0.65rem;
  }

  .text-truncate {
    max-width: 150px;
  }
}

/* === ANIMATIONS === */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tab-content {
  animation: fadeIn 0.4s ease-out;
}

.status-chip {
  transition: all 0.3s ease;
}

.status-chip:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* === LIGHT/DARK MODE TRANSITIONS === */
.inventory-card,
.dialog-card,
.modern-table,
.form-field,
.status-chip,
.serial-code,
.mac-code {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* === ENHANCED FOCUS STATES === */
.form-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.action-btn:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

/* === LOADING STATES === */
.modern-table :deep(.v-skeleton-loader) {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
}

/* === IMPROVED ACCESSIBILITY === */
.action-btn {
  min-width: 40px;
  min-height: 40px;
}

.tab-item {
  min-height: 48px;
}

/* === HISTORY DIALOG STYLES === */

/* Device Info Card */
.device-info-card {
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, rgba(var(--v-theme-secondary), 0.05) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  overflow: hidden;
}

.device-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.device-avatar-wrapper {
  position: relative;
}

.elevated-avatar {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
  border: 3px solid white;
}

.device-info {
  flex: 1;
}

.device-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
  letter-spacing: -0.5px;
}

.device-subtitle {
  font-size: 0.9rem;
  font-weight: 500;
  opacity: 0.8;
}

.status-chip-large {
  font-weight: 600;
  font-size: 0.9rem;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Device Details Grid */
.device-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(var(--v-theme-surface), 0.6);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
  transform: translateY(-1px);
}

.detail-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.1);
  flex-shrink: 0;
}

.detail-content {
  flex: 1;
  min-width: 0;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  word-break: break-word;
}

/* History Section */
.history-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 20px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
}

.section-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  font-size: 24px;
  opacity: 0.8;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
}

.section-subtitle {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

/* Enhanced Table Cells */
.timestamp-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timestamp-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.1);
  flex-shrink: 0;
}

.timestamp-content {
  flex: 1;
}

.timestamp-date {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
}

.timestamp-time {
  font-size: 0.75rem;
  font-weight: 400;
}

.action-cell {
  min-width: 180px;
}

.action-type-chip {
  font-weight: 500;
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.action-details {
  line-height: 1.3;
  word-break: break-word;
  font-size: 0.7rem;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 150px;
}

.user-avatar {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  border: 2px solid white;
}

.user-content {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.user-role {
  font-size: 0.7rem;
  line-height: 1.2;
}

/* History Table Specific */
.history-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.03) !important;
}

.history-table :deep(.v-data-table__td) {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.3) !important;
  padding: 16px 12px !important;
  vertical-align: top;
}

/* Legacy compatibility */
.timestamp-wrapper {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
}

.action-wrapper {
  min-width: 200px;
}

.action-chip {
  font-weight: 500;
  font-size: 0.75rem;
  margin-bottom: 2px;
}

.user-wrapper {
  display: flex;
  align-items: center;
}

/* === PRINT STYLES === */
@media print {
  .add-btn,
  .action-buttons,
  .modern-tabs {
    display: none !important;
  }

  .inventory-card {
    box-shadow: none;
    border: 1px solid #ccc;
  }

  .page-title {
    color: #000 !important;
  }
}
</style>