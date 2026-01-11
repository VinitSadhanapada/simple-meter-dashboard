# Simple Meter Dashboard - Project Overview

**Version:** 1.0  
**Last Updated:** January 6, 2026  
**Status:** Active Development - Ready for Handover

---

## 📋 Table of Contents
1. [Project Purpose](#project-purpose)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Features](#core-features)
5. [Directory Structure](#directory-structure)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Getting Started](#getting-started)
9. [Development Workflow](#development-workflow)
10. [Production Deployment](#production-deployment)

---

## 🎯 Project Purpose

The Simple Meter Dashboard is a comprehensive **electrical meter monitoring and management system** designed for:

- **Real-time monitoring** of electrical meters via Modbus RTU protocol
- **Remote configuration management** of Raspberry Pi devices deployed in the field
- **Alert and health monitoring** of distributed meter infrastructure
- **Data visualization** through integrated Grafana dashboards
- **Centralized device management** for multiple meter installations

### Primary Use Cases:
1. **Field Operations**: Monitor meters deployed across multiple locations
2. **Alert Management**: Track voltage, current, and power anomalies
3. **Device Configuration**: Remotely configure and update Raspberry Pi gateways
4. **Historical Analysis**: Query and export meter reading data
5. **Geographic Tracking**: View meter locations and alert status on maps

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │   Grafana    │  │  Mobile/API  │      │
│  │  (Django)    │  │  Dashboards  │  │   Clients    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────┐       │
│  │         Django Web Application (Port 8000)        │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │       │
│  │  │  Meter   │ │  Device  │ │  Alerts  │         │       │
│  │  │ Readings │ │  Config  │ │  Module  │         │       │
│  │  └──────────┘ └──────────┘ └──────────┘         │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Grafana      │  │    Loki      │  │    Redis     │      │
│  │ (Port 3000)  │  │ (Port 3100)  │  │ (Port 6379)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  PostgreSQL Database (mfmdb) - Port 5432         │       │
│  │                                                    │       │
│  │  • meter_readings (277K+ rows)                   │       │
│  │  • device_config tables                          │       │
│  │  • gateway/meter master tables                   │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    FIELD DEVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Raspberry Pi │  │ Raspberry Pi │  │ Raspberry Pi │      │
│  │   Gateway    │  │   Gateway    │  │   Gateway    │      │
│  │              │  │              │  │              │      │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │      │
│  │ │  Meter 1 │ │  │ │  Meter 2 │ │  │ │  Meter 3 │ │      │
│  │ │  Meter 2 │ │  │ │  Meter 3 │ │  │ │  Meter 4 │ │      │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Raspberry Pi** gateways read meters via Modbus RTU (RS485)
2. Data is published to **PostgreSQL** database via MQTT or direct connection
3. **Django application** provides web interface and REST APIs
4. **Grafana** visualizes real-time metrics from PostgreSQL
5. **Loki** aggregates logs from all components
6. **Redis** handles real-time alerts and caching

---

## 💻 Technology Stack

### Backend Framework
- **Django 5.2.5** - Web framework
- **Python 3.11+** - Programming language
- **PostgreSQL** - Primary database (mfmdb)
- **Redis** - Caching and real-time alerts
- **Celery** - Asynchronous task processing

### Frontend & Visualization
- **Django Templates** - Server-side rendering
- **Grafana** - Real-time dashboards and alerting
- **Loki** - Log aggregation

### Communication Protocols
- **MQTT** - Message broker for IoT data
- **Modbus RTU** - Electrical meter communication
- **REST APIs** - HTTP-based data access
- **SSH** - Remote device configuration

### DevOps & Deployment
- **Docker & Docker Compose** - Containerization
- **Git** - Version control
- **PostgreSQL** - Data persistence

### Key Python Packages
- `psycopg2` - PostgreSQL adapter
- `django-encrypted-model-fields` - Secure credential storage
- `paramiko` - SSH automation
- `paho-mqtt` - MQTT client
- `pymodbus` - Modbus protocol support
- `python-dotenv` - Environment configuration

---

## ✨ Core Features

### 1. **Meter Reading Dashboard** (`/meter_readings/latest/`)
- View latest readings from all meters
- Filter by meter name, location, time range
- Toggle between "Latest" and "Time Series" views
- Column visibility controls
- Search and export to Excel
- Real-time alert highlighting

### 2. **Device Configuration Management** (`/device-config/`)
- Manage Raspberry Pi gateways
- Configure meter devices per gateway
- SSH key management and deployment
- Remote configuration updates
- Export device configurations

### 3. **Alert System** (`/alerts/`)
- Real-time monitoring of meter parameters
- Voltage, current, frequency threshold alerts
- Redis-based event streaming
- Geographic alert mapping
- Email notifications (configured via SMTP)

### 4. **REST API** (`/api/`)
- `/api/alerts/` - Alert event stream
- `/api/alerts/geomap/` - Geographic alert data
- `/api/command-centre/health/` - System health status
- `/api/command-centre/update-meter-gis/` - Update meter locations
- `/api/set_failure_mode/` - Simulate failure scenarios

### 5. **Grafana Integration**
- Pre-built meter monitoring dashboard
- PostgreSQL data source integration
- Real-time refresh (10 seconds)
- Multi-meter selection
- Phase-wise voltage, current, power factor visualization
- Harmonics and frequency stability tracking

### 6. **SSH Remote Management**
- Automated SSH key generation and deployment
- Secure credential storage (encrypted)
- Remote command execution
- Configuration file deployment

---

## 📁 Directory Structure

```
simple-meter-dashboard/
│
├── meter_dashboard/                    # Main Django application
│   ├── meter_dashboard/                # Project settings
│   │   ├── settings.py                 # Django configuration
│   │   ├── urls.py                     # Main URL routing
│   │   ├── views.py                    # Dashboard views
│   │   └── api_views.py                # REST API endpoints
│   │
│   ├── meter_readings/                 # Meter data app
│   │   ├── models.py                   # (Uses external DB table)
│   │   ├── views.py                    # Meter reading views
│   │   ├── urls.py                     # Meter routes
│   │   └── templates/                  # HTML templates
│   │
│   ├── device_config/                  # Device management app
│   │   ├── models.py                   # RaspberryPi, DeviceConfig, etc.
│   │   ├── views.py                    # Device CRUD operations
│   │   ├── signals.py                  # Auto-export on save
│   │   ├── ssh_utils.py                # SSH automation
│   │   └── templates/                  # Device management UI
│   │
│   ├── meters/                         # Meter models app
│   │   ├── models.py                   # DcmsPiSetup, MeterReading, etc.
│   │   ├── views.py                    # Meter views
│   │   └── serializers.py              # API serializers
│   │
│   ├── alerts/                         # Alert system
│   │   ├── models.py                   # Alert models
│   │   └── templates/                  # Alert dashboard
│   │
│   └── templates/                      # Shared templates
│       ├── base_public.html            # Base template
│       ├── dashboard.html              # Main dashboard
│       └── api_live.html               # API testing page
│
├── iot_scripts/                        # IoT data collection
│   ├── config.json                     # Database & MQTT config
│   ├── failure_modes.json              # Alert thresholds
│   └── (legacy dashboard scripts)
│
├── device_config_exports/              # Auto-generated configs
│   └── (Generated JSON files per Pi)
│
├── docs/                               # Documentation
│   └── (Setup guides)
│
├── DevOps/                             # Deployment configs (in SMP/)
│   ├── grafana/                        # Grafana dashboards
│   ├── loki/                           # Loki & Promtail configs
│   └── mqttBroker/                     # Mosquitto MQTT broker
│
├── archive/                            # Old/debug scripts (CLEANUP)
├── legacy/                             # Old implementations (CLEANUP)
├── test_scripts/                       # Test utilities
│
├── docker-compose.yml                  # Container orchestration
├── Dockerfile                          # App container definition
├── requirements.txt                    # Python dependencies
├── .env                                # Environment variables
└── manage.py                           # Django management
```

### Important Files:
- **settings.py**: Django configuration, database settings
- **docker-compose.yml**: Defines app, Grafana, Loki services
- **.env**: Contains secrets (SMTP, encryption key, DB credentials)
- **config.json**: Database and MQTT configuration
- **failure_modes.json**: Alert threshold definitions

---

## 🗄️ Database Schema

### External Database: `mfmdb` (PostgreSQL)

**Main Table: `meter_readings`** (277,520 rows)
```sql
-- Time-series meter data
id SERIAL PRIMARY KEY
device_id VARCHAR(100)
meter_name VARCHAR(100)
time TIMESTAMP
model VARCHAR(100)
location VARCHAR(100)
pi_name VARCHAR(100)
pi_ip VARCHAR(15)

-- Power measurements
watts_total FLOAT
watts_r_ph, watts_y_ph, watts_b_ph FLOAT

-- Voltage measurements  
vln_average FLOAT
v_r_ph, v_y_ph, v_b_ph FLOAT
v_r_harmonics, v_y_harmonics, v_b_harmonics FLOAT

-- Current measurements
a_average FLOAT
a_r_ph, a_y_ph, a_b_ph FLOAT
a_r_harmonics, a_y_harmonics, a_b_harmonics FLOAT

-- Power factor
pf_ave FLOAT
pf_r_ph, pf_y_ph, pf_b_ph FLOAT

-- Reliability metrics
frequency FLOAT
wh_received FLOAT
on_hours FLOAT
load_hours_delivered FLOAT
no_of_interruption INTEGER
```

### Django-Managed Tables:

**`device_config_raspberrypi`** - Gateway devices
- pi_name, pi_ip, location, is_active
- ssh_username, ssh_password (encrypted), ssh_key_path
- mac_address, config_path

**`device_config_deviceconfig`** - Meter devices
- device_name, address, meter_model
- raspberry_pi (FK), device_type
- is_active, configuration (JSON)

**`device_config_modbusconfig`** - Modbus settings
- raspberry_pi (FK), port, baudrate, parity, etc.

**`device_config_systemconfig`** - System settings
- reading_interval, enable_mqtt, enable_rtc

**`dcms_pi_setup`** - Alternative Pi model (meters app)
- Similar to RaspberryPi but different use case

**`env_config`** - Environment config per Pi
- simulation_mode, reading_interval, port

---

## 🔌 API Endpoints

### Main Application (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/meter_readings/latest/` | GET | Latest meter readings with filters |
| `/meter_readings/export/excel/` | GET | Export readings to Excel |
| `/device-config/` | GET | List all Raspberry Pis |
| `/device-config/add/` | POST | Add new Pi |
| `/device-config/<id>/` | GET/PUT/DELETE | Pi detail/update/delete |
| `/device-config/<id>/devices/` | GET | Devices for specific Pi |
| `/meters/` | GET | Meter management |
| `/api/` | GET | API documentation |
| `/api/alerts/` | GET | Alert events stream (JSON) |
| `/api/alerts/geomap/` | GET | Geographic alert data |
| `/api/command-centre/health/` | GET | System health status |
| `/api/set_failure_mode/` | POST | Configure alert thresholds |
| `/ssh-command/` | POST | Execute SSH command on Pi |
| `/alerts/` | GET | Alert dashboard UI |
| `/admin/` | GET | Django admin panel |

### Query Parameters (Meter Readings)

**View Mode:**
- `view_mode=latest` - Latest reading per meter (default)
- `view_mode=timeseries` - Time-series data

**Filters:**
- `meters=<meter_name>` - Filter by meter (multi-select)
- `hours=<int>` - Hours back for time-series view
- `columns=<col_name>` - Select specific columns for export

**Example:**
```bash
# Latest readings for specific meters
GET /meter_readings/latest/?view_mode=latest&meters=Meter1&meters=Meter2

# Last 48 hours time-series
GET /meter_readings/latest/?view_mode=timeseries&hours=48

# Export to Excel
GET /meter_readings/export/excel/?meters=Meter1&columns=watts_total&columns=vln_average
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database (external, pre-configured)
- Redis server (for alerts)
- Docker & Docker Compose (recommended)
- Git

### Quick Start (Docker - Recommended)

1. **Clone the repository**
```bash
cd /home/isha/opt/simple-meter-dashboard
```

2. **Configure environment variables**
```bash
# Edit .env file with your settings
nano .env
```

Required variables:
```env
# Database
DB_HOST=192.168.112.106
DB_PORT=5432
DB_NAME=mfmdb
DB_USER=mfmuser
DB_PASSWORD=<your-password>

# Security
FIELD_ENCRYPTION_KEY=<base64-key>
SECRET_KEY=<django-secret>

# Email Alerts
ALERT_SMTP_HOST=smtp.gmail.com
ALERT_SMTP_PORT=587
ALERT_SMTP_USER=<your-email>
ALERT_SMTP_PASS=<app-password>
ALERT_FROM=<sender-email>
ALERT_TO=<recipient-email>

# Redis
REDIS_URL=redis://host.docker.internal:6379/0
CELERY_BROKER_URL=redis://host.docker.internal:6379/0
```

3. **Start the services**
```bash
docker-compose up -d
```

4. **Access the application**
- Web App: http://localhost:8000
- Grafana: http://localhost:3000
- Loki: http://localhost:3100

### Manual Setup (Development)

1. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
cd meter_dashboard
pip install -r requirements.txt
```

3. **Configure database in config.json**
```bash
cd iot_scripts
nano config.json
```

4. **Run migrations**
```bash
cd meter_dashboard
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Collect static files**
```bash
python manage.py collectstatic --noinput
```

7. **Run development server**
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 🔄 Development Workflow

### Making Changes

1. **Always work in a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Test locally before committing**
```bash
python manage.py test
```

3. **Check for errors**
```bash
python manage.py check
```

4. **Run migrations if models changed**
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding New Features

**To add a new Django app:**
```bash
cd meter_dashboard
python manage.py startapp <app_name>
```

Then add to `INSTALLED_APPS` in settings.py

**To add new API endpoint:**
1. Add view in `meter_dashboard/api_views.py`
2. Add route in `meter_dashboard/urls.py`
3. Test with `/api-live/` page

**To add new model:**
1. Define in appropriate `models.py`
2. Run `makemigrations` and `migrate`
3. Register in `admin.py` for admin interface

### Common Tasks

**View logs:**
```bash
docker-compose logs -f app      # Application logs
docker-compose logs -f grafana  # Grafana logs
docker-compose logs -f loki     # Loki logs
```

**Restart services:**
```bash
docker-compose restart app
```

**Access Django shell:**
```bash
docker-compose exec app python meter_dashboard/manage.py shell
```

**Database backup:**
```bash
pg_dump -h 192.168.112.106 -U mfmuser -d mfmdb > backup_$(date +%Y%m%d).sql
```

---

## 🚢 Production Deployment

**See [DEPLOYMENT_SECURITY_CHECKLIST.md](DEPLOYMENT_SECURITY_CHECKLIST.md) for complete production setup.**

### Key Production Changes:
1. Set `DEBUG = False` in settings.py
2. Configure proper `ALLOWED_HOSTS`
3. Use strong `SECRET_KEY` from environment
4. Enable HTTPS/SSL
5. Configure firewall rules
6. Set up automated backups
7. Configure proper logging
8. Use production-grade WSGI server (Gunicorn)
9. Set up monitoring and alerts
10. Regular security updates

### Environment-Specific Settings

Create separate environment files:
- `.env.development`
- `.env.staging`
- `.env.production`

Load appropriate file based on `DJANGO_ENV` variable.

---

## 📝 Notes for Future Developers

### Code Organization Philosophy
- **Django apps** are feature-based (meter_readings, device_config, alerts)
- **Models** represent both Django-managed and external database tables
- **Views** handle both UI and API responses
- **Templates** use Django template language with minimal JavaScript

### Key Design Decisions
1. **External PostgreSQL**: Main `meter_readings` table not Django-managed (pre-existing)
2. **Encrypted Fields**: SSH passwords and keys encrypted at rest
3. **Signal-based Export**: Device configs auto-export on save (see device_config/signals.py)
4. **Redis Alerts**: Real-time alerts stored in Redis, not database
5. **Docker-first**: Production deployment via docker-compose

### Common Pitfalls
- Don't run migrations on `meter_readings` table (it's managed externally)
- Always use environment variables for secrets
- SSH key paths must be accessible to Docker container
- Redis must be running for alert system to work
- Grafana datasource UID must match dashboard JSON files

### Where to Find Things
- **Alert thresholds**: `iot_scripts/failure_modes.json`
- **Database config**: `iot_scripts/config.json`
- **SMTP config**: `.env` file
- **Grafana dashboards**: `DevOps/grafana/` or `DevOps/loki/dashboards/`
- **SSH utilities**: `meter_dashboard/device_config/ssh_utils.py`
- **API documentation**: Visit `/api/` when app is running

---

## 🆘 Troubleshooting

### Can't connect to database
- Check `DB_HOST` in .env
- Verify PostgreSQL is running: `psql -h <host> -U mfmuser -d mfmdb`
- Check firewall rules

### Grafana can't connect to PostgreSQL
- Verify datasource UID in dashboard JSON matches Grafana config
- Check PostgreSQL allows connections from Grafana container
- Test connection in Grafana UI

### SSH key setup fails
- Ensure `ssh_password` is set in RaspberryPi model
- Check SSH connectivity manually: `ssh pi@<pi_ip>`
- Verify `.ssh` directory permissions (700)

### Alerts not working
- Check Redis is running: `redis-cli ping`
- Verify `REDIS_URL` in environment
- Check `failure_modes.json` has proper thresholds

### Docker container won't start
- Check logs: `docker-compose logs app`
- Verify all environment variables set
- Ensure ports 8000, 3000, 3100 not in use
- Check disk space

---

## 📞 Support & Contacts

**Project Handover Date:** TBD  
**Current Maintainer:** [Your Name]  
**Repository:** [Git URL if available]  
**Documentation:** See `docs/` directory  

**For questions:**
1. Check this documentation
2. Review code comments
3. Check Django admin logs
4. Review Docker logs

---

**Document Version:** 1.0  
**Last Reviewed:** January 6, 2026  
**Next Review:** [To be scheduled by new team]
