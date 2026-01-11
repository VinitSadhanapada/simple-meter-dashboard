# Quick Start Guide - Simple Meter Dashboard

**Last Updated:** January 6, 2026  
**For:** New developers and IT team

---

## 🚀 5-Minute Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Access to PostgreSQL database (192.168.112.106:5432)
- Redis running locally or via Docker

### Start the Application

```bash
# 1. Navigate to project directory
cd /home/isha/opt/simple-meter-dashboard

# 2. Start all services
docker-compose up -d

# 3. Access the application
# Web Interface: http://localhost:8000
# Grafana: http://localhost:3000
# Loki: http://localhost:3100
```

**Default Admin Credentials:**
- Create with: `docker-compose exec app python meter_dashboard/manage.py createsuperuser`
- Access: http://localhost:8000/admin/

---

## 📖 Essential Documentation

Read these in order:

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete system documentation  
   → Architecture, features, database schema, APIs

2. **[DEPLOYMENT_SECURITY_CHECKLIST.md](DEPLOYMENT_SECURITY_CHECKLIST.md)** - Before production  
   → Security fixes, deployment steps, hardening

3. **[FILE_CLEANUP_GUIDE.md](FILE_CLEANUP_GUIDE.md)** - Clean up legacy files  
   → Identify removable files, cleanup script

4. **[README.md](README.md)** - Original IoT dashboard docs  
   → Raspberry Pi setup, Modbus configuration

---

## 🗺️ Project Navigation

### Key Directories
```
simple-meter-dashboard/
├── meter_dashboard/          # 🎯 Main Django application - START HERE
│   ├── meter_dashboard/      # Settings, URLs, main views
│   ├── meter_readings/       # Meter data viewing & export
│   ├── device_config/        # Raspberry Pi & device management  
│   ├── meters/               # Additional meter models
│   └── alerts/               # Alert system
│
├── iot_scripts/              # ⚙️ IoT configurations
│   ├── config.json           # Database & MQTT settings
│   └── failure_modes.json    # Alert thresholds
│
├── scripts/                  # 🛠️ Utility scripts
│   └── cleanup.sh            # Clean up legacy files
│
└── docs/                     # 📚 Additional documentation
```

### Key Files
```
🔧 Configuration
├── .env                      # Environment variables (SECRETS - not in git)
├── .env.example              # Template for .env (to create)
├── docker-compose.yml        # Service definitions
└── settings.py               # Django configuration

💾 Database
├── iot_scripts/config.json   # DB connection settings
└── PostgreSQL (external)     # mfmdb database on 192.168.112.106

🔐 Security  
├── DEPLOYMENT_SECURITY_CHECKLIST.md  # Pre-production security
└── .env                      # Contains secrets (FIELD_ENCRYPTION_KEY, etc.)
```

---

## 🎯 Common Tasks

### View Latest Meter Readings
```
URL: http://localhost:8000/meter_readings/latest/

Features:
- Filter by meter name
- Switch between "Latest" and "Time Series" views
- Show/hide columns
- Search table
- Export to Excel
```

### Manage Devices
```
URL: http://localhost:8000/device-config/

Features:
- Add/edit Raspberry Pi gateways
- Configure meters per gateway
- Generate and deploy SSH keys
- Export device configurations
```

### View Alerts
```
URL: http://localhost:8000/alerts/

Features:
- Real-time alert monitoring
- Geographic alert map
- Alert history
```

### Access APIs
```
Base: http://localhost:8000/api/

Endpoints:
- /api/alerts/                    # Alert events (JSON)
- /api/alerts/geomap/             # Geographic data
- /api/command-centre/health/     # System health
```

### View Grafana Dashboards
```
URL: http://localhost:3000

Default credentials: admin / admin (change on first login)

Dashboard: "Meter Monitoring Dashboard"
- Real-time meter metrics
- Phase-wise voltage/current
- Power factor and harmonics
- Frequency stability
```

---

## 🔧 Development Workflow

### Make Changes to Code

```bash
# 1. Edit files in meter_dashboard/
nano meter_dashboard/meter_readings/views.py

# 2. If changed models, run migrations
docker-compose exec app python meter_dashboard/manage.py makemigrations
docker-compose exec app python meter_dashboard/manage.py migrate

# 3. Restart application
docker-compose restart app

# 4. View logs
docker-compose logs -f app
```

### Add New Django App

```bash
# 1. Create app
docker-compose exec app python meter_dashboard/manage.py startapp new_app

# 2. Add to INSTALLED_APPS in settings.py
# 3. Create models, views, urls
# 4. Run migrations
```

### Database Operations

```bash
# Access Django shell
docker-compose exec app python meter_dashboard/manage.py shell

# Run SQL directly
docker-compose exec app python meter_dashboard/manage.py dbshell

# Create superuser
docker-compose exec app python meter_dashboard/manage.py createsuperuser

# Backup database
pg_dump -h 192.168.112.106 -U mfmuser -d mfmdb > backup.sql
```

---

## 🧹 Clean Up Legacy Files

The project contains some legacy files from development. To clean up:

```bash
# Review what will be removed
cat FILE_CLEANUP_GUIDE.md

# Run cleanup script
bash scripts/cleanup.sh

# This will:
# - Archive legacy directories (archive/, legacy/)
# - Remove temporary files (*.log, tmp_*.py)
# - Clean Python cache
# - Move old database dumps to backup folder
```

