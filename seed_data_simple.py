#!/usr/bin/env python3
"""
Simple Seed Data Script for FTTH Billing Application
Creates initial users, roles, and permissions from backup data
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime


async def create_seed_data():
    """Create seed data for the application"""

    print("🌱 Starting simple seed data creation...")

    # Create database session
    from app.database import engine

    async with engine.begin() as conn:
        print("📊 Database connected")

        # Clear existing data (in correct order to avoid foreign key constraints)
        print("🧹 Clearing existing data...")

        # Clear in reverse order of dependencies
        try:
            await conn.execute(text("DELETE FROM activity_logs"))
            print("✅ Cleared activity_logs")
        except Exception as e:
            print(f"⚠️ Could not clear activity_logs: {e}")

        try:
            await conn.execute(text("DELETE FROM users"))
            print("✅ Cleared users")
        except Exception as e:
            print(f"⚠️ Could not clear users: {e}")

        try:
            await conn.execute(text("DELETE FROM role_has_permissions"))
            print("✅ Cleared role_has_permissions")
        except Exception as e:
            print(f"⚠️ Could not clear role_has_permissions: {e}")

        try:
            await conn.execute(text("DELETE FROM permissions"))
            print("✅ Cleared permissions")
        except Exception as e:
            print(f"⚠️ Could not clear permissions: {e}")

        try:
            await conn.execute(text("DELETE FROM roles"))
            print("✅ Cleared roles")
        except Exception as e:
            print(f"⚠️ Could not clear roles: {e}")

        try:
            await conn.execute(text("DELETE FROM system_settings"))
            print("✅ Cleared system_settings")
        except Exception as e:
            print(f"⚠️ Could not clear system_settings: {e}")

        try:
            await conn.execute(text("DELETE FROM paket_layanan"))
            print("✅ Cleared paket_layanan")
        except Exception as e:
            print(f"⚠️ Could not clear paket_layanan: {e}")

        try:
            await conn.execute(text("DELETE FROM harga_layanan"))
            print("✅ Cleared harga_layanan")
        except Exception as e:
            print(f"⚠️ Could not clear harga_layanan: {e}")

        try:
            await conn.execute(text("DELETE FROM mikrotik_servers"))
            print("✅ Cleared mikrotik_servers")
        except Exception as e:
            print(f"⚠️ Could not clear mikrotik_servers: {e}")

        print("✅ Existing data cleared")

        # Create Roles
        print("👥 Creating roles...")
        roles_data = [
            {"id": 2, "name": "admin"},
            {"id": 6, "name": "Finance"},
            {"id": 9, "name": "Monitoring"},
            {"id": 8, "name": "NOC"},
        ]

        for role in roles_data:
            try:
                await conn.execute(
                    text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
                    {"id": role["id"], "name": role["name"]}
                )
            except Exception as e:
                print(f"⚠️ Could not create role {role['name']}: {e}")
        print(f"✅ Created roles")

        # Create Permissions
        print("🔐 Creating permissions...")
        permissions_data = [
            {"id": 89, "name": "create_activity_log"},
            {"id": 13, "name": "create_brand_paket"},
            {"id": 81, "name": "create_dashboard"},
            {"id": 70, "name": "create_dashboard_jakinet"},
            {"id": 66, "name": "create_dashboard_pelanggan"},
            {"id": 9, "name": "create_data_teknis"},
            {"id": 93, "name": "create_inventory"},
            {"id": 17, "name": "create_invoices"},
            {"id": 45, "name": "create_kelola_s&k"},
            {"id": 5, "name": "create_langganan"},
            {"id": 56, "name": "create_laporan_pendapatan"},
            {"id": 62, "name": "create_manajemen_inventaris"},
            {"id": 21, "name": "create_mikrotik_servers"},
            {"id": 101, "name": "create_odp_management"},
            {"id": 97, "name": "create_olt"},
            {"id": 1, "name": "create_pelanggan"},
            {"id": 33, "name": "create_permissions"},
            {"id": 85, "name": "create_reports_revenue"},
            {"id": 29, "name": "create_roles"},
            {"id": 37, "name": "create_s&k"},
            {"id": 41, "name": "create_simulasi_harga"},
        ]

        for permission in permissions_data:
            try:
                await conn.execute(
                    text("INSERT INTO permissions (id, name) VALUES (:id, :name)"),
                    {"id": permission["id"], "name": permission["name"]}
                )
            except Exception as e:
                print(f"⚠️ Could not create permission {permission['name']}: {e}")
        print(f"✅ Created permissions")

        # Create Role-Permission mappings (admin gets all permissions)
        print("🔗 Creating role-permission mappings...")
        for permission in permissions_data:
            try:
                await conn.execute(
                    text("INSERT INTO role_has_permissions (permission_id, role_id) VALUES (:permission_id, :role_id)"),
                    {"permission_id": permission["id"], "role_id": 2}  # admin role
                )
            except Exception as e:
                print(f"⚠️ Could not create role-permission mapping: {e}")
        print("✅ Created role-permission mappings")

        # Create Users
        print("👤 Creating users...")
        users_data = [
            {
                "id": 4,
                "name": "Ahmad",
                "email": "ahmad@ajnusa.com",
                "password": "$2b$12$nTuJEXJ4114sbltYKFLrievZJfqGLUgrFnTlUYpCqWLDWdrOtSxRm",  # password: admin123
                "role_id": 2,
                "is_active": True,
                "created_at": datetime(2025, 7, 20, 11, 56, 17),
                "updated_at": datetime(2025, 7, 20, 11, 56, 17),
                "password_changed_at": None,
            },
            {
                "id": 5,
                "name": "Abbas",
                "email": "abbas@ajnusa.com",
                "password": "$2b$12$Rt9DvhmacupMVDoXt1A9PeoVMbg5jixUIvTFftDCkg49wLKQapbLi",  # password: abbass123
                "role_id": 9,
                "is_active": True,
                "created_at": datetime(2025, 7, 20, 12, 33, 8),
                "updated_at": datetime(2025, 9, 3, 13, 59, 5),
                "password_changed_at": None,
            },
            {
                "id": 6,
                "name": "Adolf",
                "email": "adolf@ajnusa.com",
                "password": "$2b$12$471CKrySK.ZXIHCwDcm4FuTVGhHhenSo9WaOu3dTrrbEFrOwn5yNy",  # password: adolf123
                "role_id": 6,
                "is_active": True,
                "created_at": datetime(2025, 8, 27, 11, 50, 48),
                "updated_at": datetime(2025, 8, 27, 11, 50, 48),
                "password_changed_at": None,
            },
            {
                "id": 7,
                "name": "Deni",
                "email": "coba@coba.com",
                "password": "$2b$12$tJKtQGLl92lslHqht/XMhuoIsJDc3e2sQOMULFOd/N5woINYHG/FC",  # password: deni123
                "role_id": 8,
                "is_active": True,
                "created_at": datetime(2025, 9, 20, 23, 54, 28),
                "updated_at": datetime(2025, 9, 20, 23, 54, 28),
                "password_changed_at": None,
            },
            {
                "id": 8,
                "name": "Komar",
                "email": "komar@aj.com",
                "password": "gAAAAABo48VuAgTB0_BPi1y2eyPAT0j1NO4J7klbX3cHbqJmhnXsSlUU_m7flQybRTbCIqZhTbSBc_Ewtzk0PwPxVmihdK3XQ9SYuHT5BNJ9Xm4Z0L6Kp34yJhEnmUqFQmBT5moiBUY7mouiFdmv9lt0qjkCrR97_w==",  # encrypted password
                "role_id": 6,
                "is_active": True,
                "password_changed_at": datetime(2025, 10, 6, 13, 34, 38),
                "created_at": datetime(2025, 10, 6, 20, 34, 38),
                "updated_at": datetime(2025, 10, 6, 20, 34, 38),
            }
        ]

        for user in users_data:
            try:
                await conn.execute(
                    text("""
                        INSERT INTO users (id, name, email, password, role_id, is_active, created_at, updated_at, password_changed_at)
                        VALUES (:id, :name, :email, :password, :role_id, :is_active, :created_at, :updated_at, :password_changed_at)
                    """),
                    user
                )
                print(f"✅ Created user: {user['name']}")
            except Exception as e:
                print(f"⚠️ Could not create user {user['name']}: {e}")

        # Create sample System Settings
        print("⚙️ Creating system settings...")
        settings_data = [
            {"setting_key": "app_name", "setting_value": "FTTH Billing System"},
            {"setting_key": "company_name", "setting_value": "AJN USA"},
            {"setting_key": "default_brand", "setting_value": "Jakinet"},
            {"setting_key": "timezone", "setting_value": "Asia/Jakarta"},
        ]

        for setting in settings_data:
            try:
                await conn.execute(
                    text("INSERT INTO system_settings (setting_key, setting_value) VALUES (:setting_key, :setting_value)"),
                    setting
                )
            except Exception as e:
                print(f"⚠️ Could not create setting {setting['setting_key']}: {e}")
        print(f"✅ Created system settings")

        # Create sample Brands and Packages
        print("📦 Creating brands and packages...")
        brands_data = [
            {"id": "ajn-01", "brand": "Jakinet", "pajak": 11, "xendit_key_name": "JAKINET"},
            {"id": "jlt-01", "brand": "Jelantik", "pajak": 11, "xendit_key_name": "JELANTIK"},
        ]

        for brand in brands_data:
            try:
                await conn.execute(
                    text("INSERT INTO harga_layanan (id, brand, pajak, xendit_key_name) VALUES (:id, :brand, :pajak, :xendit_key_name)"),
                    brand
                )
                print(f"✅ Created brand: {brand['brand']}")
            except Exception as e:
                print(f"⚠️ Could not create brand {brand['brand']}: {e}")

        # Create sample packages
        packages_data = [
            {"id": 1, "nama_paket": "Internet 10 Mbps", "harga": 150000, "kecepatan": "10 Mbps", "id_brand": "ajn-01"},
            {"id": 2, "nama_paket": "Internet 20 Mbps", "harga": 250000, "kecepatan": "20 Mbps", "id_brand": "ajn-01"},
            {"id": 3, "nama_paket": "Internet 50 Mbps", "harga": 450000, "kecepatan": "50 Mbps", "id_brand": "ajn-01"},
        ]

        for package in packages_data:
            try:
                await conn.execute(
                    text("INSERT INTO paket_layanan (id, nama_paket, harga, kecepatan, id_brand) VALUES (:id, :nama_paket, :harga, :kecepatan, :id_brand)"),
                    package
                )
                print(f"✅ Created package: {package['nama_paket']}")
            except Exception as e:
                print(f"⚠️ Could not create package {package['nama_paket']}: {e}")

        # Create sample Mikrotik Server
        print("🖥️ Creating Mikrotik server...")
        mikrotik_data = {
            "id": 1,
            "name": "Main Router",
            "host_ip": "192.168.1.1",
            "port": 22,
            "username": "admin",
            "password": "password",
            "is_active": True,
            "last_connection_status": "connected",
            "ros_version": "7.12",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        try:
            await conn.execute(
                text("""
                    INSERT INTO mikrotik_servers (id, name, host_ip, port, username, password, is_active, last_connection_status, ros_version, created_at, updated_at)
                    VALUES (:id, :name, :host_ip, :port, :username, :password, :is_active, :last_connection_status, :ros_version, :created_at, :updated_at)
                """),
                mikrotik_data
            )
            print("✅ Created Mikrotik server")
        except Exception as e:
            print(f"⚠️ Could not create Mikrotik server: {e}")

        await conn.commit()
        print("🎉 Seed data creation completed successfully!")

        print("\n📋 Summary:")
        print(f"   👥 Roles: 4 (admin, Finance, Monitoring, NOC)")
        print(f"   🔐 Permissions: 20")
        print(f"   👤 Users: 5")
        print(f"   ⚙️ System Settings: 4")
        print(f"   📦 Brands: 2")
        print(f"   📦 Packages: 3")
        print(f"   🖥️ Mikrotik Servers: 1")

        print("\n🔑 Default Login Credentials:")
        print("   📧 Email: ahmad@ajnusa.com")
        print("   🔒 Password: admin123")
        print("   🎭 Role: admin")

        print("\n   📧 Email: abbas@ajnusa.com")
        print("   🔒 Password: abbass123")
        print("   🎭 Role: Monitoring")

        print("\n   📧 Email: adolf@ajnusa.com")
        print("   🔒 Password: adolf123")
        print("   🎭 Role: Finance")


if __name__ == "__main__":
    try:
        asyncio.run(create_seed_data())
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        sys.exit(1)