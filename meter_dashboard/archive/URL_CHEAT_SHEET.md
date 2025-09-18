# Django URL Management Cheat Sheet

## Quick Reference Commands

### List all URLs in your project
```bash
# Using our custom management command
python manage.py list_urls

# Filter by app
python manage.py list_urls --app meters

# Search for specific patterns
python manage.py list_urls --pattern api

# Output in different formats
python manage.py list_urls --format markdown
python manage.py list_urls --format json
```

### Test URLs
```bash
# Run URL tests
python test_urls.py

# Test specific view in Django shell
python manage.py shell
>>> from django.test import Client
>>> client = Client()
>>> response = client.get('/api/meter/')
>>> print(response.status_code)
```

### Debug URL resolution
```bash
# Django shell - test URL reverse
python manage.py shell
>>> from django.urls import reverse
>>> reverse('meters:meter_data')
>>> reverse('meters:get_device_config', args=['pi001'])
```

## URL Organization Patterns

### 1. RESTful API URLs
```python
# Good pattern
urlpatterns = [
    # Collection endpoints
    path('api/devices/', device_list, name='device_list'),          # GET, POST
    path('api/meters/', meter_list, name='meter_list'),             # GET, POST
    
    # Individual resource endpoints  
    path('api/devices/<int:id>/', device_detail, name='device_detail'),      # GET, PUT, DELETE
    path('api/meters/<int:id>/', meter_detail, name='meter_detail'),         # GET, PUT, DELETE
    
    # Actions on resources
    path('api/devices/<int:id>/activate/', device_activate, name='device_activate'),  # POST
    path('api/devices/<int:id>/config/', device_config, name='device_config'),        # GET, PUT
]
```

### 2. Grouped by functionality
```python
# API endpoints
api_patterns = [
    path('meter/', meter_data, name='meter_data'),
    path('dashboard/', live_dashboard, name='live_dashboard'),
    path('config/<str:pi_device_id>/', get_device_config, name='get_device_config'),
]

# Web interface
web_patterns = [
    path('charts/', dashboard_charts, name='dashboard_charts'),
    path('devices/', device_management, name='device_management'),
]

# Combine with prefixes
urlpatterns = [
    path('api/', include(api_patterns)),
    path('', include(web_patterns)),
]
```

### 3. Versioned APIs
```python
urlpatterns = [
    path('api/v1/', include('myapp.urls_v1')),
    path('api/v2/', include('myapp.urls_v2')),
    path('api/', include('myapp.urls_v2')),  # Default to latest
]
```

## Naming Conventions

### Good URL names
- `meter_data` (action_object)
- `device_list` (object_action)
- `get_device_config` (verb_object_detail)
- `update_device_status` (verb_object_attribute)

### Bad URL names
- `data` (too vague)
- `view1` (meaningless)
- `meter_data_api_endpoint` (too verbose)

## URL Documentation Template

```python
urlpatterns = [
    # === API ENDPOINTS ===
    
    # Data Retrieval
    path('api/meter/', meter_data, name='meter_data'),
    # GET: Retrieve all meter readings
    # Response: JSON with meter data array
    
    path('api/dashboard/', live_dashboard, name='live_dashboard'),
    # GET: Get live dashboard data with current readings
    # Response: JSON with current meter status
    
    # === WEB INTERFACE ===
    
    # Dashboard Views
    path('charts/', dashboard_charts, name='dashboard_charts'),
    # GET: Display dashboard with charts and visualizations
    # Response: HTML page with charts
    
    # === DEVICE MANAGEMENT ===
    
    path('api/config/<str:pi_device_id>/', get_device_config, name='get_device_config'),
    # GET: Retrieve configuration for specific Pi device
    # Parameters: pi_device_id (string) - Device identifier
    # Response: JSON with device configuration
]
```

## Common Django URL Patterns

### Parameter Types
```python
# String (default) - matches any string except '/'
path('articles/<str:slug>/', views.article_detail)

# Integer - matches positive integers
path('devices/<int:device_id>/', views.device_detail)

# UUID - matches UUIDs
path('users/<uuid:user_id>/', views.user_profile)

# Path - matches any string including '/'
path('files/<path:file_path>/', views.file_view)

# Custom converters
path('devices/<device_id:device>/', views.device_view)
```

### Optional Parameters
```python
# Using default values in views
path('archive/', views.archive, name='archive'),
path('archive/<int:year>/', views.archive, name='archive_year'),

# In view function
def archive(request, year=None):
    # Handle both cases
    pass
```

## Debugging URLs

### Common Issues and Solutions

1. **NoReverseMatch Error**
```python
# Problem: reverse('device_detail', args=[device.id])
# Solution: Check URL name and parameters match exactly
reverse('meters:device_detail', args=[device.id])
```

2. **URL not found (404)**
```python
# Check URL patterns order (more specific patterns first)
urlpatterns = [
    path('devices/new/', device_new, name='device_new'),      # Specific first
    path('devices/<int:id>/', device_detail, name='device_detail'),  # General last
]
```

3. **Multiple URL matches**
```python
# Use namespaces to avoid conflicts
# In app urls.py
app_name = 'meters'

# In main urls.py  
path('meters/', include('meters.urls', namespace='meters')),
```

## URL Testing Checklist

- [ ] All URLs have meaningful names
- [ ] URLs follow RESTful conventions
- [ ] API endpoints are properly versioned
- [ ] All URLs are documented
- [ ] URL tests pass
- [ ] No duplicate URL names
- [ ] Proper use of namespaces
- [ ] URL patterns are ordered correctly
