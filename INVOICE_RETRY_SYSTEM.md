# 🔄 Sistem Retry Invoice Gagal

## 📋 Overview

Sistem ini menangani invoice yang gagal dibuat payment link-nya di Xendit. Ketika scheduler job membuat invoice tapi Xendit API error, sistem akan secara otomatis mecoba lagi (retry) sampai berhasil atau mencapai batas maksimal.

## 🎯 Fitur Utama

### ✅ Automatic Retry System
- **Job Scheduler**: `job_retry_failed_invoices()` jalan setiap 1 jam
- **Max Retry**: 3 kali percobaan
- **Interval**: 1 jam antara retry
- **Batch Processing**: 50 invoice per batch

### ✅ Manual Override
- **Single Retry**: `POST /invoices/{id}/retry-xendit`
- **Batch Retry**: `POST /invoices/batch-retry-xendit`
- **Failed List**: `GET /invoices/missing-payment-links`

### ✅ Real-time Notifications
- **WebSocket Alerts**: Notifikasi ke admin jika invoice tetap gagal
- **Detailed Logging**: Log lengkap untuk setiap percobaan
- **Status Tracking**: Monitoring status retry per invoice

## 🗄️ Database Schema

### Tambahan Field di `invoices` table:

```sql
xendit_retry_count    BIGINT DEFAULT 0     -- Jumlah retry
xendit_last_retry     TIMESTAMP NULL       -- Waktu retry terakhir
xendit_error_message  TEXT NULL            -- Error message terakhir
xendit_status         VARCHAR(50) DEFAULT 'pending' -- Status pembuatan payment link
```

### Status Values:
- `pending`: Menunggu proses
- `processing`: Sedang diproses
- `completed`: Payment link berhasil dibuat
- `failed`: Gagal (akan di-retry)

## 🚀 Setup Instructions

### 1. Database Migration

```bash
# Jalankan migration script
psql -U username -d database_name -f add_xendit_retry_fields.sql
```

### 2. Enable Scheduler

Di `app/main.py`, uncomment baris berikut:

```python
# Retry invoice yang gagal dibuat payment link setiap 1 jam
scheduler.add_job(job_retry_failed_invoices, 'interval', hours=1, id="retry_failed_invoices_job", replace_existing=True)
```

### 3. Restart Application

```bash
# Restart aplikasi untuk apply perubahan
uvicorn app.main:app --reload
```

## 📡 API Endpoints

### 1. Get Failed Invoices
```http
GET /invoices/missing-payment-links
Authorization: Bearer <token>
Permission: view_invoices
```

Response:
```json
[
  {
    "id": 123,
    "invoice_number": "INV-20241201-ABC123",
    "pelanggan": {
      "nama": "John Doe",
      "email": "john@example.com"
    },
    "total_harga": 150000,
    "xendit_retry_count": 2,
    "xendit_error_message": "Network timeout"
  }
]
```

### 2. Manual Retry Single Invoice
```http
POST /invoices/{invoice_id}/retry-xendit
Authorization: Bearer <token>
Permission: edit_invoices
```

Response:
```json
{
  "success": true,
  "message": "Payment link berhasil dibuat untuk invoice INV-20241201-ABC123",
  "payment_link": "https://xendit.co/invoices/xyz",
  "xendit_id": "xendit_invoice_id",
  "pelanggan": "John Doe"
}
```

### 3. Batch Retry Multiple Invoices
```http
POST /invoices/batch-retry-xendit
Authorization: Bearer <token>
Permission: edit_invoices
```

Response:
```json
{
  "success": true,
  "message": "Batch retry selesai: 3 berhasil, 1 gagal",
  "total_processed": 4,
  "success_count": 3,
  "failed_count": 1,
  "results": [
    {
      "invoice_id": 123,
      "invoice_number": "INV-20241201-ABC123",
      "success": true,
      "message": "Payment link berhasil dibuat",
      "payment_link": "https://xendit.co/invoices/xyz"
    },
    {
      "invoice_id": 124,
      "invoice_number": "INV-20241201-DEF456",
      "success": false,
      "message": "Customer data incomplete"
    }
  ]
}
```

## 🔄 Alur Kerja Sistem

### 1. Saat Invoice Gagal Dibuat
```
Scheduler Job → Create Invoice → Xendit API Error
    ↓
Save Invoice without payment_link
    ↓
Set xendit_status = 'failed'
    ↓
Set xendit_retry_count = 0
    ↓
Log error message
```

