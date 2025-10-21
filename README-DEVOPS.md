# Artacom FTTH Billing System - DevOps Guide

## Quick Start for DevOps Team

This guide provides quick commands and references for the DevOps team managing the Artacom FTTH Billing System.

## CI/CD Pipeline Overview

### Branch Strategy
```
main-bersih → Auto-deploy to Staging
main        → Manual approval → Production
feature/*   → Tests only
```

### Pipeline Stages
1. **Quality Gates** (5 min)
2. **Testing** (3 min)
3. **Build & Push** (2 min)
4. **Deploy Staging** (1 min)
5. **Deploy Production** (Manual + 1 min)

## Essential Commands

### Environment Management

```bash
# Staging environment
docker-compose -f docker-compose.staging.yml up -d
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml logs -f
docker-compose -f docker-compose.staging.yml ps

# Production environment
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml ps

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend-prod=3 --scale frontend-prod=2
```

### Database Operations

```bash
# Staging database
docker-compose -f docker-compose.staging.yml exec postgres-staging psql -U staging_user -d billing_staging

# Production database
docker-compose -f docker-compose.prod.yml exec postgres-master psql -U prod_user -d billing_prod

# Run migrations
docker-compose -f docker-compose.staging.yml exec migrate-staging alembic upgrade head
docker-compose -f docker-compose.prod.yml exec migrate-prod alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"
```

### Monitoring Commands

```bash
# Check health
curl http://localhost:8001/health  # Staging
curl https://your-domain.com/health  # Production

# Check system resources
docker stats
docker system df
docker system prune

# View logs
docker-compose -f docker-compose.staging.yml logs backend-staging
docker-compose -f docker-compose.prod.yml logs backend-prod
tail -f ./logs/prod/app.log
```

## Quality Gates

### Run Full Quality Check Locally

```bash
# Make quality check script executable
chmod +x scripts/quality-check.sh

# Run all quality checks
./scripts/quality-check.sh

# Individual checks
black --check app/
isort --check-only app/
flake8 app/
mypy app/
bandit -r app/
safety check
pytest tests/ --cov=app
```

### Coverage Requirements

- **Unit Tests**: Minimum 80% coverage
- **Integration Tests**: Core workflows covered
- **API Tests**: All endpoints tested

## Emergency Procedures

### Rollback Deployment

```bash
# 1. Get current image tags
docker images | grep billing-app

# 2. Identify previous working tag
docker-compose -f docker-compose.prod.yml images

# 3. Rollback
docker-compose -f docker-compose.prod.yml up -d --force-recreate \
  backend-prod:previous_tag \
  frontend-prod:previous_tag
```

### Database Recovery

```bash
# 1. Stop applications
docker-compose -f docker-compose.prod.yml stop backend-prod frontend-prod

# 2. Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres-master \
  psql -U prod_user billing_prod < backup_$(date +%Y%m%d).sql

# 3. Restart applications
docker-compose -f docker-compose.prod.yml start backend-prod frontend-prod

# 4. Verify health
curl -f https://your-domain.com/health
```

### Service Restart

```bash
# Restart individual services
docker-compose -f docker-compose.prod.yml restart backend-prod
docker-compose -f docker-compose.prod.yml restart frontend-prod
docker-compose -f docker-compose.prod.yml restart nginx-prod

# Full restart
docker-compose -f docker-compose.prod.yml restart
```

## Performance Monitoring

### Key Metrics to Monitor

1. **Application Metrics**
   - Response time < 200ms
   - Error rate < 1%
   - CPU usage < 70%
   - Memory usage < 80%

2. **Database Metrics**
   - Connection pool usage < 80%
   - Query time < 100ms
   - Disk usage < 85%

3. **Infrastructure Metrics**
   - Network latency < 50ms
   - Disk I/O < 80%
   - System load < 2.0

### Monitoring Tools Access

**Staging:**
- Grafana: http://staging-domain:3002 (admin/staging_grafana_password)
- Prometheus: http://staging-domain:9091

**Production:**
- Grafana: https://your-domain.com:3000 (admin/prod_grafana_password)
- Prometheus: https://your-domain.com:9090

## Security Checklist

### Daily Security Tasks

```bash
# Check for failed login attempts
grep "failed" ./logs/prod/app.log | tail -20

# Check SSL certificate expiry
openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Check Docker for vulnerabilities
docker scan billing-app-backend:latest
```

### Weekly Security Tasks

```bash
# Update base images
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull nginx:alpine

# Security scan
bandit -r app/ -f json -o security-scan-$(date +%Y%m%d).json
safety check --json --output deps-security-$(date +%Y%m%d).json
```

## Backup Procedures

