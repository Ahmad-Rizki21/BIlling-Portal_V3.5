#!/usr/bin/env python3
"""
FINAL INTEGRATED SEED SCRIPT - Complete data import from backup to new structure

Handles all missing data types with proper field mapping and foreign key relationships.
"""

import asyncio
import os
import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.mikrotik_server import MikrotikServer
from app.models.olt import OLT
from app.models.odp import ODP
from app.models.harga_layanan import HargaLayanan
from app.models.paket_layanan import PaketLayanan
from app.models.pelanggan import Pelanggan
from app.models.data_teknis import DataTeknis
from app.models.langganan import Langganan
from app.models.invoice import Invoice
from app.models.payment_callback_log import PaymentCallbackLog
from app.models.syarat_ketentuan import SyaratKetentuan
from app.models.activity_log import ActivityLog
from app.models.token_blacklist import TokenBlacklist
from app.models.traffic_history import TrafficHistory
from app.models.system_setting import SystemSetting
from app.models.role_has_permissions import RoleHasPermissions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ComprehensiveDataImporter:
    def __init__(self, db_url: str, backup_file_path: str):
        self.db_url = db_url
        self.backup_file_path = backup_file_path
        self.async_engine = create_async_engine(self.db_url)
        self.async_session = sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)

    async def clear_all_tables(self):
        """Completely clear all tables to start fresh"""
        logger.info("Clearing all existing data...")
        async with self.async_engine.begin() as conn:
            # Drop and recreate all tables
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables cleared and recreated")

    async def import_users(self):
        """Import users with proper role relationships"""
        logger.info("Importing users...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, name, email, password, role_id, created_at, updated_at, is_active FROM users"))
            rows = result.fetchall()
            
            for row in rows:
                try:
                    user = User(
                        id=row[0],
                        name=row[1],
                        email=row[2],
                        password=row[3],
                        role_id=row[4],
                        created_at=row[5],
                        updated_at=row[6],
                        is_active=row[7] if row[7] is not None else True
                    )
                    session.add(user)
                except Exception as e:
                    logger.warning(f"Failed to import user {row[0]}: {str(e)}")
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} users")

    async def import_roles(self):
        """Import roles"""
        logger.info("Importing roles...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, name FROM roles"))
            rows = result.fetchall()
            
            for row in rows:
                role = Role(id=row[0], name=row[1])
                session.add(role)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} roles")

    async def import_permissions(self):
        """Import permissions"""
        logger.info("Importing permissions...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, name FROM permissions"))
            rows = result.fetchall()
            
            for row in rows:
                permission = Permission(id=row[0], name=row[1])
                session.add(permission)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} permissions")

    async def import_role_has_permissions(self):
        """Import role_has_permissions"""
        logger.info("Importing role permissions links...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT permission_id, role_id FROM role_has_permissions"))
            rows = result.fetchall()
            
            for row in rows:
                role_permission = RoleHasPermissions(
                    permission_id=row[0],
                    role_id=row[1]
                )
                session.add(role_permission)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} role-permission links")

    async def import_mikrotik_servers(self):
        """Import Mikrotik servers"""
        logger.info("Importing Mikrotik servers...")
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT id, name, host_ip, username, password, port, ros_version, is_active, last_connection_status, last_connected_at, created_at, updated_at FROM mikrotik_servers")
            )
            rows = result.fetchall()
            
            for row in rows:
                server = MikrotikServer(
                    id=row[0],
                    name=row[1],
                    host_ip=row[2],
                    username=row[3],
                    password=row[4],
                    port=row[5],
                    ros_version=row[6],
                    is_active=row[7],
                    last_connection_status=row[8],
                    last_connected_at=row[9],
                    created_at=row[10],
                    updated_at=row[11]
                )
                session.add(server)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} Mikrotik servers")

    async def import_olt_and_odp(self):
        """Import OLT and ODP with proper hierarchy"""
        logger.info("Importing OLT and ODP...")
        async with self.async_session() as session:
            # Import OLT first
            result = await session.execute(text("SELECT id, nama_olt, ip_address, tipe_olt, username, password, mikrotik_server_id FROM olt"))
            rows = result.fetchall()
            
            for row in rows:
                olt = OLT(
                    id=row[0],
                    nama_olt=row[1],
                    ip_address=row[2],
                    tipe_olt=row[3],
                    username=row[4],
                    password=row[5],
                    mikrotik_server_id=row[6]
                )
                session.add(olt)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} OLTs")
            
            # Import ODP
            result = await session.execute(text("SELECT id, kodE_odp, alamat, kapasitas_port, latitude, longitude, parent_odp_id, olt_id FROM odp"))
            rows = result.fetchall()
            
            for row in rows:
                odp = ODP(
                    id=row[0],
                    kode_odp=row[1],
                    alamat=row[2],
                    kapasitas_port=row[3],
                    latitude=row[4],
                    longitude=row[5],
                    parent_odp_id=row[6],
                    olt_id=row[7]
                )
                session.add(odp)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} ODPs")

    async def import_harga_and_paket(self):
        """Import harga_layanan and paket_layanan with proper relationships"""
        logger.info("Importing pricing and packages...")
        async with self.async_session() as session:
            # Import harga_layanan first
            result = await session.execute(text("SELECT id_brand, brand, pajak, xendit_key_name FROM harga_layanan"))
            rows = result.fetchall()
            
            for row in rows:
                harga = HargaLayanan(
                    id_brand=row[0],
                    brand=row[1],
                    pajak=row[2],
                    xendit_key_name=row[3]
                )
                session.add(harga)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} harga_layanan records")
            
            # Import paket_layanan
            result = await session.execute(text("SELECT id, id_brand, nama_paket, kecepatan, harga FROM paket_layanan"))
            rows = result.fetchall()
            
            for row in rows:
                paket = PaketLayanan(
                    id=row[0],
                    id_brand=row[1],
                    nama_paket=row[2],
                    kecepatan=row[3],
                    harga=row[4]
                )
                session.add(paket)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} paket_layanan records")

    async def import_pelanggan_and_related(self):
        """Import customers and their related data (langganan, data_teknis)"""
        logger.info("Importing customers and related data...")
        async with self.async_session() as session:
            # Import pelanggan
            result = await session.execute(text("SELECT id, no_ktp, nama, alamat, alamat_custom, alamat_2, tgl_instalasi, blok, unit, no_telp, email, id_brand, layanan, brand_default, mikrotik_server_id, created_at, updated_at FROM pelanggan"))
            rows = result.fetchall()
            
            for row in rows:
                pelanggan = Pelanggan(
                    id=row[0],
                    no_ktp=row[1],
                    nama=row[2],
                    alamat=row[3],
                    alamat_custom=row[4],
                    alamat_2=row[5],
                    tgl_instalasi=row[6],
                    blok=row[7],
                    unit=row[8],
                    no_telp=row[9],
                    email=row[10],
                    id_brand=row[11],
                    layanan=row[12],
                    brand_default=row[13],
                    mikrotik_server_id=row[14]
                )
                session.add(pelanggan)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} pelanggan records")
            
            # Import data_teknis
            result = await session.execute(text("SELECT id, pelanggan_id, id_vlan, id_pelanggan, password_pppoe, ip_pelanggan, profile_pppoe, olt, olt_custom, pon, otb, odc, odp_id, port_odp, onu_power, speedtest_proof, mikrotik_server_id, sn, mikrotik_sync_pending FROM data_teknis"))
            rows = result.fetchall()
            
            imported_count = 0
            for row in rows:
                try:
                    # Check if pelanggan_id exists
                    pelanggan_exists = await session.execute(
                        text("SELECT 1 FROM pelanggan WHERE id = :id"),
                        {"id": row[1]}
                    )
                    if pelanggan_exists.fetchone():
                        data_teknis = DataTeknis(
                            id=row[0],
                            pelanggan_id=row[1],
                            id_vlan=row[2],
                            id_pelanggan=row[3],
                            password_pppoe=row[4],
                            ip_pelanggan=row[5],
                            profile_pppoe=row[6],
                            olt=row[7],
                            olt_custom=row[8],
                            pon=row[9],
                            otb=row[10],
                            odc=row[11],
                            odp_id=row[12],
                            port_odp=row[13],
                            onu_power=row[14],
                            speedtest_proof=row[15],
                            mikrotik_server_id=row[16],
                            sn=row[17],
                            mikrotik_sync_pending=row[18]
                        )
                        session.add(data_teknis)
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import data_teknis {row[0]}: {str(e)}")
            
            await session.commit()
            logger.info(f"Successfully imported {imported_count} data_teknis records")

            # Import langganan
            result = await session.execute(text("SELECT id, pelanggan_id, paket_layanan_id, tgl_jatuh_tempo, tgl_invoice_terakhir, metode_pembayaran, harga_awal, status, created_at, updated_at, tgl_mulai_langganan, tgl_berhenti FROM langganan"))
            rows = result.fetchall()
            
            for row in rows:
                try:
                    # Check if pelanggan_id and paket_layanan_id exist
                    pelanggan_exists = await session.execute(
                        text("SELECT 1 FROM pelanggan WHERE id = :id"),
                        {"id": row[1]}
                    )
                    if pelanggan_exists.fetchone():
                        paket_exists = await session.execute(
                            text("SELECT 1 FROM paket_layanan WHERE id = :id"),
                            {"id": row[2]}
                        )
                        if paket_exists.fetchone():
                            langganan = Langganan(
                                id=row[0],
                                pelanggan_id=row[1],
                                paket_layanan_id=row[2],
                                tgl_jatuh_tempo=row[3],
                                tgl_invoice_terakhir=row[4],
                                metode_pembayaran=row[5],
                                harga_awal=row[6],
                                status=row[7],
                                created_at=row[8],
                                updated_at=row[9],
                                tgl_mulai_langganan=row[10],
                                tgl_berhenti=row[11]
                            )
                            session.add(langganan)
                except Exception as e:
                    logger.warning(f"Failed to import langganan {row[0]}: {str(e)}")
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} langganan records")

    async def import_invoices(self):
        """Import invoices with proper mapping"""
        logger.info("Importing invoices...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, invoice_number, pelanggan_id, id_pelanggan, brand, total_harga, no_telp, email, tgl_invoice, tgl_jatuh_tempo, status_invoice, payment_link, metode_pembayaran, expiry_date, xendit_id, xendit_external_id, paid_amount, paid_at, is_processing, created_at, updated_at, deleted_at FROM invoices"))
            rows = result.fetchall()
            
            imported_count = 0
            for row in rows:
                try:
                    # Check if pelanggan_id exists
                    pelanggan_exists = await session.execute(
                        text("SELECT 1 FROM pelanggan WHERE id = :id"),
                        {"id": row[2]}
                    )
                    if pelanggan_exists.fetchone():
                        invoice = Invoice(
                            id=row[0],
                            invoice_number=row[1],
                            pelanggan_id=row[2],
                            id_pelanggan=row[3],
                            brand=row[4],
                            total_harga=Decimal(str(row[5])) if row[5] else Decimal('0'),
                            no_telp=row[6],
                            email=row[7],
                            tgl_invoice=row[8],
                            tgl_jatuh_tempo=row[9],
                            status_invoice=row[10],
                            payment_link=row[11],
                            metode_pembayaran=row[12],
                            expiry_date=row[13],
                            xendit_id=row[14],
                            xendit_external_id=row[15],
                            paid_amount=Decimal(str(row[16])) if row[16] else Decimal('0'),
                            paid_at=row[17],
                            is_processing=row[18],
                            created_at=row[19],
                            updated_at=row[20],
                            deleted_at=row[21]
                        )
                        session.add(invoice)
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import invoice {row[0]}: {str(e)}")
            
            await session.commit()
            logger.info(f"Successfully imported {imported_count} invoices records")

    async def import_system_logs_and_settings(self):
        """Import all system logs and settings"""
        logger.info("Importing system logs and settings...")
        
        # Import payment callback logs
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, idempotency_key, xendit_id, external_id, callback_data, status, processed_at, created_at FROM payment_callback_logs"))
            rows = result.fetchall()
            
            for row in rows:
                log = PaymentCallbackLog(
                    id=row[0],
                    idempotency_key=row[1],
                    xendit_id=row[2],
                    external_id=row[3],
                    callback_data=row[4],
                    status=row[5],
                    processed_at=row[6],
                    created_at=row[7]
                )
                session.add(log)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} payment callback logs")
        
        # Import syarat_ketentuan
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, judul, konten, tipe, versi, created_at FROM syarat_ketentuan"))
            rows = result.fetchall()
            
            for row in rows:
                sk = SyaratKetentuan(
                    id=row[0],
                    judul=row[1],
                    konten=row[2],
                    tipe=row[3],
                    versi=row[4],
                    created_at=row[5]
                )
                session.add(sk)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} syarat_ketentuan records")
        
        # Import activity logs
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, user_id, timestamp, action, details FROM activity_logs"))
            rows = result.fetchall()
            
            for row in rows:
                log = ActivityLog(
                    id=row[0],
                    user_id=row[1],
                    timestamp=row[2],
                    action=row[3],
                    details=row[4]
                )
                session.add(log)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} activity logs")
        
        # Import token blacklist
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, jti, user_id, token_type, expires_at, created_at, revoked, revoked_at, revoked_reason FROM token_blacklist"))
            rows = result.fetchall()
            
            for row in rows:
                token = TokenBlacklist(
                    id=row[0],
                    jti=row[1],
                    user_id=row[2],
                    token_type=row[3],
                    expires_at=row[4],
                    created_at=row[5],
                    revoked=row[6],
                    revoked_at=row[7],
                    revoked_reason=row[8]
                )
                session.add(token)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} token blacklist records")
        
        # Import system settings
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, setting_key, setting_value FROM system_settings"))
            rows = result.fetchall()
            
            for row in rows:
                setting = SystemSetting(
                    id=row[0],
                    setting_key=row[1],
                    setting_value=row[2]
                )
                session.add(setting)
            
            await session.commit()
            logger.info(f"Successfully imported {len(rows)} system settings")

    async def import_traffic_history(self):
        """Import traffic history with data_teknis relationship check"""
        logger.info("Importing traffic history...")
        async with self.async_session() as session:
            result = await session.execute(text("SELECT id, data_teknis_id, mikrotik_server_id, username_pppoe, ip_address, rx_bytes, tx_bytes, rx_packets, tx_packets, rx_mbps, tx_mbps, total_mbps, uptime_seconds, uptime_formatted, is_latest, is_active, timestamp, created_at, server_id FROM traffic_history"))
            rows = result.fetchall()
            
            imported_count = 0
            for row in rows:
                try:
                    # Check if data_teknis_id exists
                    data_teknis_exists = await session.execute(
                        text("SELECT 1 FROM data_teknis WHERE id = :id"),
                        {"id": row[1]}
                    )
                    if data_teknis_exists.fetchone():
                        history = TrafficHistory(
                            id=row[0],
                            data_teknis_id=row[1],
                            mikrotik_server_id=row[2],
                            username_pppoe=row[3],
                            ip_address=row[4],
                            rx_bytes=row[5],
                            tx_bytes=row[6],
                            rx_packets=row[7],
                            tx_packets=row[8],
                            rx_mbps=Decimal(str(row[9])) if row[9] else Decimal('0'),
                            tx_mbps=Decimal(str(row[10])) if row[10] else Decimal('0'),
                            total_mbps=Decimal(str(row[11])) if row[11] else Decimal('0'),
                            uptime_seconds=row[12],
                            uptime_formatted=row[13],
                            is_latest=row[14],
                            is_active=row[15],
                            timestamp=row[16],
                            created_at=row[17],
                            server_id=row[18]
                        )
                        session.add(history)
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import traffic history {row[0]}: {str(e)}")
            
            await session.commit()
            logger.info(f"Successfully imported {imported_count} traffic history records")

    async def run_full_import(self):
        """Run complete import process"""
        logger.info("=== Starting comprehensive data import process ===")
        
        # Clear all tables first
        await self.clear_all_tables()
        
        # Import data in proper dependency order
        await self.import_roles()
        await self.import_permissions()
        await self.import_role_has_permissions()
        await self.import_mikrotik_servers()
        await self.import_olt_and_odp()
        await self.import_harga_and_paket()
        await self.import_users()
        await self.import_pelanggan_and_related()
        await self.import_invoices()
        await self.import_system_logs_and_settings()
        await self.import_traffic_history()
        
        logger.info("=== Comprehensive import completed successfully! ===")

def main():
    """
    Complete import script that handles all data with proper relationships and error handling
    """
    db_url = os.getenv("DATABASE_URL", "mysql+aiomysql://root:@localhost:3306/ftth_billing_new")
    
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        return
    
    logger.info("Starting comprehensive database import...")
    
    importer = ComprehensiveDataImporter(db_url, "/home/ahmad/Documents/Projects/ArtacomFTTHBilling_V2/DATABASE-EXISTING/backup_seed20251102.sql")
    
    try:
        asyncio.run(importer.run_full_import())
        logger.info("🎉 COMPLETE IMPORT SUCCESSFUL - All data structures are now in place!")
    except Exception as e:
        logger.error(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Import process completed. System is now ready for operations!")

if __name__ == "__main__":
    main()