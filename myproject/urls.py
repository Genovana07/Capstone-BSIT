from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect root URL to the login page
    path('', lambda request: redirect('login'), name='root_redirect'),  # Redirect to login page if accessing the root URL
    
    # Include the accounts URLs (assuming all your app-related views are in 'accounts.urls')
    path('accounts/', include('accounts.urls')),  # Include the accounts URLs
    
    # Redirect various 'accounts' paths to their corresponding views
    path('accounts/home/', lambda request: redirect('home')),  # Redirect to home page
    path('accounts/services/', lambda request: redirect('services')),  # Redirect to services page
    path('accounts/contactus/', lambda request: redirect('contactus')),  # Redirect to contact page
    path('accounts/aboutus/', lambda request: redirect('aboutus')),  # Redirect to about us page
    
    # Any other custom redirects or paths can be added here as needed
]
