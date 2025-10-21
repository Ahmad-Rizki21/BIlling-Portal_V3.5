# 📋 Naming Conventions Guide

## Overview
Dokumen ini mendefinisikan standar naming conventions untuk proyek Artacom FTTH Billing System V2 untuk konsistensi dan maintainability.

## Python Naming Conventions

### 1. Variables and Functions
**Gunakan `snake_case` untuk semua variable names dan function names:**

```python
# ✅ BENAR
pelanggan_name = "John Doe"
def create_pelanggan_data():
    pass

# ❌ SALAH
pelangganName = "John Doe"
def createPelangganData():
    pass
```

### 2. Class Names
**Gunakan `PascalCase` untuk semua class names:**

```python
# ✅ BENAR
class PelangganService:
    pass

class InvoiceProcessor:
    pass

# ❌ SALAH
class pelangganService:
    pass

class invoice_processor:
    pass
```

### 3. Constants
**Gunakan `UPPER_SNAKE_CASE` untuk constants:**

```python
# ✅ BENAR
MAX_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"

# ❌ SALAH
maxPageSize = 100
defaultTimeout = 30
apiBaseUrl = "https://api.example.com"
```

### 4. Private Members
**Gunakan underscore prefix (`_`) untuk private members:**

```python
# ✅ BENAR
class PelangganService:
    def __init__(self):
        self._db_connection = None

    def _validate_data(self, data):
        pass

# ❌ SALAH
class PelangganService:
    def __init__(self):
        self.dbConnection = None

    def validateData(self, data):
        pass
```

## Database Naming Conventions

### 1. Table Names
**Gunakan `snake_case` plural untuk table names:**

```sql
-- ✅ BENAR
pelanggans
invoices
data_teknis_records
mikrotik_servers

-- ❌ SALAH
pelanggan
invoice
dataTeknis
mikrotikServer
```

### 2. Column Names
**Gunakan `snake_case` untuk column names:**

```sql
-- ✅ BENAR
CREATE TABLE pelanggans (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    no_ktp VARCHAR(16) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ❌ SALAH
CREATE TABLE pelanggans (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    noKtp VARCHAR(16) UNIQUE NOT NULL,
    createdAt TIMESTAMP DEFAULT NOW()
);
```

### 3. Foreign Key Columns
**Gunakan format `{table_name}_id` untuk foreign keys:**

```sql
-- ✅ BENAR
pelanggan_id INTEGER REFERENCES pelanggans(id)
mikrotik_server_id INTEGER REFERENCES mikrotik_servers(id)
harga_layanan_id INTEGER REFERENCES harga_layanans(id)

-- ❌ SALAH
pelangganID INTEGER REFERENCES pelanggans(id)
mikrotikServerID INTEGER REFERENCES mikrotik_servers(id)
id_harga_layanan INTEGER REFERENCES harga_layanans(id)
```

## API Endpoint Conventions

### 1. Resource Names
**Gunakan plural form untuk resource names:**

```python
# ✅ BENAR
router = APIRouter(prefix="/pelanggans", tags=["Pelanggans"])
router = APIRouter(prefix="/invoices", tags=["Invoices"])
router = APIRouter(prefix="/mikrotik-servers", tags=["Mikrotik Servers"])

# ❌ SALAH (meskipun masih valid, kurang konsisten)
router = APIRouter(prefix="/pelanggan", tags=["Pelanggan"])
router = APIRouter(prefix="/invoice", tags=["Invoice"])
```

### 2. HTTP Methods
**Gunakan REST conventions:**

```python
# ✅ BENAR
@router.post("/", response_model=PelangganSchema)      # Create
@router.get("/", response_model=List[PelangganSchema])  # List
@router.get("/{pelanggan_id}", response_model=...)     # Read
@router.patch("/{pelanggan_id}", response_model=...)   # Update
@router.delete("/{pelanggan_id}")                      # Delete

# Function names mengikuti pattern:
async def create_pelanggan(...):
async def read_pelanggan_by_id(...):
async def update_pelanggan(...):
async def delete_pelanggan(...):
```

## SQLAlchemy Model Conventions

### 1. Model Classes
**Gunakan `PascalCase` singular untuk model classes:**

