export interface Invoice {
  id: number;
  invoice_number: string;
  pelanggan_id: number;
  id_pelanggan: string;
  total_harga: number;
  tgl_invoice: string;
  tgl_jatuh_tempo: string;
  status_invoice: 'Lunas' | 'Belum Dibayar' | 'Kadaluarsa';
  payment_link?: string | null;
  paid_at?: string | null;
  email: string;
  no_telp: string;
  // Tambahkan property yang missing dari backend schema
  payment_link_status?: string | null;
  is_payment_link_active?: boolean | null;
  brand?: string;
  xendit_id?: string | null;
  xendit_external_id?: string | null;
  expiry_date?: string | null;
  paid_amount?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  metode_pembayaran?: string | null;
}

export interface PelangganSelectItem {
  id: number;
  nama: string;
}

export interface LanggananSelectItem {
  id: number;
  pelanggan_id: number;
  display_name: string;
}