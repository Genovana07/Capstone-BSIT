from django.contrib import admin
from django.urls import path, include  # Make sure to import include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='root_redirect'),  # Redirect to login page
    path('accounts/', include('accounts.urls')),  # Include accounts URLs
    path('accounts/home/', lambda request: redirect('home')),  # Redirect to home page
    path('accounts/services/', lambda request: redirect('services')),  # Redirect to services page
    path('accounts/contactus/', lambda request: redirect('contactus')),  # Redirect to contact page
    path('accounts/aboutus/', lambda request: redirect('aboutus')),  # Redirect to about us page
]
