# app/services/mikrotik_service.py

import routeros_api
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime

# Impor model yang dibutuhkan
from ..models.langganan import Langganan as LanggananModel
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..models.data_teknis import DataTeknis as DataTeknisModel

# Setup logger
logger = logging.getLogger(__name__)


def get_api_connection(server_info: MikrotikServerModel):
    """Membuka koneksi API ke server Mikrotik."""
    try:
        connection = routeros_api.RouterOsApiPool(
            server_info.host_ip,
            username=server_info.username,
            password=server_info.password,
            port=int(server_info.port),  # Pastikan port adalah integer
            plaintext_login=True,
        )
        api = connection.get_api()
        logger.info(f"Berhasil terhubung ke Mikrotik {server_info.name}")
        return api, connection
    except Exception as e:
        logger.error(f"Gagal terhubung ke Mikrotik {server_info.name}: {e}")
        return None, None


def update_pppoe_secret(
    api, old_id_pelanggan: str, data_teknis: DataTeknisModel, new_status: str
):
    """
    Mengubah status dan detail PPPoE secret di Mikrotik.
    Mencari berdasarkan NAMA LAMA, dan mengupdate semua data baru.
    """
    try:
        ppp_secrets = api.get_resource("/ppp/secret")

        # 1. Cari user berdasarkan 'name' LAMA
        target_secret = ppp_secrets.get(name=old_id_pelanggan)

        if not target_secret:
            logger.warning(
                f"PPPoE secret untuk nama lama '{old_id_pelanggan}' tidak ditemukan di Mikrotik. Mencoba mencari dengan nama baru '{data_teknis.id_pelanggan}'."
            )
            # Coba cari dengan nama baru sebagai fallback (jika nama tidak diubah)
            target_secret = ppp_secrets.get(name=data_teknis.id_pelanggan)
            if not target_secret:
                logger.error(
                    f"PPPoE secret '{data_teknis.id_pelanggan}' tetap tidak ditemukan. Update dibatalkan."
                )
                return

        # 2. Ambil ID internal dari secret yang ditemukan
        secret_id = target_secret[0]["id"]

        # 3. Siapkan payload data baru untuk diupdate
        update_payload = {
            "id": secret_id,
            "name": data_teknis.id_pelanggan,  # Nama baru
            "password": data_teknis.password_pppoe,  # Password baru
            "remote-address": data_teknis.ip_pelanggan,  # IP baru
        }

        # 4. Atur profile dan status 'disabled' berdasarkan status langganan
        if new_status == "Aktif":
            update_payload["profile"] = data_teknis.profile_pppoe
            update_payload["disabled"] = "no"
            logger.info(
                f"Mengaktifkan '{old_id_pelanggan}' -> '{data_teknis.id_pelanggan}', profil: '{data_teknis.profile_pppoe}'"
            )
        elif new_status == "Suspended":
            update_payload["profile"] = "SUSPENDED"
            update_payload["disabled"] = "yes"
            logger.info(
                f"Menonaktifkan '{old_id_pelanggan}' -> '{data_teknis.id_pelanggan}', profil: 'SUSPENDED'"
            )

        # 5. Kirim perintah .set() dengan semua data baru
        ppp_secrets.set(**update_payload)

        logger.info(f"Update PPPoE secret untuk '{data_teknis.id_pelanggan}' berhasil.")

    except Exception as e:
        logger.error(f"Terjadi error saat update PPPoE secret: {e}")
        raise e


def remove_active_connection(api, id_pelanggan: str):
    """Mencari dan menghapus koneksi PPPoE yang sedang aktif."""
    try:
        ppp_active = api.get_resource("/ppp/active")
        active_connections = ppp_active.get(name=id_pelanggan)

        if active_connections:
            connection_id = active_connections[0]["id"]
            ppp_active.remove(id=connection_id)
            logger.info(f"Berhasil menghapus koneksi aktif untuk '{id_pelanggan}'.")
        else:
            logger.info(
                f"Tidak ada koneksi aktif yang ditemukan untuk '{id_pelanggan}'."
            )
    except Exception as e:
        logger.error(f"Gagal menghapus koneksi aktif untuk '{id_pelanggan}': {e}")
        # Tidak perlu 'raise e' agar proses suspend utama tidak gagal total
        # jika hanya gagal menghapus koneksi aktif.


async def trigger_mikrotik_update(
    db: AsyncSession,
    langganan: LanggananModel,
    data_teknis: DataTeknisModel,
    old_id_pelanggan: str,
):
    """Fungsi utama yang dipanggil dari router atau job untuk trigger update ke Mikrotik."""
    if not hasattr(langganan, "pelanggan"):
        logger.error(
            f"Gagal trigger Mikrotik: Relasi 'pelanggan' tidak di-load untuk langganan ID {langganan.id}"
        )
        return

    if not data_teknis or not data_teknis.id_pelanggan:
        logger.warning(f"Data teknis atau id_pelanggan tidak valid. Skip update.")
        return

    server_id = data_teknis.mikrotik_server_id
    if not server_id:
        logger.error(
            f"mikrotik_server_id tidak di-set untuk data teknis ID {data_teknis.id}. Skip."
        )
        return

    mikrotik_server_info = await db.get(MikrotikServerModel, server_id)

    if not mikrotik_server_info:
        logger.error(
            f"Server Mikrotik dengan ID {server_id} tidak ditemukan di database."
        )
        return

    api, connection = get_api_connection(mikrotik_server_info)
    if not api:
        return

    try:
        # Panggil fungsi update yang sudah diperbaiki dengan argumen baru
        update_pppoe_secret(api, old_id_pelanggan, data_teknis, langganan.status)

        if langganan.status == "Suspended":
            # Saat suspend, hapus koneksi aktif dengan NAMA BARU
            remove_active_connection(api, data_teknis.id_pelanggan)

    finally:
        if connection:
            logger.info("Menutup koneksi Mikrotik.")
            connection.disconnect()


