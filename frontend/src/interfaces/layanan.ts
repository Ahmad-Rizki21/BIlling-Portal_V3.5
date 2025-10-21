// src/interfaces/layanan.ts

export interface HargaLayanan {
  id_brand: string;
  brand: string;
  pajak: number;
  xendit_key_name: string;
}

export interface PaketLayanan {
  id?: number; // Opsional saat membuat baru
  id_brand: string;
  nama_paket: string;
  kecepatan: number;
  harga: number;
}