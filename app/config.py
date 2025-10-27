# ====================================================================
# KONFIGURASI SISTEM BILLING FTTH
# ====================================================================
# File ini mengatur semua konfigurasi sistem aplikasi billing.
# Menggunakan Pydantic untuk validasi otomatis dan environment variables.
#
# Environment variables diambil dari file .env di root project.
# Pastikan file .env sudah ada dan dikonfigurasi dengan benar!
# ====================================================================

import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Cari path absolut ke root project
# Ini biar path .env file selalu ketemu mau dari mana aplikasi dijalanin
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")

# Load .env file dan override system variables
# Ini memastikan setting di .env lebih prioritas daripada environment system
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)


class Settings(BaseSettings):
    """
    Kelas utama konfigurasi sistem menggunakan Pydantic BaseSettings.
    Semua variabel di sini otomatis dibaca dari environment variables
# atau .env file. Ada validasi otomatis juga!
    """

    # ====================================================================
    # KONFIGURASI MENU & WIDGET
    # ====================================================================

    # Daftar menu yang ada di sidebar aplikasi
    # Urutan menu ini akan muncul di frontend
    MENUS: List[str] = [
        "Dashboard",                # Halaman utama admin
        "Pelanggan",               # Manajemen data pelanggan
        "Langganan",               # Manajemen langganan aktif
        "Data Teknis",             # Data teknis koneksi internet
        "Brand & Paket",           # Manajemen provider dan paket
        "Invoices",                # Manajemen tagihan/invoice
        "Reports Revenue",         # Laporan pendapatan
        "Mikrotik Servers",        # Konfigurasi server Mikrotik
        "Users",                   # Manajemen pengguna
        "Roles",                   # Manajemen role/hak akses
        "Permissions",             # Manajemen permission detail
        "S&K",                     # Syarat & Ketentuan
        "Simulasi Harga",          # Kalkulator biaya
        "Kelola S&K",             # Form edit S&K
        "inventory",               # Manajemen inventory (rename dari "Manajemen Inventaris")
        "Dashboard Pelanggan",     # Dashboard khusus pelanggan
        "Activity Log",            # Log aktivitas sistem
        "olt",                     # Manajemen OLT (Optical Line Terminal)
        "odp_management",          # Manajemen ODP (Optical Distribution Point)
        "Trouble Tickets",         # Sistem tiket trouble
    ]

    # Daftar widget yang ada di dashboard admin dan pelanggan
    # Widget-widget ini mengatur komponen apa saja yang muncul di dashboard
    DASHBOARD_WIDGETS: List[str] = [
        # Widget Dashboard Admin
        "pendapatan_bulanan",                        # Grafik pendapatan per bulan
        "statistik_pelanggan",                       # Statistik total pelanggan
        "statistik_server",                          # Status server Mikrotik
        "pelanggan_per_lokasi",                      # Peta sebaran pelanggan per lokasi
        "pelanggan_per_paket",                       # Grafik pelanggan per paket layanan
        "tren_pertumbuhan",                          # Grafik tren pertumbuhan pelanggan
        "invoice_bulanan",                           # Statistik invoice bulanan
        "status_langganan",                          # Grafik status langganan (aktif/non-aktif)
        "alamat_aktif",                              # Daftar alamat yang aktif

        # Widget Dashboard Pelanggan
        "pelanggan_statistik_utama",                 # Statistik utama pelanggan
        "pelanggan_pendapatan_jakinet",              # Pendapatan dari pelanggan Jakinet
        "pelanggan_distribusi_chart",                # Grafik distribusi pelanggan
        "pelanggan_pertumbuhan_chart",               # Grafik pertumbuhan pelanggan
        "pelanggan_status_overview_chart",           # Overview status pelanggan
        "pelanggan_metrik_cepat",                    # Metrik kecepatan internet
        "pelanggan_tren_pendapatan_chart",           # Tren pendapatan pelanggan
    ]

    # Fitur-fitur sistem yang memerlukan permission khusus
    # User harus punya permission yang sesuai untuk akses fitur ini
    SYSTEM_FEATURES: List[str] = [
        "settings",    # Akses ke pengaturan sistem
        "uploads",     # Akses ke upload file
        "traffic_monitoring",  # Akses ke traffic monitoring dashboard
    ]

    # ====================================================================
    # KONFIGURASI DATABASE & SECRET KEY
    # ====================================================================

    # Koneksi database - pastikan sesuai dengan environment kamu
    DATABASE_URL: str = "sqlite:///./billing.db"

    # Token callback dari Xendit buat webhook validation
    # SATU token per brand/company
    XENDIT_CALLBACK_TOKEN_ARTACOMINDO: str = "default_callback_token_artacom"
    XENDIT_CALLBACK_TOKEN_JELANTIK: str = "default_callback_token_jelantik"

    # Secret key buat JWT token encryption
    # HARUS DIUBAH DI PRODUCTION! Pakai string yang panjang dan random
    SECRET_KEY: str = "default_secret_key_change_in_production"

    # Algoritma encryption buat JWT
    ALGORITHM: str = "HS256"

    # Token expire time dalam menit (2 jam = 120 menit)
    # Ini mengurangi frequency refresh token biar lebih efisien
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # ====================================================================
    # KONFIGURASI XENDIT PAYMENT GATEWAY
    # ====================================================================

    # API keys dari Xendit untuk masing-masing brand
    # Dapatkan dari dashboard Xendit kamu
    XENDIT_API_KEY_JAKINET: str = "default_api_key_jakinet"
    XENDIT_API_KEY_JELANTIK: str = "default_api_key_jelantik"

    # URL endpoint API Xendit buat create invoice
    XENDIT_API_URL: str = "https://api.xendit.co/v2/invoices"

    # ====================================================================
    # KONFIGURASI ENCRYPTION
    # ====================================================================

    # Key buat enkripsi data sensitif di database (password, dll)
    # HARUS DIUBAH DI PRODUCTION! Pakai Fernet key yang valid
    ENCRYPTION_KEY: str = "default_encryption_key_change_in_production"

    @property
    def XENDIT_API_KEYS(self) -> dict:
        return {
            "JAKINET": self.XENDIT_API_KEY_JAKINET,
            "JELANTIK": self.XENDIT_API_KEY_JELANTIK,
        }

    @property
    def XENDIT_CALLBACK_TOKENS(self) -> dict:
        return {
            "ARTACOMINDO": self.XENDIT_CALLBACK_TOKEN_ARTACOMINDO,
            "JELANTIK": self.XENDIT_CALLBACK_TOKEN_JELANTIK,
        }

    class Config:
        # Be explicit about the .env file path and encoding
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
