<template>
  <v-container fluid class="pa-sm-6 pa-4">
    <div class="d-flex flex-column flex-md-row align-start align-md-center mb-8 gap-4">
      <div class="d-flex align-center">
        <v-avatar 
          class="me-4 gradient-avatar" 
          size="56"
          :style="{ 
            background: 'linear-gradient(135deg, #00ACC1 0%, #006064 100%)',
            boxShadow: '0 8px 24px rgba(0, 172, 193, 0.3)'
          }"
        >
          <v-icon color="white" size="28">mdi-lan</v-icon>
        </v-avatar>
        <div>
          <h1 class="text-h4 text-md-h3 font-weight-bold mb-1 header-gradient">
            Data Teknis Pelanggan
          </h1>
          <p class="text-subtitle-1 text-medium-emphasis mb-0 opacity-80">
            Kelola informasi teknis
          </p>
        </div>
      </div>
      <v-spacer class="d-none d-md-block"></v-spacer>
      <div class="d-flex flex-column flex-sm-row gap-3 w-100 w-md-auto">
        <v-btn 
          variant="outlined" 
          color="green" 
          @click="dialogImport = true"
          prepend-icon="mdi-file-upload"
          class="text-none flex-grow-1"
        >
          Import
        </v-btn>

       <v-dialog v-model="dialogImport" max-width="600px" :fullscreen="$vuetify.display.smAndDown">
          <v-card class="rounded-xl">
            <v-card-title class="bg-green text-white">Import Data Teknis</v-card-title>
            
            <v-card-text class="pa-6">
              <v-alert
                variant="tonal" color="info" icon="mdi-information-outline" class="mb-6" border="start"
              >
                <p class="font-weight-bold mb-2">Petunjuk Import:</p>
                <p class="mb-2">Gunakan <strong>Email Pelanggan</strong> sebagai kunci untuk mencocokkan data teknis dengan pelanggan yang ada.</p>
                <v-list density="compact" class="bg-transparent">
                  <v-list-item class="pa-0">1. Unduh <a :href="`${apiClient.defaults.baseURL}/data_teknis/template/csv`" download>template import</a>.</v-list-item>
                  <v-list-item class="pa-0">2. Isi data teknis sesuai kolom, pastikan <strong>'email_pelanggan'</strong> sudah terdaftar di Data Pelanggan.</v-list-item>
                  <v-list-item class="pa-0">3. Unggah file di bawah ini.</v-list-item>
                </v-list>
              </v-alert>

              <v-alert
                v-if="importErrors.length > 0"
                type="error"
                variant="tonal"
                class="mb-6"
                border="start"
                closable
                @update:modelValue="importErrors = []"
              >
                <p class="font-weight-bold mb-2">Detail Error:</p>
                <ul class="pl-4">
                  <li v-for="(err, i) in importErrors" :key="i" class="mb-1">{{ err }}</li>
                </ul>
              </v-alert>

              <v-file-input
                :model-value="fileToImport"
                @update:model-value="handleFileSelection"
                label="Pilih file CSV"
                accept=".csv"
                variant="outlined"
                clearable
              ></v-file-input>

            </v-card-text>
            
            <v-card-actions class="pa-4 bg-grey-lighten-5">
              <v-spacer></v-spacer>
              <v-btn text @click="dialogImport = false">Batal</v-btn>
              <v-btn 
                color="green" 
                @click="importData"
                :loading="importing"
                :disabled="!fileToImport || fileToImport.length === 0">
                Unggah & Proses
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-btn 
          variant="outlined" 
          color="cyan-darken-1"
          @click="exportData"
          prepend-icon="mdi-file-excel"
          class="text-none flex-grow-1"
        >
          Export
        </v-btn>
        <v-btn 
          color="primary" 
          elevation="8"
          @click="openDialog()"
          prepend-icon="mdi-plus-network"
          class="text-none modern-btn flex-grow-1"
          :style="{
            background: 'linear-gradient(135deg, #00ACC1 0%, #006064 100%)',
            borderRadius: '16px',
            textTransform: 'none',
            fontWeight: '600',
            letterSpacing: '0.5px'
          }"
        >
        <template v-slot:prepend>
            <v-icon class="me-2 icon-bounce">mdi-plus-network</v-icon>
          </template>
          Tambah Data
        </v-btn>
      </div>
    </div>

    <v-card class="filter-card mb-6" elevation="0">
      <div class="d-flex flex-wrap align-center gap-4 pa-4">
        <v-text-field
          v-model="searchQuery"
          label="Cari (Nama, ID PPPoE, IP)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          class="flex-grow-1"
          style="min-width: 300px;"
        ></v-text-field>

        <v-select
          v-model="selectedOlt"
          :items="oltOptions"
          label="Filter Mikrotik Server"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          style="min-width: 200px;"
        ></v-select>
        
        <v-btn
            variant="text"
            @click="resetFilters"
            class="text-none"
        >
          Reset Filter
        </v-btn>
      </div>
    </v-card>

    <v-row class="mb-6" no-gutters>
      <v-col cols="12" sm="6" md="3" class="pa-2">
        <v-card 
          class="stats-card pa-4 h-100" 
          :style="{
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%)',
            border: '1px solid rgba(76, 175, 80, 0.2)',
            backdropFilter: 'blur(10px)'
          }"
          elevation="2"
        >
          <div class="d-flex align-center">
            <v-avatar color="success" size="48" class="me-3">
              <v-icon color="white">mdi-check-network</v-icon>
            </v-avatar>
            <div>
              <div class="text-h5 font-weight-bold">{{ dataTeknisList.length }}</div>
              <div class="text-caption text-medium-emphasis">Total Pelanggan</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3" class="pa-2">
        <v-card 
          class="stats-card pa-4 h-100"
          :style="{
            background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 152, 0, 0.05) 100%)',
            border: '1px solid rgba(255, 152, 0, 0.2)',
            backdropFilter: 'blur(10px)'
          }"
          elevation="2"
        >
          <div class="d-flex align-center">
            <v-avatar color="warning" size="48" class="me-3">
              <v-icon color="white">mdi-signal</v-icon>
            </v-avatar>
            <div>
              <div class="text-h5 font-weight-bold">{{ getSignalStats().good }}</div>
              <div class="text-caption text-medium-emphasis">Sinyal Baik</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3" class="pa-2">
        <v-card 
          class="stats-card pa-4 h-100"
          :style="{
            background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%)',
            border: '1px solid rgba(244, 67, 54, 0.2)',
            backdropFilter: 'blur(10px)'
          }"
          elevation="2"
        >
          <div class="d-flex align-center">
            <v-avatar color="error" size="48" class="me-3">
              <v-icon color="white">mdi-alert</v-icon>
            </v-avatar>
            <div>
              <div class="text-h5 font-weight-bold">{{ getSignalStats().poor }}</div>
              <div class="text-caption text-medium-emphasis">Sinyal Lemah</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3" class="pa-2">
        <v-card 
          class="stats-card pa-4 h-100"
          :style="{
            background: 'linear-gradient(135deg, rgba(103, 58, 183, 0.1) 0%, rgba(103, 58, 183, 0.05) 100%)',
            border: '1px solid rgba(103, 58, 183, 0.2)',
            backdropFilter: 'blur(10px)'
          }"
          elevation="2"
        >
          <div class="d-flex align-center">
            <v-avatar color="deep-purple" size="48" class="me-3">
              <v-icon color="white">mdi-router-network</v-icon>
            </v-avatar>
            <div>
              <div class="text-h5 font-weight-bold">{{ getUniqueOLTCount() }}</div>
              <div class="text-caption text-medium-emphasis">OLT Aktif</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-card 
      elevation="8" 
      class="modern-card overflow-hidden"
      :style="{
        borderRadius: '20px',
        backdropFilter: 'blur(20px)',
        background: $vuetify.theme.current.dark 
          ? 'rgba(30, 30, 30, 0.8)' 
          : 'rgba(255, 255, 255, 0.9)',
        border: $vuetify.theme.current.dark 
          ? '1px solid rgba(255, 255, 255, 0.1)' 
          : '1px solid rgba(0, 0, 0, 0.05)'
      }"
    >
      <v-expand-transition>
        <div v-if="selectedDataTeknis.length > 0" class="selection-toolbar pa-4">
          <span class="font-weight-bold text-primary">{{ selectedDataTeknis.length }} data terpilih</span>
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
      <v-card-title 
        class="pa-6 d-flex align-center"
        :style="{
          background: 'linear-gradient(135deg, rgba(0, 172, 193, 0.1) 0%, rgba(0, 96, 100, 0.05) 100%)',
          borderBottom: '1px solid rgba(0, 172, 193, 0.2)'
        }"
      >
        <v-icon class="me-3 text-primary" size="24">mdi-table</v-icon>
        <span class="text-h5 font-weight-bold">Daftar Infrastruktur</span>
      </v-card-title>
      <div class="responsive-table-container">
        <v-data-table
          v-model="selectedDataTeknis"
          v-model:expanded="expanded"
          :headers="headers"
          :items="dataTeknisList"
          :loading="loading"
          item-value="id"
          class="elevation-0 modern-table"
          :items-per-page="10"
          :loading-text="'Memuat data...'"
          show-select
          return-object
          show-expand
        >
          <template v-slot:loading>
            <div class="text-center pa-8">
              <v-progress-circular indeterminate color="primary" size="64" width="6"></v-progress-circular>
              <div class="mt-4 text-h6">Memuat data...</div>
            </div>
          </template>
          <template v-slot:item.pelanggan_id="{ item }">
            <div class="d-flex align-center py-2" style="min-width: 250px;">
              <v-avatar :color="getAvatarColor(item.pelanggan_id)" size="40" class="me-3" :style="{ boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)' }">
                <span class="text-white font-weight-bold">{{ getPelangganInitials(item.pelanggan_id) }}</span>
              </v-avatar>
              <div>
                <div class="font-weight-bold text-body-1">{{ getPelangganName(item.pelanggan_id) }}</div>
                <div class="text-caption text-medium-emphasis">ID: {{ item.id_pelanggan }}</div>
              </div>
            </div>
          </template>
          <template v-slot:item.ip_pelanggan="{ item }">
            <a 
              :href="`http://${item.ip_pelanggan}`" 
              target="_blank" 
              rel="noopener noreferrer"
              style="text-decoration: none;"
            >
              <v-chip 
                size="small" 
                variant="tonal" 
                color="primary" 
                class="font-mono" 
                :style="{ fontFamily: 'monospace' }"
              >
                <v-icon start size="16">mdi-ip-network</v-icon>
                {{ item.ip_pelanggan }}
              </v-chip>
            </a>
          </template>
          <template v-slot:item.olt="{ item }">
            <div class="d-flex align-center">
              <v-icon class="me-2 text-primary">mdi-router-network</v-icon>
              <div>
                <div class="font-weight-medium">{{ item.olt }}</div>
                <div v-if="item.olt_custom" class="text-caption text-medium-emphasis">{{ item.olt_custom }}</div>
              </div>
            </div>
          </template>
          <template v-slot:item.onu_power="{ item }">
            <div class="text-center">
              <v-chip :color="getOnuPowerColor(item.onu_power)" size="small" variant="flat" class="font-weight-bold px-3" :style="{ minWidth: '80px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)' }">
                <v-icon :icon="getOnuPowerIcon(item.onu_power)" start size="16"></v-icon>
                {{ item.onu_power }} dBm
              </v-chip>
              <div class="text-caption mt-1 text-medium-emphasis">{{ getOnuPowerStatus(item.onu_power) }}</div>
            </div>
          </template>
          <template v-slot:item.actions="{ item }">
            <div class="d-flex justify-center gap-2" style="min-width: 180px;">
              <v-btn 
                size="small" 
                variant="tonal" 
                color="primary" 
                @click="openDialog(item)"
                class="action-btn"
                :style="{ borderRadius: '8px' }"
              >
                <v-icon size="16" class="me-1">mdi-pencil</v-icon>
                Edit
              </v-btn>
              <v-btn 
                size="small" 
                variant="tonal" 
                color="error" 
                @click="openDeleteDialog(item)"
                class="action-btn"
                :style="{ borderRadius: '8px' }"
              >
                <v-icon size="16" class="me-1">mdi-delete</v-icon>
                Hapus
              </v-btn>
            </div>
          </template>
          <template v-slot:expanded-row="{ columns, item }">
            <tr>
              <td :colspan="columns.length">
                <v-card flat class="pa-4 my-2" color="rgba(0, 172, 193, 0.05)">
                  <div class="d-flex justify-space-between align-center mb-4">
                    <h4 class="text-h6 font-weight-bold text-cyan-darken-2">Detail Lengkap</h4>
                    <v-chip size="small" variant="tonal" color="cyan-darken-2">
                      ID: {{ item.id_pelanggan }}
                    </v-chip>
                  </div>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-list-item-title class="font-weight-bold mb-2">Info Jaringan</v-list-item-title>
                      <v-list density="compact">
                        <v-list-item prepend-icon="mdi-key-variant">
                          <v-list-item-title>Password: {{ item.password_pppoe }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-account-details">
                          <v-list-item-title>Profile: {{ item.profile_pppoe }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-lan">
                          <v-list-item-title>VLAN: {{ item.id_vlan }}</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-list-item-title class="font-weight-bold mb-2">Info Infrastruktur</v-list-item-title>
                      <v-list density="compact">
                        <v-list-item prepend-icon="mdi-timeline">
                          <v-list-item-title>PON: {{ item.pon }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-cable-data">
                          <v-list-item-title>OTB: {{ item.otb }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-access-point-network">
                          <v-list-item-title>ODC: {{ item.odc }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-distribution-point">
                          <v-list-item-title>ODP ID: {{ item.odp_id || 'N/A' }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item prepend-icon="mdi-barcode-scan">
                            <v-list-item-title>SN: {{ item.sn || 'N/A' }}</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-list-item-title class="font-weight-bold mb-2">Bukti Speedtest</v-list-item-title>
                      <v-img v-if="item.speedtest_proof" :src="`${apiClient.defaults.baseURL}${item.speedtest_proof}`" height="150" class="rounded-lg elevation-2" cover>
                        <template v-slot:placeholder>
                          <div class="d-flex align-center justify-center fill-height">
                            <v-progress-circular indeterminate color="grey-lighten-4"></v-progress-circular>
                          </div>
                        </template>
                      </v-img>
                      <div v-else class="text-medium-emphasis mt-2">
                        Tidak ada gambar.
                      </div>
                    </v-col>
                  </v-row>
                </v-card>
              </td>
            </tr>
          </template>
          <template v-slot:no-data>
            <div class="text-center pa-8">
              <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-database-off</v-icon>
              <div class="text-h6 text-medium-emphasis mb-2">Tidak ada data</div>
              <div class="text-body-2 text-medium-emphasis">Belum ada data teknis</div>
            </div>
          </template>
        </v-data-table>
      </div>
    </v-card>

    <v-dialog 
        v-model="dialog"
        max-width="900px"
        :fullscreen="$vuetify.display.smAndDown"
      >
      <v-card class="d-flex flex-column" style="height: 100vh;">
        
        <v-card-title class="pa-0 flex-shrink-0" :style="{ background: 'linear-gradient(135deg, #00ACC1 0%, #006064 100%)', color: 'white' }">
          <div class="pa-4 pa-sm-6 d-flex align-center">
            <v-icon class="me-3" size="28">mdi-plus-network-outline</v-icon>
            <div>
              <div class="text-h5 text-sm-h4 font-weight-bold">{{ formTitle }}</div>
              <div class="text-body-2 opacity-90 mt-1">Lengkapi informasi teknis</div>
            </div>
          </div>
        </v-card-title>

        <v-card-text class="flex-grow-1 pa-0" style="overflow-y: auto;">
          <v-stepper v-model="currentStep" class="elevation-0" style="height: 100%; background: transparent;">
            <v-stepper-header class="px-sm-6 px-2 pt-6">
              <v-stepper-item title="Jaringan" :value="1" editable :complete="currentStep > 1"></v-stepper-item>
              <v-divider></v-divider>
              <v-stepper-item title="Infrastruktur" :value="2" editable :complete="currentStep > 2"></v-stepper-item>
              <v-divider></v-divider>
              <v-stepper-item title="ONU" :value="3" editable></v-stepper-item>
            </v-stepper-header>

            <v-stepper-window>
              <v-stepper-window-item :value="1">
                <div class="pa-4 pa-sm-6">
              <h3 class="text-h6 font-weight-bold mb-4">Informasi Jaringan</h3>
                  <v-select
                    v-model="editedItem.pelanggan_id"
                    :items="pelangganForSelect"
                    item-title="nama"
                    item-value="id"
                    label="Pilih Pelanggan"
                    :disabled="isEditMode"
                    variant="outlined"
                    class="mb-4"
                  ></v-select>
                  <v-row>
                <v-col cols="12" sm="6">
                  <v-select
                      v-model="editedItem.mikrotik_server_id"
                      :items="mikrotikServers"
                      item-title="name"
                      item-value="id"
                      label="Mikrotik Server"
                      @update:modelValue="handleOltSelection"
                      variant="outlined"
                  ></v-select>
                </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field v-model="editedItem.id_pelanggan" label="ID Pelanggan (PPPoE)" variant="outlined"></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field v-model="editedItem.password_pppoe" label="Password PPPoE" type="password" variant="outlined"></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field
                        v-model="editedItem.ip_pelanggan"
                        label="IP Pelanggan"
                        variant="outlined"
                        @update:modelValue="checkIpAvailability"
                        :loading="ipValidation.loading"
                        :error-messages="ipValidation.color === 'error' ? ipValidation.message : ''"
                        :success-messages="ipValidation.color === 'success' ? ipValidation.message : ''"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-select
                        v-model="editedItem.profile_pppoe"
                        :items="availablePppoeProfiles"
                        :loading="profilesLoading"
                        label="Profile PPPoE"
                        variant="outlined"
                        placeholder="Pilih profile yang tersedia..."
                        no-data-text="Tidak ada profile tersedia untuk paket ini"
                      ></v-select>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field v-model="editedItem.id_vlan" label="ID VLAN" variant="outlined"></v-text-field>
                    </v-col>
                  </v-row>
                </div>
              </v-stepper-window-item>

              <v-stepper-window-item :value="2">
                <div class="pa-4 pa-sm-6">
              <h3 class="text-h6 font-weight-bold mb-4">Detail Infrastruktur</h3>
                  <v-row>
                    <v-col cols="12" sm="6">
                       <v-select
                        v-model="editedItem.odp_id" :items="odpList"
                        item-title="kode_odp"
                        item-value="id"
                        label="Terhubung ke ODP"
                        variant="outlined"
                        clearable
                        :loading="loadingOdps"
                      >
                        <template v-slot:item="{ props, item }">
                          <v-list-item v-bind="props" :subtitle="item.raw.alamat"></v-list-item>
                        </template>
                      </v-select>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field v-model="editedItem.olt_custom" label="OLT Custom (Opsional)" variant="outlined"></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="3">
                      <v-text-field 
                        v-model.number="editedItem.pon" 
                        label="PON" 
                        type="number" 
                        variant="outlined" 
                        :readonly="isNocUser"
                      ></v-text-field>
                    </v-col>

                    <v-col cols="12" sm="3">
                      <v-text-field 
                        v-model.number="editedItem.otb" 
                        label="OTB" 
                        type="number" 
                        variant="outlined" 
                        :readonly="isNocUser"
                      ></v-text-field>
                    </v-col>

                    <v-col cols="12" sm="3">
                      <v-text-field 
                        v-model.number="editedItem.odc" 
                        label="ODC" 
                        type="number" 
                        variant="outlined" 
                        :readonly="isNocUser"
                      ></v-text-field>
                    </v-col>

                    <v-col cols="12" sm="3">
                      <v-text-field 
                        v-model.number="editedItem.odp" 
                        label="Port ODP" 
                        type="number" 
                        variant="outlined" 
                        :readonly="isNocUser"
                      ></v-text-field>
                    </v-col>
                    </v-row>
                </div>
              </v-stepper-window-item>

              <v-stepper-window-item :value="3">
                <div class="pa-4 pa-sm-6">
                  <h3 class="text-h6 font-weight-bold mb-4">Detail ONU</h3>
                  <v-row>
                    <v-col cols="12" sm="6">
                      <v-text-field v-model.number="editedItem.onu_power" label="ONU Power" type="number" suffix="dBm" variant="outlined"></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field 
                        v-model="editedItem.sn" 
                        label="Serial Number (SN) ONU" 
                        variant="outlined"
                        prepend-inner-icon="mdi-barcode-scan"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12">
                      <v-file-input ref="fileInputComponent" label="Unggah Bukti Speedtest" variant="outlined" accept="image/*" clearable></v-file-input>
                    </v-col>
                    <v-col cols="12">
                      <v-img v-if="imagePreviewUrl" :src="imagePreviewUrl" height="200" class="rounded-lg elevation-2" cover></v-img>
                      <div v-else class="text-center text-medium-emphasis pa-8 border rounded-lg">
                        Tidak ada bukti speedtest.
                      </div>
                    </v-col>
                  </v-row>
                </div>
              </v-stepper-window-item>
            </v-stepper-window>
          </v-stepper>
        </v-card-text>

        <v-card-actions class="pa-4 pa-sm-6 pt-0 flex-shrink-0" :style="{ background: 'rgba(0, 0, 0, 0.02)' }">
          <v-btn v-if="currentStep > 1" color="grey" variant="outlined" @click="currentStep--">
            Kembali
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="outlined" @click="closeDialog">
            Batal
          </v-btn>
          <v-btn v-if="currentStep < 3" color="primary" variant="flat" @click="currentStep++">
            Lanjut
          </v-btn>
          <v-btn v-else color="primary" variant="flat" @click="saveDataTeknis" :loading="saving">
            Simpan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card class="modern-dialog" :style="{ borderRadius: '20px' }" elevation="16">
        <v-card-title class="pa-6 d-flex align-center" :style="{ background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%)', borderBottom: '1px solid rgba(244, 67, 54, 0.2)' }">
          <v-avatar color="error" size="48" class="me-4">
            <v-icon color="white">mdi-alert</v-icon>
          </v-avatar>
          <div>
            <div class="text-h5 font-weight-bold">Konfirmasi Hapus</div>
            <div class="text-body-2 opacity-80">Tindakan ini permanen</div>
          </div>
        </v-card-title>
        <v-card-text class="pa-6">
          <div class="text-center">
            <v-icon size="64" color="error" class="mb-4 opacity-60">
              mdi-delete-alert
            </v-icon>
            <p class="text-body-1 mb-2">
              Yakin ingin menghapus data teknis ini?
            </p>
          </div>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="closeDeleteDialog" class="me-3" :style="{ borderRadius: '12px' }">
            Batal
          </v-btn>
          <v-btn color="error" variant="flat" @click="confirmDelete" prepend-icon="mdi-delete" :style="{ borderRadius: '12px' }" :loading="deleting">
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogBulkDelete" max-width="500px">
      <v-card class="modern-dialog" :style="{ borderRadius: '20px' }" elevation="16">
        <v-card-title class="pa-6 d-flex align-center" :style="{ background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%)', borderBottom: '1px solid rgba(244, 67, 54, 0.2)' }">
          <v-avatar color="error" size="48" class="me-4">
            <v-icon color="white">mdi-delete-sweep</v-icon>
          </v-avatar>
          <div>
            <div class="text-h5 font-weight-bold">Hapus Massal</div>
          </div>
        </v-card-title>
        <v-card-text class="pa-6 text-center">
          <p class="text-body-1">
            Yakin ingin menghapus <strong>{{ selectedDataTeknis.length }} data teknis</strong> terpilih?
          </p>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="dialogBulkDelete = false" class="me-3" :style="{ borderRadius: '12px' }">
            Batal
          </v-btn>
          <v-btn 
            color="error" 
            variant="flat" 
            @click="confirmBulkDelete" 
            prepend-icon="mdi-delete" 
            :style="{ borderRadius: '12px' }" 
            :loading="deleting"
          >
            Ya, Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
// --- SCRIPT ANDA TETAP SAMA, TIDAK ADA PERUBAHAN ---
import { ref, onMounted, computed, watch } from 'vue';
import apiClient from '@/services/api';
import { debounce } from 'lodash-es';
import { useAuthStore } from '@/stores/auth';

// --- Interfaces ---
interface DataTeknis {
  id: number;
  pelanggan_id: number;
  id_vlan: string;
  id_pelanggan: string;
  password_pppoe: string;
  ip_pelanggan: string;
  profile_pppoe: string;
  olt: string;
  olt_custom?: string | null;
  pon: number;
  otb: number;
  odc: number;
  odp_id?: number | null; // ID ODP (dari dropdown)
  odp: number;
  speedtest_proof?: string | null;
  onu_power: number;
  mikrotik_server_id: number;
  sn?: string | null;
}
interface Pelanggan {
  id: number;
  nama: string;
}

interface MikrotikServer {
  id: number;
  name: string;
}

interface PaketLayananSelectItem {
  id: number;
  nama_paket: string;
}

// --- State ---
const dataTeknisList = ref<DataTeknis[]>([]);
const pelangganList = ref<Pelanggan[]>([]);
const pelangganMap = ref(new Map<number, Pelanggan>());
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const dialog = ref(false);
const dialogDelete = ref(false);
const currentStep = ref(1);
const editedItem = ref<Partial<DataTeknis>>({});
const itemToDeleteId = ref<number | null>(null);
const searchQuery = ref('');
const mikrotikServers = ref<MikrotikServer[]>([]);

const profilesLoading = ref(false);
const paketLayananSelectList = ref<PaketLayananSelectItem[]>([]);
const odpList = ref<any[]>([]);
const loadingOdps = ref(false);
const profilesFromApi = ref<{ profile_name: string; usage_count: number }[]>([]);

const selectedDataTeknis = ref<DataTeknis[]>([]);
const dialogBulkDelete = ref(false);

const fileToImport = ref<File[]>([]);
const dialogImport = ref(false);
const importing = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });
const importErrors = ref<string[]>([]);
const selectedOlt = ref<string | null>(null);

const authStore = useAuthStore();

// Ref untuk komponen file input
const fileInputComponent = ref<any>(null);
const expanded = ref<readonly any[]>([]);

// --- Computed Properties ---
const isEditMode = computed(() => !!editedItem.value.id);
const formTitle = computed(() => isEditMode.value ? 'Edit Data Teknis' : 'Tambah Data Teknis');

const availablePppoeProfiles = computed(() => {
  // 1. Filter profile yang masih tersedia (kurang dari 5)
  const available = profilesFromApi.value
    .filter(p => p.usage_count < 5)
    .map(p => p.profile_name);

  // 2. Ambil profile yang sedang digunakan oleh user yang diedit
  const currentProfile = editedItem.value.profile_pppoe;

  // 3. Jika profile saat ini ada DAN belum termasuk di daftar, tambahkan.
  if (currentProfile && !available.includes(currentProfile)) {
    available.unshift(currentProfile); // Taruh di paling atas
  }

  return available;
});


const imagePreviewUrl = computed(() => {
  if (fileInputComponent.value?.files && fileInputComponent.value.files.length > 0) {
    return URL.createObjectURL(fileInputComponent.value.files[0]);
  }
  if (editedItem.value.speedtest_proof) {
    const baseUrl = apiClient.defaults.baseURL || ''; 
    return `${baseUrl}${editedItem.value.speedtest_proof}`;
  }
  return null;
});

const ipValidation = ref({
  loading: false,
  message: '',
  color: ''
});

const pelangganForSelect = computed(() => {
  if (isEditMode.value) {
    return pelangganList.value;
  }
  const existingIds = new Set(dataTeknisList.value.map(dt => dt.pelanggan_id));
  return pelangganList.value.filter(p => !existingIds.has(p.id));
});

const oltOptions = computed(() => {
  const olts = dataTeknisList.value.map(item => item.olt);
  return [...new Set(olts)]; // Mengambil daftar OLT yang unik
});

// --- Table Headers ---
const headers = [
  { title: 'Nama Pelanggan', key: 'pelanggan_id' },
  { title: 'IP Pelanggan', key: 'ip_pelanggan' },
  { title: 'OLT', key: 'olt' },
  { title: 'ONU Power', key: 'onu_power', align: 'center' as const },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' as const },
];

// const pppoeProfiles = (() => {
//   const speeds = ['10Mbps', '20Mbps', '30Mbps', '50Mbps'];
//   const alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');
//   const profiles: string[] = [];

//   for (const speed of speeds) {
//     for (const letter of alphabet) {
//       profiles.push(`${speed}-${letter}`);
//     }
//   }
//   return profiles;
// })();


const isNocUser = computed(() => {
  if (authStore.user && authStore.user.role) {
    const role = authStore.user.role;
    // Cek dulu apakah 'role' adalah objek dan memiliki properti 'name'
    if (typeof role === 'object' && role !== null && 'name' in role) {
      // Jika ya, baru akses .name
      return role.name.toLowerCase() === 'noc';
    }
    // Jika 'role' adalah string, lakukan perbandingan langsung
    if (typeof role === 'string') {
      return role.toLowerCase() === 'noc';
    }
  }
  return false;
});


function handleOltSelection(serverId: number) {
  const selectedServer = mikrotikServers.value.find(s => s.id === serverId);
  if (selectedServer) {
    editedItem.value.olt = selectedServer.name;
  }
}


// --- Methods ---
onMounted(() => {
  fetchDataTeknis();
  fetchPelanggan();
  fetchMikrotikServers();
  fetchPaketLayananForSelect();
  fetchOdpList();
});

async function fetchDataTeknis() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    if (selectedOlt.value) {
      params.append('olt', selectedOlt.value);
    }
    
    const response = await apiClient.get(`/data_teknis/?${params.toString()}`);
    dataTeknisList.value = response.data;
  } finally {
    loading.value = false;
  }
}


async function fetchOdpList() {
  loadingOdps.value = true;
  try {
    const response = await apiClient.get('/odp/');
    odpList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil daftar ODP:", error);
  } finally {
    loadingOdps.value = false;
  }
}



const applyFilters = debounce(() => {
  fetchDataTeknis();
}, 500);

watch([searchQuery, selectedOlt], () => {
  applyFilters();
});

function resetFilters() {
  searchQuery.value = '';
  selectedOlt.value = null;
}

async function fetchMikrotikServers() {
  try {
    const response = await apiClient.get('/mikrotik_servers/');
    mikrotikServers.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil daftar server Mikrotik:", error);
  }
}

async function fetchPelanggan() {
  try {
    const response = await apiClient.get('/pelanggan/');
    pelangganList.value = response.data;
    const newMap = new Map<number, Pelanggan>();
    for (const pelanggan of response.data) {
      newMap.set(pelanggan.id, pelanggan);
    }
    pelangganMap.value = newMap;

  } catch(error) {
    console.error("Gagal mengambil daftar pelanggan:", error);
  }
}

// function openDialog(item?: DataTeknis) {
//   editedItem.value = item ? { ...item } : {};
//   currentStep.value = 1;
//   dialog.value = true;
// }


function openDialog(item?: DataTeknis) {
  ipValidation.value = { loading: false, message: '', color: '' };
  if (item) {
    // Mode Edit: Gunakan data yang ada
    editedItem.value = { ...item };
  } else {
    // Mode Tambah Baru: Set nilai default di sini
    editedItem.value = {
      pon: 0,
      otb: 0,
      odc: 0,
      odp: 0,
      onu_power: 0, // Ini juga akan mengisi default 0 pada ONU Power
    };
    profilesFromApi.value = []; 
  }
  currentStep.value = 1;
  dialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  if (fileInputComponent.value) {
    fileInputComponent.value.reset();
  }
  editedItem.value = {};
  currentStep.value = 1;
}

const checkIpAvailability = debounce(async (ip: string) => {
  // Jangan cek jika IP kosong
  if (!ip) {
    ipValidation.value = { loading: false, message: '', color: '' };
    return;
  }
  
  ipValidation.value.loading = true;
  try {
    const response = await apiClient.post('/data_teknis/check-ip', {
      ip_address: ip,
      current_id: editedItem.value.id || null // Kirim ID saat mode edit
    });
    
    const { is_taken, message } = response.data;
    
    ipValidation.value.message = message;
    ipValidation.value.color = is_taken ? 'error' : 'success';

  } catch (error) {
    console.error("Gagal memeriksa IP:", error);
    ipValidation.value.message = "Gagal memeriksa ketersediaan IP.";
    ipValidation.value.color = 'error';
  } finally {
    ipValidation.value.loading = false;
  }
}, 700);

async function saveDataTeknis() {
  saving.value = true;
  try {
    const files = fileInputComponent.value?.files;
    const fileToUpload = files?.[0];

    if (fileToUpload) {
      const formData = new FormData();
      formData.append('file', fileToUpload);
      
      const uploadResponse = await apiClient.post('/uploads/speedtest/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (uploadResponse?.data?.file_url) {
        editedItem.value.speedtest_proof = uploadResponse.data.file_url;
      }
    }

    let updatedData: DataTeknis; // Deklarasikan variabel di sini

    if (isEditMode.value) {
      // Tangkap respons dari server setelah PATCH
      const response = await apiClient.patch(`/data_teknis/${editedItem.value.id}`, editedItem.value);
      updatedData = response.data;
      
      // Cari index dari data lama di dalam array
      const index = dataTeknisList.value.findIndex(item => item.id === updatedData.id);
      if (index !== -1) {
        // Ganti data lama dengan data baru yang diterima dari server
        dataTeknisList.value[index] = updatedData;
      }

    } else {
      // Untuk "Tambah Data", panggil ulang fetchDataTeknis
      await apiClient.post('/data_teknis/', editedItem.value);
      fetchDataTeknis(); 
    }
    
    closeDialog();
  } catch (error) {
    console.error("Gagal saat menyimpan data teknis:", error);
  } finally {
    saving.value = false;
  }
}

function openDeleteDialog(item: DataTeknis) {
  itemToDeleteId.value = item.id;
  dialogDelete.value = true;
}

function closeDeleteDialog() {
  dialogDelete.value = false;
  itemToDeleteId.value = null;
}


async function confirmBulkDelete() {
  const itemsToDelete = [...selectedDataTeknis.value];
  if (itemsToDelete.length === 0) return;

  deleting.value = true;
  try {
    const deletePromises = itemsToDelete.map(item =>
      apiClient.delete(`/data_teknis/${item.id}`)
    );
    await Promise.all(deletePromises);
    showSnackbar(`${itemsToDelete.length} data teknis berhasil dihapus.`, 'success');
    fetchDataTeknis();
    selectedDataTeknis.value = [];
  } catch (error) {
    console.error("Gagal melakukan hapus massal data teknis:", error);
    showSnackbar('Terjadi kesalahan saat menghapus data.', 'error');
  } finally {
    deleting.value = false;
    dialogBulkDelete.value = false;
  }
}

async function confirmDelete() {
  if (itemToDeleteId.value === null) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/data_teknis/${itemToDeleteId.value}`);
    fetchDataTeknis();
    closeDeleteDialog();
  } catch (error) {
    console.error("Gagal menghapus data teknis:", error);
  } finally {
    deleting.value = false;
  }
}

function getPelangganName(pelangganId: number) {
  return pelangganMap.value.get(pelangganId)?.nama || 'Tidak Ditemukan';
}

function getPelangganInitials(pelangganId: number) {
  const name = getPelangganName(pelangganId);
  if (name === 'Tidak Ditemukan') return '?';
  return name.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase();
}

function getAvatarColor(pelangganId: number) {
  const colors = ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'error'];
  return colors[pelangganId % colors.length];
}

function getOnuPowerColor(power: number) {
  if (!power) return 'grey';
  if (power <= -27) return 'error';
  if (power <= -24) return 'warning';
  return 'success';
}

function getOnuPowerIcon(power: number) {
  if (!power) return 'mdi-help-circle';
  if (power <= -27) return 'mdi-signal-off';
  if (power <= -24) return 'mdi-signal-2g';
  return 'mdi-signal-4g';
}

function getOnuPowerStatus(power: number) {
  if (!power) return 'N/A';
  if (power <= -27) return 'Sinyal Lemah';
  if (power <= -24) return 'Sinyal Sedang';
  return 'Sinyal Baik';
}

function getSignalStats() {
  const good = dataTeknisList.value.filter(item => item.onu_power > -24).length;
  const poor = dataTeknisList.value.filter(item => item.onu_power <= -27).length;
  return { good, poor };
}

function getUniqueOLTCount() {
  const uniqueOLTs = new Set(dataTeknisList.value.map(item => item.olt));
  return uniqueOLTs.size;
}

async function exportData() {
  try {
    const response = await apiClient.get('/data_teknis/export/csv', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'data_teknis.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Gagal mengunduh file:", error);
  }
}
async function importData() {
  const file = fileToImport.value[0];
  if (!file) {
    showSnackbar("Silakan pilih file CSV terlebih dahulu.", "error");
    return;
  }

  importing.value = true;
  importErrors.value = [];
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post('/data_teknis/import/csv', formData);
    showSnackbar(response.data.message || 'Impor berhasil!', 'success');
    fetchDataTeknis();
    dialogImport.value = false;
    fileToImport.value = [];
    
  } catch (error: any) {
    console.error("Gagal mengimpor data:", error);
    const detail = error.response?.data?.detail;
    let snackbarMessage = "Gagal mengimpor data.";
    let errorList: string[] = ["Terjadi kesalahan yang tidak diketahui."];

    if (typeof detail === 'object' && detail !== null && Array.isArray(detail.errors)) {
      snackbarMessage = detail.message || snackbarMessage;
      errorList = detail.errors;
    } else if (typeof detail === 'string') {
      snackbarMessage = detail;
      errorList = [detail];
    }
    
    importErrors.value = errorList;
    showSnackbar(snackbarMessage, "error");
  } finally {
    importing.value = false;
  }
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

function showSnackbar(text: string, color: string) {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

/**
 * Watcher cerdas yang memantau perubahan pada pelanggan DAN OLT/Server yang dipilih.
 * Ini akan memicu pengambilan profil PPPoE hanya jika kedua informasi tersebut sudah ada.
 */
watch(
  () => [editedItem.value.pelanggan_id, editedItem.value.mikrotik_server_id],
  async ([newPelangganId, newServerId]) => {
    // Jika salah satu kosong, reset dan hentikan proses
    if (!newPelangganId || !newServerId) {
      profilesFromApi.value = [];
      if (editedItem.value) editedItem.value.profile_pppoe = undefined;
      return;
    }

    await handleProfileFetch(newPelangganId, newServerId);
  },
  { deep: true }
);

async function handleProfileFetch(pelangganId: number, serverId: number) {
  // Reset state yang relevan
  profilesLoading.value = true;
  profilesFromApi.value = [];
  if (editedItem.value) editedItem.value.profile_pppoe = undefined;

  try {
    // 1. Ambil detail pelanggan untuk mengetahui paket layanan apa yang dia gunakan
    const pelangganResponse = await apiClient.get(`/pelanggan/${pelangganId}`);
    const pelangganDetail = pelangganResponse.data;

    if (pelangganDetail && pelangganDetail.layanan) {
      // 2. Cari ID paket yang namanya cocok dengan 'layanan' pelanggan
      const paketTerkait = paketLayananSelectList.value.find(
        (p: PaketLayananSelectItem) => p.nama_paket === pelangganDetail.layanan
      );

      if (paketTerkait) {
        // 3. Jika paket ditemukan, panggil API dengan SEMUA info yang dibutuhkan
        await fetchAvailableProfiles(paketTerkait.id, pelangganId, serverId);
      }
    }
  } catch (error) {
    console.error("Gagal mengambil data detail pelanggan:", error);
  } finally {
    profilesLoading.value = false;
  }
}

async function fetchPaketLayananForSelect() {
  try {
    // Asumsi endpoint ini mengembalikan semua paket layanan
    const response = await apiClient.get<PaketLayananSelectItem[]>('/paket_layanan/');
    paketLayananSelectList.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data paket layanan:", error);
  }
}


async function fetchAvailableProfiles(paketLayananId: number, pelangganId: number, serverId: number) {
  if (!paketLayananId || !pelangganId || !serverId) {
    profilesFromApi.value = [];
    return;
  }
  profilesLoading.value = true;
  try {
    // --- PERBAIKAN UTAMA DI SINI ---
    // Kirim mikrotik_server_id sebagai query parameter
    const response = await apiClient.get(
      `/data_teknis/available-profiles/${paketLayananId}/${pelangganId}?mikrotik_server_id=${serverId}`
    );
    profilesFromApi.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil profile PPPoE yang tersedia:", error);
    profilesFromApi.value = [];
  } finally {
    profilesLoading.value = false;
  }
}

</script>

<style scoped>
.gap-3 {
  gap: 12px;
}
.gap-4 {
  gap: 16px;
}

.responsive-table-container {
  overflow-x: auto;
  width: 100%;
}

/* DIHAPUS: Semua CSS custom untuk dialog responsive dihilangkan
   karena sudah ditangani oleh prop :fullscreen dan struktur flexbox.
   Ini adalah cara yang paling bersih dan stabil.
*/

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

.filter-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(var(--v-theme-shadow), 0.12),
    0 2px 6px rgba(var(--v-theme-shadow), 0.16);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

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

.filter-card .d-flex {
  padding: 28px 32px !important;
  gap: 20px !important;
}

.filter-card .v-text-field, .filter-card .v-select {
  min-width: 250px !important;
}

.filter-card :deep(.v-field) {
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border: 2px solid rgba(var(--v-theme-outline-variant), 0.3) !important;
  border-radius: 16px !important;
  box-shadow: inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card :deep(.v-field:hover) {
  border-color: rgba(var(--v-theme-primary), 0.4) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.filter-card :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-surface), 1) !important;
  box-shadow: 
    inset 0 2px 4px rgba(var(--v-theme-shadow), 0.06),
    0 0 0 3px rgba(var(--v-theme-primary), 0.12);
}

.filter-card .v-text-field :deep(.v-field__prepend-inner .v-icon) {
  color: rgba(var(--v-theme-primary), 0.7) !important;
  transition: color 0.2s ease;
}

.filter-card .v-text-field:hover :deep(.v-field__prepend-inner .v-icon) {
  color: rgb(var(--v-theme-primary)) !important;
}

.filter-card .v-btn[variant="text"] {
  border-radius: 14px !important;
  font-weight: 600 !important;
  height: 48px !important;
  min-width: 120px !important;
  color: rgba(var(--v-theme-primary), 0.8) !important;
  background: rgba(var(--v-theme-primary), 0.08) !important;
  border: 1px solid rgba(var(--v-theme-primary), 0.2) !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.filter-card .v-btn[variant="text"]:hover {
  background: rgba(var(--v-theme-primary), 0.12) !important;
  color: rgb(var(--v-theme-primary)) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

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
    margin: 0;
  }
}

.header-gradient {
  background: linear-gradient(135deg, #00ACC1 0%, #006064 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.gradient-avatar {
  position: relative;
  overflow: hidden;
}

.gradient-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  z-index: 1;
}

.selection-toolbar {
  display: flex;
  align-items: center;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.15);
}

.modern-btn {
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(0);
}

.modern-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 172, 193, 0.4) !important;
}

.modern-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.modern-btn:hover::before {
  left: 100%;
}

.icon-bounce {
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-4px);
  }
  60% {
    transform: translateY(-2px);
  }
}

.stats-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 16px !important;
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1) !important;
}

.stats-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #00ACC1, #006064);
}

.modern-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-card:hover {
  transform: translateY(-2px);
}

.modern-table {
  background: transparent !important;
}

.modern-table :deep(.v-data-table-header) {
  background: rgba(0, 172, 193, 0.05) !important;
}

.modern-table :deep(.v-data-table__tr:hover) {
  background: rgba(0, 172, 193, 0.05) !important;
}

.action-btn {
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.modern-dialog {
  position: relative;
  overflow: hidden;
  border-radius: 24px !important;
}

.modern-dialog::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #00ACC1, #006064);
  z-index: 1;
}

:deep(.v-text-field .v-field--focused),
:deep(.v-select .v-field--focused) {
  box-shadow: 0 0 0 2px rgba(0, 172, 193, 0.2);
  border-color: #00ACC1 !important;
}

.v-theme--dark .stats-card,
.v-theme--dark .modern-card {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.v-theme--dark .modern-dialog {
  background: rgba(30, 30, 30, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

@media (max-width: 768px) {
  .stats-card {
    margin-bottom: 8px;
  }
  
  .modern-btn {
    width: 100%;
    margin-top: 0;
  }
  
  .action-btn {
    min-width: 80px;
  }
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 172, 193, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 172, 193, 0.5);
}

.v-progress-circular {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 172, 193, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(0, 172, 193, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 172, 193, 0);
  }
}

.v-chip {
  transition: all 0.2s ease;
}

.v-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>