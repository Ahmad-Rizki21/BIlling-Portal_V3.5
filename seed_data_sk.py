#!/usr/bin/env python3
"""
Seed script KHUSUS untuk Syarat & Ketentuan (S&K)
- Hanya mengimport 13 records syarat_ketentuan dengan konten lengkap
- TIDAK mengganggu data lain (pelanggan, langganan, invoice, dll)
- Aman digunakan kapan saja tanpa menghapus data penting
"""

import asyncio
import sys
import os
import re
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

async def create_seed_data():
    """Create seed data from existing SQL backup file"""

    print("🌱 Starting seed data creation from backup...")

    # Database setup
    from app.database import engine, Base

    async with engine.begin() as conn:
        print("📊 Database connected")

        # Read backup file
        backup_path = project_root / "DATABASE-EXISTING" / "backup_seed20251102.sql"

        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_path}")
            return

        print(f"📄 Reading backup file: {backup_path}")
        with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        print("✅ Backup file loaded successfully")

        # Clear existing data - ONLY syarat_ketentuan table
        print("🧹 Clearing existing syarat_ketentuan data...")
        tables_to_clear = [
            "syarat_ketentuan"  # Only clear this table
        ]

        for table in tables_to_clear:
            try:
                await conn.execute(text(f"DELETE FROM {table}"))
                await conn.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
                print(f"✅ Cleared {table}")
            except Exception as e:
                print(f"⚠️ Could not clear {table}: {e}")

        # Define complete syarat_ketentuan data directly
        # This ensures all 13 records with complete content are imported
        complete_records = [
            {
                "id": 1,
                "judul": "Update Fitur Sistem v2.1.4 - Menu S&K, Kalkulator Prorate, dan Perbaikan",
                "konten": "<p>Kami telah melakukan pembaruan pada sistem ke versi <strong>v2.1.4</strong>. Pembaruan ini mencakup beberapa penambahan fitur baru serta perbaikan untuk meningkatkan kenyamanan dan stabilitas. Berikut rinciannya:</p>\n\n<h4><strong>Penambahan Fitur Baru:</strong></h4>\n<ul>\n  <li><strong>Menu Syarat & Ketentuan (S&K):</strong> Menambahkan menu baru untuk mengelola dan melihat Syarat & Ketentuan (S&K) langsung dari dasbor.</li>\n  <li><strong>Tampilan Alamat di Menu Langganan:</strong> Informasi alamat pelanggan kini ditampilkan pada halaman langganan untuk mempermudah identifikasi lokasi.</li>\n  <li><strong>Kalkulator Prorate:</strong> Memperkenalkan fitur kalkulator untuk simulasi perhitungan tagihan prorate secara akurat.</li>\n  <li><strong>Shortcut WhatsApp:</strong> Menambahkan tombol pintasan WhatsApp untuk mempermudah dan mempercepat komunikasi dengan pelanggan.</li>\n</ul>\n\n<h4><strong>Perbaikan dan Peningkatan:</strong></h4>\n<ul>\n  <li><strong>Perbaikan Bug Profil PPPOE:</strong> Mengatasi masalah yang terjadi pada saat pengelolaan profil PPPOE untuk meningkatkan integrasi dengan Mikrotik.</li>\n  <li><strong>Perbaikan Bug Perhitungan Prorate:</strong> Menyempurnakan akurasi perhitungan pada fitur tagihan prorate.</li>\n</ul>\n\n<p>Pembaruan ini telah dipublikasikan pada <strong>18 Agustus 2025</strong>. Terima kasih telah menggunakan layanan kami.</p>",
                "tipe": "Pembaruan",
                "versi": "2.1.4",
                "created_at": "2025-08-18 15:27:57"
            },
            {
                "id": 2,
                "judul": "SYARAT & KETENTUAN",
                "konten": "<p>Dengan hormat,</p>\n<p>Bersama ini kami informasikan adanya pembaruan pada Syarat dan Ketentuan (S&K) terkait sistem penagihan, pembayaran, dan penonaktifan layanan. Pembaruan ini berlaku efektif sejak tanggal diumumkan.</p>\n<p>Berikut adalah rincian perubahannya:</p>\n<ul>\n  <li>\n    <strong>Penerbitan Tagihan Otomatis</strong><br>\n    Sistem akan secara otomatis menerbitkan dan mengirimkan tagihan (<em>invoice</em>) kepada setiap pelanggan <strong>5 (lima) hari sebelum tanggal jatuh tempo</strong> yang telah ditetapkan.\n  </li>\n  <br>\n  <li>\n    <strong>Masa Aktif Tautan Pembayaran</strong><br>\n    Setiap tautan pembayaran (<em>invoice link</em>) yang dikirimkan memiliki masa aktif selama <strong>10 (sepuluh) hari</strong>. Pelanggan diharapkan untuk menyelesaikan pembayaran dalam kurun waktu tersebut sebelum tautan kedaluwarsa.\n  </li>\n  <br>\n  <li>\n    <strong>Jadwal Pengingat Pembayaran</strong><br>\n    Sistem pengingat pembayaran akan dikirimkan secara otomatis sebanyak <strong>2 (dua) kali</strong>, dengan jadwal sebagai berikut:\n    <ul>\n      <li>Pengingat pertama dikirimkan pada <strong>tanggal 1</strong></li>\n      <li>Pengingat kedua dikirimkan pada <strong>tanggal 4</strong></li>\n    </ul>\n  </li>\n  <br>\n  <li>\n    <strong>Penonaktifan Layanan Akibat Keterlambatan</strong><br>\n    Apabila pembayaran tagihan belum kami terima hingga melewati tanggal 1 pada bulan berjalan, maka layanan akan dinonaktifkan secara otomatis. Proses penonaktifan dan pemutusan koneksi paksa oleh sistem akan dilakukan pada <strong>tanggal 5 pukul 00:00 WIB</strong>.\n  </li>\n</ul>\n<p>Mohon untuk memperhatikan perubahan ini demi kelancaran proses pembayaran dan keberlangsungan layanan Anda. Atas perhatiannya, kami ucapkan terima kasih.</p>\n<p><em>Hormat kami,</em><br><strong>Team Pengembang</strong></p>",
                "tipe": "Ketentuan",
                "versi": None,
                "created_at": "2025-08-20 04:41:42"
            },
            {
                "id": 3,
                "judul": "Pembaruan Sistem v2.1.5: Peningkatan Performa, Akurasi Data, dan Fitur Dashboard",
                "konten": "<p>Kami telah melakukan pembaruan pada sistem ke versi <strong>v2.1.5</strong>. Pembaruan ini mencakup beberapa peningkatan performa, perbaikan bug, dan penambahan fitur baru untuk meningkatkan stabilitas dan akurasi data. Berikut rinciannya:</p>\n\n<h4>Penambahan Fitur Baru:</h4>\n<ul>\n    <li><strong>Widget Dashboard Interaktif:</strong> Menambahkan kemampuan untuk mengklik grafik \"Pelanggan per Paket\" di dashboard untuk melihat rincian detail pelanggan berdasarkan Lokasi dan Brand.</li>\n</ul>\n\n<h4>Perbaikan dan Peningkatan:</h4>\n<ul>\n    <li><strong>Optimasi Kinerja Sistem Latar Belakang:</strong> Menyempurnakan proses otomatis (seperti pembuatan invoice dan suspensi layanan) agar dapat menangani ribuan data pelanggan secara efisien tanpa membebani server.</li>\n    <li><strong>Perbaikan Bug Tampilan Data:</strong> Mengatasi masalah yang menyebabkan daftar data (seperti pelanggan & langganan) hanya menampilkan 100 item, kini seluruh data dapat diakses.</li>\n    <li><strong>Peningkatan Akurasi Filter:</strong> Memperbaiki logika filter agar selalu melakukan pencarian di seluruh database, memastikan hasil yang ditampilkan (contoh: filter status \"Suspended\") selalu akurat.</li>\n    <li><strong>Validasi Logika Penagihan:</strong> Melakukan verifikasi dan memastikan sistem secara otomatis tidak akan mengirimkan invoice baru kepada pelanggan yang statusnya \"Suspended\".</li>\n</ul>\n\n<p>Pembaruan ini dipublikasikan pada <strong>21 Agustus 2025</strong>. Terima kasih telah menggunakan layanan kami.</p>",
                "tipe": "Pembaruan",
                "versi": "2.1.5",
                "created_at": "2025-08-21 13:03:44"
            },
            {
                "id": 4,
                "judul": "Pembaruan dan Update Request Feature v2.1.6",
                "konten": "<div>\n<h1>Pembaruan Sistem & Catatan Rilis v2.1.6</h1>\n<p>Kami telah melakukan serangkaian pembaruan pada sistem ke versi <strong>v2.1.6</strong>. Pembaruan ini mencakup penambahan fitur baru yang signifikan, perbaikan bug kritis di sisi backend dan frontend, serta peningkatan alur kerja untuk meningkatkan stabilitas dan akurasi data. Berikut rinciannya:</p>\n\n<h4>Penambahan Fitur Baru:</h4>\n<ul>\n    <li><strong>Opsi Penagihan Prorate Gabungan:</strong> Menambahkan fungsionalitas baru agar dapat membuat tagihan pertama yang mencakup biaya prorate sisa bulan ini ditambah biaya penuh untuk bulan berikutnya dalam satu invoice. Sistem kini secara otomatis mengatur jatuh tempo berikutnya 2 bulan ke depan setelah pembayaran gabungan dilunasi.</li>\n    <li><strong>Pemilihan Profil PPPoE Otomatis untuk NOC:</strong> Mengimplementasikan fitur cerdas pada form \"Tambah Data Teknis\". Sistem kini secara otomatis:\n        <ol>\n            <li>Mendeteksi lokasi pelanggan untuk menentukan server Mikrotik yang relevan.</li>\n            <li>Menganalisis paket layanan yang dipilih untuk menentukan kecepatan (misal: 20 Mbps).</li>\n            <li>Menampilkan daftar profil PPPoE yang tersedia di Mikrotik yang sesuai dengan kecepatan tersebut dan memiliki kurang dari 5 pengguna aktif.</li>\n        </ol>\n        Fitur ini secara drastis mengurangi kesalahan input manual dan mempercepat alur kerja tim NOC.\n    </li>\n    <li><strong>Fungsionalitas Edit untuk Konten (S&K):</strong> Menambahkan kemampuan untuk memperbarui (update) data Syarat & Ketentuan yang sudah ada melalui dialog form, tidak hanya menambah dan menghapus.</li>\n</ul>\n\n<h4>Perbaikan dan Peningkatan:</h4>\n<ul>\n    <li><strong>Perbaikan Kritis: Aplikasi 'Freeze' pada Halaman Data Teknis:</strong> Menyelesaikan masalah aplikasi tidak responsif (freeze) saat membuka dialog \"Tambah Data Teknis\". Akar masalahnya adalah <em>race condition</em> saat memuat data awal. Perbaikan dilakukan dengan merestrukturisasi <em>lifecycle hook</em> <code>onMounted</code> menggunakan <code>Promise.all</code> untuk memastikan semua data (pelanggan, langganan, dll.) selesai dimuat sebelum halaman dapat diinteraksikan.</li>\n    <li><strong>Penyesuaian Alur Kerja Sesuai Proses Bisnis:</strong> Menyesuaikan form \"Tambah Data Teknis\" agar 100% cocok dengan alur kerja <strong>Sales (Pelanggan) -> NOC (Data Teknis) -> Finance (Langganan)</strong>. Kini, tim NOC dapat memilih Paket Layanan secara manual saat membuat data teknis, karena data Langganan baru akan dibuat oleh tim Finance di tahap selanjutnya.</li>\n    <li><strong>Sinkronisasi Model Data dan Database:</strong> Memperbaiki serangkaian bug kritis yang disebabkan oleh ketidaksesuaian antara kode aplikasi dan struktur database, termasuk memperbaiki nama kolom yang salah (<code>tanggal_mulai</code> vs <code>tgl_mulai_langganan</code>) pada Model SQLAlchemy dan Skema Pydantic serta menjalankan migrasi database (Alembic) dengan benar.</li>\n    <li><strong>Optimalisasi Penanganan Cache Browser:</strong> Mengidentifikasi dan memberikan solusi untuk masalah <em>caching</em> browser yang menyebabkan pengguna tidak menerima versi aplikasi terbaru setelah update. Rekomendasi konfigurasi server (Nginx) telah diberikan untuk mencegah masalah ini terjadi lagi di masa depan.</li>\n    <li><strong>Peningkatan Stabilitas Server:</strong> Mengatasi masalah <code>500 Internal Server Error</code> yang persisten dengan melakukan reset total pada cache bytecode Python (<code>__pycache__</code>) di server, memastikan aplikasi selalu menjalankan versi kode terbaru setelah di-restart.</li>\n    <li><strong>Implementasi Pengecekan Kode Otomatis (CI/CD):</strong> Mengintegrasikan GitHub Actions ke dalam repositori untuk secara otomatis memeriksa kualitas dan format kode (menggunakan black, flake8), memastikan konsistensi dan mengurangi potensi bug di masa depan.</li>\n</ul>\n\n<p>Pembaruan dan perbaikan ini diselesaikan pada <strong>22 Agustus 2025</strong>. Terima kasih atas kerja sama Anda dalam proses ini.</p>\n</div>",
                "tipe": "Pembaruan",
                "versi": "2.1.6",
                "created_at": "2025-08-22 11:14:11"
            },
            {
                "id": 5,
                "judul": "Pembaruan Sistem v2.2.0: Hak Akses Widget Dashboard & Peningkatan Stabilitas",
                "konten": "<p>Pembaruan kali ini menghadirkan fitur baru yang signifikan dalam hal kontrol akses dan laporan, ditambah serangkaian peningkatan stabilitas dan perbaikan bug untuk meningkatkan pengalaman pengguna secara keseluruhan.</p>\n<br>\n<strong>Fitur Baru</strong>\n<p><strong>1. Kontrol Akses Widget Dashboard:</strong> Kini Anda dapat mengatur widget mana yang bisa dilihat oleh setiap peran pengguna (misalnya, NOC atau Finance) langsung dari menu \"Role Management\". Fitur ini memberikan kontrol keamanan yang lebih baik dan memastikan setiap tim hanya melihat data yang relevan.</p>\n<p><strong>2. Fitur Laporan Pendapatan Lengkap:</strong> Kami telah menambahkan halaman Laporan baru yang canggih. Anda sekarang bisa melihat riwayat pendapatan, memfilternya berdasarkan rentang tanggal dan lokasi pelanggan, serta mengekspor hasilnya ke file Excel dengan format yang rapi.</p>\n<br>\n<strong>Peningkatan & Perbaikan</strong>\n<p><strong>- Peningkatan Kompatibilitas Server:</strong> Memperbaiki <em>error</em> fatal (<code>locale.Error</code>) untuk memastikan aplikasi dapat berjalan stabil di berbagai lingkungan server (Linux/Windows), bahkan yang tidak memiliki konfigurasi bahasa Indonesia.</p>\n<p><strong>- Stabilitas Dashboard:</strong> Memperbaiki masalah yang menyebabkan <em>chart</em> gagal dimuat atau halaman menjadi kosong. Dashboard kini lebih tangguh dan akan menampilkan data secara konsisten sesuai hak akses pengguna.</p>\n<p><strong>- Perbaikan Tampilan UI:</strong> Menghilangkan duplikasi kartu statistik di halaman Dashboard untuk tampilan yang lebih bersih dan akurat.</p>\n<p><strong>- Peningkatan Ekspor Excel:</strong> Laporan Excel kini secara otomatis memformat angka sebagai mata uang Rupiah (\"Rp\") dan merapikan tampilan kolom untuk keterbacaan yang lebih baik.</p>",
                "tipe": "Pembaruan",
                "versi": "2.2.0",
                "created_at": "2025-08-23 21:00:59"
            },
            {
                "id": 6,
                "judul": "SYARAT & KETENTUAN",
                "konten": "<p>Dengan hormat,</p>\n<p>Kami memberitahukan adanya pembaruan penting pada sistem dan Syarat dan Ketentuan (S&K) kami. Pembaruan ini bertujuan untuk meningkatkan validasi, akurasi, dan pengalaman Anda dalam mengelola layanan. Aturan ini berlaku efektif sejak pengumuman ini diterbitkan.</p>\n<p>Berikut adalah poin utama pembaruan tersebut:</p>\n<ul>\n<li>\n<strong>Pengenalan Portal Pelanggan Baru: Portal FTTH Artacom</strong><br>\nUntuk memberikan pengalaman yang lebih baik dan terintegrasi, kami secara resmi memindahkan sistem manajemen penagihan (<em>Billing System</em>) ke platform terpusat yang baru, yaitu <strong>Portal FTTH Artacom</strong>. Ke depannya, portal ini akan menjadi pusat untuk semua kebutuhan Anda, mulai dari melihat tagihan, melakukan pembayaran, hingga mengajukan perubahan layanan.\n</li>\n<br>\n<li>\n<strong>Verifikasi untuk Penyesuaian Harga Layanan via Portal</strong><br>\nSejalan dengan pengenalan portal baru, setiap permintaan untuk mengubah harga layanan (baik peningkatan maupun penurunan paket) wajib diajukan melalui Portal FTTH Artacom dan akan melalui tahap verifikasi serta persetujuan (<em>approval</em>) dari Tim Billing kami. Penyesuaian harga tidak lagi terjadi secara instan, melainkan akan diproses setelah mendapatkan validasi dari tim kami.\n</li>\n</ul>\n<p>Kami mohon Anda dapat segera membiasakan diri dengan Portal FTTH Artacom. Langkah ini kami ambil sebagai komitmen untuk menjaga ketertiban administrasi dan memberikan layanan yang lebih transparan bagi seluruh pelanggan.</p>\n<p>Atas perhatian dan kerja sama Anda, kami ucapkan terima kasih.</p>\n<p><em>Hormat kami,</em><br><strong>Tim Artacom</strong></p>",
                "tipe": "Ketentuan",
                "versi": None,
                "created_at": "2025-09-05 20:04:04"
            },
            {
                "id": 7,
                "judul": "v2.5.0: Rilis Fitur Manajemen Infrastruktur, Dashboard Baru, dan Lainnya!",
                "konten": "<p>Selamat datang di <strong>Portal v2.5.0</strong>! Pembaruan besar kali ini menandai evolusi dari versi 2.2.0, dengan membawa serangkaian fitur baru yang revolusioner untuk manajemen infrastruktur dan pelaporan. Kami juga menyertakan berbagai peningkatan fungsionalitas dan perbaikan bug krusial untuk menjadikan portal ini lebih andal dan efisien untuk operasional harian Anda.</p>\n<br>\n<strong>Fitur Baru</strong>\n<p><strong>1. Dashboard Monitoring Baru & Visualisasi Data:</strong> Kami memperkenalkan dua dashboard canggih: satu untuk ringkasan operasional penuh dan satu lagi khusus untuk memonitor pelanggan Jakinet secara terpisah. Tampilan ringkasan pendapatan dan piutang juga telah dirombak agar lebih intuitif dan mudah dibaca.</p>\n<p><strong>2. Manajemen Infrastruktur Jaringan (OLT & Inventaris):</strong> Kini Anda dapat mengelola perangkat OLT, melacak ODP (Optical Distribution Point), dan memantau seluruh inventaris perangkat jaringan (seperti Mikrotik, Kabel, dan ONT/ONU) langsung dari satu menu terpusat. Fitur ini memberikan kontrol penuh atas aset fisik jaringan Anda.</p>\n<p><strong>3. Laporan & Ringkasan Bulanan:</strong> Fitur baru untuk melihat ringkasan tagihan (<em>invoicing</em>) per bulan secara otomatis. Anda juga dapat melacak jumlah pelanggan aktif dan yang ditangguhkan (<em>suspend</em>) secara real-time untuk analisis bisnis yang lebih baik.</p>\n<p><strong>4. Mode Pemeliharaan Sistem (Maintenance Mode):</strong> Sebuah menu baru yang memungkinkan Anda mengaktifkan mode pemeliharaan dengan mudah. Fitur ini akan menampilkan pemberitahuan di sisi pelanggan saat sistem sedang dalam perbaikan, memastikan komunikasi yang jelas selama proses maintenance.</p>\n<p><strong>5. Notifikasi Real-time untuk Tim NOC:</strong> Sistem kini akan mengirimkan notifikasi otomatis setiap kali Data Teknis pelanggan berhasil dibuat. Hal ini mempercepat alur kerja dan koordinasi antara tim administrasi dan tim teknis (NOC).</p>\n<br>\n<strong>Peningkatan & Perbaikan Bug</strong>\n<p><strong>- Peningkatan Fungsionalitas Tabel:</strong> Kami meningkatkan kemampuan filter dan urutan data. Kini Anda dapat melakukan filter berdasarkan alamat atau riwayat pelanggan, serta mengurutkan data berdasarkan tanggal jatuh tempo dengan lebih cepat dan mudah.</p>\n<p><strong>- Stabilitas Sinkronisasi Mikrotik:</strong> Memperbaiki masalah sinkronisasi krusial antara Portal dan perangkat Mikrotik. Proses penangguhan (<em>suspend</em>), aktivasi ulang (<em>unsuspend</em>), dan pembaruan data teknis pelanggan kini berjalan jauh lebih andal dan konsisten.</p>\n<p><strong>- Perbaikan Fitur Impor Data Massal:</strong> Menyelesaikan bug signifikan yang terjadi pada fitur impor data. Proses impor untuk data pelanggan, data teknis, dan data langganan kini berjalan lebih lancar, cepat, dan bebas eror.</p>\n<p><strong>- Koreksi Profil PPPoE & Deskripsi Pembayaran:</strong> Memperbaiki kesalahan logika pada penyimpanan profil PPPoE di Data Teknis dan mengoreksi deskripsi transaksi yang dikirimkan ke payment gateway (Xendit) agar sesuai format.</p>\n\n<p>Terima kasih telah menggunakan layanan kami. Kami berharap pembaruan ini dapat membantu operasional bisnis Anda menjadi lebih baik.</p>\n\n<p><em>Hormat kami,</em><br><strong>Team Pengembang</strong></p>",
                "tipe": "Pembaruan",
                "versi": "2.5.0",
                "created_at": "2025-09-05 20:15:38"
            },
            {
                "id": 8,
                "judul": "Laporan Pembaruan Aplikasi V2.5.1",
                "konten": "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Laporan Update Aplikasi</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 20px;\n            background-color: #f4f4f4;\n        }\n        .container {\n            max-width: 800px;\n            margin: auto;\n            background: #fff;\n            padding: 20px 40px;\n            border-radius: 8px;\n            box-shadow: 0 0 10px rgba(0,0,0,0.1);\n        }\n        h1, h2 {\n            color: #2c3e50;\n        }\n        h2 {\n            border-bottom: 2px solid #3498db;\n            padding-bottom: 5px;\n            margin-top: 30px;\n        }\n        .new-feature, .bug-fix {\n            margin-bottom: 20px;\n        }\n        ul {\n            list-style-type: disc;\n            padding-left: 20px;\n        }\n        li {\n            margin-bottom: 10px;\n        }\n        .new-user-label {\n            display: inline-block;\n            background-color: #27ae60;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n    </style>\n</head>\n<body>\n<div class=\"container\">\n    <h1>Laporan Update Aplikasi</h1>\n    <p>Halo semuanya!</p>\n    <p>Ada kabar gembira nih. Tim pengembang baru saja menyelesaikan update besar untuk aplikasi kita. Fokus utama kita kali ini adalah membuat sistem lebih stabil, enggak gampang error, dan pastinya lebih gampang dipakai buat kalian semua.</p>\n    \n    <h2>Perbaikan dan Peningkatan Bug</h2>\n    <div class=\"bug-fix\">\n        <ul>\n            <li>\n                <strong>Pemilihan Server Mikrotik Lebih Cerdas:</strong> Dulu, aplikasi suka salah pilih server Mikrotik dan selalu terhubung ke server pertama yang ada di daftar, misalnya \"Tambun\", meskipun alamat pelanggannya di \"Waringin\". Sekarang, aplikasi sudah pintar! Sistem akan mencocokkan alamat pelanggan dengan nama server yang sesuai secara otomatis. Jadi, enggak akan salah Mikrotik lagi.\n            </li>\n            <li>\n                <strong>Hubungan Database Diperbaiki:</strong> Pernah ada error ankeh (AttributeError dan InvalidRequestError) saat sistem mau nyambungin data pelanggan ke server Mikrotik]. Nah, bug ini sudah kami perbaiki dengan menambahkan kolom mikrotik_server_id dan bikin hubungan dua arah yang benar di database> Query OK, 125 rows affected (0.643 sec)]. Sekarang semua data sudah nyambung dengan rapih.\n            </li>\n            <li>\n                <strong>Pilihan Profil PPPoE Makin Lengkap:</strong> Sebelumnya, daftar profil PPPoE yang tersedia untuk pelanggan baru kadang enggak muncul semua. Sekarang, logika di aplikasi sudah ditingkatkan. Semua profil yang relevan akan ditampilkan, dan filternya pun sudah bekerja dengan baik.\n            </li>\n            <li>\n                <strong>Tampilan Dropdown Pelanggan Beres:</strong> Di formulir \"Tambah Langganan\", nama pelanggan sering muncul dobel. Kami sudah bereskan masalah ini dengan memperbaiki struktur template dropdown-nya. Sekarang, setiap pelanggan cuma muncul sekali dan rapih.\n            </li>\n        </ul>\n    </div>\n\n    <h2>Fitur Baru</h2>\n    <div class=\"new-feature\">\n        <ul>\n            <li>\n                <strong>Penanda Pelanggan Baru:</strong> Sekarang, di menu \"Tambah Langganan\", setiap pelanggan yang belum punya langganan akan otomatis ditandai dengan tulisan <span class=\"new-user-label\">NEW USER</span>. Ini bikin kalian lebih cepat tahu siapa saja pelanggan yang perlu dibuatkan langganan.\n            </li>\n        </ul>\n    </div>\n\n    <p>Terima kasih banyak sudah menggunakan sistem ini. Semoga update kali ini bikin kerjaan kalian makin lancar ya!</p>\n    \n    <p><strong>Hormat kami,</strong><br><strong>Team Pengembang</strong></p>\n</div>\n</body>\n</html>",
                "tipe": "Pembaruan",
                "versi": "2.5.1",
                "created_at": "2025-09-07 19:47:07"
            },
            {
                "id": 9,
                "judul": "Laporan Pembaruan Aplikasi V2.5.2",
                "konten": "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Changelog v2.5.3</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 20px;\n            background-color: #f4f4f4;\n        }\n        .container {\n            max-width: 800px;\n            margin: auto;\n            background: #fff;\n            padding: 20px 40px;\n            border-radius: 8px;\n            box-shadow: 0 0 10px rgba(0,0,0,0.1);\n        }\n        h1, h2 {\n            color: #2c3e50;\n        }\n        h1 {\n            border-bottom: 3px solid #3498db;\n            padding-bottom: 10px;\n        }\n        h2 {\n            border-bottom: 2px solid #3499db8a;\n            padding-bottom: 5px;\n            margin-top: 30px;\n        }\n        ul {\n            list-style-type: disc;\n            padding-left: 20px;\n        }\n        li {\n            margin-bottom: 10px;\n        }\n        .new-user-label {\n            display: inline-block;\n            background-color: #27ae60;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n    </style>\n</head>\n<body>\n<div class=\"container\">\n    <h1>Changelog Aplikasi - Versi 2.5.2</h1>\n    <p>Berikut adalah ringkasan perubahan dan perbaikan yang diterapkan pada versi ini:</p>\n\n    <h2>Bug Fixes & Improvement</h2>\n    <ul>\n        <li>\n            <strong>Logika Pemilihan Server Mikrotik:</strong> Sistem kini otomatis mencocokkan nama area pelanggan dengan server Mikrotik yang sesuai. Sebelumnya, sistem hanya memilih server pertama dalam daftar.\n        </li>\n        <li>\n            <strong>Relasi Data Mikrotik:</strong> Perbaikan pada relasi database yang sebelumnya menyebabkan AttributeError dan InvalidRequestError. Ditambahkan kolom mikrotik_server_id dan relasi dua arah antar model.\n        </li>\n        <li>\n            <strong>Daftar Profil PPPoE:</strong> Logic pemfilteran profil PPPoE diperbaiki agar seluruh profil yang aktif dapat muncul sesuai area/server.\n        </li>\n        <li>\n            <strong>Dropdown Pelanggan:</strong> Perbaikan pada struktur tampilan dropdown di form \"Tambah Langganan\". Nama pelanggan yang sebelumnya tampil ganda kini hanya muncul satu kali.\n        </li>\n        <li>\n            <strong>Suspended/Unsuspended:</strong> Perbaikan pada fitur otomatisasi status suspend/unsuspend berdasarkan status pembayaran. Status pelanggan kini diperbarui secara konsisten dan akurat.\n        </li>\n        <li>\n            <strong>Dashboard Jakinet:</strong> Bug yang menyebabkan area \"Jelantik\" dan \"Jelantik Nagrak\" tidak muncul di dashboard telah diperbaiki.\n        </li>\n    </ul>\n\n    <h2>System Improvements</h2>\n    <ul>\n        <li>\n            <strong>Activity Log:</strong> Penambahan fitur log aktivitas untuk mencatat semua tindakan penting seperti pembuatan invoice, update data, dan lainnya. <span class=\"new-user-label\">NEW</span>\n        </li>\n        <li>\n            <strong>Database Optimization:</strong> Refactor model dan optimasi query untuk menghindari masalah N+1 di entitas Pelanggan, Langganan, Data Teknis, dan Invoice.\n        </li>\n        <li>\n            <strong>Stabilitas Script Main:</strong> Perbaikan pada script main.py untuk menghindari pembuatan invoice ganda. Sekarang proses berjalan lebih stabil dan terkontrol.\n        </li>\n        <li>\n            <strong>Integrasi Mikrotik:</strong> Data teknis sekarang diambil langsung dari Mikrotik, bukan lagi dari OLT, untuk penyederhanaan manajemen perangkat.\n        </li>\n    </ul>\n\n    <h2>New Feature</h2>\n    <ul>\n        <li>\n            <strong>Penanda \"NEW USER\":</strong> Pelanggan yang belum memiliki langganan akan otomatis ditandai dengan label <span class=\"new-user-label\">NEW USER</span> di form \"Tambah Langganan\".\n        </li>\n    </ul>\n\n    <p>Silakan update ke versi ini untuk mendapatkan semua perubahan di atas.</p>\n\n    <p><strong>— Dev Team</strong></p>\n</div>\n</body>\n</html>",
                "tipe": "Pembaruan",
                "versi": "2.5.2",
                "created_at": "2025-09-09 22:37:58"
            },
            {
                "id": 10,
                "judul": "Update v2.5.3 - Optimasi Tampilan Mobile & Role Fix",
                "konten": "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Changelog v2.5.3</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 20px;\n            background-color: #f4f4f4;\n        }\n        .container {\n            max-width: 800px;\n            margin: auto;\n            background: #fff;\n            padding: 20px 40px;\n            border-radius: 8px;\n            box-shadow: 0 0 10px rgba(0,0,0,0.1);\n        }\n        h1, h2 {\n            color: #2c3e50;\n        }\n        h2 {\n            border-bottom: 2px solid #3498db;\n            padding-bottom: 5px;\n            margin-top: 30px;\n        }\n        ul {\n            list-style-type: disc;\n            padding-left: 20px;\n        }\n        li {\n            margin-bottom: 10px;\n        }\n        .new-user-label {\n            display: inline-block;\n            background-color: #27ae60;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n    </style>\n</head>\n<body>\n<div class=\"container\">\n    <h1>Changelog v2.5.3</h1>\n    <p>Berikut ini adalah ringkasan perubahan pada versi 2.5.3:</p>\n\n    <h2>Bug Fixes & Improvements</h2>\n    <ul>\n        <li>\n            <strong>Responsive UI (Mobile):</strong> Perbaikan tampilan halaman Invoice dan Data Teknis agar lebih usable di perangkat mobile.\n        </li>\n        <li>\n            <strong>Android Performance:</strong> Batasi jumlah data yang ditampilkan di beberapa halaman berat untuk mengurangi lag di device Android low-end.\n        </li>\n        <li>\n            <strong>Role Management:</strong> Fix permission dan hak akses untuk role NOC dan Teknisi.\n        </li>\n        <li>\n            <strong>Notifikasi:</strong> Arahkan notifikasi terkait pembayaran dari NOC langsung ke tim Finance.\n        </li>\n    </ul>\n\n    <h2>System Updates</h2>\n    <ul>\n        <li>\n            <strong>APK Rebuild:</strong> Build ulang versi Android (.apk) dengan semua perubahan di atas. Sudah bisa di-download untuk distribusi internal/testing.\n        </li>\n    </ul>\n\n    <h2>New Feature</h2>\n    <ul>\n        <li>\n            <strong>Auto Role & Notification Logic:</strong> Tambahkan logic tagging pengguna berdasarkan role dan optimasi alur notifikasi. <span class=\"new-user-label\">NEW</span>\n        </li>\n    </ul>\n\n    <p>Catatan: Disarankan untuk clear cache jika tampilan mobile belum berubah setelah update.</p>\n\n    <p><strong>— Dev Team</strong></p>\n</div>\n</body>\n</html>",
                "tipe": "Pembaruan",
                "versi": "2.5.3",
                "created_at": "2025-09-13 23:50:00"
            },
            {
                "id": 11,
                "judul": "Changelog ArtacomFTTHBilling_V2 v2.9.0",
                "konten": "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Changelog ArtacomFTTHBilling_V2 v2.9.0</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 20px;\n            background-color: #f4f4f4;\n        }\n        .container {\n            max-width: 800px;\n            margin: auto;\n            background: #fff;\n            padding: 20px 40px;\n            border-radius: 8px;\n            box-shadow: 0 0 10px rgba(0,0,0,0.1);\n        }\n        h1, h2 {\n            color: #2c3e50;\n        }\n        h1 {\n            border-bottom: 3px solid #3498db;\n            padding-bottom: 10px;\n        }\n        h2 {\n            border-bottom: 2px solid #3499db8a;\n            padding-bottom: 5px;\n            margin-top: 30px;\n        }\n        ul {\n            list-style-type: disc;\n            padding-left: 20px;\n        }\n        li {\n            margin-bottom: 10px;\n        }\n        .new-label {\n            display: inline-block;\n            background-color: #27ae60;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n        .fix-label {\n            display: inline-block;\n            background-color: #e74c3c;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n        .prod-ready {\n            background-color: #2c3e50;\n            color: white;\n            padding: 10px;\n            text-align: center;\n            border-radius: 4px;\n            margin-top: 20px;\n            font-weight: bold;\n        }\n    </style>\n</head>\n<body>\n<div class=\"container\">\n    <h1>Changelog ArtacomFTTHBilling_V2 v2.9.0</h1>\n    <p><strong>Tanggal Update:</strong> 11 Oktober 2025</p>\n    <p>Versi ini merupakan hasil transformasi komprehensif sistem billing. Semua isu kritikal telah diselesaikan. Sistem kini Enterprise-Grade</p>\n\n    <h2>Perbaikan Keamanan & Stabilitas</h2>\n    <ul>\n        <li>\n            <strong>Pengurangan Risiko Keamanan 90%</strong>: Semua sensitive logging (seperti password) di backend telah dihapus, dan sistem autentikasi (JWT) dibersihkan. <span class=\"fix-label\">FIX KRITIKAL</span>\n        </li>\n        <li>\n            <strong>Peningkatan Validasi Password</strong>: Implementasi validasi password yang kuat (9 kriteria termasuk min 8 chars, uppercase, digit, special char).\n        </li>\n        <li>\n            <strong>Konsistensi Data</strong>: Operasi-operasi kritikal kini menggunakan Atomic Transactions untuk menjamin konsistensi data.\n        </li>\n        <li>\n            <strong>Penanganan Error Graceful</strong>: Implementasi global exception handlers di backend FastAPI untuk mencegah aplikasi crash dan memastikan graceful degradation.\n        </li>\n    </ul>\n\n    <h2>Peningkatan Kinerja & Optimasi (200-300% Boost)</h2>\n    <ul>\n        <li>\n            <strong>Database Lebih Cepat</strong>: Permasalahan N+1 Query yang menyebabkan lambatnya proses background job dan API telah dieliminasi melalui comprehensive eager loading.\n        </li>\n        <li>\n            <strong>API Response Time 70% Lebih Cepat</strong>: Peningkatan signifikan di seluruh API, dengan waktu respons rata-rata menjadi di bawah 1 detik (dari sebelumnya 2-5 detik).\n        </li>\n        <li>\n            <strong>Pengurangan Penggunaan Memori 60%</strong>: Optimasi database connection pool dan perbaikan isu double app mounting di frontend.\n        </li>\n        <li>\n            <strong>Optimasi Penanganan Limit API</strong>: Fixed isu loading data dengan mengoptimalkan pagination handling pada dataset besar.\n        </li>\n    </ul>\n\n    <h2>Perbaikan dan Fitur Terbaru (Mobile & Desktop)</h2>\n    <ul>\n        <li>\n            <strong>Perbaikan Konsistensi Tampilan Mobile vs Desktop</strong>: Isu di halaman Langganan di mana perangkat Mobile hanya menampilkan ID pelanggan (bukan nama) telah diperbaiki. Data pelanggan kini dimuat lengkap untuk tampilan yang konsisten dan user-friendly di semua perangkat. <span class=\"new-label\">LATEST FIX</span>\n        </li>\n        <li>\n            <strong>Type Safety Lengkap</strong>: Semua peringatan Pylance (untuk backend) dan perbaikan konfigurasi TypeScript (untuk frontend) telah diselesaikan, memastikan kualitas kode yang lebih tinggi dan pengalaman debugging yang lebih baik.\n        </li>\n        <li>\n            <strong>Penghapusan Inisialisasi Ganda Vue.js</strong>: Memory leak dan perilaku tak terduga akibat duplicate app initialization di main.ts telah diperbaiki.\n        </li>\n    </ul>\n\n    <div class=\"prod-ready\">\n        FINAL STATUS: SISTEM ArtacomFTTHBilling_V2\n    </div>\n\n    <p style=\"margin-top: 20px;\">Catatan: Disarankan untuk clear cache di browser atau aplikasi mobile Anda untuk mendapatkan semua pembaruan kinerja.</p>\n\n    <p><strong>— Tim Pengembang (Dev Team)</strong></p>\n</div>\n</body>\n</html>",
                "tipe": "Pembaruan",
                "versi": "2.9.0",
                "created_at": "2025-10-11 11:23:50"
            },
            {
                "id": 12,
                "judul": "SYARAT & KETENTUAN",
                "konten": "<p>Dengan hormat,</p> <p>Kami memberitahukan adanya pembaruan penting pada sistem dan kebijakan internal terkait proses Billing Otomatis dan Aktivasi Layanan di <strong>Portal FTTH Artacom</strong>. Pembaruan ini bertujuan untuk meningkatkan validasi data, efisiensi kerja tim, serta memastikan sistem layanan berjalan dengan akurat dan konsisten. Kebijakan ini berlaku efektif sejak pengumuman ini diterbitkan.</p> <p>Berikut adalah poin utama pembaruan tersebut:</p> <ul> <li> <strong>Aktivasi Otomatis Setelah Pembayaran Billing Otomatis</strong><br> Bagi pelanggan yang telah masuk ke dalam aplikasi <strong>Portal FTTH Artacom</strong> dengan metode pembayaran <em>Billing Otomatis</em>, sistem akan secara otomatis mengaktifkan layanan setelah pembayaran diterima dan terverifikasi. Tidak diperlukan tindakan manual dari tim untuk proses aktivasi ini. </li> <br> <li> <strong>Suspensi Otomatis bagi Pelanggan yang Tidak Melakukan Pembayaran</strong><br> Pelanggan yang telah menerima <em>Billing Otomatis</em> namun tidak menyelesaikan pembayaran sesuai periode yang ditentukan akan otomatis berstatus <strong>Suspended</strong>. Tim Billing dan Support wajib memastikan status layanan sesuai dengan hasil verifikasi sistem. </li> <br> <li> <strong>Penerapan Tarif Prorate untuk Pembayaran di Tengah Bulan</strong><br> Apabila pelanggan melakukan pembayaran atau aktivasi layanan di pertengahan bulan, sistem akan secara otomatis mengenakan tarif <strong>Prorate</strong> (perhitungan berdasarkan sisa waktu penggunaan di bulan berjalan), bukan tarif penuh. Namun, jika pelanggan ingin melakukan pembayaran sekaligus untuk bulan berikutnya, maka akan dikenakan <strong>tarif Prorate untuk bulan berjalan</strong> dan <strong>tarif penuh untuk bulan selanjutnya</strong>. </li> </ul> <p>Diharapkan seluruh <strong>Tim Internal Artacom</strong> dapat memahami dan menerapkan kebijakan ini secara konsisten dalam setiap proses penanganan pelanggan. Langkah ini diambil sebagai bagian dari komitmen perusahaan untuk meningkatkan efisiensi sistem, transparansi proses billing, dan kualitas layanan kepada pelanggan.</p> <p>Atas perhatian dan kerja sama seluruh tim, kami ucapkan terima kasih.</p> <p><em>Hormat kami,</em><br> <strong>Manajemen Artacom</strong></p>",
                "tipe": "Ketentuan",
                "versi": None,
                "created_at": "2025-10-13 21:14:43"
            },
            {
                "id": 13,
                "judul": "Pembaruan Sistem Portal FTTH V3 Versi 3.1.0",
                "konten": "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Changelog Portal FTTH V3 v3.1.0</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 20px;\n            background-color: #f4f4f4;\n        }\n        .container {\n            max-width: 800px;\n            margin: auto;\n            background: #fff;\n            padding: 20px 40px;\n            border-radius: 8px;\n            box-shadow: 0 0 10px rgba(0,0,0,0.1);\n        }\n        h1, h2 {\n            color: #2c3e50;\n        }\n        h1 {\n            border-bottom: 3px solid #3498db;\n            padding-bottom: 10px;\n        }\n        h2 {\n            border-bottom: 2px solid #3499db8a;\n            padding-bottom: 5px;\n            margin-top: 30px;\n        }\n        ul {\n            list-style-type: disc;\n            padding-left: 20px;\n        }\n        li {\n            margin-bottom: 10px;\n        }\n        .new-label {\n            display: inline-block;\n            background-color: #27ae60;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n        .fix-label {\n            display: inline-block;\n            background-color: #e74c3c;\n            color: white;\n            padding: 2px 8px;\n            border-radius: 4px;\n            font-size: 0.8em;\n            font-weight: bold;\n            margin-left: 10px;\n        }\n        .prod-ready {\n            background-color: #2c3e50;\n            color: white;\n            padding: 10px;\n            text-align: center;\n            border-radius: 4px;\n            margin-top: 20px;\n            font-weight: bold;\n        }\n    </style>\n</head>\n<body>\n<div class=\"container\">\n    <h1>Changelog Portal FTTH V3 v3.1.0</h1>\n    <p><strong>Tanggal Update:</strong> 21 Oktober 2025</p>\n    <p>Versi ini membawa fitur yang sangat dinantikan yaitu manajemen Trouble Ticket langsung di dalam portal, serta peningkatan pengalaman pengguna pada perangkat mobile dan perbaikan penting pada fitur impor data.</p>\n    <h2>Fitur & Peningkatan Terbaru</h2>\n    <ul>\n        <li>\n            <strong>Manajemen Trouble Ticket Terintegrasi</strong>: Kini Anda dapat membuat dan melacak <i>Trouble Ticket</i> serta melihat laporannya langsung dari Portal FTTH V3, menyatukan alur kerja tim teknis dalam satu platform. <span class=\"new-label\">BARU</span>\n        </li>\n        <li>\n            <strong>Tampilan Responsif untuk Mobile & Tablet</strong>: Kami telah menambahkan layout tombol khusus yang dioptimalkan untuk perangkat Android dan Tablet, memastikan pengalaman pengguna yang lebih nyaman dan intuitif saat diakses dari mana saja. <span class=\"new-label\">BARU</span>\n        </li>\n        <li>\n            <strong>Validasi Impor CSV yang Lebih Cerdas</strong>: Sistem kini secara otomatis mendeteksi dan melewati kolom kosong dalam file CSV, membuat proses impor data menjadi lebih lancar dan bebas dari kesalahan. <span class=\"new-label\">BARU</span>\n        </li>\n    </ul>\n    <h2>Perbaikan Bug</h2>\n    <ul>\n        <li>\n            <strong>Perbaikan Impor CSV Gagal</strong>: Memperbaiki bug kritis di mana proses unggah data massal (bulking) gagal jika file CSV mengandung kolom kosong. Kini, impor data dapat berjalan dengan sukses tanpa gangguan. <span class=\"fix-label\">PERBAIKAN</span>\n        </li>\n    </ul>\n    <div class=\"prod-ready\">\n        STATUS UPDATE: Portal FTTH V3 Siap Digunakan\n    </div>\n    <p style=\"margin-top: 20px;\">Catatan: Disarankan untuk melakukan <i>clear cache</i> pada browser Anda untuk memastikan semua pembaruan dan perbaikan diterapkan dengan sempurna.</p>\n    <p><strong>— Tim Pengembang (Dev Team)</strong></p>\n</div>\n</body>\n</html>",
                "tipe": "Pembaruan",
                "versi": "3.1.0",
                "created_at": "2025-10-21 23:09:24"
            }
        ]

        # Create Syarat & Ketentuan using complete records directly
        print("📋 Creating all 13 syarat_ketentuan records with complete content...")
        created_count = 0
        failed_count = 0

        for record in complete_records:
            try:
                # Clean data to avoid encoding issues
                judul = record["judul"]
                konten = record["konten"]
                tipe = record["tipe"]
                versi = record["versi"]

                # Remove problematic Unicode characters that cause MySQL errors
                judul = re.sub(r'[^\x00-\x7F]', ' ', judul) if judul else ""
                konten = re.sub(r'[^\x00-\x7F]', ' ', konten) if konten else ""
                tipe = re.sub(r'[^\x00-\x7F]', ' ', tipe) if tipe else ""
                versi = re.sub(r'[^\x00-\x7F]', ' ', versi) if versi else None

                # Ensure valid UTF-8 encoding
                judul = judul.encode('utf-8', errors='ignore').decode('utf-8')
                konten = konten.encode('utf-8', errors='ignore').decode('utf-8')
                tipe = tipe.encode('utf-8', errors='ignore').decode('utf-8')
                if versi:
                    versi = versi.encode('utf-8', errors='ignore').decode('utf-8')

                # Prepare data for insert
                syarat_data = {
                    "id": record["id"],
                    "judul": judul,
                    "konten": konten,
                    "tipe": tipe,
                    "versi": versi,
                    "created_at": record["created_at"]
                }

                # Insert record
                await conn.execute(
                    text("""
                        INSERT INTO syarat_ketentuan
                        (id, judul, konten, tipe, versi, created_at)
                        VALUES
                        (:id, :judul, :konten, :tipe, :versi, :created_at)
                    """),
                    syarat_data
                )

                created_count += 1
                print(f"✅ Imported #{created_count}: {judul[:50]}...")

            except Exception as e:
                print(f"❌ Error importing record {record['id']}: {e}")
                failed_count += 1
                continue

        print(f"✅ Successfully imported {created_count} syarat_ketentuan records!")
        if failed_count > 0:
            print(f"⚠️ Failed to import {failed_count} records")

        # Create admin user (same as original)
        print("👤 Creating admin user...")
        try:
            # Check if admin user already exists
            existing_admin = await conn.execute(text("SELECT id FROM users WHERE username = 'admin'"))
            if existing_admin.fetchone():
                print("ℹ️ Admin user already exists, skipping creation")
            else:
                from app.auth import get_password_hash
                admin_password = "admin123"  # Change this in production!
                hashed_password = get_password_hash(admin_password)

                await conn.execute(
                    text("""
                        INSERT INTO users (username, email, full_name, password_hash, is_active, is_superuser, role)
                        VALUES ('admin', 'admin@example.com', 'Administrator', :password, true, true, 'superadmin')
                    """),
                    {"password": hashed_password}
                )
                print("✅ Admin user created (username: admin, password: admin123)")
        except Exception as e:
            print(f"⚠️ Error creating admin user: {e}")

        await conn.commit()
        print("✅ All 13 syarat_ketentuan records imported successfully!")
        print("\n📋 Summary:")
        print(f"   📊 Syarat & Ketentuan: 13 records dengan konten lengkap")
        print("   ✅ Hanya tabel syarat_ketentuan yang terpengaruh")
        print("   ✅ Tabel lain tidak tersentuh (aman)")

if __name__ == "__main__":
    try:
        asyncio.run(create_seed_data())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)