# Meter Dashboard API Reference

## Overview
- The system uses Django ORM models and Celery tasks for background operations.
- Key models: RaspberryPi, MeterDevice, SystemConfiguration, OTADeployment.
- Key task: run_ota_deployment (background OTA deployment).

## Models
### RaspberryPi
- Stores Pi info, SSH config, location, status.
- Methods: setup_ssh_key, test_ssh_connection.

### MeterDevice
- Stores meter info, address, model, Pi assignment.
- Methods: get_available_meter_models, get_predefined_choices.

### SystemConfiguration
- Stores per-Pi system config (intervals, ports, logging).

### OTADeployment
- Tracks OTA script deployments, status, timestamps.

## Celery Task
### run_ota_deployment(ota_id)
- Args: ota_id (int)
- Syncs files from server to Pi using rsync over SSH.
- Updates status and timestamps.

## Usage
- All models are managed via Django admin.
- Celery tasks are triggered from admin actions.

---
