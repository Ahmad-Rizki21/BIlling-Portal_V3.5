# 📚 API Documentation - Artacom FTTH Billing System V2

## Overview
API ini digunakan untuk mengelola sistem billing FTTH (Fiber to the Home) Artacom. API ini dibangun menggunakan **FastAPI** dengan **SQLAlchemy** untuk database operations dan **Pydantic** untuk data validation.

## Base URL
```
Development: http://localhost:8000
Production:  https://billingftth.my.id
```

## Authentication
API menggunakan **OAuth2 Bearer Token** untuk autentikasi. Setiap request (kecuali login dan token refresh) harus menyertakan header:

```http
Authorization: Bearer <access_token>
```

### Mendapatkan Access Token
```http
POST /api/users/token
Content-Type: application/x-www-form-urlencoded

username=your_email@example.com&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 🏗️ API Endpoints

### Authentication Endpoints

#### Login
```http
POST /api/users/token
```
Melakukan autentikasi user dan mendapatkan access token.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
- `200 OK`: Token berhasil dibuat
- `401 Unauthorized`: Email atau password salah
- `403 Forbidden`: User tidak aktif

#### Refresh Token
```http
POST /api/users/refresh
```
Refresh access token menggunakan refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /api/users/logout
```
Logout dan blacklist token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 🏠 Dashboard Endpoints

#### Get Dashboard Data
```http
GET /api/dashboard/
Authorization: Bearer <token>
```
Mengambil data dashboard utama (statistik, charts, revenue summary).

**Response:**
```json
{
  "stat_cards": [
    {
      "title": "Total Pelanggan",
      "value": 1250,
      "icon": "users",
      "color": "primary"
    }
  ],
  "revenue_summary": {
    "total": 50000000,
    "periode": "Januari 2024",
    "breakdown": [...]
  },
  "charts": [...]
}
```

#### Get Customer Segmentation
```http
GET /api/dashboard/loyalitas-users-by-segment?segmen=setia
Authorization: Bearer <token>
```
Mengambil data segmentasi pelanggan berdasarkan loyalitas pembayaran.

**Query Parameters:**
- `segmen` (optional): Filter segment (`setia`, `lunas-telat`, `menunggak`)

### 👥 Pelanggan Endpoints

#### Create Pelanggan
```http
POST /api/pelanggan/
Authorization: Bearer <token>
```
Membuat pelanggan baru.

**Request Body:**
```json
{
  "nama": "John Doe",
  "email": "john@example.com",
  "no_telp": "08123456789",
  "no_ktp": "1234567890123456",
  "alamat": "Jl. Example No. 123",
  "id_brand": "JAKINET",
  "tanggal_instalasi": "2024-01-15"
}
```

**Response:**
```json
{
  "id": 123,
  "nama": "John Doe",
  "email": "john@example.com",
  "no_telp": "08123456789",
  "alamat": "Jl. Example No. 123",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Get All Pelanggan
```http
GET /api/pelanggan/
Authorization: Bearer <token>
```
Mengambil daftar pelanggan dengan pagination dan filter.

**Query Parameters:**
- `skip` (int): Offset untuk pagination (default: 0)
- `limit` (int): Jumlah records per halaman (default: 15, max: 100)
- `search` (string): Search berdasarkan nama, email, atau no_telp
- `alamat` (string): Filter berdasarkan alamat
- `id_brand` (string): Filter berdasarkan brand
- `fields` (string): Comma-separated fields untuk response optimization

**Response:**
```json
{
  "data": [
    {
      "id": 123,
      "nama": "John Doe",
      "email": "john@example.com",
      "no_telp": "08123456789"
    }
  ],
  "total_count": 1250,
  "skip": 0,
  "limit": 15
}
```

#### Get Pelanggan by ID
```http
GET /api/pelanggan/{pelanggan_id}
Authorization: Bearer <token>
```
Mengambil detail pelanggan berdasarkan ID.

**Response:**
```json
{
  "id": 123,
  "nama": "John Doe",
  "email": "john@example.com",
  "no_telp": "08123456789",
  "alamat": "Jl. Example No. 123",
  "harga_layanan": {
    "id": 1,
    "nama_paket": "Internet 50Mbps",
    "harga": 500000
  },
  "data_teknis": {
    "ip_pelanggan": "192.168.1.100",
    "vlan": 100
  }
}
```

#### Update Pelanggan
```http
PATCH /api/pelanggan/{pelanggan_id}
Authorization: Bearer <token>
```
Update data pelanggan.

**Request Body:**
```json
{
  "nama": "John Smith",
  "alamat": "Jl. Updated Address No. 456"
}
```

#### Delete Pelanggan
```http
DELETE /api/pelanggan/{pelanggan_id}
Authorization: Bearer <token>
```
Hapus pelanggan dan semua data terkait.

**Response:** `204 No Content`

#### Export Pelanggan to CSV
```http
GET /api/pelanggan/export/csv
Authorization: Bearer <token>
```
Export data pelanggan ke CSV dengan filter yang sama seperti GET.

**Query Parameters:**
- `skip` (int): Offset untuk pagination
- `limit` (int): Max 50,000 records
- `search`, `alamat`, `id_brand`: Filter parameters

#### Import Pelanggan from CSV
```http
POST /api/pelanggan/import
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
Import pelanggan dari file CSV.

