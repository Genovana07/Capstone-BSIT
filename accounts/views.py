from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

# Register View
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
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("login")

    return render(request, "accounts/register.html")

# Login View
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

# Logout View
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
    team_members = [
        {'name': 'Alice Reyes', 'img': 'images/speaker1.png'},
        {'name': 'Bob Santos', 'img': 'images/speaker1.png'},
        {'name': 'Charlie Cruz', 'img': 'images/speaker1.png'},
    ]
    return render(request, "accounts/aboutus.html", {'team_members': team_members})

# Contact Us Page
def contactus(request):
    return render(request, "accounts/contactus.html")

# Profile Page (Only for Logged-in Users)
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

# My Bookings (Only for Logged-in Users)
@login_required
def mybookings(request):
    booking_list = [
        {'id': 1312213, 'date_booked': 'April 16, 2024', 'event_datetime': 'April 16, 2024', 'status': 'Pending', 'total': 20000},
        {'id': 1312214, 'date_booked': 'April 17, 2024', 'event_datetime': 'April 25, 2024', 'status': 'Approved', 'total': 30000}
    ]
    return render(request, 'accounts/mybookings.html', {'booking_list': booking_list})

# History Page (Only for Logged-in Users)
@login_required
def history(request):
    history_list = [
        {'id': 1312213, 'event_date': 'April 16, 2024', 'package': 'Birthday Package', 'status': 'Completed', 'total': 20000}
    ]
    return render(request, 'accounts/history.html', {'history_list': history_list})

# Dashboard View (only accessible by logged-in users)
@login_required
def dashboard(request):
    return render(request, 'client/dashboard.html')

# Booking View
@login_required
def booking(request):
    return render(request, 'client/booking.html')

# Event View
@login_required
def event(request):
    return render(request, 'client/event.html')

# Equipment Inventory View
@login_required
def equipment(request):
    return render(request, 'client/equipment.html')