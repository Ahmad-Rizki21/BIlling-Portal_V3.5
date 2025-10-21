# Artacom FTTH Billing System - Deployment Guide

## Overview

This guide covers the complete deployment process for the Artacom FTTH Billing System using enterprise-grade CI/CD pipeline with staging and production environments.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  CI/CD Pipeline │───▶│  Staging Env    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Developers    │───▶│  Manual Approvals│───▶│ Production Env  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements

**Minimum Staging Environment:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- Network: 100Mbps

**Minimum Production Environment:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 1Gbps
- High availability setup recommended

### Software Requirements

- Docker & Docker Compose
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for production)

## Environment Setup

### 1. Repository Setup

```bash
# Clone the repository
git clone https://github.com/Ahmad-Rizki21/BillingFtthV2.git
cd BillingFtthV2

# Create feature branches
git checkout -b feature/new-feature
git checkout main-bersih  # For staging
git checkout main          # For production
```

### 2. Environment Configuration

#### Staging Environment

```bash
# Copy environment template
cp .env.staging.example .env.staging

# Edit with actual values
nano .env.staging
```

**Required Staging Variables:**
```bash
# Database
STAGING_DB_NAME=billing_staging
STAGING_DB_USER=staging_user
STAGING_DB_PASSWORD=your_secure_password

# Redis
STAGING_REDIS_PASSWORD=your_redis_password

# Security
STAGING_SECRET_KEY=your_32_character_secret_key
STAGING_ENCRYPTION_KEY=your_32_character_encryption_key

# Xendit
STAGING_XENDIT_CALLBACK_TOKEN_ARTACOMINDO=your_staging_token
STAGING_XENDIT_CALLBACK_TOKEN_JELANTIK=your_staging_token
STAGING_XENDIT_API_KEY_JAKINET=your_staging_api_key
STAGING_XENDIT_API_KEY_JELANTIK=your_staging_api_key
```

#### Production Environment

```bash
# Copy environment template
cp .env.prod.example .env.prod

# Edit with production values
nano .env.prod
```

**Required Production Variables:**
```bash
# Database (use strong passwords)
PROD_DB_NAME=billing_prod
PROD_DB_USER=prod_user
PROD_DB_PASSWORD=very_strong_prod_password

# Redis
PROD_REDIS_PASSWORD=very_strong_redis_password

# Security (use cryptographically secure keys)
PROD_SECRET_KEY=cryptographically_secure_32_char_key
PROD_ENCRYPTION_KEY=generated_32_char_encryption_key

# Xendit Production
PROD_XENDIT_CALLBACK_TOKEN_ARTACOMINDO=prod_token
PROD_XENDIT_CALLBACK_TOKEN_JELANTIK=prod_token
PROD_XENDIT_API_KEY_JAKINET=prod_api_key
PROD_XENDIT_API_KEY_JELANTIK=prod_api_key
```

### 3. GitHub Secrets Setup

See `.github/workflows/secrets-setup.md` for detailed instructions.

**Quick Setup:**
```bash
# Install GitHub CLI
# Then set secrets:
gh secret set STAGING_DB_PASSWORD --body "your_staging_db_password"
gh secret set PROD_DB_PASSWORD --body "your_prod_db_password"
gh secret set PROD_SECRET_KEY --body "your_prod_secret_key"
# ... set all other required secrets
```

## Deployment Process

### Automated CI/CD Pipeline

The system uses GitHub Actions for automated deployment:

#### Branch Strategy

- **main-bersih**: Auto-deploy to staging
- **main**: Requires approval, deploys to production
- **feature branches**: Run tests only, no deployment

#### Pipeline Stages

1. **Code Quality & Security**
   - Linting (flake8, ESLint)
   - Type checking (mypy, TypeScript)
   - Security scanning (bandit, safety)
   - Code formatting (black, isort, prettier)

2. **Testing**
   - Unit tests with 80%+ coverage requirement
   - Integration tests
   - API tests

3. **Build & Push**
   - Build Docker images
   - Push to container registry
   - Multi-platform builds (amd64, arm64)

4. **Deployment**
   - Staging: Automatic
   - Production: Manual approval required

### Manual Deployment

#### Staging Deployment

