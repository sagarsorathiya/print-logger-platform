#!/bin/bash
# One-Click Deployment Script for Print Tracking Portal
# Usage: ./deploy.sh [production|development]

set -euo pipefail

# Configuration
DEPLOY_MODE="${1:-development}"
PROJECT_NAME="printportal"
DB_NAME="printportal"
DB_USER="printportal_user"
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@localhost}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for production
check_permissions() {
    if [[ "$DEPLOY_MODE" == "production" && $EUID -ne 0 ]]; then
        log_error "Production deployment must be run as root"
        echo "Usage: sudo ./deploy.sh production"
        exit 1
    fi
}

# Generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Generate secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y python3.9 python3.9-venv python3-pip nginx postgresql postgresql-contrib curl git
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y python39 python39-pip nginx postgresql-server postgresql-contrib curl git
        postgresql-setup initdb
    else
        log_error "Unsupported package manager. Please install dependencies manually."
        exit 1
    fi
    
    log_success "System dependencies installed"
}

# Setup PostgreSQL
setup_database() {
    log_info "Setting up PostgreSQL database..."
    
    # Generate database password
    DB_PASSWORD=$(generate_password)
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        # Start PostgreSQL service
        systemctl enable postgresql
        systemctl start postgresql
        
        # Create database and user
        sudo -u postgres psql <<EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
\q
EOF
        
        # Store database URL for production
        DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
    else
        # Use SQLite for development
        DATABASE_URL="sqlite:///./printportal.db"
    fi
    
    log_success "Database setup completed"
}

# Create application user (production only)
create_app_user() {
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        log_info "Creating application user..."
        
        if ! id "$PROJECT_NAME" &>/dev/null; then
            useradd -m -s /bin/bash $PROJECT_NAME
            usermod -aG www-data $PROJECT_NAME
        fi
        
        mkdir -p /opt/$PROJECT_NAME
        chown $PROJECT_NAME:$PROJECT_NAME /opt/$PROJECT_NAME
        
        log_success "Application user created"
    fi
}

# Setup application
setup_application() {
    log_info "Setting up application..."
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        INSTALL_DIR="/opt/$PROJECT_NAME"
        VENV_PATH="$INSTALL_DIR/venv"
        
        # Copy files to production directory
        cp -r . $INSTALL_DIR/
        chown -R $PROJECT_NAME:$PROJECT_NAME $INSTALL_DIR
        
        # Switch to app user for remaining commands
        sudo -u $PROJECT_NAME bash <<EOF
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF
    else
        INSTALL_DIR="$(pwd)"
        VENV_PATH="$INSTALL_DIR/venv"
        
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    log_success "Application setup completed"
}

# Create environment configuration
create_environment() {
    log_info "Creating environment configuration..."
    
    SECRET_KEY=$(generate_secret_key)
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        ENV_FILE="/opt/$PROJECT_NAME/.env"
    else
        ENV_FILE="$(pwd)/.env"
    fi
    
    cat > "$ENV_FILE" <<EOF
# Database Configuration
DATABASE_URL=${DATABASE_URL}

# Security Settings
SECRET_KEY=${SECRET_KEY}
DEBUG=$([[ "$DEPLOY_MODE" == "development" ]] && echo "true" || echo "false")
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS and Security
CORS_ORIGINS=["http://localhost:8080","https://${DOMAIN}"]
ALLOWED_HOSTS=["localhost","${DOMAIN}"]

# Logging
LOG_LEVEL=INFO

# LDAP Configuration (disabled by default)
LDAP_ENABLED=false

# Agent Settings
AGENT_UPDATE_INTERVAL=300
AGENT_OFFLINE_CACHE_DAYS=7
EOF
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        chown $PROJECT_NAME:$PROJECT_NAME "$ENV_FILE"
        chmod 600 "$ENV_FILE"
    fi
    
    log_success "Environment configuration created"
}

# Initialize database
initialize_database() {
    log_info "Initializing database..."
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        sudo -u $PROJECT_NAME bash <<EOF
cd /opt/$PROJECT_NAME
source venv/bin/activate
cd backend
python -m alembic upgrade head
python init_db.py
EOF
    else
        source venv/bin/activate
        python setup_db.py
    fi
    
    log_success "Database initialized"
}

# Setup systemd service (production only)
setup_systemd_service() {
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        log_info "Setting up systemd service..."
        
        cp scripts/printportal.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable printportal
        systemctl start printportal
        
        # Wait for service to start
        sleep 5
        
        if systemctl is-active --quiet printportal; then
            log_success "Systemd service started successfully"
        else
            log_error "Failed to start systemd service"
            journalctl -u printportal --no-pager -l
            exit 1
        fi
    fi
}

