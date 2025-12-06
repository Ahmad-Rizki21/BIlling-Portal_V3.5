#!/usr/bin/env python3
"""
Simple Script untuk Check dan Suspend User per Lokasi
====================================================
Script yang lebih sederhana dan aman tanpa complex ORM imports
menggunakan SQL query langsung untuk menghindari model conflicts.

Features:
- Summary Suspended user per lokasi
- Simple batch suspend per lokasi
- Dry-run mode untuk testing
- Detail reporting

Usage:
1. python3 simple_suspend_checker.py --summary
2. python3 simple_suspend_checker.py --location waringin --dry-run
3. python3 simple_suspend_checker.py --location waringin --execute
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import database configuration from main app
from app.database import AsyncSessionLocal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

class SimpleSuspendProcessor:
    """Simple processor menggunakan raw SQL untuk avoid ORM issues"""

    def __init__(self, dry_run: bool = False, batch_size: int = 20):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.results = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'failed_details': [],
            'processed_locations': [],
            'start_time': datetime.now(),
            'end_time': None
        }

    async def get_suspended_summary(self, session):
        """Get summary Suspended user per lokasi menggunakan SQL"""
        query = text("""
            SELECT
                COALESCE(p.alamat, 'Unknown') as location,
                COALESCE(m.name, 'No Server') as server_name,
                COALESCE(m.host_ip, 'N/A') as host_ip,
                COUNT(l.id) as count
            FROM langganan l
            JOIN pelanggan p ON l.pelanggan_id = p.id
            LEFT JOIN data_teknis dt ON p.id = dt.pelanggan_id
            LEFT JOIN mikrotik_servers m ON dt.mikrotik_server_id = m.id
            WHERE l.status = 'Suspended'
            GROUP BY p.alamat, m.name, m.host_ip
            ORDER BY count DESC
        """)

        result = await session.execute(query)
        return result.fetchall()

    async def get_location_details(self, session, location_name):
        """Get detail Suspended user untuk lokasi tertentu"""
        query = text("""
            SELECT
                l.id as langganan_id,
                l.status,
                p.nama as pelanggan_nama,
                p.alamat as alamat,
                p.email,
                p.no_telp,
                dt.id_pelanggan,
                dt.password_pppoe,
                dt.ip_pelanggan,
                dt.profile_pppoe,
                dt.mikrotik_server_id,
                m.name as server_name,
                m.host_ip as server_ip,
                m.port as server_port,
                m.username as server_username,
                m.password as server_password,
                pl.nama_paket,
                l.tgl_jatuh_tempo
            FROM langganan l
            JOIN pelanggan p ON l.pelanggan_id = p.id
            LEFT JOIN data_teknis dt ON p.id = dt.pelanggan_id
            LEFT JOIN mikrotik_servers m ON dt.mikrotik_server_id = m.id
            LEFT JOIN paket_layanan pl ON l.paket_layanan_id = pl.id
            WHERE l.status = 'Suspended'
            AND LOWER(p.alamat) LIKE LOWER(:location_name)
            ORDER BY p.nama
        """)

        result = await session.execute(query, {"location_name": f"%{location_name}%"})
        return result.fetchall()

    async def update_mikrotik_sync(self, session, user_data):
        """Update Mikrotik untuk satu user"""
        try:
            if self.dry_run:
                print(f"   🔍 DRY-RUN: Would update {user_data.get('id_pelanggan', 'N/A')} on {user_data.get('server_name', 'N/A')}")
                return True

            # Import Mikrotik service di dalam function untuk avoid circular import
            from app.services import mikrotik_service

            # Build server info
            server_info = {
                'host': user_data.get('server_ip'),
                'port': user_data.get('server_port'),
                'username': user_data.get('server_username'),
                'password': user_data.get('server_password')
            }

            # Build langganan-like object
            class SimpleLangganan:
                def __init__(self, data):
                    self.id = data.get('langganan_id')
                    self.status = 'Suspended'
                    self.pelanggan = SimplePelanggan(data)

            class SimplePelanggan:
                def __init__(self, data):
                    self.nama = data.get('pelanggan_nama')
                    self.data_teknis = [SimpleDataTeknis(data)]

            class SimpleDataTeknis:
                def __init__(self, data):
                    self.id_pelanggan = data.get('id_pelanggan')
                    self.password_pppoe = data.get('password_pppoe')
                    self.ip_pelanggan = data.get('ip_pelanggan')
                    self.profile_pppoe = data.get('profile_pppoe')
                    self.mikrotik_server_id = data.get('mikrotik_server_id')
                    self.mikrotik_sync_pending = False

            # Create objects
            langganan = SimpleLangganan(user_data)
            data_teknis = SimpleDataTeknis(user_data)

            # Call Mikrotik service
            await mikrotik_service.trigger_mikrotik_update(
                db=session,
                langganan=langganan,
                data_teknis=data_teknis,
                old_id_pelanggan=user_data['id_pelanggan']
            )

            return True

        except Exception as e:
            error_msg = str(e)
            self.results['failed_details'].append({
                'langganan_id': user_data['langganan_id'],
                'pelanggan_nama': user_data['pelanggan_nama'],
                'error': error_msg
            })
            print(f"   ❌ FAILED: {error_msg}")
            return False

    async def process_location(self, session, location_name):
        """Process suspend untuk satu lokasi"""
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING LOCATION: {location_name.upper()}")
        print(f"{'='*60}")

        # Get location details
        users = await self.get_location_details(session, location_name)

        if not users:
            print(f"⚠️  Tidak ada user Suspended di lokasi '{location_name}'")
            return

        print(f"📊 Found {len(users)} suspended users in {location_name}")

        # Group by server
        server_groups = {}
        for user in users:
            # Convert row to dict for easier access
            user_dict = {}
            for column in user._mapping.keys():
                user_dict[column] = getattr(user, column)

            server_key = f"{user_dict.get('server_name', 'No Server')} ({user_dict.get('server_ip', 'N/A')})"
            if server_key not in server_groups:
                server_groups[server_key] = []
            server_groups[server_key].append(user_dict)

        print(f"🖥️  Grouped by {len(server_groups)} Mikrotik server(s)")

        # Process per batch
        total_processed = 0
        for server_name, server_users in server_groups.items():
            print(f"\n🖥️  Processing {len(server_users)} users on {server_name}")

            for i in range(0, len(server_users), self.batch_size):
                batch = server_users[i:i + self.batch_size]
                print(f"\n📦 Batch {i//self.batch_size + 1}: {len(batch)} users")

                batch_success = 0
                for j, user in enumerate(batch):
                    print(f"[{i+j+1}/{len(users)}] ", end="")
                    print(f"🔄 {user.get('pelanggan_nama', 'Unknown')} - {user.get('id_pelanggan', 'N/A')}")
                    print(f"   📍 {user.get('alamat', 'Unknown') or 'Unknown'}")

                    if not user.get('id_pelanggan'):
                        print(f"   ⚠️  Skipped: No PPPoE username")
                        self.results['skipped_count'] += 1
                        continue

                    if not user.get('mikrotik_server_id'):
                        print(f"   ⚠️  Skipped: No Mikrotik server assigned")
                        self.results['skipped_count'] += 1
                        continue

                    success = await self.update_mikrotik_sync(session, user)
                    if success:
                        batch_success += 1
                        self.results['success_count'] += 1
                        print(f"   ✅ SUCCESS: PPPoE secret disabled")
                    else:
                        self.results['failed_count'] += 1

                total_processed += len(batch)
                print(f"\n📊 Batch Summary: {batch_success}/{len(batch)} success")

                # Pause between batches
                if i + self.batch_size < len(server_users):
                    print("⏸️  Pausing 2 seconds...")
                    await asyncio.sleep(2)

        self.results['processed_locations'].append(location_name)
        self.results['total_processed'] += total_processed
        print(f"\n✅ Location {location_name} completed: {total_processed} users processed")

    def print_summary(self, summary_data):
        """Print summary results"""
        print("\n📊 SUSPENDED USER SUMMARY")
        print("="*60)

        total_users = sum(row.count for row in summary_data)
        print(f"👥 Total Suspended Users: {total_users}")
        print(f"📍 Total Locations: {len(set(row.location for row in summary_data))}")
        print(f"🖥️  Total Mikrotik Servers: {len(set(row.server_name for row in summary_data if row.server_name))}")

        print(f"\n📍 Breakdown by Location & Server:")
        print("-"*60)

        current_location = None
        location_total = 0

        for row in summary_data:
            if row.location != current_location:
                if current_location is not None:
                    print(f"   📊 Subtotal {current_location}: {location_total} users")

                current_location = row.location
                location_total = 0
                print(f"\n🏠 Location: {current_location}")

            server_name = row.server_name or "No Server"
            print(f"   🖥️  {server_name} ({row.host_ip}): {row.count} users")
            location_total += row.count

        if current_location is not None:
            print(f"   📊 Subtotal {current_location}: {location_total} users")

    def print_final_summary(self):
        """Print final processing summary"""
        self.results['end_time'] = datetime.now()
        duration = self.results['end_time'] - self.results['start_time']

        print(f"\n{'='*60}")
        print(f"📊 PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"⏱️  Duration: {duration}")
        print(f"📋 Locations: {', '.join(self.results['processed_locations'])}")
        print(f"📊 Total Processed: {self.results['total_processed']}")
        print(f"✅ Success: {self.results['success_count']}")
        print(f"❌ Failed: {self.results['failed_count']}")
        print(f"⏭️  Skipped: {self.results['skipped_count']}")

        if self.results['failed_details']:
            print(f"\n❌ Failed Details:")
            for detail in self.results['failed_details']:
                print(f"   • {detail['pelanggan_nama']}: {detail['error']}")

        mode = "DRY RUN" if self.dry_run else "LIVE MODE"
        print(f"\n🎯 Mode: {mode}")
        if self.dry_run:
            print("🔍 This was a DRY RUN - no actual changes made to Mikrotik")
        else:
            print("💾 Changes have been applied to Mikrotik servers")

        # Save results to file
        filename = f"suspend_results_{self.results['start_time'].strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"📁 Results saved to: {filename}")

async def main():
    parser = argparse.ArgumentParser(description='Simple Suspended User Processor')
    parser.add_argument('--summary', '-s', action='store_true', help='Show summary semua lokasi')
    parser.add_argument('--location', '-l', help='Process lokasi tertentu')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run mode')
    parser.add_argument('--execute', '-e', action='store_true', help='Execute mode (default is dry-run)')
    parser.add_argument('--batch-size', '-b', type=int, default=20, help='Batch size (default: 20)')

    args = parser.parse_args()

    if not any([args.summary, args.location]):
        print("❌ Pilih salah satu:")
        print("  --summary           : Show summary semua lokasi")
        print("  --location <name>   : Process lokasi tertentu")
        print("\nContoh:")
        print("  python3 simple_suspend_checker.py --summary")
        print("  python3 simple_suspend_checker.py --location waringin --dry-run")
        print("  python3 simple_suspend_checker.py --location waringin --execute")
        return

    # Initialize processor
    dry_run = not args.execute  # Default dry-run unless --execute is specified
    processor = SimpleSuspendProcessor(dry_run=dry_run, batch_size=args.batch_size)

    print(f"🚀 Starting Simple Suspend Processor")
    print(f"📋 Mode: {'DRY RUN' if dry_run else 'LIVE MODE'}")
    print(f"📦 Batch Size: {args.batch_size}")

    if dry_run:
        print("🔍 DRY RUN MODE - Tidak ada perubahan ke Mikrotik!")
        print("   Untuk eksekusi nyata, tambahkan --execute flag")

    async with AsyncSessionLocal() as session:
        try:
            if args.summary:
                summary_data = await processor.get_suspended_summary(session)
                processor.print_summary(summary_data)

            elif args.location:
                await processor.process_location(session, args.location)
                processor.print_final_summary()

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())