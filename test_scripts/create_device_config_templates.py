#!/usr/bin/env python3
"""
Create HTML templates for device configuration management
"""


def create_base_template():
    """Create base template with Bootstrap styling"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Device Configuration Management{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        .navbar-brand {
            font-weight: bold;
        }
        .card-header {
            background-color: #007bff;
            color: white;
        }
        .btn-action {
            margin: 2px;
        }
        .meter-row {
            background-color: #f8f9fa;
            margin: 5px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .status-active {
            color: #28a745;
        }
        .status-inactive {
            color: #dc3545;
        }
        .connection-status {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .connection-online {
            background-color: #28a745;
        }
        .connection-offline {
            background-color: #dc3545;
        }
        .connection-unknown {
            background-color: #ffc107;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'device_config:device_config' %}">
                <i class="fas fa-microchip"></i> Device Config Management
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{% url 'meter_readings:dashboard' %}">
                    <i class="fas fa-chart-line"></i> Dashboard
                </a>
                <a class="nav-link" href="{% url 'device_config:device_config' %}">
                    <i class="fas fa-cogs"></i> Device Config
                </a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-4">
        <!-- Messages -->
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    {% block extra_js %}
    {% endblock %}
</body>
</html>
'''


def create_device_config_template():
    """Create main device configuration listing template"""
    return '''
{% extends 'device_config/base.html' %}

{% block title %}Device Configuration Management{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="fas fa-raspberry-pi"></i> Raspberry Pi Configurations
                </h5>
                <a href="{% url 'device_config:add_pi' %}" class="btn btn-light">
                    <i class="fas fa-plus"></i> Add New Pi
                </a>
            </div>
            <div class="card-body">
                {% if pi_configs %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Pi Name</th>
                                    <th>IP Address</th>
                                    <th>Location</th>
                                    <th>Meters</th>
                                    <th>Last Updated</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for pi_config in pi_configs %}
                                <tr>
                                    <td>
                                        <span class="connection-status connection-unknown" id="status-{{ forloop.counter0 }}"></span>
                                        {% if pi_config.is_active %}
                                            <span class="badge bg-success">Active</span>
                                        {% else %}
                                            <span class="badge bg-secondary">Inactive</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <strong>{{ pi_config.pi_name }}</strong>
                                        {% if pi_config.description %}
                                            <br><small class="text-muted">{{ pi_config.description }}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <code>{{ pi_config.pi_ip }}</code>
                                        <br><small class="text-muted">{{ pi_config.ssh_username }}@{{ pi_config.pi_ip }}</small>
                                    </td>
                                    <td>
                                        <i class="fas fa-map-marker-alt"></i> {{ pi_config.location }}
                                        {% if pi_config.contact_person %}
                                            <br><small class="text-muted">Contact: {{ pi_config.contact_person }}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">{{ pi_config.meters|length }} meters</span>
                                        {% for meter in pi_config.meters %}
                                            <br><small class="text-muted">{{ meter.meter_name }} ({{ meter.meter_model }})</small>
                                        {% endfor %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            <i class="fas fa-clock"></i> Just now
                                        </small>
                                    </td>
                                    <td>
                                        <div class="btn-group-vertical btn-group-sm">
                                            <!-- Test Connection -->
                                            <button class="btn btn-outline-info btn-action" 
                                                    onclick="testConnection({{ forloop.counter0 }})"
                                                    id="test-btn-{{ forloop.counter0 }}">
                                                <i class="fas fa-plug"></i> Test
                                            </button>
                                            
                                            <!-- Deploy Config -->
                                            <button class="btn btn-outline-success btn-action" 
                                                    onclick="deployConfig({{ forloop.counter0 }})"
                                                    id="deploy-btn-{{ forloop.counter0 }}">
                                                <i class="fas fa-upload"></i> Deploy
                                            </button>
                                            
                                            <!-- Edit -->
                                            <a href="{% url 'device_config:edit_pi' forloop.counter0 %}" 
                                               class="btn btn-outline-primary btn-action">
                                                <i class="fas fa-edit"></i> Edit
                                            </a>
                                            
                                            <!-- Delete -->
                                            <button class="btn btn-outline-danger btn-action" 
                                                    onclick="deletePi({{ forloop.counter0 }}, '{{ pi_config.pi_name }}')">
                                                <i class="fas fa-trash"></i> Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="fas fa-raspberry-pi fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No Pi configurations found</h5>
                        <p class="text-muted">Add your first Raspberry Pi to get started</p>
                        <a href="{% url 'device_config:add_pi' %}" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Add New Pi
                        </a>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Deletion</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete Pi <strong id="delete-pi-name"></strong>?</p>
                <p class="text-danger">This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form method="post" id="delete-form" style="display: inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function testConnection(piId) {
    const btn = document.getElementById(`test-btn-${piId}`);
    const status = document.getElementById(`status-${piId}`);
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    btn.disabled = true;
    
    fetch(`{% url 'device_config:device_config' %}test-connection/${piId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            status.className = 'connection-status connection-online';
            btn.innerHTML = '<i class="fas fa-check"></i> Connected';
            btn.className = 'btn btn-success btn-action';
        } else {
            status.className = 'connection-status connection-offline';
            btn.innerHTML = '<i class="fas fa-times"></i> Failed';
            btn.className = 'btn btn-danger btn-action';
            alert('Connection failed: ' + data.error);
        }
    })
    .catch(error => {
        status.className = 'connection-status connection-offline';
        btn.innerHTML = '<i class="fas fa-times"></i> Error';
        btn.className = 'btn btn-danger btn-action';
        alert('Connection test failed: ' + error);
    })
    .finally(() => {
        btn.disabled = false;
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-plug"></i> Test';
            btn.className = 'btn btn-outline-info btn-action';
        }, 3000);
    });
}

function deployConfig(piId) {
    const btn = document.getElementById(`deploy-btn-${piId}`);
    
    if (!confirm('Deploy configuration to this Pi?')) return;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deploying...';
    btn.disabled = true;
    
    fetch(`{% url 'device_config:device_config' %}deploy-config/${piId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            btn.innerHTML = '<i class="fas fa-check"></i> Deployed';
            btn.className = 'btn btn-success btn-action';
            alert('Configuration deployed successfully!');
        } else {
            btn.innerHTML = '<i class="fas fa-times"></i> Failed';
            btn.className = 'btn btn-danger btn-action';
            alert('Deployment failed: ' + data.error);
        }
    })
    .catch(error => {
        btn.innerHTML = '<i class="fas fa-times"></i> Error';
        btn.className = 'btn btn-danger btn-action';
        alert('Deployment failed: ' + error);
    })
    .finally(() => {
        btn.disabled = false;
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-upload"></i> Deploy';
            btn.className = 'btn btn-outline-success btn-action';
        }, 3000);
    });
}

function deletePi(piId, piName) {
    document.getElementById('delete-pi-name').textContent = piName;
    document.getElementById('delete-form').action = `{% url 'device_config:device_config' %}delete-pi/${piId}/`;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}
</script>
{% endblock %}
'''


def create_add_pi_template():
    """Create add Pi form template"""
    return '''
{% extends 'device_config/base.html' %}

{% block title %}Add New Pi Configuration{% endblock %}

{% block content %}
<div class="row">
    <div class="col-lg-8 offset-lg-2">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-plus"></i> Add New Raspberry Pi Configuration
                </h5>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    
                    <!-- Pi Basic Information -->
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="pi_name" class="form-label">Pi Name *</label>
                                <input type="text" class="form-control" id="pi_name" name="pi_name" required>
                                <div class="form-text">Unique identifier for this Pi</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="pi_ip" class="form-label">Pi IP Address *</label>
                                <input type="text" class="form-control" id="pi_ip" name="pi_ip" required>
                                <div class="form-text">IP address to connect to this Pi</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="location" class="form-label">Location *</label>
                                <input type="text" class="form-control" id="location" name="location" required>
                                <div class="form-text">Physical location of this Pi</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="contact_person" class="form-label">Contact Person</label>
                                <input type="text" class="form-control" id="contact_person" name="contact_person">
                                <div class="form-text">Person responsible for this Pi</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="description" class="form-label">Description</label>
                        <textarea class="form-control" id="description" name="description" rows="2"></textarea>
                        <div class="form-text">Optional description for this Pi</div>
                    </div>
                    
                    <!-- SSH Configuration -->
                    <h6 class="border-bottom pb-2 mb-3">SSH Configuration</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_username" class="form-label">SSH Username</label>
                                <input type="text" class="form-control" id="ssh_username" name="ssh_username" value="pi">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_password" class="form-label">SSH Password</label>
                                <input type="password" class="form-control" id="ssh_password" name="ssh_password">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_key_path" class="form-label">SSH Key Path</label>
                                <input type="text" class="form-control" id="ssh_key_path" name="ssh_key_path" value="/home/pi/.ssh/id_rsa">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="config_path" class="form-label">Configuration Path</label>
                        <input type="text" class="form-control" id="config_path" name="config_path" value="/home/pi/MFM_offline_setup">
                        <div class="form-text">Path where configuration files will be deployed</div>
                    </div>
                    
                    <!-- Pi Status -->
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="is_active" name="is_active" checked>
                            <label class="form-check-label" for="is_active">
                                Pi is active and should receive deployments
                            </label>
                        </div>
                    </div>
                    
                    <!-- Meter Configurations -->
                    <h6 class="border-bottom pb-2 mb-3">Meter Configurations</h6>
                    <div id="meters-container">
                        <div class="meter-row">
                            <div class="row">
                                <div class="col-md-5">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Name</label>
                                        <input type="text" class="form-control" name="meter_name[]" placeholder="e.g., Main Meter 01">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Modbus Address</label>
                                        <input type="number" class="form-control" name="meter_address[]" value="1" min="1" max="247">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Model</label>
                                        <select class="form-select" name="meter_model[]">
                                            <option value="LG6400">LG6400</option>
                                            <option value="LG6900">LG6900</option>
                                            <option value="LG+5220">LG+5220</option>
                                            <option value="Generic">Generic</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-1">
                                    <div class="mb-3">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeMeter(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <button type="button" class="btn btn-outline-secondary" onclick="addMeter()">
                            <i class="fas fa-plus"></i> Add Another Meter
                        </button>
                    </div>
                    
                    <!-- Form Actions -->
                    <div class="d-flex justify-content-between">
                        <a href="{% url 'device_config:device_config' %}" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Cancel
                        </a>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Save Pi Configuration
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function addMeter() {
    const container = document.getElementById('meters-container');
    const meterRow = document.createElement('div');
    meterRow.className = 'meter-row';
    meterRow.innerHTML = `
        <div class="row">
            <div class="col-md-5">
                <div class="mb-3">
                    <label class="form-label">Meter Name</label>
                    <input type="text" class="form-control" name="meter_name[]" placeholder="e.g., Main Meter 02">
                </div>
            </div>
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Modbus Address</label>
                    <input type="number" class="form-control" name="meter_address[]" value="1" min="1" max="247">
                </div>
            </div>
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Meter Model</label>
                    <select class="form-select" name="meter_model[]">
                        <option value="LG6400">LG6400</option>
                        <option value="LG6900">LG6900</option>
                        <option value="LG+5220">LG+5220</option>
                        <option value="Generic">Generic</option>
                    </select>
                </div>
            </div>
            <div class="col-md-1">
                <div class="mb-3">
                    <label class="form-label">&nbsp;</label>
                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeMeter(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    container.appendChild(meterRow);
}

function removeMeter(button) {
    const meterRow = button.closest('.meter-row');
    const container = document.getElementById('meters-container');
    
    if (container.children.length > 1) {
        meterRow.remove();
    } else {
        alert('At least one meter configuration is required');
    }
}
</script>
{% endblock %}
'''


if __name__ == "__main__":
    from pathlib import Path

    print("📁 Creating device configuration templates...")

    # Create templates directory
    template_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create templates
    templates = {
        'base.html': create_base_template(),
        'device_config.html': create_device_config_template(),
        'add_pi.html': create_add_pi_template(),
    }

    for filename, content in templates.items():
        with open(template_dir / filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created {filename}")

    print("🎨 Device configuration templates created!")
