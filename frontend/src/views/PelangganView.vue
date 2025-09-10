<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="header-card mb-4 mb-md-6">
      <div class="d-flex flex-column align-center gap-4">
        <div class="d-flex align-center header-info">
          <div class="header-avatar-wrapper">
            <v-avatar class="header-avatar" color="transparent" size="50">
              <v-icon color="white" size="28">mdi-account-group</v-icon>
            </v-avatar>
          </div>
          <div class="ml-4">
            <h1 class="header-title">Data Pelanggan</h1>
            <p class="header-subtitle">Kelola semua data pelanggan Anda dengan mudah</p>
          </div>
        </div>
        
        <!-- Mobile Action Buttons -->
        <div class="action-buttons-container">
          <v-btn
            color="success"
            @click="dialogImport = true"
            prepend-icon="mdi-file-upload-outline"
            class="action-btn text-none mobile-btn"
            size="default"
            block
          >
            Import Data
          </v-btn>
          <v-btn
            color="primary"
            @click="exportToCsv"
            :loading="exporting"
            prepend-icon="mdi-file-download-outline"
            class="action-btn text-none mobile-btn"
            size="default"
            block
          >
            Export Data
          </v-btn>
          <v-btn 
            color="primary" 
            @click="openDialog()" 
            prepend-icon="mdi-account-plus" 
            class="primary-btn text-none mobile-btn" 
            size="default"
            block
            elevation="3"
          >
            Tambah Pelanggan
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Filter Card - Mobile Optimized -->
    <v-card class="filter-card mb-4 mb-md-6" elevation="0">
      <div class="pa-4">
        <!-- Search Field -->
        <v-text-field
          v-model="searchQuery"
          label="Cari Pelanggan (Nama, Email, No. Telp)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          class="mb-3"
        ></v-text-field>

        <!-- Filter Row -->
        <div class="d-flex flex-column flex-sm-row gap-3 mb-3">
          <v-select
            v-model="selectedAlamat"
            :items="alamatOptions"
            label="Filter Alamat"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
            class="flex-grow-1"
          ></v-select>

          <v-select
            v-model="selectedBrand"
            :items="hargaLayananList"
            item-title="brand"
            item-value="id_brand"
            label="Filter Brand"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
            class="flex-grow-1"
          ></v-select>
        </div>
        
        <!-- Reset Button -->
        <v-btn
          variant="text"
          @click="resetFilters"
          class="text-none"
          block
        >
          Reset Filter
        </v-btn>
      </div>
    </v-card>

    <!-- Data Table Card -->
    <v-card class="data-table-card" elevation="0">
      <div class="card-header">
        <div class="d-flex align-center">
          <div class="header-icon-wrapper">
            <v-icon color="primary" size="20">mdi-format-list-bulleted-square</v-icon>
          </div>
          <span class="card-title ml-3">Daftar Pelanggan</span>
        </div>
        <v-chip color="primary" variant="tonal" size="small" class="count-chip">
          <v-icon start size="small">mdi-account-multiple</v-icon>
          {{ pelangganList.length }}
        </v-chip>
      </div>
      
      <v-expand-transition>
        <div v-if="selectedPelanggan.length > 0" class="selection-toolbar">
          <span class="font-weight-bold text-primary">{{ selectedPelanggan.length }} pelanggan terpilih</span>
          <v-spacer></v-spacer>
          <v-btn 
            color="error" 
            variant="tonal" 
            prepend-icon="mdi-delete-sweep"
            @click="deleteSelectedPelanggan"
            size="small"
          >
            <span class="d-none d-sm-inline">Hapus Terpilih</span>
            <span class="d-inline d-sm-none">Hapus</span>
          </v-btn>
        </div>
      </v-expand-transition>

      <div class="d-block d-md-none">
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular color="primary" indeterminate size="48"></v-progress-circular>
          <p class="mt-4 text-medium-emphasis">Memuat data pelanggan...</p>
        </div>
        
        <div v-else-if="pelangganList.length === 0" class="no-data-wrapper">
          <v-icon size="64" color="surface-variant">mdi-account-off</v-icon>
          <div class="no-data-text">Belum ada data pelanggan</div>
          <p class="text-medium-emphasis mt-2">Mulai dengan menambahkan pelanggan pertama Anda</p>
          <v-btn 
            color="primary" 
            variant="elevated" 
            @click="openDialog()" 
            class="mt-6 text-none"
            prepend-icon="mdi-account-plus"
          >
            Tambah Pelanggan
          </v-btn>
        </div>

        <div v-else class="mobile-cards-container">
          <v-card
            v-for="item in pelangganList"
            :key="item.id"
            class="mobile-customer-card mb-3"
            elevation="2"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-checkbox
                  v-model="selectedPelanggan"
                  :value="item"
                  hide-details
                  class="me-3"
                ></v-checkbox>
                <div class="flex-grow-1">
                  <h3 class="mobile-customer-name">{{ item.nama }}</h3>
                  <p class="mobile-customer-email text-medium-emphasis">{{ item.email }}</p>
                </div>
              </div>

              <!-- Customer Details -->
              <div class="mobile-details">
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-card-account-details</v-icon>
                  <span class="detail-label">No. KTP:</span>
                  <span class="detail-value">{{ item.no_ktp }}</span>
                </div>
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-map-marker</v-icon>
                  <span class="detail-label">Alamat:</span>
                  <span class="detail-value">{{ item.alamat }}</span>
                </div>
                <div v-if="item.alamat_2" class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-map-marker-outline</v-icon>
                  <span class="detail-label">Alamat 2:</span>
                  <span class="detail-value">{{ item.alamat_2 }}</span>
                </div>
                 <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-home-variant</v-icon>
                  <span class="detail-label">Blok/Unit:</span>
                  <span class="detail-value">{{ item.blok }} / {{ item.unit }}</span>
                </div>
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-phone</v-icon>
                  <span class="detail-label">Telepon:</span>
                  <span class="detail-value">{{ item.no_telp }}</span>
                </div>
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-wifi</v-icon>
                  <span class="detail-label">Layanan:</span>
                  <span class="detail-value">{{ item.layanan }}</span>
                </div>
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-domain</v-icon>
                  <span class="detail-label">Brand:</span>
                  <v-chip v-if="item.harga_layanan"
                    size="small"
                    :color="getBrandChipColor(item.harga_layanan?.brand || '')"
                    variant="tonal"
                    class="ml-2"
                  >
                    {{ item.harga_layanan?.brand || 'N/A' }}
                  </v-chip>
                </div>
                <div class="detail-row">
                  <v-icon size="small" class="me-2 text-medium-emphasis">mdi-calendar</v-icon>
                  <span class="detail-label">Instalasi:</span>
                  <span class="detail-value">{{ formatDate(item.tgl_instalasi) }}</span>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="d-flex gap-2 mt-4">
                <v-btn 
                  size="small" 
                  variant="tonal" 
                  color="primary" 
                  @click="openDialog(item)" 
                  prepend-icon="mdi-pencil"
                  class="flex-grow-1"
                >
                  Edit
                </v-btn>
                <v-btn 
                  size="small" 
                  variant="tonal" 
                  color="error" 
                  @click="openDeleteDialog(item)" 
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

      <!-- Desktop Table -->
      <div class="d-none d-md-block table-container">
        <v-data-table
          v-model="selectedPelanggan"
          :headers="headers"
          :items="pelangganList"
          :loading="loading"
          item-value="id"
          class="elegant-table"
          :items-per-page="10"
          :items-per-page-options="[5, 10, 25, 50]"
          hover
          show-select
          return-object
        >
        <template v-slot:loading>
            <div class="d-flex justify-center align-center py-12">
              <div class="text-center">
                <v-progress-circular color="primary" indeterminate size="48"></v-progress-circular>
                <p class="mt-4 text-medium-emphasis">Memuat data pelanggan...</p>
              </div>
            </div>
          </template>
          
          <template v-slot:item.nama="{ item }">
            <div class="customer-info">
              <div class="customer-name">{{ item.nama }}</div>
            </div>
          </template>
                    
          <template v-slot:item.id_brand="{ item }">
            <v-chip v-if="item.harga_layanan"
              size="small"
              :color="getBrandChipColor(item.harga_layanan?.brand || '')"
              variant="tonal"
              class="brand-chip"
            >
              <v-icon start size="small">mdi-wifi</v-icon>
              {{ item.harga_layanan?.brand || 'N/A' }}
            </v-chip>
          </template>
          
          <template v-slot:item.tgl_instalasi="{ item }">
            <div class="date-cell">
              <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
              {{ formatDate(item.tgl_instalasi) }}
            </div>
          </template>
          
          <template v-slot:item.actions="{ item }">
            <div class="action-buttons">
              <v-btn 
                size="small" 
                variant="tonal" 
                color="primary" 
                @click="openDialog(item)" 
                icon="mdi-pencil"
                class="action-btn-small"
              ></v-btn>
              <v-btn 
                size="small" 
                variant="tonal" 
                color="error" 
                @click="openDeleteDialog(item)" 
                icon="mdi-delete"
                class="action-btn-small"
              ></v-btn>
            </div>
          </template>
          
          <template v-slot:no-data>
            <div class="no-data-wrapper">
              <v-icon size="64" color="surface-variant">mdi-account-off</v-icon>
              <div class="no-data-text">Belum ada data pelanggan</div>
              <p class="text-medium-emphasis mt-2">Mulai dengan menambahkan pelanggan pertama Anda</p>
              <v-btn 
                color="primary" 
                variant="elevated" 
                @click="openDialog()" 
                class="mt-6 text-none"
                prepend-icon="mdi-account-plus"
              >
                Tambah Pelanggan
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </div>
    </v-card>

    <!-- Dialogs (unchanged) -->
    <v-dialog v-model="dialog" max-width="1000px" :fullscreen="$vuetify.display.mobile" persistent class="form-dialog">
      <v-card class="form-card">
        <div class="form-header">
          <div class="form-header-content">
            <v-icon class="mr-3" size="24">mdi-account-edit</v-icon>
            <span class="form-title">{{ formTitle }}</span>
          </div>
          <v-btn 
            v-if="$vuetify.display.mobile"
            icon 
            variant="text" 
            @click="closeDialog"
            class="mobile-close-btn"
          >
            <v-icon color="white">mdi-close</v-icon>
          </v-btn>
        </div>
        
        <v-card-text class="form-content">
          <v-form ref="form" v-model="isFormValid">
            <v-stepper v-model="currentStep" flat class="elegant-stepper" :mobile="$vuetify.display.mobile">
              <v-stepper-header class="stepper-header">
                <v-stepper-item 
                  title="Info Pribadi" 
                  :value="1" 
                  :complete="currentStep > 1" 
                  color="primary"
                ></v-stepper-item>
                <v-divider class="stepper-divider"></v-divider>
                <v-stepper-item 
                  title="Alamat & Layanan" 
                  :value="2" 
                  color="primary"
                ></v-stepper-item>
              </v-stepper-header>
              
              <v-stepper-window class="stepper-content">
                <v-stepper-window-item :value="1" class="step-content">
                  <div class="step-header">
                    <h3 class="step-title">Informasi Pribadi</h3>
                    <p class="step-subtitle">Masukkan data pribadi pelanggan dengan lengkap</p>
                  </div>
                  
                  <v-row class="form-row">
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-account</v-icon>
                          Nama Lengkap
                        </label>
                        <v-text-field 
                          v-model="editedItem.nama" 
                          :rules="[rules.required]" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-card-account-details</v-icon>
                          Nomor KTP
                        </label>
                        <v-text-field 
                          v-model="editedItem.no_ktp" 
                          :rules="[rules.required, rules.ktp]" 
                          variant="outlined" 
                          counter="16"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-email</v-icon>
                          Email
                        </label>
                        <v-text-field 
                          v-model="editedItem.email" 
                          :rules="[rules.required, rules.email]" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-phone</v-icon>
                          Nomor Telepon
                        </label>
                        <v-text-field 
                          v-model="editedItem.no_telp" 
                          :rules="[rules.required, rules.phone]" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                  </v-row>
                </v-stepper-window-item>
                
                <v-stepper-window-item :value="2" class="step-content">
                  <div class="step-header">
                    <h3 class="step-title">Alamat & Layanan</h3>
                    <p class="step-subtitle">Lengkapi informasi alamat dan layanan pelanggan</p>
                  </div>
                  
                  <v-row class="form-row">
                    <v-col cols="12">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-map-marker</v-icon>
                          Alamat Utama
                        </label>
                        <v-combobox
                          v-model="editedItem.alamat"
                          :items="alamatOptions"
                          :rules="[rules.required]"
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                          placeholder="Pilih atau ketik alamat"
                        ></v-combobox>
                        </div>
                    </v-col>
                    <v-col cols="12">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-map-marker-outline</v-icon>
                          Alamat Tambahan (Opsional)
                        </label>
                        <v-text-field 
                          v-model="editedItem.alamat_2" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-home-variant</v-icon>
                          Blok
                        </label>
                        <v-text-field 
                          v-model="editedItem.blok" 
                          :rules="[rules.required]" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-door</v-icon>
                          Unit
                        </label>
                        <v-text-field 
                          v-model="editedItem.unit" 
                          :rules="[rules.required]" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="4">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-calendar</v-icon>
                          Tanggal Instalasi
                        </label>
                        <v-text-field 
                          v-model="editedItem.tgl_instalasi" 
                          type="date" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-text-field>
                      </div>
                    </v-col>
                    <v-col cols="12" md="4">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-wifi</v-icon>
                          Layanan
                        </label>
                        <v-select
                          v-model="editedItem.layanan"
                          :items="layananOptions"
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-select>
                      </div>
                    </v-col>
                    <v-col cols="12" md="4">
                      <div class="input-group">
                        <label class="input-label">
                          <v-icon size="small" class="mr-2">mdi-domain</v-icon>
                          Brand Provider
                        </label>
                        <v-select 
                          v-model="editedItem.id_brand" 
                          :items="hargaLayananList" 
                          item-title="brand" 
                          item-value="id_brand" 
                          variant="outlined"
                          class="elegant-input"
                          density="comfortable"
                        ></v-select>
                      </div>
                    </v-col>
                  </v-row>
                </v-stepper-window-item>
              </v-stepper-window>
            </v-stepper>
          </v-form>
        </v-card-text>
        
        <v-card-actions class="form-actions">
          <v-btn 
            v-if="currentStep > 1" 
            @click="currentStep--" 
            variant="text"
            class="nav-btn"
            prepend-icon="mdi-arrow-left"
          >
            Kembali
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn 
            v-if="!$vuetify.display.mobile"
            @click="closeDialog" 
            variant="text" 
            class="nav-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            v-if="currentStep < 2" 
            @click="currentStep++" 
            color="primary"
            class="nav-btn"
            append-icon="mdi-arrow-right"
          >
            Lanjut
          </v-btn>
          <v-btn 
            v-else 
            @click="savePelanggan" 
            :loading="saving" 
            :disabled="!isFormValid" 
            color="primary" 
            variant="elevated"
            class="save-btn"
            prepend-icon="mdi-content-save"
          >
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px" class="delete-dialog">
      <v-card class="delete-card">
        <div class="delete-header">
          <v-icon class="mr-3">mdi-delete-alert</v-icon>
          <span class="delete-title">Konfirmasi Hapus</span>
        </div>
        
        <v-card-text class="delete-content">
          <div class="delete-message">
            <v-icon size="72" color="warning" class="mb-4">mdi-alert-circle-outline</v-icon>
            <p class="delete-text">
              Anda yakin ingin menghapus pelanggan 
              <strong class="customer-name-delete">{{ itemToDelete?.nama }}</strong>?
            </p>
            <p class="delete-warning">Tindakan ini tidak dapat dibatalkan!</p>
          </div>
        </v-card-text>
        
        <v-card-actions class="delete-actions">
          <v-spacer></v-spacer>
          <v-btn 
            @click="closeDeleteDialog" 
            variant="text"
            class="cancel-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            @click="confirmDelete"  
            :loading="deleting" 
            color="error" 
            variant="elevated"
            class="delete-btn"
            prepend-icon="mdi-delete"
          >
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bulk Delete Dialog -->
    <v-dialog v-model="dialogBulkDelete" max-width="500px" class="delete-dialog">
      <v-card class="delete-card">
        <div class="delete-header">
          <v-icon class="mr-3">mdi-delete-sweep-outline</v-icon>
          <span class="delete-title">Konfirmasi Hapus Massal</span>
        </div>

        <v-card-text class="delete-content">
          <div class="delete-message">
            <v-icon size="72" color="warning" class="mb-4">mdi-alert-circle-outline</v-icon>
            <p class="delete-text">
              Anda yakin ingin menghapus 
              <strong>{{ selectedPelanggan.length }} pelanggan</strong> yang dipilih?
            </p>
            <p class="delete-warning">Tindakan ini tidak dapat dibatalkan!</p>
          </div>
        </v-card-text>

        <v-card-actions class="delete-actions">
          <v-spacer></v-spacer>
            <v-btn 
              @click="dialogBulkDelete = false" 
              variant="text"
              class="cancel-btn"
            >
              Batal
            </v-btn>
            <v-btn
              @click="confirmBulkDelete"
              :loading="deleting"
              color="error"
              variant="elevated"
              class="delete-btn"
              prepend-icon="mdi-delete"
            >
              Ya, Hapus
            </v-btn>
          </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- Import Dialog -->
    <v-dialog v-model="dialogImport" max-width="800px" :fullscreen="$vuetify.display.mobile" persistent class="import-dialog">
      <v-card class="import-card">
        <div class="import-header">
          <v-icon class="mr-3">mdi-upload</v-icon>
          <span class="import-title">Import Pelanggan dari CSV</span>
          <v-spacer></v-spacer>
          <v-btn 
            icon 
            variant="text" 
            @click="closeImportDialog"
            size="small"
          >
            <v-icon color="white">mdi-close</v-icon>
          </v-btn>
        </div>
        
        <v-card-text class="import-content">
          <v-sheet 
            border 
            rounded="lg" 
            class="template-card pa-4 mb-6"
            color="surface-variant"
          >
            <div class="d-flex flex-column flex-sm-row align-center gap-4">
              <div class="template-icon">
                <v-icon color="success" size="32">mdi-file-document-outline</v-icon>
              </div>
              <div class="flex-grow-1 text-center text-sm-left">
                <div class="template-title">Gunakan Template Kami</div>
                <p class="template-subtitle">
                  Unduh template CSV untuk memastikan format data sesuai dengan sistem.
                </p>
              </div>
              <v-btn 
                color="success" 
                variant="elevated" 
                @click="downloadCsvTemplate" 
                :loading="downloadingTemplate" 
                prepend-icon="mdi-download" 
                class="template-btn"
                :block="$vuetify.display.mobile"
              >
                Unduh Template
              </v-btn>
            </div>
          </v-sheet>

          <div class="mb-4">
            <h6 class="text-h6 mb-3 d-flex align-center upload-title">
              <v-icon class="mr-2">mdi-cloud-upload</v-icon>
              Unggah File CSV
            </h6>
            <v-file-input 
              :model-value="fileToImport"
              @update:model-value="handleFileSelection"
              label="Pilih file .csv" 
              accept=".csv" 
              variant="outlined" 
              prepend-icon="" 
              prepend-inner-icon="mdi-paperclip" 
              show-size 
              clearable 
              hide-details="auto"
              class="file-input"
              density="comfortable"
            >
            </v-file-input>
          </div>

          <v-expand-transition>
            <div v-if="importErrors.length > 0" class="mt-4">
              <v-alert 
                type="error" 
                variant="tonal" 
                prominent 
                border="start"
                class="error-alert"
              >
                <template v-slot:title>
                  <div class="d-flex justify-space-between align-center">
                    <span>Import Gagal</span>
                    <v-chip color="error" size="small">
                      {{ importErrors.length }} Kesalahan
                    </v-chip>
                  </div>
                </template>
                
                <p class="mb-3">Mohon perbaiki kesalahan berikut di file CSV Anda dan coba lagi.</p>
                <v-divider class="mb-3"></v-divider>
                
                <div class="error-list">
                  <div 
                    v-for="(error, i) in importErrors" 
                    :key="i" 
                    class="error-item d-flex align-start mb-2"
                  >
                    <v-icon size="small" color="error" class="mr-2 mt-1">mdi-alert-circle</v-icon>
                    <span class="text-body-2">{{ error }}</span>
                  </div>
                </div>
              </v-alert>
            </div>
          </v-expand-transition>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="import-actions">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            @click="closeImportDialog"
            class="nav-btn"
          >
            Batal
          </v-btn>
          <v-btn 
            color="success" 
            variant="elevated" 
            @click="importFromCsv" 
            :loading="importing" 
            :disabled="fileToImport.length === 0" 
            prepend-icon="mdi-upload" 
            class="import-btn"
          >
            Import Sekarang
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar 
      v-model="snackbar.show" 
      :color="snackbar.color" 
      :timeout="4000" 
      location="top right"
      class="enhanced-snackbar"
    >
      <div class="d-flex align-center">
        <v-icon class="mr-2">
          {{ snackbar.color === 'success' ? 'mdi-check-circle' : 
             snackbar.color === 'error' ? 'mdi-alert-circle' : 'mdi-information' }}
        </v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import apiClient from '@/services/api';
