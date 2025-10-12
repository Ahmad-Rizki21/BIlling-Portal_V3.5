# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List

# Get the absolute path to the project root
# This makes the .env file path robust regardless of where the app is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")

# Force override to ensure .env file takes precedence over system variables
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)


class Settings(BaseSettings):
    # Variabel MENUS yang sudah ada
    MENUS: List[str] = [
        "Dashboard",
        "Pelanggan",
        "Langganan",
        "Data Teknis",
        "Brand & Paket",
        "Invoices",
        "Reports Revenue",
        "Mikrotik Servers",
        "Users",
        "Roles",
        "Permissions",
        "S&K",
        "Simulasi Harga",
        "Kelola S&K",  # Tetap
        "inventory",  # Ubah "Manajemen Inventaris" menjadi "inventory"
        "Dashboard Pelanggan",
        "Activity Log",
        "olt",
        "odp_management",
    ]

    # --- TAMBAHKAN INI ---
    # Daftar widget yang ada di dashboard Anda
    DASHBOARD_WIDGETS: List[str] = [
        "pendapatan_bulanan",
        "statistik_pelanggan",
        "statistik_server",
        "pelanggan_per_lokasi",
        "pelanggan_per_paket",
        "tren_pertumbuhan",
        "invoice_bulanan",
        "status_langganan",
        "alamat_aktif",
        # Dashboard Pelanggan Widget
        "pelanggan_statistik_utama",
        "pelanggan_pendapatan_jakinet",
        "pelanggan_distribusi_chart",
        "pelanggan_pertumbuhan_chart",
        "pelanggan_status_overview_chart",
        "pelanggan_metrik_cepat",
        "pelanggan_tren_pendapatan_chart",
    ]
    # ---------------------

    DATABASE_URL: str = "sqlite:///./billing.db"
    XENDIT_CALLBACK_TOKEN_ARTACOMINDO: str = "default_callback_token_artacom"
    XENDIT_CALLBACK_TOKEN_JELANTIK: str = "default_callback_token_jelantik"
    SECRET_KEY: str = "default_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    XENDIT_API_KEY_JAKINET: str = "default_api_key_jakinet"
    XENDIT_API_KEY_JELANTIK: str = "default_api_key_jelantik"
    XENDIT_API_URL: str = "https://api.xendit.co/v2/invoices"

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