```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Check deployment status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

#### Production Deployment

```bash
# Deploy to production (requires approval)
docker-compose -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Database Management

#### Migrations

```bash
# For staging
docker-compose -f docker-compose.staging.yml exec backend alembic upgrade head

# For production
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### Backups

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres-master pg_dump -U prod_user billing_prod > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres-master psql -U prod_user billing_prod < backup.sql
```

## Monitoring & Logging

### Access Monitoring Tools

#### Staging Environment

- **Application**: http://staging-domain:8001
- **Frontend**: http://staging-domain:3001
- **Grafana**: http://staging-domain:3002
- **Prometheus**: http://staging-domain:9091

#### Production Environment

- **Application**: https://your-domain.com
- **Grafana**: https://your-domain.com:3000
- **Prometheus**: https://your-domain.com:9090

### Log Locations

- **Application logs**: `./logs/{env}/`
- **Nginx logs**: `./logs/nginx-{env}/`
- **Database logs**: Docker container logs

### Health Checks

```bash
# Check application health
curl https://your-domain.com/health

# Check database connection
curl https://your-domain.com/health/db

# Check external services
curl https://your-domain.com/health/services
```

## SSL/TLS Setup

### For Production

1. **Obtain SSL Certificates**
   ```bash
   # Using Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   ```

2. **Configure Nginx**
   ```bash
   # Copy certificates
   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/prod/cert.pem
   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/prod/key.pem
   ```

3. **Update Environment**
   ```bash
   # Add to .env.prod
   PROD_SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
   PROD_SSL_KEY_PATH=/etc/nginx/ssl/key.pem
   ```

## Scaling & Performance

### Horizontal Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend-prod=3

# Scale frontend services
docker-compose -f docker-compose.prod.yml up -d --scale frontend-prod=2
```

### Performance Tuning

1. **Database Optimization**
   - Configure connection pooling
   - Add appropriate indexes
   - Enable query caching

2. **Redis Optimization**
   - Configure memory limits
   - Enable persistence
   - Set up replication

3. **Application Tuning**
   - Adjust worker processes
   - Configure rate limiting
   - Enable response caching

## Security Considerations

### Network Security

- Use firewall to restrict access
- Enable VPN for admin access
- Configure security groups

### Application Security

- Regular security updates
- Monitor for vulnerabilities
- Use WAF (Web Application Firewall)
- Enable DDoS protection

### Data Security

- Encrypt sensitive data
- Regular backups
- Access control management
- Audit logging

## Troubleshooting

### Common Issues

#### Deployment Fails

```bash
# Check logs
docker-compose logs

# Check resource usage
docker stats

# Check disk space
df -h
```

#### Database Connection Issues

```bash
# Test database connection
docker-compose exec postgres psql -U user -d database

# Check database logs
docker-compose logs postgres
```

#### Application Errors

```bash
# Check application logs
docker-compose logs backend

# Check health status
curl http://localhost:8000/health
```

### Emergency Procedures

#### Rollback Deployment

```bash
# Get previous image tag
docker images | grep billing-app

# Rollback to previous version
docker-compose -f docker-compose.prod.yml up -d --force-recreate \
  backend-prod:tag_name \
  frontend-prod:tag_name
```

#### Database Recovery

```bash
# Stop application
docker-compose -f docker-compose.prod.yml stop backend-prod

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres-master \
  psql -U prod_user billing_prod < backup.sql

# Start application
docker-compose -f docker-compose.prod.yml start backend-prod
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs, monitor performance
- **Weekly**: Update dependencies, security scans
- **Monthly**: Database maintenance, backup verification
- **Quarterly**: Security audit, performance review

### Updates

#### Application Updates

```bash
# Pull latest code
git pull origin main

# Deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### System Updates

```bash
# Update Docker images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

## Support

For deployment issues:

1. Check logs and error messages
2. Review this documentation
3. Check GitHub Actions workflow status
4. Contact the development team

## Best Practices

1. **Always test in staging first**
2. **Keep secrets secure**
3. **Monitor deployments closely**
4. **Have rollback procedures ready**
5. **Document any custom configurations**
6. **Regular security updates**
7. **Performance monitoring**
8. **Backup verification**

---

*This documentation is maintained by the Artacom Development Team. For updates and questions, please contact the development team or create an issue in the repository.*