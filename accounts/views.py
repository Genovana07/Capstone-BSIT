from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)  # Auto-hashes password
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("login")

    return render(request, "accounts/register.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)  
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# Home Page
def home(request):
    return render(request, "accounts/home.html") 

# Services Page
def services(request):
    return render(request, "accounts/services.html")

# About Us Page
def aboutus(request):
    return render(request, "accounts/aboutus.html")

# Contact Us Page
def contactus(request):
    return render(request, "accounts/contactus.html")

# Profile Page (Only for Logged-in Users)
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def mybookings(request):
    return render(request, 'accounts/mybookings.html')

@login_required
def history(request):
    # Dummy data example
    history_list = [
        {
            'id': 1312213,
            'event_date': 'April 16, 2024',
            'package': 'Birthday Package',
            'status': 'Completed',
            'total': 20000
        },
        # Add more entries as needed
    ]
    return render(request, 'accounts/history.html', {'history_list': history_list})

@login_required
def mybookings(request):
    # Dummy sample data (replace with real DB query)
    booking_list = [
        {
            'id': 1312213,
            'date_booked': 'April 16, 2024',
            'event_datetime': 'April 16, 2024',
            'status': 'Pending',
            'total': 20000
        },
        {
            'id': 1312214,
            'date_booked': 'April 17, 2024',
            'event_datetime': 'April 25, 2024',
            'status': 'Approved',
            'total': 30000
        }
    ]
    return render(request, 'accounts/mybookings.html', {'booking_list': booking_list})
