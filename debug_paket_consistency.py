#!/usr/bin/env python3
"""
Debug script untuk memeriksa konsistensi data paket layanan
Script ini akan membantu mengidentifikasi masalah dengan paket layanan yang tidak terload
"""

import asyncio
import sys
import os

# Tambahkan direktori app ke Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.langganan import Langganan as LanggananModel
from app.models.paket_layanan import PaketLayanan as PaketLayananModel
from app.models.pelanggan import Pelanggan as PelangganModel
from app.config import get_settings


async def check_paket_consistency():
    """Memeriksa konsistensi data paket layanan"""

    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with AsyncSession(engine) as session:
        print("🔍 Memeriksa konsistensi data paket layanan...")

        # 1. Get all paket layanan
        print("\n📋 DAFTAR SEMUA PAKET LAYANAN:")
        paket_query = select(PaketLayananModel)
        paket_result = await session.execute(paket_query)
        all_paket = paket_result.scalars().all()

        print(f"Total paket layanan: {len(all_paket)}")
        for paket in all_paket:
            print(f"  - ID: {paket.id}, Nama: {paket.nama_paket}, Harga: {paket.harga}")

        # 2. Get all langganan dengan paket data
        print("\n📋 MEMERIKSA LANGGANAN DENGAN PAKET DATA:")
        langganan_query = select(LanggananModel).options(
            joinedload(LanggananModel.pelanggan), joinedload(LanggananModel.paket_layanan)
        )
        langganan_result = await session.execute(langganan_query)
        all_langganan = langganan_result.scalars().unique().all()

        print(f"Total langganan: {len(all_langganan)}")

        # 3. Cari langganan dengan paket_id yang tidak valid
        problematic_langganan = []
        valid_paket_ids = {paket.id for paket in all_paket}

        for langganan in all_langganan:
            if langganan.paket_layanan_id and langganan.paket_layanan_id not in valid_paket_ids:
                problematic_langganan.append(langganan)

        if problematic_langganan:
            print(f"\n❌ Ditemukan {len(problematic_langganan)} langganan dengan paket_id yang tidak valid:")
            for langganan in problematic_langganan[:10]:  # Limit to 10
                pelanggan_nama = langganan.pelanggan.nama if langganan.pelanggan else "PELANGGAN TIDAK ADA"
                print(
                    f"  - Langganan ID: {langganan.id}, Pelanggan: {pelanggan_nama}, Paket ID: {langganan.paket_layanan_id} (TIDAK VALID)"
                )
        else:
            print("\n✅ Semua langganan memiliki paket_id yang valid")

        # 4. Cari langganan tanpa paket data tapi ada paket_id
        print("\n📋 MEMERIKSA LANGGANAN TANPA PAKET DATA:")
        langganan_without_paket_data = []

        for langganan in all_langganan:
            if langganan.paket_layanan_id and not langganan.paket_layanan:
                langganan_without_paket_data.append(langganan)

        if langganan_without_paket_data:
            print(f"❌ Ditemukan {len(langganan_without_paket_data)} langganan tanpa paket data:")

            # Group by paket_layanan_id
            paket_groups = {}
            for langganan in langganan_without_paket_data:
                paket_id = langganan.paket_layanan_id
                if paket_id not in paket_groups:
                    paket_groups[paket_id] = []
                paket_groups[paket_id].append(langganan)

            for paket_id, langganan_list in paket_groups.items():
                print(f"\n  Paket ID {paket_id} ({len(langganan_list)} langganan):")
                for langganan in langganan_list[:5]:  # Limit to 5 per paket
                    pelanggan_nama = langganan.pelanggan.nama if langganan.pelanggan else "PELANGGAN TIDAK ADA"
                    print(f"    - Langganan ID: {langganan.id}, Pelanggan: {pelanggan_nama}, Status: {langganan.status}")
        else:
            print("✅ Semua langganan dengan paket_id memiliki data paket yang lengkap")

        # 5. Cek spesifik paket ID 5 yang muncul di console log
        print("\n📋 MEMERIKSA PAKET ID 5:")
        paket_5 = next((p for p in all_paket if p.id == 5), None)
        if paket_5:
            print(f"✅ Paket ID 5 ditemukan: {paket_5.nama_paket}, Harga: {paket_5.harga}")
        else:
            print("❌ Paket ID 5 TIDAK DITEMUKAN di database!")

            # Cari langganan yang menggunakan paket ID 5
            langganan_with_paket_5 = [l for l in all_langganan if l.paket_layanan_id == 5]
            if langganan_with_paket_5:
                print(f"📊 {len(langganan_with_paket_5)} langganan menggunakan paket ID 5:")
                for langganan in langganan_with_paket_5[:5]:
                    pelanggan_nama = langganan.pelanggan.nama if langganan.pelanggan else "PELANGGAN TIDAK ADA"
                    print(f"  - Langganan ID: {langganan.id}, Pelanggan: {pelanggan_nama}")

        # 6. Summary
        print("\n📊 SUMMARY:")
        print(f"  - Total paket layanan: {len(all_paket)}")
        print(f"  - Total langganan: {len(all_langganan)}")
        print(f"  - Langganan dengan paket_id tidak valid: {len(problematic_langganan)}")
        print(f"  - Langganan tanpa paket data: {len(langganan_without_paket_data)}")

        if problematic_langganan or langganan_without_paket_data:
            print("\n⚠️ ADA MASALAH KONSISTENSI DATA!")
            print("Solusi yang disarankan:")
            print("1. Cek apakah ada paket layanan yang dihapus tapi masih direferensikan oleh langganan")
            print("2. Jalankan migration untuk memperbaiki data yang tidak konsisten")
            print("3. Periksa eager loading di backend endpoint /langganan/")
        else:
            print("\n✅ Data konsistensi paket layanan NORMAL")

        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_paket_consistency())