import type { Pelanggan as BasePelanggan } from '@/interfaces/pelanggan';
import { debounce } from 'lodash-es';

// --- INTERFACES ---
interface HargaLayanan {
  id_brand: string;
  brand: string;
}
interface Pelanggan extends BasePelanggan {
  alamat_2?: string | null;
  id_brand?: string | null;
  harga_layanan?: HargaLayanan | null;
}

// --- STATE MANAGEMENT ---
const pelangganList = ref<Pelanggan[]>([]);
const hargaLayananList = ref<HargaLayanan[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const dialogBulkDelete = ref(false);
const editedIndex = ref(-1);
const currentStep = ref(1);
const isFormValid = ref(false);
const selectedPelanggan = ref<any[]>([]);

const dialogImport = ref(false);
const importing = ref(false);
const exporting = ref(false);
const downloadingTemplate = ref(false);
const fileToImport = ref<File[]>([]);
const importErrors = ref<string[]>([]);

const searchQuery = ref('');
const selectedAlamat = ref<string | null>(null);
const selectedBrand = ref<string | null>(null);

const defaultItem: Partial<Pelanggan> = { 
  id: undefined, 
  nama: '', 
  no_ktp: '', 
  email: '', 
  no_telp: '', 
  layanan: '',
  alamat: '', 
  blok: '', 
  unit: '', 
  tgl_instalasi: new Date().toISOString().split('T')[0], 
  alamat_2: '',
  id_brand: null
};
const editedItem = ref<Partial<Pelanggan>>({ ...defaultItem });
const itemToDelete = ref<Pelanggan | null>(null);
const snackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' | 'warning' });

const alamatOptions = ref([
  'Tambun',
  'Rusun Pinus Elok',
  'Luar Pinus Elok',
  'Rusun Pulogebang',
  'Rusun Cakung KM2',
  'Rusun Tipar Cakung',
  'Rusun Albo',
  'Rusun Nagrak',
  'Waringin',
  'Parama'
]);

const layananOptions = ref([
  'Internet 10 Mbps',
  'Internet 20 Mbps',
  'Internet 30 Mbps',
  'Internet 50 Mbps'
]);

// --- VALIDATION RULES ---
const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi',
  email: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Format email tidak valid',
  phone: (value: string) => /^[\+]?[0-9\s\-\(\)]{10,}$/.test(value) || 'Format nomor telepon tidak valid',
  ktp: (value: string) => (value && value.length === 16 && /^[0-9]+$/.test(value)) || 'Nomor KTP harus 16 digit angka',
};