### 2. Automatic Retry Process
```
job_retry_failed_invoices() (setiap jam)
    ↓
Cari invoice dengan:
  - xendit_id IS NULL
  - status_invoice = 'Belum Dibayar'
  - xendit_retry_count < 3
  - xendit_last_retry > 1 jam lalu
    ↓
Untuk setiap invoice:
  - Update status ke 'processing'
  - Coba buat payment link ke Xendit
  - Jika berhasil:
    - Update payment_link, xendit_id
    - Set xendit_status = 'completed'
  - Jika gagal:
    - Increment xendit_retry_count
    - Update xendit_error_message
    - Set xendit_status = 'failed'
```

### 3. Manual Admin Intervention
```
Admin lihat invoice gagal →
GET /invoices/missing-payment-links
    ↓
Admin pilih aksi:
  - Single retry: POST /invoices/{id}/retry-xendit
  - Batch retry: POST /invoices/batch-retry-xendit
    ↓
System proses retry dengan priority HIGH
    ↓
Return detail hasilnya
```

## 📊 Monitoring & Logging

### 1. System Logs
```bash
# Monitoring job execution
grep "job_retry_failed_invoices" /var/log/app.log

# Tracking individual invoice retries
grep "Retrying invoice" /var/log/app.log

# Success/failure notifications
grep "MANUAL RETRY\|BATCH retry" /var/log/app.log
```

### 2. Database Queries
```sql
-- Cek invoice yang masih gagal
SELECT COUNT(*) FROM invoices
WHERE xendit_id IS NULL
  AND status_invoice = 'Belum Dibayar'
  AND xendit_retry_count >= 3;

-- Monitor retry attempts
SELECT invoice_number, xendit_retry_count, xendit_status, xendit_error_message
FROM invoices
WHERE xendit_status = 'failed'
ORDER BY xendit_last_retry DESC;

-- Success rate analysis
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_invoices,
  COUNT(CASE WHEN xendit_id IS NOT NULL THEN 1 END) as successful,
  COUNT(CASE WHEN xendit_id IS NULL THEN 1 END) as failed
FROM invoices
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 3. Real-time Notifications
- **WebSocket**: Notifikasi real-time ke admin dashboard
- **Alert Types**: Error, Warning, Success
- **Data Included**: failed_count, max_retry, action_url

## 🛠️ Troubleshooting

### Common Issues:

#### 1. Job Tidak Jalan
```bash
# Cek scheduler status
grep "Scheduler has been started" /var/log/app.log

# Cek job registration
grep "retry_failed_invoices_job" /var/log/app.log
```

#### 2. Notification Tidak Terkirim
```bash
# Cek WebSocket connection
grep "WebSocket" /var/log/app.log | tail -20

# Cek admin user roles
SELECT u.id, u.username, r.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE r.name IN ('admin', 'super_admin');
```

#### 3. Database Migration Issues
```bash
# Cek apakah fields sudah ada
\d invoices

# Manual migration
psql -U username -d database_name -c "
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS xendit_retry_count BIGINT DEFAULT 0;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS xendit_last_retry TIMESTAMP NULL;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS xendit_error_message TEXT NULL;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS xendit_status VARCHAR(50) DEFAULT 'pending';
"
```

## 📈 Performance Considerations

### 1. Database Optimization
- **Indexes**: Added indexes on retry fields for fast queries
- **Batch Processing**: Process 50 invoices per batch
- **Connection Pooling**: Use existing database pool

### 2. API Rate Limiting
- **Xendit API**: Use existing rate limiter with normal priority
- **Manual Retry**: High priority for admin requests
- **Automatic Retry**: Normal priority to avoid rate limit

### 3. Memory Management
- **Batch Size**: 50 invoices per batch
- **Connection Cleanup**: Proper cleanup after each batch
- **Error Handling**: Continue processing even if some fail

## 🔒 Security Features

### 1. Access Control
- **Permissions**: `edit_invoices` required for retry operations
- **Role-based**: Only admin/super_admin receive notifications
- **Audit Trail**: All retry attempts logged

### 2. Data Validation
- **Input Validation**: Validate invoice data before retry
- **Error Sanitization**: Sanitize error messages before logging
- **Permission Checks**: Verify user permissions on each request

## 🎉 Benefits

### ✅ Business Benefits
- **No Lost Revenue**: All invoices are saved and retried
- **Customer Satisfaction**: Faster payment link creation
- **Admin Efficiency**: Manual override when needed
- **Real-time Monitoring**: Immediate alerts for issues

### ✅ Technical Benefits
- **Graceful Degradation**: System works even if Xendit is down
- **Scalable Architecture**: Handles large volumes of invoices
- **Comprehensive Logging**: Full audit trail
- **Automated Recovery**: Minimal manual intervention needed

---

## 📞 Support

Jika ada masalah dengan sistem retry invoice:
1. Cek logs untuk error messages
2. Verify database migration success
3. Check scheduler job status
4. Review API rate limits
5. Contact development team with logs

Created: 2025-10-31
Version: 1.0.0
Status: Production Ready