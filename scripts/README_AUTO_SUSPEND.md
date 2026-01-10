# Auto Suspend Overdue Invoice - Quick Guide

## 🚀 Cara Menjalankan Script (URGENT)

### 1. Testing Mode (Dry Run) - Cek dulu tanpa ubah data

```bash
cd /home/ahmad/Desktop/Projects/Billing-Jelantik
python3 scripts/auto_suspend_overdue.py --dry-run
```

### 2. Live Mode (Execute) - Langsung suspend user

```bash
cd /home/ahmad/Desktop/Projects/Billing-Jelantik
python3 scripts/auto_suspend_overdue.py --execute
```

### 3. Cek tanggal tertentu

```bash
python3 scripts/auto_suspend_overdue.py --execute --check-date 2026-01-05
```

## 📋 Apa yang Dilakukan Script?

1. **Cek User Overdue**: Cari user yang:

   - Invoice sudah jatuh tempo (status "Belum Dibayar" atau "Expired")
   - Status langganan masih "Aktif" (harusnya sudah "Suspended")
   - Punya data teknis dan Mikrotik server

2. **Suspend ke Mikrotik**:

   - Disable PPPoE secret (disabled = yes)
   - Ubah profile PPPoE ke "SUSPENDED"
   - Disconnect koneksi aktif user

3. **Update Database**:

   - Ubah status langganan dari "Aktif" ke "Suspended"

4. **Generate Report**:
   - Summary hasil suspend
   - Detail user yang di-suspend
   - Error log jika ada yang gagal
   - File JSON di folder `logs/`

## ⏰ Setup Cron untuk Auto Run Setiap Tanggal 5 Jam 00:00

### Edit crontab:

```bash
crontab -e
```

### Tambahkan baris ini:

```bash
# Auto suspend overdue invoices setiap tanggal 5 jam 00:00
0 0 5 * * cd /home/ahmad/Desktop/Projects/Billing-Jelantik && /usr/bin/python3 scripts/auto_suspend_overdue.py --execute >> logs/auto_suspend_cron.log 2>&1
```

### Cek crontab sudah terdaftar:

```bash
crontab -l
```

## 📊 Output Script

Script akan menampilkan:

- ✅ User yang berhasil di-suspend
- ❌ User yang gagal di-suspend (dengan error detail)
- ⏭️ User yang sudah suspended sebelumnya
- 📊 Summary total per lokasi dan server

## 🔍 Contoh Output

```
🚀 AUTO SUSPEND OVERDUE INVOICES
======================================================================
📅 Check Date: 2026-01-05
🔍 Mode: LIVE EXECUTION
======================================================================

📊 Found 15 users with overdue invoices

──────────────────────────────────────────────────────────────────────
📍 Location: Waringin
🖥️  Server: MikrotikA (192.168.1.1)
👥 Users: 5
──────────────────────────────────────────────────────────────────────

[1/5] 🔄 Processing: Budi Santoso
   📧 Email: budi@example.com
   📞 Phone: 081234567890
   🆔 PPPoE: budi_waringin
   📄 Invoice: INV/2025/12/001
   📅 Due Date: 2025-12-05
   💰 Amount: Rp 350,000
   📊 Status: Belum Dibayar
   ✅ Mikrotik: PPPoE secret disabled and profile changed to SUSPENDED
   ✅ Mikrotik: Active connection disconnected
   ✅ Database: Langganan status updated to Suspended
   ✅ SUCCESS: User suspended successfully
```

## 📁 File Log

Hasil eksekusi disimpan di:

```
logs/auto_suspend_results_YYYYMMDD_HHMMSS.json
```

Format JSON:

```json
{
  "total_checked": 15,
  "total_suspended": 14,
  "success_count": 14,
  "failed_count": 1,
  "suspended_users": [
    {
      "nama": "Budi Santoso",
      "id_pelanggan": "budi_waringin",
      "invoice_number": "INV/2025/12/001",
      "due_date": "2025-12-05",
      "amount": 350000
    }
  ],
  "failed_details": [...]
}
```

## ⚠️ Troubleshooting

### Error: "No module named 'app'"

```bash
# Pastikan run dari root project
cd /home/ahmad/Desktop/Projects/Billing-Jelantik
python3 scripts/auto_suspend_overdue.py --execute
```

### Error: "Database connection failed"

```bash
# Cek file .env sudah ada dan benar
cat .env | grep DATABASE_URL
```

### Error: "Mikrotik connection failed"

- Cek Mikrotik server online
- Cek username/password Mikrotik di database
- Cek port API Mikrotik (default 8728) terbuka

## 🎯 Tips

1. **Selalu test dulu dengan --dry-run** sebelum execute
2. **Cek log file** setelah eksekusi untuk detail
3. **Monitor cron log** untuk auto-run: `tail -f logs/auto_suspend_cron.log`
4. **Backup database** sebelum run pertama kali

## 📞 Support

Jika ada error atau pertanyaan, cek:

1. File log di `logs/auto_suspend_results_*.json`
2. Cron log di `logs/auto_suspend_cron.log`
3. Application log di `logs/` folder
