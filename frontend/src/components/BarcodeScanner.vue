<template>
  <v-dialog v-model="isOpen" max-width="600px" persistent>
    <v-card class="barcode-scanner-dialog">
      <v-card-title class="scanner-header">
        <v-icon class="me-3" color="primary">
          {{ isMultipleMode ? 'mdi-barcode-multiple' : 'mdi-barcode-scan' }}
        </v-icon>
        <span>
          {{
            isMultipleMode
              ? 'Scan Multiple Barcode (EN, SN, MAC)'
              : scanType === 'serial'
                ? 'Scan Serial Number'
                : 'Scan MAC Address'
          }}
        </span>
        <v-spacer></v-spacer>
        <v-btn
          icon
          variant="text"
          size="small"
          @click="closeScanner"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="scanner-content">
        <!-- Scanner Instructions -->
        <div class="scanner-instructions">
          <div class="scanner-icon-wrapper">
            <v-icon size="80" color="primary" class="scanner-main-icon">
              {{ isMultipleMode ? 'mdi-barcode-multiple' : 'mdi-barcode-scanner' }}
            </v-icon>
            <v-icon size="40" color="success" class="scanner-ready-icon">mdi-check-circle</v-icon>
          </div>

          <div class="text-center mt-4">
            <h3 class="text-h6 font-weight-bold mb-2">
              {{ isMultipleMode ? 'Scan Multiple Barcode' : 'Siap Scan Barcode' }}
            </h3>
            <p class="text-body-2 text-medium-emphasis mb-4">
              <span v-if="isMultipleMode">
                Scan 3 barcode (EN, SN, MAC) dari dus barang. System akan otomatis mendeteksi tipe barcode.
              </span>
              <span v-else>
                Gunakan alat scanner barcode eksternal Anda
              </span>
            </p>

            <!-- Status Indicator -->
            <div class="status-indicator">
              <v-chip
                :color="isListening ? 'success' : 'warning'"
                variant="elevated"
                size="large"
                prepend-icon="mdi-ear-hearing"
              >
                <span v-if="isMultipleMode && scanResults.length > 0">
                  {{ scanResults.length }} barcode terdeteksi
                </span>
                <span v-else>
                  {{ isListening ? 'Scanner Aktif - Siap Menerima Input' : 'Mengaktifkan Scanner...' }}
                </span>
              </v-chip>
            </div>
          </div>

          <!-- Visual Scanner Field -->
          <div class="scanner-field-wrapper">
            <v-text-field
              ref="scannerField"
              v-model="scannedValue"
              :label="`arahkan scanner ke barcode ${scanType === 'serial' ? 'Serial Number' : 'MAC Address'}`"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-barcode"
              class="scanner-field"
              readonly
              bg-color="grey-lighten-4"
            >
              <template v-slot:append-inner>
                <v-progress-circular
                  v-if="isListening"
                  indeterminate
                  size="20"
                  width="2"
                  color="success"
                ></v-progress-circular>
              </template>
            </v-text-field>

            <div class="scanner-hint">
              <v-icon size="20" color="info">mdi-information</v-icon>
              <span class="text-caption">
                Barcode akan terdeteksi otomatis saat scanner membaca kode
              </span>
            </div>
          </div>
        </div>

        <!-- Multiple Scan Results (only show in multiple mode) -->
        <div v-if="isMultipleMode && scanResults.length > 0" class="multiple-results">
          <v-divider class="my-4"></v-divider>
          <h4 class="text-h6 mb-3">Hasil Scan:</h4>

          <div class="results-grid">
            <!-- EN Result -->
            <div v-if="getLatestResultByType('en')" class="result-card">
              <div class="result-header">
                <v-icon size="20" color="primary">mdi-package-variant</v-icon>
                <span class="result-label">Equipment Number (EN)</span>
                <v-chip size="x-small" color="success">✓</v-chip>
              </div>
              <div class="result-value">
                <code class="result-code">{{ getLatestResultByType('en')?.formatted }}</code>
              </div>
            </div>

            <!-- Serial Number Result -->
            <div v-if="getLatestResultByType('serial')" class="result-card">
              <div class="result-header">
                <v-icon size="20" color="info">mdi-identifier</v-icon>
                <span class="result-label">Serial Number (SN)</span>
                <v-chip size="x-small" color="success">✓</v-chip>
              </div>
              <div class="result-value">
                <code class="result-code">{{ getLatestResultByType('serial')?.formatted }}</code>
              </div>
            </div>

            <!-- MAC Address Result -->
            <div v-if="getLatestResultByType('mac')" class="result-card">
              <div class="result-header">
                <v-icon size="20" color="warning">mdi-network-outline</v-icon>
                <span class="result-label">MAC Address</span>
                <v-chip size="x-small" color="success">✓</v-chip>
              </div>
              <div class="result-value">
                <code class="result-code">{{ getLatestResultByType('mac')?.formatted }}</code>
              </div>
            </div>
          </div>

          <!-- Processing indicator -->
          <div class="processing-hint mt-3">
            <v-icon size="16" color="info">mdi-information</v-icon>
            <span class="text-caption">
              {{ scanResults.length >= 3 ? 'Memproses hasil...' : `Scan ${3 - scanResults.length} barcode lagi` }}
            </span>
          </div>
        </div>

        <!-- Manual Input Section -->
        <v-divider class="my-4"></v-divider>
        <div class="manual-input-section">
          <div class="d-flex align-center gap-3 mb-3">
            <v-icon color="grey-darken-1">mdi-keyboard</v-icon>
            <span class="text-body-2">Input Manual (jika scanner tidak bekerja):</span>
          </div>
          <v-text-field
            ref="manualField"
            v-model="manualInput"
            :label="`Ketik ${scanType === 'serial' ? 'Serial Number' : 'MAC Address'} manual`"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-keyboard-outline"
            @keyup.enter="confirmManualInput"
            :hint="scanType === 'mac' ? 'Format: AA:BB:CC:DD:EE:FF atau AABBCCDDEEFF' : ''"
            persistent-hint
            clearable
          ></v-text-field>
        </div>

        <!-- Last Scanned Result -->
        <div v-if="lastScannedResult" class="last-result">
          <v-divider class="mb-3"></v-divider>
          <div class="d-flex align-center gap-2">
            <v-icon color="success" size="20">mdi-check-bold</v-icon>
            <span class="text-caption text-success font-weight-medium">Terakhir berhasil:</span>
            <code class="last-result-code">{{ lastScannedResult }}</code>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="scanner-actions">
        <v-btn
          variant="text"
          color="grey-darken-1"
          @click="closeScanner"
        >
          Tutup
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          v-if="isMultipleMode"
          color="warning"
          variant="outlined"
          @click="clearScanResults"
          prepend-icon="mdi-eraser"
        >
          Clear Hasil
        </v-btn>
        <v-btn
          v-else
          color="primary"
          variant="outlined"
          @click="resetScanner"
          prepend-icon="mdi-refresh"
        >
          Reset Scanner
        </v-btn>
        <v-btn
          v-if="manualInput && !isMultipleMode"
          color="success"
          variant="elevated"
          @click="confirmManualInput"
          prepend-icon="mdi-check"
        >
          Gunakan Manual
        </v-btn>
        <v-btn
          v-if="isMultipleMode && hasValidMultipleResults"
          color="success"
          variant="elevated"
          @click="processMultipleResults"
          prepend-icon="mdi-check-all"
        >
          Proses Hasil ({{ scanResults.length }} barcode)
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue';
import { useBarcodeScanner, type BarcodeScanResult } from '@/composables/useBarcodeScanner';