// --- TABLE HEADERS ---
const headers = [
  { title: 'Pelanggan', key: 'nama', sortable: true, minWidth: '160px' },
  { title: 'No. KTP', key: 'no_ktp', sortable: true },
  { title: 'Email', key: 'email', sortable: true },
  { title: 'Alamat', key: 'alamat', sortable: false },
  { title: 'Alamat Tambahan', key: 'alamat_2', sortable: false },
  { title: 'Blok', key: 'blok', sortable: false },
  { title: 'Unit', key: 'unit', sortable: false },
  { title: 'No. Telepon', key: 'no_telp', sortable: false },
  { title: 'Layanan', key: 'layanan', sortable: false },
  { title: 'Brand', key: 'id_brand', sortable: true },
  { title: 'Tgl Instalasi', key: 'tgl_instalasi', align: 'center', sortable: true },
  { title: 'Aksi', key: 'actions', sortable: false, align: 'center', width: '120px' },
] as const;

// --- COMPUTED PROPERTIES ---
const formTitle = computed(() => editedIndex.value === -1 ? 'Tambah Pelanggan Baru' : 'Edit Pelanggan');

// --- LIFECYCLE HOOK ---
onMounted(() => {
  fetchPelanggan();
  fetchHargaLayanan();
});

// --- DELETE FUNCTIONS ---
function deleteSelectedPelanggan() {
  if (selectedPelanggan.value.length === 0) {
    showSnackbar('Tidak ada pelanggan yang dipilih.', 'warning');
    return;
  }
  dialogBulkDelete.value = true;
}