**Request:**
```
file: [CSV file]
```

**CSV Template:**
```csv
Nama,No KTP,Email,No Telepon,Layanan,Alamat,Tanggal Instalasi (YYYY-MM-DD),ID Brand
John Doe,1234567890123456,john@example.com,08123456789,Internet 50Mbps,"Jl. Example No. 123",2024-01-15,JAKINET
```

### 📋 Data Teknis Endpoints

#### Create Data Teknis
```http
POST /api/data_teknis/
Authorization: Bearer <token>
```
Membuat data teknis untuk pelanggan.

**Request Body:**
```json
{
  "pelanggan_id": 123,
  "ip_pelanggan": "192.168.1.100",
  "vlan": 100,
  "sn_ont": "ALCL12345678",
  "port_odp": "ODP-01/P01",
  "port_olt": "1/GP1"
}
```

#### Get Data Teknis by Pelanggan
```http
GET /api/data_teknis/pelanggan/{pelanggan_id}
Authorization: Bearer <token>
```
Mengambil data teknis berdasarkan pelanggan ID.

#### Update Data Teknis
```http
PATCH /api/data_teknis/{data_teknis_id}
Authorization: Bearer <token>
```

### 💰 Invoice Endpoints

#### Create Invoice
```http
POST /api/invoices/
Authorization: Bearer <token>
```
Membuat invoice baru untuk pelanggan.

**Request Body:**
```json
{
  "pelanggan_id": 123,
  "periode": "2024-01",
  "tanggal_jatuh_tempo": "2024-01-31",
  "items": [
    {
      "deskripsi": "Internet 50Mbps",
      "jumlah": 1,
      "harga": 500000
    }
  ]
}
```

#### Get Invoices
```http
GET /api/invoices/
Authorization: Bearer <token>
```
Mengambil daftar invoice dengan filter.

**Query Parameters:**
- `pelanggan_id` (int): Filter berdasarkan pelanggan
- `status_invoice` (string): Filter status (`Draft`, `Menunggu Pembayaran`, `Lunas`, `Jatuh Tempo`)
- `periode` (string): Filter periode (`2024-01`)
- `skip`, `limit`: Pagination

#### Get Invoice by ID
```http
GET /api/invoices/{invoice_id}
Authorization: Bearer <token>
```

#### Update Invoice Status
```http
PATCH /api/invoices/{invoice_id}/status
Authorization: Bearer <token>
```
Update status invoice (misal: set ke `Lunas`).

### 🔧 Mikrotik Endpoints

#### Test Connection
```http
POST /api/mikrotik_servers/{server_id}/test
Authorization: Bearer <token>
```
Test koneksi ke Mikrotik server.

#### Sync Pelanggan
```http
POST /api/mikrotik_servers/{server_id}/sync/{pelanggan_id}
Authorization: Bearer <token>
```
Sync data pelanggan ke Mikrotik (create/update PPPoE secret).

#### Get Connection Health
```http
GET /api/mikrotik_servers/health
Authorization: Bearer <token>
```
Mengambil status koneksi semua Mikrotik servers.

### 📊 Reports Endpoints

#### Revenue Report
```http
GET /api/reports/revenue
Authorization: Bearer <token>
```
Mengambil laporan revenue.

**Query Parameters:**
- `start_date` (date): Start date (`YYYY-MM-DD`)
- `end_date` (date): End date (`YYYY-MM-DD`)
- `group_by` (string): Grouping (`month`, `brand`, `status`)

#### Customer Report
```http
GET /api/reports/customers
Authorization: Bearer <token>
```
Mengambil laporan pelanggan.

**Query Parameters:**
- `segment` (string): Customer segment
- `status` (string): Customer status
- `brand` (string): Filter brand

### 📱 Notifications Endpoints

#### Get Notifications
```http
GET /api/notifications/
Authorization: Bearer <token>
```
Mengambil daftar notifications untuk user.

#### Mark as Read
```http
PATCH /api/notifications/{notification_id}/read
Authorization: Bearer <token>
```

### 📋 Activity Logs Endpoints

