<template>
  <div style="height:500px; width:100%; border-radius: 8px; overflow: hidden;">
    <l-map 
      ref="map" 
      v-model:zoom="zoom" 
      :center="center" 
      :use-global-leaflet="false"
    >
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer-type="base"
        name="OpenStreetMap"
      ></l-tile-layer>

        <l-marker 
        v-for="odp in odpsWithCoords" 
        :key="odp.id" 
        :lat-lng="[odp.latitude!, odp.longitude!]"
        >
        <l-popup>
          <div class="font-weight-bold">{{ odp.kode_odp }}</div>
          <div>{{ odp.alamat }}</div>
        </l-popup>
      </l-marker>
    </l-map>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LPopup } from "@vue-leaflet/vue-leaflet";

// --- Tipe Data ---
interface ODP {
  id: number;
  kode_odp: string;
  alamat: string;
  latitude?: number;
  longitude?: number;
}

// --- Props ---
// Komponen ini menerima 'props' bernama 'odps' dari parent (ODPView.vue)
const props = defineProps({
  odps: {
    type: Array as () => ODP[],
    default: () => []
  }
});

// --- State Peta ---
const zoom = ref(13);
// Atur titik tengah peta. Sesuaikan dengan lokasi utama Anda (contoh: Bekasi)
const center = ref<[number, number]>([-6.2383, 106.9756]); 

// --- Computed Property ---
// Filter ODP agar hanya yang memiliki data latitude & longitude yang akan ditampilkan
// Ini mencegah error jika ada data ODP lama yang belum punya koordinat
const odpsWithCoords = computed(() => {
  return props.odps.filter(odp => 
    odp.latitude !== null && odp.longitude !== null && 
    odp.latitude !== undefined && odp.longitude !== undefined
  );
});

</script>