interface Props {
  modelValue: boolean;
  scanType: 'serial' | 'mac' | 'multiple';
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'detected', value: string): void;
  (e: 'multiple-detected', value: { en?: string; serial?: string; mac?: string }): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// State
const isOpen = ref(false);
const isListening = ref(false);
const scannedValue = ref('');
const manualInput = ref('');
const lastScannedResult = ref('');
const scannerField = ref<HTMLInputElement>();
const manualField = ref<HTMLInputElement>();

// Multiple scanning state
const scanResults = ref<BarcodeScanResult[]>([]);
const isMultipleMode = computed(() => props.scanType === 'multiple');

// Use barcode scanner composable
const {
  detectBarcodeType,
  processAnyBarcode,
  processMultipleScan,
} = useBarcodeScanner();

// USB Scanner state
let scannerBuffer = '';
let scannerTimeout: number | null = null;
let keyboardListener: ((event: KeyboardEvent) => void) | null = null;

// Sync with v-model
watch(() => props.modelValue, (newVal) => {
  isOpen.value = newVal;
  if (newVal) {
    nextTick(() => {
      startListening();
    });
  } else {
    stopListening();
  }
});

watch(isOpen, (newVal) => {
  emit('update:modelValue', newVal);
});

// USB Scanner Detection Methods
function startListening() {
  resetScanner();
  isListening.value = true;

  // Focus on scanner field untuk menerima input dari USB scanner
  nextTick(() => {
    if (scannerField.value) {
      const inputElement = scannerField.value.querySelector('input');
      if (inputElement) {
        inputElement.focus();
      }
    }
  });

  // Setup keyboard event listener untuk USB scanner
  keyboardListener = handleKeyboardInput;
  document.addEventListener('keydown', keyboardListener);
}

