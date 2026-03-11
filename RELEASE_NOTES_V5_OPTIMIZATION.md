# Release Notes - Billing Apps V5.0 Optimization Plan

Dokumen ini mencatat riwayat perubahan dan optimasi besar-besaran ("Refactoring") dari Versi 4.0 Stable menuju **Versi 5.0**. Fokus utama dari update ini adalah **Maintainability, Scalability, dan Reliability** tanpa mengubah Logika Bisnis inti.

---

## Ringkasan Perubahan (Update History)

| Komponen               | Status  | Perubahan Utama                                                                                                             |
| :--------------------- | :------ | :-------------------------------------------------------------------------------------------------------------------------- |
| **Background Jobs**    | Selesai | Pemecahan file monolithic `jobs.py` menjadi package modular.                                                                |
| **Service Layer**      | Selesai | Pembuatan Service terpusat: `Invoice`, `Langganan`, `DataTeknis`, `TroubleTicket`, `Dashboard`, `Inventory`, & `Pelanggan`. |
| **Modul Main**         | Selesai | Pemisahan Scheduler ke `app/core/scheduler.py`.                                                                             |
| **Router Refactoring** | Selesai | Pembersihan router `invoice.py`, `langganan.py`, `trouble_ticket.py`, `dashboard.py`, `inventory.py`, & `pelanggan.py`.     |
| **Utility Layer**      | Selesai | Pembuatan `app/utils/date_utils.py` untuk standarisasi tanggal.                                                             |
| **Consistency**        | Selesai | Penyatuan alur bisnis terpusat di Service Layer & Advanced Reporting.                                                       |

---

## Detail Teknis Refactoring

### 1. Modularisasi Background Jobs (`app/jobs/`)

Tabel pemetaan pemindahan kode dari `jobs.py` (V4.0) ke Package Jobs (V5.0):

- `app/jobs/billing.py`: Menangani pembuatan invoice harian & retry invoice gagal.
- `app/jobs/suspend.py`: Menangani isolir otomatis & sinkronisasi Mikrotik.
- `app/jobs/maintenance.py`: Menangani pembersihan cache & pengarsipan data.
- `app/jobs/reminders.py`: Menangani pengiriman notifikasi pengingat pembayaran.

**Manfaat:** Mengurangi risiko error sistemik jika salah satu job bermasalah dan memudahkan debugging spesifik per fitur.

### 2. Implementasi Service Layer (`app/services/`)

//================Invoice Section========\\

#### Invoice Service

Membuat service baru `InvoiceService` di `app/services/invoice_service.py` untuk mengeliminasi duplikasi kode:

- **`create_invoice()`**: Satu fungsi standar untuk membuat invoice (Manual, Otomatis, Reinvoice). Menjamin perhitungan pajak dan diskon selalu sama.
- **`process_payment()`**: Pusat logika saat tagihan lunas. Menjamin perhitungan tanggal jatuh tempo berikutnya (`next_due_date`) konsisten 100%.
- **`get_filtered_invoices_stmt()`**: Standarisasi query pencarian invoice di dashboard agar lebih cepat dan reliabel.

//================Langganan Section========\\

#### Langganan Service

- **`LanggananService` (`app/services/langganan_service.py`)**:
  - `calculate_price_and_due_date()`: Perhitungan harga (prorate/full) & pajak.
  - `create_langganan()`: Validasi data teknis & pembuatan record.
  - `update_langganan()`: Manajemen status "Berhenti" & history otomatis.
  - `apply_diskon_to_price()`: Logika diskon dinamis terpusat.

//================Data Teknis Section========\\

#### Data Teknis Service

- **`DataTeknisService` (`app/services/data_teknis_service.py`)**:
  - `create_data_teknis()`: Integrasi Mikrotik (trigger_create) & Notifikasi Finance.
  - `update_data_teknis()`: Sinkronisasi update ke Mikrotik (trigger_update).
  - `check_ip_availability()`: Validasi IP ganda di Database vs Seluruh Mikrotik Server.
  - `import_from_csv()`: Validasi massal (Email Customer, Server Name, ODP Code) & Batch Insert.

//================Trouble Ticket Section========\\

#### Trouble Ticket Service

- **`TroubleTicketService` (`app/services/trouble_ticket_service.py`)**:
  - `create_ticket()`: Standarisasi pembuatan tiket dengan nomor otomatis & notifikasi.
  - `update_downtime()`: Kalkulasi otomatis durasi gangguan (menit).
  - **Technical Stabilization**: Perbaikan `ResponseValidationError` via Comprehensive Nested Eager Loading.
  - **Advanced Reporting**: Analisis tren bulanan, resolusi rate teknisi, dan identifikasi akumulasi downtime tertinggi.

