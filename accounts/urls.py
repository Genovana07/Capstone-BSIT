from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import admin_requests_view, dashboard_redirect  # ✅ tinanggal ko yung request_admin_access_view

urlpatterns = [
    # Public pages (no login required)
    path('', views.home, name='home'),
    path('services/', views.services_view, name='services'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('contactus/', views.contactus, name='contactus'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User pages (login required)
    path('profile/', views.profile, name='profile'),
    path('mybookings/', views.mybookings, name='mybookings'),
    path('mybookings/<int:booking_id>/', views.view_mybooking, name='view_mybooking'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('history/', views.history, name='history'),
    path('create_booking/', views.create_booking, name='create_booking'),
    path('profile/update/', views.update_profile, name='update_profile'),

    # Admin/Dashboard pages (login required)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('booking/', views.booking, name='booking'),
    path('booking/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('booking/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
    path('complete_booking/<int:id>/', views.complete_booking, name='complete_booking'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),

    path('event/', views.event, name='event'),
    path('equipment/', views.equipment, name='equipment'),
    path('tracking/', views.tracking, name='tracking'),
    path('reviews/', views.reviews, name='reviews'),
    path('customer/', views.customer, name='customer'),
    path('employee/', views.employee, name='employee'),

    # APIs
    path('api/bookings/', views.booking_events_api, name='booking_events_api'),
    path('delete_booking/<int:id>/', views.delete_booking, name='delete_booking'),
    path("chatbot-api/", views.chatbot_api, name="chatbot_api"),

    # Inventory
    path('inventory/', views.equipment, name='inventory_list'),
    path('inventory/update/<int:equipment_id>/', views.update_inventory, name='update_inventory'),

    # Admin requests (superuser only)
    path('admin-requests/', views.admin_requests_view, name='admin_requests_view'),
    path('approve-admin/<int:user_id>/', views.approve_admin, name='approve_admin'),

    # Dashboard redirect
    path('dashboard-redirect/', dashboard_redirect, name='dashboard_redirect'),
]

# ✅ Serve media files (if in DEBUG mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
