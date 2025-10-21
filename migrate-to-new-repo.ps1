# ============================================
# MIGRATION SCRIPT - BILLINGJELANTIKFTTHV3
# Clean migration to new GitHub repository
# ============================================

# Configuration
$OLD_REPO = "https://github.com/Ahmad-Rizki21/ArtacomFTTHBilling_V2.git"
$NEW_REPO = "https://github.com/Ahmad-Rizki21/BillingJelantikFTTHV3.git"
$TEMP_DIR = "temp-clean-repo"

Write-Host "🚀 Starting clean migration to new repository..." -ForegroundColor Green

# Step 1: Create temporary clean repository
Write-Host "📁 Creating temporary clean repository..." -ForegroundColor Yellow
if (Test-Path $TEMP_DIR) {
    Remove-Item -Path $TEMP_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Step 2: Initialize new clean repository
Set-Location $TEMP_DIR
git init
git config user.name "Ahmad Rizki"
git config user.email "ahmad.rizki@example.com"

# Step 3: Copy only necessary files from original repo
Write-Host "📋 Copying necessary files..." -ForegroundColor Yellow

# Create directories structure
New-Item -ItemType Directory -Path "app" -Force | Out-Null
New-Item -ItemType Directory -Path "frontend" -Force | Out-Null
New-Item -ItemType Directory -Path "alembic" -Force | Out-Null
New-Item -ItemType Directory -Path "scripts" -Force | Out-Null
New-Item -ItemType Directory -Path "tests" -Force | Out-Null

# Core application files to include
$includeFiles = @(
    "app/main.py",
    "app/database.py",
    "app/auth.py",
    "app/config.py",
    "app/constants.py",
    "app/encryption.py",
    "app/encryption_utils.py",
    "app/logging_config.py",
    "app/websocket_manager.py",
    "app/jobs.py",
    "app/__init__.py",
    "app/models",
    "app/routers",
    "app/schemas",
    "app/services",
    "app/utils",
    "frontend/src",
    "frontend/public",
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/tsconfig.json",
    "frontend/index.html",
    "frontend/README.md",
    "alembic/env.py",
    "alembic/script.py.mako",
    "alembic/versions",
    "requirements.txt",
    "pyproject.toml",
    "pytest.ini",
    "docker-compose.prod.yml",
    "docker-compose.staging.yml",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    ".gitignore",
    "README.md",
    "API_DOCUMENTATION.md",
    "DEPLOYMENT.md",
    "NAMING_CONVENTIONS.md"
)

# Copy files
foreach ($file in $includeFiles) {
    $sourcePath = "../$file"
    $destPath = $file

    if (Test-Path $sourcePath) {
        Write-Host "  ✓ Copying $file" -ForegroundColor Cyan
        Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
    } else {
        Write-Host "  ⚠ Skipping $file (not found)" -ForegroundColor Yellow
    }
}

# Step 4: Create proper README for new repo
Write-Host "📝 Creating README for new repository..." -ForegroundColor Yellow
$readmeContent = @"
# BillingJelantikFTTHV3

Sistem billing FTTH (Fiber to the Home) yang modern dengan teknologi FastAPI + Vue.js.

## 🚀 Fitur Utama

- **Backend**: FastAPI dengan Python
- **Frontend**: Vue.js 3 dengan TypeScript
- **Database**: MySQL dengan Alembic migrations
- **Mobile**: Android dengan Capacitor
- **Authentication**: JWT token-based
- **Real-time**: WebSocket notifications
- **Deployment**: Docker + Docker Compose

## 📁 Struktur Proyek

```
├── app/                    # Backend FastAPI
│   ├── models/            # SQLAlchemy models
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── frontend/              # Vue.js frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   └── dist/              # Build output
├── alembic/               # Database migrations
├── scripts/               # Deployment scripts
├── tests/                 # Test files
└── docker-compose.yml     # Docker configuration
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, Pydantic
- **Frontend**: Vue.js 3, TypeScript, Vite, Vuetify
- **Database**: MySQL 8.0+
- **Authentication**: JWT dengan refresh token
- **Real-time**: WebSocket
- **Mobile**: Capacitor + Android
- **DevOps**: Docker, GitHub Actions

## 📋 Instalasi

### Prerequisites
- Python 3.13+
- Node.js 18+
- MySQL 8.0+
- Docker (opsional)

### Backend Setup
```bash
cd app
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🚀 Deployment

### Production dengan Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

## 📖 Dokumentasi

- [API Documentation](./API_DOCUMENTATION.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Naming Conventions](./NAMING_CONVENTIONS.md)

## 🤝 Kontributor

- Ahmad Rizki - *Initial work* - [Ahmad-Rizki21](https://github.com/Ahmad-Rizki21)

## 📄 Lisensi

Licensed under MIT License - see LICENSE file for details
"@

Set-Content -Path "README.md" -Value $readmeContent -Encoding UTF8

# Step 5: Add and commit files
Write-Host "📦 Adding files to git..." -ForegroundColor Yellow
git add .
$commitMessage = "🎉 Initial commit: BillingJelantikFTTHV3

Clean FastAPI + Vue.js FTTH billing system
Complete backend with models, routers, and services
Modern frontend with Vue.js 3 + TypeScript
Mobile app support with Capacitor
Real-time WebSocket notifications
JWT authentication system
Database migrations with Alembic
Docker deployment configuration
Comprehensive documentation

Generated with automated migration script"

git commit -m $commitMessage

# Step 6: Add remote and push
Write-Host "🌐 Adding remote repository..." -ForegroundColor Yellow
git remote add origin $NEW_REPO

Write-Host "📤 Pushing to new repository..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

# Step 7: Cleanup
Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
Set-Location ..
Remove-Item -Path $TEMP_DIR -Recurse -Force

Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
Write-Host "🔗 New repository: $NEW_REPO" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Visit the new repository at: $NEW_REPO" -ForegroundColor White
Write-Host "2. Configure GitHub Actions CI/CD pipeline" -ForegroundColor White
Write-Host "3. Update any external references to the new repo" -ForegroundColor White
Write-Host "4. Add collaborators as needed" -ForegroundColor White