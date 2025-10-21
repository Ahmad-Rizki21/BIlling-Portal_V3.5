import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Memuat variabel environment dari file .env
load_dotenv()

# Ambil URL database dari environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Pastikan DATABASE_URL tidak kosong
if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di file .env")

# --- BAGIAN PALING PENTING ADA DI SINI ---
# Membuat engine database dengan konfigurasi connection pool yang stabil
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # echo=False di production untuk log yang lebih bersih
    pool_recycle=1800,  # Daur ulang koneksi setiap 30 menit
    pool_pre_ping=True,   # Cek koneksi sebelum digunakan
    pool_size=10,         # Jumlah koneksi minimum di pool
    max_overflow=20       # Jumlah koneksi maksimum yang bisa dibuat
)
# ------------------------------------------

# Membuat session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class untuk semua model SQLAlchemy
Base = declarative_base()

# Dependency untuk mendapatkan sesi database di setiap endpoint
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session