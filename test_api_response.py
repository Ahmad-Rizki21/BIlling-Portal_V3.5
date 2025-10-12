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

    print("[TEST] Testing API Endpoints...")
    print("=" * 60)

    # 1. Test endpoint pelanggan
    print("\n[1] Testing GET /pelanggan/")
    status, response, error = run_curl(f"{base_url}/pelanggan/")
    if status == 200:
        try:
            data = json.loads(response)
            pelanggan_list = data if isinstance(data, list) else data.get("data", [])
            print(f"   [OK] Status: {status}")
            print(f"   [DATA] Total pelanggan: {len(pelanggan_list)}")

            # Cek apakah pelanggan ID 258 ada
            pelanggan_258 = [p for p in pelanggan_list if p.get("id") == 258]
            if pelanggan_258:
                print(f"   [OK] Pelanggan ID 258 ditemukan: {pelanggan_258[0].get('nama', 'N/A')}")
            else:
                print("   [ERROR] Pelanggan ID 258 TIDAK ditemukan dalam response!")

                # Cari ID terdekat
                if pelanggan_list:
                    max_id = max(p.get("id", 0) for p in pelanggan_list)
                    min_id = min(p.get("id", 0) for p in pelanggan_list)
                    print(f"   [DATA] Range ID pelanggan: {min_id} - {max_id}")
        except json.JSONDecodeError:
            print("   [ERROR] Cannot parse JSON response")
    else:
        print(f"   [ERROR] Status: {status}")
        print(f"   [ERROR] Error: {error}")

    # 2. Test endpoint langganan for invoice selection
    print("\n[2] Testing GET /langganan/?for_invoice_selection=true")
    status, response, error = run_curl(f"{base_url}/langganan/?for_invoice_selection=true")
    if status == 200:
        try:
            data = json.loads(response)
            langganan_list = data if isinstance(data, list) else data.get("data", [])
            print(f"   [OK] Status: {status}")
            print(f"   [DATA] Total langganan: {len(langganan_list)}")

            # Cek apakah langganan ID 244 ada
            langganan_244 = [l for l in langganan_list if l.get("id") == 244]
            if langganan_244:
                print("   [OK] Langganan ID 244 ditemukan")
            else:
                print("   [ERROR] Langganan ID 244 TIDAK ditemukan dalam response!")
        except json.JSONDecodeError:
            print("   [ERROR] Cannot parse JSON response")
    else:
        print(f"   [ERROR] Status: {status}")

    # 3. Test endpoint langganan tanpa filter
    print("\n[3] Testing GET /langganan/ (tanpa filter)")
    status, response, error = run_curl(f"{base_url}/langganan/")
    if status == 200:
        try:
            data = json.loads(response)
            langganan_list = data if isinstance(data, list) else data.get("data", [])
            print(f"   [OK] Status: {status}")
            print(f"   [DATA] Total langganan (tanpa filter): {len(langganan_list)}")
        except json.JSONDecodeError:
            print("   [ERROR] Cannot parse JSON response")
    else:
        print(f"   [ERROR] Status: {status}")

    print("\n" + "=" * 60)
    print("[TEST] Analisis Selesai!")
    print("\n[INFO] Jika ada perbedaan antara database dan API response:")
    print("   1. Cek pagination/limit di backend")
    print("   2. Cek user permissions/role")
    print("   3. Cek filter yang aktif di endpoint")


if __name__ == "__main__":
    test_api_endpoints()