def check_ip_in_secrets(api, ip_address: str) -> str | None:
    """
    Memeriksa apakah sebuah IP sudah digunakan sebagai 'remote-address' di PPP secrets.
    Mengembalikan nama secret jika ditemukan, jika tidak None.
    """
    try:
        ppp_secrets = api.get_resource("/ppp/secret")
        # Query Mikrotik untuk mencari secret dengan remote-address yang cocok
        existing_secret = ppp_secrets.get(remote_address=ip_address)

        if existing_secret:
            # Jika ditemukan, kembalikan nama (ID Pelanggan) dari secret tersebut
            owner_name = existing_secret[0].get("name", "N/A")
            logger.info(
                f"IP {ip_address} ditemukan di Mikrotik, digunakan oleh secret: {owner_name}"
            )
            return owner_name

        return None
    except Exception as e:
        logger.error(f"Gagal memeriksa IP di Mikrotik: {e}")
        # Anggap tidak ditemukan jika terjadi error koneksi agar tidak menghalangi input
        return None


def get_active_connections(api):
    """
    Mengambil daftar semua koneksi PPP yang sedang aktif dari Mikrotik.
    """
    try:
        # Perintah ini akan mengambil semua entri dari /ppp/active
        logger.info("Mengambil data live 'Active Connections' dari Mikrotik...")
        # OPTIMISASI: Hanya ambil properti yang dibutuhkan (.id dan profile) untuk mengurangi beban.
        # Ini akan mempercepat proses secara signifikan.
        active_list = api.get_resource("/ppp/active").get(proplist=".id,profile")
        logger.info(f"Ditemukan {len(active_list)} koneksi aktif.")
        return active_list
    except Exception as e:
        logger.error(f"Gagal mengambil 'Active Connections': {e}")
        return []


# --- FUNGSI BARU UNTUK MEMBUAT SECRET ---
def create_pppoe_secret(api, data_teknis: DataTeknisModel):
    """Menambahkan PPPoE secret baru di Mikrotik."""
    try:
        ppp_secrets = api.get_resource("/ppp/secret")

        # Siapkan data untuk secret baru
        secret_payload = {
            "name": data_teknis.id_pelanggan,
            "password": data_teknis.password_pppoe,
            "profile": data_teknis.profile_pppoe,
            "service": "pppoe",
            # 'comment': f"Created by Billing API on {datetime.now().strftime('%Y-%m-%d')}"
        }

        # Tambahkan IP Address jika ada
        if data_teknis.ip_pelanggan:
            secret_payload["remote-address"] = data_teknis.ip_pelanggan

        ppp_secrets.add(**secret_payload)
        logger.info(
            f"Berhasil membuat PPPoE secret untuk '{data_teknis.id_pelanggan}'."
        )

    except Exception as e:
        logger.error(
            f"Gagal membuat PPPoE secret untuk '{data_teknis.id_pelanggan}': {e}"
        )
        raise e


# --- FUNGSI BARU SEBAGAI TRIGGER ---
async def trigger_mikrotik_create(db: AsyncSession, data_teknis: DataTeknisModel):
    """Fungsi utama yang dipanggil untuk trigger pembuatan secret di Mikrotik."""
    if not data_teknis or not data_teknis.id_pelanggan:
        logger.warning(
            f"Data teknis atau id_pelanggan tidak valid. Skip pembuatan secret."
        )
        return

    server_id = data_teknis.mikrotik_server_id
    if not server_id:
        logger.error(
            f"mikrotik_server_id tidak di-set untuk data teknis ID {data_teknis.id}. Skip."
        )
        return

    mikrotik_server_info = await db.get(MikrotikServerModel, server_id)
    if not mikrotik_server_info:
        logger.error(f"Server Mikrotik dengan ID {server_id} tidak ditemukan.")
        return

    api, connection = get_api_connection(mikrotik_server_info)
    if not api:
        return

    try:
        create_pppoe_secret(api, data_teknis)
    finally:
        if connection:
            logger.info("Menutup koneksi Mikrotik.")
            connection.disconnect()


def get_all_ppp_profiles(api):
    """Mengambil semua nama PPPoE Profile dari Mikrotik."""
    try:
        ppp_profiles = api.get_resource("/ppp/profile")
        profiles = ppp_profiles.get()
        # Ekstrak hanya kolom 'name' dari setiap profile
        profile_names = [p["name"] for p in profiles]
        logger.info(f"Ditemukan {len(profile_names)} profile di Mikrotik.")
        return profile_names
    except Exception as e:
        logger.error(f"Gagal mengambil daftar PPPoE profile: {e}")
        raise e
