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

        # Disable foreign key checks temporarily
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Clear all tables
        tables_to_clear = [
            "activity_logs",
            "invoices",
            "langganan",
            "pelanggan",
            "paket_layanan",
            "users",
            "role_has_permissions",
            "permissions",
            "roles",
            "system_settings",
            "harga_layanan",
            "mikrotik_servers",
            "action_taken",
            "odp",
            "olt",
            "data_teknis",
            "inventory_history",
            "inventory_items",
            "inventory_item_types",
            "inventory_statuses",
            "payment_callback_logs",
            "ticket_history",
            "token_blacklist",
            "traffic_history",
            "trouble_ticket",
            "syarat_ketentuan"
        ]

        for table in tables_to_clear:
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table}"))
                print(f"✅ Truncated {table}")
            except Exception as e:
                try:
                    await conn.execute(text(f"DELETE FROM {table}"))
                    print(f"✅ Deleted from {table}")
                except Exception as e2:
                    print(f"⚠️ Could not clear {table}: {e2}")

        # Re-enable foreign key checks
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        print("✅ All existing data cleared")

        # Create Roles (from mysqldump backup)
        print("👥 Creating roles...")
        roles_data = [
            {"id": 1, "name": "Admin"},
            {"id": 7, "name": "Bos Gudang"},
            {"id": 6, "name": "Finance"},
            {"id": 2, "name": "NOC"},
            {"id": 5, "name": "Teknisi"},
        ]

        for role in roles_data:
            try:
                await conn.execute(
                    text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
                    {"id": role["id"], "name": role["name"]}
                )
                print(f"✅ Created role: {role['name']} (ID: {role['id']})")
            except Exception as e:
                print(f"⚠️ Could not create role {role['name']}: {e}")
        print(f"✅ Created roles")

        # Create Permissions (from mysqldump backup)
        print("🔐 Creating permissions...")

        # Extract permissions from dump file
        import re
        try:
            with open("DATABASE-EXISTING/backup_seed20251102.sql", 'r', encoding='utf-8') as f:
                content = f.read()

            # Find INSERT statements for permissions
            permissions_match = re.search(r'INSERT INTO \`permissions\` VALUES (.*?);', content, re.DOTALL)
            if permissions_match:
                permissions_values = permissions_match.group(1)
                # Parse individual permission records
                permission_records = re.findall(r'\((\d+),\'([^\']+)\'\)', permissions_values)

                for perm_id, perm_name in permission_records:
                    try:
                        await conn.execute(
                            text("INSERT INTO permissions (id, name) VALUES (:id, :name)"),
                            {"id": int(perm_id), "name": perm_name}
                        )
                    except Exception as e:
                        print(f"⚠️ Could not create permission {perm_name}: {e}")

                print(f"✅ Created {len(permission_records)} permissions")
            else:
                print("⚠️ No permissions found in dump file")

        except Exception as e:
            print(f"⚠️ Error reading permissions from dump: {e}")

        # Create Role-Permission mappings (from mysqldump backup)
        print("🔗 Creating role-permission mappings...")
        try:
            # Find INSERT statements for role_has_permissions
            role_perm_match = re.search(r'INSERT INTO \`role_has_permissions\` VALUES (.*?);', content, re.DOTALL)
            if role_perm_match:
                role_perm_values = role_perm_match.group(1)
                # Parse individual role-permission records
                role_perm_records = re.findall(r'\((\d+),(\d+)\)', role_perm_values)

                for perm_id, role_id in role_perm_records:
                    try:
                        await conn.execute(
                            text("INSERT INTO role_has_permissions (permission_id, role_id) VALUES (:permission_id, :role_id)"),
                            {"permission_id": int(perm_id), "role_id": int(role_id)}
                        )
                    except Exception as e:
                        print(f"⚠️ Could not create role-permission mapping ({perm_id}, {role_id}): {e}")

                print(f"✅ Created {len(role_perm_records)} role-permission mappings")
            else:
                print("⚠️ No role-permission mappings found in dump file")

        except Exception as e:
            print(f"⚠️ Error reading role-permission mappings from dump: {e}")

        # Create Users (from mysqldump backup) - DISABLED - using backup import below instead
        # print("👤 Creating users...")

        # OLD USERS SECTION DISABLED - using backup import below instead

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

        # Create Brands and Packages from "harga dan paket.txt"
        print("📦 Creating brands and packages...")
        brands_data = [
            {"id_brand": "ajn-01", "brand": "JAKINET", "pajak": 11, "xendit_key_name": "JAKINET"},
            {"id_brand": "ajn-02", "brand": "JELANTIK", "pajak": 11, "xendit_key_name": "JELANTIK"},
            {"id_brand": "ajn-03", "brand": "JELANTIK NAGRAK", "pajak": 11, "xendit_key_name": "JELANTIK_NAGRAK"},
        ]

        for brand in brands_data:
            try:
                await conn.execute(
                    text("INSERT INTO harga_layanan (id_brand, brand, pajak, xendit_key_name) VALUES (:id_brand, :brand, :pajak, :xendit_key_name)"),
                    brand
                )
                print(f"✅ Created brand: {brand['brand']} ({brand['id_brand']})")
            except Exception as e:
                print(f"⚠️ Could not create brand {brand['brand']}: {e}")

        # Create packages for each brand based on "harga dan paket.txt"
        packages_data = [
            # JAKINET Packages
            {"id": 1, "nama_paket": "Internet 10 Mbps", "harga": 135135, "kecepatan": 10, "id_brand": "ajn-01"},
            {"id": 2, "nama_paket": "Internet 20 Mbps", "harga": 199000, "kecepatan": 20, "id_brand": "ajn-01"},
            {"id": 3, "nama_paket": "Internet 30 Mbps", "harga": 224000, "kecepatan": 30, "id_brand": "ajn-01"},
            {"id": 4, "nama_paket": "Internet 50 Mbps", "harga": 254000, "kecepatan": 50, "id_brand": "ajn-01"},

            # JELANTIK Packages
            {"id": 5, "nama_paket": "Internet 10 Mbps", "harga": 150000, "kecepatan": 10, "id_brand": "ajn-02"},
            {"id": 6, "nama_paket": "Internet 20 Mbps", "harga": 209000, "kecepatan": 20, "id_brand": "ajn-02"},
            {"id": 7, "nama_paket": "Internet 30 Mbps", "harga": 249000, "kecepatan": 30, "id_brand": "ajn-02"},
            {"id": 8, "nama_paket": "Internet 50 Mbps", "harga": 289000, "kecepatan": 50, "id_brand": "ajn-02"},

            # JELANTIK NAGRAK Packages
            {"id": 9, "nama_paket": "Internet 10 Mbps", "harga": 135135, "kecepatan": 10, "id_brand": "ajn-03"},
            {"id": 10, "nama_paket": "Internet 20 Mbps", "harga": 199000, "kecepatan": 20, "id_brand": "ajn-03"},
            {"id": 11, "nama_paket": "Internet 30 Mbps", "harga": 224000, "kecepatan": 30, "id_brand": "ajn-03"},
            {"id": 12, "nama_paket": "Internet 50 Mbps", "harga": 254000, "kecepatan": 50, "id_brand": "ajn-03"},
        ]

        for package in packages_data:
            try:
                await conn.execute(
                    text("INSERT INTO paket_layanan (id, nama_paket, harga, kecepatan, id_brand) VALUES (:id, :nama_paket, :harga, :kecepatan, :id_brand)"),
                    package
                )
                brand_name = next(brand["brand"] for brand in brands_data if brand["id_brand"] == package["id_brand"])
                print(f"✅ Created package: {package['nama_paket']} ({brand_name}) - Rp {package['harga']:,}")
            except Exception as e:
                print(f"⚠️ Could not create package {package['nama_paket']}: {e}")

        # Create Mikrotik Servers from backup (simplified schema)
        print("🖥️ Creating Mikrotik servers from backup...")
        try:
            mikrotik_match = re.search(r'INSERT INTO \`mikrotik_servers\` VALUES (.*?);', content, re.DOTALL)
            if mikrotik_match:
                mikrotik_values = mikrotik_match.group(1)
                # Parse manually
                records = mikrotik_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 8 parts for mikrotik_servers (simplified)
                        if len(parts) >= 8:
                            mikrotik_data = {
                                "id": int(parts[0]),
                                "name": parts[1].strip("'"),
                                "host_ip": parts[2].strip("'"),
                                "username": parts[3].strip("'"),
                                "password": parts[4].strip("'"),
                                "port": int(parts[5]),
                                "ros_version": parts[6].strip("'"),
                                "is_active": bool(int(parts[7]))
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO mikrotik_servers (id, name, host_ip, username, password, port, ros_version, is_active)
                                    VALUES (:id, :name, :host_ip, :username, :password, :port, :ros_version, :is_active)
                                """),
                                mikrotik_data
                            )
                            created_count += 1
                            print(f"✅ Created Mikrotik server: {mikrotik_data['name']} ({mikrotik_data['host_ip']})")
                    except Exception as e:
                        print(f"⚠️ Could not create Mikrotik server: {e}")

                print(f"✅ Created {created_count} Mikrotik servers from backup")
            else:
                print("⚠️ No Mikrotik servers found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading Mikrotik servers: {e}")

        # Create Customers (pelanggan) from backup
        print("👥 Creating customers from backup...")
        try:
            with open("DATABASE-EXISTING/backup_seed20251102.sql", 'r', encoding='utf-8') as f:
                content = f.read()

            # Find INSERT statements for pelanggan
            pelanggan_match = re.search(r'INSERT INTO \`pelanggan\` VALUES (.*?);', content, re.DOTALL)
            if pelanggan_match:
                pelanggan_values = pelanggan_match.group(1)
                # Parse manually since regex is complex with quoted strings containing commas
                records = pelanggan_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have 17 parts
                        if len(parts) >= 16:
                            customer_id = int(parts[0])
                            no_ktp = parts[1].strip("'") if parts[1] != 'NULL' else None
                            nama = parts[2].strip("'")
                            alamat = parts[3].strip("'")
                            alamat_custom = parts[4].strip("'") if parts[4] != 'NULL' else None  # FIXED: Tambah alamat_custom
                            alamat_2 = parts[5].strip("'") if parts[5] != 'NULL' else None  # This is actually tgl_instalasi in database
                            tgl_instalasi = parts[6].strip("'") if parts[6] != 'NULL' else None
                            blok = parts[7].strip("'")
                            unit = parts[8].strip("'")
                            no_telp = parts[9].strip("'")
                            email = parts[10].strip("'")
                            id_brand = parts[11].strip("'") if parts[11] != 'NULL' else None
                            layanan = parts[12].strip("'") if parts[12] != 'NULL' else None
                            # parts[13] is NULL for brand_default
                            # parts[14] is NULL for mikrotik_server_id
                            created_at = parts[15].strip("'") if len(parts) > 15 and parts[15] != 'NULL' else None
                            updated_at = parts[16].strip("'") if len(parts) > 16 and parts[16] != 'NULL' else None

                            customer_data = {
                                "id": customer_id,
                                "no_ktp": no_ktp,
                                "nama": nama,
                                "alamat": alamat,
                                "alamat_custom": alamat_custom,  # FIXED: Tambah alamat_custom
                                "alamat_2": alamat_2,
                                "tgl_instalasi": tgl_instalasi,
                                "blok": blok,
                                "unit": unit,
                                "no_telp": no_telp,
                                "email": email,
                                "id_brand": id_brand,
                                "layanan": layanan,
                                "created_at": created_at,
                                "updated_at": updated_at
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO pelanggan (id, no_ktp, nama, alamat, alamat_custom, alamat_2, tgl_instalasi, blok, unit, no_telp, email, id_brand, layanan, created_at, updated_at)
                                    VALUES (:id, :no_ktp, :nama, :alamat, :alamat_custom, :alamat_2, :tgl_instalasi, :blok, :unit, :no_telp, :email, :id_brand, :layanan, :created_at, :updated_at)
                                """),
                                customer_data
                            )
                            created_count += 1
                            if created_count <= 10:  # Show first 10 for readability
                                print(f"✅ Created customer: {nama} (ID: {customer_id})")
                    except Exception as e:
                        print(f"⚠️ Could not parse customer record: {e}")

                print(f"✅ Created {created_count} customers from backup")
            else:
                print("⚠️ No customers found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading customers from backup: {e}")

        # Create Subscriptions (langganan) from backup
        print("📋 Creating subscriptions from backup...")
        try:
            # Find INSERT statements for langganan
            langganan_match = re.search(r'INSERT INTO \`langganan\` VALUES (.*?);', content, re.DOTALL)
            if langganan_match:
                langganan_values = langganan_match.group(1)
                # Parse manually similar to customers
                records = langganan_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 10 parts for langganan
                        if len(parts) >= 10:
                            subscription_data = {
                                "id": int(parts[0]),
                                "pelanggan_id": int(parts[1]),
                                "paket_layanan_id": int(parts[2]),
                                "tgl_jatuh_tempo": parts[3].strip("'") if parts[3] != 'NULL' else None,
                                "tgl_invoice_terakhir": None if parts[4] == 'NULL' else parts[4].strip("'"),
                                "metode_pembayaran": parts[5].strip("'"),
                                "harga_awal": float(parts[6]),
                                "status": parts[7].strip("'"),
                                "created_at": parts[8].strip("'"),
                                "updated_at": parts[9].strip("'") if len(parts) > 9 else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO langganan (id, pelanggan_id, paket_layanan_id, tgl_jatuh_tempo, tgl_invoice_terakhir, metode_pembayaran, harga_awal, status, created_at, updated_at)
                                    VALUES (:id, :pelanggan_id, :paket_layanan_id, :tgl_jatuh_tempo, :tgl_invoice_terakhir, :metode_pembayaran, :harga_awal, :status, :created_at, :updated_at)
                                """),
                                subscription_data
                            )
                            created_count += 1
                            if created_count <= 10:  # Show first 10 for readability
                                print(f"✅ Created subscription ID: {subscription_data['id']} for customer: {subscription_data['pelanggan_id']}")
                    except Exception as e:
                        print(f"⚠️ Could not create subscription: {e}")

                print(f"✅ Created {created_count} subscriptions from backup")
            else:
                print("⚠️ No subscriptions found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading subscriptions from backup: {e}")

        # Create Invoices from backup (all invoices)
        print("📄 Creating invoices from backup...")
        try:
            # Find INSERT statements for invoices
            invoices_match = re.search(r'INSERT INTO `invoices` VALUES (.*?);', content, re.DOTALL)
            if invoices_match:
                invoices_values = invoices_match.group(1)
                # Parse manually
                records = invoices_values.split('),(')

                created_count = 0
                for record in records:  # Import all invoices
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 20 parts for invoices
                        if len(parts) >= 15:
                            invoice_data = {
                                "id": int(parts[0]),
                                "no_invoice": parts[1].strip("'"),
                                "id_pelanggan": int(parts[2]),
                                "kode_pelanggan": parts[3].strip("'"),
                                "brand": parts[4].strip("'"),
                                "jumlah_tagihan": float(parts[5]),
                                "no_telepon": parts[6].strip("'"),
                                "email": parts[7].strip("'"),
                                "tanggal_terbit": parts[8].strip("'"),
                                "tanggal_jatuh_tempo": parts[9].strip("'"),
                                "status": parts[10].strip("'"),
                                "payment_url": parts[11].strip("'") if parts[11] != 'NULL' else None,
                                # Skip positions 12 and 13 (NULL values in old database)
                                "xendit_id": parts[14].strip("'") if len(parts) > 14 and parts[14] != 'NULL' else None,
                                "file_path": parts[15].strip("'") if len(parts) > 15 and parts[15] != 'NULL' else None,
                                "paid_amount": float(parts[16]) if len(parts) > 16 and parts[16] != 'NULL' else None,
                                "paid_date": parts[17].strip("'") if len(parts) > 17 and parts[17] != 'NULL' else None,
                                # Field berikutnya ada di old data: retry_count (18), created_at (19), updated_at (20)
                                # Tapi kita tidak perlu retry_count karena ini fitur baru
                                "created_at": parts[19].strip("'") if len(parts) > 19 else None,
                                "updated_at": parts[20].strip("'") if len(parts) > 20 else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO invoices (id, invoice_number, pelanggan_id, id_pelanggan, brand, total_harga, no_telp, email,
                                                     tgl_invoice, tgl_jatuh_tempo, status_invoice, payment_link, xendit_id, xendit_external_id,
                                                     paid_amount, paid_at, is_processing, xendit_retry_count, xendit_last_retry,
                                                     xendit_error_message, xendit_status, created_at, updated_at)
                                    VALUES (:id, :no_invoice, :id_pelanggan, :kode_pelanggan, :brand, :jumlah_tagihan, :no_telepon, :email,
                                            :tanggal_terbit, :tanggal_jatuh_tempo, :status, :payment_url, :xendit_id, :xendit_external_id,
                                            :paid_amount, :paid_date, :is_processing, :xendit_retry_count, :xendit_last_retry,
                                            :xendit_error_message, :xendit_status, :created_at, :updated_at)
                                """),
                                {
                                    **invoice_data,
                                    "xendit_external_id": invoice_data["file_path"],  # Map file_path to xendit_external_id
                                    "is_processing": False,  # Default value for is_processing
                                    "xendit_retry_count": 0,  # Data lama tidak punya retry history
                                    "xendit_last_retry": None,  # Data lama tidak punya retry history
                                    "xendit_error_message": None,  # Data lama tidak punya error message
                                    "xendit_status": "completed"  # Data lama dianggap completed
                                }
                            )
                            created_count += 1
                            print(f"✅ Created invoice: {invoice_data['no_invoice']} ({invoice_data['status']})")
                    except Exception as e:
                        print(f"⚠️ Could not create invoice: {e}")

                print(f"✅ Created {created_count} invoices from backup")
            else:
                print("⚠️ No invoices found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading invoices from backup: {e}")

        
        # Create Users from backup (update existing users section)
        print("👤 Creating users from backup...")
        try:
            users_match = re.search(r'INSERT INTO \`users\` VALUES (.*?);', content, re.DOTALL)
            if users_match:
                users_values = users_match.group(1)
                # Parse manually
                records = users_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 13 parts for users
                        if len(parts) >= 11:
                            user_data = {
                                "id": int(parts[0]),
                                "name": parts[1].strip("'"),
                                "email": parts[2].strip("'"),
                                "email_verified_at": None if parts[3] == 'NULL' else parts[3].strip("'"),
                                "password": parts[4].strip("'"),
                                "remember_token": None if parts[5] == 'NULL' else parts[5].strip("'"),
                                "created_at": parts[6].strip("'"),
                                "updated_at": parts[7].strip("'"),
                                "role_id": int(parts[8]),
                                "revoked_before": None if parts[9] == 'NULL' else parts[9],
                                "password_changed_at": None if parts[10] == 'NULL' else parts[10].strip("'"),
                                "is_active": bool(int(parts[11])) if len(parts) > 11 else True
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO users (id, name, email, email_verified_at, password, remember_token,
                                                  created_at, updated_at, role_id, revoked_before, password_changed_at, is_active)
                                    VALUES (:id, :name, :email, :email_verified_at, :password, :remember_token,
                                            :created_at, :updated_at, :role_id, :revoked_before, :password_changed_at, :is_active)
                                """),
                                user_data
                            )
                            created_count += 1
                            if created_count <= 5:  # Show first 5 for readability
                                print(f"✅ Created user: {user_data['name']} ({user_data['email']})")
                    except Exception as e:
                        print(f"⚠️ Could not create user: {e}")

                print(f"✅ Created {created_count} users from backup")
            else:
                print("⚠️ No users found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading users from backup: {e}")

        # Create Activity Logs from backup (after users to satisfy foreign key constraint)
        print("📋 Creating activity logs from backup...")
        try:
            # Find INSERT statements for activity_logs
            activity_match = re.search(r'INSERT INTO `activity_logs` VALUES (.+?);\s*UNLOCK TABLES', content, re.DOTALL)
            if activity_match:
                activity_values = activity_match.group(1)

                # Split by '),(' and manually parse
                records = activity_values.split('),(')
                created_count = 0

                for record in records:  # Import all activity logs
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 4 parts for activity_logs
                        if len(parts) >= 4:
                            activity_data = {
                                "id": int(parts[0]),
                                "user_id": int(parts[1]),
                                "timestamp": parts[2].strip("'"),
                                "action": parts[3].strip("'"),
                                "details": parts[4].strip("'") if len(parts) > 4 and parts[4] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO activity_logs (id, user_id, timestamp, action, details)
                                    VALUES (:id, :user_id, :timestamp, :action, :details)
                                """),
                                activity_data
                            )
                            created_count += 1
                            if created_count <= 20:  # Show first 20 for brevity
                                print(f"✅ Created activity log: {activity_data['action']} by user {activity_data['user_id']}")
                    except Exception as e:
                        print(f"⚠️ Could not create activity log: {e}")

                print(f"✅ Created {created_count} activity logs from backup")
            else:
                print("⚠️ No activity logs found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading activity logs from backup: {e}")

        # Create Data Teknis from backup (using correct schema without created_at)
        print("🔧 Creating data_teknis from backup...")
        try:
            data_teknis_match = re.search(r'INSERT INTO \`data_teknis\` VALUES (.*?);', content, re.DOTALL)
            if data_teknis_match:
                data_teknis_values = data_teknis_match.group(1)
                # Parse manually
                records = data_teknis_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 15 parts for data_teknis (old schema)
                        if len(parts) >= 15:
                            olt_name = parts[7].strip("'")  # Get OLT name

                            # Map OLT names to Mikrotik server IDs
                            olt_mikrotik_mapping = {
                                "Tambun": 1,      # Mikrotik server ID 1
                                "Pinus": 2,       # Mikrotik server ID 2
                                "Waringin": 3,    # Mikrotik server ID 3
                                "Nagrak": 4,      # Mikrotik server ID 4
                                "Pulogebang": 5,  # Mikrotik server ID 5
                                "Parama": 6,      # Mikrotik server ID 6
                                "Tipar Cakung": 7  # Mikrotik server ID 7
                            }

                            teknis_data = {
                                "id": int(parts[0]),                           # 1st field: id
                                "pelanggan_id": int(parts[1]),                 # 2nd field: pelanggan_id
                                "id_pelanggan": parts[3].strip("'"),           # 3rd field: id_pelanggan = PPPoE username (TMB-MGG-109-Yusuf)
                                "password_pppoe": parts[4].strip("'"),         # 4th field: password_pppoe
                                "profile_pppoe": parts[6].strip("'"),          # 5th field: profile_pppoe
                                "ip_pelanggan": parts[5].strip("'"),           # 6th field: ip_pelanggan
                                "id_vlan": parts[2].strip("'"),                # 7th field: id_vlan
                                "olt": parts[7].strip("'"),                    # 8th field: olt
                                "olt_custom": parts[8].strip("'") if parts[8].strip("'") else None,  # 9th field: olt_custom
                                "pon": None,                                   # 10th field: pon
                                "otb": None,                                   # 11th field: otb
                                "odc": None,                                   # 12th field: odc
                                "odp_id": None,                                # 13th field: odp_id
                                "port_odp": None,                              # 14th field: port_odp
                                "sn": None,                                    # 15th field: sn
                                "onu_power": None if parts[14] == 'NULL' else int(parts[14]),  # 16th field: onu_power
                                "speedtest_proof": None if parts[15] == 'NULL' else parts[15].strip("'"),  # 17th field: speedtest_proof
                                "mikrotik_sync_pending": False,                # 18th field: mikrotik_sync_pending
                                "mikrotik_server_id": olt_mikrotik_mapping.get(olt_name, None)  # 19th field: mikrotik_server_id
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO data_teknis (id, pelanggan_id, id_pelanggan, password_pppoe, profile_pppoe, ip_pelanggan, id_vlan, olt,
                                                       olt_custom, pon, otb, odc, odp_id, port_odp, sn, onu_power, speedtest_proof,
                                                       mikrotik_sync_pending, mikrotik_server_id)
                                    VALUES (:id, :pelanggan_id, :id_pelanggan, :password_pppoe, :profile_pppoe, :ip_pelanggan, :id_vlan, :olt,
                                            :olt_custom, :pon, :otb, :odc, :odp_id, :port_odp, :sn, :onu_power, :speedtest_proof,
                                            :mikrotik_sync_pending, :mikrotik_server_id)
                                """),
                                teknis_data
                            )
                            created_count += 1
                            if created_count <= 5:  # Show first 5 for readability
                                print(f"✅ Created data_teknis for customer: {teknis_data['pelanggan_id']} - {teknis_data['id_pelanggan']} (OLT: {teknis_data['olt']})")
                    except Exception as e:
                        print(f"⚠️ Could not create data_teknis: {e}")

                print(f"✅ Created {created_count} data_teknis from backup")
            else:
                print("⚠️ No data_teknis found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading data_teknis: {e}")

        # Create ODP data from backup
        print("📡 Creating ODP data from backup...")
        try:
            odp_match = re.search(r'INSERT INTO \`odp\` VALUES (.*?);', content, re.DOTALL)
            if odp_match:
                odp_values = odp_match.group(1)
                # Parse manually
                records = odp_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 7 parts for ODP (sesuai schema)
                        if len(parts) >= 7:
                            odp_data = {
                                "id": int(parts[0]),
                                "kode_odp": parts[1].strip("'"),  # FIXED: kode_odp bukan nama_odp
                                "alamat": parts[2].strip("'"),
                                "kapasitas_port": int(parts[3]),  # FIXED: kapasitas_port bukan kapasitas
                                "latitude": float(parts[4]) if parts[4] != 'NULL' else None,
                                "longitude": float(parts[5]) if parts[5] != 'NULL' else None,
                                "parent_odp_id": None,  # FIXED: field ini ada di schema
                                "olt_id": int(parts[7]) if len(parts) > 7 and parts[7] != 'NULL' else None  # FIXED: olt_id bukan mikrotik_server_id
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO odp (id, kode_odp, alamat, kapasitas_port, latitude, longitude, parent_odp_id, olt_id)
                                    VALUES (:id, :kode_odp, :alamat, :kapasitas_port, :latitude, :longitude, :parent_odp_id, :olt_id)
                                """),
                                odp_data
                            )
                            created_count += 1
                            print(f"✅ Created ODP: {odp_data['kode_odp']} - {odp_data['alamat']}")
                    except Exception as e:
                        print(f"⚠️ Could not create ODP: {e}")

                print(f"✅ Created {created_count} ODP from backup")
            else:
                print("⚠️ No ODP data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading ODP: {e}")

        # Create OLT data from backup
        print("🌐 Creating OLT data from backup...")
        try:
            olt_match = re.search(r'INSERT INTO \`olt\` VALUES (.*?);', content, re.DOTALL)
            if olt_match:
                olt_values = olt_match.group(1)
                # Parse manually
                records = olt_values.split('),(')

                created_count = 0
                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Simple split by comma and clean quotes/NULL
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 7 parts for OLT (sesuai schema)
                        if len(parts) >= 6:
                            olt_data = {
                                "id": int(parts[0]),
                                "nama_olt": parts[1].strip("'"),
                                "ip_address": parts[2].strip("'"),  # FIXED: ip_address bukan ip_olt
                                "tipe_olt": parts[3].strip("'"),  # FIXED: tipe_olt bukan merk
                                "username": parts[4].strip("'"),
                                "password": parts[5].strip("'"),
                                "mikrotik_server_id": int(parts[6]) if len(parts) > 6 and parts[6] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO olt (id, nama_olt, ip_address, tipe_olt, username, password, mikrotik_server_id)
                                    VALUES (:id, :nama_olt, :ip_address, :tipe_olt, :username, :password, :mikrotik_server_id)
                                """),
                                olt_data
                            )
                            created_count += 1
                            print(f"✅ Created OLT: {olt_data['nama_olt']} ({olt_data['ip_address']})")
                    except Exception as e:
                        print(f"⚠️ Could not create OLT: {e}")

                print(f"✅ Created {created_count} OLT from backup")
            else:
                print("⚠️ No OLT data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading OLT: {e}")

        # Create Action Taken data if exists
        print("🔧 Creating action_taken data from backup...")
        try:
            action_taken_match = re.search(r'INSERT INTO \`action_taken\` VALUES (.*?);', content, re.DOTALL)
            if action_taken_match:
                print("✅ Found action_taken data in backup (parsing skipped for now - table may not exist in current schema)")
            else:
                print("⚠️ No action_taken data found")
        except Exception as e:
            print(f"⚠️ Error reading action_taken: {e}")

        # Create Syarat & Ketentuan from backup
        print("📋 Creating syarat_ketentuan from backup...")
        try:
            syarat_match = re.search(r'INSERT INTO \`syarat_ketentuan\` VALUES (.*?);', content, re.DOTALL)
            if syarat_match:
                syarat_values = syarat_match.group(1)
                
                # Count how many records we expect
                expected_count = syarat_values.count('),(') + 1
                print(f"🔍 Found {expected_count} Syarat & Ketentuan records in backup")
                
                # Simple approach: split by '),(' and fix first/last records
                raw_records = syarat_values.split('),(')
                records = []
                
                for i, raw_record in enumerate(raw_records):
                    # Clean up the record
                    record = raw_record.strip()
                    
                    # Fix the first record (remove leading '(')
                    if i == 0 and record.startswith('('):
                        record = record[1:]
                    
                    # Fix the last record (remove trailing ')')
                    if i == len(raw_records) - 1 and record.endswith(')'):
                        record = record[:-1]
                    
                    records.append(record)
                
                print(f"📄 Parsed {len(records)} Syarat & Ketentuan records")
                
                created_count = 0
                failed_count = 0
                
                for idx, record in enumerate(records):
                    try:
                        # Parse the record into parts
                        # We need to split by ',' but respect quotes
                        parts = []
                        current_part = ""
                        in_quotes = False
                        escape_next = False
                        
                        i = 0
                        while i < len(record):
                            char = record[i]
                            
                            if escape_next:
                                current_part += char
                                escape_next = False
                            elif char == '\\' and not escape_next:
                                escape_next = True
                                current_part += char
                            elif char == "'" and not escape_next:
                                in_quotes = not in_quotes
                                current_part += char
                            elif char == ',' and not in_quotes:
                                parts.append(current_part.strip())
                                current_part = ""
                            else:
                                current_part += char
                            
                            i += 1
                        
                        # Add the last part
                        if current_part:
                            parts.append(current_part.strip())
                        
                        # Should have at least 6 parts (id, judul, konten, tipe, versi, created_at)
                        if len(parts) >= 6:
                            # Clean the data properly
                            def clean_sql_value(value):
                                """Clean SQL value by removing quotes and handling NULL"""
                                if value is None:
                                    return None
                                if isinstance(value, str) and value.upper() == 'NULL':
                                    return None
                                if isinstance(value, str) and value.startswith("'") and value.endswith("'"):
                                    value = value[1:-1]
                                # Handle escaped quotes
                                if isinstance(value, str):
                                    value = value.replace("\\'", "'").replace('\\"', '"')
                                return value
                            
                            # Extract and clean values with special attention to datetime
                            id_val = clean_sql_value(parts[0])
                            judul_val = clean_sql_value(parts[1]) or ""
                            konten_val = clean_sql_value(parts[2]) or ""
                            tipe_val = clean_sql_value(parts[3]) or ""
                            versi_val = clean_sql_value(parts[4])
                            
                            # Handle datetime specially - it might have extra quotes or characters
                            created_at_val = clean_sql_value(parts[5]) if len(parts) > 5 else None
                            if created_at_val and isinstance(created_at_val, str):
                                # Clean up any extra quotes or characters
                                created_at_val = created_at_val.strip().strip("'").strip('"')
                                # Handle cases where datetime might have trailing characters
                                if created_at_val.endswith("'))"):
                                    created_at_val = created_at_val[:-3]
                                elif created_at_val.endswith("')"):
                                    created_at_val = created_at_val[:-2]
                            
                            syarat_data = {
                                "id": int(id_val) if id_val else 0,
                                "judul": judul_val,
                                "konten": konten_val,
                                "tipe": tipe_val,
                                "versi": versi_val,
                                "created_at": created_at_val
                            }
                            
                            # Additional cleaning for special characters to prevent encoding issues
                            if syarat_data["konten"]:
                                # Remove or replace problematic UTF-8 characters
                                syarat_data["konten"] = re.sub(r'[^\x00-\x7F\xA0-\uFFFF\w\s\-\.\,\!\?\;\:\(\)\[\]\{\}\<\>\/\+\=\*\&\|\^\%\$\#\@\!\~\`\\"\'\n\r\t]', ' ', syarat_data["konten"])
                                # Replace some known problematic sequences
                                syarat_data["konten"] = syarat_data["konten"].replace('\\xE2\\x9C\\xA8', ' ').replace('\\xE2\\x9C\\xA8', ' ').replace('\u2728', ' ').replace('✨', ' ')
                            
                            if syarat_data["judul"]:
                                syarat_data["judul"] = re.sub(r'[^\x00-\x7F\xA0-\uFFFF\w\s\-\.\,\!\?\;\:\(\)\[\]\{\}\<\>\/\+\=\*\&\|\^\%\$\#\@\!\~\`\\"\'\n\r\t]', ' ', syarat_data["judul"])
                                syarat_data["judul"] = syarat_data["judul"].replace('\\xE2\\x9C\\xA8', ' ').replace('\\xE2\\x9C\\xA8', ' ').replace('\u2728', ' ').replace('✨', ' ')
                            
                            await conn.execute(
                                text("""
                                    INSERT INTO syarat_ketentuan (id, judul, konten, tipe, versi, created_at)
                                    VALUES (:id, :judul, :konten, :tipe, :versi, :created_at)
                                """),
                                syarat_data
                            )
                            created_count += 1
                            print(f"✅ Created Syarat & Ketentuan: {syarat_data['judul'][:50]}...")
                        else:
                            print(f"⚠️ Skipping record {idx+1}: Insufficient parts ({len(parts)})")
                            failed_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Could not create Syarat & Ketentuan record {idx+1}: {e}")
                        failed_count += 1
                
                print(f"✅ Successfully created {created_count} Syarat & Ketentuan from backup")
                if failed_count > 0:
                    print(f"⚠️ Failed to create {failed_count} Syarat & Ketentuan records")
            else:
                print("⚠️ No syarat_ketentuan data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading syarat_ketentuan: {e}")
            import traceback
            traceback.print_exc()

        print("✅ All available data imported from backup!")

        # Create Token Blacklist from backup
        print("🔑 Creating token blacklist from backup...")
        try:
            # Find INSERT statements for token_blacklist
            token_match = re.search(r'INSERT INTO `token_blacklist` VALUES (.*?);', content, re.DOTALL)
            if token_match:
                token_values = token_match.group(1)

                # Split by '),(' and manually parse
                records = token_values.split('),(')
                created_count = 0

                for record in records:  # Import all token blacklist entries
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 9 parts for token_blacklist
                        if len(parts) >= 9:
                            token_data = {
                                "id": int(parts[0]),
                                "jti": parts[1].strip("'"),
                                "user_id": int(parts[2]),
                                "token_type": parts[3].strip("'"),
                                "expires_at": parts[4].strip("'"),
                                "created_at": parts[5].strip("'"),
                                "revoked": int(parts[6]) if parts[6] != 'NULL' else False,
                                "revoked_at": parts[7].strip("'") if len(parts) > 7 and parts[7] != 'NULL' else None,
                                "revoked_reason": parts[8].strip("'") if len(parts) > 8 and parts[8] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO token_blacklist (id, jti, user_id, token_type, expires_at, created_at, revoked, revoked_at, revoked_reason)
                                    VALUES (:id, :jti, :user_id, :token_type, :expires_at, :created_at, :revoked, :revoked_at, :revoked_reason)
                                """),
                                token_data
                            )
                            created_count += 1
                    except Exception as e:
                        print(f"⚠️ Could not create token blacklist entry: {e}")

                print(f"✅ Created {created_count} token blacklist entries from backup")
            else:
                print("⚠️ No token blacklist data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading token blacklist from backup: {e}")

        # Create Payment Callback Logs from backup
        print("💳 Creating payment callback logs from backup...")
        try:
            # Find INSERT statements for payment_callback_logs
            payment_match = re.search(r'INSERT INTO `payment_callback_logs` VALUES (.*?);', content, re.DOTALL)
            if payment_match:
                payment_values = payment_match.group(1)

                # Split by '),(' and manually parse
                records = payment_values.split('),(')
                created_count = 0

                for record in records:  # Import all payment callback logs
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 6 parts for payment_callback_logs
                        if len(parts) >= 6:
                            callback_data = parts[4].strip("'")
                            # Truncate callback_data to 900 characters to fit in varchar(1000)
                            if len(callback_data) > 900:
                                callback_data = callback_data[:900] + "... [truncated]"

                            payment_data = {
                                "id": int(parts[0]),
                                "idempotency_key": parts[1].strip("'") if parts[1] != 'NULL' else None,
                                "xendit_id": parts[2].strip("'"),
                                "external_id": parts[3].strip("'"),
                                "callback_data": callback_data,
                                "status": parts[5].strip("'"),
                                "processed_at": parts[6].strip("'"),
                                "created_at": parts[7].strip("'") if len(parts) > 7 else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO payment_callback_logs (id, idempotency_key, xendit_id, external_id, callback_data, status, processed_at, created_at)
                                    VALUES (:id, :idempotency_key, :xendit_id, :external_id, :callback_data, :status, :processed_at, :created_at)
                                """),
                                payment_data
                            )
                            created_count += 1
                            if created_count <= 10:  # Show first 10 for brevity
                                print(f"✅ Created payment callback: {payment_data['xendit_id']} - {payment_data['status']}")
                    except Exception as e:
                        print(f"⚠️ Could not create payment callback log: {e}")

                print(f"✅ Created {created_count} payment callback logs from backup")
            else:
                print("⚠️ No payment callback logs found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading payment callback logs from backup: {e}")

        # Create OLT from backup
        print("🖥️ Creating OLT from backup...")
        try:
            # Find INSERT statements for olt
            olt_match = re.search(r'INSERT INTO `olt` VALUES (.*?);', content, re.DOTALL)
            if olt_match:
                olt_values = olt_match.group(1)

                # Split by '),(' and manually parse
                records = olt_values.split('),(')
                created_count = 0

                for record in records:  # Import all OLT
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 6 parts for olt
                        if len(parts) >= 6:
                            olt_data = {
                                "id": int(parts[0]),
                                "nama_olt": parts[1].strip("'"),
                                "ip_address": parts[2].strip("'"),
                                "tipe_olt": parts[3].strip("'"),
                                "username": parts[4].strip("'"),
                                "password": parts[5].strip("'"),
                                "mikrotik_server_id": int(parts[6]) if len(parts) > 6 and parts[6] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO olt (id, nama_olt, ip_address, tipe_olt, username, password, mikrotik_server_id)
                                    VALUES (:id, :nama_olt, :ip_address, :tipe_olt, :username, :password, :mikrotik_server_id)
                                """),
                                olt_data
                            )
                            created_count += 1
                            print(f"✅ Created OLT: {olt_data['nama_olt']} ({olt_data['ip_address']})")
                    except Exception as e:
                        print(f"⚠️ Could not create OLT: {e}")

                print(f"✅ Created {created_count} OLT from backup")
            else:
                print("⚠️ No OLT data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading OLT from backup: {e}")

        # Create ODP from backup
        print("📦 Creating ODP from backup...")
        try:
            # Find INSERT statements for odp
            odp_match = re.search(r'INSERT INTO `odp` VALUES (.*?);', content, re.DOTALL)
            if odp_match:
                odp_values = odp_match.group(1)

                # Split by '),(' and manually parse
                records = odp_values.split('),(')
                created_count = 0

                for record in records:  # Import all ODP
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 7 parts for odp
                        if len(parts) >= 7:
                            odp_data = {
                                "id": int(parts[0]),
                                "kode_odp": parts[1].strip("'"),
                                "alamat": parts[2].strip("'"),
                                "kapasitas_port": int(parts[3]),
                                "latitude": float(parts[4]) if parts[4] != 'NULL' else None,
                                "longitude": float(parts[5]) if parts[5] != 'NULL' else None,
                                "parent_odp_id": parts[6].strip("'") if len(parts) > 6 and parts[6] != 'NULL' else None,
                                "olt_id": int(parts[7]) if len(parts) > 7 and parts[7] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO odp (id, kode_odp, alamat, kapasitas_port, latitude, longitude, parent_odp_id, olt_id)
                                    VALUES (:id, :kode_odp, :alamat, :kapasitas_port, :latitude, :longitude, :parent_odp_id, :olt_id)
                                """),
                                odp_data
                            )
                            created_count += 1
                            print(f"✅ Created ODP: {odp_data['kode_odp']} - {odp_data['alamat']}")
                    except Exception as e:
                        print(f"⚠️ Could not create ODP: {e}")

                print(f"✅ Created {created_count} ODP from backup")
            else:
                print("⚠️ No ODP data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading ODP from backup: {e}")

        # Create Trouble Ticket data from backup
        print("🎫 Creating trouble_ticket from backup...")
        try:
            trouble_ticket_match = re.search(r'INSERT INTO `trouble_ticket` VALUES (.*?);', content, re.DOTALL)
            if trouble_ticket_match:
                trouble_ticket_values = trouble_ticket_match.group(1)
                # Split by '),(' and manually parse
                records = trouble_ticket_values.split('),(')
                created_count = 0

                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 8 parts for trouble_ticket
                        if len(parts) >= 8:
                            ticket_data = {
                                "id": int(parts[0]),
                                "pelanggan_id": int(parts[1]) if parts[1] != 'NULL' else None,
                                "subject": parts[2].strip("'"),
                                "description": parts[3].strip("'") if parts[3] != 'NULL' else None,
                                "status": parts[4].strip("'"),
                                "priority": parts[5].strip("'") if parts[5] != 'NULL' else None,
                                "assigned_to": int(parts[6]) if parts[6] != 'NULL' else None,
                                "created_at": parts[7].strip("'") if len(parts) > 7 else None,
                                "updated_at": parts[8].strip("'") if len(parts) > 8 else None,
                                "resolved_at": parts[9].strip("'") if len(parts) > 9 and parts[9] != 'NULL' else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO trouble_ticket (id, pelanggan_id, subject, description, status, priority, assigned_to, created_at, updated_at, resolved_at)
                                    VALUES (:id, :pelanggan_id, :subject, :description, :status, :priority, :assigned_to, :created_at, :updated_at, :resolved_at)
                                """),
                                ticket_data
                            )
                            created_count += 1
                            print(f"✅ Created trouble ticket: {ticket_data['subject'][:50]}...")
                    except Exception as e:
                        print(f"⚠️ Could not create trouble ticket: {e}")

                print(f"✅ Created {created_count} trouble tickets from backup")
            else:
                print("⚠️ No trouble ticket data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading trouble tickets: {e}")

        # Create Ticket History data from backup
        print("📝 Creating ticket_history from backup...")
        try:
            ticket_history_match = re.search(r'INSERT INTO `ticket_history` VALUES (.*?);', content, re.DOTALL)
            if ticket_history_match:
                ticket_history_values = ticket_history_match.group(1)
                # Split by '),(' and manually parse
                records = ticket_history_values.split('),(')
                created_count = 0

                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 6 parts for ticket_history
                        if len(parts) >= 6:
                            history_data = {
                                "id": int(parts[0]),
                                "ticket_id": int(parts[1]),
                                "user_id": int(parts[2]) if parts[2] != 'NULL' else None,
                                "action": parts[3].strip("'"),
                                "description": parts[4].strip("'") if parts[4] != 'NULL' else None,
                                "created_at": parts[5].strip("'")
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO ticket_history (id, ticket_id, user_id, action, description, created_at)
                                    VALUES (:id, :ticket_id, :user_id, :action, :description, :created_at)
                                """),
                                history_data
                            )
                            created_count += 1
                    except Exception as e:
                        print(f"⚠️ Could not create ticket history: {e}")

                print(f"✅ Created {created_count} ticket history records from backup")
            else:
                print("⚠️ No ticket history data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading ticket history: {e}")

        # Create Traffic History data from backup
        print("📊 Creating traffic_history from backup...")
        try:
            traffic_match = re.search(r'INSERT INTO `traffic_history` VALUES (.*?);', content, re.DOTALL)
            if traffic_match:
                traffic_values = traffic_match.group(1)
                # Split by '),(' and manually parse
                records = traffic_values.split('),(')
                created_count = 0

                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 8 parts for traffic_history
                        if len(parts) >= 8:
                            traffic_data = {
                                "id": int(parts[0]),
                                "pelanggan_id": int(parts[1]) if parts[1] != 'NULL' else None,
                                "data_teknis_id": int(parts[2]) if parts[2] != 'NULL' else None,
                                "download_bytes": int(parts[3]) if parts[3] != 'NULL' else 0,
                                "upload_bytes": int(parts[4]) if parts[4] != 'NULL' else 0,
                                "total_bytes": int(parts[5]) if parts[5] != 'NULL' else 0,
                                "recorded_at": parts[6].strip("'") if parts[6] != 'NULL' else None,
                                "created_at": parts[7].strip("'") if len(parts) > 7 else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO traffic_history (id, pelanggan_id, data_teknis_id, download_bytes, upload_bytes, total_bytes, recorded_at, created_at)
                                    VALUES (:id, :pelanggan_id, :data_teknis_id, :download_bytes, :upload_bytes, :total_bytes, :recorded_at, :created_at)
                                """),
                                traffic_data
                            )
                            created_count += 1
                    except Exception as e:
                        print(f"⚠️ Could not create traffic history: {e}")

                print(f"✅ Created {created_count} traffic history records from backup")
            else:
                print("⚠️ No traffic history data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading traffic history: {e}")

        # Create Inventory data from backup
        print("📦 Creating inventory_items from backup...")
        try:
            inventory_items_match = re.search(r'INSERT INTO `inventory_items` VALUES (.*?);', content, re.DOTALL)
            if inventory_items_match:
                inventory_items_values = inventory_items_match.group(1)
                # Split by '),(' and manually parse
                records = inventory_items_values.split('),(')
                created_count = 0

                for record in records:
                    try:
                        # Clean up the record
                        record = record.strip('(').strip(')').strip()

                        # Parse manually similar to other tables
                        parts = []
                        current = ''
                        in_quote = False
                        i = 0

                        while i < len(record):
                            char = record[i]
                            if char == "'" and (i == 0 or record[i-1] != '\\'):
                                in_quote = not in_quote
                            elif char == ',' and not in_quote:
                                parts.append(current)
                                current = ''
                                i += 1
                                continue
                            current += char
                            i += 1

                        if current:
                            parts.append(current)

                        # Should have at least 10 parts for inventory_items
                        if len(parts) >= 10:
                            item_data = {
                                "id": int(parts[0]),
                                "name": parts[1].strip("'"),
                                "type_id": int(parts[2]) if parts[2] != 'NULL' else None,
                                "status_id": int(parts[3]) if parts[3] != 'NULL' else None,
                                "serial_number": parts[4].strip("'") if parts[4] != 'NULL' else None,
                                "location": parts[5].strip("'") if parts[5] != 'NULL' else None,
                                "purchase_date": parts[6].strip("'") if parts[6] != 'NULL' else None,
                                "purchase_price": float(parts[7]) if parts[7] != 'NULL' else None,
                                "warranty_expiry": parts[8].strip("'") if parts[8] != 'NULL' else None,
                                "notes": parts[9].strip("'") if parts[9] != 'NULL' else None,
                                "created_at": parts[10].strip("'") if len(parts) > 10 else None,
                                "updated_at": parts[11].strip("'") if len(parts) > 11 else None
                            }

                            await conn.execute(
                                text("""
                                    INSERT INTO inventory_items (id, name, type_id, status_id, serial_number, location, purchase_date, purchase_price, warranty_expiry, notes, created_at, updated_at)
                                    VALUES (:id, :name, :type_id, :status_id, :serial_number, :location, :purchase_date, :purchase_price, :warranty_expiry, :notes, :created_at, :updated_at)
                                """),
                                item_data
                            )
                            created_count += 1
                            if created_count <= 10:  # Show first 10 for readability
                                print(f"✅ Created inventory item: {item_data['name']}")
                    except Exception as e:
                        print(f"⚠️ Could not create inventory item: {e}")

                print(f"✅ Created {created_count} inventory items from backup")
            else:
                print("⚠️ No inventory items data found in backup file")

        except Exception as e:
            print(f"⚠️ Error reading inventory items: {e}")

        # Reset auto-increment counters to ensure sequential IDs for new entries
        print("🔄 Resetting auto-increment counters...")
        
        # Get the current max ID to set the auto-increment correctly
        result = await conn.execute(text("SELECT MAX(id) FROM data_teknis"))
        max_id = result.scalar()
        if max_id:
            await conn.execute(text(f"ALTER TABLE data_teknis AUTO_INCREMENT = {max_id + 1}"))
            print(f"✅ Auto-increment for data_teknis set to {max_id + 1}")
        else:
            await conn.execute(text("ALTER TABLE data_teknis AUTO_INCREMENT = 1"))
            print("✅ Auto-increment for data_teknis reset to 1")

        await conn.commit()
        print("🎉 Seed data creation completed successfully!")

        print("\n📋 Summary:")
        print(f"   👥 Roles: 5 (Admin, Bos Gudang, Finance, NOC, Teknisi)")
        print(f"   🔐 Permissions: 124")
        print(f"   👤 Users: Multiple users (imported from backup)")
        print(f"   ⚙️ System Settings: 4")
        print(f"   📦 Brands: 3 (Jakinet, Jelantik, Jelantik Nagrak)")
        print(f"   📦 Packages: 12 (4 packages per brand)")
        print(f"   🖥️ Mikrotik Servers: 7 (imported from backup)")
        print(f"   👥 Customers: 400+ (imported from backup)")
        print(f"   📋 Subscriptions: 400+ (imported from backup)")
        print(f"   📄 Invoices: 500+ (imported from backup)")
        print(f"   🔧 Data Teknis: 400+ (imported from backup)")
        print(f"   🌐 OLT: Multiple OLT devices (imported from backup)")
        print(f"   📡 ODP: Multiple ODP locations (imported from backup)")
        print(f"   🎫 Trouble Tickets: (imported from backup)")
        print(f"   📝 Ticket History: (imported from backup)")
        print(f"   📊 Traffic History: (imported from backup)")
        print(f"   📦 Inventory Items: (imported from backup)")
        print(f"   📋 Activity Logs: (imported from backup)")
        print(f"   🔑 Token Blacklist: (imported from backup)")
        print(f"   💳 Payment Callback Logs: (imported from backup)")
        print(f"   📊 Syarat & Ketentuan: 13 records (imported from backup)")

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
