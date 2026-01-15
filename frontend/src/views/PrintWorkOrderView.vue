<template>
  <div class="print-container">
    <!-- Non-printable Toolbar -->
    <div class="no-print toolbar d-flex flex-column flex-md-row align-center mb-4 pa-3 pa-md-4 bg-grey-lighten-4">
      <!-- Back Button -->
      <div class="d-flex align-center mb-2 mb-md-0">
        <v-btn prepend-icon="mdi-arrow-left" variant="text" @click="handleBack">Kembali</v-btn>
      </div>

      <!-- Spacer for Desktop -->
      <div class="d-none d-md-block mx-4"></div>

      <!-- Controls Group -->
      <div class="d-flex flex-column flex-md-row align-center gap-3 flex-grow-1 mb-2 mb-md-0">
        <!-- Input Tanggal Instalasi -->
        <div class="d-flex align-center">
          <span class="text-caption mr-3 text-grey-darken-1">Tanggal:</span>
          <v-text-field
            v-model="tanggalInstalasi"
            type="date"
            density="compact"
            variant="outlined"
            hide-details
            bg-color="white"
            style="min-width: 200px; max-width: 220px;"
          ></v-text-field>
        </div>

        <!-- WO Selector -->
        <div class="d-flex align-center" v-if="workOrderList.length > 1">
          <span class="text-caption mr-3 text-grey-darken-1 d-none d-md-inline">WO:</span>
          <v-select
            v-model="selectedWoNo"
            :items="workOrderList"
            item-title="no_wo"
            item-value="no_wo"
            density="compact"
            variant="outlined"
            hide-details
            bg-color="white"
            style="min-width: 180px; max-width: 220px;"
            placeholder="Pilih WO"
          ></v-select>
        </div>
      </div>

      <!-- Spacer to push button to right on desktop -->
      <v-spacer class="d-none d-md-block"></v-spacer>

      <!-- Print Button -->
      <v-btn
        color="primary"
        :loading="saving"
        prepend-icon="mdi-printer"
        @click="saveAndPrint"
        class="text-none"
        size="default"
      >
        {{ isBulkMode ? 'Cetak Semua' : 'Simpan & Cetak' }}
      </v-btn>
    </div>

    <div class="content-wrapper">
      <!-- SIDEBAR (Upload Section) -->
      <div v-if="!isBulkMode" class="sidebar no-print">
        <div class="upload-section bg-white elevation-1 pa-4 rounded">
          <div class="text-h6 mb-4 d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-camera-plus</v-icon>
            <span class="font-weight-medium">Upload Dokumentasi</span>
          </div>

          <v-row>
            <!-- Photo ODP Before -->
            <v-col cols="12">
              <div class="upload-action-box" :class="{ 'has-file': documents.photo_odp_before }">
                <div class="box-header">ODP (Sebelum)</div>
                <div v-if="documents.photo_odp_before" class="preview-container">
                  <img :src="getDocumentUrl(documents.photo_odp_before)" alt="ODP Before" />
                  <div class="overlay">
                    <v-btn color="error" variant="flat" size="small" prepend-icon="mdi-delete" @click="deleteDocument('photo_odp_before')">Hapus</v-btn>
                  </div>
                </div>
                <div v-else class="upload-trigger" @click="triggerFileInput('fileOdpBefore')">
                  <div class="d-flex flex-column align-center">
                    <v-icon size="30" color="primary" class="mb-2">mdi-cloud-upload</v-icon>
                    <div class="text-caption font-weight-medium text-grey-darken-2">Upload Foto</div>
                  </div>
                </div>
                <input ref="fileOdpBefore" type="file" accept="image/*" style="display: none" @change="handleFileUpload($event, 'photo_odp_before')" />
              </div>
            </v-col>

            <!-- Photo ODP After -->
            <v-col cols="12">
              <div class="upload-action-box" :class="{ 'has-file': documents.photo_odp_after }">
                <div class="box-header">ODP (Sesudah)</div>
                  <div v-if="documents.photo_odp_after" class="preview-container">
                  <img :src="getDocumentUrl(documents.photo_odp_after)" alt="ODP After" />
                  <div class="overlay">
                    <v-btn color="error" variant="flat" size="small" prepend-icon="mdi-delete" @click="deleteDocument('photo_odp_after')">Hapus</v-btn>
                  </div>
                </div>
                <div v-else class="upload-trigger" @click="triggerFileInput('fileOdpAfter')">
                  <div class="d-flex flex-column align-center">
                    <v-icon size="30" color="primary" class="mb-2">mdi-cloud-upload</v-icon>
                    <div class="text-caption font-weight-medium text-grey-darken-2">Upload Foto</div>
                  </div>
                </div>
                <input ref="fileOdpAfter" type="file" accept="image/*" style="display: none" @change="handleFileUpload($event, 'photo_odp_after')" />
              </div>
            </v-col>

            <!-- Photo ONU -->
            <v-col cols="12">
              <div class="upload-action-box" :class="{ 'has-file': documents.photo_onu }">
                <div class="box-header">ONU/ONT Aktif</div>
                <div v-if="documents.photo_onu" class="preview-container">
                  <img :src="getDocumentUrl(documents.photo_onu)" alt="ONU" />
                  <div class="overlay">
                    <v-btn color="error" variant="flat" size="small" prepend-icon="mdi-delete" @click="deleteDocument('photo_onu')">Hapus</v-btn>
                  </div>
                </div>
                <div v-else class="upload-trigger" @click="triggerFileInput('fileOnu')">
                  <div class="d-flex flex-column align-center">
                     <v-icon size="30" color="primary" class="mb-2">mdi-cloud-upload</v-icon>
                     <div class="text-caption font-weight-medium text-grey-darken-2">Upload Foto</div>
                  </div>
                </div>
                <input ref="fileOnu" type="file" accept="image/*" style="display: none" @change="handleFileUpload($event, 'photo_onu')" />
              </div>
            </v-col>

            <!-- Photo Speedtest -->
            <v-col cols="12">
               <div class="upload-action-box" :class="{ 'has-file': documents.photo_speedtest }">
                <div class="box-header">Speed Test</div>
                <div v-if="documents.photo_speedtest" class="preview-container">
                  <img :src="getDocumentUrl(documents.photo_speedtest)" alt="Speedtest" />
                  <div class="overlay">
                    <v-btn color="error" variant="flat" size="small" prepend-icon="mdi-delete" @click="deleteDocument('photo_speedtest')">Hapus</v-btn>
                  </div>
                </div>
                <div v-else class="upload-trigger" @click="triggerFileInput('fileSpeedtest')">
                  <div class="d-flex flex-column align-center">
                    <v-icon size="30" color="primary" class="mb-2">mdi-cloud-upload</v-icon>
                    <div class="text-caption font-weight-medium text-grey-darken-2">Upload Foto</div>
                  </div>
                </div>
                <input ref="fileSpeedtest" type="file" accept="image/*" style="display: none" @change="handleFileUpload($event, 'photo_speedtest')" />
              </div>
            </v-col>
          </v-row>
        </div>
      </div>

      <!-- MAIN PREVIEW AREA -->
      <div class="print-preview-container">
        <!-- Loop for Bulk Print -->
        <div v-for="(item, index) in printItems" :key="index" class="print-item-group">
           <div class="print-pages-row">
              <!-- Page 1: Work Order -->
             <!-- Note: moved wrapper class logic to CSS -->

      <div class="page-a4 elevation-2 mx-auto bg-white" id="printable-area">
        <!-- Header -->
        <div class="d-flex justify-space-between align-start mb-3 border-bottom pb-2">
          <!-- Logo/Title Left -->
          <div>
             <div class="text-caption text-grey-darken-1 mb-1">{{ formatDate(new Date()) }}</div>
             <h1 class="text-h4 font-weight-bold primary--text mb-1">WORK ORDER</h1>
             <div class="text-subtitle-1 font-weight-medium">Formulir Instalasi & Aktivasi</div>
          </div>
          
          <!-- Header Right -->
          <div class="text-right">
            <div class="d-flex flex-column align-end">
              <!-- Logo JELANTIK -->
              <img 
                v-if="item.pelanggan?.harga_layanan?.brand === 'JELANTIK'" 
                src="/logo-jelantik.png" 
                alt="Logo" 
                class="mb-2"
                style="height: 50px; object-fit: contain;"
              />

              <img 
                v-if="item.pelanggan?.harga_layanan?.brand === 'JELANTIK NAGRAK'" 
                src="/logo-jelantik.png" 
                alt="Logo" 
                class="mb-2"
                style="height: 50px; object-fit: contain;"
              />
              
              <!-- Logo JAKINET -->
              <img 
                v-else-if="item.pelanggan?.harga_layanan?.brand === 'JAKINET'" 
                src="/logo-jakine.png" 
                alt="Logo" 
                class="mb-2"
                style="height: 80px; object-fit: contain;"
              />

              <!-- Company Name (Always Visible) -->
              <div class="text-caption font-weight-bold mb-1">ARTACOM BILLING SYSTEM</div>
            </div>
            
            <div class="text-h6 font-weight-bold mb-0">
              {{ item.workOrder?.no_wo || 'FTTH - 01 - NEW INSTALLATION' }}
            </div>
          </div>
        </div>

        <!-- Section: Customer Info -->
        <div class="section mb-1">
          <div class="section-title mb-1">
            <v-icon size="small" class="mr-2">mdi-account</v-icon>
            INFORMASI PELANGGAN
          </div>
          <table class="info-table">
            <tbody>
              <tr>
                <td width="30%" class="label">Nama Pelanggan</td>
                <td>: {{ item.pelanggan?.nama || '-' }}</td>
              </tr>
              <tr>
                <td class="label">ID Pelanggan (CID)</td>
                <td>: {{ item.pelanggan?.data_teknis?.user_pppoe || '................................................' }}</td>
              </tr>
              <tr>
                <td class="label">Nomor Telepon</td>
                <td>: {{ item.pelanggan?.no_telp || '-' }}</td>
              </tr>
              <tr>
                <td class="label">Email</td>
                <td>: {{ item.pelanggan?.email || '-' }}</td>
              </tr>
              <tr>
                <td class="label">Alamat Instalasi</td>
                <td>: {{ item.pelanggan?.alamat }} {{ item.pelanggan?.blok ? `Blok ${item.pelanggan.blok}` : '' }} {{ item.pelanggan?.unit ? `No. ${item.pelanggan.unit}` : '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Section: Service Info -->
        <div class="section mb-1">
          <div class="section-title mb-1">
            <v-icon size="small" class="mr-2">mdi-wifi</v-icon>
            LAYANAN & PERANGKAT
          </div>
          <table class="info-table">
            <tbody>
              <tr>
                <td width="30%" class="label">Brand / Provider</td>
                <td>: {{ item.pelanggan?.harga_layanan?.brand || item.pelanggan?.id_brand || '-' }}</td>
              </tr>
              <tr>
                <td class="label">Paket Layanan</td>
                <td>: <strong>{{ item.pelanggan?.layanan || '-' }}</strong></td>
              </tr>
              <tr>
                <td class="label">IP Address (WAN)</td>
                <td>: {{ item.pelanggan?.data_teknis?.ip_address || '................................................' }}</td>
              </tr>
              <tr>
                <td class="label">Serial Number (SN) Modem</td>
                <td>: ............................................................................</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Section: Technician Checklist -->
        <div class="section mb-2">
          <div class="section-title mb-2">
            <v-icon size="small" class="mr-2">mdi-clipboard-check</v-icon>
            PEMERIKSAAN TEKNIS (Diisi oleh Teknisi)
          </div>

          <!-- Tanggal Instalasi Field -->
          <v-row class="mb-4">
            <v-col cols="4">
              <div class="measurement-box">
                <div class="label">Tanggal Instalasi</div>
                <div class="value-date">
                  <template v-if="item.tanggalInstalasi">{{ formatDate(new Date(item.tanggalInstalasi)) }}</template>
                  <template v-else>&nbsp;</template>
                </div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="measurement-box">
                <div class="label">Jam Mulai</div>
                <div class="value-date">&nbsp;</div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="measurement-box">
                <div class="label">Jam Selesai</div>
                <div class="value-date">&nbsp;</div>
              </div>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Cek Port ODP / FAT</span>
              </div>
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Kabel Dropcore Rapi</span>
              </div>
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Modem / ONU Online</span>
              </div>
            </v-col>
            <v-col cols="6">
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Speed Test Lancar</span>
              </div>
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Konfigurasi WiFi</span>
              </div>
              <div class="checklist-item mb-2">
                <div class="box"></div>
                <span>Edukasi Pelanggan</span>
              </div>
            </v-col>
          </v-row>

          <!-- Measurement Fields -->
          <v-row class="mt-4">
            <v-col cols="6">
              <div class="measurement-box">
                <div class="label">Redaman (Power dBm)</div>
                <div class="value">dBm</div>
              </div>
            </v-col>
            <v-col cols="6">
              <div class="measurement-box">
                <div class="label">Speed Test (Down/Up)</div>
                <div class="value">Mbps / Mbps</div>
              </div>
            </v-col>
          </v-row>
        </div>

        <!-- Section: Signature (Moved to Page 1) -->
        <div class="signature-section mt-10">
          <v-row>
            <v-col cols="6" class="text-center">
              <div class="mb-4 font-weight-bold">Disetujui Oleh (Pelanggan),</div>
              
              <!-- Signature Image (Show if uploaded) -->
              <div v-if="item.documents?.signature_pelanggan" class="signature-image-container mx-auto" style="width: 200px;">
                <img 
                  :src="getDocumentUrl(item.documents.signature_pelanggan)" 
                  class="signature-image" 
                  alt="Tanda Tangan Pelanggan"
                  style="width: 100%; height: auto; display: block;"
                />
                
                <!-- Delete Button (Only Show in Screen, Hide in Print) -->
                <div class="no-print mt-2" v-if="!isBulkMode">
                  <v-btn 
                    size="x-small" 
                    color="error" 
                    variant="text" 
                    prepend-icon="mdi-delete"
                    @click="deleteDocument('signature_pelanggan')"
                  >Hapus Tanda Tangan</v-btn>
                </div>
              </div>

              <!-- Signature Pad (Show if NOT uploaded and NOT Bulk Mode) -->
              <div v-else-if="!isBulkMode" class="signature-pad-wrapper no-print mx-auto" style="width: 100%; max-width: 300px;">
                <div class="signature-pad-container mb-2">
                  <VueSignaturePad
                    id="signature_pelanggan"
                    width="100%"
                    height="150px"
                    ref="signaturePadPelanggan"
                    :options="sigOption"
                  />
                </div>
                <div class="signature-actions d-flex justify-center gap-2">
                  <v-btn size="small" variant="text" color="grey" @click="clearSignature('pelanggan')">Ulangi</v-btn>
                  <v-btn size="small" color="primary" @click="saveSignature('pelanggan')">Simpan</v-btn>
                </div>
              </div>

              <!-- Empty Line (Fallback for Print if no signature) -->
              <div v-if="!item.documents?.signature_pelanggan" class="signature-line mx-auto mt-16 print-only"></div>
              
              <div class="mt-2 text-body-2 font-weight-medium">{{ item.pelanggan?.nama || 'Nama Pelanggan' }}</div>
            </v-col>
            
            <v-col cols="6" class="text-center">
              <div class="mb-4 font-weight-bold">Dikerjakan Oleh (Teknisi),</div>
              
              <!-- Signature Image (Show if uploaded) -->
              <div v-if="item.documents?.signature_teknisi" class="signature-image-container mx-auto" style="width: 200px;">
                <img 
                  :src="getDocumentUrl(item.documents.signature_teknisi)" 
                  class="signature-image" 
                  alt="Tanda Tangan Teknisi"
                  style="width: 100%; height: auto; display: block;"
                />

                 <!-- Delete Button (Only Show in Screen, Hide in Print) -->
                <div class="no-print mt-2" v-if="!isBulkMode">
                  <v-btn 
                    size="x-small" 
                    color="error" 
                    variant="text" 
                    prepend-icon="mdi-delete"
                    @click="deleteDocument('signature_teknisi')"
                  >Hapus Tanda Tangan</v-btn>
                </div>
              </div>

               <!-- Signature Pad (Show if NOT uploaded and NOT Bulk Mode) -->
              <div v-else-if="!isBulkMode" class="signature-pad-wrapper no-print mx-auto" style="width: 100%; max-width: 300px;">
                <div class="signature-pad-container mb-2">
                  <VueSignaturePad
                    id="signature_teknisi"
                    width="100%"
                    height="150px"
                    ref="signaturePadTeknisi"
                    :options="sigOption"
                  />
                </div>
                <div class="signature-actions d-flex justify-center gap-2">
                  <v-btn size="small" variant="text" color="grey" @click="clearSignature('teknisi')">Ulangi</v-btn>
                  <v-btn size="small" color="primary" @click="saveSignature('teknisi')">Simpan</v-btn>
                </div>
              </div>

              <!-- Empty Line (Fallback for Print if no signature) -->
              <div v-if="!item.documents?.signature_teknisi" class="signature-line mx-auto mt-10 print-only"></div>

              <div class="mt-2 text-body-2">.....................................</div>
            </v-col>
          </v-row>
        </div>
      </div>

      <!-- Page 2: BA Instalasi -->
      <div class="page-a4 elevation-2 mx-auto bg-white" v-if="item.hasPhotos">

        <!-- Section: Documentation Photos (Printable) -->
        <div class="section mb-8">
           
           <!-- Header Page 2 -->
          <div class="d-flex justify-space-between align-start mb-6 border-bottom pb-2">
            <!-- Logo/Title Left -->
            <div>
               <div class="text-caption text-grey-darken-1 mb-1">{{ formatDate(new Date()) }}</div>
               <h1 class="text-h4 font-weight-bold primary--text mb-1">BA INSTALASI</h1>
               <div class="text-subtitle-1 font-weight-medium">Berita Acara Instalasi & Aktivasi</div>
            </div>
            
            <!-- Header Right -->
            <div class="text-right">
              <div class="d-flex flex-column align-end">
                <!-- Logo JELANTIK -->
                <img 
                  v-if="item.pelanggan?.harga_layanan?.brand === 'JELANTIK'" 
                  src="/logo-jelantik.png" 
                  alt="Logo" 
                  class="mb-2"
                  style="height: 50px; object-fit: contain;"
                />

                <!-- LOGO JELANTIK NAGRAK -->
                <img 
                  v-if="item.pelanggan?.harga_layanan?.brand === 'JELANTIK NAGRAK'" 
                  src="/logo-jelantik.png" 
                  alt="Logo" 
                  class="mb-2"
                  style="height: 50px; object-fit: contain;"
                />
                
                <!-- Logo JAKINET -->
                <img 
                  v-else-if="item.pelanggan?.harga_layanan?.brand === 'JAKINET'" 
                  src="/logo-jakine.png" 
                  alt="Logo" 
                  class="mb-2"
                  style="height: 80px; object-fit: contain;"
                />
  
                <!-- Company Name (Always Visible) -->
                <div class="text-caption font-weight-bold mb-1">ARTACOM BILLING SYSTEM</div>
              </div>
              
              <div class="text-h6 font-weight-bold mb-0">
                {{ item.workOrder?.no_wo || 'FTTH - 01 - NEW INSTALLATION' }}
              </div>
            </div>
          </div>

          <div class="section-title mb-3">
            <v-icon size="small" class="mr-2">mdi-camera</v-icon>
            DOKUMENTASI FOTO
          </div>

          <v-row>
            <v-col cols="6" v-if="item.documents.photo_odp_before">
              <div class="photo-box">
                <div class="photo-label">ODP (Sebelum)</div>
                <img :src="getDocumentUrl(item.documents.photo_odp_before)" alt="ODP Before" class="photo-print" />
              </div>
            </v-col>
            <v-col cols="6" v-if="item.documents.photo_odp_after">
              <div class="photo-box">
                <div class="photo-label">ODP (Sesudah)</div>
                <img :src="getDocumentUrl(item.documents.photo_odp_after)" alt="ODP After" class="photo-print" />
              </div>
            </v-col>
            <v-col cols="6" v-if="item.documents.photo_onu">
              <div class="photo-box">
                <div class="photo-label">ONU/ONT Aktif</div>
                <img :src="getDocumentUrl(item.documents.photo_onu)" alt="ONU" class="photo-print" />
              </div>
            </v-col>
            <v-col cols="6" v-if="item.documents.photo_speedtest">
              <div class="photo-box">
                <div class="photo-label">Speed Test</div>
                <img :src="getDocumentUrl(item.documents.photo_speedtest)" alt="Speedtest" class="photo-print" />
              </div>
            </v-col>
          </v-row>
          
           <!-- Additional Signatures (Leader & Finance) -->
          <div class="signature-section mt-4">
            <v-row>
              <v-col cols="6" class="text-center">
                <div class="mb-8 text-caption font-weight-bold">Mengetahui (Leader / Spv),</div>
                <div class="signature-line mx-auto"></div>
                <div class="mt-2 text-caption">.....................................</div>
              </v-col>
              <v-col cols="6" class="text-center">
                <div class="mb-8 text-caption font-weight-bold">Diverifikasi (Finance),</div>
                <div class="signature-line mx-auto"></div>
                <div class="mt-2 text-caption">.....................................</div>
              </v-col>
            </v-row>
            <!-- Additional Signature (Teknisi 2 / Helper) -->
             <v-row class="mt-2 justify-center">
              <v-col cols="6" class="text-center">
                <div class="mb-8 text-caption font-weight-bold">Dikerjakan Oleh (Teknisi),</div>
                <div class="signature-line mx-auto"></div>
                <div class="mt-2 text-caption">.....................................</div>
              </v-col>
            </v-row>
          </div>
        </div>

        <!-- Section: Signature -->


      </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, getCurrentInstance } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// @ts-ignore
import { VueSignaturePad } from 'vue-signature-pad';
import apiClient, { instalasiAPI } from '@/services/api';

const route = useRoute();
const router = useRouter();
const pelanggan = ref<any>(null);
const workOrder = ref<any>(null);
const workOrderList = ref<any[]>([]);
const selectedWoNo = ref<string | null>(null);
const tanggalInstalasi = ref<string>('');
const saving = ref(false);
const uploading = ref(false);

const signaturePadPelanggan = ref<any>(null);
const signaturePadTeknisi = ref<any>(null);
const sigOption = {
  penColor: "rgb(0, 0, 0)",
  backgroundColor: "rgb(255,255,255)"
};

// Documents storage
const documents = ref<Record<string, any>>({
  photo_odp_before: null,
  photo_odp_after: null,
  photo_onu: null,
  photo_speedtest: null,
  signature_pelanggan: null,
  signature_teknisi: null
});

// Check if any photos are uploaded
const hasPhotos = computed(() => {
  return Object.values(documents.value).some(doc => doc !== null);
});

// Helper untuk mendapatkan tanggal hari ini dalam format YYYY-MM-DD
const getTodayDate = () => {
  return new Date().toISOString().split('T')[0];
};

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  }).format(date);
};

