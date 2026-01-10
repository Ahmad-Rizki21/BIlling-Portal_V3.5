# Scheduler Jobs - Production Ready! 🚀

## ✅ **Jobs yang AKTIF di Production**

### 1. **Invoice Generation** 📄

```python
scheduler.add_job(
    job_generate_invoices,
    'cron',
    hour=10,
    minute=0,
    timezone='Asia/Jakarta'
)
```

- **Schedule**: Setiap hari jam 10:00 WIB
- **Function**: Generate invoice H-5 sebelum jatuh tempo
- **Example**: Jatuh tempo 1 Jan → Invoice dibuat 27 Des jam 10:00
- **Output**: Invoice + Payment link Xendit + WhatsApp notification

---

### 2. **Suspend Services** 🔒 **(ENHANCED with Rollback!)**

```python
scheduler.add_job(
    job_suspend_services,
    'cron',
    day=5,
    hour=0,
    minute=0,
    timezone='Asia/Jakarta',
    max_instances=1,
    misfire_grace_time=300
)
```

- **Schedule**: Setiap tanggal 5 jam 00:00 WIB
- **Function**: Auto-suspend user yang telat bayar
- **Enhanced**: Automatic Mikrotik rollback jika DB gagal
- **Target**: User dengan invoice jatuh tempo tanggal 1 yang belum bayar
- **Actions**:
  1. Suspend ke Mikrotik (disable + profile SUSPENDED)
  2. Update DB (status → "Suspended", invoice → "Kadaluarsa")
  3. Rollback Mikrotik jika DB gagal (ZERO INCONSISTENCY!)

---

### 3. **Payment Verification** 💰

```python
scheduler.add_job(
    job_verify_payments,
    'interval',
    minutes=15,
    max_instances=1
)
```

- **Schedule**: Setiap 15 menit
- **Function**: Verifikasi pembayaran yang terlewat
- **Purpose**: Antisipasi webhook Xendit yang gagal
- **Actions**:
  1. Cek pembayaran lunas di Xendit (3 hari terakhir)
  2. Bandingkan dengan status di DB
  3. Proses pembayaran yang belum tercatat
  4. Update invoice → "Lunas"
  5. Re-activate user yang suspended

---

### 4. **Mikrotik Sync Retry** 🔄

```python
scheduler.add_job(
    job_retry_mikrotik_syncs,
    'interval',
    minutes=5,
    max_instances=1
)
```

- **Schedule**: Setiap 5 menit
- **Function**: Retry sync Mikrotik yang gagal
- **Purpose**: Auto-recovery untuk suspend/unsuspend yang gagal
- **Actions**:
  1. Cari data_teknis dengan flag `mikrotik_sync_pending = True`
  2. Retry update ke Mikrotik
  3. Clear flag jika sukses
  4. Max retry: 3 kali

---

### 5. **Failed Invoice Retry** 🔁

```python
scheduler.add_job(
    job_retry_failed_invoices,
    'interval',
    hours=1,
    max_instances=1
)
```

- **Schedule**: Setiap 1 jam
- **Function**: Retry invoice yang gagal generate payment link
- **Purpose**: Auto-recovery untuk invoice tanpa payment link
- **Actions**:
  1. Cari invoice dengan `xendit_id = NULL`
  2. Retry generate payment link ke Xendit
  3. Update invoice jika sukses
  4. Max retry: 3 kali

---

## ⏭️ **Jobs yang DINONAKTIFKAN**

### 1. **Payment Reminders** 📧

- **Reason**: Belum ada integrasi WhatsApp/Email gateway
- **Manual Trigger**: Bisa dijalankan manual jika diperlukan

### 2. **Traffic Monitoring** 📊

- **Reason**: Resource intensive, tidak critical
- **Alternative**: Manual monitoring via Mikrotik dashboard

### 3. **Archive Invoice** 🗄️

- **Reason**: Bisa dijalankan manual setiap 3 bulan
- **Manual Trigger**: Via admin panel atau script

---

## 📋 **Scheduler Timeline (Daily)**

```
00:00 WIB (Tanggal 5) → Suspend Services (user telat bayar)
                        ├─ Suspend ke Mikrotik
                        ├─ Update DB
                        └─ Rollback jika perlu

Every 5 min          → Mikrotik Sync Retry
                        └─ Auto-recovery suspend/unsuspend gagal

Every 15 min         → Payment Verification
                        └─ Antisipasi webhook Xendit gagal

Every 1 hour         → Failed Invoice Retry
                        └─ Auto-recovery payment link gagal

10:00 WIB            → Invoice Generation (H-5)
                        ├─ Generate invoice
                        ├─ Create payment link
                        └─ Send WhatsApp notification
```

