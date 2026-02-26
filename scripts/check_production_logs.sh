#!/bin/bash

# ====================================================================
# DIAGNOSTIC SCRIPT: PRODUCTION LOGGING & HEALTH CHECK
# ====================================================================
# Sesuai saran dari laporan: "Log Server (terbaru): Kosong"
# Jalankan script ini di server production (Ubuntu) untuk diagnosa.

echo "===================================================================="
echo "🔍 MEMULAI DIAGNOSA SISTEM LOGGING"
echo "===================================================================="

# 1. Cek User dan Direktori Saat Ini
echo "[1/6] Info Lingkungan:"
echo "User: $(whoami)"
echo "Path: $(pwd)"
echo ""

# 2. Cari Lokasi Log Aplikasi
echo "[2/6] Memeriksa file log aplikasi di folder local 'logs/':"
if [ -d "logs" ]; then
    echo "✅ Folder logs/ ditemukan."
    ls -lh logs/
else
    echo "❌ Folder logs/ TIDAK ditemukan di direktori saat ini."
    echo "Mencoba mencari file app.log di seluruh sistem (mungkin butuh waktu)..."
    find / -name "app.log" 2>/dev/null | head -n 3
fi
echo ""

# 3. Jalankan perintah deteksi dini (sesuai saran laporan)
echo "[3/6] Menjalankan journalctl untuk deteksi error (30 baris terakhir):"
sudo journalctl -n 30 --since "today" | grep -i "error\|fail\|warn\|xendit\|invoice"
if [ $? -ne 0 ]; then
    echo "TIDAK ditemukan error kritis di journalctl untuk hari ini."
fi
echo ""

# 4. Cek Status rsyslog dan Config logrotate
echo "[4/6] Memeriksa rsyslog dan logrotate:"
systemctl is-active rsyslog >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ rsyslog AKTIF."
else
    echo "❌ rsyslog MATI atau tidak terinstall."
fi

if [ -f "/etc/logrotate.d/rsyslog" ]; then
    echo "✅ Konfigurasi logrotate rsyslog ditemukan."
else
    echo "⚠️ Konfigurasi logrotate rsyslog tidak ditemukan di folder standar."
fi
echo ""

# 5. Cek Ukuran file syslog dan portal-billing.log
echo "[5/6] Memeriksa file log sistem:"
LOGS_TO_CHECK=("/var/log/syslog" "/var/log/portal-billing.log")
for logfile in "${LOGS_TO_CHECK[@]}"; do
    if [ -f "$logfile" ]; then
        SIZE=$(du -sh "$logfile" | cut -f1)
        MOD=$(stat -c %y "$logfile")
        echo "✅ $logfile ditemukan. Ukuran: $SIZE. Terakhir update: $MOD"
    else
        echo "❌ $logfile TIDAK ditemukan."
    fi
done
echo ""

# 6. Kesimpulan & Saran
echo "[6/6] SARAN TINDAKAN:"
echo "--------------------------------------------------------------------"
echo "Jika folder logs/ aplikasi kosong atau tidak ditemukan:"
echo "1. Pastikan aplikasi memiliki izin tulis (write permission) ke folder logs."
echo "2. Update file .env dengan path log yang benar, contoh:"
echo "   LOG_PATH_APP=/var/www/billing/logs/app.log"
echo "3. Restart PM2 atau service aplikasi Anda."
echo "--------------------------------------------------------------------"
echo "Selesai."
