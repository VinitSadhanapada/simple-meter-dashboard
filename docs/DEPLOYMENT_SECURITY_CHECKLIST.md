# Production Deployment & Security Checklist

**Project:** Simple Meter Dashboard  
**Prepared for:** IT Team Handover  
**Date:** January 6, 2026  
**Priority:** CRITICAL - Execute before production deployment

---

## 🔴 CRITICAL SECURITY ISSUES (Must Fix Before Production)

### 1. Django SECRET_KEY Hardcoded ❌
**File:** `meter_dashboard/meter_dashboard/settings.py`  
**Current:** Hardcoded insecure key  
**Risk:** Session hijacking, CSRF bypass, data tampering

**Fix:**
```python
# OLD (Line ~34):
SECRET_KEY = 'django-insecure-oj5u3*o#et2qytr%ujc&4=yukmyq2473z%%x54^+)j7&w1cw+h'

# NEW:
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")
```

**Generate new key:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Add to `.env`:
```env
SECRET_KEY=<generated-key-here>
```

---

### 2. DEBUG Mode Enabled ❌
**File:** `meter_dashboard/meter_dashboard/settings.py`  
**Current:** `DEBUG = True`  
**Risk:** Exposes stack traces, settings, database queries to users

**Fix:**
```python
# Line ~37
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

Add to `.env`:
```env
# Development
DEBUG=True

# Production
DEBUG=False
```

---

### 3. ALLOWED_HOSTS Too Permissive ❌
**File:** `meter_dashboard/meter_dashboard/settings.py`  
**Current:** `ALLOWED_HOSTS = ['*']`  
**Risk:** Host header poisoning attacks

**Fix:**
```python
# Line ~40
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

Add to `.env`:
```env
# Production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,<server-ip>
```

---

### 4. Hardcoded Database Password Fallbacks ❌
**File:** `meter_dashboard/meter_readings/views.py`  
**Lines:** 28, 89, 287  
**Current:** Falls back to `password='devi'`  
**Risk:** Weak password exposed in code

**Fix:** Remove ALL hardcoded password fallbacks
```python
# OLD:
password=db_settings.get('PASSWORD', 'devi'),

# NEW:
password=db_settings.get('PASSWORD'),
```

Then ensure `.env` ALWAYS has:
```env
DB_PASSWORD=<strong-password>
```

---

### 5. Sensitive Files Not in .gitignore ❌
**Files at risk:**
- `.env` (contains SMTP passwords, encryption keys)
- `.env.grafana`
- `iot_scripts/config.json` (database credentials)

**Fix:** Verify `.gitignore` contains:
```gitignore
# Environment files
.env
.env.*
*.env

# Config files with secrets
iot_scripts/config.json
config.json

# Logs
*.log
logs/
dashboard_debug.log

# Database dumps
*.sql
*.dump

# Python
__pycache__/
*.pyc
.venv/
venv/

# Django
staticfiles/
db.sqlite3

# SSH keys
*.pem
*.key
id_rsa*

# Device exports (may contain sensitive info)
device_config_exports/*.json
```

---

### 6. No HTTPS/SSL Enforcement ❌
**Current:** HTTP only  
**Risk:** Credentials sent in plaintext

**Fix:** Add to settings.py (production only):
```python
if not DEBUG:
    # HTTPS Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

**Deployment:** Use nginx/Apache as reverse proxy with SSL certificates

---

## 🔶 IMPORTANT SECURITY IMPROVEMENTS

### 7. Add Security Middleware
**File:** `settings.py` MIDDLEWARE section

Add after existing middleware:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... existing middleware ...
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add these:
    'django.middleware.csrf.CsrfViewMiddleware',  # Already present - verify
]
```

---

### 8. Database Connection Security
**File:** `settings.py`

Add SSL/TLS for database connection:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',  # Add this in production
        },
    }
}
```

---

### 9. Rate Limiting (Prevent DoS)
Install django-ratelimit:
```bash
pip install django-ratelimit
```

Add to views that accept POST:
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # ...
```

---