```python
# ✅ BENAR
class Pelanggan(Base):
    pass

class DataTeknis(Base):
    pass

class MikrotikServer(Base):
    pass
```

### 2. Relationship Properties
**Gunakan singular untuk one-to-one, plural untuk one-to-many:**

```python
# ✅ BENAR
class Pelanggan(Base):
    # One-to-one relationship
    data_teknis: Mapped["DataTeknis"] = relationship(...)

    # One-to-many relationship
    invoices: Mapped[List["Invoice"]] = relationship(...)
    langganans: Mapped[List["Langganan"]] = relationship(...)

class MikrotikServer(Base):
    # One-to-many relationship
    data_teknis_records: Mapped[List["DataTeknis"]] = relationship(...)

# ❌ SALAH
class Pelanggan(Base):
    data_teknises: Mapped[List["DataTeknis"]] = relationship(...)  # salah, should be singular
    invoice: Mapped["Invoice"] = relationship(...)                 # salah, should be plural
```

### 3. Column Definitions
**Gunakan descriptive names dengan `snake_case`:**

```python
# ✅ BENAR
class Pelanggan(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    no_ktp: Mapped[str] = mapped_column(String(16), unique=True)
    tanggal_instalasi: Mapped[Date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# ❌ SALAH
class Pelanggan(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    noKtp: Mapped[str] = mapped_column(String(16), unique=True)      # camelCase
    tglInstalasi: Mapped[Date] = mapped_column(Date)                 # abbreviations
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())  # camelCase
```

## File and Directory Conventions

### 1. Python Files
**Gunakan `snake_case` untuk module names:**

```
# ✅ BENAR
pelanggan_service.py
data_teknis.py
mikrotik_server.py
notification_service.py

# ❌ SALAH
pelangganService.py
dataTeknis.py
mikrotikServer.py
notificationService.py
```

### 2. Directory Names
**Gunakan `snake_case` untuk directory names:**

```
# ✅ BENAR
app/
├── services/
├── routers/
├── models/
├── schemas/
└── utils/

# ❌ SALAH
app/
├── services/
├── Routers/
├── Models/
├── Schemas/
└── utils/
```

## Schema (Pydantic) Conventions

### 1. Schema Classes
**Gunakan descriptive names dengan `PascalCase`:**

```python
# ✅ BENAR
class PelangganCreate(BaseModel):
    pass

class PelangganUpdate(BaseModel):
    pass

class PelangganResponse(BaseModel):
    pass

class PelangganListResponse(BaseModel):
    pass

# ❌ SALAH
class CreatePelanggan(BaseModel):      # kurang deskriptif
class pelangganCreate(BaseModel):      # tidak PascalCase
class Pelanggan_Creation(BaseModel):   # underscore
```

### 2. Field Names
**Gunakan `snake_case` untuk field names:**

```python
# ✅ BENAR
class PelangganCreate(BaseModel):
    nama: str
    email: EmailStr
    no_ktp: str
    alamat: str
    tanggal_instalasi: Optional[date] = None

# ❌ SALAH
class PelangganCreate(BaseModel):
    nama: str
    email: EmailStr
    noKtp: str                      # camelCase
    alamat: str
    tglInstalasi: Optional[date] = None  # abbreviations + camelCase
```

## Service Layer Conventions

### 1. Service Classes
**Gunakan `{ResourceName}Service` pattern:**

```python
# ✅ BENAR
class PelangganService(BaseService):
    pass

class InvoiceService(BaseService):
    pass

class MikrotikService(BaseService):
    pass

# ❌ SALAH
class PelangganManager(BaseService):     # tidak konsisten
class invoiceService(BaseService):       # tidak PascalCase
class ServiceMikrotik(BaseService):      # urutan salah
```

### 2. Method Names
**Gunakan descriptive action verbs:**

