#!/bin/bash

# Backup script for FTTH Billing System
set -e

# Configuration
DB_HOST="postgres"
DB_PORT="5432"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-billing_ftth}"
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/billing_backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Starting database backup at $(date)"

# Create database backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress the backup
gzip $BACKUP_FILE
BACKUP_FILE="${BACKUP_FILE}.gz"

# Upload to cloud storage (optional - uncomment and configure)
# aws s3 cp $BACKUP_FILE s3://your-backup-bucket/

# Remove backups older than 7 days
find $BACKUP_DIR -name "billing_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"

# Upload static files backup (optional)
STATIC_BACKUP_FILE="${BACKUP_DIR}/static_backup_${TIMESTAMP}.tar.gz"
tar -czf $STATIC_BACKUP_FILE -C /app static/

echo "Static files backup completed: $STATIC_BACKUP_FILE"

# Clean old static backups
find $BACKUP_DIR -name "static_backup_*.tar.gz" -mtime +3 -delete

echo "All backups completed successfully at $(date)"