async function confirmBulkDelete() {
  const itemsToDelete = [...selectedPelanggan.value];
  deleting.value = true;

  try {
    const deletePromises = itemsToDelete.map(pelanggan =>
      apiClient.delete(`/pelanggan/${pelanggan.id}`)
    );

    await Promise.all(deletePromises);
    showSnackbar(`${itemsToDelete.length} pelanggan berhasil dihapus.`, 'success');
    await fetchPelanggan();
    selectedPelanggan.value = [];

  } catch (error) {
    console.error("Gagal melakukan hapus massal:", error);
    showSnackbar('Terjadi kesalahan saat menghapus data.', 'error');
  } finally {
    deleting.value = false;
    dialogBulkDelete.value = false;
  }
}

// --- CRUD METHODS ---
async function fetchPelanggan() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    if (selectedAlamat.value) {
      params.append('alamat', selectedAlamat.value);
    }
    if (selectedBrand.value) {
      params.append('id_brand', selectedBrand.value);
    }

    const response = await apiClient.get(`/pelanggan/?${params.toString()}`);
    pelangganList.value = response.data;
  } catch (error) { 
    console.error("Gagal mengambil data pelanggan:", error);
    showSnackbar('Gagal mengambil data pelanggan', 'error');
  } finally { 
    loading.value = false; 
  }
}

