export interface Pelanggan {
  id: number;
  no_ktp: string;
  nama: string;
  alamat: string;
  email: string;
  no_telp: string;
  tgl_instalasi: string | Date | null;
  blok: string;
  unit: string;
  layanan: string;
}