// Get document URL for display
const getDocumentUrl = (doc: any) => {
  if (!doc) return '';
  // If doc is an object (from API response or reactive state)
  if (typeof doc === 'object') {
    const id = doc.id || doc.value?.id;
    if (id) {
      return `${apiClient.defaults.baseURL}/instalasi/documents/${id}/download`;
    }
  }
  // If doc is just an ID (number or string)
  if (typeof doc === 'number' || typeof doc === 'string') {
    return `${apiClient.defaults.baseURL}/instalasi/documents/${doc}/download`;
  }
  return '';
};

// Safe file input trigger
// Define refs interface manually since vue-tsc might complain
const fileOdpBefore = ref<HTMLInputElement | null>(null);
const fileOdpAfter = ref<HTMLInputElement | null>(null);
const fileOnu = ref<HTMLInputElement | null>(null);
const fileSpeedtest = ref<HTMLInputElement | null>(null);

const triggerFileInput = (refName: string) => {
  const refs: Record<string, any> = {
    fileOdpBefore,
    fileOdpAfter,
    fileOnu,
    fileSpeedtest
  };
  
  const fileInput = refs[refName]?.value;
  if (fileInput) {
    fileInput.click();
  }
};

// Helper: Get pelanggan ID as number
const getPelangganId = (): number => {
  const id = route.params.id;
  const idStr = Array.isArray(id) ? id[0] : id;
  return Number(idStr);
};