const applyFilters = debounce(() => {
  fetchPelanggan();
}, 500);

watch([searchQuery, selectedAlamat, selectedBrand], () => {
  applyFilters();
});

function resetFilters() {
  searchQuery.value = '';
  selectedAlamat.value = null;
  selectedBrand.value = null;
}

function handleFileSelection(newFiles: File | File[]) {
  importErrors.value = [];

  if (Array.isArray(newFiles)) {
    fileToImport.value = newFiles;
  } else if (newFiles) {
    fileToImport.value = [newFiles];
  } else {
    fileToImport.value = [];
  }
}

async function fetchHargaLayanan() {
  try {
    const response = await apiClient.get('/harga_layanan');
    hargaLayananList.value = response.data;
  } catch (error) { 
    console.error("Gagal mengambil data harga layanan:", error);
  }
}

function openDialog(item?: Pelanggan) {
  editedIndex.value = item ? pelangganList.value.findIndex(p => p.id === item.id) : -1;
  const targetItem = item ? { ...item } : { ...defaultItem };
  if (targetItem.tgl_instalasi) {
    targetItem.tgl_instalasi = new Date(targetItem.tgl_instalasi).toISOString().split('T')[0];
  }
  editedItem.value = targetItem;
  currentStep.value = 1;
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editedItem.value = { ...defaultItem };
  editedIndex.value = -1;
  currentStep.value = 1;
}

