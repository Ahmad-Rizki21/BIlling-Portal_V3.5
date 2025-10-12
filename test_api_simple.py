#!/usr/bin/env python3
"""
Script sederhana untuk testing API response tanpa dependencies external
"""

import json
import subprocess


def test_api_with_curl():
    """Test API endpoints menggunakan curl"""

    base_url = "http://localhost:8000"  # Ganti dengan URL production Anda

    print("🔍 Testing API Endpoints...")
    print("=" * 60)

    # 1. Test endpoint pelanggan
    print("\n1️⃣ Testing GET /pelanggan/")
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", f"{base_url}/pelanggan/"], capture_output=True, text=True, timeout=10
        )

        if len(result.stdout) >= 3:
            response_text = result.stdout[:-3]
            status_code = int(result.stdout[-3:])

            if status_code == 200:
                try:
                    data = json.loads(response_text)
                    if isinstance(data, list):
                        print(f"   ✅ Status: {status_code}")
                        print(f"   📊 Total pelanggan: {len(data)}")

                        # Cek pelanggan ID 258
                        pelanggan_258 = [p for p in data if p.get("id") == 258]
                        if pelanggan_258:
                            print(f"   ✅ Pelanggan ID 258: {pelanggan_258[0].get('nama', 'N/A')}")
                        else:
                            print("   ❌ Pelanggan ID 258 TIDAK ditemukan!")
                            if data:
                                max_id = max(p.get("id", 0) for p in data)
                                min_id = min(p.get("id", 0) for p in data)
                                print(f"   📊 Range ID: {min_id} - {max_id}")
                    else:
                        print(f"   ❌ Response bukan array: {type(data)}")
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
            else:
                print(f"   ❌ HTTP Status: {status_code}")
                print(f"   📄 Response: {response_text[:200]}...")
        else:
            print("   ❌ Invalid curl response")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # 2. Test endpoint langganan for invoice selection
    print("\n2️⃣ Testing GET /langganan/?for_invoice_selection=true")
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", f"{base_url}/langganan/?for_invoice_selection=true"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if len(result.stdout) >= 3:
            response_text = result.stdout[:-3]
            status_code = int(result.stdout[-3:])

            if status_code == 200:
                try:
                    data = json.loads(response_text)
                    if isinstance(data, list):
                        print(f"   ✅ Status: {status_code}")
                        print(f"   📊 Total langganan: {len(data)}")

                        # Cek langganan ID 244
                        langganan_244 = [l for l in data if l.get("id") == 244]
                        if langganan_244:
                            langg = langganan_244[0]
                            print(f"   ✅ Langganan ID 244:")
                            print(f"      pelanggan_id: {langg.get('pelanggan_id')}")
                            print(f"      status: {langg.get('status')}")
                            if langg.get("pelanggan"):
                                print(f"      nama pelanggan: {langg['pelanggan'].get('nama', 'N/A')}")
                            else:
                                print("      ❌ Data pelanggan tidak ada!")
                        else:
                            print("   ❌ Langganan ID 244 TIDAK ditemukan!")
                            if data:
                                max_id = max(l.get("id", 0) for l in data)
                                min_id = min(l.get("id", 0) for l in data)
                                print(f"   📊 Range ID: {min_id} - {max_id}")

                                # Cari yang punya pelanggan_id 258
                                pelanggan_258 = [l for l in data if l.get("pelanggan_id") == 258]
                                if pelanggan_258:
                                    print(f"   ℹ️ {len(pelanggan_258)} langganan dengan pelanggan_id 258:")
                                    for l in pelanggan_258:
                                        print(f"      - ID {l.get('id')}: {l.get('status')}")
                                else:
                                    print("   ❌ Tidak ada langganan dengan pelanggan_id 258")
                    else:
                        print(f"   ❌ Response bukan array: {type(data)}")
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
            else:
                print(f"   ❌ HTTP Status: {status_code}")
                print(f"   📄 Response: {response_text[:200]}...")
        else:
            print("   ❌ Invalid curl response")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # 3. Test endpoint langganan tanpa filter
    print("\n3️⃣ Testing GET /langganan/ (tanpa filter)")
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", f"{base_url}/langganan/"], capture_output=True, text=True, timeout=10
        )

        if len(result.stdout) >= 3:
            response_text = result.stdout[:-3]
            status_code = int(result.stdout[-3:])

            if status_code == 200:
                try:
                    data = json.loads(response_text)
                    if isinstance(data, list):
                        print(f"   ✅ Status: {status_code}")
                        print(f"   📊 Total langganan (tanpa filter): {len(data)}")

                        # Cek langganan ID 244
                        langganan_244 = [l for l in data if l.get("id") == 244]
                        if langganan_244:
                            print("   ✅ Langganan ID 244 ditemukan dalam data lengkap")
                        else:
                            print("   ❌ Langganan ID 244 TIDAK ditemukan dalam data lengkap")
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
            else:
                print(f"   ❌ HTTP Status: {status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # 4. Test generate invoice
    print("\n4️⃣ Testing POST /invoices/generate (untuk lihat error)")
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-w",
                "%{http_code}",
                "-X",
                "POST",
                "-H",
                "Content-Type: application/json",
                "-d",
                '{"langganan_id": 244}',
                f"{base_url}/invoices/generate",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if len(result.stdout) >= 3:
            response_text = result.stdout[:-3]
            status_code = int(result.stdout[-3:])

            print(f"   Status: {status_code}")
            if status_code != 200:
                try:
                    error_data = json.loads(response_text)
                    print(f"   ❌ Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   ❌ Error: {response_text}")
            else:
                print("   ✅ Invoice berhasil dibuat!")
        else:
            print("   ❌ Invalid curl response")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 60)
    print("🔍 Analisis Selesai!")
    print("\n💡 Jika ada perbedaan:")
    print("   1. Cek pagination/limit di backend")
    print("   2. Cek user permissions")
    print("   3. Cek filter yang aktif")


if __name__ == "__main__":
    test_api_with_curl()
