# CI/CD Pipeline Setup Guide

## GitHub Secrets Configuration

### Required Secrets

#### Production Server Secrets:
- `PROD_HOST` - Production server IP or hostname
- `PROD_USERNAME` - SSH username for production server
- `PROD_SSH_KEY` - SSH private key for production server
- `PRODUCTION_URL` - Production application URL (for health checks)

#### Staging Server Secrets:
- `STAGING_HOST` - Staging server IP or hostname
- `STAGING_USERNAME` - SSH username for staging server
- `STAGING_SSH_KEY` - SSH private key for staging server

### Setup Instructions

#### 1. Generate SSH Keys (for each server):
```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/billing-portal-ci

# Copy public key to server
ssh-copy-id -i ~/.ssh/billing-portal-ci.pub user@your-server.com

# Test SSH connection
ssh -i ~/.ssh/billing-portal-ci user@your-server.com
```

#### 2. Add Secrets to GitHub Repository:
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each secret above
4. Paste the values:
   - For SSH keys: Copy the **private** key content (`~/.ssh/billing-portal-ci`)
   - For hosts: Server IP addresses or domain names
   - For usernames: SSH usernames

#### 3. Server Preparation (Production & Staging):

```bash
# On both production and staging servers
sudo mkdir -p /var/www/billing-portal
sudo mkdir -p /var/www/billing-portal-staging
sudo chown -R $USER:$USER /var/www/billing-portal*
chmod 755 /var/www/billing-portal*

# Install required software
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server

# Install gunicorn for production
pip3 install gunicorn

# Setup PostgreSQL
sudo -u postgres createdb billing_ftth_prod
sudo -u postgres createuser --interactive

# Setup nginx configuration
sudo nano /etc/nginx/sites-available/billing-portal
```

#### 4. Nginx Configuration:

```nginx
# /etc/nginx/sites-available/billing-portal
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend
    location / {
        root /var/www/billing-portal;
        try_files $uri $uri/ /index.html;

        # Cache static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/billing-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Pipeline Workflow

### Development Workflow:
1. **Push to `dev` branch** → Triggers:
   - Backend tests
   - Frontend tests
   - Security scans
   - Migration tests
   - **Deploy to staging server**

2. **Pull Request to `main`** → Triggers:
   - All tests (same as above)
   - Build validation
   - No deployment (wait for merge)

3. **Push to `main` branch** → Triggers:
   - All tests
   - **Deploy to production server**
   - Health checks

### Artifacts:
- `backend-test-results` - Test reports and coverage
- `frontend-dist` - Built frontend assets
- `security-reports` - Security scan results
- `production-package` - Complete deployment package

### Environment-specific:
- **Staging**: `dev` branch deployments
- **Production**: `main` branch deployments only
- **Rollback**: Automatic backup creation before deployment

## Deployment Process

### Automatic Deployment Package Includes:
- ✅ Backend Python application
- ✅ Frontend built assets
- ✅ Database migration scripts
- ✅ Requirements.txt
- ✅ Production deployment script
- ✅ Environment configuration template

### Health Checks:
- Database connectivity
- API endpoint availability
- Frontend serving
- Service status monitoring

## Security Features

- 🔒 SSH key authentication
- 🛡️ Security scanning (Bandit, Safety)
- 📊 Code coverage reporting
- 🔍 Dependency vulnerability checks
- 🏭 Environment separation (staging vs production)
- 🚫 No hardcoded secrets in code
- 📝 Comprehensive logging