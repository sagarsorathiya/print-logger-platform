# Production Deployment Guide

This guide covers deploying the Distributed Print Tracking Portal in production environments with high availability, security, and scalability.

## 📋 Prerequisites

### System Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 50GB storage
- **Recommended**: 4+ CPU cores, 8GB+ RAM, 200GB+ storage  
- **OS**: Ubuntu 20.04+ or Windows Server 2019+
- **Database**: PostgreSQL 12+ (SQLite for small deployments)
- **Web Server**: nginx (recommended) or Apache
- **SSL Certificate**: Required for production

### Network Requirements
- HTTPS access (port 443) for web portal
- Database access from application server
- Windows PCs with network access to portal for agents

## 🛠️ Production Setup

### 1. Database Setup (PostgreSQL)

**Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

**Create database and user:**
```bash
sudo -u postgres psql

-- Create database and user
CREATE DATABASE printportal;
CREATE USER printportal_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE printportal TO printportal_user;

-- Grant schema permissions
\c printportal
GRANT ALL ON SCHEMA public TO printportal_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO printportal_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO printportal_user;

\q
```

**Configure PostgreSQL:**
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/12/main/postgresql.conf

# Recommended settings for production
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1

# Edit pg_hba.conf for security
sudo nano /etc/postgresql/12/main/pg_hba.conf

# Add application access (replace with actual server IP)
host    printportal     printportal_user    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Application Deployment

**Prepare the system:**
```bash
# Install system dependencies
sudo apt install python3.9 python3.9-venv python3-pip nginx git

# Create application user
sudo useradd -m -s /bin/bash printportal
sudo usermod -aG www-data printportal

# Create application directory
sudo mkdir -p /opt/printportal
sudo chown printportal:printportal /opt/printportal
```

**Deploy the application:**
```bash
# Switch to application user
sudo -u printportal -i

# Clone repository
cd /opt/printportal
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs
```

**Configure environment:**
```bash
# Create production environment file
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://printportal_user:your_secure_password_here@localhost:5432/printportal

# Security Settings
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
DEBUG=false
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS and Security
CORS_ORIGINS=["https://your-domain.com"]
ALLOWED_HOSTS=["your-domain.com"]

# Logging
LOG_LEVEL=INFO

# LDAP Configuration (optional)
LDAP_ENABLED=true
LDAP_SERVER=ldaps://your-domain-controller:636
LDAP_BIND_DN=CN=service-account,OU=Service Accounts,DC=company,DC=com
LDAP_BIND_PASSWORD=service_account_password
LDAP_SEARCH_BASE=DC=company,DC=com

# Agent Settings
AGENT_UPDATE_INTERVAL=300
AGENT_OFFLINE_CACHE_DAYS=7
EOF

# Secure the environment file
chmod 600 .env
```

**Initialize database:**
```bash
# Run migrations
cd backend
python -m alembic upgrade head

# Create initial admin user
python init_db.py
```

### 3. Service Configuration

**Create systemd service:**
```bash
# Copy service file
sudo cp scripts/printportal.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable printportal
sudo systemctl start printportal

# Check service status
sudo systemctl status printportal
```

**Test the API:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Check logs
sudo journalctl -u printportal -f
```

### 4. Web Server Setup (nginx)

**Install and configure nginx:**
```bash
# Install nginx
sudo apt install nginx

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create site configuration
sudo tee /etc/nginx/sites-available/printportal << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;

