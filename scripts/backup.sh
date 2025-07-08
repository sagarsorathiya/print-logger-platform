#!/bin/bash
# Production backup script for Print Tracking Portal
# Run as root via cron: 0 2 * * * /opt/printportal/scripts/backup.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/backup/printportal"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/printportal_backup.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting backup process"

# Database backup
log "Backing up database..."
if sudo -u postgres pg_dump printportal | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"; then
    log "Database backup completed: db_$DATE.sql.gz"
else
    log "ERROR: Database backup failed"
    exit 1
fi

# Application backup
log "Backing up application files..."
if tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" \
    /opt/printportal \
    --exclude=/opt/printportal/venv \
    --exclude=/opt/printportal/logs \
    --exclude=/opt/printportal/__pycache__ \
    --exclude=/opt/printportal/.git \
    --exclude=/opt/printportal/agent_cache; then
    log "Application backup completed: app_$DATE.tar.gz"
else
    log "ERROR: Application backup failed"
    exit 1
fi

# Configuration backup
log "Backing up configuration files..."
cp /etc/nginx/sites-available/printportal "$BACKUP_DIR/nginx_$DATE.conf"
cp /etc/systemd/system/printportal.service "$BACKUP_DIR/systemd_$DATE.service"
cp /opt/printportal/.env "$BACKUP_DIR/env_$DATE" 2>/dev/null || log "WARNING: .env file not found"

# SSL certificates backup
if [ -d "/etc/letsencrypt/live" ]; then
    tar -czf "$BACKUP_DIR/ssl_$DATE.tar.gz" /etc/letsencrypt/live /etc/letsencrypt/renewal
    log "SSL certificates backup completed: ssl_$DATE.tar.gz"
fi

# Clean old backups
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.conf" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.service" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "env_*" -mtime +$RETENTION_DAYS -delete

# Backup verification
log "Verifying backups..."
if [ -f "$BACKUP_DIR/db_$DATE.sql.gz" ] && [ -f "$BACKUP_DIR/app_$DATE.tar.gz" ]; then
    DB_SIZE=$(stat -c%s "$BACKUP_DIR/db_$DATE.sql.gz")
    APP_SIZE=$(stat -c%s "$BACKUP_DIR/app_$DATE.tar.gz")
    log "Backup verification successful - DB: ${DB_SIZE} bytes, App: ${APP_SIZE} bytes"
else
    log "ERROR: Backup verification failed - missing files"
    exit 1
fi

# Optional: Upload to remote storage
# rsync -az "$BACKUP_DIR/" backup-server:/remote/backup/path/
# log "Remote backup upload completed"

log "Backup process completed successfully"

# Send notification (optional)
# echo "Print Portal backup completed successfully on $(hostname)" | mail -s "Backup Success" admin@company.com