function stopListening() {
  isListening.value = false;

  if (keyboardListener) {
    document.removeEventListener('keydown', keyboardListener);
    keyboardListener = null;
  }

  if (scannerTimeout) {
    clearTimeout(scannerTimeout);
    scannerTimeout = null;
  }
}

function handleKeyboardInput(event: KeyboardEvent) {
  // Ignore if focus is on manual input field
  if (document.activeElement === manualField.value?.querySelector('input')) {
    return;
  }

  // USB scanner biasanya input karakter sangat cepat
  // Kita deteksi pola input cepat sebagai barcode scanner

  // Handle typical USB scanner behavior
  if (event.key === 'Enter') {
    // Enter biasanya menandakan akhir dari barcode scan
    if (scannerBuffer.length > 0) {
      processScannedData(scannerBuffer);
      scannerBuffer = '';
    }
    event.preventDefault();
    return;
  }

  // Handle tab atau escape
  if (event.key === 'Tab' || event.key === 'Escape') {
    scannerBuffer = '';
    return;
  }

  // Collect characters
  if (event.key && event.key.length === 1) {
    scannerBuffer += event.key;

    // Auto-reset buffer jika terlalu lama tidak ada input (tanda bukan scanner)
    if (scannerTimeout) {
      clearTimeout(scannerTimeout);
    }
    scannerTimeout = setTimeout(() => {
      scannerBuffer = '';
    }, 100) as any; // 100ms timeout untuk membedakan scanner vs manual typing

    // Update visual feedback
    scannedValue.value = scannerBuffer;
    event.preventDefault();
  }
}

function processScannedData(data: string) {
  if (isMultipleMode.value) {
    // Multiple scanning mode
    const result = processAnyBarcode(data);
    scanResults.value.push(result);

    // Update visual feedback
    scannedValue.value = `${scanResults.value.length} barcode terdeteksi`;

    // Auto-process after 3 scans or after 2 seconds of inactivity
    if (scanResults.value.length >= 3) {
      processMultipleResults();
    } else {
      // Reset timeout untuk auto-process
      if (scannerTimeout) {
        clearTimeout(scannerTimeout);
      }
      scannerTimeout = setTimeout(() => {
        if (scanResults.value.length > 0) {
          processMultipleResults();
        }
      }, 2000); // 2 detik untuk scan berikutnya
    }
  } else {
    // Single scanning mode (serial/mac)
    let processedText = data.trim();

    if (props.scanType === 'mac') {
      processedText = cleanMacAddress(processedText);
      if (!isValidMacAddress(processedText)) {
        showError('Format MAC Address tidak valid. Harap scan ulang.');
        return;
      }
    } else if (props.scanType === 'serial') {
      processedText = cleanSerialNumber(processedText);
      if (!processedText) {
        showError('Serial Number tidak valid. Harap scan ulang.');
        return;
      }
    }

    // Success
    lastScannedResult.value = processedText;
    emit('detected', processedText);

    // Auto close setelah berhasil
    setTimeout(() => {
      closeScanner();
    }, 500);
  }
}

