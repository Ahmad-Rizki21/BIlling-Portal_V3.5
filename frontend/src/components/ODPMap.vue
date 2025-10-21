<template>
  <div style="height: 500px; width: 100%; border-radius: 8px; overflow: hidden">
    <div v-if="loading" class="d-flex justify-center align-center" style="height: 100%">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>
    <div v-else ref="mapContainer" style="width: 100%; height: 100%"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// --- Tipe Data ---
interface ODP {
  id: number;
  kode_odp: string;
  alamat: string;
  latitude?: number;
  longitude?: number;
}

// --- Props ---
const props = defineProps({
  odps: {
    type: Array as () => ODP[],
    default: () => [],
  },
});

// --- State ---
const loading = ref(true);
const mapContainer = ref<HTMLDivElement | null>(null);
let map: L.Map | null = null;
let markers: L.Marker[] = [];

// --- Computed Property ---
const odpsWithCoords = computed(() => {
  return props.odps.filter(
    (odp) => odp.latitude != null && odp.longitude != null
  );
});

// --- Methods ---
const updateMarkers = () => {
  if (!map) return;

  // Clear existing markers
  markers.forEach(marker => map!.removeLayer(marker));
  markers = [];

  // Add new markers
  odpsWithCoords.value.forEach((odp) => {
    if (odp.longitude && odp.latitude) {
      const popupContent = `
        <div style="padding: 8px;">
          <div style="font-weight: bold;">${odp.kode_odp}</div>
          <div>${odp.alamat}</div>
        </div>
      `;

      const customIcon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background: #1976D2;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    const popup = L.popup()
        .setLatLng([odp.latitude, odp.longitude])
        .setContent(popupContent);

    const newMarker = L.marker([odp.latitude, odp.longitude], { icon: customIcon })
        .bindPopup(popup)
        .addTo(map!);

      markers.push(newMarker);
    }
  });
};

// --- Lifecycle Hooks ---
onMounted(async () => {
  // Set loading to false to render the map container
  loading.value = false;
  
  try {
    // Wait for the DOM to update after loading is set to false
    await nextTick();

    if (mapContainer.value) {
      // Initialize Leaflet map centered on Indonesia
      const mapInstance = L.map(mapContainer.value).setView([-6.2383, 106.9756], 12);
      map = mapInstance;

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(mapInstance);

      // Now that the map is initialized, update the markers
      updateMarkers();
    }
  } catch (error: unknown) {
    console.error('Failed to initialize map:', error);
    // Show error message instead of infinite loading
    if (mapContainer.value) {
      mapContainer.value.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666; text-align: center;">
          <div>
            <v-icon size="48" color="error">mdi-map-marker-off</v-icon>
            <p style="margin: 10px 0; font-weight: 500;">Map tidak dapat dimuat</p>
            <p style="margin: 0; font-size: 14px; color: #999;">Pastikan koneksi internet stabil</p>
          </div>
        </div>
      `;
    }
  }
});

onUnmounted(() => {
  map?.remove();
});

// --- Watchers ---
watch(odpsWithCoords, () => {
  if (!loading.value) {
    updateMarkers();
  }
}, { immediate: false });

</script>

<style scoped>
/* Custom marker styling */
.custom-marker {
  background: #1976D2;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* Leaflet map styling */
.leaflet-container {
  border-radius: 8px;
  overflow: hidden;
}

.leaflet-tile-pane {
  z-index: 1;
}

.leaflet-control-container {
  z-index: 1000;
}
</style>