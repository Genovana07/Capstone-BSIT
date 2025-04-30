from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile

# Register View
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")  # <-- added
        province = request.POST.get("province")
        city = request.POST.get("city")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            Profile.objects.create(
                user=user,
                contact_number=phone,
                address=address,  # <-- added
                province=province,
                city=city
            )
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("login")

    return render(request, "accounts/register.html")
# Login View
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

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

# Profile Page
@login_required
def profile(request):
    if request.method == "POST":
        # Update User basic info
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        # Update Profile extended info
        profile = user.profile
        profile.contact_number = request.POST.get('phone')
        profile.province = request.POST.get('province')
        profile.city = request.POST.get('city')
        profile.address = request.POST.get('address')
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'accounts/profile.html')

# My Bookings Page
@login_required
def mybookings(request):
    booking_list = [
        {'id': 1312213, 'date_booked': 'April 16, 2024', 'event_datetime': 'April 16, 2024', 'status': 'Pending', 'total': 20000},
        {'id': 1312214, 'date_booked': 'April 17, 2024', 'event_datetime': 'April 25, 2024', 'status': 'Approved', 'total': 30000}
    ]
    return render(request, 'accounts/mybookings.html', {'booking_list': booking_list})

# History Page
@login_required
def history(request):
    history_list = [
        {'id': 1312213, 'event_date': 'April 16, 2024', 'package': 'Birthday Package', 'status': 'Completed', 'total': 20000}
    ]
    return render(request, 'accounts/history.html', {'history_list': history_list})

# Dashboard View
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

# Equipment Tracking View
@login_required
def tracking(request):
    return render(request, 'client/tracking.html')

#Reviews
@login_required
def reviews(request):
    return render(request, 'client/reviews.html')

#Customer
@login_required
def customer(request):
    return render(request, 'client/customer.html')

#Employee
@login_required
def employee(request):
    return render(request, 'client/employee.html')