const printItems = ref<any[]>([]);
const isBulkMode = computed(() => {
    return !!route.query.ids;
});

const fetchData = async () => {
  try {
    printItems.value = [];
    let ids: number[] = [];

    if (route.query.ids) {
        // Bulk Mode
        ids = (route.query.ids as string).split(',').map(Number);
    } else {
        // Single Mode
        const id = getPelangganId();
        if (id) ids.push(id);
    }

    // Iterate through IDs and fetch data for each
    for (const id of ids) {
        // Fetch Pelanggan details
        const response = await apiClient.get(`/pelanggan/${id}`);
        const pData = response.data;
        
        let woData = null;
        let tglInstalasi = '';
        const docsData: Record<string, any> = {
            photo_odp_before: null,
            photo_odp_after: null,
            photo_onu: null,
            photo_speedtest: null,
            signature_pelanggan: null,
            signature_teknisi: null
        };

        // Initialize tanggalInstalasi
        if (pData?.tgl_instalasi) {
          const date = new Date(pData.tgl_instalasi);
          tglInstalasi = date.toISOString().split('T')[0];
        }

        // Handle WO History
        if (pData?.work_orders && pData.work_orders.length > 0) {
          const sortedWos = [...pData.work_orders].sort((a: any, b: any) => b.id - a.id);
          woData = sortedWos[0];
        } else {
             woData = {
                no_wo: pData.no_wo || 'NEW',
                created_at: new Date()
            }
        }

         // Fetch Documents
         try {
            const docResponse = await instalasiAPI.getDocuments(id);
            if (docResponse.data?.documents) {
              docResponse.data.documents.forEach((doc: any) => {
                docsData[doc.document_type] = doc;
              });
            }
         } catch (e) {
            console.error(`Error fetching docs for ${id}:`, e);
         }

         // Check photos
         const hasPhotos = Object.values(docsData).some(doc => doc !== null);

         // Add to item list
         printItems.value.push({
            pelanggan: pData,
            workOrder: woData,
            documents: docsData,
            tanggalInstalasi: tglInstalasi,
            hasPhotos: hasPhotos
         });

         // If single mode, populate the global refs for backward compatibility/upload section
         if (!isBulkMode.value) {
            pelanggan.value = pData;
            workOrder.value = woData;
            tanggalInstalasi.value = tglInstalasi;
            documents.value = docsData;
            // workOrderList logic omitted for bulk safety, but okay for single
             if (pData?.work_orders) {
                workOrderList.value = [...pData.work_orders].sort((a: any, b: any) => b.id - a.id);
                selectedWoNo.value = woData.no_wo;
             }
         }
    }

  } catch (error) {
    console.error('Failed to fetch data:', error);
    alert('Gagal memuat data pelanggan');
  }
};