# Setup nginx (production only)
setup_nginx() {
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        log_info "Setting up nginx..."
        
        # Create nginx configuration
        sed "s/your-domain.com/${DOMAIN}/g" docs/nginx.conf > /etc/nginx/sites-available/$PROJECT_NAME
        
        # Enable site
        ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Test configuration
        nginx -t
        
        # Start nginx
        systemctl enable nginx
        systemctl restart nginx
        
        log_success "Nginx configured"
        
        # Setup SSL if not localhost
        if [[ "$DOMAIN" != "localhost" ]]; then
            setup_ssl
        fi
    fi
}

# Setup SSL certificate
setup_ssl() {
    log_info "Setting up SSL certificate..."
    
    # Install certbot
    if command -v apt-get &> /dev/null; then
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        yum install -y certbot python3-certbot-nginx
    fi
    
    # Obtain certificate
    certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
    
    log_success "SSL certificate configured"
}

# Setup monitoring scripts
setup_monitoring() {
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        log_info "Setting up monitoring..."
        
        # Make scripts executable
        chmod +x scripts/backup.sh
        chmod +x scripts/health_check.sh
        
        # Setup cron jobs
        crontab -l 2>/dev/null | grep -v printportal > /tmp/crontab_backup || true
        cat >> /tmp/crontab_backup <<EOF
# Print Portal backup (daily at 2 AM)
0 2 * * * /opt/printportal/scripts/backup.sh

# Print Portal health check (every 5 minutes)
*/5 * * * * /opt/printportal/scripts/health_check.sh
EOF
        crontab /tmp/crontab_backup
        rm /tmp/crontab_backup
        
        log_success "Monitoring configured"
    fi
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        # Test API health
        if curl -f -s http://localhost:8000/health > /dev/null; then
            log_success "API health check passed"
        else
            log_error "API health check failed"
            exit 1
        fi
        
        # Test web access
        if curl -f -s "http://localhost/" > /dev/null; then
            log_success "Web server responding"
        else
            log_warning "Web server check failed - this may be normal if nginx is configured for HTTPS only"
        fi
    else
        log_info "Development mode - start services manually:"
        echo "  1. API Server: python -m uvicorn backend.main:app --reload --port 8000"
        echo "  2. Web Portal: cd frontend && python -m http.server 8080"
        echo "  3. Access: http://localhost:8080"
        echo "  4. Login: admin@example.com / admin123"
    fi
}

# Display final information
show_completion_info() {
    log_success "Deployment completed successfully!"
    echo
    echo "=== Deployment Information ==="
    echo "Mode: $DEPLOY_MODE"
    echo "Domain: $DOMAIN"
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        echo "Application Directory: /opt/$PROJECT_NAME"
        echo "Database: PostgreSQL ($DB_NAME)"
        echo "Web URL: https://$DOMAIN"
        echo "API URL: https://$DOMAIN/api/v1/docs"
        echo
        echo "Services:"
        echo "  - systemctl status printportal"
        echo "  - systemctl status nginx"
        echo "  - systemctl status postgresql"
        echo
        echo "Logs:"
        echo "  - journalctl -u printportal -f"
        echo "  - tail -f /var/log/nginx/printportal.error.log"
        echo "  - tail -f /opt/printportal/logs/app.log"
    else
        echo "Database: SQLite (printportal.db)"
        echo "Web URL: http://localhost:8080"
        echo "API URL: http://localhost:8000/docs"
        echo
        echo "To start development servers:"
        echo "  # Terminal 1:"
        echo "  source venv/bin/activate"
        echo "  python -m uvicorn backend.main:app --reload --port 8000"
        echo
        echo "  # Terminal 2:"
        echo "  cd frontend"
        echo "  python -m http.server 8080"
    fi
    
    echo
    echo "Default Admin Login:"
    echo "  Email: admin@example.com"
    echo "  Password: admin123"
    echo
    echo "Next Steps:"
    echo "  1. Change default admin password"
    echo "  2. Configure LDAP/AD integration (if needed)"
    echo "  3. Deploy Windows agents"
    echo "  4. Review monitoring and backup settings"
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        echo "  5. Update firewall rules if needed"
        echo "  6. Schedule regular maintenance"
    fi
}

# Main deployment function
main() {
    echo "=== Print Tracking Portal Deployment ==="
    echo "Mode: $DEPLOY_MODE"
    echo "Domain: $DOMAIN"
    echo
    
    check_permissions
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        install_dependencies
        setup_database
        create_app_user
    else
        setup_database
    fi
    
    setup_application
    create_environment
    initialize_database
    
    if [[ "$DEPLOY_MODE" == "production" ]]; then
        setup_systemd_service
        setup_nginx
        setup_monitoring
    fi
    
    test_deployment
    show_completion_info
}

# Handle interrupts
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