# Upstream backend
upstream printportal_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/printportal.access.log;
    error_log /var/log/nginx/printportal.error.log;

    # Client settings
    client_max_body_size 10M;
    
    # API endpoints with rate limiting
    location /api/v1/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://printportal_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://printportal_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check (no rate limiting)
    location /health {
        proxy_pass http://printportal_backend;
        access_log off;
    }

    # Static files
    location /static/ {
        alias /opt/printportal/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript application/json image/svg+xml;
    }

    # Frontend
    location / {
        alias /opt/printportal/frontend/;
        try_files $uri $uri/ /index.html;
        
        # Cache HTML files for short time
        location ~* \.html$ {
            expires 1h;
            add_header Cache-Control "public, must-revalidate";
        }
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/printportal /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

**SSL Certificate (Let's Encrypt):**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🔒 Security Configuration

### 1. Firewall Setup
```bash
# Ubuntu/Debian with UFW
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# CentOS/RHEL with firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Environment Security
```bash
# Secure environment file
sudo chown printportal:printportal /opt/printportal/.env
sudo chmod 600 /opt/printportal/.env

# Create log rotation
sudo tee /etc/logrotate.d/printportal << 'EOF'
/opt/printportal/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 printportal printportal
    postrotate
        systemctl reload printportal
    endscript
}
EOF
```

### 3. Database Security
```bash
# Secure PostgreSQL configuration
sudo nano /etc/postgresql/12/main/postgresql.conf

# Add these security settings:
# ssl = on
# password_encryption = scram-sha-256
# log_connections = on
# log_disconnections = on
# log_statement = 'ddl'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. LDAP/Active Directory Integration
```env
# Add to .env file for AD integration
LDAP_ENABLED=true
LDAP_SERVER=ldaps://dc1.company.com:636
LDAP_BIND_DN=CN=print-service,OU=Service Accounts,DC=company,DC=com
LDAP_BIND_PASSWORD=SecureServicePassword123!
LDAP_SEARCH_BASE=DC=company,DC=com
LDAP_USER_FILTER=(sAMAccountName={username})
LDAP_GROUP_FILTER=(member={user_dn})
LDAP_ADMIN_GROUP=CN=PrintPortal Admins,OU=Groups,DC=company,DC=com
```

## 🖥️ Agent Deployment

### 1. Agent Architecture
The Windows agent consists of:
- **Print Monitor Service**: Monitors Windows print spooler
- **API Client**: Communicates with portal backend
- **Local Storage**: Caches data during offline periods
- **Configuration Manager**: Handles settings and updates

### 2. Mass Deployment Options

**Option A: Group Policy Deployment**
```powershell
# Create GPO for software installation
# 1. Open Group Policy Management Console
# 2. Create new GPO: "Print Portal Agent"
# 3. Navigate to: Computer Configuration > Policies > Software Settings > Software Installation
# 4. Right-click > New > Package
# 5. Browse to PrintAgentInstaller.msi
# 6. Choose "Assigned" deployment method

# Set installation parameters via registry
# Computer Configuration > Preferences > Windows Settings > Registry
# Key: HKEY_LOCAL_MACHINE\SOFTWARE\PrintPortal
# Values:
#   - PortalUrl (REG_SZ): https://your-domain.com
#   - SiteId (REG_SZ): SITE001
#   - UpdateInterval (REG_DWORD): 300
```

**Option B: Manual Installation**
```cmd
# Install with parameters
msiexec /i PrintAgentInstaller.msi /quiet ^
  PORTAL_URL=https://your-domain.com ^
  SITE_ID=SITE001 ^
  INSTALL_LOCATION="C:\Program Files\PrintPortal" ^
  /l*v install.log

# Verify installation
sc query "PrintPortalAgent"
```

**Option C: PowerShell Deployment Script**
```powershell
# deploy_agent.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$PortalUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$SiteId,
    
    [string]$ComputerList = "computers.txt"
)

$computers = Get-Content $ComputerList
$msiPath = "\\server\share\PrintAgentInstaller.msi"

foreach ($computer in $computers) {
    if (Test-Connection -ComputerName $computer -Count 1 -Quiet) {
        Write-Host "Installing on $computer..."
        
        $session = New-PSSession -ComputerName $computer -ErrorAction SilentlyContinue
        if ($session) {
            Invoke-Command -Session $session -ScriptBlock {
                param($msi, $url, $site)
                
                $args = "/i `"$msi`" /quiet PORTAL_URL=`"$url`" SITE_ID=`"$site`""
                Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Wait
                
                # Verify service started
                Start-Service -Name "PrintPortalAgent" -ErrorAction SilentlyContinue
            } -ArgumentList $msiPath, $PortalUrl, $SiteId
            
            Remove-PSSession $session
            Write-Host "Completed: $computer"
        } else {
            Write-Warning "Failed to connect to: $computer"
        }
    } else {
        Write-Warning "Cannot reach: $computer"
    }
}
```

### 3. Agent Configuration
```ini
# Default config file: C:\Program Files\PrintPortal\config.ini
[portal]
url = https://your-domain.com
api_key = auto-generated-on-first-run
site_id = SITE001
update_interval = 300

[logging]
level = INFO
max_file_size = 10MB
max_files = 5

[cache]
max_days = 7
max_entries = 10000
sync_interval = 60

[monitoring]
track_color = true
track_duplex = true
track_document_names = true
excluded_printers = Microsoft XPS,Microsoft Print to PDF
```

### 4. Agent Management
```powershell
# Check agent status
Get-Service "PrintPortalAgent"

# View agent logs
Get-Content "C:\Program Files\PrintPortal\logs\agent.log" -Tail 50

# Force configuration update
Restart-Service "PrintPortalAgent"

# Uninstall agent
msiexec /x {PRODUCT-GUID} /quiet
```

## 📊 Monitoring and Maintenance

### 1. Application Monitoring
```bash
# Check service health
sudo systemctl status printportal
curl -f http://localhost:8000/health || echo "API is down"

# Monitor resource usage
htop
sudo iotop -ao
df -h

# Monitor logs in real-time
sudo journalctl -u printportal -f
tail -f /var/log/nginx/printportal.error.log
```

### 2. Database Monitoring
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('printportal')) as size;

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'printportal';