const fetchDocuments = async (pelangganId: number) => {
  try {
    const response = await instalasiAPI.getDocuments(pelangganId);
    if (response.data?.documents) {
      // Map documents by type
      response.data.documents.forEach((doc: any) => {
        documents.value[doc.document_type] = doc;
      });
    }
  } catch (error) {
    console.error('Failed to fetch documents:', error);
    // Don't alert, just log it
  }
};

const handleFileUpload = async (event: Event, documentType: string) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    uploading.value = true;
    const pelangganId = getPelangganId();

    const response = await instalasiAPI.uploadDocument(
      pelangganId,
      documentType,
      file
    );

    // Update documents ref
    if (response.data?.document) {
      documents.value[documentType] = response.data.document;
    }

    // Show success message
    alert(`Foto ${documentType.replace(/_/g, ' ')} berhasil diupload!`);

  } catch (error) {
    console.error('Upload failed:', error);
    alert('Gagal upload foto. Silakan coba lagi.');
  } finally {
    uploading.value = false;
    // Reset input
    input.value = '';
  }
};

// Signature Handling
const uploadSignature = async (role: 'pelanggan' | 'teknisi', silent = false) => {
  const padRef = role === 'pelanggan' ? signaturePadPelanggan.value : signaturePadTeknisi.value;
  if (!padRef) return false;

  // Handle array if inside v-for (Vue 3 behavior)
  const pad = Array.isArray(padRef) ? padRef[0] : padRef;
  if (!pad || typeof pad.saveSignature !== 'function') {
    console.error('Signature pad instance not found or saveSignature not available');
    return false;
  }

  const { isEmpty, data } = pad.saveSignature();
  
  if (isEmpty) {
    if (!silent) alert('Tanda tangan masih kosong!');
    return false;
  }

  try {
    if (!silent) uploading.value = true;
    
    // Convert base64 to file
    const res = await fetch(data);
    const blob = await res.blob();
    const file = new File([blob], `signature_${role}.png`, { type: 'image/png' });

    const pelangganId = getPelangganId();
    const docType = role === 'pelanggan' ? 'signature_pelanggan' : 'signature_teknisi';

    const response = await instalasiAPI.uploadDocument(
      pelangganId,
      docType,
      file
    );

    if (response.data?.document) {
      if (!isBulkMode.value) {
         documents.value[docType] = response.data.document;
         // Update printItems for immediate refresh
         if(printItems.value.length > 0) {
            printItems.value[0].documents[docType] = response.data.document;
         }
      }
    }

    if (!silent) alert('Tanda tangan berhasil disimpan!');
    return true;

  } catch (error) {
    console.error('Save signature failed:', error);
    if (!silent) alert('Gagal menyimpan tanda tangan.');
    return false;
  } finally {
    if (!silent) uploading.value = false;
  }
};

