# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List

load_dotenv()


class Settings(BaseSettings):
    # Variabel MENUS yang sudah ada
    MENUS: List[str] = [
        "Pelanggan",
        "Langganan",
        "Data Teknis",
        "Brand & Paket",
        "Invoices",
        "Laporan Pendapatan",
        "Mikrotik Servers",
        "Users",
        "Roles",
        "Permissions",
        "S&K",
        "Simulasi Harga",
        "Kelola S&K",
        "Manajemen Inventaris", 
        "Dashboard Jakinet",
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

        #Dashboard Pelanggan Widget
        "pelanggan_statistik_utama",
        "pelanggan_pendapatan_jakinet",
        "pelanggan_distribusi_chart",
        "pelanggan_pertumbuhan_chart",
        "pelanggan_status_overview_chart",
        "pelanggan_metrik_cepat",
        "pelanggan_tren_pendapatan_chart"
    ]
    # ---------------------

    DATABASE_URL: str
    XENDIT_CALLBACK_TOKEN_ARTACOMINDO: str
    XENDIT_CALLBACK_TOKEN_JELANTIK: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    XENDIT_API_KEY_JAKINET: str
    XENDIT_API_KEY_JELANTIK: str
    XENDIT_API_URL: str = "https://api.xendit.co/v2/invoices"

    ENCRYPTION_KEY: str

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
        env_file = ".env"


settings = Settings()
