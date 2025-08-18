"""
Security and Monitoring Improvement Suggestions

1. Enhanced Authentication & Authorization
2. API Security & Rate Limiting
3. Database Security
4. Monitoring & Alerting
5. Backup & Recovery
"""

# Security Settings for Django
SECURITY_IMPROVEMENTS = """
# Add to settings.py

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS Settings (for production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Session Security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# CSRF Protection
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 3600

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/mfm_dashboard.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/mfm_security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'meters': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'device_config': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# API Rate Limiting
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
    'rest_framework.throttling.ScopedRateThrottle',
]

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '5/min',
    'device_config': '50/hour',
}
"""

# Monitoring Script
MONITORING_SCRIPT = '''
#!/bin/bash
# MFM Dashboard Monitoring Script

LOG_FILE="/var/log/mfm_monitoring.log"
EMAIL_ALERT="admin@company.com"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

check_database() {
    psql -U mfmuser -d mfmdb -h localhost -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        log_message "ALERT: Database connection failed"
        echo "Database is down!" | mail -s "MFM DB Alert" $EMAIL_ALERT
        return 1
    fi
    log_message "Database check: OK"
    return 0
}

check_django() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/meter/)
    if [ "$response" != "200" ]; then
        log_message "ALERT: Django application not responding (HTTP $response)"
        echo "Django app is down!" | mail -s "MFM Django Alert" $EMAIL_ALERT
        return 1
    fi
    log_message "Django check: OK"
    return 0
}

check_disk_space() {
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -gt 85 ]; then
        log_message "ALERT: Disk usage is ${disk_usage}%"
        echo "Disk usage is ${disk_usage}%" | mail -s "MFM Disk Alert" $EMAIL_ALERT
    fi
    log_message "Disk usage: ${disk_usage}%"
}

check_memory() {
    memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    if [ $memory_usage -gt 90 ]; then
        log_message "ALERT: Memory usage is ${memory_usage}%"
        echo "Memory usage is ${memory_usage}%" | mail -s "MFM Memory Alert" $EMAIL_ALERT
    fi
    log_message "Memory usage: ${memory_usage}%"
}

check_recent_data() {
    # Check if we have received data in the last 10 minutes
    recent_count=$(psql -U mfmuser -d mfmdb -h localhost -t -c "SELECT COUNT(*) FROM meter_readings WHERE reading_time > NOW() - INTERVAL '10 minutes';" 2>/dev/null)
    
    if [ -z "$recent_count" ] || [ "$recent_count" -eq 0 ]; then
        log_message "ALERT: No recent meter data received"
        echo "No meter data in last 10 minutes" | mail -s "MFM Data Alert" $EMAIL_ALERT
    else
        log_message "Recent data check: $recent_count readings in last 10 minutes"
    fi
}

# Run all checks
log_message "Starting monitoring checks"
check_database
check_django
check_disk_space
check_memory
check_recent_data
log_message "Monitoring checks completed"
'''

# Backup Script
BACKUP_SCRIPT = '''
#!/bin/bash
# MFM Dashboard Backup Script

BACKUP_DIR="/backup/mfm_dashboard"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
pg_dump -U mfmuser -h localhost mfmdb | gzip > $BACKUP_DIR/mfmdb_$DATE.sql.gz

# Application backup
echo "Starting application backup..."
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='*.log' \
    /home/isha/deepak/MFM_offline_setup/

# Configuration backup
echo "Starting configuration backup..."
cp -r /etc/postgresql $BACKUP_DIR/postgresql_config_$DATE
cp /etc/nginx/sites-available/* $BACKUP_DIR/ 2>/dev/null || true

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
'''