const saveSignature = (role: 'pelanggan' | 'teknisi') => {
    uploadSignature(role, false);
}

const clearSignature = (role: 'pelanggan' | 'teknisi') => {
  const padRef = role === 'pelanggan' ? signaturePadPelanggan.value : signaturePadTeknisi.value;
  const pad = Array.isArray(padRef) ? padRef[0] : padRef;
  if (pad && typeof pad.clearSignature === 'function') {
    pad.clearSignature();
  }
};

const deleteDocument = async (documentType: string) => {
  const doc = documents.value[documentType];
  if (!doc) return;

  if (!confirm(`Hapus foto ${documentType.replace(/_/g, ' ')}?`)) return;

  try {
    const docId = typeof doc === 'object' ? doc.id : doc;
    await instalasiAPI.deleteDocument(docId);
    documents.value[documentType] = null;
    
    // Update printItems too
    if (printItems.value.length > 0) {
         printItems.value[0].documents[documentType] = null;
    }

  } catch (error) {
    console.error('Delete failed:', error);
    alert('Gagal menghapus foto.');
  }
};

watch(selectedWoNo, (newVal) => {
  if (newVal) {
    const found = workOrderList.value.find(w => w.no_wo === newVal);
    if (found) workOrder.value = found;
  }
});

// Sync input tanggal instalasi dengan tampilan
watch(tanggalInstalasi, (newVal) => {
  if (printItems.value.length > 0) {
    printItems.value.forEach(item => {
      item.tanggalInstalasi = newVal;
    });
  }
});

