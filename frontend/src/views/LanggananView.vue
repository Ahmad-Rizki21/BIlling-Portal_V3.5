<template>
  <v-container fluid class="pa-sm-6 pa-4">
    <div class="header-card mb-4 mb-md-6">
      <div class="d-flex flex-column align-center gap-4">
        <div class="d-flex align-center header-info">
          <div class="header-avatar-wrapper">
            <v-avatar class="header-avatar" color="transparent" size="50">
              <v-icon color="white" size="28">mdi-wifi-star</v-icon>
            </v-avatar>
          </div>
          <div class="ml-4">
            <h1 class="header-title">Manajemen Langganan</h1>
            <p class="header-subtitle">Kelola semua langganan pelanggan dengan mudah</p>
          </div>
        </div>

        <!-- Mobile Action Buttons -->
        <div class="action-buttons-container">
          <v-btn
            color="success"
            @click="dialogImport = true"
            prepend-icon="mdi-file-upload-outline"
            :loading="importing"
            class="action-btn text-none mobile-btn"
            size="default"
            block
          >
            Import
          </v-btn>
          <v-btn
            color="primary"
            @click="exportLangganan"
            :loading="exporting"
            prepend-icon="mdi-file-download-outline"
            class="action-btn text-none mobile-btn"
            size="default"
            block
          >
            Export
          </v-btn>
          <v-btn
            color="primary"
            @click="openDialog()"
            prepend-icon="mdi-plus-circle"
            class="primary-btn text-none mobile-btn"
            size="default"
            block
            elevation="3"
          >
            Tambah Langganan
          </v-btn>
        </div>
      </div>
    </div>
    <!-- Import Dialog -->
    <v-dialog v-model="dialogImport" max-width="800px" :fullscreen="$vuetify.display.mobile" persistent class="import-dialog">
      <v-card class="import-card">
        <div class="import-header">
          <v-icon class="mr-3">mdi-upload</v-icon>
          <span class="import-title">Import Langganan dari CSV</span>
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
          <v-alert
            type="info"
            variant="tonal"
            icon="mdi-information-outline"
            class="mb-6"
            border="start"
          >
            Gunakan <strong>Email Pelanggan</strong> dan <strong>Nama Paket Layanan</strong> sebagai kunci pencocokan.
            <a :href="`${apiClient.defaults.baseURL}/langganan/template/csv`" download>Unduh template di sini</a>.
          </v-alert>

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

        <v-card class="filter-card mb-6" elevation="0">
  <div class="d-flex flex-wrap align-center gap-4 pa-4">
    <v-text-field
      v-model="searchQuery"
      label="Cari Nama Pelanggan"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      :density="fieldDensity"
      hide-details
      clearable
      class="flex-grow-1"
      style="min-width: 250px;"
    ></v-text-field>

    <v-select
      v-model="selectedAlamat"
      :items="alamatOptions"
      label="Filter Alamat"
      prepend-inner-icon="mdi-map-marker"
      variant="outlined"
      density="comfortable"
      hide-details
      clearable
      class="flex-grow-1"
      style="min-width: 200px;"
    ></v-select>

    <v-select
      v-model="selectedPaket"
      :items="uniquePaketLayananOptions"
      item-title="nama_paket"
      item-value="id"
      label="Filter Paket Layanan"
      prepend-inner-icon="mdi-wifi-star"
      variant="outlined"
      density="comfortable"
      hide-details
      clearable
      class="flex-grow-1"
      style="min-width: 200px;"
    ></v-select>

    <v-select
      v-model="selectedStatus"
      :items="statusOptions"
      label="Filter Status"
      prepend-inner-icon="mdi-list-status"
      variant="outlined"
      density="comfortable"
      hide-details
      clearable
      class="flex-grow-1"
      style="min-width: 180px;"
    ></v-select>
    
    <v-btn
        variant="text"
        @click="resetFilters"
        class="text-none"
    >
      <v-icon start>mdi-refresh</v-icon>
      Reset
    </v-btn>
  </div>
</v-card>

    <v-card elevation="3" class="rounded-lg">
      <v-card-title class="d-flex align-center pa-4 pa-sm-6 bg-grey-lighten-5">
        <v-icon start icon="mdi-format-list-bulleted-square" color="primary"></v-icon>
        <span class="text-h6 font-weight-bold">Daftar Langganan</span>
        <v-spacer></v-spacer>
        <v-chip color="primary" variant="outlined" size="small">
          {{ langgananList.length }} langganan
        </v-chip>
      </v-card-title>

      <v-expand-transition>
        <div v-if="selectedLangganan.length > 0" class="selection-toolbar pa-4">
          <span class="font-weight-bold text-primary">{{ selectedLangganan.length }} langganan terpilih</span>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete-sweep"
            @click="dialogBulkDelete = true"
          >
            Hapus Terpilih
          </v-btn>
        </div>
      </v-expand-transition>
      
      <!-- Mobile Card View -->
      <div class="d-block d-md-none">
  <div v-if="loading" class="px-4 py-4">
    <SkeletonLoader type="list" :items="5" />
  </div>
  
  <div v-else-if="langgananList.length === 0" class="pa-8 text-center">
    <v-icon size="64" color="grey-lighten-1">mdi-wifi-off</v-icon>
    <p class="mt-4 text-h6 text-medium-emphasis">Belum ada data langganan</p>
    <v-btn 
      color="primary" 
      variant="elevated" 
      @click="openDialog()" 
      class="mt-6 text-none"
      prepend-icon="mdi-plus-circle"
    >
      Tambah Langganan
    </v-btn>
  </div>

  <div v-else class="pa-2">
    <v-card
      v-for="item in langgananList"
      :key="item.id"
      class="mb-3"
      elevation="2"
      rounded="lg"
    >
      <v-card-text class="pa-4">
        <div class="d-flex align-center mb-3">
          <v-checkbox
            v-model="selectedLangganan"
            :value="item"
            hide-details
            class="me-2 pa-0"
            density="compact"
          ></v-checkbox>
          <div class="flex-grow-1">
            <h3 class="text-body-1 font-weight-bold">{{ getPelangganName(item.pelanggan_id) }}</h3>
            <p class="text-caption text-medium-emphasis">{{ getPaketName(item.paket_layanan_id) }}</p>
          </div>
          <v-chip
            size="small"
            :color="getStatusColor(item.status)"
            class="font-weight-bold"
            label
          >
            {{ item.status }}
          </v-chip>
        </div>

        <v-divider class="mb-3"></v-divider>

        <v-list density="compact" class="bg-transparent">
          <v-list-item class="px-0">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-phone</v-icon>
            </template>
            <v-list-item-title class="text-body-2">No. Telepon</v-list-item-title>
            <template v-slot:append>
              <span class="text-body-2">{{ getPelangganPhone(item.pelanggan_id) }}</span>
            </template>
          </v-list-item>
          <v-list-item class="px-0" v-if="(item.status === 'Aktif' || item.status === 'Berhenti')">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-wifi-router</v-icon>
            </template>
            <v-list-item-title class="text-body-2">Status Modem</v-list-item-title>
            <template v-slot:append>
              <v-chip
                size="x-small"
                :color="getModemStatusColor(item.status_modem, item.status)"
                class="font-weight-bold"
                label
              >
                {{ formatModemStatus(item.status_modem, item.status) }}
              </v-chip>
            </template>
          </v-list-item>
          <v-list-item class="px-0" v-if="item.status === 'Suspended'">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-whatsapp</v-icon>
            </template>
            <v-list-item-title class="text-body-2">Status WhatsApp</v-list-item-title>
            <template v-slot:append>
              <div class="text-right">
                <v-chip
                  size="x-small"
                  :color="item.whatsapp_status ? 'success' : 'warning'"
                  class="font-weight-bold mb-1"
                  label
                >
                  {{ item.whatsapp_status ? 'Sudah Dikirim' : 'Belum Dikirim' }}
                </v-chip>
                <div v-if="item.last_whatsapp_sent" class="text-caption text-medium-emphasis">
                  {{ formatDate(item.last_whatsapp_sent, true) }}
                </div>
              </div>
            </template>
          </v-list-item>
          <v-list-item class="px-0" v-if="item.status === 'Berhenti' && item.alasan_berhenti">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-information-outline</v-icon>
            </template>
            <v-list-item-title class="text-body-2">Alasan Berhenti</v-list-item-title>
            <template v-slot:append>
              <span class="text-body-2 text-medium-emphasis text-right">{{ formatAlasanBerhenti(item.alasan_berhenti, item.status) }}</span>
            </template>
          </v-list-item>
          <v-list-item class="px-0">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-cash</v-icon>
            </template>
            <v-list-item-title class="text-body-2">Harga</v-list-item-title>
            <template v-slot:append>
              <span class="text-body-2 font-weight-bold text-success">{{ formatCurrency(item.harga_final) }}</span>
            </template>
          </v-list-item>
          <v-list-item class="px-0">
            <template v-slot:prepend>
              <v-icon size="18" class="me-3 text-medium-emphasis">mdi-calendar-alert</v-icon>
            </template>
            <v-list-item-title class="text-body-2">Jatuh Tempo</v-list-item-title>
            <template v-slot:append>
              <span class="text-body-2">{{ formatDate(item.tgl_jatuh_tempo) }}</span>
            </template>
          </v-list-item>
        </v-list>

        <v-divider class="mt-2"></v-divider>

        <div class="d-flex gap-2 mt-3">
          <v-btn size="small" variant="tonal" color="primary" @click="navigateToEdit(item)" class="flex-grow-1">
            <v-icon start size="16">mdi-pencil</v-icon> Edit
          </v-btn>
          <v-btn size="small" variant="tonal" color="info" @click="openPelangganView(item)" class="flex-grow-1">
            <v-icon start size="16">mdi-eye</v-icon> View
          </v-btn>
          <v-btn
            v-if="item.status === 'Suspended'"
            size="small"
            variant="tonal"
            :color="item.whatsapp_status ? 'success' : 'warning'"
            @click="sendWhatsApp(item)"
            class="flex-grow-1"
          >
            <v-icon start size="16">mdi-whatsapp</v-icon>
            {{ item.whatsapp_status ? 'Chat Lagi' : 'WhatsApp' }}
          </v-btn>
          <v-btn size="small" variant="tonal" color="error" @click="openDeleteDialog(item)" class="flex-grow-1">
            <v-icon start size="16">mdi-delete</v-icon> Hapus
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <div v-if="hasMoreData && langgananList.length > 0" class="text-center pa-4">
      <v-btn
        variant="tonal"
        color="primary"
        @click="loadMore"
        :loading="loadingMore"
        class="text-none"
      >
        Muat Lebih Banyak
      </v-btn>
    </div>
  </div>
</div>

      <!-- Desktop Table View -->
      <div class="table-responsive-wrapper d-none d-md-block">
        <v-data-table
          v-model="selectedLangganan"
          :headers="headers"
          :items="langgananList"
          :loading="loading"
          item-value="id"
          class="elevation-0"
          :items-per-page="-1"
          :server-items-length="-1"
          show-select
          return-object
          hide-default-footer
        >

          <template v-slot:loading>
            <SkeletonLoader type="table" :rows="8" />
          </template>

          <template v-slot:item.nomor="{ index }: { index: number }">
            {{ index + 1 }}
          </template>

          <template v-slot:item.pelanggan_id="{ item }: { item: Langganan }">
            <div class="font-weight-bold">{{ getPelangganName(item.pelanggan_id) }}</div>
            <div class="text-caption text-medium-emphasis">ID: {{ item.pelanggan_id }}</div>
          </template>

          <template v-slot:item.pelanggan.alamat="{ item }: { item: Langganan }">
            <div class="text-caption" style="max-width: 200px; white-space: normal;">
              {{ getPelangganAlamat(item.pelanggan_id) }}
            </div>
          </template>

          <template v-slot:item.pelanggan.no_tlp="{ item }: { item: Langganan }">
            <div class="text-body-2">
              {{ getPelangganPhone(item.pelanggan_id) }}
            </div>
          </template>

          <template v-slot:item.paket_layanan_id="{ item }: { item: Langganan }">
            <div class="font-weight-medium">{{ getPaketName(item.paket_layanan_id) }}</div>
          </template>
          
          <template v-slot:item.metode_pembayaran="{ item }: { item: Langganan }">
            <v-chip
              size="small"
              variant="tonal"
              :color="item.metode_pembayaran === 'Prorate' ? 'blue' : 'grey-darken-1'"
            >
              {{ item.metode_pembayaran }}
            </v-chip>
          </template>

          <template v-slot:item.harga_awal="{ item }: { item: Langganan }">
            <div class="font-weight-bold text-right">
              {{ formatCurrency(item.harga_awal) }}
            </div>
          </template>

          <template v-slot:item.harga_final="{ item }"> <div class="font-weight-bold text-right">
              {{ formatCurrency(item.harga_final) }} </div>
          </template>

          <template v-slot:item.status="{ item }: { item: Langganan }">
            <v-chip
              size="small"
              :color="getStatusColor(item.status)"
              class="font-weight-bold"
            >
              {{ item.status }}
            </v-chip>
          </template>

          <template v-slot:item.status_modem="{ item }: { item: Langganan }">
            <v-chip
              size="small"
              :color="getModemStatusColor(item.status_modem, item.status)"
              class="font-weight-bold"
              label
            >
              {{ formatModemStatus(item.status_modem, item.status) }}
            </v-chip>
          </template>

          <template v-slot:item.alasan_berhenti="{ item }: { item: Langganan }">
            <div class="text-body-2" style="max-width: 200px; white-space: normal;">
              {{ formatAlasanBerhenti(item.alasan_berhenti, item.status) }}
            </div>
          </template>

          <template v-slot:item.tgl_jatuh_tempo="{ item }: { item: Langganan }">
              {{ formatDate(item.tgl_jatuh_tempo) }}
          </template>

          <template v-slot:item.whatsapp_status="{ item }: { item: Langganan }">
            <div v-if="item.status === 'Suspended'" class="text-center">
              <v-chip
                size="x-small"
                :color="item.whatsapp_status ? 'success' : 'warning'"
                class="font-weight-bold mb-1"
                label
              >
                {{ item.whatsapp_status ? 'Sudah' : 'Belum' }}
              </v-chip>
              <div v-if="item.last_whatsapp_sent" class="text-caption text-medium-emphasis">
                {{ formatDate(item.last_whatsapp_sent, true) }}
              </div>
            </div>
            <span v-else class="text-medium-emphasis text-body-2">-</span>
          </template>

          <template v-slot:item.actions="{ item }: { item: Langganan }">
            <div class="d-flex justify-center ga-2">
              <v-btn size="small" variant="tonal" color="primary" @click="navigateToEdit(item)">
                <v-icon start size="16">mdi-pencil</v-icon> Edit
              </v-btn>
              <v-btn size="small" variant="tonal" color="info" @click="openPelangganView(item)">
                <v-icon start size="16">mdi-eye</v-icon> View
              </v-btn>
              <v-btn
                v-if="item.status === 'Suspended'"
                size="small"
                variant="tonal"
                :color="item.whatsapp_status ? 'success' : 'warning'"
                @click="sendWhatsApp(item)"
              >
                <v-icon start size="16">mdi-whatsapp</v-icon>
                {{ item.whatsapp_status ? 'Chat Lagi' : 'WhatsApp' }}
              </v-btn>
              <v-btn size="small" variant="tonal" color="error" @click="openDeleteDialog(item)">
                <v-icon start size="16">mdi-delete</v-icon> Hapus
              </v-btn>
            </div>
          </template>
        </v-data-table>
        
        </div>

      <!-- Custom Pagination Controls untuk Desktop -->
      <div class="d-none d-md-block pa-2">
        <v-card class="pa-3">
          <div class="d-flex align-center justify-space-between">
            <!-- Total Count -->
            <v-chip variant="outlined" color="primary" size="large">
              Total: {{ totalLanggananCount }} Langganan di server
            </v-chip>

            <!-- Custom Pagination -->
            <div class="d-flex align-center">
              <v-select
                v-model="itemsPerPage"
                :items="[10, 15, 25, 50, 100]"
                variant="outlined"
                density="compact"
                hide-details
                style="width: 80px"
                class="mr-3"
                @update:model-value="onItemsPerPageChange"
              ></v-select>

              <span class="text-body-2 mr-3">
                {{ (desktopPage - 1) * itemsPerPage + 1 }}-{{ Math.min(desktopPage * itemsPerPage, totalLanggananCount) }} of {{ totalLanggananCount }}
              </span>

              <v-btn
                icon="mdi-chevron-left"
                variant="text"
                :disabled="desktopPage === 1"
                @click="goToPreviousPage"
                class="mr-1"
              ></v-btn>

              <v-btn
                icon="mdi-chevron-right"
                variant="text"
                :disabled="desktopPage >= Math.ceil(totalLanggananCount / itemsPerPage)"
                @click="goToNextPage"
              ></v-btn>
            </div>
          </div>
        </v-card>
      </div>
    </v-card>