**Important:** Creates a backup before removing anything!

---

## 🐛 Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Port 8000 already in use
sudo lsof -i :8000  # Find process using port
# 2. Database connection failed
# Check DB_HOST, DB_USER, DB_PASSWORD in .env
# 3. Redis not running
docker-compose up redis  # or start local Redis
```

### Can't connect to database

```bash
# Test connection manually
PGPASSWORD='devi' psql -h 192.168.112.106 -U mfmuser -d mfmdb -c "\dt"

# If fails:
# - Check database is running
# - Verify firewall allows connection
# - Check credentials in .env
```

### Grafana dashboards empty

```bash
# 1. Check PostgreSQL datasource in Grafana
# 2. Verify database has data:
PGPASSWORD='devi' psql -h 192.168.112.106 -U mfmuser -d mfmdb -c "SELECT COUNT(*) FROM meter_readings;"

# 3. Check datasource UID matches dashboard JSON
# Should be: postgres-mfmdb or bf1zkrmp84268a
```

### SSH key deployment fails

```bash
# 1. Ensure ssh_password is set in RaspberryPi model
# 2. Test SSH manually:
ssh pi@<raspberry-pi-ip>

# 3. Check logs in Django admin for error details
# 4. Verify SSH port (default 22) is correct
```

### Permission denied in Docker

```bash
# Give ownership to current user
sudo chown -R $USER:$USER .

# Or run as root (not recommended)
docker-compose exec -u root app bash
```

---

## 📚 Learning Resources

### Django Documentation
- [Django Official Docs](https://docs.djangoproject.com/)
- [Django Models](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [Django Views](https://docs.djangoproject.com/en/stable/topics/http/views/)
- [Django Templates](https://docs.djangoproject.com/en/stable/topics/templates/)

### Project-Specific
- [Encrypted Model Fields](https://github.com/foundertherapy/django-encrypted-model-fields) - For SSH password encryption
- [psycopg2](https://www.psycopg.org/docs/) - PostgreSQL adapter
- [Paramiko](http://www.paramiko.org/) - SSH library

### Docker & DevOps
- [Docker Compose](https://docs.docker.com/compose/)
- [Grafana](https://grafana.com/docs/grafana/latest/)
- [PostgreSQL](https://www.postgresql.org/docs/)

---

## 🔄 Regular Maintenance

### Daily
- Check application logs: `docker-compose logs --tail=100 app`
- Monitor disk space: `df -h`

### Weekly
- Review error logs in Django admin
- Check database size: `SELECT pg_size_pretty(pg_database_size('mfmdb'));`

### Monthly
- Update Python dependencies: `pip list --outdated`
- Clean Docker images: `docker system prune`
- Review and rotate logs

### Quarterly
- Security audit (see DEPLOYMENT_SECURITY_CHECKLIST.md)
- Update Django: Check for new releases
- Test backup restoration

---

## 🆘 Getting Help

### Check These First
1. Application logs: `docker-compose logs app`
2. Django admin errors: http://localhost:8000/admin/
3. Database connection: Test with psql
4. This documentation: PROJECT_OVERVIEW.md

### Debug Mode
```bash
# Enable debug output (DEVELOPMENT ONLY)
# Edit .env:
DEBUG=True

# Restart:
docker-compose restart app

# Remember to set DEBUG=False for production!
```

### Common Error Messages

**"relation does not exist"**
→ Run migrations: `python manage.py migrate`

**"no such table: meter_readings"**
→ Check database connection, table exists in PostgreSQL (not Django-managed)

**"CSRF verification failed"**
→ Check ALLOWED_HOSTS in settings.py

**"Permission denied (publickey)"**
→ SSH key not deployed correctly, check device_config app

---

## ✅ Post-Setup Checklist

After initial setup, verify:

- [ ] Application loads: http://localhost:8000
- [ ] Meter readings display with data
- [ ] Device config page accessible
- [ ] Grafana loads: http://localhost:3000
- [ ] Can create/edit devices
- [ ] Can export data to Excel
- [ ] Alerts dashboard shows events
- [ ] API endpoints return data
- [ ] Django admin accessible
- [ ] SSH key generation works (test on one Pi)

---

## 🎓 Next Steps

1. **Read PROJECT_OVERVIEW.md** - Understand system architecture
2. **Explore the admin panel** - http://localhost:8000/admin/
3. **Test key features** - Create device, view readings, check alerts
4. **Review security checklist** - Before production deployment
5. **Clean up legacy files** - Run scripts/cleanup.sh
6. **Customize** - Add your own features, dashboards, reports

---

## 📞 Handover Information

**Current Status:** Development complete, ready for IT team  
**Deployment Target:** To be determined by IT team  
**Security Review:** Required before production (see DEPLOYMENT_SECURITY_CHECKLIST.md)

**Known Issues:**
- None critical for development environment
- Production security fixes required (see checklist)

**Future Enhancements:**
- Add reporting feature (export meter summaries)
- Enhanced alert rules engine
- Mobile app integration
- Additional Grafana dashboards

---

**Document Version:** 1.0  
**Last Updated:** January 6, 2026  
**Maintained By:** Project documentation  

**For detailed information, always refer to:**
- **PROJECT_OVERVIEW.md** - Complete technical documentation
- **DEPLOYMENT_SECURITY_CHECKLIST.md** - Production deployment guide
