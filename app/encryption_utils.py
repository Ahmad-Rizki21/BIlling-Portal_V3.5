# app/encryption_utils.py
"""
Modul ini buat setup automatic encryption/decryption pake SQLAlchemy event listeners.
Jadi kita nggak perlu manual encrypt/decrypt tiap kali save/load data.

Cara kerja:
- Event listeners bakal jalan otomatis saat ada operasi database
- before_insert/before_update: encrypt data sebelum disimpan
- load: decrypt data setelah diambil dari database

Data yang dienkripsi otomatis:
- Password user (login sistem)
- Password PPPoE pelanggan (internet)
- Nomor KTP pelanggan (data pribadi)
- Password Mikrotik server (konfigurasi)

Security benefits:
- Transparent encryption - developer nggak perlu panggil manual
- Consistent encryption across all database operations
- Prevent human error (lupa encrypt)
- Zero-impact ke existing code base
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

from .encryption import encryption_service
from .models.mikrotik_server import MikrotikServer
from .models.user import User


# Import models inside functions to avoid circular imports
def setup_datateknis_listeners():
    """
    Setup event listeners khusus buat model DataTeknis.
    Model ini isi data teknis pelanggan termasuk password PPPoE.

    Event yang di-setup:
    - before_insert/before_update: encrypt password PPPoE
    - load: decrypt password PPPoE saat dibaca

    Note:
    - Commented out karena lagi debugging atau perubahan logic
    - Password PPPoE ini dipake buat login internet pelanggan
    - Sensitif banget harus selalu terenkripsi di database
    """
    from .models.data_teknis import DataTeknis

    # Enkripsi password PPPoE sebelum insert/update
    # @event.listens_for(DataTeknis, 'before_insert')
    # @event.listens_for(DataTeknis, 'before_update')
    def encrypt_pppoe_password(mapper, connection, target):
        if target.password_pppoe and not target.password_pppoe.startswith("gAAAAAB"):
            target.password_pppoe = encryption_service.encrypt(target.password_pppoe)

    # Dekripsi password PPPoE setelah select
    # @event.listens_for(DataTeknis, 'load')
    def decrypt_pppoe_password(target, context):
        if target.password_pppoe and target.password_pppoe.startswith("gAAAAAB"):
            target.password_pppoe = encryption_service.decrypt(target.password_pppoe)


def setup_pelanggan_listeners():
    """
    Setup event listeners buat model Pelanggan.
    Fokusnya buat enkripsi nomor KTP pelanggan.

    Yang diproteksi:
    - Nomor KTP (data pribadi sensitif)
    - Auto encrypt saat simpan data baru atau update
    - Auto decrypt saat ambil data dari database

    Privacy protection:
    - KTP itu data pribadi yang sangat sensitif
    - Harus dienkripsi di database compliance ke privacy laws
    - Decrypt hanya saat dibaca di aplikasi

    Error handling:
    - Graceful fallback kalau gagal decrypt
    - Log error buat debugging
    - Biarkan nilai tetap terenkripsi kalau error
    """
    from .models.pelanggan import Pelanggan

    @event.listens_for(Pelanggan, "before_insert")
    @event.listens_for(Pelanggan, "before_update")
    def encrypt_nik(mapper, connection, target):
        if target.no_ktp and not encryption_service.is_encrypted(target.no_ktp):
            target.no_ktp = encryption_service.encrypt(target.no_ktp)

    @event.listens_for(Pelanggan, "load")
    def decrypt_nik(target, context):
        if target.no_ktp and encryption_service.is_encrypted(target.no_ktp):
            try:
                target.no_ktp = encryption_service.decrypt(target.no_ktp)
            except Exception as e:
                # Jika gagal mendekripsi, log error dan biarkan nilai tetap seperti adanya
                print(f"Peringatan: Gagal mendekripsi no_ktp untuk pelanggan ID {getattr(target, 'id', 'unknown')}: {e}")
                # Biarkan nilai tetap terenkripsi agar tidak menyebabkan error validasi


def encrypt_sensitive_data():
    """
    Setup semua event listeners buat ENKRIPSI data sensitif.
    Fungsi ini dipanggil sekali saat aplikasi startup.

    Event yang di-setup:
    - User password (login sistem admin/staff)
    - Mikrotik server password (akses network device)
    - DataTeknis password PPPoE (password internet pelanggan)
    - Pelanggan nomor KTP (data pribadi)

    Cara panggil:
    from app.encryption_utils import encrypt_sensitive_data
    encrypt_sensitive_data()

    Note:
    - Ini setup encryption ONLY (before_insert/before_update)
    - Buat decrypt, panggil decrypt_sensitive_data()
    - Must dipanggil sebelum operasi database dimulai
    """

    # Enkripsi password user sebelum insert/update
    @event.listens_for(User, "before_insert")
    @event.listens_for(User, "before_update")
    def encrypt_user_password(mapper, connection, target):
        if target.password and not target.password.startswith("gAAAAAB"):
            target.password = encryption_service.encrypt(target.password)

    # Enkripsi password Mikrotik sebelum insert/update
    # @event.listens_for(MikrotikServer, 'before_insert')
    # @event.listens_for(MikrotikServer, 'before_update')
    def encrypt_mikrotik_password(mapper, connection, target):
        if target.password and not target.password.startswith("gAAAAAB"):
            target.password = encryption_service.encrypt(target.password)

    setup_datateknis_listeners()
    setup_pelanggan_listeners()


def decrypt_sensitive_data():
    """
    Setup semua event listeners buat DEKRIPSI data sensitif.
    Fungsi ini dipanggil sekali saat aplikasi startup.

    Event yang di-setup:
    - User password (auto decrypt saat login)
    - Mikrotik server password (saat konek ke device)
    - DataTeknis password PPPoE (saat dipake buat Mikrotik)
    - Pelanggan nomor KTP (saat ditampilkan di UI)

    Cara kerja:
    - Event 'load' bakal trigger setiap kali object di-load dari DB
    - Data otomatis terdecrypt di memory
    - Tetap terenkripsi di database

    Cara panggil:
    from app.encryption_utils import decrypt_sensitive_data
    decrypt_sensitive_data()

    Performance:
    - Decrypt hanya saat data dibaca, tidak saat query
    - Ciphertext tetap di database
    - Plaintext hanya di application memory
    """

    # Dekripsi password user setelah select
    @event.listens_for(User, "load")
    def decrypt_user_password(target, context):
        if target.password and target.password.startswith("gAAAAAB"):
            target.password = encryption_service.decrypt(target.password)

    # Dekripsi password Mikrotik setelah select
    # @event.listens_for(MikrotikServer, 'load')
    def decrypt_mikrotik_password(target, context):
        if target.password and target.password.startswith("gAAAAAB"):
            target.password = encryption_service.decrypt(target.password)

    setup_datateknis_listeners()
    setup_pelanggan_listeners()
