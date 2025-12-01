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
- **Multi-stage Docker builds** untuk optimal image size
- **Database migrations** otomatis
- **Health checks** dan monitoring
- **Rollback capabilities** jika deployment gagal

### 📊 Environment Support
- **Development**: `docker-compose.dev.yml` dengan live reload
- **Staging**: Branch `dev` untuk testing
- **Production**: Branch `main` dengan full monitoring

## 🐳 Docker Deployment

### Quick Start (Development)
```bash
# Clone repository
git clone https://github.com/Ahmad-Rizki21/BIlling-Portal_V3.5.git
cd BIlling-Portal_V3.5

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Access applications
# Backend API: http://localhost:8000
# Frontend: http://localhost:5173
# PgAdmin: http://localhost:5050
# Redis Commander: http://localhost:8081
```

### Production Deployment
```bash
# Set environment variables
cp .env.example .env
# Edit .env dengan production values

# Deploy to production
docker-compose -f docker-compose.production.yml up -d

# Run database migrations
docker-compose -f docker-compose.production.yml run migrate
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
- **PostgreSQL**: Database utama dengan replication
- **Redis**: Cache dan session storage
- **Nginx**: Reverse proxy dan load balancer
- **Docker**: Containerization dan orchestration

## Instalasi

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis

### Setup Backend
```bash
# Clone repository
git clone https://github.com/Ahmad-Rizki21/BIlling-Portal_V3.5.git
cd BIlling-Portal_V3.5

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

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