-- Monitor slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
WHERE query LIKE '%print_jobs%' 
ORDER BY mean_time DESC LIMIT 10;
```

### 3. Performance Optimization
```bash
# Database maintenance
sudo -u postgres psql printportal << 'EOF'
-- Analyze tables for query optimization
ANALYZE;

-- Reindex if needed
REINDEX DATABASE printportal;

-- Clean up old statistics
DELETE FROM print_jobs WHERE created_at < NOW() - INTERVAL '1 year';
VACUUM ANALYZE print_jobs;
EOF

# Log rotation
sudo logrotate -f /etc/logrotate.d/printportal

# Clear application cache
sudo systemctl restart printportal
```

### 4. Backup Strategy
```bash
#!/bin/bash
# backup_portal.sh
BACKUP_DIR="/backup/printportal"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
sudo -u postgres pg_dump printportal | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Application files backup
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" \
    /opt/printportal \
    --exclude=/opt/printportal/venv \
    --exclude=/opt/printportal/logs \
    --exclude=/opt/printportal/__pycache__ \
    --exclude=/opt/printportal/.git

# Configuration backup
cp /etc/nginx/sites-available/printportal "$BACKUP_DIR/nginx_$DATE.conf"
cp /etc/systemd/system/printportal.service "$BACKUP_DIR/systemd_$DATE.service"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.conf" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.service" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 5. Agent Fleet Monitoring
```sql
-- Check agent connectivity
SELECT 
    site_id,
    COUNT(*) as agent_count,
    MAX(last_seen) as last_contact,
    CASE 
        WHEN MAX(last_seen) > NOW() - INTERVAL '1 hour' THEN 'Online'
        WHEN MAX(last_seen) > NOW() - INTERVAL '1 day' THEN 'Stale'
        ELSE 'Offline'
    END as status
FROM agents 
GROUP BY site_id
ORDER BY site_id;

-- Monitor print job volume
SELECT 
    DATE(created_at) as date,
    site_id,
    COUNT(*) as jobs,
    SUM(pages) as total_pages
FROM print_jobs 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at), site_id
ORDER BY date DESC, site_id;
```

## 🎯 Post-Deployment Checklist

### Initial Setup Verification
- [ ] Database created and migrations applied
- [ ] Admin user created and can log in
- [ ] API server running and responding to health checks
- [ ] Web portal accessible via HTTPS
- [ ] SSL certificate valid and auto-renewal configured
- [ ] Firewall rules configured properly
- [ ] Log rotation configured

### Security Verification
- [ ] Default passwords changed
- [ ] Environment file permissions set correctly (600)
- [ ] LDAP/AD integration tested (if enabled)
- [ ] JWT tokens working properly
- [ ] API rate limiting active
- [ ] Security headers present in responses

### Monitoring Setup
- [ ] Health check script installed and running
- [ ] Backup script scheduled in cron
- [ ] Log monitoring configured
- [ ] Alert notifications tested
- [ ] Performance baseline established

### Agent Deployment
- [ ] Test agent installed and reporting data
- [ ] Mass deployment method chosen and tested
- [ ] Agent auto-registration working
- [ ] Site identification configured correctly
- [ ] Offline caching tested

### Final Testing
- [ ] Print job data flowing from agents to portal
- [ ] Web dashboard displaying data correctly
- [ ] Reports generating accurate statistics
- [ ] User management working
- [ ] Export functionality tested
- [ ] Multi-site data segregation verified

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- **Daily**: Monitor logs and system health
- **Weekly**: Check agent connectivity and data flow
- **Monthly**: Review and archive old print job data
- **Quarterly**: Update system components and security patches

### Documentation
- Keep deployment documentation updated
- Document any custom configurations
- Maintain agent deployment procedures
- Update troubleshooting guides based on issues encountered

### Monitoring Dashboards
Consider setting up monitoring dashboards with:
- System resource usage (CPU, memory, disk)
- Database performance metrics
- API response times
- Agent connectivity status
- Print job volume trends

---

**Deployment Complete!** Your Distributed Print Tracking Portal is now ready for production use.

For questions or issues, refer to:
- Application logs: `/opt/printportal/logs/`
- System logs: `journalctl -u printportal`
- This deployment guide and troubleshooting sections
- Project README and documentation
