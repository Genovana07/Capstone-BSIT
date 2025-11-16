from django.contrib import admin
from .models import Booking, ServicePackage, Equipment, PackageEquipment, Review

# --------------------
# BOOKING ADMIN
# --------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'event_type', 'event_date',
        'event_time', 'location', 'status', 'package_title'
    )
    list_filter = ('event_type', 'event_date', 'status', 'package__title')
    search_fields = ('full_name', 'email', 'location', 'package__title')
    ordering = ('-event_date', 'event_time')

    def package_title(self, obj):
        return obj.package.title if obj.package else "-"
    package_title.short_description = "Package"


# --------------------
# PACKAGE EQUIPMENT INLINE
# --------------------
class PackageEquipmentInline(admin.TabularInline):
    model = PackageEquipment
    extra = 0
    fields = ("equipment", "quantity_required")
    show_change_link = True


# --------------------
# SERVICE PACKAGE ADMIN
# --------------------
@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'equipment_list')
    search_fields = ('title', 'category')
    inlines = [PackageEquipmentInline]  # ✅ show equipment inline per package

    def equipment_list(self, obj):
        return ", ".join(
            [f"{pe.equipment.name} (x{pe.quantity_required})"
             for pe in PackageEquipment.objects.filter(package=obj)]
        )
    equipment_list.short_description = "Equipment"


# --------------------
# EQUIPMENT ADMIN
# --------------------
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity_available', 'quantity_rented')
    search_fields = ('name',)


# --------------------
# PACKAGE EQUIPMENT ADMIN
# --------------------
@admin.register(PackageEquipment)
class PackageEquipmentAdmin(admin.ModelAdmin):
    list_display = ('package', 'equipment', 'quantity_required')
    search_fields = ('package__title', 'equipment__name')
    list_filter = ('package', 'equipment')


# --------------------
# REVIEW ADMIN
# --------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'comment', 'created_at')
    search_fields = ('booking__full_name', 'comment')
    list_filter = ('rating', 'created_at')