### Automated Backups

```bash
# Database backup (runs daily)
docker-compose -f docker-compose.prod.yml exec postgres-master \
  pg_dump -U prod_user billing_prod | gzip > ./backups/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Application logs backup
tar -czf ./backups/logs_$(date +%Y%m%d).tar.gz ./logs/prod/

# Config backup
tar -czf ./backups/config_$(date +%Y%m%d).tar.gz \
  .env.prod \
  docker-compose.prod.yml \
  nginx/prod.conf \
  ssl/prod/
```

### Manual Backup

```bash
# Full system backup
./scripts/backup-full.sh

# Database only
./scripts/backup-db.sh

# Configuration only
./scripts/backup-config.sh
```

## Troubleshooting Common Issues

### Application Won't Start

```bash
# 1. Check logs
docker-compose -f docker-compose.prod.yml logs backend-prod

# 2. Check environment variables
docker-compose -f docker-compose.prod.yml exec backend-prod env | grep -E "(DATABASE|REDIS|SECRET)"

# 3. Check database connection
docker-compose -f docker-compose.prod.yml exec backend-prod python -c "
from app.database import engine
try:
    engine.connect()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### High CPU Usage

```bash
# 1. Identify processes
docker stats --no-stream

# 2. Check application logs for errors
docker-compose -f docker-compose.prod.yml logs backend-prod | grep ERROR | tail -20

# 3. Restart services if needed
docker-compose -f docker-compose.prod.yml restart backend-prod
```

### Database Connection Issues

```bash
# 1. Test direct connection
docker-compose -f docker-compose.prod.yml exec postgres-master pg_isready

# 2. Check connection pool
docker-compose -f docker-compose.prod.yml exec postgres-master psql -U prod_user -d billing_prod -c "
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
"

# 3. Check slow queries
docker-compose -f docker-compose.prod.yml exec postgres-master psql -U prod_user -d billing_prod -c "
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;
"
```

## Deployment Scripts

### Quick Deploy Script

```bash
#!/bin/bash
# quick-deploy.sh

ENVIRONMENT=${1:-staging}
BRANCH=${2:-main-bersih}

if [ "$ENVIRONMENT" = "staging" ]; then
    docker-compose -f docker-compose.staging.yml pull
    docker-compose -f docker-compose.staging.yml up -d
elif [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.prod.yml pull
    docker-compose -f docker-compose.prod.yml up -d
else
    echo "Usage: $0 [staging|production] [branch]"
    exit 1
fi

echo "Deployment to $ENVIRONMENT completed"
echo "Checking health..."
sleep 30

if [ "$ENVIRONMENT" = "staging" ]; then
    curl -f http://localhost:8001/health
else
    curl -f https://your-domain.com/health
fi
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

ENVIRONMENT=${1:-staging}

if [ "$ENVIRONMENT" = "staging" ]; then
    URL="http://localhost:8001/health"
else
    URL="https://your-domain.com/health"
fi

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $response -eq 200 ]; then
    echo "✅ $ENVIRONMENT is healthy"
    exit 0
else
    echo "❌ $ENVIRONMENT is unhealthy (HTTP $response)"
    exit 1
fi
```

## Environment Variables Reference

### Critical Security Variables

```bash
# Generate strong secrets
openssl rand -base64 32  # For SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # For ENCRYPTION_KEY
```

### Production Required Variables

```bash
# Database
PROD_DB_PASSWORD=strong_password_here
PROD_REPLICATION_PASSWORD=replication_password_here

# Security
PROD_SECRET_KEY=32_character_random_string
PROD_ENCRYPTION_KEY=32_character_encryption_key

# External Services
PROD_XENDIT_API_KEY_JAKINET=production_api_key
PROD_XENDIT_API_KEY_JELANTIK=production_api_key

# Monitoring
PROD_SENTRY_DSN=https://your_sentry_dsn
PROD_GRAFANA_PASSWORD=strong_grafana_password
```

## Contact Information

### Development Team
- **Backend Lead**: [Contact Info]
- **Frontend Lead**: [Contact Info]
- **DevOps Lead**: [Contact Info]

### Emergency Contacts
- **On-call DevOps**: [Phone/Email]
- **System Admin**: [Phone/Email]
- **Database Admin**: [Phone/Email]

### Documentation Links
- **Full Deployment Guide**: [DEPLOYMENT.md]
- **GitHub Secrets Setup**: [.github/workflows/secrets-setup.md]
- **API Documentation**: https://your-domain.com/docs
- **Monitoring Dashboard**: https://your-domain.com:3000

---

*This DevOps guide is maintained by the Artacom DevOps team. For questions or updates, please contact the DevOps lead.*