### 10. Update Password Validation
Already configured but verify strength:
```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},  # Increase from 8 to 12
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Configuration

- [ ] Generate strong SECRET_KEY and add to environment
- [ ] Set DEBUG=False for production
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Remove all hardcoded passwords from code
- [ ] Change default database password ('devi' to strong password)
- [ ] Verify .gitignore covers all sensitive files
- [ ] Create .env.example template (without real secrets)
- [ ] Set up SSL certificates (Let's Encrypt recommended)

### Database

- [ ] Use strong PostgreSQL password (16+ characters, mixed)
- [ ] Restrict PostgreSQL access to specific IPs only
- [ ] Enable SSL for PostgreSQL connections
- [ ] Set up automated daily backups
- [ ] Test backup restoration procedure
- [ ] Create read-only database user for Grafana

### Application

- [ ] Run `python manage.py check --deploy`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Run all migrations: `python manage.py migrate`
- [ ] Create admin superuser with strong password
- [ ] Test all critical endpoints
- [ ] Verify CSRF protection working
- [ ] Test file upload limits (prevent large file DoS)

### Docker & Services

- [ ] Use production-ready Dockerfile (multi-stage build)
- [ ] Don't run containers as root
- [ ] Limit container resources (CPU, memory)
- [ ] Use Docker secrets instead of environment variables
- [ ] Scan images for vulnerabilities: `docker scan <image>`
- [ ] Use specific version tags (not :latest)
- [ ] Configure log rotation for containers

### Network & Infrastructure

- [ ] Configure firewall (only allow 80, 443, 22)
- [ ] Disable direct database access from internet
- [ ] Use VPN for SSH access if possible
- [ ] Set up fail2ban for SSH brute-force protection
- [ ] Configure nginx/Apache reverse proxy
- [ ] Enable nginx rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)

### Redis Security

- [ ] Set Redis password: `requirepass <strong-password>`
- [ ] Bind Redis to localhost only (not 0.0.0.0)
- [ ] Disable dangerous commands: `rename-command FLUSHALL ""`
- [ ] Enable Redis persistence (AOF or RDB)

### Secrets Management

- [ ] Rotate SMTP passwords
- [ ] Rotate FIELD_ENCRYPTION_KEY
- [ ] Store secrets in vault (HashiCorp Vault/AWS Secrets Manager)
- [ ] Use different keys for dev/staging/production
- [ ] Document secret rotation procedures

### Monitoring & Logging

- [ ] Set up centralized logging (Loki already configured)
- [ ] Configure log retention policy
- [ ] Set up error alerting (Sentry or similar)
- [ ] Monitor disk space usage
- [ ] Set up uptime monitoring
- [ ] Configure Grafana alerts for critical metrics
- [ ] Create runbook for common issues

### Backup & Recovery

- [ ] Automated PostgreSQL backups (pg_dump daily)
- [ ] Backup Redis AOF/RDB files
- [ ] Backup device_config_exports directory
- [ ] Store backups off-site (S3, external drive)
- [ ] Test restoration procedure quarterly
- [ ] Document recovery time objectives (RTO)

### Documentation

- [ ] Complete API documentation
- [ ] Document all environment variables
- [ ] Create troubleshooting guide
- [ ] Document deployment process
- [ ] Create rollback procedures
- [ ] Document database schema changes
- [ ] Create user manual for web interface

---

## 🔧 PRODUCTION DEPLOYMENT STEPS

### Step 1: Prepare Environment File

Create `.env.production`:
```env
# Django Core
SECRET_KEY=<50-char-random-string>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,<server-ip>

# Database
DB_ENGINE=postgresql
DB_HOST=<internal-db-host>
DB_PORT=5432
DB_NAME=mfmdb
DB_USER=mfmuser
DB_PASSWORD=<strong-password>

# Security
FIELD_ENCRYPTION_KEY=<base64-32-bytes>

# Email (SMTP)
ALERT_SMTP_HOST=smtp.gmail.com
ALERT_SMTP_PORT=587
ALERT_SMTP_USER=<email>
ALERT_SMTP_PASS=<app-specific-password>
ALERT_FROM=<sender-email>
ALERT_TO=<recipient-email>

# Redis
REDIS_URL=redis://:password@redis:6379/0
CELERY_BROKER_URL=redis://:password@redis:6379/0