//================Dashboard Section========\\

#### Dashboard Service

- **`DashboardService` (`app/services/dashboard_service.py`)**:
  - **Modularization**: Pemindahan seluruh logika agregasi data dari router ke service layer.
  - **Optimization**: Eksekusi paralel menggunakan `asyncio.gather` & sentralisasi in-memory cache.
  - **Localization**: Implementasi `locale` setting untuk standarisasi format nama bulan Bahasa Indonesia.

//================Inventory Section========\\

#### Inventory Service

- **`InventoryService` (`app/services/inventory_service.py`)**:
  - **Modularization**: Sentralisasi manajemen stok, tracking history, dan validasi Serial Number/MAC Address.
  - **Bulk Operations**: Refaktorisasi `bulk_import` & template generation agar lebih robust.
  - **Consistency**: Otomasi pencatatan perubahan ke `InventoryHistory`.

//================Pelanggan Section========\\

#### Pelanggan Service

- **`PelangganService` (`app/services/pelanggan_service.py`)**:
  - **Modularization**: Sentralisasi manajemen database pelanggan dan alur CRUD terpusat.
  - **Advanced Search**: Implementasi query builder yang dioptimasi untuk filter kompleks (lokasi, status koneksi, brand).
  - **Auto-Sync Sync**: Logika cerdas berbasis Regex Matching untuk otomatis mengupdate paket langganan saat layanan berubah.
  - **Cascade Delete**: Implementasi penghapusan aman untuk seluruh data terkait dalam satu transaksi atomic.

---

### 3. Standarisasi Operasi Tanggal (`app/utils/date_utils.py`)

Semua fungsi manipulasi tanggal dipindahkan ke utility terpusat:

- `safe_to_datetime()`
- `safe_format_date()`
- `parse_xendit_datetime()`
- `safe_relativedelta_operation()`

### 4. Main App & Infrastruktur API

- **Modular Scheduler (`app/core/scheduler.py`)**: Pemisahan konfigurasi job harian dari `main.py`.
- **Sentralisasi API Prefix (`/api`)**: Seluruh endpoint kini otomatis menggunakan prefix `/api` via induk `api_router`.
- **Auto-Env Detection**: Frontend kini mendeteksi mode `Development` vs `Production` secara dinamis.

### 5. Optimasi Performa Database

- Implementasi **Comprehensive Eager Loading** (`joinedload`, `selectinload`) pada fungsi-fungsi kritikal untuk mencegah _N+1 Query_.
- Peningkatan efisiensi query pencarian invoice dan agregasi dashboard.

---

## Jaminan Keamanan & Business Logic

Update ini **TIDAK** mengubah:

1.  Alur perhitungan harga dan pajak.
2.  Mekanisme integrasi Xendit.
3.  Logika "Safety Net" Mikrotik (Auto-Rollback tetap aktif).
4.  Skema database inti.

## Catatan untuk Developer

- Selalu gunakan **Service Layer** untuk menambah fitur bisnis baru.
- Gunakan `date_utils` untuk semua manipulasi waktu.
- Pastikan menggunakan `async` secara konsisten pada lapisan database.

---

## RENCANA OPTIMASI MENDATANG (BACKLOG)

### 1. Modul Keuangan / Xendit (Prioritas: TINGGI)

**Masalah**: Logika webhook Xendit dan pengelolaan riwayat pembayaran masih tercampur di router, menyulitkan unit testing dan pemeliharaan integrasi eksternal.
**Saran**: Pembuatan `PaymentService` untuk memisahkan validasi signature Xendit, otomasi pencatatan histori pembayaran, dan pemicuan status lunas pada invoice secara atomic.

### 2. Integrasi WhatsApp API (Prioritas: MENENGAH - TINGGI)

**Fitur**: Menggabungkan layanan WhatsApp Gateway API resmi / pihak ketiga ke dalam sistem notifikasi.
**Saran Implementasi**:

- **Automated Reminders**: Notifikasi otomatis via pesan WhatsApp H-3, H-1, dan hari-H jatuh tempo tagihan.
- **Payment Link Delivery**: Mengirimkan Link Pembayaran Xendit langsung ke WhatsApp pelanggan untuk memudahkan pelanggan dalam melakukan checkout (Tap n Pay).
- **Modul `NotificationService`**: Membuat _service layer_ terpusat khusus mengurus pengiriman pesan (WA/Email).

---

**Versi:** 5.0-beta-refactored  
**Status:** Stable / Production Ready  
**Tanggal:** 2026-03-10
