# 🚀 Migration Guide: ArtacomFTTHBilling_V2 → BillingJelantikFTTHV3

## 📋 Overview
Guide untuk migrasi clean ke repository GitHub baru tanpa file-file yang tidak perlu dan tanpa Claude sebagai contributor.

## 🎯 Target Repository
- **Old**: `https://github.com/Ahmad-Rizki21/ArtacomFTTHBilling_V2.git`
- **New**: `https://github.com/Ahmad-Rizki21/BillingJelantikFTTHV3.git`

## 📁 File/Folder yang akan di-exclude:
- ❌ `DATABASE-EXISTING/` (folder database lama)
- ❌ `node_modules/` (dependencies)
- ❌ `venv/` (virtual environment)
- ❌ `logs/` (log files)
- ❌ `__pycache__/` (Python cache)
- ❌ File-file Claude dan AI assistant
- ❌ File-file debug dan test sementara
- ❌ File backup (`.bak`, `.old`)
- ❌ Screenshot dan dokumentasi lama
- ❌ Build artifacts (dist/, build/)

## ✅ File/Folder yang akan di-include:
- ✅ `app/` (Backend FastAPI)
- ✅ `frontend/src/` (Source code frontend)
- ✅ `frontend/package.json` (Dependencies config)
- ✅ `alembic/` (Database migrations)
- ✅ `requirements.txt` (Python dependencies)
- ✅ Docker files dan compose files
- ✅ `.github/workflows/` (CI/CD pipeline)
- ✅ Dokumentasi penting (README, API docs, deployment)

## 🛠️ Cara Menjalankan Migrasi

### Metode 1: Otomatis dengan PowerShell Script
```powershell
# Jalankan script migrasi
.\migrate-to-new-repo.ps1
```

### Metode 2: Manual Step by Step

#### 1. **Clone repository lama**
```bash
git clone https://github.com/Ahmad-Rizki21/ArtacomFTTHBilling_V2.git temp-repo
cd temp-repo
```

#### 2. **Buat repository baru kosong**
```bash
cd ..
mkdir billing-jelantik-ftth-v3
cd billing-jelantik-ftth-v3
git init
git remote add origin https://github.com/Ahmad-Rizki21/BillingJelantikFTTHV3.git
```

#### 3. **Copy file-file penting**
```powershell
# Copy direktori utama
Copy-Item ..\temp-repo\app\* .\app\ -Recurse -Force
Copy-Item ..\temp-repo\frontend\src\* .\frontend\src\ -Recurse -Force
Copy-Item ..\temp-repo\frontend\package.json .\frontend\ -Force
Copy-Item ..\temp-repo\frontend\vite.config.ts .\frontend\ -Force
Copy-Item ..\temp-repo\alembic\* .\alembic\ -Recurse -Force
Copy-Item ..\temp-repo\requirements.txt . -Force
Copy-Item ..\temp-repo\pyproject.toml . -Force
Copy-Item ..\temp-repo\Dockerfile.backend . -Force
Copy-Item ..\temp-repo\frontend\Dockerfile .\frontend\ -Force
Copy-Item ..\temp-repo\.gitignore . -Force
Copy-Item ..\temp-repo\README.md . -Force
```

#### 4. **Setup git configuration**
```bash
git config user.name "Ahmad Rizki"
git config user.email "ahmad.rizki@example.com"
```

#### 5. **Add dan commit**
```bash
git add .
git commit -m "🎉 Initial commit: BillingJelantikFTTHV3

- Clean FastAPI + Vue.js FTTH billing system
- Complete backend with models, routers, and services
- Modern frontend with Vue.js 3 + TypeScript
- Mobile app support with Capacitor
- Real-time WebSocket notifications
- JWT authentication system
- Database migrations with Alembic
- Docker deployment configuration
- Comprehensive CI/CD pipeline
- Clean repository without unnecessary files

🤖 Generated with automated migration script

Co-Authored-By: System <noreply@system.com>"
```

#### 6. **Push ke repository baru**
```bash
git branch -M main
git push -u origin main
```

## 🔧 CI/CD Pipeline Features

### ✅ **Backend Testing**
- Python 3.13
- MySQL 8.0 testing database
- Linting (flake8, black)
- Security checks (bandit, safety)
- Unit tests dengan pytest
- Coverage reporting

### ✅ **Frontend Testing**
- Node.js 18
- TypeScript linting
- Unit tests
- Build verification

### ✅ **Security & Quality**
- Trivy vulnerability scanning
- Docker image building
- GitHub security tab integration
- Code coverage reporting

### ✅ **Deployment**
- Automated Docker builds
- Multi-environment (staging/production)
- Android app building
- Health checks

## 📱 Mobile App Build
Script akan otomatis build Android app:
- Frontend build
- Capacitor integration
- Gradle build process
- APK generation

## 🗂️ Struktur Repository Baru

```
BillingJelantikFTTHV3/
├── app/                    # Backend FastAPI
│   ├── models/            # SQLAlchemy models
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── frontend/              # Vue.js frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   ├── package.json       # Dependencies
│   └── vite.config.ts     # Vite config
├── alembic/               # Database migrations
├── .github/workflows/     # CI/CD pipeline
├── requirements.txt       # Python dependencies
├── Dockerfile.backend     # Backend Docker image
├── docker-compose.prod.yml # Production compose
└── README.md             # Project documentation
```

## 🔐 Environment Setup

Setelah migrasi, setup environment variables:

```bash
# Backend
cp .env.example .env
# Edit .env dengan:
# - DATABASE_URL
# - SECRET_KEY
# - ENCRYPTION_KEY

# Frontend
cd frontend
cp .env.example .env.local
# Edit .env.local dengan:
# - VITE_API_BASE_URL
```

## 🚀 Deployment Commands

### Development
```bash
# Backend
cd app
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

### Production
```bash
# Docker
docker-compose -f docker-compose.prod.yml up -d

# Manual build
docker build -f Dockerfile.backend -t billing-backend .
docker build -f frontend/Dockerfile -t billing-frontend ./frontend
```

## 📊 Monitoring & Logging

- **Backend**: Structured logging dengan rotation
- **Frontend**: Error tracking dan performance monitoring
- **CI/CD**: GitHub Actions dengan comprehensive reporting
- **Security**: Automated vulnerability scanning

## 🧹 Cleanup Setelah Migrasi

Setelah migrasi berhasil:
```bash
# Hapus temporary folder
rm -rf temp-repo

# Update local remote origin
git remote set-url origin https://github.com/Ahmad-Rizki21/BillingJelantikFTTHV3.git

# Verify
git remote -v
```

## ✅ Checklist Selesai

- [ ] Repository baru dibuat di GitHub
- [ ] File-file penting berhasil dicopy
- [ ] .gitignore komprehensif diaplikasikan
- [ ] CI/CD pipeline terkonfigurasi
- [ ] Initial commit berhasil
- [ ] Push ke repository baru berhasil
- [ ] Environment variables disetup
- [ ] Development environment berjalan
- [ ] Production deployment terkonfigurasi
- [ ] Mobile app build berjalan

## 🔗 Links

- **New Repository**: https://github.com/Ahmad-Rizki21/BillingJelantikFTTHV3
- **CI/CD Pipeline**: `.github/workflows/ci-cd.yml`
- **Documentation**: `README.md`
- **Migration Script**: `migrate-to-new-repo.ps1`

---

**🎉 Selamat! Repository baru Anda sudah siap digunakan dengan struktur yang clean dan CI/CD pipeline yang komprehensif!**