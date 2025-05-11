from django.contrib import admin
from .models import Booking, ServicePackage

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'event_type', 'event_date',
        'event_time', 'location', 'status'
    )
    list_filter = ('event_type', 'event_date', 'status')
    search_fields = ('full_name', 'email', 'location')
    ordering = ('-event_date', 'event_time')

@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    search_fields = ('title',)
