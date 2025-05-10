from django.urls import path
from .views import dashboard, login_view, register_view, logout_view
from . import views

urlpatterns = [
    # Public pages (no login required)
    path('', views.home, name='home'),
    path('services/', views.services_view, name='services'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('contactus/', views.contactus, name='contactus'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Protected pages (login_required)
    path('profile/', views.profile, name='profile'),  # Only accessible by logged-in users
    path('mybookings/', views.mybookings, name='mybookings'),  # Only accessible by logged-in users
    path('history/', views.history, name='history'),  # Only accessible by logged-in users
    path('create_booking/', views.create_booking, name='create_booking'),
    path('mybookings/<int:booking_id>/', views.view_mybooking, name='view_mybooking'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),


    # Dashboard page (protected by login_required)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('booking/', views.booking, name='booking'),
    path('booking/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('booking/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
    path('event/', views.event, name='event'),
    path('equipment/', views.equipment, name='equipment'),
    path('tracking/', views.tracking, name='tracking'),
    path('reviews/', views.reviews, name='reviews'),
    path('customer/', views.customer, name='customer'),
    path('employee/', views.employee, name='employee'),
    path('booking/<int:booking_id>/', views.view_booking, name='view_booking'),
]
