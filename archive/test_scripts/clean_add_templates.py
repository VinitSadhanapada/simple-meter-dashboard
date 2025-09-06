#!/usr/bin/env python3
"""
Create clean add device template without extra fields
"""
from pathlib import Path

def create_clean_add_device_template():
    """Create add_device.html without extra fields"""
    
    template_content = '''{% extends 'device_config/base.html' %}

{% block title %}Add New Device{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-plus"></i> Add New Raspberry Pi Device
                    </h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <!-- Essential Device Information -->
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="pi_name" class="form-label">Device Name *</label>
                                    <input type="text" class="form-control" id="pi_name" name="pi_name" required>
                                    <div class="form-text">Unique identifier for this device</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="pi_ip" class="form-label">IP Address *</label>
                                    <input type="text" class="form-control" id="pi_ip" name="pi_ip" required>
                                    <div class="form-text">IP address for SSH connection</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="location" class="form-label">Location *</label>
                            <input type="text" class="form-control" id="location" name="location" required>
                            <div class="form-text">Physical location of this device</div>
                        </div>
                        
                        <!-- SSH Configuration -->
                        <h6 class="border-bottom pb-2 mb-3">SSH Configuration</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="ssh_username" class="form-label">SSH Username</label>
                                    <input type="text" class="form-control" id="ssh_username" name="ssh_username" value="pi">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="ssh_password" class="form-label">SSH Password</label>
                                    <input type="password" class="form-control" id="ssh_password" name="ssh_password">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="ssh_key_path" class="form-label">SSH Key Path</label>
                                    <input type="text" class="form-control" id="ssh_key_path" name="ssh_key_path" value="/home/pi/.ssh/id_rsa">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="config_path" class="form-label">Configuration Path</label>
                                    <input type="text" class="form-control" id="config_path" name="config_path" value="/home/pi/MFM_offline_setup">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Pi Status -->
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="is_active" name="is_active" checked>
                                <label class="form-check-label" for="is_active">
                                    Device is active and should receive deployments
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
                                            <label class="form-label">Meter Address</label>
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
                        
                        <!-- Hidden fields for removed extra fields -->
                        <input type="hidden" name="contact_person" value="">
                        <input type="hidden" name="description" value="">
                        
                        <!-- Form Actions -->
                        <div class="d-flex justify-content-between">
                            <a href="{% url 'device_config:device_list' %}" class="btn btn-secondary">
                                <i class="fas fa-arrow-left"></i> Cancel
                            </a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Save Device Configuration
                            </button>
                        </div>
                    </form>
                </div>
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
                    <label class="form-label">Meter Address</label>
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
{% endblock %}'''
    
    template_file = Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/add_device.html')
    template_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ Created clean add_device.html template")

def main():
    """Create clean templates"""
    
    print("🧹 Creating clean add device templates...")
    
    create_clean_add_device_template()
    
    print("""
🎉 Templates Fixed!

✅ Removed extra fields:
   ❌ Contact Person field
   ❌ Description field
   
✅ Fixed field names:
   ✅ "Meter Address" (not "Modbus Address")
   
✅ Hidden fields still send empty values for:
   • contact_person = ""
   • description = ""
   
📝 Now the form only shows essential fields:
   • Pi Name (required)
   • IP Address (required) 
   • Location (required)
   • SSH Configuration
   • Meter Configurations
   
🔗 Access at: http://localhost:8000/device-config/add/
    """)

if __name__ == "__main__":
    main()