<!--
  Perubahan di atas mengadopsi pola responsif dari halaman lain.
  - `d-block d-md-none`: Menampilkan daftar kartu hanya di layar kecil (mobile).
  - `d-none d-md-block`: Menyembunyikan tabel di layar kecil dan menampilkannya di layar medium ke atas (desktop).
-->
<v-dialog v-model="dialog" max-width="800px" persistent scrollable>
  <v-card class="subscription-modal">
    <!-- Simplified Header -->
    <v-card-title class="modal-header">
      <div class="header-content">
        <v-icon color="white" size="24" class="me-3">
          {{ editedIndex === -1 ? 'mdi-plus-circle' : 'mdi-pencil' }}
        </v-icon>
        <div>
          <h3 class="header-title">{{ formTitle }}</h3>
          <p class="header-subtitle">
            {{ editedIndex === -1 ? 'Tambahkan langganan baru untuk pelanggan' : 'Perbarui informasi langganan' }}
          </p>
        </div>
      </div>
    </v-card-title>

    <!-- Form Content -->
    <v-card-text class="modal-content">
      <v-form ref="formRef" v-model="formValid" lazy-validation>
        <!-- Customer Selection -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-account</v-icon>
            Informasi Pelanggan
          </h4>
            <label class="input-label">
              Pilih Pelanggan
              <span class="required-flag text-error">*</span>
            </label>
            <v-autocomplete
              v-model="editedItem.pelanggan_id"
              :items="dropdownPelangganSource"
              item-title="nama"
              item-value="id"
              placeholder="Ketik nama pelanggan untuk mencari..."
              variant="outlined"
              prepend-inner-icon="mdi-account-search"
              :rules="[rules.required]"
              :disabled="editedIndex !== -1"
              density="comfortable"
              clearable
              hide-details="auto"
              class="mb-4"
            >
              <template v-slot:item="{ props, item }">
  <v-list-item v-bind="props" class="px-4">
    <template v-slot:prepend>
      <v-avatar color="primary" size="32">
        <v-icon color="white" size="16">mdi-account</v-icon>
      </v-avatar>
    </template>
    <!-- Hilangkan title default dan ganti dengan custom -->
    <template v-slot:title>
      <div class="font-weight-medium d-flex align-center">
        <span class="flex-grow-1">{{ item.raw.nama }}</span>
        <!-- Mode Tambah: Semua pelanggan adalah USER BARU -->
        <!-- Mode Edit: Tampilkan chip hanya untuk pelanggan benar-benar baru -->
        <v-chip
          v-if="editedIndex === -1 || isPelangganBaru(item.raw.id)"
          size="x-small"
          color="success"
          variant="elevated"
          class="ms-2 flex-shrink-0"
        >
          USER BARU
        </v-chip>
      </div>
    </template>
  </v-list-item>