const saveAndPrint = async () => {
  try {
    saving.value = true;

    // 1. Simpan Tanda Tangan jika ada (Silent save)
    // Cek apakah ada tanda tangan di pad pelanggan yg belum disave (pad visible)
    await uploadSignature('pelanggan', true);
    await uploadSignature('teknisi', true);

    // Give a small delay for DOM update if signatures were just saved
    await new Promise(resolve => setTimeout(resolve, 500));

    // 2. Simpan tanggal instalasi ke database
    const id = getPelangganId();
    await apiClient.patch(`/pelanggan/${id}`, {
      tgl_instalasi: tanggalInstalasi.value || null
    });

    // Update pelanggan value untuk display
    if (pelanggan.value) {
      pelanggan.value.tgl_instalasi = tanggalInstalasi.value;
    }

    // 3. Lanjutkan print
    window.print();
  } catch (error) {
    console.error('Gagal menyimpan tanggal instalasi:', error);
    alert('Gagal menyimpan data. Silakan coba lagi.');
  } finally {
    saving.value = false;
  }
};

const printPage = () => {
  window.print();
};

const handleBack = () => {
  router.push({ name: 'pelanggan' });
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.print-container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 50px;
}

.page-a4 {
  width: 210mm;
  min-height: 297mm;
  background: white;
  margin: 0 auto 30px auto; 
  padding: 10mm 15mm;
  box-sizing: border-box;
  position: relative;
  transition: all 0.3s ease;
}