function processMultipleResults() {
  if (scanResults.value.length === 0) return;

  const processed = processMultipleScan(scanResults.value);

  // Validasi bahwa kita punya minimal serial number
  if (!processed.serial) {
    showError('Serial Number tidak ditemukan. Harap scan ulang.');
    scanResults.value = [];
    return;
  }

  // Emit multiple detected event
  emit('multiple-detected', processed);

  // Update last scanned result dengan serial number
  lastScannedResult.value = processed.serial || '';

  // Auto close
  setTimeout(() => {
    closeScanner();
  }, 1000);
}

function confirmManualInput() {
  if (!manualInput.value.trim()) return;

  let processedText = manualInput.value.trim();

  if (props.scanType === 'mac') {
    processedText = cleanMacAddress(processedText);
    if (!isValidMacAddress(processedText)) {
      showError('Format MAC Address tidak valid. Gunakan format AA:BB:CC:DD:EE:FF');
      return;
    }
  } else if (props.scanType === 'serial') {
    processedText = cleanSerialNumber(processedText);
    if (!processedText) {
      showError('Serial Number tidak valid');
      return;
    }
  }

  lastScannedResult.value = processedText;
  emit('detected', processedText);
  closeScanner();
}

function resetScanner() {
  scannerBuffer = '';
  scannedValue.value = '';
  manualInput.value = '';
  scanResults.value = [];

  // Clear any pending timeouts
  if (scannerTimeout) {
    clearTimeout(scannerTimeout);
    scannerTimeout = null;
  }

  // Re-focus on scanner field
  nextTick(() => {
    if (scannerField.value) {
      const inputElement = scannerField.value.querySelector('input');
      if (inputElement) {
        inputElement.focus();
      }
    }
  });
}

function showError(message: string) {
  // Show error in visual way
  if (scannerField.value) {
    const inputElement = scannerField.value.querySelector('input');
    if (inputElement) {
      inputElement.classList.add('error-shake');
      setTimeout(() => {
        inputElement.classList.remove('error-shake');
      }, 500);
    }
  }

  // Reset buffer
  scannerBuffer = '';
  scannedValue.value = '';
}

// Utility functions
function cleanMacAddress(mac: string): string {
  // Remove all non-hex characters
  const cleaned = mac.replace(/[^a-fA-F0-9]/g, '');

  // If exactly 12 hex characters, format as MAC address
  if (cleaned.length === 12) {
    return cleaned.match(/.{1,2}/g)?.join(':').toUpperCase() || '';
  }

  return '';
}

function isValidMacAddress(mac: string): boolean {
  const macRegex = /^([0-9A-F]{2}:){5}[0-9A-F]{2}$/i;
  return macRegex.test(mac);
}

function cleanSerialNumber(serial: string): string {
  // Remove unwanted characters, keep alphanumeric, dashes, underscores
  return serial.replace(/[^A-Za-z0-9\-_]/g, '').toUpperCase();
}

function closeScanner() {
  isOpen.value = false;
  stopListening();
  resetScanner();
}

// Helper functions untuk multiple scanning
function getLatestResultByType(type: string): BarcodeScanResult | undefined {
  return scanResults.value.filter(r => r.type === type).pop();
}

function clearScanResults() {
  scanResults.value = [];
  scannedValue.value = '';
  scannerBuffer = '';
}

const hasValidMultipleResults = computed(() => {
  if (!isMultipleMode.value) return false;

  // Check if we have at least a serial number
  const hasSerial = scanResults.value.some(r => r.type === 'serial' && r.isValid);
  if (!hasSerial) return false;

  // Check if we have at least one other type
  const hasEn = scanResults.value.some(r => r.type === 'en' && r.isValid);
  const hasMac = scanResults.value.some(r => r.type === 'mac' && r.isValid);

  return hasEn || hasMac;
});

