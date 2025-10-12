#!/usr/bin/env python3
"""
Script untuk debugging konsistensi data antara tabel langganan dan pelanggan
Gunakan script ini di server production untuk mengidentifikasi data yang tidak konsisten.
"""

import asyncio
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.models.langganan import Langganan
from app.models.pelanggan import Pelanggan


async def debug_data_consistency():
    """Cek konsistensi data antara langganan dan pelanggan"""

    print("🔍 Memulai debugging konsistensi data...")
    print("=" * 60)

    async with engine.begin() as conn:
        # 1. Cek total records
        print("\n📊 Statistik Database:")

        total_pelanggan = await conn.scalar(text("SELECT COUNT(*) FROM pelanggan"))
        total_langganan = await conn.scalar(text("SELECT COUNT(*) FROM langganan"))

        print(f"   Total Pelanggan: {total_pelanggan:,}")
        print(f"   Total Langganan: {total_langganan:,}")

        # 2. Cek pelanggan_id yang ada di langganan tapi tidak ada di pelanggan
        print("\n🚨 Mengecek data yang tidak konsisten...")

        # Query untuk menemukan pelanggan_id yang ada di langganan tapi tidak ada di pelanggan
        query = text(
            """
            SELECT DISTINCT l.pelanggan_id, l.id as langganan_id, l.status
            FROM langganan l
            LEFT JOIN pelanggan p ON l.pelanggan_id = p.id
            WHERE p.id IS NULL
            ORDER BY l.pelanggan_id
        """
        )

        result = await conn.execute(query)
        orphaned_langganan = result.fetchall()

        if orphaned_langganan:
            print(f"\n❌ Ditemukan {len(orphaned_langganan)} langganan dengan pelanggan_id yang tidak ada:")
            print("   pelanggan_id | langganan_id | status")
            print("   -------------|--------------|---------")

            for row in orphaned_langganan:
                print(f"   {row[0]:>11} | {row[1]:>12} | {row[2]}")
        else:
            print("✅ Tidak ada data langganan yang terisolasi")

        # 3. Cek detail spesifik untuk ID yang disebutkan
        print("\n🔍 Mengecek ID spesifik yang disebutkan (258, 244)...")

        # Cek apakah pelanggan ID 258 ada
        pelanggan_258 = await conn.scalar(text("SELECT COUNT(*) FROM pelanggan WHERE id = 258"))
        langganan_244 = await conn.scalar(text("SELECT COUNT(*) FROM langganan WHERE id = 244"))

        if langganan_244 > 0:
            # Cek detail langganan ID 244
            detail_244 = await conn.execute(
                text(
                    """
                SELECT l.id, l.pelanggan_id, l.status, p.nama as pelanggan_nama
                FROM langganan l
                LEFT JOIN pelanggan p ON l.pelanggan_id = p.id
                WHERE l.id = 244
            """
                )
            )
            row_244 = detail_244.fetchone()

            if row_244:
                print(f"\n📋 Detail Langganan ID 244:")
                print(f"   ID: {row_244[0]}")
                print(f"   pelanggan_id: {row_244[1]}")
                print(f"   Status: {row_244[2]}")
                print(f"   Nama Pelanggan: {row_244[3] or '❌ TIDAK DITEMUKAN'}")

                if row_244[3] is None:
                    print(f"   ❌ ERROR: Pelanggan ID {row_244[1]} tidak ada di database!")
        else:
            print("   Langganan ID 244 tidak ditemukan")

        if pelanggan_258 > 0:
            # Cek detail pelanggan ID 258
            detail_258 = await conn.execute(
                text(
                    """
                SELECT p.id, p.nama, p.no_telp, p.email
                FROM pelanggan p
                WHERE p.id = 258
            """
                )
            )
            row_258 = detail_258.fetchone()

            if row_258:
                print(f"\n📋 Detail Pelanggan ID 258:")
                print(f"   ID: {row_258[0]}")
                print(f"   Nama: {row_258[1]}")
                print(f"   No. Telp: {row_258[2]}")
                print(f"   Email: {row_258[3]}")
        else:
            print("   Pelanggan ID 258 tidak ditemukan")

        # 4. Generate SQL untuk memperbaiki data
        if orphaned_langganan:
            print(f"\n🛠️  SQL untuk memperbaiki data (HATI-HATI!):")
            print("-- Opsi 1: Hapus langganan yang tidak valid (tidak disarankan)")
            for row in orphaned_langganan:
                print(f"DELETE FROM langganan WHERE id = {row[1]}; -- pelanggan_id={row[0]} tidak ada")

            print("\n-- Opsi 2: Update ke pelanggan dummy (lebih aman)")
            print("-- Pertama, buat pelanggan dummy:")
            print(
                "INSERT INTO pelanggan (id, nama, alamat, no_telp, email) VALUES (999999, 'PELANGGAN DUMMY', 'Alamat Dummy', '0000000000', 'dummy@example.com') ON CONFLICT (id) DO NOTHING;"
            )
            print("-- Kemudian update langganan:")
            for row in orphaned_langganan:
                print(f"UPDATE langganan SET pelanggan_id = 999999 WHERE id = {row[1]};")


async def main():
    """Main function"""
    try:
        await debug_data_consistency()
        print("\n" + "=" * 60)
        print("✅ Debugging selesai!")
        print("💡 Jika menemukan data tidak konsisten, perbaiki dengan hati-hati di production!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
