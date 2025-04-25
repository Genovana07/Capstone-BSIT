from django.urls import path
from .views import dashboard, login_view, register_view, logout_view
from . import views

urlpatterns = [
    # Public pages (no login required)
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('contactus/', views.contactus, name='contactus'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Protected pages (login_required)
    path('profile/', views.profile, name='profile'),  # Only accessible by logged-in users
    path('mybookings/', views.mybookings, name='mybookings'),  # Only accessible by logged-in users
    path('history/', views.history, name='history'),  # Only accessible by logged-in users

    # Dashboard page (protected by login_required)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('booking/', views.booking, name='booking'),
    path('event/', views.event, name='event'),
    path('equipment/', views.equipment, name='equipment'),
    
]
