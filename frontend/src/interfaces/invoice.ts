export interface Invoice {
  id: number;
  invoice_number: string;
  pelanggan_id: number;
  id_pelanggan: string;
  total_harga: number;
  tgl_invoice: string;
  tgl_jatuh_tempo: string;
  status_invoice: 'Lunas' | 'Belum Dibayar' | 'Kadaluarsa' | 'Expired';
  payment_link?: string | null;
  paid_at?: string | null;
  email: string;
  no_telp: string;
  pelanggan_nama?: string | null;  // Nama pelanggan langsung dari invoice object
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
  // Reinvoice tracking fields
  is_reinvoice?: boolean;
  original_invoice_id?: number | null;
  reinvoice_reason?: string | null;
  // Invoice type field
  invoice_type?: string;
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