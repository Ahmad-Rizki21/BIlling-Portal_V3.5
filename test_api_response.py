#!/usr/bin/env python3
"""
Script untuk testing API response dan mencari masalah data loading
"""

import json
import subprocess
import sys


def run_curl(url, method="GET", data=None):
    """Run curl command and return response"""
    try:
        cmd = ["curl", "-s", "-w", "%{http_code}", "-X", method]
        if data:
            cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Split response body and status code
        response_text = result.stdout[:-3]  # Last 3 chars are status code
        status_code = int(result.stdout[-3:])

        return status_code, response_text, result.stderr
    except subprocess.TimeoutExpired:
        return 0, "", "Timeout"
    except Exception as e:
        return 0, "", str(e)

def test_api_endpoints():
    """Test API endpoints untuk memahami masalah data loading"""

    base_url = "http://localhost:8000"  # Ganti dengan URL production Anda

    print("🔍 Testing API Endpoints...")
    print("=" * 60)

        # 1. Test endpoint pelanggan
        print("\n1️⃣ Testing GET /pelanggan/")
        try:
            async with session.get(f"{base_url}/pelanggan/") as response:
                if response.status == 200:
                    data = await response.json()
                    pelanggan_list = data if isinstance(data, list) else data.get('data', [])
                    print(f"   ✅ Status: {response.status}")
                    print(f"   📊 Total pelanggan: {len(pelanggan_list)}")

                    # Cek apakah pelanggan ID 258 ada
                    pelanggan_258 = [p for p in pelanggan_list if p.get('id') == 258]
                    if pelanggan_258:
                        print(f"   ✅ Pelanggan ID 258 ditemukan: {pelanggan_258[0].get('nama', 'N/A')}")
                    else:
                        print("   ❌ Pelanggan ID 258 TIDAK ditemukan dalam response!")

                        # Cari ID terdekat
                        if pelanggan_list:
                            max_id = max(p.get('id', 0) for p in pelanggan_list)
                            min_id = min(p.get('id', 0) for p in pelanggan_list)
                            print(f"   📊 Range ID pelanggan: {min_id} - {max_id}")
                else:
                    print(f"   ❌ Error: {response.status}")
                    error_text = await response.text()
                    print(f"   📄 Error detail: {error_text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 2. Test endpoint langganan for invoice selection
        print("\n2️⃣ Testing GET /langganan/?for_invoice_selection=true")
        try:
            async with session.get(f"{base_url}/langganan/?for_invoice_selection=true") as response:
                if response.status == 200:
                    data = await response.json()
                    langganan_list = data if isinstance(data, list) else data.get('data', [])
                    print(f"   ✅ Status: {response.status}")
                    print(f"   📊 Total langganan: {len(langganan_list)}")

                    # Cek apakah langganan ID 244 ada
                    langganan_244 = [l for l in langganan_list if l.get('id') == 244]
                    if langganan_244:
                        langg = langganan_244[0]
                        print(f"   ✅ Langganan ID 244 ditemukan:")
                        print(f"      pelanggan_id: {langg.get('pelanggan_id')}")
                        print(f"      status: {langg.get('status')}")
                        if langg.get('pelanggan'):
                            print(f"      nama pelanggan: {langg['pelanggan'].get('nama', 'N/A')}")
                        else:
                            print("      ❌ Data pelanggan tidak ada dalam response!")
                    else:
                        print("   ❌ Langganan ID 244 TIDAK ditemukan dalam response!")

                        # Cari ID terdekat
                        if langganan_list:
                            max_id = max(l.get('id', 0) for l in langganan_list)
                            min_id = min(l.get('id', 0) for l in langganan_list)
                            print(f"   📊 Range ID langganan: {min_id} - {max_id}")

                            # Cari pelanggan_id yang sama
                            pelanggan_id_258 = [l for l in langganan_list if l.get('pelanggan_id') == 258]
                            if pelanggan_id_258:
                                print(f"   ℹ️  Ditemukan {len(pelanggan_id_258)} langganan dengan pelanggan_id 258:")
                                for l in pelanggan_id_258:
                                    print(f"      - ID {l.get('id')}: {l.get('status')}")
                            else:
                                print("   ❌ Tidak ada langganan dengan pelanggan_id 258")
                else:
                    print(f"   ❌ Error: {response.status}")
                    error_text = await response.text()
                    print(f"   📄 Error detail: {error_text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 3. Test endpoint langganan tanpa filter
        print("\n3️⃣ Testing GET /langganan/ (tanpa filter)")
        try:
            async with session.get(f"{base_url}/langganan/") as response:
                if response.status == 200:
                    data = await response.json()
                    langganan_list = data if isinstance(data, list) else data.get('data', [])
                    print(f"   ✅ Status: {response.status}")
                    print(f"   📊 Total langganan (tanpa filter): {len(langganan_list)}")

                    # Cek apakah langganan ID 244 ada
                    langganan_244 = [l for l in langganan_list if l.get('id') == 244]
                    if langganan_244:
                        print(f"   ✅ Langganan ID 244 ditemukan dalam data lengkap")
                    else:
                        print("   ❌ Langganan ID 244 TIDAK ditemukan dalam data lengkap")
                else:
                    print(f"   ❌ Error: {response.status}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 4. Test generate invoice endpoint (akan gagal tapi bisa lihat error)
        print("\n4️⃣ Testing POST /invoices/generate (untuk lihat error detail)")
        try:
            payload = {"langganan_id": 244}
            async with session.post(f"{base_url}/invoices/generate", json=payload) as response:
                print(f"   Status: {response.status}")
                if response.status != 200:
                    error_data = await response.json()
                    print(f"   ❌ Error detail: {error_data.get('detail', 'Unknown error')}")
                else:
                    print("   ✅ Invoice berhasil dibuat (mungkin data sudah diperbaiki)")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        print("\n" + "=" * 60)
        print("🔍 Analisis Selesai!")
        print("\n💡 Jika ada perbedaan antara database dan API response:")
        print("   1. Cek pagination/limit di backend")
        print("   2. Cek user permissions/role")
        print("   3. Cek filter yang aktif di endpoint")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())