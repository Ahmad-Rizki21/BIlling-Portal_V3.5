from sqlalchemy import event
from sqlalchemy.orm import Session

from .encryption import encryption_service
from .models.mikrotik_server import MikrotikServer
from .models.user import User


# Import models inside functions to avoid circular imports
def setup_datateknis_listeners():
    """Setup event listeners for DataTeknis model after all models are loaded."""
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
    """Setup event listeners for Pelanggan model."""
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
    """Setup event listeners untuk enkripsi data sensitif"""

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
    """Setup event listeners untuk dekripsi data sensitif saat diakses"""

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
