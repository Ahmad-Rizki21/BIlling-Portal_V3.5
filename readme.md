# Billing Portal FTTH V3.5

Sistem billing untuk layanan Fiber to the Home (FTTH) dengan fitur lengkap.

## Fitur Utama

- **Manajemen Pelanggan**: Data pelanggan, langganan, dan status pembayaran
- **Manajemen Layanan**: Paket layanan, harga, dan konfigurasi
- **Invoice & Pembayaran**: Generate invoice, integrasi payment gateway
- **Inventory Management**: Manajemen perangkat dan infrastruktur
- **Monitoring Dashboard**: Real-time monitoring dan reporting
- **Mobile Support**: Aplikasi mobile dengan Capacitor

## CI/CD Pipeline

Project ini menggunakan GitHub Actions yang modern dan reliable:

### 🔄 Automated Testing
- **Backend Tests**: Pytest dengan coverage reporting
- **Frontend Tests**: TypeScript checking, linting, dan build validation
- **Security Scans**: Bandit dan Safety untuk vulnerability detection
- **Code Quality**: Flake8, Black, dan MyPy untuk code standards

### 🚀 Automated Deployment
- **Automated database migrations**
- **Health checks** dan monitoring
- **Rollback capabilities** jika deployment gagal

### 📊 Environment Support
- **Development**: Local development dengan hot reload
- **Staging**: Branch `dev` untuk testing
- **Production**: Branch `main` dengan full monitoring

## Quick Start (Local Development)

```bash
# Clone repository
git clone https://github.com/Ahmad-Rizki21/BIlling-Portal_V3.5.git
cd BIlling-Portal_V3.5

# Setup Backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup Database (PostgreSQL)
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
# Buat database dan user sesuai kebutuhan

# Copy dan edit environment variables
cp .env.example .env
# Edit .env dengan konfigurasi database Anda

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload

# Open new terminal untuk frontend
cd frontend
npm install
npm run dev

# Access applications
# Backend API: http://localhost:8000
# Frontend: http://localhost:5173
# API Documentation: http://localhost:8000/docs
```

## Teknologi

### Backend
- **FastAPI**: Framework API modern Python
- **SQLAlchemy**: ORM untuk database
- **Alembic**: Database migrations
- **Xendit**: Payment gateway integration
- **Mikrotik API**: Network device management

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vuetify**: Material Design component framework
- **Pinia**: State management
- **Vite**: Build tool

### Infrastructure
- **PostgreSQL**: Database utama
- **Redis**: Cache dan session storage
- **Nginx**: Reverse proxy dan load balancer (opsional untuk production)
- **Local Development**: Development environment langsung di mesin lokal

## Instalasi

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis (opsional, untuk cache)

### Setup Backend
```bash
# Clone repository
git clone https://github.com/Ahmad-Rizki21/BIlling-Portal_V3.5.git
cd BIlling-Portal_V3.5

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Setup database PostgreSQL
sudo -u postgres createdb billing_ftth
sudo -u postgres createuser --interactive

# Database migration
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

### Setup Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Production Deployment (Tanpa Docker)
```bash
# Setup production environment
sudo apt install postgresql nginx redis-server

# Setup database dengan user dan database production
sudo -u postgres createdb billing_ftth_prod
sudo -u postgres createuser --interactive

# Install backend dependencies
cd /path/to/BIlling-Portal_V3.5
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment production
cp .env.example .env
# Edit .env dengan production values

# Run migrations
alembic upgrade head

# Build frontend
cd frontend
npm install
npm run build

# Setup Nginx untuk serve frontend dan proxy API
# Copy nginx configuration dan restart nginx

# Start backend dengan Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables

Key environment variables yang perlu dikonfigurasi:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Xendit
XENDIT_API_KEY=your_xendit_api_key

# Secret Key
SECRET_KEY=your_secret_key
```

## API Documentation

API documentation tersedia di:
- Development: `http://localhost:8000/docs`
- Production: `https://your-domain.com/docs`

## Contributing

1. Fork repository
2. Buat branch baru (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## License

Copyright © 2024 Ahmad Rizki. All rights reserved.