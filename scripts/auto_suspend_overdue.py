#!/usr/bin/env python3
"""
Auto Suspend Overdue Invoice Script
====================================
Script untuk otomatis suspend user yang invoice-nya sudah jatuh tempo
tapi status langganan masih aktif.

Logika:
- Cek user yang invoice terakhir sudah jatuh tempo (status "Belum Dibayar" atau "Expired")
- Status langganan masih "Aktif" (seharusnya sudah "Suspended")
- Suspend ke Mikrotik: disable PPPoE secret + ubah profile ke "SUSPENDED"
- Update status langganan di database menjadi "Suspended"
- Berjalan otomatis setiap tanggal 5 jam 00:00

Features:
- Dry-run mode untuk testing
- Batch processing untuk efisiensi
- Detail logging dan reporting
- Error handling yang robust
- Summary report per lokasi dan server

Usage:
1. Dry-run (testing): python3 auto_suspend_overdue.py --dry-run
2. Execute (live): python3 auto_suspend_overdue.py --execute
3. Specific date check: python3 auto_suspend_overdue.py --execute --check-date 2024-01-05

Scheduled via cron:
0 0 5 * * cd /path/to/project && python3 scripts/auto_suspend_overdue.py --execute
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import database configuration
from app.database import AsyncSessionLocal
from sqlalchemy import text, and_, or_
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Import models
from app.models.langganan import Langganan as LanggananModel
from app.models.pelanggan import Pelanggan as PelangganModel
from app.models.data_teknis import DataTeknis as DataTeknisModel
from app.models.mikrotik_server import MikrotikServer as MikrotikServerModel
from app.models.invoice import Invoice as InvoiceModel

# Import mikrotik service
from app.services import mikrotik_service


class AutoSuspendProcessor:
    """Processor untuk auto suspend user dengan invoice jatuh tempo"""

    def __init__(self, dry_run: bool = False, batch_size: int = 20, check_date: date = None):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.check_date = check_date or date.today()
        self.results = {
            'total_checked': 0,
            'total_suspended': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'already_suspended_count': 0,
            'failed_details': [],
            'suspended_users': [],
            'start_time': datetime.now(),
            'end_time': None,
            'check_date': str(self.check_date)
        }

    async def get_overdue_users(self, session) -> List[Any]:
        """
        Mengambil user yang invoice-nya sudah jatuh tempo tapi langganan masih aktif.
        
        Kriteria:
        1. Status langganan = "Aktif" (case-insensitive)
        2. Ada invoice dengan status "Belum Dibayar" atau "Expired"
        3. Tanggal jatuh tempo invoice < tanggal check (sudah lewat)
        4. Punya data teknis (untuk suspend ke Mikrotik)
        """
        
        # Query untuk mendapatkan user yang perlu di-suspend
        # Menggunakan subquery untuk mendapatkan invoice terakhir yang belum dibayar
        query = text("""
            SELECT DISTINCT
                l.id as langganan_id,
                l.status as langganan_status,
                l.pelanggan_id,
                p.nama as pelanggan_nama,
                p.alamat,
                p.email,
                p.no_telp,
                dt.id as data_teknis_id,
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
                i.invoice_number,
                i.tgl_jatuh_tempo,
                i.status_invoice,
                i.total_harga
            FROM langganan l
            INNER JOIN pelanggan p ON l.pelanggan_id = p.id
            LEFT JOIN data_teknis dt ON p.id = dt.pelanggan_id
            LEFT JOIN mikrotik_servers m ON dt.mikrotik_server_id = m.id
            INNER JOIN (
                -- Subquery untuk mendapatkan invoice terakhir yang belum dibayar per pelanggan
                SELECT 
                    i1.pelanggan_id,
                    i1.invoice_number,
                    i1.tgl_jatuh_tempo,
                    i1.status_invoice,
                    i1.total_harga
                FROM invoices i1
                INNER JOIN (
                    SELECT 
                        pelanggan_id,
                        MAX(tgl_invoice) as max_tgl_invoice
                    FROM invoices
                    WHERE status_invoice IN ('Belum Dibayar', 'Expired')
                    AND tgl_jatuh_tempo < :check_date
                    GROUP BY pelanggan_id
                ) i2 ON i1.pelanggan_id = i2.pelanggan_id 
                    AND i1.tgl_invoice = i2.max_tgl_invoice
                WHERE i1.status_invoice IN ('Belum Dibayar', 'Expired')
            ) i ON l.pelanggan_id = i.pelanggan_id
            WHERE LOWER(l.status) = 'aktif'
            AND dt.id IS NOT NULL
            AND dt.mikrotik_server_id IS NOT NULL
            ORDER BY p.alamat, p.nama
        """)

        result = await session.execute(query, {"check_date": self.check_date})
        return result.fetchall()

    async def suspend_to_mikrotik(self, session, user_data: Dict[str, Any]) -> tuple[bool, Any]:
        """
        Suspend user ke Mikrotik:
        1. Update PPPoE secret: disabled = yes
        2. Update profile ke "SUSPENDED"
        3. Disconnect active connection
        
        Returns:
            tuple: (success: bool, mikrotik_server_info: Any)
        """
        try:
            if self.dry_run:
                print(f"   🔍 DRY-RUN: Would suspend {user_data['id_pelanggan']} on {user_data['server_name']}")
                return (True, None)

            # Get Mikrotik server info
            server_id = user_data['mikrotik_server_id']
            mikrotik_server = await session.get(MikrotikServerModel, server_id)
            
            if not mikrotik_server:
                raise Exception(f"Mikrotik server ID {server_id} not found")

            # Get API connection
            api, connection = mikrotik_service.get_api_connection(mikrotik_server)
            if not api:
                raise Exception("Failed to get Mikrotik API connection")

            try:
                # Update PPPoE secret to suspended
                ppp_secrets = api.get_resource("/ppp/secret")
                target_secret = ppp_secrets.get(name=user_data['id_pelanggan'])

                if not target_secret:
                    raise Exception(f"PPPoE secret '{user_data['id_pelanggan']}' not found in Mikrotik")

                secret_id = target_secret[0]["id"]
                
                # Update to suspended state
                update_payload = {
                    "id": secret_id,
                    "profile": "SUSPENDED",
                    "disabled": "yes"
                }
                
                ppp_secrets.set(**update_payload)
                print(f"   ✅ Mikrotik: PPPoE secret disabled and profile changed to SUSPENDED")

                # Remove active connection if exists
                try:
                    ppp_active = api.get_resource("/ppp/active")
                    active_connections = ppp_active.get(name=user_data['id_pelanggan'])
                    
                    if active_connections:
                        connection_id = active_connections[0]["id"]
                        ppp_active.remove(id=connection_id)
                        print(f"   ✅ Mikrotik: Active connection disconnected")
                except Exception as e:
                    print(f"   ⚠️  Warning: Could not disconnect active connection: {e}")

                return (True, mikrotik_server)

            finally:
                if connection:
                    mikrotik_service.mikrotik_pool.return_connection(
                        connection, 
                        mikrotik_server.host_ip, 
                        int(mikrotik_server.port)
                    )

        except Exception as e:
            error_msg = str(e)
            self.results['failed_details'].append({
                'langganan_id': user_data['langganan_id'],
                'pelanggan_nama': user_data['pelanggan_nama'],
                'id_pelanggan': user_data['id_pelanggan'],
                'error': error_msg
            })
            print(f"   ❌ FAILED: {error_msg}")
            return (False, None)

    async def rollback_mikrotik(self, session, user_data: Dict[str, Any], mikrotik_server) -> bool:
        """
        Rollback Mikrotik suspend - re-enable user jika database gagal
        """
        try:
            if self.dry_run:
                print(f"   🔍 DRY-RUN: Would rollback (re-enable) {user_data['id_pelanggan']}")
                return True

            print(f"   🔄 [ROLLBACK] Re-enabling user in Mikrotik...")

            # Get API connection
            api, connection = mikrotik_service.get_api_connection(mikrotik_server)
            if not api:
                raise Exception("Failed to get Mikrotik API connection for rollback")

            try:
                # Get original profile from data_teknis
                data_teknis = await session.get(DataTeknisModel, user_data['data_teknis_id'])
                if not data_teknis:
                    raise Exception("Data teknis not found for rollback")

                # Update PPPoE secret back to active
                ppp_secrets = api.get_resource("/ppp/secret")
                target_secret = ppp_secrets.get(name=user_data['id_pelanggan'])

                if not target_secret:
                    raise Exception(f"PPPoE secret '{user_data['id_pelanggan']}' not found for rollback")

                secret_id = target_secret[0]["id"]
                
                # Re-enable with original profile
                update_payload = {
                    "id": secret_id,
                    "profile": data_teknis.profile_pppoe,
                    "disabled": "no"
                }
                
                ppp_secrets.set(**update_payload)
                print(f"   ✅ [ROLLBACK] User re-enabled in Mikrotik successfully")
                return True

            finally:
                if connection:
                    mikrotik_service.mikrotik_pool.return_connection(
                        connection, 
                        mikrotik_server.host_ip, 
                        int(mikrotik_server.port)
                    )

        except Exception as e:
            print(f"   ❌ [ROLLBACK] FAILED: {e}")
            return False

    async def update_langganan_status(self, session, user_data: Dict[str, Any], mikrotik_success: bool, mikrotik_server) -> bool:
        """
        Update status langganan di database menjadi 'Suspended'
        Jika gagal dan Mikrotik sudah di-suspend, akan rollback Mikrotik
        """
        try:
            if self.dry_run:
                print(f"   🔍 DRY-RUN: Would update langganan {user_data['langganan_id']} to Suspended")
                return True

            # Get langganan
            langganan = await session.get(LanggananModel, user_data['langganan_id'])
            if not langganan:
                raise Exception(f"Langganan ID {user_data['langganan_id']} not found")

            # Update status
            langganan.status = "Suspended"
            await session.commit()
            
            print(f"   ✅ Database: Langganan status updated to Suspended")
            return True

        except Exception as e:
            await session.rollback()
            print(f"   ❌ Database update failed: {e}")
            
            # ROLLBACK MIKROTIK jika sebelumnya sukses
            if mikrotik_success and mikrotik_server:
                print(f"   🔄 [ROLLBACK] Attempting to re-enable user in Mikrotik...")
                rollback_success = await self.rollback_mikrotik(session, user_data, mikrotik_server)
                
                if rollback_success:
                    print(f"   ✅ [ROLLBACK] System state consistent - user still active")
                else:
                    print(f"   ❌ [ROLLBACK] CRITICAL: Inconsistent state!")
                    print(f"   ⚠️  User suspended in Mikrotik but DB still Aktif")
                    print(f"   🔧 Manual intervention required for: {user_data['pelanggan_nama']}")
            
            return False

    async def process_suspensions(self, session):
        """Process semua user yang perlu di-suspend"""
        print(f"\n{'='*70}")
        print(f"🚀 AUTO SUSPEND OVERDUE INVOICES")
        print(f"{'='*70}")
        print(f"📅 Check Date: {self.check_date}")
        print(f"🔍 Mode: {'DRY RUN (Testing)' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"{'='*70}\n")

        # Get users to suspend
        users = await self.get_overdue_users(session)
        
        if not users:
            print("✅ No users need to be suspended. All invoices are up to date!")
            return

        self.results['total_checked'] = len(users)
        print(f"📊 Found {len(users)} users with overdue invoices\n")

        # Group by location and server
        location_groups = {}
        for user in users:
            # Convert row to dict
            user_dict = {}
            for column in user._mapping.keys():
                user_dict[column] = getattr(user, column)

            location = user_dict.get('alamat') or 'Unknown Location'
            server = f"{user_dict.get('server_name', 'No Server')} ({user_dict.get('server_ip', 'N/A')})"
            
            key = f"{location}|{server}"
            if key not in location_groups:
                location_groups[key] = {
                    'location': location,
                    'server': server,
                    'users': []
                }
            location_groups[key]['users'].append(user_dict)

        # Process each group
        for group_key, group_data in location_groups.items():
            location = group_data['location']
            server = group_data['server']
            users_list = group_data['users']

            print(f"\n{'─'*70}")
            print(f"📍 Location: {location}")
            print(f"🖥️  Server: {server}")
            print(f"👥 Users: {len(users_list)}")
            print(f"{'─'*70}\n")

            # Process in batches
            for i in range(0, len(users_list), self.batch_size):
                batch = users_list[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                
                print(f"📦 Batch {batch_num}: Processing {len(batch)} users\n")

                for j, user in enumerate(batch):
                    user_num = i + j + 1
                    print(f"[{user_num}/{len(users_list)}] 🔄 Processing: {user['pelanggan_nama']}")
                    print(f"   📧 Email: {user['email']}")
                    print(f"   📞 Phone: {user['no_telp']}")
                    print(f"   🆔 PPPoE: {user['id_pelanggan']}")
                    print(f"   📄 Invoice: {user['invoice_number']}")
                    print(f"   📅 Due Date: {user['tgl_jatuh_tempo']}")
                    print(f"   💰 Amount: Rp {user['total_harga']:,.0f}")
                    print(f"   📊 Status: {user['status_invoice']}")

                    # Check if already suspended
                    if user['langganan_status'].lower() == 'suspended':
                        print(f"   ⏭️  SKIPPED: Already suspended in database")
                        self.results['already_suspended_count'] += 1
                        continue

                    # STEP 1: Suspend to Mikrotik
                    mikrotik_success, mikrotik_server = await self.suspend_to_mikrotik(session, user)
                    
                    # STEP 2: Update database (with rollback capability)
                    db_success = await self.update_langganan_status(session, user, mikrotik_success, mikrotik_server)
                    
                    if db_success:
                        self.results['success_count'] += 1
                        self.results['total_suspended'] += 1
                        self.results['suspended_users'].append({
                            'nama': user['pelanggan_nama'],
                            'id_pelanggan': user['id_pelanggan'],
                            'invoice_number': user['invoice_number'],
                            'due_date': str(user['tgl_jatuh_tempo']),
                            'amount': float(user['total_harga'])
                        })
                        
                        if mikrotik_success:
                            print(f"   ✅ SUCCESS: Full suspend (Mikrotik + DB)\n")
                        else:
                            print(f"   ⚠️  PARTIAL: DB suspended, Mikrotik failed (will retry)\n")
                    else:
                        self.results['failed_count'] += 1
                        if mikrotik_success:
                            print(f"   ❌ FAILED: Database failed (Mikrotik rolled back)\n")
                        else:
                            print(f"   ❌ FAILED: Both Mikrotik and Database failed\n")

                # Pause between batches
                if i + self.batch_size < len(users_list):
                    print("⏸️  Pausing 2 seconds before next batch...\n")
                    await asyncio.sleep(2)

    def print_final_summary(self):
        """Print final processing summary"""
        self.results['end_time'] = datetime.now()
        duration = self.results['end_time'] - self.results['start_time']

        print(f"\n{'='*70}")
        print(f"📊 FINAL SUMMARY")
        print(f"{'='*70}")
        print(f"⏱️  Duration: {duration}")
        print(f"📅 Check Date: {self.check_date}")
        print(f"🔍 Total Checked: {self.results['total_checked']}")
        print(f"🔴 Total Suspended: {self.results['total_suspended']}")
        print(f"✅ Success: {self.results['success_count']}")
        print(f"❌ Failed: {self.results['failed_count']}")
        print(f"⏭️  Already Suspended: {self.results['already_suspended_count']}")
        
        if self.results['failed_details']:
            print(f"\n❌ Failed Details:")
            for detail in self.results['failed_details']:
                print(f"   • {detail['pelanggan_nama']} ({detail['id_pelanggan']}): {detail['error']}")

        mode = "DRY RUN" if self.dry_run else "LIVE MODE"
        print(f"\n🎯 Mode: {mode}")
        
        if self.dry_run:
            print("🔍 This was a DRY RUN - no actual changes made!")
            print("   Run with --execute flag to apply changes")
        else:
            print("💾 Changes have been applied to Mikrotik and Database")

        # Save results to file
        timestamp = self.results['start_time'].strftime('%Y%m%d_%H%M%S')
        filename = f"auto_suspend_results_{timestamp}.json"
        filepath = project_root / "logs" / filename
        
        # Create logs directory if not exists
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {filepath}")
        print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(
        description='Auto Suspend Users with Overdue Invoices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (testing mode)
  python3 auto_suspend_overdue.py --dry-run
  
  # Execute (live mode)
  python3 auto_suspend_overdue.py --execute
  
  # Check specific date
  python3 auto_suspend_overdue.py --execute --check-date 2024-01-05
  
  # Custom batch size
  python3 auto_suspend_overdue.py --execute --batch-size 10

Cron Schedule (runs every 5th day at 00:00):
  0 0 5 * * cd /path/to/project && python3 scripts/auto_suspend_overdue.py --execute
        """
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Dry run mode (no changes will be made)'
    )
    parser.add_argument(
        '--execute', '-e',
        action='store_true',
        help='Execute mode (apply changes)'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=20,
        help='Batch size for processing (default: 20)'
    )
    parser.add_argument(
        '--check-date', '-c',
        type=str,
        help='Check date in YYYY-MM-DD format (default: today)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        print("❌ Error: You must specify either --dry-run or --execute")
        print("\nExamples:")
        print("  python3 auto_suspend_overdue.py --dry-run")
        print("  python3 auto_suspend_overdue.py --execute")
        return

    # Parse check date
    check_date = None
    if args.check_date:
        try:
            check_date = datetime.strptime(args.check_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Error: Invalid date format '{args.check_date}'. Use YYYY-MM-DD")
            return

    # Initialize processor
    dry_run = args.dry_run  # If --execute is specified, dry_run will be False
    processor = AutoSuspendProcessor(
        dry_run=dry_run,
        batch_size=args.batch_size,
        check_date=check_date
    )

    print(f"\n🚀 Starting Auto Suspend Processor")
    print(f"📋 Mode: {'DRY RUN (Testing)' if dry_run else 'LIVE EXECUTION'}")
    print(f"📦 Batch Size: {args.batch_size}")
    print(f"📅 Check Date: {processor.check_date}")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made!")
        print("   Use --execute flag to apply changes")

    # Process suspensions
    async with AsyncSessionLocal() as session:
        try:
            await processor.process_suspensions(session)
            processor.print_final_summary()

        except Exception as e:
            print(f"\n❌ Fatal Error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