# Application
DEVICE_CONFIG_EXPORT_DIR=/app/device_config_exports
```

### Step 2: Update Docker Compose for Production

Create `docker-compose.prod.yml`:
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: meter_dashboard_prod
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    volumes:
      - ./device_config_exports:/app/device_config_exports:ro
      - static_volume:/app/staticfiles
    restart: unless-stopped
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/command-centre/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: redis_prod
    command: redis-server --requirepass <redis-password> --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana_prod
    env_file:
      - .env.production
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped
    ports:
      - "3000:3000"

  loki:
    image: grafana/loki:3.4.1
    container_name: loki_prod
    volumes:
      - loki_data:/tmp/loki
    restart: unless-stopped
    ports:
      - "3100:3100"

  nginx:
    image: nginx:alpine
    container_name: nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/static:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
  grafana_data:
  loki_data:
  static_volume:
```

### Step 3: Create Production Dockerfile

Create `Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt meter_dashboard/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "meter_dashboard.meter_dashboard.wsgi:application"]
```

### Step 4: Nginx Configuration

Create `nginx/nginx.conf`:
```nginx
upstream django_app {
    server app:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location /static/ {
        alias /static/;
    }

    location / {
        proxy_pass http://django_app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

### Step 5: Deploy

```bash
# 1. Pull latest code
git pull origin main

# 2. Build production images
docker-compose -f docker-compose.prod.yml build

# 3. Run migrations
docker-compose -f docker-compose.prod.yml run --rm app python meter_dashboard/manage.py migrate

# 4. Collect static files
docker-compose -f docker-compose.prod.yml run --rm app python meter_dashboard/manage.py collectstatic --noinput

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Check health
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/command-centre/health/
```

---

## 🧪 TESTING CHECKLIST

Before going live, test:

- [ ] All pages load without errors
- [ ] Login/logout functionality
- [ ] Meter readings display correctly
- [ ] Device configuration CRUD operations
- [ ] SSH key generation and deployment
- [ ] Alert system triggers correctly
- [ ] Grafana dashboards load
- [ ] API endpoints return valid responses
- [ ] Excel export works
- [ ] CSRF protection blocks invalid requests
- [ ] Rate limiting works
- [ ] SSL certificate valid
- [ ] Redirects HTTP to HTTPS
- [ ] Session timeout works
- [ ] Password reset email sends
- [ ] Backups running automatically

---

## 🔍 POST-DEPLOYMENT MONITORING

### Week 1:
- Monitor logs daily for errors
- Check disk space daily
- Verify backups complete successfully
- Monitor response times
- Check for failed login attempts

### Month 1:
- Review security logs
- Test backup restoration
- Update dependencies
- Review access logs for anomalies
- Conduct security scan

### Quarterly:
- Security audit
- Password rotation
- Dependency updates
- Performance optimization
- Disaster recovery drill

---

## 🚨 INCIDENT RESPONSE

### If Breach Suspected:
1. Isolate affected systems
2. Preserve logs
3. Notify management/security team
4. Change all passwords and keys
5. Review access logs
6. Conduct forensics
7. Document incident
8. Update security measures

### Emergency Contacts:
- **IT Team Lead:** [TBD]
- **Database Admin:** [TBD]
- **Security Officer:** [TBD]

---

## 📚 COMPLIANCE & STANDARDS

### Recommended Compliance:
- [ ] GDPR (if handling EU data)
- [ ] ISO 27001 (Information Security)
- [ ] NIST Cybersecurity Framework
- [ ] OWASP Top 10 (Web Application Security)

### Regular Audits:
- Code security review (quarterly)
- Penetration testing (annually)
- Dependency vulnerability scan (monthly)
- Access control review (quarterly)

---

## 🎓 SECURITY TRAINING

### For IT Team:
1. Django security best practices
2. Docker security hardening
3. PostgreSQL security configuration
4. Incident response procedures
5. Backup and recovery procedures

### Resources:
- [Django Security Docs](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Last Updated:** January 6, 2026  
**Review Schedule:** Quarterly  
**Next Review:** April 2026  

**IMPORTANT:** This checklist must be completed BEFORE production deployment.  
**DO NOT skip any critical security items.**