</template>
            </v-autocomplete>
        </div>

        <!-- Package and Payment -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-wifi</v-icon>
            Paket & Pembayaran
          </h4>
          
          <v-row>
            <v-col cols="12" md="6">
              <label class="input-label">
                Pilih Paket Layanan
                <span class="required-flag text-error">*</span>
              </label>
              <v-select
                v-model="editedItem.paket_layanan_id"
                :items="filteredPaketLayanan"
                :loading="paketLoading"
                item-title="nama_paket"
                item-value="id"
                :disabled="!editedItem.pelanggan_id || isPaketLocked"
                placeholder="Pilih pelanggan terlebih dahulu"
                variant="outlined"
                prepend-inner-icon="mdi-wifi-star"
                :rules="[rules.required]"
                density="comfortable"
                hide-details="auto"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props" class="px-4">
                    <template v-slot:prepend>
                      <v-avatar color="indigo" size="32">
                        <v-icon color="white" size="16">mdi-wifi</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-medium">{{ item.raw.nama_paket }}</v-list-item-title>
                    <v-list-item-subtitle>{{ item.raw.kecepatan }} Mbps - {{ formatCurrency(item.raw.harga) }}</v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
            
            <v-col cols="12" md="6">
              <label class="input-label">
                Metode Pembayaran
                <span class="required-flag text-error">*</span>
              </label>
              <v-select
                v-model="editedItem.metode_pembayaran"
                :items="[
                  { title: 'Otomatis (Bulanan)', value: 'Otomatis' }, 
                  { title: 'Prorate (Proporsional)', value: 'Prorate' }
                ]"
                variant="outlined"
                prepend-inner-icon="mdi-cash-multiple"
                density="comfortable"
                hide-details="auto"
              ></v-select>
            </v-col>
          </v-row>

          <!-- Pricing Display -->
          <div v-if="editedItem.metode_pembayaran === 'Otomatis'" class="mt-4">
            <v-text-field
              :model-value="editedItem.harga_awal"
              label="Total Harga Bulanan"
              variant="outlined"
              prepend-inner-icon="mdi-currency-usd"
              prefix="Rp"
              readonly
              density="comfortable"
              class="price-field"
            ></v-text-field>
          </div>

          <!-- Prorate Options -->
          <template v-if="editedItem.metode_pembayaran === 'Prorate'">
            <v-row class="mt-2">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedItem.tgl_mulai_langganan"
                  label="Tanggal Mulai Langganan"
                  type="date"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-start"
                  density="comfortable"
                  hide-details="auto"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6" class="d-flex align-center">
                <v-switch
                  v-model="isProratePlusFull"
                  color="primary"
                  label="Sertakan tagihan penuh bulan depan"
                  inset
                  hide-details
                  density="comfortable"
                ></v-switch>
              </v-col>
            </v-row>

            <!-- Prorate Pricing Info -->
            <div class="mt-4">
              <v-alert
                v-if="isProratePlusFull && hargaProrate > 0"
                variant="tonal"
                color="info"
                icon="mdi-information-outline"
                density="compact"
                class="mb-4"
              >
                <div class="text-body-2">
                  <strong>Rincian Tagihan Pertama:</strong>
                  <div class="ms-2 mt-1">
                    • Biaya Prorate: {{ formatCurrency(hargaProrate) }}<br>
                    • Biaya Bulan Depan: {{ formatCurrency(hargaNormal) }}
                  </div>
                </div>
              </v-alert>

              <v-text-field
                :model-value="editedItem.harga_awal"
                :label="isProratePlusFull ? 'Total Tagihan Pertama' : 'Total Harga Prorate'"
                variant="outlined"
                prepend-inner-icon="mdi-currency-usd-circle"
                prefix="Rp"
                readonly
                density="comfortable"
                class="price-field"
              ></v-text-field>
            </div>
          </template>
        </div>

        <!-- Status and Schedule -->
        <div class="form-section">
          <h4 class="section-title">
            <v-icon size="18" class="me-2">mdi-cog</v-icon>
            Status & Jadwal
          </h4>
          
          <v-row>
            <v-col cols="12" md="6">
              <label class="input-label">
                Status Langganan
                <span class="required-flag text-error">*</span>
              </label>
              <v-select
                v-model="editedItem.status"
                :items="[
                  { title: 'Aktif', value: 'Aktif' },
                  { title: 'Suspended', value: 'Suspended' },
                  { title: 'Berhenti', value: 'Berhenti' }
                ]"
                variant="outlined"
                prepend-inner-icon="mdi-check-circle-outline"
                :rules="[rules.required]"
                density="comfortable"
                hide-details="auto"
              ></v-select>
            </v-col>
            
            <v-col cols="12" md="6">
              <label class="input-label">
                Tanggal Jatuh Tempo
                <span class="required-flag text-error">*</span>
              </label>
              <v-text-field
                v-model="editedItem.tgl_jatuh_tempo"
                type="date"
                variant="outlined"
                prepend-inner-icon="mdi-calendar-alert"
                :rules="[rules.required]"
                density="comfortable"
                hide-details="auto"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Status Modem Section - Muncul untuk Aktif dan Berhenti -->
          <v-expand-transition>
            <div v-if="editedItem.status === 'Aktif' || editedItem.status === 'Berhenti'" class="mt-4">
              <label class="input-label">
                Status Modem
                <span class="text-caption text-medium-emphasis ms-2">
                  {{ editedItem.status === 'Aktif' ? '(Wajib diisi)' : '(Wajib diisi)' }}
                </span>
              </label>
              <v-select
                v-model="editedItem.status_modem"
                :items="getStatusModemOptions(editedItem.status)"
                item-title="title"
                item-value="value"
                variant="outlined"
                prepend-inner-icon="mdi-wifi-router"
                density="comfortable"
                hide-details="auto"
                class="status-modem-field"
              ></v-select>
            </div>
          </v-expand-transition>

          <!-- Alasan Berhenti Section - Hanya muncul jika status = Berhenti -->
          <v-expand-transition>
            <div v-if="editedItem.status === 'Berhenti'" class="mt-4">
              <label class="input-label">
                Alasan Berhenti
                <span class="text-caption text-medium-emphasis ms-2">(Opsional)</span>
              </label>
              <v-textarea
                v-model="editedItem.alasan_berhenti"
                label="Tuliskan alasan pelanggan berhenti berlangganan..."
                variant="outlined"
                prepend-inner-icon="mdi-text-box-outline"
                rows="3"
                auto-grow
                density="comfortable"
                hide-details="auto"
                class="alasan-field"
                placeholder="Contoh: Pindah rumah, tidak puas dengan layanan, alasan ekonomi, dll."
              ></v-textarea>
            </div>
          </v-expand-transition>
        </div>
      </v-form>
    </v-card-text>

    <!-- Action Buttons -->
    <v-card-actions class="modal-actions">
      <v-spacer></v-spacer>
      <v-btn
        variant="text"
        color="grey-darken-1"
        @click="closeDialog"
        class="text-none"
      >
        Batal
      </v-btn>
      <v-btn
        color="primary"
        variant="flat"
        @click="saveLangganan"
        :loading="saving"
        :disabled="!isFormValid"
        class="text-none"
      >
        <v-icon start size="18">{{ editedIndex === -1 ? 'mdi-plus' : 'mdi-content-save' }}</v-icon>
        {{ editedIndex === -1 ? 'Tambah Langganan' : 'Simpan Perubahan' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
    <!-- Enhanced Delete Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="rounded-xl elevation-8">
        <div class="delete-header text-center pa-8">
          <v-avatar size="64" color="error" class="mb-4">
            <v-icon size="32" color="white">mdi-delete-alert</v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold text-error mb-2">Konfirmasi Hapus</h2>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Apakah Anda yakin ingin menghapus langganan untuk pelanggan 
            <strong class="text-primary">{{ itemToDelete?.pelanggan?.nama || '...' }}</strong>?
          </p>
          <v-alert variant="tonal" color="warning" class="mt-4 text-start">
            <v-icon start>mdi-alert-triangle</v-icon>
            Tindakan ini tidak dapat dibatalkan
          </v-alert>
        </div>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1" 
            @click="closeDeleteDialog"
            class="text-none me-2"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmDelete" 
            :loading="deleting"
            class="text-none"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogBulkDelete" max-width="500px">
      <v-card class="rounded-xl elevation-8">
        <div class="delete-header text-center pa-8">
          <v-avatar size="64" color="error" class="mb-4">
            <v-icon size="32" color="white">mdi-delete-alert</v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold text-error mb-2">Konfirmasi Hapus Massal</h2>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Anda yakin ingin menghapus <strong>{{ selectedLangganan.length }} langganan</strong> yang dipilih?
          </p>
        </div>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            variant="text" 
            color="grey-darken-1" 
            @click="dialogBulkDelete = false"
            class="text-none me-2"
          >
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmBulkDelete" 
            :loading="deleting"
            class="text-none"
          >
            <v-icon start>mdi-delete</v-icon>
            Ya, Hapus
          </v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Modal View Pelanggan -->
    <v-dialog v-model="pelangganViewDialog" max-width="900px" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center pa-4 bg-primary text-white">
          <v-icon class="me-3">mdi-account-details</v-icon>
          Detail Pelanggan & Statistik Pembayaran
        </v-card-title>

        <v-card-text class="pa-4" v-if="selectedPelanggan">
          <!-- Customer Information Section -->
          <div class="mb-6">
            <h3 class="text-h6 font-weight-bold mb-3 d-flex align-center">
              <v-icon class="me-2" color="primary">mdi-account-circle</v-icon>
              Informasi Pelanggan
            </h3>
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-account</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Nama</v-list-item-title>
                    <v-list-item-subtitle>{{ selectedPelanggan.pelanggan?.nama || 'N/A' }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-phone</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">No. Telepon</v-list-item-title>
                    <v-list-item-subtitle>{{ selectedPelanggan.pelanggan?.no_telp || 'N/A' }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-map-marker</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Alamat</v-list-item-title>
                    <v-list-item-subtitle>{{ selectedPelanggan.pelanggan?.alamat || 'N/A' }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-identifier</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">ID Pelanggan</v-list-item-title>
                    <v-list-item-subtitle>
                      <div class="d-flex align-center">
                        <span>{{ selectedPelanggan.pelanggan_id }}</span>
                        <v-chip
                          v-if="dataTeknisInfo && dataTeknisInfo.id_pelanggan"
                          size="x-small"
                          color="primary"
                          class="ms-2"
                          label
                        >
                          {{ dataTeknisInfo.id_pelanggan }}
                        </v-chip>
                      </div>
                      <div v-if="dataTeknisInfo && dataTeknisInfo.id_pelanggan" class="text-caption text-medium-emphasis mt-1">
                        ID Pelanggan (Data Teknis)
                      </div>
                    </v-list-item-subtitle>
                  </v-list-item>
                                    <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-cash</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Harga/Bulan</v-list-item-title>
                    <v-list-item-subtitle>{{ formatCurrency(selectedPelanggan.harga_final) }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </div>

          <v-divider class="my-4"></v-divider>

          <!-- Subscription Information -->
          <div class="mb-6">
            <h3 class="text-h6 font-weight-bold mb-3 d-flex align-center">
              <v-icon class="me-2" color="primary">mdi-package</v-icon>
              Informasi Langganan
            </h3>
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-package-variant</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Paket Layanan</v-list-item-title>
                    <v-list-item-subtitle>{{ getPaketName(selectedPelanggan.paket_layanan_id) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-credit-card</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Metode Pembayaran</v-list-item-title>
                    <v-list-item-subtitle>{{ selectedPelanggan.metode_pembayaran }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-calendar</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Tanggal Mulai</v-list-item-title>
                    <v-list-item-subtitle>{{ formatDate(selectedPelanggan.tgl_mulai_langganan) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-calendar-alert</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Jatuh Tempo</v-list-item-title>
                    <v-list-item-subtitle>{{ formatDate(selectedPelanggan.tgl_jatuh_tempo) }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </div>

          <v-divider class="my-4"></v-divider>

          <!-- Data Teknis Information -->
          <div class="mb-6" v-if="dataTeknisInfo">
            <h3 class="text-h6 font-weight-bold mb-3 d-flex align-center">
              <v-icon class="me-2" color="primary">mdi-network-outline</v-icon>
              Data Teknis
            </h3>
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item v-if="dataTeknisInfo.ip_pelanggan">
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-ip-network</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">IP Address</v-list-item-title>
                    <v-list-item-subtitle>{{ dataTeknisInfo.ip_pelanggan }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="dataTeknisInfo.profile_pppoe">
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-speedometer</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Profile PPPoE</v-list-item-title>
                    <v-list-item-subtitle>{{ dataTeknisInfo.profile_pppoe }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item v-if="dataTeknisInfo.olt">
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-server</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">OLT</v-list-item-title>
                    <v-list-item-subtitle>{{ dataTeknisInfo.olt }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="dataTeknisInfo.pon !== null && dataTeknisInfo.pon !== undefined">
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-ethernet</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">PON Port</v-list-item-title>
                    <v-list-item-subtitle>{{ dataTeknisInfo.pon }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="dataTeknisInfo.sn">
                    <template v-slot:prepend>
                      <v-icon size="20" class="me-3 text-medium-emphasis">mdi-serial-number</v-icon>
                    </template>
                    <v-list-item-title class="font-weight-bold">Serial Number ONU</v-list-item-title>
                    <v-list-item-subtitle>{{ dataTeknisInfo.sn }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </div>

          <v-divider class="my-4"></v-divider>

          <!-- Payment Statistics -->
          <div class="mb-6">
            <h3 class="text-h6 font-weight-bold mb-3 d-flex align-center">
              <v-icon class="me-2" color="primary">mdi-chart-pie</v-icon>
              Statistik Pembayaran
            </h3>
            <v-row>
              <v-col cols="12" md="4">
                <v-card class="pa-3" variant="tonal" color="success">
                  <div class="d-flex align-center">
                    <v-icon size="32" color="success" class="me-3">mdi-check-circle</v-icon>
                    <div>
                      <div class="text-h5 font-weight-bold text-success">{{ paymentStats.onTimeCount }}</div>
                      <div class="text-body-2">Pembayaran Tepat Waktu</div>
                    </div>
                  </div>
                  <div class="mt-2">
                    <v-progress-linear
                      :model-value="paymentStats.totalInvoices > 0 ? (paymentStats.onTimeCount / paymentStats.totalInvoices) * 100 : 0"
                      color="success"
                      height="6"
                      rounded
                    ></v-progress-linear>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card class="pa-3" variant="tonal" color="warning">
                  <div class="d-flex align-center">
                    <v-icon size="32" color="warning" class="me-3">mdi-clock-alert</v-icon>
                    <div>
                      <div class="text-h5 font-weight-bold text-warning">{{ paymentStats.lateCount }}</div>
                      <div class="text-body-2">Pembayaran Terlambat</div>
                    </div>
                  </div>
                  <div class="mt-2">
                    <v-progress-linear
                      :model-value="paymentStats.totalInvoices > 0 ? (paymentStats.lateCount / paymentStats.totalInvoices) * 100 : 0"
                      color="warning"
                      height="6"
                      rounded
                    ></v-progress-linear>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card class="pa-3" variant="tonal" color="info">
                  <div class="d-flex align-center">
                    <v-icon size="32" color="info" class="me-3">mdi-receipt</v-icon>
                    <div>
                      <div class="text-h5 font-weight-bold text-info">{{ paymentStats.totalInvoices }}</div>
                      <div class="text-body-2">Total Invoice</div>
                    </div>
                  </div>
                </v-card>
              </v-col>
            </v-row>
          </div>

          <v-divider class="my-4"></v-divider>

          <!-- Payment History -->
          <div>
            <h3 class="text-h6 font-weight-bold mb-3 d-flex align-center">
              <v-icon class="me-2" color="primary">mdi-history</v-icon>
              Riwayat Pembayaran
            </h3>
            <div v-if="paymentHistory.length === 0" class="text-center pa-4 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-receipt-outline</v-icon>
              <div>Belum ada riwayat pembayaran</div>
            </div>
            <v-data-table
              v-else
              :headers="paymentHeaders"
              :items="paymentHistory"
              density="compact"
              hide-default-footer
              class="elevation-1"
            >
              <template v-slot:item.tanggal_bayar="{ item }">
                {{ formatDate(item.tanggal_bayar) }}
              </template>
              <template v-slot:item.status_pembayaran="{ item }">
                <v-chip
                  :color="item.status_pembayaran === 'Lunas' ? 'success' : 'warning'"
                  size="small"
                  label
                >
                  {{ item.status_pembayaran }}
                </v-chip>
              </template>
              <template v-slot:item.terlambat="{ item }">
                <v-chip
                  v-if="item.terlambat > 0"
                  color="error"
                  size="small"
                  variant="tonal"
                >
                  {{ item.terlambat }} hari
                </v-chip>
                <v-chip
                  v-else
                  color="success"
                  size="small"
                  variant="tonal"
                >
                  <v-icon start size="12">mdi-check</v-icon>
                  Tepat waktu
                </v-chip>
              </template>
            </v-data-table>
          </div>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="elevated" @click="pelangganViewDialog = false">
            Tutup
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
// import { ref, onMounted, computed, watch } from 'vue';
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '@/services/api';
import { useDisplay } from 'vuetify';
import { debounce } from 'lodash-es';
import SkeletonLoader from '@/components/SkeletonLoader.vue';


// --- Router ---
const router = useRouter();

// --- Responsive State ---
const { mobile } = useDisplay();
const fieldDensity = computed(() => mobile.value ? 'compact' : 'comfortable');
const notificationPelangganList = ref<PelangganSelectItem[] | null>(null);

const mobilePage = ref(1);
const desktopPage = ref(1);
const itemsPerPage = ref(25); // Jumlah item yang di-load setiap kali di mobile & desktop
const hasMoreData = ref(true);
const loadingMore = ref(false);


// --- Interfaces ---
interface Langganan {
  id: number;
  pelanggan_id: number;
  paket_layanan_id: number;
  status: string;
  pelanggan: PelangganData;
  tgl_jatuh_tempo: string | null;
  tgl_invoice_terakhir: string | null;
  metode_pembayaran: string;
  harga_awal: number | null;
  harga_final: number;
  tgl_mulai_langganan?: string | null;
  alasan_berhenti?: string | null;
  status_modem?: string | null;
  whatsapp_status?: string | null;
  last_whatsapp_sent?: string | null;
}

interface PelangganData {
  id: number;
  nama: string;
  alamat: string;
  no_telp?: string;
}

interface PelangganSelectItem {
  id: number;
  nama: string;
  id_brand: string;
  alamat?: string; // Optional karena mungkin tidak ada di semua API calls
  no_telp?: string; // Nomor telepon pelanggan
}

interface PaketLayananSelectItem {
  id: number;
  nama_paket: string;
  kecepatan: number;
  harga: number;
  id_brand: string;
}

// --- State ---
const langgananList = ref<Langganan[]>([]);
const pelangganSelectList = ref<PelangganSelectItem[]>([]);
const paketLayananSelectList = ref<PaketLayananSelectItem[]>([]);
const filteredPaketLayanan = ref<PaketLayananSelectItem[]>([]);

const loading = ref(true);
const paketLoading = ref(true);
const isPaketLocked = ref(false);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const editedIndex = ref(-1);
const formValid = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' | 'warning' });

const selectedLangganan = ref<Langganan[]>([]);
const dialogBulkDelete = ref(false);

// Pelanggan View Modal Data
const pelangganViewDialog = ref(false);
const selectedPelanggan = ref<Langganan | null>(null);
const dataTeknisInfo = ref<any>(null);
const paymentHistory = ref<any[]>([]);
const paymentStats = ref({
  onTimeCount: 0,
  lateCount: 0,
  totalInvoices: 0
});


const paymentHeaders = [
  { title: 'No. Invoice', key: 'id', sortable: false },
  { title: 'Tanggal Bayar', key: 'tanggal_bayar', sortable: false },
  { title: 'Jumlah', key: 'jumlah', sortable: false },
  { title: 'Status', key: 'status_pembayaran', sortable: false },
  { title: 'Keterlambatan', key: 'terlambat', sortable: false }
];

const dialogImport = ref(false);
const importing = ref(false);
const exporting = ref(false);
const fileToImport = ref<File[]>([]);
const importErrors = ref<string[]>([]);

const searchQuery = ref('');
const selectedAlamat = ref('');
const selectedPaket = ref<number | null>(null);
const selectedStatus = ref<string | null>(null);
const statusOptions = ref(['Aktif', 'Suspended', 'Berhenti']);

const isProratePlusFull = ref<boolean>(false);
const hargaProrate = ref<number>(0);
const hargaNormal = ref<number>(0);

// --- State for Total Count ---
const totalLanggananCount = ref(0);


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

function closeImportDialog() {
  dialogImport.value = false;
  fileToImport.value = [];
  importErrors.value = [];
}

const defaultItem: Partial<Langganan> = {
  pelanggan_id: undefined,
  paket_layanan_id: undefined,
  status: 'Aktif',
  tgl_jatuh_tempo: null,
  tgl_invoice_terakhir: null,
  metode_pembayaran: 'Otomatis',
  harga_awal: 0,
  tgl_mulai_langganan: null,
  alasan_berhenti: null,
  status_modem: 'Terpasang',
};
const editedItem = ref({ ...defaultItem });
const itemToDelete = ref<Langganan | null>(null);
const newPelangganIdMarker = ref<number | null>(null);

const isEditMode = computed(() => editedIndex.value > -1);

// --- Validation Rules ---
const rules = {
  required: (value: any) => !!value || 'Field ini wajib diisi',
};

// --- Dynamic Headers based on Filter ---
const baseHeaders = [
  { title: 'No', key: 'nomor', sortable: false, width: '3%' }, // Beri lebar sangat kecil
  // ATUR LEBAR NAMA DAN ALAMAT SECARA EKSPLISIT
  { title: 'Nama Pelanggan', key: 'pelanggan.nama', sortable: true, width: '13%' },
  { title: 'Alamat', key: 'pelanggan.alamat', sortable: false, width: '10%' },
  { title: 'No. Telepon', key: 'pelanggan.no_telp', sortable: false, width: '9%' },
  { title: 'Paket Layanan', key: 'paket_layanan_id', width: '11%' },
  { title: 'Metode Bayar', key: 'metode_pembayaran', align: 'center', width: '9%' },
  { title: 'Harga', key: 'harga_final', align: 'end', width: '7%' },
  { title: 'Status', key: 'status', align: 'center', width: '8%' },
  { title: 'Jatuh Tempo', key: 'tgl_jatuh_tempo', align: 'center', width: '8%' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center', width: '18%' },
];

// Alasan Berhenti header yang akan ditambahkan saat filter = "Berhenti"
const alasanBerhentiHeader = {
  title: 'Alasan Berhenti',
  key: 'alasan_berhenti',
  sortable: false,
  width: '12%'
};

// Status Modem header yang akan ditambahkan saat filter bukan "Suspended"
const statusModemHeader = {
  title: 'Status Modem',
  key: 'status_modem',
  sortable: false,
  width: '10%',
  align: 'center'
};

// Status WhatsApp header yang akan ditambahkan saat filter = "Suspended"
const whatsappStatusHeader = {
  title: 'Status WhatsApp',
  key: 'whatsapp_status',
  sortable: false,
  width: '8%',
  align: 'center'
};

// Computed headers yang dinamis berdasarkan filter
const headers = computed(() => {
  let newHeaders: any[] = [...baseHeaders];
  const statusIndex = baseHeaders.findIndex(h => h.key === 'status');

  // Logic untuk menambahkan kolom berdasarkan filter
  let columnsAdded = 0;

  // Tambahkan Status Modem untuk filter "Aktif" atau "Berhenti"
  if (selectedStatus.value === 'Aktif' || selectedStatus.value === 'Berhenti') {
    newHeaders.splice(statusIndex + 1 + columnsAdded, 0, statusModemHeader);
    columnsAdded++;
  }

  // Tambahkan Status WhatsApp hanya untuk filter "Suspended"
  if (selectedStatus.value === 'Suspended') {
    newHeaders.splice(statusIndex + 1 + columnsAdded, 0, whatsappStatusHeader);
    columnsAdded++;
  }

  // Tambahkan Alasan Berhenti hanya untuk filter "Berhenti"
  if (selectedStatus.value === 'Berhenti') {
    newHeaders.splice(statusIndex + 1 + columnsAdded, 0, alasanBerhentiHeader);
    columnsAdded++;
  }

  // Adjust width kolom lain untuk balance
  return newHeaders.map((header: any) => {
    if (header.key === 'actions') {
      return { ...header, width: columnsAdded > 0 ? '8%' : '10%' };
    }
    if (header.key === 'harga_final') {
      return { ...header, width: columnsAdded > 0 ? '7%' : '8%' };
    }
    if (header.key === 'tgl_jatuh_tempo') {
      return { ...header, width: columnsAdded > 1 ? '8%' : '10%' };
    }
    return header;
  });
});

// --- Computed Properties ---
const formTitle = computed(() => (editedIndex.value === -1 ? 'Tambah Langganan Baru' : 'Edit Langganan'));
const isFormValid = computed(() => !!(editedItem.value.pelanggan_id && editedItem.value.paket_layanan_id && editedItem.value.status));

// --- Lifecycle ---
onMounted(() => {
  fetchLangganan();
  fetchPelangganForSelect();
  fetchPaketLayananForSelect();
  fetchAlamatOptions();
  // fetchTotalCount(); // This is now redundant

  window.addEventListener('new-notification', handleNewNotification);

});

onUnmounted(() => {
  window.removeEventListener('new-notification', handleNewNotification);
});


const dropdownPelangganSource = computed(() => {
  if (notificationPelangganList.value) {
    return notificationPelangganList.value;
  }

  // Saat mode Edit, tampilkan semua pelanggan agar pilihan yang ada tidak hilang
  if (isEditMode.value) {
    return pelangganSelectList.value;
  }

  // Saat mode Tambah: HANYA tampilkan pelanggan yang benar-benar baru (belum pernah ada langganan)
  const newPelangganOnly = pelangganSelectList.value.filter(pelanggan =>
    isPelangganBaru(pelanggan.id)
  );

  return newPelangganOnly;
});

watch(() => editedItem.value.pelanggan_id, async (newPelangganId) => {
  // Reset HANYA pilihan paket layanan
  editedItem.value.paket_layanan_id = undefined;
  isPaketLocked.value = false;
  
  // Baris yang menyebabkan error ('hargaAwal.value = 0;') sudah dihapus.

  if (!newPelangganId) {
    filteredPaketLayanan.value = [];
    return;
  }

  try {
    // 1. Panggil API untuk mendapatkan detail lengkap pelanggan
    const response = await apiClient.get(`/pelanggan/${newPelangganId}`);
    const pelangganDetail = response.data;

    if (!pelangganDetail || !pelangganDetail.id_brand || !pelangganDetail.layanan) {
      filteredPaketLayanan.value = [];
      return;
    }

    const customerBrandId = pelangganDetail.id_brand;
    const customerLayananName = pelangganDetail.layanan;

    // 2. Saring daftar paket berdasarkan brand pelanggan
    filteredPaketLayanan.value = paketLayananSelectList.value.filter(
      paket => paket.id_brand === customerBrandId
    );

    // 3. Cari dan pilih paket yang namanya cocok dengan layanan pelanggan
    const matchedPaket = filteredPaketLayanan.value.find(
      paket => paket.nama_paket === customerLayananName
    );

    if (matchedPaket) {
      // Jika paket cocok, langsung pilih paket tersebut.
      // Perubahan ini akan otomatis memicu watch lain yang menghitung harga.
      editedItem.value.paket_layanan_id = matchedPaket.id;
      isPaketLocked.value = true;
    }

  } catch (error) {
    console.error("Gagal mengambil detail pelanggan:", error);
    filteredPaketLayanan.value = [];
  }
}, { immediate: true });


const handleNewNotification = async (event: Event) => {
  const customEvent = event as CustomEvent;
  const notificationData = customEvent.detail;

  if (notificationData.type === 'new_technical_data' && notificationData.data.pelanggan_id) {
    const newPelangganId = notificationData.data.pelanggan_id;
    newPelangganIdMarker.value = newPelangganId;
    
    await fetchPelangganForSelect();
    await fetchLangganan();

    // Cari objek pelanggan yang baru dari daftar yang sudah di-update
    const newPelanggan = pelangganSelectList.value.find(p => p.id === newPelangganId);
    
    if (newPelanggan) {
      // Isi daftar sementara HANYA dengan pelanggan baru tersebut
      notificationPelangganList.value = [newPelanggan];
    }

    openDialog();
    
    nextTick(() => {
      editedItem.value.pelanggan_id = newPelangganId;
    });
  }
};



watch(
  () => [
    editedItem.value.metode_pembayaran, 
    editedItem.value.paket_layanan_id, 
    editedItem.value.pelanggan_id, 
    editedItem.value.tgl_mulai_langganan,
    isProratePlusFull.value // Pantau juga switch
  ],
  async ([metode, paketId, pelangganId, tglMulai, proratePlus]) => {
    
    // Reset rincian harga setiap kali ada perubahan
    hargaProrate.value = 0;
    hargaNormal.value = 0;

    // Jika beralih ke Otomatis, matikan switch
    if (metode === 'Otomatis') {
      isProratePlusFull.value = false;
    }

    if (metode === 'Prorate' && !tglMulai && editedIndex.value === -1) {
      return; 
    }
    
    if (!dialog.value || !paketId || !pelangganId) {
      if(editedIndex.value === -1) {
        editedItem.value.harga_awal = 0;
      }
      return;
    }

    let endpoint = '/langganan/calculate-price';
    // Pilih endpoint yang benar
    if (metode === 'Prorate' && proratePlus) {
      endpoint = '/langganan/calculate-prorate-plus-full';
    }

    try {
      const payload = {
        paket_layanan_id: paketId,
        metode_pembayaran: metode,
        pelanggan_id: pelangganId,
        ...(metode !== 'Otomatis' && { tgl_mulai: tglMulai })
      };
      
      const response = await apiClient.post(endpoint, payload);
      
      // Tangani dua jenis response
      if (metode === 'Prorate' && proratePlus) {
        editedItem.value.harga_awal = response.data.harga_total_awal;
        hargaProrate.value = response.data.harga_prorate || 0;
        hargaNormal.value = response.data.harga_normal || 0;
      } else {
        editedItem.value.harga_awal = response.data.harga_awal;
      }
      
      editedItem.value.tgl_jatuh_tempo = response.data.tgl_jatuh_tempo;
      
    } catch (error: unknown) {
      console.error(`Error memanggil API ${endpoint}:`, error);
      editedItem.value.harga_awal = 0;
    }
  },
  { deep: true }
);



// --- API Methods ---
async function fetchLangganan(isLoadMore = false, explicitPage: number | null = null) {
  if (isLoadMore) {
    loadingMore.value = true;
  } else {
    loading.value = true;
    // Reset pagination for both mobile and desktop when it's not a loadMore action
    if (!isLoadMore && explicitPage === null) {
      desktopPage.value = 1;
      mobilePage.value = 1;
    }
    hasMoreData.value = true; // Reset status "has more"
  }

  try {
    const params = new URLSearchParams();
    if (searchQuery.value) params.append('search', searchQuery.value);
    if (selectedAlamat.value && selectedAlamat.value.trim() !== '') params.append('alamat', selectedAlamat.value.trim());
    if (selectedPaket.value) params.append('paket_layanan_id', String(selectedPaket.value));
    if (selectedStatus.value) params.append('status', selectedStatus.value);

    // --- LOGIKA KUNCI: Tambahkan paginasi ---
    // Determine page number based on the context
    let currentPage: number;
    if (explicitPage !== null) {
      // This is when onPageChange is called directly
      currentPage = explicitPage;
      desktopPage.value = explicitPage; // Update desktop page
    } else if (isLoadMore) {
      // This is for mobile infinite scroll
      currentPage = mobilePage.value;
    } else {
      // For initial load or filter changes, use desktopPage for desktop view
      currentPage = isLoadMore ? mobilePage.value : desktopPage.value;
    }

    const skip = (currentPage - 1) * itemsPerPage.value;
    params.append('skip', String(skip));
    params.append('limit', String(itemsPerPage.value));
    
    const response = await apiClient.get(`/langganan/?${params.toString()}`);
    const { data: newData, total_count: newTotalCount } = response.data;

    let filteredData = newData;
    if (selectedPaket.value) {
      const selectedPackage = paketLayananSelectList.value.find(p => p.id === selectedPaket.value);
      if (selectedPackage) {
        const allSameNamePackageIds = paketLayananSelectList.value
          .filter(p => p.nama_paket === selectedPackage.nama_paket)
          .map(p => p.id);
        
        filteredData = newData.filter((item: Langganan) => 
          allSameNamePackageIds.includes(item.paket_layanan_id)
        );
      }
    }

    if (isLoadMore) {
      langgananList.value.push(...filteredData);
    } else {
      langgananList.value = filteredData;
      totalLanggananCount.value = newTotalCount;

      // Update cache pelanggan baru ketika data berubah (bukan loadMore)
      updatePelangganBaruCache();
    }

    if (langgananList.value.length >= newTotalCount) {
      hasMoreData.value = false;
    } else {
      hasMoreData.value = true;
    }

  } catch (error) {
    console.error("Gagal mengambil data langganan:", error);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function loadMore() {
  if (!loadingMore.value) {
    mobilePage.value++;
    fetchLangganan(true); // Panggil fetch dengan flag isLoadMore
  }
}


function onItemsPerPageChange(itemsPerPageValue: number) {
  itemsPerPage.value = itemsPerPageValue;
  desktopPage.value = 1; // Reset ke halaman pertama saat items per page berubah
  fetchLangganan();
}

// Custom pagination functions
function goToPreviousPage() {
  if (desktopPage.value > 1) {
    const newPage = desktopPage.value - 1;
    desktopPage.value = newPage;
    fetchLangganan(false, newPage);
  }
}

async function goToNextPage() {
  const maxPage = Math.ceil(totalLanggananCount.value / itemsPerPage.value);
  if (desktopPage.value < maxPage) {
    const newPage = desktopPage.value + 1;
    desktopPage.value = newPage;
    await nextTick();
    fetchLangganan(false, newPage);
  }
}

// Fungsi yang di-debounce untuk menerapkan filter
const applyFilters = debounce(() => {
  fetchLangganan();
}, 500); // Tunda 500ms

// Perhatikan perubahan pada filter dan panggil fungsi applyFilters
watch([searchQuery, selectedAlamat, selectedPaket, selectedStatus], () => {
  applyFilters();
});


async function confirmBulkDelete() {
  const itemsToDelete = [...selectedLangganan.value];
  if (itemsToDelete.length === 0) return;

  deleting.value = true;
  try {
    const deletePromises = itemsToDelete.map(langganan =>
      apiClient.delete(`/langganan/${langganan.id}`)
    );
    await Promise.all(deletePromises);

    // Asumsi Anda punya fungsi showSnackbar
    // showSnackbar(`${itemsToDelete.length} langganan berhasil dihapus.`, 'success');
    
    fetchLangganan();
    selectedLangganan.value = [];
  } catch (error) {
    console.error("Gagal melakukan hapus massal langganan:", error);
    // showSnackbar('Terjadi kesalahan saat menghapus data.', 'error');
  } finally {
    deleting.value = false;
    dialogBulkDelete.value = false;
  }
}

const alamatOptions = ref<string[]>([]);

// Fungsi untuk mengambil semua alamat dari database
async function fetchAlamatOptions() {
  // Skip endpoint yang menyebabkan error 405, langsung ambil dari data pelanggan
  try {
    // Ambil pelanggan dengan parameter untuk mendapatkan semua data yang mungkin dibutuhkan
    const response = await apiClient.get('/pelanggan/?limit=10000');
    const pelangganData = response.data.data || response.data;
    
    if (Array.isArray(pelangganData)) {
      const allAlamat = pelangganData
        .map(pelanggan => pelanggan.alamat || '')
        .filter(alamat => typeof alamat === 'string' && alamat.trim() !== '');
      alamatOptions.value = [...new Set(allAlamat)].sort();
    } else {
      // Jika tidak mendapatkan format data yang diharapkan, gunakan data dari langgananList sebagai fallback
      if (langgananList.value && Array.isArray(langgananList.value) && langgananList.value.length > 0) {
        const allAlamat = langgananList.value
          .map(item => item.pelanggan?.alamat || '')
          .filter(alamat => typeof alamat === 'string' && alamat.trim() !== '');
        alamatOptions.value = [...new Set(allAlamat)].sort();
      } else {
        alamatOptions.value = [];
      }
    }
  } catch (error) {
    console.warn("Gagal mengambil alamat dari pelanggan, menggunakan data lokal:", error);
    // Fallback ke data lokal dari langgananList
    if (langgananList.value && Array.isArray(langgananList.value) && langgananList.value.length > 0) {
      const allAlamat = langgananList.value
        .map(item => item.pelanggan?.alamat || '')
        .filter(alamat => typeof alamat === 'string' && alamat.trim() !== '');
      alamatOptions.value = [...new Set(allAlamat)].sort();
    } else {
      alamatOptions.value = [];
    }
  }
}

const uniquePaketLayananOptions = computed(() => {
  if (!paketLayananSelectList.value || paketLayananSelectList.value.length === 0) {
    return [];
  }
  // Create a Set to store unique package names
  const uniqueNames = new Set<string>();
  const uniquePackages: PaketLayananSelectItem[] = [];

  paketLayananSelectList.value.forEach(item => {
    if (!uniqueNames.has(item.nama_paket)) {
      uniqueNames.add(item.nama_paket);
      uniquePackages.push(item);
    }
  });

  return uniquePackages;
});

// Fungsi untuk mereset semua filter
function resetFilters() {
  searchQuery.value = '';
  selectedAlamat.value = '';
  selectedPaket.value = null;
  selectedStatus.value = null;
}
// ============================================

// eligiblePelangganForSelect sudah tidak digunakan lagi, digantikan oleh dropdownPelangganSource

async function fetchPelangganForSelect() {
  try {
    // Load semua pelanggan tanpa limit untuk dropdown select
    // Gunakan for_invoice_selection=true untuk menghilangkan limit
    const response = await apiClient.get<{ data: PelangganSelectItem[] }>('/pelanggan/?for_invoice_selection=true');

    if (response.data && Array.isArray(response.data.data)) {
      pelangganSelectList.value = response.data.data;

      // Background: Update cache untuk semua pelanggan
      updatePelangganBaruCache();
    } else {
      console.error("Struktur data pelanggan dari API tidak sesuai. Properti 'data' tidak ditemukan atau bukan array:", response.data);
      pelangganSelectList.value = [];
    }
  } catch (error) {
    console.error("Gagal mengambil data pelanggan untuk select:", error);
    pelangganSelectList.value = [];
  }
}

// Fungsi untuk mengupdate cache pelanggan baru secara asynchronous
async function updatePelangganBaruCache() {
  // Clear cache lama
  pelangganBaruCache.clear();

  try {
    // Load semua langganan tanpa pagination untuk checking yang akurat
    const response = await apiClient.get('/langganan/?limit=10000');
    const allLangganan = response.data.data || response.data;

    if (Array.isArray(allLangganan)) {
      // Buat Set dari semua pelanggan_id yang sudah ada langganan
      const existingPelangganIds = new Set(allLangganan.map((l: any) => l.pelanggan_id));

      // Update cache untuk semua pelanggan
      pelangganSelectList.value.forEach(pelanggan => {
        const isNew = !existingPelangganIds.has(pelanggan.id);
        pelangganBaruCache.set(pelanggan.id, isNew);
      });
    } else {
      // Fallback: gunakan data dari current page
      const existingPelangganIds = new Set(langgananList.value.map(l => l.pelanggan_id));
      pelangganSelectList.value.forEach(pelanggan => {
        const isNew = !existingPelangganIds.has(pelanggan.id);
        pelangganBaruCache.set(pelanggan.id, isNew);
      });
    }
  } catch (error) {
    console.warn('Gagal mengupdate cache pelanggan baru, menggunakan fallback:', error);
    // Fallback: gunakan data dari current page
    const existingPelangganIds = new Set(langgananList.value.map(l => l.pelanggan_id));
    pelangganSelectList.value.forEach(pelanggan => {
      const isNew = !existingPelangganIds.has(pelanggan.id);
      pelangganBaruCache.set(pelanggan.id, isNew);
    });
  }
}

async function fetchPaketLayananForSelect() {
  paketLoading.value = true;
  try {
    const response = await apiClient.get<PaketLayananSelectItem[]>('/paket_layanan/');
    paketLayananSelectList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data paket layanan untuk select:", error);
    paketLayananSelectList.value = [];
  } finally {
    paketLoading.value = false;
  }
}

function openDialog(item?: Langganan) {
  editedIndex.value = item ? langgananList.value.findIndex(l => l.id === item.id) : -1;
  editedItem.value = item ? { ...item } : { ...defaultItem };
  dialog.value = true;
}

function navigateToEdit(item: Langganan) {
  router.push(`/langganan/${item.id}/edit`);
}

function closeDialog() {
  dialog.value = false;
  // Reset daftar sementara saat dialog ditutup
  notificationPelangganList.value = null; 
  setTimeout(() => {
    editedItem.value = { ...defaultItem };
    editedIndex.value = -1;
  }, 300);
}

async function saveLangganan() {
  // Validasi form (tidak berubah)
  if (!isFormValid.value) return;
  
  saving.value = true;
  
  // Siapkan payload yang akan dikirim ke backend
  const dataToSave = {
    pelanggan_id: editedItem.value.pelanggan_id,
    paket_layanan_id: editedItem.value.paket_layanan_id,
    status: editedItem.value.status,
    metode_pembayaran: editedItem.value.metode_pembayaran,
    tgl_mulai_langganan: editedItem.value.tgl_mulai_langganan,

    // Kirim status switch ke backend
    sertakan_bulan_depan: isProratePlusFull.value 
  };

  try {
    if (editedIndex.value > -1) {
      // Logika update tidak perlu mengirim 'sertakan_bulan_depan'
      // jadi kita bisa gunakan payload yang lebih sederhana
      const updatePayload = {
        paket_layanan_id: editedItem.value.paket_layanan_id,
        status: editedItem.value.status,
        metode_pembayaran: editedItem.value.metode_pembayaran,
        tgl_jatuh_tempo: editedItem.value.tgl_jatuh_tempo,
        harga_awal: editedItem.value.harga_awal,
        alasan_berhenti: editedItem.value.alasan_berhenti || null,
        status_modem: editedItem.value.status_modem || null
      };
      await apiClient.patch(`/langganan/${editedItem.value.id}`, updatePayload);
      showSnackbar('Data langganan berhasil diperbarui', 'success');
    } else {
      // Saat membuat baru, kirim payload yang sudah kita siapkan
      await apiClient.post('/langganan/', dataToSave);
      showSnackbar('Data langganan berhasil ditambahkan', 'success');
    }
    fetchLangganan();
    closeDialog();
  } catch (error) {
    console.error("Gagal menyimpan data langganan:", error);
    showSnackbar('Gagal menyimpan data langganan', 'error');
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: Langganan) {
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
    await apiClient.delete(`/langganan/${itemToDelete.value.id}`);
    fetchLangganan();
    closeDeleteDialog();
  } catch (error) {
    console.error("Gagal menghapus langganan:", error);
  } finally {
    deleting.value = false;
  }
}

// function isPelangganExisting(pelangganId: number): boolean {
//   // Cari apakah pelanggan sudah pernah memiliki langganan sebelumnya
//   // yang sudah disimpan (memiliki ID dan bukan item yang sedang diedit)
//   return langgananList.value.some(l =>
//     l.pelanggan_id === pelangganId &&
//     l.id !== editedItem.value.id // Exclude current editing item
//   );
// }

// Cache untuk hasil pengecekan pelanggan
const pelangganBaruCache = new Map<number, boolean>();

// Fungsi: Cek apakah pelanggan benar-benar baru (belum pernah ada invoice/langganan sama sekali)
function isPelangganBaru(pelangganId: number): boolean {
  if (!pelangganId) return false;

  // Cek cache dulu
  if (pelangganBaruCache.has(pelangganId)) {
    return pelangganBaruCache.get(pelangganId)!;
  }

  // Cek di langgananList yang sudah dimuat (current page)
  const hasLanggananSebelumnya = langgananList.value.some(l => l.pelanggan_id === pelangganId);

  // Cache hasilnya
  pelangganBaruCache.set(pelangganId, !hasLanggananSebelumnya);

  // Jika belum pernah ada langganan sama sekali, ini adalah pelanggan benar-benar baru
  return !hasLanggananSebelumnya;
}


// --- Helper Methods ---
function getPelangganName(pelangganId: number | undefined): string {
  if (!pelangganId) return 'N/A';

  // Check if pelangganSelectList.value is an array before calling .find()
  if (!Array.isArray(pelangganSelectList.value)) {
    return `ID ${pelangganId}`;
  }
  const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
  return pelanggan?.nama || `ID ${pelangganId}`;
}

function getPelangganAlamat(pelangganId: number | undefined): string {
  if (!pelangganId) return 'Alamat tidak tersedia';

  // Prioritaskan data dari backend yang sudah ter-load di langgananList
  if (Array.isArray(langgananList.value)) {
    const langganan = langgananList.value.find(l => l.pelanggan_id === pelangganId);
    if (langganan?.pelanggan?.alamat) {
      return langganan.pelanggan.alamat;
    }
  }

  // Fallback: Cari dari pelangganSelectList jika tidak ada di backend
  if (Array.isArray(pelangganSelectList.value)) {
    const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
    if (pelanggan?.alamat) {
      return pelanggan.alamat;
    }
    return pelanggan ? 'Alamat tersedia' : 'Alamat tidak tersedia';
  }

  return 'Alamat tidak tersedia';
}

function getPelangganPhone(pelangganId: number | undefined): string {
  if (!pelangganId) return 'N/A';

  // Prioritaskan data dari backend yang sudah ter-load di langgananList
  if (Array.isArray(langgananList.value)) {
    const langganan = langgananList.value.find(l => l.pelanggan_id === pelangganId);
    if (langganan?.pelanggan?.no_telp) {
      return langganan.pelanggan.no_telp;
    }
  }

  // Fallback: Cari dari pelangganSelectList jika tidak ada di backend
  if (Array.isArray(pelangganSelectList.value)) {
    const pelanggan = pelangganSelectList.value.find(p => p.id === pelangganId);
    if (pelanggan?.no_telp) {
      return pelanggan.no_telp;
    }
  }

  return 'N/A';
}

function getPaketName(paketId: number | undefined): string {
    if (!paketId) return 'N/A';
    // Check if paketLayananSelectList.value is an array before calling .find()
    if (!Array.isArray(paketLayananSelectList.value)) {
      return `ID Paket ${paketId}`;
    }
    const paket = paketLayananSelectList.value.find(p => p.id === paketId);
    return paket?.nama_paket || `ID Paket ${paketId}`;
}

function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'aktif': return 'green';
    case 'non-aktif': return 'orange';
    case 'berhenti': return 'red';
    default: return 'grey';
  }
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateString: string | Date | null | undefined, includeTime: boolean = false): string {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Invalid Date';

  if (includeTime) {
    // Format dengan timezone WIB
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Jakarta'
    };

    const formattedDate = date.toLocaleString('id-ID', options);

    // Ganti koma dengan "pukul" dan tambahkan WIB
    return formattedDate.replace(/,/g, ' pukul') + ' WIB';
  } else {
    return date.toLocaleDateString('id-ID', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
  }
}



async function exportLangganan() {
  exporting.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    if (selectedAlamat.value && selectedAlamat.value.trim() !== '') {
      params.append('alamat', selectedAlamat.value.trim());
    }
    if (selectedPaket.value) {
      params.append('paket_layanan_id', String(selectedPaket.value));
    }
    if (selectedStatus.value) {
      params.append('status', selectedStatus.value);
    }
    // Tambahkan flag untuk export semua data (tanpa pagination)
    params.append('export_all', 'true');

    const queryString = params.toString();
    const exportUrl = `/langganan/export/csv${queryString ? '?' + queryString : ''}`;

    const response = await apiClient.get(exportUrl, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `export_langganan_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error("Gagal mengekspor data langganan:", error);
  } finally {
    exporting.value = false;
  }
}


async function importFromCsv() {
  const file = fileToImport.value[0];
  if (!file) return;

  importing.value = true;
  importErrors.value = [];
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post('/langganan/import/csv', formData);
    // Tampilkan notifikasi sukses
    console.log(response.data.message);
    fetchLangganan(); // Muat ulang data
    closeImportDialog();
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    if (detail && detail.errors) {
      importErrors.value = detail.errors;
    } else {
      importErrors.value = [detail || "Terjadi kesalahan."];
    }
  } finally {
    importing.value = false;
  }
}

function formatAlasanBerhenti(alasan: string | null | undefined, status: string): string {
  if (status !== 'Berhenti') return '-';
  return alasan || 'Tidak ada alasan';
}

function formatModemStatus(statusModem: string | null | undefined, langgananStatus: string): string {
  // Jika status langganan Suspended, tampilkan "-"
  if (langgananStatus === 'Suspended') return '-';

  // Jika status langganan Aktif atau Berhenti
  if (statusModem) return statusModem;

  // Default logic berdasarkan status langganan
  if (langgananStatus === 'Aktif') return 'Terpasang';
  if (langgananStatus === 'Berhenti') return 'Diambil';

  return '-';
}

function getModemStatusColor(statusModem: string | null | undefined, langgananStatus: string): string {
  const modemStatus = formatModemStatus(statusModem, langgananStatus);

  switch (modemStatus) {
    case 'Terpasang': return 'success';
    case 'Diambil': return 'warning';
    case 'Rusak': return 'error';
    case 'Replacement': return 'info';
    default: return 'grey';
  }
}

function getStatusModemOptions(langgananStatus: string): Array<{title: string, value: string}> {
  if (langgananStatus === 'Aktif') {
    return [
      { title: '✅ Terpasang', value: 'Terpasang' },
      { title: '🔄 Replacement', value: 'Replacement' },
      { title: '❌ Rusak', value: 'Rusak' }
    ];
  } else if (langgananStatus === 'Berhenti') {
    return [
      { title: '✅ Diambil', value: 'Diambil' },
      { title: '❌ Hilang', value: 'Hilang' },
      { title: '💥 Rusak', value: 'Rusak' }
    ];
  }
  return [];
}

// --- WhatsApp Functions ---
async function sendWhatsApp(item: Langganan) {
  const phoneNumber = getPelangganPhone(item.pelanggan_id);

  if (phoneNumber === 'N/A' || !phoneNumber) {
    // Tampilkan alert bahwa nomor telepon tidak tersedia
    alert('Nomor telepon pelanggan tidak tersedia');
    return;
  }

  // Format nomor telepon untuk WhatsApp
  const formattedPhone = phoneNumber.replace(/^0/, '62').replace(/[-\s]/g, '');

  // Format tanggal jatuh tempo
  const jatuhTempo = item.tgl_jatuh_tempo ?
    new Date(item.tgl_jatuh_tempo).toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    }) : 'N/A';

  // Ambil ID Pelanggan dari Data Teknis
  let idPelanggan = item.id; // fallback ke langganan_id
  try {
    const dataTeknisResponse = await apiClient.get(`/data_teknis/by-pelanggan/${item.pelanggan_id}`);
    if (dataTeknisResponse.data && dataTeknisResponse.data.length > 0) {
      // Cari yang cocok dengan langganan ini
      const dataTeknis = dataTeknisResponse.data.find((dt: any) =>
        dt.nama_pelanggan === item.pelanggan?.nama ||
        dt.no_telp === item.pelanggan?.no_telp
      );
      if (dataTeknis && dataTeknis.id_pelanggan) {
        idPelanggan = dataTeknis.id_pelanggan;
      }
    }
  } catch (error) {
    console.warn('Gagal mengambil ID Pelanggan dari Data Teknis, menggunakan fallback:', error);
  }

  // Buat pesan WhatsApp (sesuai template yang diminta)
  const message = `Halo ${item.pelanggan?.nama || 'Pelanggan'},

Kami dari tim support Artacom. Langganan internet Anda dengan nomor ${idPelanggan} saat ini dalam status SUSPENDED.

Mohon segera melakukan pembayaran untuk mengaktifkan kembali layanan internet Anda.

Total tagihan: Rp ${item.harga_awal?.toLocaleString('id-ID') || '0'}
Jatuh tempo: ${jatuhTempo}

Terima kasih atas perhatian Anda.`;

  // Encode pesan untuk URL
  const encodedMessage = encodeURIComponent(message);

  // Buka WhatsApp dengan nomor dan pesan
  const whatsappUrl = `https://wa.me/${formattedPhone}?text=${encodedMessage}`;
  window.open(whatsappUrl, '_blank');

  // Update status WhatsApp di database
  try {
    const response = await apiClient.patch(`/langganan/${item.id}`, {
      whatsapp_status: 'sent',
      last_whatsapp_sent: new Date().toISOString()
    });

    if (response.data) {
      // Update data di frontend
      const index = langgananList.value.findIndex(l => l.id === item.id);
      if (index !== -1) {
        langgananList.value[index] = {
          ...langgananList.value[index],
          whatsapp_status: 'sent',
          last_whatsapp_sent: new Date().toISOString()
        };
      }
    }

    console.log('WhatsApp status updated successfully');

  } catch (error: any) {
    console.error('Error updating WhatsApp status:', error);

    // Fallback: tetap update status di frontend
    const index = langgananList.value.findIndex(l => l.id === item.id);
    if (index !== -1) {
      langgananList.value[index] = {
        ...langgananList.value[index],
        whatsapp_status: 'sent',
        last_whatsapp_sent: new Date().toISOString()
      };
    }
  }
}

// Function to open Pelanggan View Modal
async function openPelangganView(item: Langganan) {
  selectedPelanggan.value = item;
  pelangganViewDialog.value = true;

  // Fetch data teknis to get ID Pelanggan from Data Teknis
  try {
    const response = await apiClient.get(`/data_teknis/by-pelanggan/${item.pelanggan_id}`);
    if (response.data && response.data.length > 0) {
      dataTeknisInfo.value = response.data[0]; // Ambil data teknis pertama
    } else {
      dataTeknisInfo.value = null;
    }
  } catch (error) {
    console.warn('Data teknis not found:', error);
    dataTeknisInfo.value = null;
  }

  try {
    // Use existing search parameter to find invoices by pelanggan name/id
    // Non-disruptive approach - no API changes needed
    const customerName = getPelangganName(item.pelanggan_id);
    const customerId = item.pelanggan_id.toString();

    // Try both name and ID in search to maximize results
    const searchTerms = [customerName, customerId];
    let allInvoices: any[] = [];

    for (const searchTerm of searchTerms) {
      try {
        const response = await apiClient.get(`/invoices?search=${encodeURIComponent(searchTerm)}`);
        if (response.data && Array.isArray(response.data)) {
          // Filter results to ensure they belong to this customer
          const customerInvoices = response.data.filter((invoice: any) =>
            invoice.pelanggan_id === item.pelanggan_id ||
            invoice.id_pelanggan === customerId ||
            invoice.no_telp === getPelangganPhone(item.pelanggan_id)
          );
          allInvoices.push(...customerInvoices);
        }
      } catch (searchError) {
        console.warn(`Search with term "${searchTerm}" failed:`, searchError);
      }
    }

    // Remove duplicates by ID
    const uniqueInvoices = allInvoices.filter((invoice, index, self) =>
      index === self.findIndex((inv) => inv.id === invoice.id)
    );

    if (uniqueInvoices.length > 0) {
      paymentHistory.value = uniqueInvoices.map((invoice: any) => {
        // Calculate keterlambatan (days late)
        let terlambat = 0;
        if (invoice.paid_at && invoice.tgl_jatuh_tempo) {
          const payDate = new Date(invoice.paid_at);
          const dueDate = new Date(invoice.tgl_jatuh_tempo);
          terlambat = Math.ceil((payDate.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24));
        }

        return {
          id: invoice.invoice_number || `INV-${invoice.id}`,
          tanggal_bayar: invoice.paid_at || invoice.tgl_jatuh_tempo,
          jumlah: invoice.total_harga || 0,
          status_pembayaran: invoice.status_invoice || (invoice.paid_at ? 'Lunas' : 'Menunggu'),
          terlambat: Math.max(0, terlambat)
        };
      });

      // Calculate payment statistics
      const totalInvoices = uniqueInvoices.length;
      const latePayments = uniqueInvoices.filter((invoice: any) => {
        if (!invoice.paid_at) return false;
        const payDate = new Date(invoice.paid_at);
        const dueDate = new Date(invoice.tgl_jatuh_tempo);
        return payDate > dueDate;
      }).length;

      paymentStats.value = {
        totalInvoices,
        lateCount: latePayments,
        onTimeCount: totalInvoices - latePayments
      };
    } else {
      // No invoices found
      paymentHistory.value = [];
      paymentStats.value = {
        totalInvoices: 0,
        lateCount: 0,
        onTimeCount: 0
      };
    }

  } catch (error) {
    console.error('Error fetching payment history:', error);
    paymentHistory.value = [];
    paymentStats.value = {
      totalInvoices: 0,
      lateCount: 0,
      onTimeCount: 0
    };
  }
}

// --- HELPER FUNCTIONS ---
function showSnackbar(text: string, color: 'success' | 'error' | 'warning') {
  snackbar.value = { show: true, text, color };
}

// getPelangganName function sudah ada di line 2206, gunakan yang sudah ada
</script>

<style scoped>
/* ============================================
   MOBILE-FIRST RESPONSIVE DESIGN
   ============================================ */

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
  align-items: stretch !important;
}

.header-info {
  width: 100%;
  justify-content: flex-start;
  margin-bottom: 0;
}

.header-avatar-wrapper {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.header-title {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 4px;
}

.header-subtitle {
  font-size: 1.05rem;
  opacity: 0.85;
  line-height: 1.3;
}

/* Action Buttons Container - Fixed Positioning */
.action-buttons-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-self: flex-end;
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

.upload-title {
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  font-size: 1rem;
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

.nav-btn {
  border-radius: 10px;
  font-weight: 600;
  text-transform: none;
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
    align-self: center;
  }

  .mobile-btn {
    width: auto;
    min-width: 140px;
  }
}

/* Large Desktop (1024px and up) */
@media (min-width: 1024px) {
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
}

/* Dark Theme Adjustments */
.v-theme--dark .header-card {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .import-card {
  background: #1e293b;
  border-color: #334155;
}

.v-theme--dark .error-item {
  background: rgba(var(--v-theme-error), 0.1);
}

/* ============================================
   BASE CONTAINER STYLING
   ============================================ */
.v-container {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Light Mode Base */
.v-theme--light .v-container {
  background: linear-gradient(135deg, 
    var(--light-bg-secondary) 0%, 
    var(--light-bg-tertiary) 100%);
  color: var(--light-text-primary);
}

/* Dark Mode Base */
.v-theme--dark .v-container {
  background: linear-gradient(135deg, 
    var(--dark-bg-primary) 0%, 
    var(--dark-bg-secondary) 100%);
  color: var(--dark-text-primary);
}

/* ============================================
   HEADER SECTION STYLING
   ============================================ */
.header-section {
  margin-bottom: 32px;
  padding: 24px 0;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
}

/* Light Mode Header */
.v-theme--light .header-section {
  background: linear-gradient(135deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%);
  border: 1px solid var(--light-border);
  box-shadow: 0 4px 20px var(--light-shadow);
}

/* Dark Mode Header */
.v-theme--dark .header-section {
  background: linear-gradient(135deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%);
  border: 1px solid var(--dark-border);
  box-shadow: 0 4px 20px var(--dark-shadow);
}

/* Header Icon Styling */
.header-section .v-avatar {
  box-shadow: 0 4px 16px rgba(var(--primary-500), 0.3);
}

.header-section .text-primary {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}


/* Enhanced Form Dialog Styling */
        .subscription-form-container {
            max-width: 100vw;
            max-height: 100vh;
            overflow-y: auto;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            font-family: 'Inter', 'Roboto', sans-serif;
        }

        .form-dialog {
            border-radius: 24px !important;
            overflow: hidden;
            max-width: 800px;
            margin: 20px auto;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15), 0 15px 40px rgba(0, 0, 0, 0.1) !important;
            background: white;
        }

        /* Enhanced Header */
        .form-header {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #4338ca 100%) !important;
            position: relative;
            overflow: hidden;
            padding: 32px !important;
            color: white;
        }

        .form-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 200px;
            height: 200%;
            background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
            transform: rotate(25deg);
            transition: all 0.5s ease;
        }

        .form-header:hover::before {
            right: -10%;
            transform: rotate(25deg) scale(1.1);
        }

        .form-header-content {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .form-icon-wrapper {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .form-icon {
            background: white !important;
            color: #6366f1 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            width: 48px !important;
            height: 48px !important;
        }

        .form-title {
            font-size: 2rem !important;
            font-weight: 800 !important;
            margin-bottom: 8px !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: 0.5px !important;
            line-height: 1.2 !important;
        }

        .form-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem !important;
            font-weight: 400 !important;
            margin: 0 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            line-height: 1.4 !important;
            letter-spacing: 0.2px !important;
        }

        /* Form Content */
        .form-content {
            padding: 32px !important;
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        }

        /* Form Sections */
        .form-section {
            margin-bottom: 40px !important;
            position: relative;
        }

        .form-section:last-child {
            margin-bottom: 24px !important;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px !important;
            padding: 16px 0 12px 0;
            position: relative;
        }

        .section-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 40px;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, 
                rgba(99, 102, 241, 0.3) 0%,
                rgba(99, 102, 241, 0.1) 50%,
                transparent 100%
            );
        }

        .section-title {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 0.8px !important;
            margin: 0;
        }

        .section-icon {
            color: #6366f1 !important;
            font-size: 1.3rem !important;
        }

        /* Enhanced Form Fields */
        .enhanced-field {
            margin-bottom: 24px !important;
        }

        .enhanced-field .v-field {
            border-radius: 16px !important;
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid rgba(99, 102, 241, 0.1) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
            min-height: 56px !important;
        }

        .enhanced-field .v-field:hover {
            background: rgba(255, 255, 255, 1) !important;
            border-color: rgba(99, 102, 241, 0.3) !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.1) !important;
        }

        .enhanced-field .v-field--focused {
            background: white !important;
            border-color: #6366f1 !important;
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15), 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
        }

        .enhanced-field .v-field__input {
            padding: 16px 20px !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            min-height: 24px !important;
        }

        .enhanced-field .v-field__prepend-inner .v-icon {
            color: rgba(99, 102, 241, 0.7) !important;
            font-size: 1.2rem !important;
            margin-right: 12px !important;
        }

        .enhanced-field .v-field--focused .v-field__prepend-inner .v-icon {
            color: #6366f1 !important;
            transform: scale(1.05);
        }

        /* Price Field Special Styling */
        .price-field .v-field {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
            border-color: rgba(14, 165, 233, 0.3) !important;
        }

        .price-field .v-field:hover {
            border-color: rgba(14, 165, 233, 0.5) !important;
        }

        .price-field .v-field--focused {
            border-color: #0ea5e9 !important;
            box-shadow: 0 8px 25px rgba(14, 165, 233, 0.15), 0 0 0 4px rgba(14, 165, 233, 0.1) !important;
        }

        .price-field .v-field__input {
            color: #0369a1 !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }

        /* Row and Column Spacing */
        .v-row {
            margin-bottom: 16px !important;
        }

        .v-row:last-child {
            margin-bottom: 0 !important;
        }

        /* Switch Styling */
        .v-switch {
            margin-top: 8px;
        }

        /* Alert Styling */
        .v-alert {
            border-radius: 16px !important;
            margin-bottom: 20px !important;
            border: 1px solid rgba(59, 130, 246, 0.2) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08) !important;
        }

        .v-alert--variant-tonal {
            background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%) !important;
        }

        /* Action Footer */
        .action-footer {
            background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
            border-top: 1px solid rgba(0, 0, 0, 0.06);
            padding: 32px !important;
        }

        .action-buttons {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 16px;
        }

        /* Enhanced Buttons */
        .cancel-btn {
            color: #6b7280 !important;
            background: rgba(107, 114, 128, 0.1) !important;
            border: 1px solid rgba(107, 114, 128, 0.2) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            text-transform: none !important;
            padding: 14px 24px !important;
            min-height: 48px !important;
            transition: all 0.3s ease !important;
        }

        .cancel-btn:hover {
            background: rgba(107, 114, 128, 0.15) !important;
            color: #374151 !important;
            border-color: rgba(107, 114, 128, 0.3) !important;
        }

        .save-btn {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: none !important;
            padding: 14px 32px !important;
            font-size: 1rem !important;
            letter-spacing: 0.3px !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3), 0 3px 10px rgba(99, 102, 241, 0.2) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
            min-height: 48px !important;
        }

        .save-btn:hover {
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4), 0 5px 15px rgba(99, 102, 241, 0.3) !important;
        }

        .save-btn:active {
            transform: translateY(0);
            transition: all 0.1s ease;
        }

        /* Button Ripple Effect */
        .save-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transition: width 0.6s ease, height 0.6s ease;
            transform: translate(-50%, -50%);
            z-index: 0;
        }

        .save-btn:active::before {
            width: 300px;
            height: 300px;
        }

        .save-btn .v-btn__content {
            position: relative;
            z-index: 1;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .form-dialog {
                margin: 16px !important;
                max-width: calc(100vw - 32px) !important;
                border-radius: 16px !important;
            }

            .form-header {
                padding: 24px !important;
            }

            .form-title {
                font-size: 1.5rem !important;
                line-height: 1.3 !important;
                text-align: center;
            }

            .form-subtitle {
                font-size: 0.95rem !important;
                text-align: center;
            }

            .form-content {
                padding: 24px !important;
            }

            .form-section {
                margin-bottom: 32px !important;
            }

            .section-title {
                font-size: 1.1rem !important;
            }

            .action-footer {
                padding: 20px !important;
            }

            .action-buttons {
                flex-direction: column;
                width: 100%;
                gap: 12px;
            }

            .cancel-btn,
            .save-btn {
                width: 100%;
                justify-content: center;
            }

            .form-header-content {
                flex-direction: column;
                text-align: center;
                gap: 16px;
            }
        }

        @media (max-width: 480px) {
            .form-header {
                padding: 20px !important;
            }

            .form-title {
                font-size: 1.3rem !important;
            }

            .form-subtitle {
                font-size: 0.9rem !important;
            }

            .form-content {
                padding: 20px !important;
            }

            .enhanced-field {
                margin-bottom: 20px !important;
            }

            .section-title {
                font-size: 1rem !important;
            }
        }

        /* Dark Theme Support */
        @media (prefers-color-scheme: dark) {
            .subscription-form-container {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            }

            .form-dialog {
                background: #1e1e1e;
            }

            .form-content {
                background: linear-gradient(145deg, #1e1e1e 0%, #2a2a2a 100%);
            }

            .section-title {
                color: #e5e7eb;
            }

            .enhanced-field .v-field {
                background: rgba(42, 42, 42, 0.9) !important;
                border-color: rgba(255, 255, 255, 0.1) !important;
                color: #e5e7eb !important;
            }

            .enhanced-field .v-field:hover {
                background: rgba(46, 46, 46, 1) !important;
                border-color: rgba(99, 102, 241, 0.4) !important;
            }

            .enhanced-field .v-field--focused {
                background: rgba(30, 30, 30, 1) !important;
                border-color: #6366f1 !important;
            }

            .action-footer {
                background: linear-gradient(145deg, #2a2a2a 0%, #3d3d3d 100%);
                border-top-color: rgba(255, 255, 255, 0.1);
            }
        }

        /* Smooth Transitions */
        * {
            transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
        }

        /* Focus Visible States for Accessibility */
        .v-btn:focus-visible,
        .v-field:focus-visible,
        .v-select:focus-visible {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }

        /* Loading State */
        .v-btn--loading {
            pointer-events: none;
        }

        .v-btn--loading .v-btn__overlay {
            background: rgba(255, 255, 255, 0.1);
        }

/* ============================================
   ENHANCED BUTTON STYLING
   ============================================ */


/* Modal Styling */
.subscription-modal {
  border-radius: 16px !important;
  overflow: hidden;
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  width: 100%;
}

.header-title {
  font-size: 2rem !important;
  font-weight: 800 !important;
  margin-bottom: 4px;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 0;
  line-height: 1.3;
}

.modal-content {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 32px;
}

.form-section:last-child {
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(var(--v-border-color), 0.12);
}

.price-field {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.modal-actions {
  padding: 20px 24px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background-color: rgba(var(--v-theme-surface), 0.5);
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-header {
    padding: 20px;
  }
  
  .header-title {
    font-size: 1.8rem !important;
  }
  
  .header-subtitle {
    font-size: 1rem !important;
  }
  
  .modal-content {
    padding: 20px;
    max-height: 65vh;
  }
  
  .form-section {
    margin-bottom: 24px;
  }
  
  .section-title {
    font-size: 0.95rem;
    margin-bottom: 12px;
  }
}

@media (max-width: 600px) {
  .modal-header {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .modal-content {
    padding: 16px;
  }
  
  .modal-actions {
    padding: 16px;
    flex-direction: column;
    gap: 8px;
  }
  
  .modal-actions .v-btn {
    width: 100%;
  }
}

/* Landscape Mobile Optimization */
@media (max-height: 600px) and (orientation: landscape) {
  .modal-content {
    max-height: 50vh;
    padding: 16px 24px;
  }
  
  .form-section {
    margin-bottom: 20px;
  }
  
  .section-title {
    margin-bottom: 12px;
    font-size: 0.9rem;
  }
  
  .modal-header {
    padding: 16px 24px;
  }
  
  .header-title {
    font-size: 1rem;
  }
  
  .header-subtitle {
    font-size: 0.8rem;
  }
}

/* Import Button */
.import-btn {
  background: linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 0 4px 16px rgba(var(--success-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.import-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--success-500), 0.4) !important;
}

/* Export Button */
.export-btn {
  background: linear-gradient(135deg, var(--info-500) 0%, var(--info-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 0 4px 16px rgba(var(--info-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.export-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--info-500), 0.4) !important;
}

/* Add Subscription Button */
.add-subscription-btn {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 16px !important;
  padding: 14px 28px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  font-size: 1rem !important;
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.add-subscription-btn:hover {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%) !important;
  transform: translateY(-3px);
  box-shadow: 0 10px 32px rgba(var(--primary-500), 0.4) !important;
}

/* ============================================
   FILTER CARD STYLING
   ============================================ */
.filter-card {
  border-radius: 20px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  margin-bottom: 24px;
}

/* Light Mode Filter Card */
.v-theme--light .filter-card {
  background: linear-gradient(145deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
  border: 1px solid var(--light-border) !important;
  box-shadow: 0 4px 20px var(--light-shadow) !important;
}

.v-theme--light .filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px var(--light-shadow-hover) !important;
  border-color: rgba(var(--primary-500), 0.2) !important;
}

/* Dark Mode Filter Card */
.v-theme--dark .filter-card {
  background: linear-gradient(145deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
  border: 1px solid var(--dark-border) !important;
  box-shadow: 0 4px 20px var(--dark-shadow) !important;
}

.v-theme--dark .filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px var(--dark-shadow-hover) !important;
  border-color: rgba(var(--primary-500), 0.3) !important;
}

/* Filter Card Top Border Effect */
.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--primary-500) 50%, 
    transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.filter-card:hover::before {
  opacity: 1;
}


.v-data-table :deep(td),
.v-data-table :deep(th) {
  /* Kurangi padding horizontal dari default 16px menjadi 8px */
  padding: 0 8px !important; 
}

/* ============================================
   FORM FIELD STYLING
   ============================================ */

/* Base Field Styling */
.enhanced-form-field .v-field {
  border-radius: 12px !important;
  border-width: 2px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Light Mode Fields */
.v-theme--light .enhanced-form-field .v-field {
  background: rgba(255, 255, 255, 0.9) !important;
  border-color: var(--light-border) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
}

.v-theme--light .enhanced-form-field .v-field:hover {
  background: rgba(255, 255, 255, 1) !important;
  border-color: rgba(var(--primary-500), 0.4) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.1) !important;
}

.v-theme--light .enhanced-form-field .v-field--focused {
  background: white !important;
  border-color: var(--primary-500) !important;
  box-shadow: 0 0 0 4px rgba(var(--primary-500), 0.1) !important;
}

/* Dark Mode Fields */
.v-theme--dark .enhanced-form-field .v-field {
  background: rgba(42, 42, 42, 0.9) !important;
  border-color: var(--dark-border) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
  color: var(--dark-text-primary) !important;
}

.v-theme--dark .enhanced-form-field .v-field:hover {
  background: rgba(46, 46, 46, 1) !important;
  border-color: rgba(var(--primary-500), 0.5) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.2) !important;
}

.v-theme--dark .enhanced-form-field .v-field--focused {
  background: var(--dark-surface-variant) !important;
  border-color: var(--primary-500) !important;
  box-shadow: 0 0 0 4px rgba(var(--primary-500), 0.2) !important;
}

/* Field Input Text Color */
.v-theme--dark .enhanced-form-field .v-field__input {
  color: var(--dark-text-primary) !important;
}

.v-theme--light .enhanced-form-field .v-field__input {
  color: var(--light-text-primary) !important;
}

/* Field Label Colors */
.v-theme--dark .enhanced-form-field .v-field-label {
  color: var(--dark-text-secondary) !important;
}

.v-theme--light .enhanced-form-field .v-field-label {
  color: var(--light-text-secondary) !important;
}

/* ============================================
   DATA TABLE STYLING
   ============================================ */
.v-data-table {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08) !important;
}

/* Light Mode Data Table */
.v-theme--light .v-data-table {
  background: var(--light-surface) !important;
  border: 1px solid var(--light-border) !important;
}

.v-theme--light .v-data-table .v-data-table-header {
  background: linear-gradient(135deg, 
    var(--light-surface-variant) 0%, 
    var(--light-bg-tertiary) 100%) !important;
  border-bottom: 1px solid var(--light-border) !important;
}

.v-theme--light .v-data-table tbody tr:nth-child(even) {
  background: rgba(var(--primary-50), 0.3) !important;
}

.v-theme--light .v-data-table tbody tr:hover {
  background: rgba(var(--primary-50), 0.6) !important;
}

/* Dark Mode Data Table */
.v-theme--dark .v-data-table {
  background: var(--dark-surface) !important;
  border: 1px solid var(--dark-border) !important;
}

.v-theme--dark .v-data-table .v-data-table-header {
  background: linear-gradient(135deg, 
    var(--dark-surface-variant) 0%, 
    var(--dark-bg-tertiary) 100%) !important;
  border-bottom: 1px solid var(--dark-border) !important;
}

.v-theme--dark .v-data-table tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02) !important;
}

.v-theme--dark .v-data-table tbody tr:hover {
  background: rgba(var(--primary-500), 0.1) !important;
}

/* Data Table Text Colors */
.v-theme--dark .v-data-table th,
.v-theme--dark .v-data-table td {
  color: var(--dark-text-primary) !important;
}

.v-theme--light .v-data-table th,
.v-theme--light .v-data-table td {
  color: var(--light-text-primary) !important;
}

/* ============================================
   IMPORT DIALOG STYLING
   ============================================ */
.import-dialog {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.15) !important;
}

/* Import Dialog Header */
.import-dialog-header {
  background: linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%) !important;
  color: white !important;
  padding: 24px 32px !important;
  position: relative;
  overflow: hidden;
}

.import-dialog-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 100px;
  height: 200%;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(15deg);
  transition: all 0.3s ease;
}

/* Import Dialog Content - Light Mode */
.v-theme--light .import-dialog-content {
  background: linear-gradient(145deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
  color: var(--light-text-primary) !important;
}

/* Import Dialog Content - Dark Mode */
.v-theme--dark .import-dialog-content {
  background: linear-gradient(145deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
  color: var(--dark-text-primary) !important;
}

/* Import File Input Styling */
.import-file-input .v-field {
  border-radius: 16px !important;
  border: 3px dashed rgba(var(--success-500), 0.3) !important;
  min-height: 80px !important;
  padding: 16px !important;
  transition: all 0.3s ease !important;
}

/* Light Mode File Input */
.v-theme--light .import-file-input .v-field {
  background: linear-gradient(135deg, 
    rgba(var(--success-50), 0.5) 0%, 
    rgba(var(--success-50), 0.3) 100%) !important;
}

.v-theme--light .import-file-input .v-field:hover {
  background: linear-gradient(135deg, 
    rgba(var(--success-50), 0.8) 0%, 
    rgba(var(--success-50), 0.6) 100%) !important;
  border-color: rgba(var(--success-500), 0.5) !important;
}

/* Dark Mode File Input */
.v-theme--dark .import-file-input .v-field {
  background: linear-gradient(135deg, 
    rgba(var(--success-500), 0.1) 0%, 
    rgba(var(--success-500), 0.05) 100%) !important;
}

.v-theme--dark .import-file-input .v-field:hover {
  background: linear-gradient(135deg, 
    rgba(var(--success-500), 0.15) 0%, 
    rgba(var(--success-500), 0.1) 100%) !important;
  border-color: rgba(var(--success-500), 0.5) !important;
}

/* ============================================
   FORM DIALOG STYLING
   ============================================ */
.subscription-form-dialog {
  border-radius: 24px !important;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15) !important;
}

/* Enhanced Form Header */
.enhanced-form-header {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 50%, var(--primary-700) 100%) !important;
  position: relative;
  overflow: hidden;
  padding: 32px !important;
}

.enhanced-form-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200%;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  transform: rotate(25deg);
  transition: all 0.5s ease;
}

/* Section Cards - Light Mode */
.v-theme--light .enhanced-section-card {
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.9) 100%) !important;
  border: 1px solid rgba(var(--primary-500), 0.1) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
}

.v-theme--light .enhanced-section-card:hover {
  border-color: rgba(var(--primary-500), 0.2) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08) !important;
}

/* Section Cards - Dark Mode */
.v-theme--dark .enhanced-section-card {
  background: linear-gradient(145deg, 
    rgba(30, 30, 30, 0.95) 0%,
    rgba(42, 42, 42, 0.9) 100%) !important;
  border: 1px solid rgba(var(--primary-500), 0.15) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
}

.v-theme--dark .enhanced-section-card:hover {
  border-color: rgba(var(--primary-500), 0.3) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
}

/* ============================================
   ACTION BUTTONS STYLING
   ============================================ */

/* Cancel Button */
.enhanced-cancel-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  padding: 14px 24px !important;
  transition: all 0.3s ease !important;
}

/* Light Mode Cancel Button */
.v-theme--light .enhanced-cancel-btn {
  color: var(--light-text-secondary) !important;
  background: rgba(107, 114, 128, 0.1) !important;
  border: 1px solid rgba(107, 114, 128, 0.2) !important;
}

.v-theme--light .enhanced-cancel-btn:hover {
  background: rgba(107, 114, 128, 0.15) !important;
  color: var(--light-text-primary) !important;
}

/* Dark Mode Cancel Button */
.v-theme--dark .enhanced-cancel-btn {
  color: var(--dark-text-secondary) !important;
  background: rgba(156, 163, 175, 0.1) !important;
  border: 1px solid rgba(156, 163, 175, 0.2) !important;
}

.v-theme--dark .enhanced-cancel-btn:hover {
  background: rgba(156, 163, 175, 0.15) !important;
  color: var(--dark-text-primary) !important;
}

/* Save Button */
.enhanced-save-btn {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  padding: 14px 32px !important;
  font-size: 1rem !important;
  box-shadow: 0 6px 20px rgba(var(--primary-500), 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.enhanced-save-btn:hover {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(var(--primary-500), 0.4) !important;
}

/* ============================================
   ACTION FOOTER STYLING
   ============================================ */

/* Light Mode Action Footer */
.v-theme--light .enhanced-action-footer {
  background: linear-gradient(145deg, 
    var(--light-surface-variant) 0%, 
    var(--light-bg-tertiary) 100%) !important;
  border-top: 1px solid var(--light-border) !important;
}

/* Dark Mode Action Footer */
.v-theme--dark .enhanced-action-footer {
  background: linear-gradient(145deg, 
    var(--dark-surface-variant) 0%, 
    var(--dark-bg-tertiary) 100%) !important;
  border-top: 1px solid var(--dark-border) !important;
}

/* ============================================
   DELETE DIALOG STYLING
   ============================================ */
.delete-header {
  transition: background 0.3s ease;
}

/* Light Mode Delete Header */
.v-theme--light .delete-header {
  background: linear-gradient(135deg, 
    var(--light-surface) 0%, 
    var(--light-surface-variant) 100%) !important;
}

/* Dark Mode Delete Header */
.v-theme--dark .delete-header {
  background: linear-gradient(135deg, 
    var(--dark-surface) 0%, 
    var(--dark-surface-variant) 100%) !important;
}

/* ============================================
   SELECTION TOOLBAR
   ============================================ */
.selection-toolbar {
  border-radius: 12px 12px 0 0;
  transition: all 0.3s ease;
}

/* Light Mode Selection Toolbar */
.v-theme--light .selection-toolbar {
  background: rgba(var(--primary-50), 0.6) !important;
  border-bottom: 1px solid rgba(var(--primary-500), 0.15) !important;
  color: var(--light-text-primary) !important;
}

/* Dark Mode Selection Toolbar */
.v-theme--dark .selection-toolbar {
  background: rgba(var(--primary-500), 0.15) !important;
  border-bottom: 1px solid rgba(var(--primary-500), 0.25) !important;
  color: var(--dark-text-primary) !important;
}

/* ============================================
   CHIP STYLING
   ============================================ */
.v-chip {
  font-weight: 600 !important;
  border-radius: 8px !important;
}

/* Status Chips */
.v-chip--color-green {
  background: linear-gradient(135deg, var(--success-500), var(--success-600)) !important;
  color: white !important;
}

.v-chip--color-red {
  background: linear-gradient(135deg, var(--error-500), var(--error-600)) !important;
  color: white !important;
}

.v-chip--color-blue {
  background: linear-gradient(135deg, var(--info-500), var(--info-600)) !important;
  color: white !important;
}

/* ============================================
   RESPONSIVE ENHANCEMENTS
   ============================================ */

@media (max-width: 768px) {
  /* Fix header title size for mobile */
  .header-card .header-title {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
  }

  .header-card .header-subtitle {
    font-size: 1rem !important;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .import-btn,
  .export-btn,
  .add-subscription-btn {
    width: 100%;
    justify-content: center;
  }
  
  .subscription-form-dialog {
    margin: 16px !important;
    max-width: calc(100vw - 32px) !important;
    border-radius: 16px !important;
  }
  
  .enhanced-form-header {
    padding: 24px !important;
    height: auto; 
  display: flex;
  align-items: center;
  }
  
  .enhanced-section-card {
    padding: 20px !important;
    margin: 0 -4px !important;
  }
  
  .filter-card .d-flex {
    flex-direction: column !important;
    gap: 12px !important;
  }
  
  .enhanced-form-field,
  .v-select,
  .v-text-field {
    min-width: 100% !important;
  }
}

@media (max-width: 480px) {
  .import-dialog-content {
    padding: 20px !important;
  }
  
  .import-dialog-header {
    padding: 20px !important;
  }
  
  .enhanced-action-footer {
    padding: 20px !important;
  }
  
  .enhanced-action-footer .action-buttons {
    flex-direction: column;
    width: 100%;
    gap: 12px;
  }
  
  .enhanced-cancel-btn,
  .enhanced-save-btn {
    width: 100%;
    justify-content: center;
  }
}

/* ============================================
   SMOOTH TRANSITIONS
   ============================================ */
* {
  transition: background-color 0.3s ease,
              border-color 0.3s ease,
              color 0.3s ease,
              box-shadow 0.3s ease;
}

/* ============================================
   ACCESSIBILITY ENHANCEMENTS
   ============================================ */

/* Focus Visible States */
.v-btn:focus-visible,
.v-field:focus-visible,
.v-select:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

/* High Contrast Support */
@media (prefers-contrast: high) {
  :root {
    --light-border: rgba(0, 0, 0, 0.3);
    --dark-border: rgba(255, 255, 255, 0.3);
  }
}

/* ============================================
   TYPOGRAPHY CONSISTENCY
   ============================================ */

/* Ensure consistent font family */
.add-subscription-btn .v-btn__content,
.enhanced-save-btn .v-btn__content,
.enhanced-form-header .form-title,
.enhanced-form-header .form-subtitle,
.enhanced-section-header .section-title,
.step-badge {
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Text selection styling */
.enhanced-form-header .form-title::selection,
.enhanced-form-header .form-subtitle::selection,
.enhanced-section-header .section-title::selection {
  background: rgba(255, 255, 255, 0.3);
  color: inherit;
}

/* Prevent text selection on buttons */
.add-subscription-btn,
.enhanced-save-btn,
.step-badge {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}


/* High contrast mode support */
@media (prefers-contrast: high) {
  .add-subscription-btn,
  .enhanced-save-btn,
  .step-badge {
    border: 2px solid rgba(255, 255, 255, 0.5) !important;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
  }

  .enhanced-section-header .section-title {
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }
}

/* Focus visible states for keyboard navigation */
.add-subscription-btn:focus-visible,
.enhanced-save-btn:focus-visible {
  outline: 3px solid rgba(255, 255, 255, 0.8);
  outline-offset: 2px;
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .add-subscription-btn .v-icon,
  .enhanced-save-btn .v-icon {
    transition: none !important;
  }

  .add-subscription-btn:hover .v-icon {
    transform: none !important;
  }
}

.input-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.required-flag {
  margin-left: 4px;
  font-weight: bold;
}
/* ============================================
   ENHANCED IMPORT/EXPORT BUTTONS STYLING
   ============================================ */

/* Container untuk button group di header */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Enhanced Import Button */
.import-btn {
  position: relative;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 
    0 4px 12px rgba(76, 175, 80, 0.3),
    0 2px 6px rgba(76, 175, 80, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
}

.import-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(76, 175, 80, 0.4),
    0 4px 12px rgba(76, 175, 80, 0.3) !important;
}

.import-btn:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

/* Import button icon animation */
.import-btn .v-icon {
  transition: transform 0.3s ease;
}

.import-btn:hover .v-icon {
  transform: translateY(-2px) scale(1.1);
}

/* Enhanced Export Button */
.export-btn {
  position: relative;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  box-shadow: 
    0 4px 12px rgba(33, 150, 243, 0.3),
    0 2px 6px rgba(33, 150, 243, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
}

.export-btn:hover {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(33, 150, 243, 0.4),
    0 4px 12px rgba(33, 150, 243, 0.3) !important;
}

.export-btn:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

/* Export button icon animation */
.export-btn .v-icon {
  transition: transform 0.3s ease;
}

.export-btn:hover .v-icon {
  transform: translateY(-2px) scale(1.1);
}

/* Enhanced Add Button */
/* Add Subscription Button - Enhanced */
.add-subscription-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 16px !important;
  padding: 14px 28px !important;
  font-weight: 700 !important;
  text-transform: none !important;
  font-size: 1rem !important;
  letter-spacing: 0.3px !important;
  box-shadow: 
    0 6px 20px rgba(99, 102, 241, 0.3),
    0 3px 10px rgba(99, 102, 241, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
  min-height: 48px !important;
}

.add-subscription-btn:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
  transform: translateY(-3px);
  box-shadow: 
    0 8px 30px rgba(99, 102, 241, 0.4),
    0 5px 15px rgba(99, 102, 241, 0.3) !important;
}

.add-subscription-btn:active {
  transform: translateY(-1px);
  transition: all 0.1s ease;
}

/* Ripple effect for buttons */
.import-btn::before,
.export-btn::before,
.add-subscription-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: width 0.6s ease, height 0.6s ease;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.import-btn:active::before,
.export-btn:active::before,
.add-subscription-btn:active::before {
  width: 300px;
  height: 300px;
}

/* Button text and icon positioning */
.import-btn .v-btn__content,
.export-btn .v-btn__content,
.add-subscription-btn .v-btn__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700 !important;
  font-size: 1rem !important;
  white-space: nowrap;
}

.add-subscription-btn .v-icon {
  font-size: 1.2rem !important;
  transition: transform 0.3s ease;
}

.add-subscription-btn:hover .v-icon {
  transform: scale(1.1) rotate(90deg);
}

/* ============================================
   ENHANCED IMPORT DIALOG STYLING
   ============================================ */

.import-dialog {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 10px 30px rgba(0, 0, 0, 0.1) !important;
}

/* Import dialog header */
.import-dialog-header {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 50%, #388e3c 100%) !important;
  color: white !important;
  padding: 24px 32px !important;
  position: relative;
  overflow: hidden;
}

.import-dialog-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 100px;
  height: 200%;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(15deg);
  transition: all 0.3s ease;
}

.import-dialog-header:hover::before {
  right: -5%;
}

.import-dialog-header .v-card-title {
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  margin: 0 !important;
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-dialog-header .v-card-title::before {
  content: '📊';
  font-size: 1.8rem;
}

/* Import dialog content */
.import-dialog-content {
  padding: 32px !important;
  background: linear-gradient(145deg, #fafafa 0%, #f5f5f5 100%);
}

/* Enhanced info alert */
.import-info-alert {
  border-radius: 12px !important;
  border: 1px solid rgba(33, 150, 243, 0.2) !important;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%) !important;
  padding: 20px !important;
  margin-bottom: 24px !important;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.1) !important;
}

.import-info-alert .v-alert__content {
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
}

.import-info-alert strong {
  color: #1976d2 !important;
  font-weight: 700 !important;
}

.import-info-alert a {
  color: #1976d2 !important;
  text-decoration: none !important;
  font-weight: 600 !important;
  padding: 4px 8px !important;
  border-radius: 6px !important;
  background: rgba(25, 118, 210, 0.1) !important;
  transition: all 0.2s ease !important;
}

.import-info-alert a:hover {
  background: rgba(25, 118, 210, 0.2) !important;
  transform: translateY(-1px);
}

/* Enhanced error alert */
.import-error-alert {
  border-radius: 12px !important;
  background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%) !important;
  border: 1px solid rgba(244, 67, 54, 0.2) !important;
  margin-bottom: 20px !important;
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.1) !important;
}

.import-error-alert ul {
  margin: 0 !important;
  padding-left: 20px !important;
}

.import-error-alert li {
  margin-bottom: 4px !important;
  color: #c62828 !important;
  font-weight: 500 !important;
}

/* Enhanced file input */
.import-file-input {
  margin-top: 24px !important;
}

.import-file-input .v-field {
  border-radius: 16px !important;
  border: 3px dashed rgba(76, 175, 80, 0.3) !important;
  background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e8 100%) !important;
  transition: all 0.3s ease !important;
  min-height: 80px !important;
  padding: 16px !important;
}

.import-file-input .v-field:hover {
  border-color: rgba(76, 175, 80, 0.5) !important;
  background: linear-gradient(135deg, #e8f5e8 0%, #dcedc8 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.15) !important;
}

.import-file-input .v-field--focused {
  border-color: #4caf50 !important;
  background: white !important;
  box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.1) !important;
}

.import-file-input .v-field__input {
  padding-top: 20px !important;
  font-weight: 600 !important;
  color: #2e7d32 !important;
}

.import-file-input .v-field__prepend-inner {
  padding-right: 16px !important;
}

.import-file-input .v-field__prepend-inner .v-icon {
  color: #4caf50 !important;
  font-size: 1.5rem !important;
}

/* Dialog actions */
.import-dialog-actions {
  padding: 24px 32px !important;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.import-dialog-actions .v-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  padding: 12px 24px !important;
}

.import-upload-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
}

.import-upload-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
}

.import-cancel-btn {
  color: #666 !important;
  background: rgba(0, 0, 0, 0.04) !important;
}

.import-cancel-btn:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #333 !important;
}

.gap-4 {
  gap: 16px;
}

/* ============================================
   STYLING BARU UNTUK FILTER CARD
   ============================================ */

.filter-card {
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  background: linear-gradient(145deg, 
    rgba(var(--v-theme-surface), 0.95) 0%, 
    rgba(var(--v-theme-background), 0.98) 100%);
  backdrop-filter: blur(10px);
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 3px rgba(var(--v-theme-shadow), 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

/* Efek hover pada filter card */
.filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(var(--v-theme-shadow), 0.12),
    0 2px 6px rgba(var(--v-theme-shadow), 0.16);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

/* Efek glow subtle di bagian atas card */
.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(var(--v-theme-primary), 0.6) 50%, 
    transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.filter-card:hover::before {
  opacity: 1;
}

/* Container utama filter */
.filter-card .d-flex {
  padding: 28px 32px !important;
  gap: 20px !important;
}

/* Styling untuk text field pencarian */
.filter-card .v-text-field {
  min-width: 320px !important;
}

.filter-card .v-text-field :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border: 2px solid rgba(var(--v-theme-outline-variant), 0.3) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-text-field :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.filter-card .v-text-field :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

/* Icon pencarian */
.filter-card .v-text-field :deep(.v-field__prepend-inner) {
  padding-right: 12px;
}

.filter-card .v-text-field :deep(.v-field__prepend-inner .v-icon) {
  color: rgba(var(--v-theme-primary), 0.7) !important;
  transition: color 0.2s ease;
}

.filter-card .v-text-field:hover :deep(.v-field__prepend-inner .v-icon) {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Styling untuk select fields (alamat & brand) */
.filter-card .v-select {
  min-width: 220px !important;
}

.filter-card .v-select :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border: 2px solid rgba(var(--v-theme-outline-variant), 0.3) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-select :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.filter-card .v-select :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

/* Label styling yang lebih refined */
.filter-card .v-field :deep(.v-field__label) {
  color: rgba(var(--v-theme-on-surface), 0.7) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
}

.filter-card .v-field--focused :deep(.v-field__label) {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Tombol Reset Filter */
.filter-card .v-btn[variant="text"] {
  border-radius: 14px !important;
  font-weight: 600 !important;
  height: 48px !important;
  min-width: 120px !important;
  color: rgba(var(--v-theme-primary), 0.8) !important;
  background: rgba(var(--v-theme-primary), 0.08) !important;
  border: 1px solid rgba(var(--v-theme-primary), 0.2) !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.filter-card .v-btn[variant="text"]:hover {
  background: rgba(var(--v-theme-primary), 0.12) !important;
  color: rgb(var(--v-theme-primary)) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.filter-card .v-btn[variant="text"]:active {
  transform: translateY(0);
}

/* Efek ripple custom untuk tombol reset */
.filter-card .v-btn[variant="text"]::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.3);
  transition: width 0.3s ease, height 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.filter-card .v-btn[variant="text"]:hover::before {
  width: 100%;
  height: 100%;
}

/* Responsive design untuk mobile */
@media (max-width: 960px) {
  .filter-card .d-flex {
    padding: 20px 24px !important;
    gap: 16px !important;
  }
  
  .filter-card .v-text-field,
  .filter-card .v-select {
    min-width: 100% !important;
  }
  
  .filter-card .v-btn[variant="text"] {
    width: 100% !important;
    margin-top: 8px;
  }
}

@media (max-width: 600px) {
  .filter-card .d-flex {
    padding: 16px 20px !important;
    flex-direction: column !important;
    gap: 12px !important;
  }
  
  .filter-card {
    border-radius: 16px;
    margin: 0 8px;
  }
}

.selection-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.15);
}

/* Dark mode adjustments */
.v-theme--dark .filter-card {
  background: linear-gradient(145deg, 
    rgba(var(--v-theme-surface), 0.9) 0%, 
    rgba(var(--v-theme-background), 0.95) 100%);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.v-theme--dark .filter-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.v-theme--dark .filter-card .v-text-field :deep(.v-field),
.v-theme--dark .filter-card .v-select :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.6) !important;
  border-color: rgba(var(--v-theme-outline), 0.3) !important;
}

.v-theme--dark .filter-card .v-text-field :deep(.v-field:hover),
.v-theme--dark .filter-card .v-select :deep(.v-field:hover) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border-color: rgba(var(--v-theme-primary), 0.5) !important;
}

/* Loading state untuk field */
.filter-card .v-field--loading :deep(.v-field) {
  opacity: 0.7;
  pointer-events: none;
}

/* Animasi untuk smooth transitions */
.filter-card * {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Focus ring yang lebih halus */
.filter-card .v-field--focused :deep(.v-field__outline) {
  border-width: 2px !important;
  border-color: rgb(var(--v-theme-primary)) !important;
}

/* Custom scrollbar untuk dropdown */
.filter-card .v-select :deep(.v-list) {
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(var(--v-theme-shadow), 0.15);
}

.filter-card .v-select :deep(.v-list-item) {
  border-radius: 8px;
  margin: 2px 8px;
  transition: all 0.2s ease;
}

.filter-card .v-select :deep(.v-list-item:hover) {
  background: rgba(var(--v-theme-primary), 0.08) !important;
  transform: translateX(4px);
}

.v-data-table {
  --v-data-table-header-height: 60px;
}

/* Enhanced Form Styling */
.form-header-gradient {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%);
  position: relative;
  overflow: hidden;
}

.form-header-decoration {
  position: absolute;
  top: 0;
  right: -50px;
  width: 100px;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  transform: skewX(-15deg);
}

.form-icon-container {
  position: relative;
  z-index: 2;
}

.step-indicator {
  position: relative;
}

.step-line {
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #1976d2 50%, transparent 100%);
  flex: 1;
  opacity: 0.3;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section-header {
  display: flex;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(25, 118, 210, 0.1);
}

.enhanced-field {
  margin-bottom: 1rem;
}

.enhanced-field .v-field {
  background-color: rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.enhanced-field .v-field:hover {
  background-color: rgba(255, 255, 255, 0.95) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.enhanced-field .v-field--focused {
  background-color: white !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.15);
}

.price-field .v-field {
  background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%) !important;
  border: 2px solid rgba(76, 175, 80, 0.2) !important;
}

.action-footer {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.save-button {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3) !important;
  transition: all 0.3s ease !important;
}

.save-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4) !important;
}

.delete-header {
  background: linear-gradient(135deg, #fafafa 0%, #f8f8f8 100%);
}

/* Custom scrollbar for dialog */
.v-overlay__content::-webkit-scrollbar {
  width: 6px;
}

.v-overlay__content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.v-overlay__content::-webkit-scrollbar-thumb {
  background: rgba(25, 118, 210, 0.3);
  border-radius: 3px;
}

.v-overlay__content::-webkit-scrollbar-thumb:hover {
  background: rgba(25, 118, 210, 0.5);
}

/* Smooth animations */
.v-dialog > .v-overlay__content {
  animation: dialogSlideIn 0.3s ease-out;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced card styling */
.v-card.rounded-xl {
  border-radius: 16px !important;
  overflow: hidden;
}

/* Field focus effects */
.enhanced-field .v-input--focused .v-field__outline {
  border-color: #1976d2 !important;
  border-width: 2px !important;
}

/* Improved spacing and typography */
.form-section .v-card {
  transition: all 0.3s ease;
}

.form-section .v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
}

/* Enhanced button styles */
.v-btn.text-none {
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px;
}

/* Loading animation enhancement */
.v-btn--loading {
  pointer-events: none;
}

.v-btn--loading .v-btn__overlay {
  background: rgba(255, 255, 255, 0.1);
}

/* Responsive improvements */
@media (max-width: 768px) {
  .form-header-gradient {
    padding: 1.5rem !important;
  }
  
  .form-header-gradient h2 {
    font-size: 1.5rem !important;
  }
  
  .v-dialog > .v-overlay__content {
    margin: 1rem !important;
    max-width: calc(100vw - 2rem) !important;
  }
  
  .step-indicator {
    margin-bottom: 1.5rem !important;
  }
  
  .form-section {
    margin-bottom: 1.5rem !important;
  }
}
</style>