#!/bin/bash
# Health check script for Print Tracking Portal
# Add to cron for regular monitoring: */5 * * * * /opt/printportal/scripts/health_check.sh

set -euo pipefail

# Configuration
PORTAL_URL="https://your-domain.com"
LOG_FILE="/var/log/printportal_health.log"
ALERT_EMAIL="admin@company.com"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Send alert function
send_alert() {
    local message="$1"
    log "ALERT: $message"
    echo "Print Portal Alert: $message" | mail -s "Print Portal Health Alert" "$ALERT_EMAIL" 2>/dev/null || true
}

# Check API health
check_api() {
    if curl -f -s "$PORTAL_URL/health" > /dev/null; then
        log "API health check: OK"
        return 0
    else
        send_alert "API health check failed - $PORTAL_URL/health not responding"
        return 1
    fi
}

# Check service status
check_service() {
    if systemctl is-active --quiet printportal; then
        log "Service status: OK"
        return 0
    else
        send_alert "PrintPortal service is not running"
        return 1
    fi
}

# Check database connectivity
check_database() {
    if sudo -u postgres psql -d printportal -c "SELECT 1;" > /dev/null 2>&1; then
        log "Database connectivity: OK"
        return 0
    else
        send_alert "Database connectivity failed"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -lt 90 ]; then
        log "Disk space: OK ($usage% used)"
        return 0
    else
        send_alert "High disk usage: $usage% - cleanup required"
        return 1
    fi
}

# Check memory usage
check_memory() {
    local mem_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
    if (( $(echo "$mem_usage < 90" | bc -l) )); then
        log "Memory usage: OK ($mem_usage% used)"
        return 0
    else
        send_alert "High memory usage: $mem_usage%"
        return 1
    fi
}

# Check agent connectivity (agents seen in last hour)
check_agents() {
    local offline_count=$(sudo -u postgres psql -d printportal -t -c "
        SELECT COUNT(*) FROM agents 
        WHERE last_seen < NOW() - INTERVAL '1 hour';" | tr -d ' ')
    
    if [ "$offline_count" -eq 0 ]; then
        log "Agent connectivity: OK"
        return 0
    else
        log "WARNING: $offline_count agents offline for >1 hour"
        return 1
    fi
}

# Main health check
main() {
    log "Starting health check"
    
    local issues=0
    
    check_service || ((issues++))
    check_api || ((issues++))
    check_database || ((issues++))
    check_disk_space || ((issues++))
    check_memory || ((issues++))
    check_agents || true  # Don't count agent issues as critical
    
    if [ $issues -eq 0 ]; then
        log "Health check completed - all systems OK"
    else
        log "Health check completed - $issues issues detected"
    fi
}

main "$@"