/* ===== RESPONSIVE DESIGN - SCREEN ONLY ===== */
/* Mobile First Approach - Does NOT affect print */

/* Tablet (Portrait) */
@media screen and (max-width: 960px) {
  .page-a4 {
    width: 100%;
    min-height: auto;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  .text-h4 {
    font-size: 1.5rem !important;
  }
  
  .text-h6 {
    font-size: 1rem !important;
  }
  
  .section-title {
    font-size: 0.95rem;
  }
  
  .info-table td {
    font-size: 0.8rem;
    padding: 2px 4px;
  }
}

/* Mobile (Large - iPhone 14 Pro Max, etc) */
@media screen and (max-width: 600px) {
  .page-a4 {
    width: 100%;
    padding: 12px;
    margin: 0 0 12px 0;
    border-radius: 8px;
  }
  
  /* Header Adjustments */
  .text-h4 {
    font-size: 1.25rem !important;
  }
  
  .text-h6 {
    font-size: 0.9rem !important;
  }
  
  .text-subtitle-1 {
    font-size: 0.75rem !important;
  }
  
  .text-caption {
    font-size: 0.65rem !important;
  }
  
  /* Section Titles */
  .section-title {
    font-size: 0.85rem;
    padding-bottom: 4px;
  }
  
  .section-title .v-icon {
    font-size: 16px !important;
  }
  
  /* Info Table - Stack on Mobile */
  .info-table {
    display: block;
  }
  
  .info-table tbody,
  .info-table tr {
    display: block;
    width: 100%;
  }
  
  .info-table td {
    display: block;
    width: 100% !important;
    font-size: 0.75rem;
    padding: 4px 8px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .info-table td.label {
    font-weight: 600;
    color: #666;
    padding-bottom: 2px;
  }
  
  .info-table tr {
    margin-bottom: 8px;
    background: #fafafa;
    border-radius: 4px;
    overflow: hidden;
  }
  
  /* Measurement Boxes - Stack Vertically */
  .measurement-box {
    margin-bottom: 8px;
  }
  
  .measurement-box .label {
    font-size: 0.75rem;
  }
  
  .measurement-box .value,
  .measurement-box .value-date {
    font-size: 0.95rem;
    padding: 6px;
  }
  
  /* Checklist Items */
  .checklist-item {
    font-size: 0.8rem;
    margin-bottom: 8px;
  }
  
  .checklist-item .box {
    width: 16px;
    height: 16px;
    margin-right: 8px;
  }
  
  /* Signature Section */
  .signature-section {
    margin-top: 16px;
  }
  
  .signature-line {
    margin-top: 40px;
  }
}

/* Mobile (Small - iPhone SE, etc) */
@media screen and (max-width: 430px) {
  .page-a4 {
    padding: 10px;
  }
  
  .text-h4 {
    font-size: 1.1rem !important;
  }
  
  .section-title {
    font-size: 0.8rem;
  }
  
  .info-table td {
    font-size: 0.7rem;
    padding: 3px 6px;
  }
  
  .measurement-box .label {
    font-size: 0.7rem;
  }
  
  .checklist-item {
    font-size: 0.75rem;
  }
}

.section-title {
  font-weight: bold;
  font-size: 1.1rem;
  border-bottom: 2px solid #333;
  padding-bottom: 2px;
  display: flex;
  align-items: center;
  color: #333;
}

.signature-pad-container {
  border: 1px dashed #ccc;
  border-radius: 4px;
  background-color: #f9f9f9;
}

@media print {
  @page {
    size: A4;
    margin: 0;
  }
  
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* Hide everything by default */
  .no-print, 
  .v-app-bar,
  .v-navigation-drawer,
  .v-footer,
  .upload-section {
    display: none !important;
  }

  /* Specific hide for signature pads in print */
  .signature-pad-wrapper, 
  .signature-actions {
    display: none !important;
  }

  /* Ensure signature image is visible if exists */
  .signature-image {
    display: block !important;
  }
}

.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table td {
  padding: 1px 2px;
  vertical-align: top;
  font-size: 0.85rem;
  color: #333;
}

.info-table .label {
  font-weight: 400;
  color: #555;
}

.border-bottom {
  border-bottom: 1px solid #ccc;
}

.checklist-item {
  display: flex;
  align-items: center;
  font-size: 0.95rem;
  color: #333;
}

.checklist-item .box {
  width: 18px;
  height: 18px;
  border: 1.5px solid #555;
  margin-right: 10px;
}

.measurement-box {
  border: 1px solid #aaa;
  padding: 5px;
  border-radius: 4px;
  height: 100%;
}

.measurement-box .label {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 5px;
}

.measurement-box .value {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: right;
  color: #ccc; /* Placeholder color */
}

.measurement-box .value-date {
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
  color: #333;
  padding: 8px;
  border-bottom: 1px dashed #999;
}

.measurement-box .value-date {
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
  color: #333;
  padding: 8px;
  border-bottom: 1px dashed #999;
}

.signature-line {
  width: 80%;
  border-bottom: 1px solid #333;
}

/* Upload Section Modern Styles - REUSE EXISTING STYLES for sidebar */
.content-wrapper {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 20px;
  padding: 0 20px;
  width: 100%;
}

/* Tablet & Mobile - Stack Layout */
@media screen and (max-width: 960px) {
  .content-wrapper {
    flex-direction: column;
    padding: 0 12px;
    gap: 16px;
  }
}

@media screen and (max-width: 600px) {
  .content-wrapper {
    padding: 0 8px;
    gap: 12px;
  }
}

.sidebar {
  width: 320px; /* Standard width */
  flex-shrink: 0;
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

@media screen and (max-width: 960px) {
  .sidebar {
    width: 100%;
    position: static;
    max-height: none;
    order: 2; /* Move sidebar below preview on mobile */
  }
}

@media screen and (max-width: 600px) {
  .sidebar {
    margin-bottom: 16px;
  }
}

.print-preview-container {
   flex-grow: 1;
   display: flex;
   flex-direction: column;
   gap: 40px;
}

/* Row containing WO and BA */
.print-pages-row {
  display: flex;
  flex-direction: row;
  gap: 0; /* Papers touch each other on desktop */
  align-items: flex-start;
  flex-wrap: nowrap; /* Prevent wrapping on desktop */
}

/* Stack pages vertically on mobile */
@media screen and (max-width: 960px) {
  .print-pages-row {
    flex-direction: column;
    gap: 20px;
  }
}

@media screen and (max-width: 600px) {
  .print-pages-row {
    gap: 16px;
  }
}

@media print {
  @page {
    margin: 0;
    size: A4 portrait;
  }
  body {
    margin: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .print-container, .content-wrapper, .print-preview-container, .print-item-group {
    display: block !important;
    width: 100%;
    margin: 0;
    padding: 0;
    background: white;
  }
  
  .no-print, .sidebar {
    display: none !important;
  }

  /* Reset the side-by-side flex layout for print */
  .print-pages-row {
    display: block !important;
    gap: 0;
  }
  
  .page-a4 {
    width: 210mm;
    min-height: 297mm; 
    height: auto;
    margin: 0 auto;
    padding: 10mm 15mm; 
    box-shadow: none !important;
    border: none !important;
    page-break-after: always !important;
    break-after: page;
    position: relative;
    overflow: hidden; 
  }

  /* Make sure the last page doesn't produce an extra blank one if valid */
  .print-item-group:last-child .print-pages-row .page-a4:last-child {
      page-break-after: auto !important;
      break-after: auto;
  }
}

/* Upload Section Modern Styles */
.upload-action-box {
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  background-color: #fafafa;
  transition: all 0.3s ease;
  height: 100%;
}

.upload-action-box:hover {
  border-color: #2196F3;
  background-color: #f5f9ff;
}

.upload-action-box.has-file {
  border-style: solid;
  border-color: #e0e0e0;
}

.box-header {
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  color: #555;
  background: white;
  border-bottom: 1px solid #eee;
  text-align: center;
}

.upload-trigger {
  padding: 30px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 150px;
}

.preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: black;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-container .overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.preview-container:hover .overlay {
  opacity: 1;
}

/* Photo Box for Print */
.photo-box {
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.photo-label {
  background-color: #f5f5f5;
  padding: 4px 8px;
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  border-bottom: 1px solid #ddd;
}

.photo-print {
  width: 100%;
  height: 200px;
  object-fit: contain;
  background-color: #f8f8f8;
  display: block;
}

/* Mobile Photo Adjustments */
@media screen and (max-width: 600px) {
  .photo-box {
    margin-bottom: 12px;
  }
  
  .photo-label {
    font-size: 0.75rem;
    padding: 6px 8px;
  }
  
  .photo-print {
    height: 180px;
  }
}

/* Upload Section Responsive */
@media screen and (max-width: 600px) {
  .upload-action-box {
    border-radius: 8px;
  }
  
  .box-header {
    font-size: 0.8rem;
    padding: 6px 12px;
  }
  
  .upload-trigger {
    min-height: 120px;
    padding: 20px 12px;
  }
  
  .preview-container {
    aspect-ratio: 4/3;
  }
}

.page-break-inside-avoid {
  page-break-inside: avoid;
}

</style>