// Cleanup on unmount
onUnmounted(() => {
  stopListening();
});
</script>

<style scoped>
.barcode-scanner-dialog {
  border-radius: 16px;
  overflow: hidden;
}

.scanner-header {
  background: rgba(var(--v-theme-primary), 0.05);
  padding: 20px 24px;
  font-size: 1.25rem;
  font-weight: 600;
}

.scanner-content {
  padding: 24px;
  background: rgb(var(--v-theme-surface));
}

.scanner-instructions {
  text-align: center;
  margin-bottom: 24px;
}

.scanner-icon-wrapper {
  position: relative;
  display: inline-block;
}

.scanner-main-icon {
  animation: pulse 2s ease-in-out infinite;
}

.scanner-ready-icon {
  position: absolute;
  bottom: -5px;
  right: -5px;
  animation: checkBounce 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.95); }
}

@keyframes checkBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.status-indicator {
  margin: 16px 0;
}

.scanner-field-wrapper {
  max-width: 500px;
  margin: 0 auto;
}

.scanner-field {
  transition: all 0.3s ease;
}

.scanner-field.error-shake {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.scanner-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 16px;
  background: rgba(var(--v-theme-info), 0.1);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-info), 0.2);
}

.manual-input-section {
  margin-top: 24px;
}

.last-result {
  margin-top: 16px;
}

.last-result-code {
  background: rgba(var(--v-theme-success), 0.1);
  color: rgb(var(--v-theme-success));
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
  border: 1px solid rgba(var(--v-theme-success), 0.2);
}

/* Multiple Results Styling */
.multiple-results {
  margin-top: 24px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.result-card {
  background: rgba(var(--v-theme-surface), 0.8);
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.result-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--v-theme-primary), var(--v-theme-secondary));
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.result-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  flex-grow: 1;
}

.result-value {
  background: rgba(var(--v-theme-primary), 0.05);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  min-height: 48px;
  display: flex;
  align-items: center;
}

.result-code {
  background: none;
  color: rgb(var(--v-theme-primary));
  padding: 0;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  word-break: break-all;
  line-height: 1.4;
}

.processing-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-info), 0.1);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-info), 0.2);
}

.scanner-actions {
  background: rgba(var(--v-theme-surface), 0.5);
  padding: 16px 24px;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}

/* Dark mode adjustments */
.v-theme--dark .scanner-header {
  background: rgba(var(--v-theme-primary), 0.15);
}

.v-theme--dark .scanner-content {
  background: #1e293b;
}

.v-theme--dark .scanner-actions {
  background: rgba(15, 23, 42, 0.5);
}

.v-theme--dark .scanner-hint {
  background: rgba(var(--v-theme-info), 0.15);
  border-color: rgba(var(--v-theme-info), 0.3);
}

.v-theme--dark .last-result-code {
  background: rgba(var(--v-theme-success), 0.15);
  border-color: rgba(var(--v-theme-success), 0.3);
}

/* Focus states for accessibility */
.scanner-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

/* Scanner field visual feedback when listening */
.scanner-field :deep(.v-field) {
  transition: all 0.3s ease;
}

.scanner-field :deep(.v-field--focused) {
  border-color: rgb(var(--v-theme-success));
  box-shadow: 0 0 0 2px rgba(var(--v-theme-success), 0.2);
}

/* Mobile responsiveness */
@media (max-width: 600px) {
  .scanner-content {
    padding: 16px;
  }

  .scanner-main-icon {
    size: 60px;
  }

  .scanner-ready-icon {
    size: 30px;
  }

  .scanner-field-wrapper {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .scanner-content {
    padding: 12px;
  }

  .scanner-actions {
    padding: 12px 16px;
    flex-direction: column;
    gap: 8px;
  }

  .scanner-actions .v-btn {
    width: 100%;
  }
}
</style>