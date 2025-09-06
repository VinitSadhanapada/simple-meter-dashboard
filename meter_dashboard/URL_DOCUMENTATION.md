# Django URL Documentation - Meter Dashboard

## Project URL Structure

### Main Project URLs (`meter_dashboard/urls.py`)
- `admin/` - Django Admin Interface
- `` (root) - Includes all meter app URLs

### Meter App URLs (`meters/urls.py`)

#### API Endpoints

##### Data Retrieval APIs
| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `api/meter/` | `meter_data` | `meters:meter_data` | GET | Retrieve meter readings and data |
| `api/dashboard/` | `live_dashboard` | `meters:live_dashboard` | GET | Get live dashboard data |

##### Device Configuration APIs
| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `api/config/<pi_device_id>/` | `get_device_config` | `meters:get_device_config` | GET | Get device configuration by PI ID |
| `api/status/<pi_device_id>/` | `update_device_status` | `meters:update_device_status` | POST | Update device status |

#### Web Interface URLs

##### Dashboard Views
| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `charts/` | `dashboard_charts` | `meters:dashboard_charts` | GET | Display dashboard with charts |
| `devices/` | `device_management` | `meters:device_management` | GET | Device management interface |

##### Device Management Actions
| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `devices/<device_id>/push-config/` | `push_config_view` | `meters:push_config` | POST | Push configuration to device |

## URL Naming Conventions

### Pattern: `app_name:url_name`
- Use app namespaces to avoid conflicts
- Use descriptive, action-based names
- Follow REST conventions for APIs

### Examples:
```python
# In templates
{% url 'meters:dashboard_charts' %}
{% url 'meters:get_device_config' pi_device_id='pi001' %}

# In views
from django.urls import reverse
url = reverse('meters:meter_data')
```

## API Testing Commands

### Using curl:
```bash
# Get meter data
curl -X GET http://localhost:8000/api/meter/

# Get dashboard data
curl -X GET http://localhost:8000/api/dashboard/

# Get device config
curl -X GET http://localhost:8000/api/config/pi001/

# Update device status
curl -X POST http://localhost:8000/api/status/pi001/ \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

### Using Django shell:
```python
from django.test import Client
from django.urls import reverse

client = Client()

# Test API endpoints
response = client.get(reverse('meters:meter_data'))
response = client.get(reverse('meters:get_device_config', args=['pi001']))
```

## URL Organization Guidelines

1. **Group by functionality** - APIs, web views, actions
2. **Use consistent naming** - Follow REST patterns
3. **Add comments** - Explain complex URLs
4. **Version APIs** - For future compatibility
5. **Use namespaces** - Prevent URL name conflicts

## Future Considerations

### API Versioning
```python
# Future API versioning structure
path('api/v1/meter/', meter_data_v1, name='meter_data_v1'),
path('api/v2/meter/', meter_data_v2, name='meter_data_v2'),
```

### Authentication URLs
```python
# When adding authentication
path('auth/login/', auth_views.LoginView.as_view(), name='login'),
path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
```