```python
# ✅ BENAR
class PelangganService:
    async def create_pelanggan(self, data: PelangganCreate) -> Pelanggan:
        pass

    async def get_pelanggan_by_id(self, pelanggan_id: int) -> Pelanggan:
        pass

    async def search_pelanggans(self, filters: SearchFilters) -> List[Pelanggan]:
        pass

    async def update_pelanggan(self, pelanggan_id: int, data: PelangganUpdate) -> Pelanggan:
        pass

    async def delete_pelanggan(self, pelanggan_id: int) -> None:
        pass

# ❌ SALAH
class PelangganService:
    async def create(self, data):                      # tidak spesifik
    async def get(self, id):                          # tidak spesifik
    async def search(self, filters):                   # kurang deskriptif
    async def update_data(self, id, data):             # inkonsisten
    async def remove(self, id):                       # synonym yang membingungkan
```

## Testing Conventions

### 1. Test Files
**Gunakan `test_` prefix untuk test files:**

```
# ✅ BENAR
tests/
├── test_pelanggan_service.py
├── test_invoice_router.py
├── test_mikrotik_integration.py
└── conftest.py

# ❌ SALAH
tests/
├── pelanggan_test.py
├── invoice_router_tests.py
├── mikrotik_integration_tests.py
└── config.py
```

### 2. Test Functions
**Gunakan `test_` prefix dengan descriptive names:**

```python
# ✅ BENAR
class TestPelangganService:
    async def test_create_pelanggan_success(self):
        pass

    async def test_create_pelangan_duplicate_email_raises_error(self):
        pass

    async def test_get_pelanggan_by_id_not_found_returns_none(self):
        pass

# ❌ SALAH
class TestPelangganService:
    async def test_1(self):                    # tidak deskriptif
    async def create_success(self):            # tidak ada prefix
    async def testDuplicateEmail(self):        # tidak deskriptif
    async def should_return_none_if_not_found(self):  # terlalu panjang
```

## Configuration Constants

### 1. Environment Variables
**Gunakan `UPPER_SNAKE_CASE` dengan descriptive names:**

```python
# ✅ BENAR
DATABASE_URL = "postgresql://..."
SECRET_KEY = "your-secret-key"
XENDIT_API_KEY_JAKINET = "jakinet-api-key"
MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# ❌ SALAH
database_url = "postgresql://..."     # tidak uppercase
secretKey = "your-secret-key"        # camelCase
xendit_key = "jakinet-api-key"       # tidak deskriptif
maxSize = 10 * 1024 * 1024          # tidak deskriptif
```

## Error Message Conventions

### 1. Error Messages
**Gunakan Bahasa Indonesia yang konsisten dan user-friendly:**

```python
# ✅ BENAR
class ErrorMessages:
    NOT_FOUND = "{resource} tidak ditemukan"
    DUPLICATE_EMAIL = "Email '{email}' sudah terdaftar"
    INVALID_FORMAT = "Format {field} tidak valid"
    REQUIRED_FIELD = "Field {field} wajib diisi"

# ❌ SALAH
class ErrorMessages:
    NOT_FOUND = "{resource} not found"                    # Bahasa Inggris
    DUPLICATE_EMAIL = "Email already exists"              # Bahasa Inggris
    INVALID_FORMAT = "Invalid {field} format"             # Bahasa Inggris
    REQUIRED_FIELD = "{field} is required"                # Bahasa Inggris
```

## Summary

### ✅ DO's:
- Gunakan `snake_case` untuk variables, functions, modules
- Gunakan `PascalCase` untuk classes
- Gunakan `UPPER_SNAKE_CASE` untuk constants
- Gunakan descriptive names yang jelas
- Konsisten dalam konvensi yang sudah ditetapkan
- Gunakan Bahasa Indonesia untuk user-facing messages

### ❌ DON'Ts:
- Gunakan `camelCase` di Python code
- Gunakan abbreviations yang tidak jelas (kecuali yang sudah umum seperti `id`, `url`)
- Mix conventions dalam satu file
- Gunakan names yang terlalu pendek atau tidak deskriptif
- Gunakan Bahasa Inggris untuk user-facing messages

### 🎯 Key Principles:
1. **Clarity**: Names harus jelas dan mudah dimengerti
2. **Consistency**: Ikuti konvensi yang sudah ditetapkan secara konsisten
3. **Descriptive**: Names harus mendeskripsikan purpose dengan baik
4. **Maintainable**: Code harus mudah dimaintain oleh developer lain