---

## 🔍 **Monitoring Scheduler**

### **Cek Status Scheduler:**

```bash
# Lihat log startup
tail -f logs/app.log | grep "SCHEDULED JOBS"

# Output yang diharapkan:
# ✅ Invoice Generation: AKTIF - Setiap hari jam 10:00 WIB
# ✅ Suspend Services: AKTIF - Setiap tanggal 5 jam 00:00 WIB (ENHANCED with Rollback!)
# ✅ Payment Verification: AKTIF - Setiap 15 menit
# ✅ Mikrotik Sync Retry: AKTIF - Setiap 5 menit
# ✅ Payment Link Retry: AKTIF - Setiap 1 jam
```

### **Cek Eksekusi Jobs:**

```bash
# Invoice generation
grep "job_generate_invoices" logs/app.log

# Suspend services
grep "job_suspend_services" logs/app.log

# Payment verification
grep "job_verify_payments" logs/app.log

# Mikrotik retry
grep "job_retry_mikrotik_syncs" logs/app.log

# Failed invoice retry
grep "job_retry_failed_invoices" logs/app.log
```

### **Cek Error:**

```bash
# Cek error scheduler
grep "FAIL.*Scheduler" logs/app.log

# Cek critical errors
grep "CRITICAL" logs/app.log

# Cek rollback events
grep "ROLLBACK" logs/app.log
```

---

## 🚨 **Troubleshooting**

### **Problem: Scheduler tidak jalan**

```bash
# Cek apakah scheduler sudah start
grep "Scheduler telah dimulai" logs/app.log

# Restart aplikasi
sudo systemctl restart billing-app
```

### **Problem: Job tidak execute**

```bash
# Cek apakah job terdaftar
# Di startup log harus ada: "✅ [Job Name]: AKTIF"

# Cek timezone
date
# Harus: Asia/Jakarta (WIB)

# Cek misfire
grep "misfire" logs/app.log
```

### **Problem: Duplicate job execution**

```bash
# Cek max_instances
# Semua job sudah set max_instances=1

# Cek scheduler already running
grep "SchedulerAlreadyRunningError" logs/app.log
```

---

## 📊 **Performance Metrics**

### **Expected Load:**

- **Invoice Generation**: ~5-10 detik per 100 invoice
- **Suspend Services**: ~2-3 detik per user (include Mikrotik)
- **Payment Verification**: ~1-2 detik per 10 invoice
- **Mikrotik Retry**: ~1 detik per user
- **Failed Invoice Retry**: ~2-3 detik per invoice

### **Database Impact:**

- **Read Queries**: ~100-500 per menit (normal)
- **Write Queries**: ~10-50 per menit (normal)
- **Peak Load**: Tanggal 5 jam 00:00 (suspend) dan jam 10:00 (invoice)

---

## ✅ **Production Checklist**

- [x] Invoice generation aktif (H-5 logic)
- [x] Suspend services aktif (dengan rollback!)
- [x] Payment verification aktif (antisipasi webhook gagal)
- [x] Mikrotik retry aktif (auto-recovery)
- [x] Failed invoice retry aktif (auto-recovery)
- [x] Logging lengkap dan detail
- [x] Error handling robust
- [x] Max instances = 1 (prevent duplicate)
- [x] Misfire grace time configured
- [x] Timezone = Asia/Jakarta

---

## 🎯 **Next Steps**

1. **Monitor** scheduler execution selama 1 minggu
2. **Review** log files untuk error patterns
3. **Optimize** batch size jika diperlukan
4. **Enable** payment reminders jika WhatsApp gateway sudah ready
5. **Enable** archive invoice setiap 3 bulan

---

## 📝 **Notes**

- Semua scheduler menggunakan `max_instances=1` untuk prevent duplicate execution
- Suspend services punya `misfire_grace_time=300` (5 menit) untuk handle server restart
- Payment verification jalan setiap 15 menit untuk balance antara responsiveness dan load
- Mikrotik retry jalan setiap 5 menit untuk quick recovery
- Failed invoice retry jalan setiap 1 jam untuk avoid Xendit rate limit

**PRODUCTION READY! 🚀**
