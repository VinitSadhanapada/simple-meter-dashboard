# 📦 Requirements and Dependencies

## Overview
This document outlines all the Python packages required for the Enhanced Meter Dashboard System with Django integration and field encryption.

## 📁 Requirements Files

### 1. **Main Requirements** - `/requirements.txt`
- **Purpose**: Complete requirements for the entire MFM offline setup
- **Usage**: `pip install -r requirements.txt`
- **Includes**: All packages for Flask, Django, hardware communication, and data processing

### 2. **Django-Specific Requirements** - `/meter_dashboard/requirements.txt`
- **Purpose**: Minimal requirements specifically for the Django meter dashboard
- **Usage**: `pip install -r meter_dashboard/requirements.txt`
- **Includes**: Django framework, database, encryption, and core dependencies

### 3. **Current Environment Snapshot** - `/meter_dashboard/current_environment.txt`
- **Purpose**: Exact freeze of current working environment
- **Usage**: `pip install -r current_environment.txt` (for exact replication)
- **Generated**: `pip freeze > current_environment.txt`

## 🔧 Core Package Categories

### **Django Framework**
```
Django==5.2.4                   # Web framework
djangorestframework==3.16.0     # REST API framework
sqlparse==0.5.3                 # SQL parsing
asgiref==3.9.1                  # ASGI utilities
```

### **Database Support**
```
psycopg2-binary==2.9.10         # PostgreSQL adapter
```

### **Security & Encryption**
```
cryptography==3.4.8             # Field-level encryption for sensitive data
```

### **Environment & Configuration**
```
python-dotenv==1.1.1            # Environment variable loading
```

### **Data Processing**
```
numpy==1.24.3                   # Numerical computing
pandas==2.0.3                   # Data analysis and manipulation
python-dateutil==2.9.0.post0    # Date utilities
pytz==2022.1                    # Timezone support
tzdata==2025.2                  # Timezone database
```

### **Hardware Communication**
```
pymodbus==3.9.2                 # Modbus protocol implementation
pyserial==3.5                   # Serial communication
paho-mqtt==2.1.0                # MQTT client
smbus2==0.4.2                   # I2C/SMBus interface (Raspberry Pi)
```

### **Web Framework (Flask)**
```
flask==2.3.3                    # Web framework for simple dashboards
blinker==1.9.0                  # Signal support
click==8.2.1                    # Command line interface
itsdangerous==2.2.0             # Security utilities
Jinja2==3.1.6                   # Template engine
MarkupSafe==3.0.2               # Safe string handling
Werkzeug==3.1.3                 # WSGI utilities
```

### **Terminal & CLI**
```
termcolor==3.1.0                # Colored terminal output
```

### **Visualization (Optional)**
```
matplotlib==3.10.5              # Plotting library
contourpy==1.3.2                # Contour calculations
cycler==0.12.1                  # Composable style cycles
fonttools==4.59.0               # Font handling
kiwisolver==1.4.8               # Fast implementation of Cassowary constraint solver
Pillow==9.0.1                   # Image processing
```

### **Utilities**
```
six==1.16.0                     # Python 2/3 compatibility
typing_extensions==4.14.1       # Type hints backport
packaging==25.0                 # Package utilities
pyparsing==2.4.7                # Parsing library
```

## 🆕 New Packages Added

### **For Django Integration**
- **Django==5.2.4**: Main web framework
- **djangorestframework==3.16.0**: REST API capabilities
- **sqlparse==0.5.3**: SQL parsing utilities
- **asgiref==3.9.1**: ASGI support

### **For Field Encryption**
- **cryptography==3.4.8**: Provides Fernet encryption for sensitive fields
- **python-dotenv==1.1.1**: Environment variable management

### **Updated Packages**
- **pymodbus**: Updated from 2.5.3 to 3.9.2 for better compatibility
- **numpy**: Updated from 1.24.2 to 1.24.3
- **pytz**: Updated from 2025.2 to 2022.1 for stability

## 🚀 Installation Commands

### **Quick Setup (Django Project)**
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
pip install -r requirements.txt
```

### **Full System Setup**
```bash
cd /home/isha/deepak/MFM_offline_setup
pip install -r requirements.txt
```

### **Exact Environment Replication**
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
pip install -r current_environment.txt
```

## 🔒 Security Considerations

### **Encryption Dependencies**
- **cryptography**: Required for field-level encryption of SSH passwords and key paths
- **python-dotenv**: Securely loads encryption keys from environment files

### **Database Security**
- **psycopg2-binary**: Secure PostgreSQL connection with SSL support

## 📊 Version Management

### **Locked Versions**
All packages are locked to specific versions for:
- **Stability**: Consistent behavior across deployments
- **Security**: Known security states
- **Compatibility**: Tested combinations
- **Offline Deployment**: Reliable package availability

### **Update Strategy**
1. Test updates in development environment
2. Update `requirements.txt` with new versions
3. Regenerate `current_environment.txt`
4. Document changes in this file

## 🐛 Troubleshooting

### **Common Issues**
1. **PostgreSQL Connection**: Ensure `psycopg2-binary` is installed
2. **Encryption Errors**: Check `cryptography` package installation
3. **Django Errors**: Verify Django and related packages versions
4. **Hardware Communication**: Ensure `pymodbus` and `pyserial` compatibility

### **Package Conflicts**
If package conflicts occur:
```bash
pip install --force-reinstall -r requirements.txt
```

## 🎯 Deployment Notes

### **Production Deployment**
- Use `requirements.txt` for predictable deployments
- Include `python-dotenv` for environment management
- Ensure `cryptography` for data security

### **Development Setup**
- Use `current_environment.txt` for exact replication
- Install in virtual environment for isolation
- Test all packages before committing changes