#### Get Activity Logs
```http
GET /api/activity-logs/
Authorization: Bearer <token>
```
Mengambil log aktivitas sistem.

**Query Parameters:**
- `skip`, `limit`: Pagination
- `user_id` (int): Filter berdasarkan user
- `action` (string): Filter action
- `start_date`, `end_date`: Filter date range

## 🔒 Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message description",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

### Common HTTP Status Codes

#### Success Codes
- `200 OK`: Request berhasil
- `201 Created`: Resource berhasil dibuat
- `204 No Content`: Resource berhasil dihapus

#### Client Error Codes
- `400 Bad Request`: Request tidak valid
- `401 Unauthorized`: Tidak terautentikasi
- `403 Forbidden`: Tidak memiliki permission
- `404 Not Found`: Resource tidak ditemukan
- `409 Conflict`: Data conflict (duplicate)
- `422 Unprocessable Entity`: Validation error

#### Server Error Codes
- `500 Internal Server Error`: Error server
- `503 Service Unavailable`: Maintenance mode

### Validation Errors
```json
{
  "detail": {
    "message": "Validation failed",
    "errors": [
      {
        "field": "email",
        "message": "Email format is invalid"
      }
    ]
  }
}
```

## 📝 Data Models

### Pelanggan Model
```json
{
  "id": 123,
  "nama": "John Doe",
  "email": "john@example.com",
  "no_telp": "08123456789",
  "no_ktp": "1234567890123456",
  "alamat": "Jl. Example No. 123",
  "alamat_2": "RT 01/RW 02",
  "blok": "A",
  "unit": "123",
  "tanggal_instalasi": "2024-01-15",
  "id_brand": "JAKINET",
  "status": "Aktif",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Data Teknis Model
```json
{
  "id": 456,
  "pelanggan_id": 123,
  "ip_pelanggan": "192.168.1.100",
  "password_pppoe": "encrypted_password",
  "vlan": 100,
  "sn_ont": "ALCL12345678",
  "port_odp": "ODP-01/P01",
  "port_olt": "1/GP1",
  "status": "Aktif",
  "mikrotik_server_id": 1,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Invoice Model
```json
{
  "id": 789,
  "nomor_invoice": "INV-2024-001",
  "pelanggan_id": 123,
  "periode": "2024-01",
  "tanggal_invoice": "2024-01-01",
  "tanggal_jatuh_tempo": "2024-01-31",
  "total_harga": 500000,
  "status_invoice": "Menunggu Pembayaran",
  "paid_at": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 🚀 Rate Limiting

### Rate Limit Rules
- **Authentication endpoints**: 5 requests per 5 minutes per IP
- **General API endpoints**: 100 requests per minute per user
- **Export endpoints**: 10 requests per hour per user
- **Import endpoints**: 5 requests per hour per user

### Rate Limit Response
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

## 🌐 WebSocket

### Real-time Notifications
Connect ke WebSocket untuk real-time notifications:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications?token=<access_token>');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Notification:', data);
};
```

### WebSocket Message Format
```json
{
  "type": "new_invoice",
  "message": "Invoice baru telah dibuat",
  "data": {
    "invoice_id": 789,
    "nomor_invoice": "INV-2024-001",
    "pelanggan_nama": "John Doe"
  },
  "timestamp": "2024-01-15T10:00:00Z"
}
```

## 🔧 Development

### Local Development Setup
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Setup environment variables (copy `.env.example` ke `.env`)
4. Run database migrations: `alembic upgrade head`
5. Start development server: `uvicorn app.main:app --reload`

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@localhost/billing_db
SECRET_KEY=your-secret-key
XENDIT_API_KEY_JAKINET=your-xendit-key
XENDIT_CALLBACK_TOKEN_JAKINET=your-callback-token
```

### Testing
Run tests: `pytest tests/`

## 📞 Support

### API Support
- **Documentation**: [API Documentation](./API_DOCUMENTATION.md)
- **Naming Conventions**: [Naming Conventions Guide](./NAMING_CONVENTIONS.md)
- **Architecture**: [Architecture Overview](./ARCHITECTURE.md)

### Contact
- **Developer Team**: dev@artacom.id
- **Support**: support@artacom.id
- **Documentation**: docs@artacom.id

---

## 📋 Changelog

### Version 2.0.0
- ✅ Authentication security improvements
- ✅ Service layer architecture
- ✅ Code deduplication and optimization
- ✅ Enhanced error handling
- ✅ Real-time notifications via WebSocket
- ✅ Improved API documentation
- ✅ Rate limiting implementation
- ✅ CSV import/export optimization
- ✅ Magic numbers elimination
- ✅ Naming conventions standardization

### Version 1.0.0
- Initial release with basic CRUD operations
- Mikrotik integration
- Invoice management
- Customer management