async function savePelanggan() {
  if (!isFormValid.value) return;
  saving.value = true;
  try {
    if (editedIndex.value > -1) {
      await apiClient.patch(`/pelanggan/${editedItem.value.id}`, editedItem.value);
      showSnackbar('Data pelanggan berhasil diperbarui', 'success');
    } else {
      await apiClient.post('/pelanggan/', editedItem.value);
      showSnackbar('Data pelanggan berhasil ditambahkan', 'success');
    }
    await fetchPelanggan();
    closeDialog();
  } catch (error) {
    console.error("Gagal menyimpan data pelanggan:", error);
    showSnackbar('Gagal menyimpan data pelanggan', 'error');
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: Pelanggan) {
  itemToDelete.value = item;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  itemToDelete.value = null;
}

async function confirmDelete() {
  if (!itemToDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/pelanggan/${itemToDelete.value.id}`);
    await fetchPelanggan();
    showSnackbar('Data pelanggan berhasil dihapus', 'success');
    closeDeleteDialog();
  } catch (error) {
    console.error("Gagal menghapus data pelanggan:", error);
    showSnackbar('Gagal menghapus data pelanggan', 'error');
  } finally {
    deleting.value = false;
  }
}

// --- IMPORT/EXPORT METHODS ---
function closeImportDialog() {
  dialogImport.value = false;
  importing.value = false;
  fileToImport.value = [];
  importErrors.value = [];
}

async function downloadCsvTemplate() {
  downloadingTemplate.value = true;
  try {
    const response = await apiClient.get('/pelanggan/template/csv', { responseType: 'blob' });
    downloadFile(response.data, 'template_import_pelanggan.csv');
  } catch (error) {
    console.error("Gagal mengunduh template:", error);
    showSnackbar('Gagal mengunduh template.', 'error');
  } finally {
    downloadingTemplate.value = false;
  }
}

async function exportToCsv() {
  exporting.value = true;
  try {
    const response = await apiClient.get('/pelanggan/export/csv', { responseType: 'blob' });
    const date = new Date().toISOString().split('T')[0];
    downloadFile(response.data, `export_pelanggan_${date}.csv`);
  } catch (error) {
    console.error("Gagal mengekspor data:", error);
    showSnackbar('Tidak ada data untuk diekspor atau terjadi kesalahan.', 'error');
  } finally {
    exporting.value = false;
  }
}

async function importFromCsv() {
  const file = fileToImport.value[0]; 

  if (!file) {
    showSnackbar('Silakan pilih file CSV terlebih dahulu.', 'warning');
    return;
  }

  importing.value = true;
  importErrors.value = []; // Selalu bersihkan error lama
  
  const formData = new FormData();
  formData.append('file', file); 
  
  try {
    const response = await apiClient.post('/pelanggan/import', formData);
    showSnackbar(response.data.message, 'success');
    await fetchPelanggan();
    closeImportDialog();

  } catch (error: any) {
    // ▼▼▼ UBAH BAGIAN CATCH INI ▼▼▼
    console.error("Gagal mengimpor data:", error);
    if (error.response?.data?.errors) {
      // Jika backend mengirimkan daftar error yang spesifik
      importErrors.value = error.response.data.errors;
    } else if (error.response?.data?.detail) {
      // Jika backend mengirimkan satu pesan error umum
      const detailMsg = error.response.data.detail;
      if (typeof detailMsg === 'string') {
        importErrors.value = [detailMsg];
      } else {
        importErrors.value = ["Terjadi kesalahan yang tidak diketahui."];
      }
    } else {
      // Fallback untuk error jaringan atau lainnya
      importErrors.value = ["Tidak dapat terhubung ke server atau terjadi error."];
    }
    // ▲▲▲ AKHIR PERUBAHAN ▲▲▲
  } finally {
    importing.value = false;
  }
}
// --- HELPER FUNCTIONS ---
function downloadFile(blobData: any, filename: string) {
  const url = window.URL.createObjectURL(new Blob([blobData]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

function getBrandChipColor(brandName: string): string {
  if (brandName.includes('JAKINET')) return 'blue';
  if (brandName.includes('JELANTIK')) return 'purple';
  if (brandName.includes('JELANTIK NAGRAK')) return 'emerald';
  return 'grey';
}

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

function showSnackbar(text: string, color: 'success' | 'error' | 'warning') {
  snackbar.value = { show: true, text, color };
}
</script>

<style scoped>
/* ============================================
   MOBILE-FIRST RESPONSIVE DESIGN
   ============================================ */

/* ============================================
   MOBILE-FIRST RESPONSIVE DESIGN - FIXED POSITIONING
   ============================================ */

/* Base Styles */
.modern-app {
  background-color: rgb(var(--v-theme-background));
  transition: background-color 0.3s ease;
}

/* Header Card - Mobile Optimized with Fixed Positioning */
.header-card {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  border-radius: 20px;
  padding: 24px;
  color: rgb(var(--v-theme-on-primary));
  box-shadow: 0 8px 32px rgba(var(--v-theme-primary), 0.25);
  position: relative;
}

.header-card .d-flex.flex-column {
  align-items: stretch !important; /* Changed from align-center to stretch */
}

.header-info {
  width: 100%;
  justify-content: flex-start;
  margin-bottom: 0; /* Reset margin */
}

.header-avatar-wrapper {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.header-title {
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 4px;
}

.header-subtitle {
  font-size: 0.95rem;
  opacity: 0.85;
  line-height: 1.3;
}

/* Action Buttons Container - Fixed Positioning */
.action-buttons-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-self: flex-end; /* Align to the right on desktop */
}

.mobile-btn {
  border-radius: 14px;
  font-weight: 600;
  height: 48px;
  transition: all 0.3s ease;
}

.action-btn {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  backdrop-filter: blur(5px);
}

.action-btn:hover {
  background-color: rgba(255, 255, 255, 0.25) !important;
  transform: translateY(-1px);
}

.primary-btn {
  background: white !important;
  color: rgb(var(--v-theme-primary)) !important;
}

/* Filter Card - Mobile Optimized */
.filter-card {
  border-radius: 16px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 12px rgba(var(--v-theme-shadow), 0.08);
}

/* Data Table Card */
.data-table-card {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgb(var(--v-theme-outline-variant));
  background: rgb(var(--v-theme-surface));
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant));
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.count-chip {
  font-size: 0.8rem;
}

/* Selection Toolbar */
.selection-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.15);
}

/* Mobile Cards Container */
.mobile-cards-container {
  padding: 16px;
}

.mobile-customer-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-outline-variant), 0.5);
}

.mobile-customer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-shadow), 0.15);
}

.mobile-customer-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 2px;
}

.mobile-customer-email {
  font-size: 0.85rem;
  margin: 0;
}

/* Mobile Details */
.mobile-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  line-height: 1.4;
}

.detail-label {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-left: 8px;
  margin-right: 8px;
  min-width: 70px;
}

.detail-value {
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex: 1;
}

/* Desktop Table Styles */
.elegant-table {
  background: transparent !important;
}

.elegant-table :deep(th) {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  opacity: 0.8;
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
}

.elegant-table :deep(td) {
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant)) !important;
}

.customer-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.customer-email {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn-small {
  min-width: 32px;
}

/* No Data State */
.no-data-wrapper {
  text-align: center;
  padding: 48px 24px;
}

.no-data-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-top: 16px;
}

/* Form Dialog - Mobile Optimized */
.form-card {
  border-radius: 20px;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
  border: 1px solid rgb(var(--v-theme-outline-variant));
}

.form-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  padding: 24px 28px;
  color: rgb(var(--v-theme-on-primary));
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-header-content {
  display: flex;
  align-items: center;
}

.form-title {
  font-size: 1.5rem;
  font-weight: 700;
}

.mobile-close-btn {
  color: white !important;
}

.form-content {
  padding: 28px !important;
  background: rgb(var(--v-theme-background));
}

.stepper-header, .stepper-content {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px solid rgb(var(--v-theme-outline-variant));
}

.stepper-header {
  margin-bottom: 20px;
  padding: 12px;
}

.stepper-content {
  padding: 24px;
}

.step-header {
  margin-bottom: 24px;
  text-align: center;
}

.step-title {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 700;
  font-size: 1.3rem;
  margin-bottom: 8px;
}

.step-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.95rem;
  line-height: 1.4;
}

.input-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.elegant-input :deep(.v-field) {
  border-radius: 12px;
  background: rgb(var(--v-theme-background));
}

.form-actions {
  padding: 20px 28px !important;
  border-top: 1px solid rgb(var(--v-theme-outline-variant));
  background: rgb(var(--v-theme-surface));
}

.nav-btn, .save-btn {
  border-radius: 12px;
  font-weight: 600;
  height: 44px;
  text-transform: none;
}

/* Delete Dialog */
.delete-card, .import-card {
  border-radius: 16px;
  background: rgb(var(--v-theme-surface));
}

.delete-header {
  background: rgb(var(--v-theme-error));
  color: rgb(var(--v-theme-on-error));
  padding: 20px 24px;
  display: flex;
  align-items: center;
}

.delete-title {
  font-size: 1.2rem;
  font-weight: 700;
}

.delete-content {
  padding: 28px !important;
  text-align: center;
}

.delete-message {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.delete-text {
  font-size: 1rem;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-on-surface));
}

.delete-warning {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
}

.customer-name-delete {
  color: rgb(var(--v-theme-error));
}

.delete-actions {
  padding: 16px 24px !important;
  border-top: 1px solid rgb(var(--v-theme-outline-variant));
}

.cancel-btn, .delete-btn {
  border-radius: 10px;
  font-weight: 600;
  text-transform: none;
}

/* Import Dialog */
.import-header {
  background: rgb(var(--v-theme-success));
  color: rgb(var(--v-theme-on-success));
  padding: 20px 24px;
  display: flex;
  align-items: center;
}

.import-title {
  font-size: 1.2rem;
  font-weight: 700;
}

.import-content {
  padding: 28px !important;
}

.template-card {
  border: 2px dashed rgba(var(--v-theme-success), 0.3);
  background: rgba(var(--v-theme-success), 0.05);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.template-card:hover {
  border-color: rgb(var(--v-theme-success));
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(var(--v-theme-success), 0.15);
}

.template-title, .upload-title {
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  font-size: 1rem;
}

.template-subtitle {
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.4;
  font-size: 0.9rem;
}

.file-input :deep(.v-field) {
  border: 2px dashed rgb(var(--v-theme-outline-variant)) !important;
  background: rgb(var(--v-theme-surface)) !important;
  border-radius: 12px;
  transition: all 0.2s ease-in-out;
}

.file-input :deep(.v-field:hover) {
  border-color: rgb(var(--v-theme-success)) !important;
  background: rgba(var(--v-theme-success), 0.05) !important;
}

.error-alert {
  border-radius: 12px;
}

.error-item {
  background: rgba(var(--v-theme-error), 0.05);
  border-radius: 8px;
  padding: 8px 12px;
}

.import-actions {
  padding: 16px 24px !important;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgb(var(--v-theme-outline-variant));
}

.import-btn {
  background: rgb(var(--v-theme-success)) !important;
  color: rgb(var(--v-theme-on-success)) !important;
  border-radius: 10px;
  font-weight: 600;
  text-transform: none;
}

.template-btn {
  border-radius: 10px;
  font-weight: 600;
  text-transform: none;
}

/* Snackbar */
.enhanced-snackbar {
  border-radius: 12px;
}

/* ============================================
   RESPONSIVE BREAKPOINTS - FIXED POSITIONING
   ============================================ */

/* Tablet (768px and up) */
@media (min-width: 768px) {
  .header-card {
    padding: 32px;
    border-radius: 24px;
  }

  /* FIXED: Header layout for desktop */
  .header-card .d-flex.flex-column {
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
  }

  .header-info {
    flex: 1;
    margin-right: 24px;
  }
  
  .header-title {
    font-size: 2.25rem;
  }
  
  .header-subtitle {
    font-size: 1.1rem;
  }
  
  .action-buttons-container {
    flex-direction: row;
    justify-content: flex-end;
    gap: 16px;
    width: auto;
    flex-shrink: 0;
    align-self: center; /* Center vertically with header info */
  }
  
  .mobile-btn {
    width: auto;
    min-width: 140px;
  }
  
  .card-header {
    padding: 24px 28px;
  }
  
  .card-title {
    font-size: 1.5rem;
  }
  
  .form-content {
    padding: 36px !important;
  }
  
  .stepper-content {
    padding: 32px;
  }
  
  .step-title {
    font-size: 1.5rem;
  }
  
  .step-subtitle {
    font-size: 1rem;
  }
  
  .template-card .d-flex {
    align-items: center;
  }
  
  .template-btn {
    width: auto;
  }
}

/* Large Desktop (1024px and up) */
@media (min-width: 1024px) {
  .filter-card {
    border-radius: 20px;
  }
  
  .filter-card .d-flex {
    flex-direction: row;
    align-items: center;
    gap: 20px;
  }
  
  .data-table-card {
    border-radius: 20px;
  }

  /* Enhanced button sizing for larger screens */
  .action-buttons-container {
    gap: 20px;
  }

  .mobile-btn {
    min-width: 160px;
    height: 52px;
    font-size: 0.95rem;
  }
}

/* Mobile Specific Adjustments */
@media (max-width: 767px) {
  .v-container {
    padding: 12px !important;
  }

  /* FIXED: Mobile header remains column layout */
  .header-card .d-flex.flex-column {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 20px;
  }

  .header-info {
    margin-right: 0;
  }
  
  .header-card {
    margin-bottom: 16px;
  }
  
  .filter-card {
    margin-bottom: 16px;
  }
  
  .card-header {
    padding: 16px 20px;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .card-title {
    font-size: 1.1rem;
  }
  
  .count-chip {
    align-self: flex-end;
  }
  
  .selection-toolbar {
    padding: 12px 20px;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .selection-toolbar .v-btn {
    width: 100%;
  }
  
  .mobile-cards-container {
    padding: 12px;
  }
  
  .mobile-customer-card {
    margin-bottom: 12px;
  }
  
  .mobile-customer-card .v-card-text {
    padding: 16px !important;
  }
  
  .mobile-customer-name {
    font-size: 1rem;
  }
  
  .detail-row {
    font-size: 0.8rem;
  }
  
  .detail-label {
    min-width: 60px;
    font-size: 0.8rem;
  }
  
  .form-header {
    padding: 20px 24px;
  }
  
  .form-title {
    font-size: 1.2rem;
  }
  
  .form-content {
    padding: 20px !important;
  }
  
  .stepper-content {
    padding: 20px;
  }
  
  .step-title {
    font-size: 1.2rem;
  }
  
  .step-subtitle {
    font-size: 0.9rem;
  }
  
  .input-label {
    font-size: 0.85rem;
  }
  
  .form-actions {
    padding: 16px 20px !important;
    flex-wrap: wrap;
  }
  
  .nav-btn, .save-btn {
    height: 40px;
    font-size: 0.9rem;
  }
  
  .delete-content, .import-content {
    padding: 20px !important;
  }
  
  .delete-text {
    font-size: 0.9rem;
  }
  
  .delete-warning {
    font-size: 0.8rem;
  }
  
  .template-card .d-flex {
    text-align: center;
  }
  
  .template-title {
    font-size: 0.95rem;
  }
  
  .template-subtitle {
    font-size: 0.85rem;
  }
}

/* Extra Small Mobile (480px and below) */
@media (max-width: 480px) {
  .header-card {
    padding: 20px;
    border-radius: 16px;
  }
  
  .header-title {
    font-size: 1.4rem;
  }
  
  .header-subtitle {
    font-size: 0.85rem;
  }
  
  .header-avatar-wrapper {
    padding: 10px;
  }
  
  .header-avatar {
    size: 40px;
  }
  
  .mobile-btn {
    height: 44px;
    font-size: 0.9rem;
  }
  
  .filter-card, .data-table-card {
    border-radius: 12px;
  }
  
  .mobile-customer-name {
    font-size: 0.95rem;
  }
  
  .mobile-customer-email {
    font-size: 0.8rem;
  }
  
  .detail-row {
    font-size: 0.75rem;
  }
  
  .detail-label {
    min-width: 55px;
  }
  
  .no-data-text {
    font-size: 1rem;
  }
  
  .form-title {
    font-size: 1.1rem;
  }
  
  .step-title {
    font-size: 1.1rem;
  }
}

/* Dark Theme Adjustments */
.v-theme--dark .header-card {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .filter-card,
.v-theme--dark .data-table-card,
.v-theme--dark .form-card,
.v-theme--dark .delete-card,
.v-theme--dark .import-card {
  background: #1e293b;
  border-color: #334155;
}

.v-theme--dark .mobile-customer-card {
  background: #1e293b;
  border-color: #334155;
}

.v-theme--dark .mobile-customer-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .card-header {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-color: #334155;
}

.v-theme--dark .selection-toolbar {
  background-color: rgba(var(--v-theme-primary), 0.15);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.v-theme--dark .stepper-header,
.v-theme--dark .stepper-content {
  background: #0f1629;
  border-color: #334155;
}

.v-theme--dark .template-card {
  background: rgba(var(--v-theme-success), 0.1);
  border-color: rgba(var(--v-theme-success), 0.3);
}

.v-theme--dark .error-item {
  background: rgba(var(--v-theme-error), 0.1);
}

/* Accessibility Improvements */
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}

/* Focus States */
.mobile-customer-card:focus-within {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.action-btn:focus-visible,
.primary-btn:focus-visible,
.mobile-btn:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.8);
  outline-offset: 2px;
}

/* Loading States */
.mobile-customer-card.loading {
  opacity: 0.7;
  pointer-events: none;
}

/* Animation Classes */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(20px);
}

/* Print Styles */
@media print {
  .header-card,
  .filter-card,
  .v-btn,
  .selection-toolbar {
    display: none !important;
  }
  
  .mobile-customer-card {
    break-inside: avoid;
    border: 1px solid #000;
    margin-bottom: 16px;
  }
  
  .mobile-customer-name {
    color: #000 !important;
  }
  
  .detail-value {
    color: #000 !important;
  }
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  .mobile-customer-card {
    border: 2px solid;
  }
  
  .detail-label {
    font-weight: 700;
  }
  
  .mobile-customer-name {
    font-weight: 800;
  }
}
</style>