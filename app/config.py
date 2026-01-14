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
    # CATATAN: Nama menu ini akan di-convert ke snake_case untuk permission names
    # Contoh: "Dashboard" -> create_dashboard, view_dashboard, edit_dashboard, delete_dashboard
    MENUS: List[str] = [
        "Dashboard",                # Halaman utama admin
        "Pelanggan",               # Manajemen data pelanggan
        "Langganan",               # Manajemen langganan aktif
        "Teknis",                  # Data teknis koneksi internet (sebelumnya "Data Teknis")
        "Paket",                   # Manajemen provider dan paket (sebelumnya "Brand & Paket")
        "Invoices",                # Manajemen tagihan/invoice
        "Reports",                 # Laporan pendapatan (sebelumnya "Reports Revenue")
        "Analytics",               # AI-powered analytics untuk insight bisnis
        "Servers",                 # Konfigurasi server Mikrotik (sebelumnya "Mikrotik Servers")
        "Users",                   # Manajemen pengguna
        "Roles",                   # Manajemen role/hak akses
        "Permissions",             # Manajemen permission detail
        "SK",                      # Syarat & Ketentuan (gabungan "S&K" dan "Kelola S&K")
        "Simulasi",                # Kalkulator biaya (sebelumnya "Simulasi Harga")
        "Inventory",               # Manajemen inventory
        "Dashboard_Pelanggan",     # Dashboard khusus pelanggan
        "Activity_Log",            # Log aktivitas sistem
        "OLT",                     # Manajemen OLT (Optical Line Terminal)
        "ODP",                     # Manajemen ODP (sebelumnya "odp_management")
        "Trouble_Tickets",         # Sistem tiket trouble
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
        "invoice_generation_monitor",                # Monitoring generate invoice otomatis
        "future_invoice_projection",                 # Proyeksi invoice untuk tanggal spesifik

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

    # Permissions untuk widget-dashboard
    # Format: "widget_name": ["role1", "role2", ...]
    # Roles yang tersedia: superadmin, admin, manager, staff, viewer
    DASHBOARD_WIDGET_PERMISSIONS: dict = {
        # Widget Financial (High restriction)
        "pendapatan_bulanan": ["superadmin", "admin", "manager"],
        "invoice_bulanan": ["superadmin", "admin", "manager"],

        # Widget Monitoring (High restriction)
        "invoice_generation_monitor": ["superadmin", "admin", "manager"],
        "future_invoice_projection": ["superadmin", "admin", "manager"],

        # Widget Server/System (High restriction)
        "statistik_server": ["superadmin", "admin"],

        # Widget Analytics (Medium restriction)
        "statistik_pelanggan": ["superadmin", "admin", "manager", "staff"],
        "pelanggan_per_lokasi": ["superadmin", "admin", "manager", "staff"],
        "pelanggan_per_paket": ["superadmin", "admin", "manager", "staff"],
        "tren_pertumbuhan": ["superadmin", "admin", "manager"],
        "status_langganan": ["superadmin", "admin", "manager", "staff"],
        "alamat_aktif": ["superadmin", "admin", "manager", "staff"],

        # Widget Pelanggan (Lower restriction)
        "pelanggan_statistik_utama": ["superadmin", "admin", "manager", "staff", "viewer"],
        "pelanggan_pendapatan_jakinet": ["superadmin", "admin", "manager", "staff"],
        "pelanggan_distribusi_chart": ["superadmin", "admin", "manager", "staff", "viewer"],
        "pelanggan_pertumbuhan_chart": ["superadmin", "admin", "manager", "staff", "viewer"],
        "pelanggan_status_overview_chart": ["superadmin", "admin", "manager", "staff", "viewer"],
        "pelanggan_metrik_cepat": ["superadmin", "admin", "manager", "staff"],
        "pelanggan_tren_pendapatan_chart": ["superadmin", "admin", "manager", "staff"],
    }

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
    #
    # Brand & Account Configuration:
    # - ajn-01 (JAKINET) -> JAKINET API key (ARTACOMINDO account di Xendit)
    # - ajn-02 (JELANTIK) -> JELANTIK API key (murni JELANTIK account)
    # - ajn-03 (JELANTIK NAGRAK) -> JAKINET API key (pesan masuk ke Jakinet/ARTACOMINDO)
    XENDIT_API_KEY_JAKINET: str = "xnd_development_sUcGnffFboAxjvHU1zhbNFrqkFm6vb11kQCinNq8069epNtrT3xWownlvwN9Lam0"  # ARTACOMINDO account
    XENDIT_API_KEY_JELANTIK: str = "xnd_development_RJWrICPkupWykS3MGtbTL9xvuiT1SV6SASPkX1KSBN1dCzE69hr4F8brdITg84"  # JELANTIK account

    # URL endpoint API Xendit buat create invoice
    XENDIT_API_URL: str = "https://api.xendit.co/v2/invoices"

    # ====================================================================
    # KONFIGURASI ENCRYPTION
    # ====================================================================

    # Key buat enkripsi data sensitif di database (password, dll)
    # HARUS DIUBAH DI PRODUCTION! Pakai Fernet key yang valid
    ENCRYPTION_KEY: str = "default_encryption_key_change_in_production"

    # ====================================================================
    # KONFIGURASI AI ANALYTICS (GROQ)
    # ====================================================================

    # API Key dari Groq untuk AI Analytics
    # Dapatkan dari https://console.groq.com/keys
    # Simpan di environment variable: GROQ_API_KEY=gsk_...
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Base URL untuk Groq API (OpenAI compatible)
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Model yang digunakan untuk analisis
    # llama-3.3-70b-versatile: Model terbaru Llama 3.3 70B (Gratis & Cepat)
    # llama-3.1-70b-versatile: Llama 3.1 70B (Gratis)
    # mixtral-8x7b-32768: Mixtral 8x7B (Gratis)
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Cache TTL untuk AI responses (dalam detik)
    # Default: 1 jam (3600 detik)
    ANALYTICS_CACHE_TTL: int = 3600

    # Rate limiting untuk AI requests
    # Maximum requests per minute per user
    ANALYTICS_RATE_LIMIT: int = 10

    @property
    def XENDIT_API_KEYS(self) -> dict:
        return {
            "JAKINET": self.XENDIT_API_KEY_JAKINET,        # ARTACOMINDO account (ajn-01, ajn-03)
            "JELANTIK": self.XENDIT_API_KEY_JELANTIK,      # JELANTIK account (ajn-02)
            # Support keys untuk brand code yang ada di database
            "ajn-01": self.XENDIT_API_KEY_JAKINET,         # JAKINET -> ARTACOMINDO account
            "ajn-02": self.XENDIT_API_KEY_JELANTIK,        # JELANTIK -> JELANTIK account
            "ajn-03": self.XENDIT_API_KEY_JAKINET,         # JELANTIK NAGRAK -> ARTACOMINDO account
        }

    @property
    def XENDIT_CALLBACK_TOKENS(self) -> dict:
        return {
            "ARTACOMINDO": self.XENDIT_CALLBACK_TOKEN_ARTACOMINDO,
            "JELANTIK": self.XENDIT_CALLBACK_TOKEN_JELANTIK,
        }

    def can_access_widget(self, widget_name: str, user_role: str) -> bool:
        """
        Check if user can access specific widget based on their role
        """
        # Convert role to lowercase for case-insensitive comparison
        user_role = user_role.lower()

        # Check widget-specific permissions
        if widget_name in self.DASHBOARD_WIDGET_PERMISSIONS:
            allowed_roles = self.DASHBOARD_WIDGET_PERMISSIONS[widget_name]
            return user_role in [role.lower() for role in allowed_roles]

        # Default: only admins and above can access if widget not in permissions
        return user_role in ["superadmin", "admin"]

    def get_user_widgets(self, user_role: str) -> List[str]:
        """
        Get list of widgets user can access based on their role
        """
        user_role = user_role.lower()
        accessible_widgets = []

        for widget_name in self.DASHBOARD_WIDGETS:
            if self.can_access_widget(widget_name, user_role):
                accessible_widgets.append(widget_name)

        return accessible_widgets

    class Config:
        # Be explicit about the .env file path and encoding
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
