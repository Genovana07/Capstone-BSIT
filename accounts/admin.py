from django.contrib import admin
from .models import Booking, ServicePackage, Equipment, PackageEquipment

# Register the Booking model with the admin interface
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'event_type', 'event_date',
        'event_time', 'location', 'status', 'package_title'
    )
    list_filter = ('event_type', 'event_date', 'status', 'package__title')  # Added filter by package title
    search_fields = ('full_name', 'email', 'location', 'package__title')  # Search by full_name, email, location, and package title
    ordering = ('-event_date', 'event_time')

    # Display the package title in the list view
    def package_title(self, obj):
        return obj.package.title
    package_title.short_description = "Package"

# Register the ServicePackage model with the admin interface
@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'equipment_list')  # Added equipment list display
    search_fields = ('title',)
    
    # Display the equipment associated with the service package
    def equipment_list(self, obj):
        return ", ".join([equipment.name for equipment in obj.equipment.all()])
    equipment_list.short_description = "Equipment"

# Register Equipment model with the admin interface for visibility
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity_available', 'quantity_rented')  # Show equipment details
    search_fields = ('name',)

# Register PackageEquipment model to manage the relation between ServicePackage and Equipment
@admin.register(PackageEquipment)
class PackageEquipmentAdmin(admin.ModelAdmin):
    list_display = ('package', 'equipment', 'quantity_required')
    search_fields = ('package__title', 'equipment__name')
