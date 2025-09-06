from django.contrib import admin
from .models_30_08 import RPI_30_08, Meter_30_08

class MeterInline_30_08(admin.TabularInline):
    model = Meter_30_08
    extra = 1

@admin.register(RPI_30_08)
class RPIAdmin_30_08(admin.ModelAdmin):
    list_display = ('pi_name', 'pi_ip', 'location', 'is_active')
    inlines = [MeterInline_30_08]
    search_fields = ('pi_name', 'pi_ip', 'location', 'contact_person')
    list_filter = ('is_active',)

@admin.register(Meter_30_08)
class MeterAdmin_30_08(admin.ModelAdmin):
    list_display = ('meter_name', 'meter_address', 'meter_model', 'location', 'rpi')
    search_fields = ('meter_name', 'meter_model', 'location')
    list_filter = ('meter_model',)
