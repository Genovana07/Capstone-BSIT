from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile
from django.core.exceptions import PermissionDenied
from .models import Booking,ServicePackage
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from datetime import datetime, timedelta

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        province = request.POST.get("province")
        city = request.POST.get("city")

        # Validation
        if not username:
            messages.error(request, "Username is required.")
        elif not email:
            messages.error(request, "Email is required.")
        elif not password or not confirm_password:
            messages.error(request, "Password and confirmation are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create profile
            Profile.objects.create(
                user=user,
                contact_number=phone,
                address=address,
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
            # Redirect admin users to dashboard
            if user.is_superuser or user.is_staff:
                return redirect("dashboard")
            else:
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

# Services View
def services_view(request):
    packages = [
        {"title": "Basic Birthday Sound System", "description": "For small birthday parties up to 50 guests.", "price": "₱3,000", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Birthday Sound System", "description": "For medium birthday parties up to 100 guests.", "price": "₱5,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Birthday Sound System", "description": "For large birthday parties up to 150 guests.", "price": "₱8,000", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Basic Wedding Sound System", "description": "For small weddings up to 100 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Wedding Sound System", "description": "For medium weddings up to 200 guests.", "price": "₱10,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "2 Subwoofers",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Wedding Sound System", "description": "For large weddings up to 500 guests.", "price": "₱15,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Basic Corporate Event Sound System", "description": "For corporate events up to 50 guests.", "price": "₱4,000", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors",
        "Sound System Setup & Testing",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Corporate Event Sound System", "description": "For corporate events up to 150 guests.", "price": "₱6,500", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Corporate Event Sound System", "description": "For corporate events up to 300 guests.", "price": "₱10,500", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Basic Concert Sound System", "description": "For small concerts up to 100 guests.", "price": "₱7,500", "equipment": [
        "4 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Standard Concert Sound System", "description": "For medium concerts up to 300 guests.", "price": "₱12,000", "equipment": [
        "6 Speakers (300-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Premium Concert Sound System", "description": "For large concerts up to 1,000 guests.", "price": "₱20,000", "equipment": [
        "8 Speakers (600-800 watts)",
        "6 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "5-hour Event Duration"
    ]},
    {"title": "Basic Seminar Sound System", "description": "For seminars up to 50 guests.", "price": "₱3,500", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Seminar Sound System", "description": "For seminars up to 150 guests.", "price": "₱5,500", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Seminar Sound System", "description": "For seminars up to 300 guests.", "price": "₱9,000", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Basic Conference Sound System", "description": "For conferences up to 50 guests.", "price": "₱4,000", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors",
        "Sound System Setup & Testing",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Conference Sound System", "description": "For conferences up to 200 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Conference Sound System", "description": "For conferences up to 500 guests.", "price": "₱12,500", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Custom Sound System Package", "description": "For customized event requirements, price varies.", "price": "Varies", "equipment": [
        "Tailored Speaker Setup",
        "Custom Microphones",
        "Custom Mixer Console",
        "Stage Monitors",
        "Subwoofers",
        "Full Setup & Testing",
        "Duration as per requirement"
    ]},
    {"title": "Basic Graduation Sound System", "description": "For small graduation events up to 100 guests.", "price": "₱6,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Standard Graduation Sound System", "description": "For medium graduation events up to 200 guests.", "price": "₱9,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "2 Subwoofers",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    {"title": "Premium Graduation Sound System", "description": "For large graduation events up to 500 guests.", "price": "₱14,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "3-hour Event Duration"
    ]},
    {"title": "Basic Awarding Ceremony Sound System", "description": "For small awarding ceremonies up to 50 guests.", "price": "₱4,500", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors",
        "Sound System Setup & Testing",
        "1-hour Event Duration"
    ]},
    {"title": "Standard Awarding Ceremony Sound System", "description": "For medium awarding ceremonies up to 150 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "2-hour Event Duration"
    ]},
    # Add remaining packages here...
    ]
    
    range_values = list(range(1, len(packages) + 1))

    return render(request, 'accounts/services.html', {
        'packages': packages,
        'range_values': range_values
    })

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

@login_required
def mybookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    booking_list = []
    for b in bookings:
        booking_list.append({
            'id': b.id,  # ✅ add this line
            'event_datetime': f"{b.event_date.strftime('%B %d, %Y')} at {b.event_time.strftime('%I:%M %p')}",
            'date_booked': b.created_at.strftime('%B %d, %Y'),
            'status': b.status,
            'total': b.price,
            'event_type': b.event_type,
            'package_title': b.package.title,
        })

    return render(request, 'accounts/mybookings.html', {'booking_list': booking_list})

@login_required
def view_mybooking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'accounts/view_mybooking.html', {'booking': booking})

# History Page

@login_required
def history(request):
    bookings = Booking.objects.filter(user=request.user).exclude(status='Processing').order_by('-event_date')

    history_list = []
    for booking in bookings:
        history_list.append({
            'id': booking.id,
            'customer_name': booking.full_name,
            'date_booked': booking.created_at.strftime('%B %d, %Y'),
            'package': booking.package.title,
            'event_date': booking.event_date.strftime('%B %d, %Y'),
            'total': booking.price,
            'rating': '⭐ Rate'  # Placeholder for rating system
        })

    return render(request, 'accounts/history.html', {'history_list': history_list})


@login_required
def create_booking(request):
    if request.method == "POST":
        selected_package = request.POST.get("selected_package")
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        contact_number = request.POST.get("contact_number")
        event_date = request.POST.get("event_date")
        event_time = request.POST.get("event_time")
        event_type = request.POST.get("event_type")
        location = request.POST.get("location")
        audience_size = request.POST.get("audience_size")

        try:
            package = ServicePackage.objects.get(title=selected_package)
        except ServicePackage.DoesNotExist:
            messages.error(request, f"The selected package '{selected_package}' does not exist.")
            return redirect('services')

        # Convert event_time to datetime object
        event_time_obj = datetime.strptime(event_time, "%H:%M")

        # Calculate end time (Assuming 4 hours duration)
        end_time_obj = event_time_obj + timedelta(hours=4)
        end_time = end_time_obj.time()  # Get just the time part

        # Create the booking
        Booking.objects.create(
            user=request.user,
            package=package,
            full_name=full_name,
            email=email,
            contact_number=contact_number,
            event_date=event_date,
            event_time=event_time,
            end_time=end_time,  # Save the calculated end_time
            event_type=event_type,
            location=location,
            audience_size=audience_size,
            price=package.price
        )

        messages.success(request, f"Your booking for {selected_package} has been successfully created!")
        return redirect("mybookings")  # Redirect to user's booking page

    return redirect("services")

def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            print("User is not authenticated.")  # Debugging line
            return redirect("login")
        if not request.user.is_staff and not request.user.is_superuser:
            print(f"User {request.user.username} does not have admin privileges.")  # Debugging line
            raise PermissionDenied  # User is denied access
        return view_func(request, *args, **kwargs)
    return wrapper

# Admin Dashboard

@login_required
@admin_only
def dashboard(request):
    bookings = Booking.objects.all()
    booking_count = bookings.count()
    pending_count = bookings.filter(status="Processing").count()

    def parse_price(price):
        try:
            return float(str(price).replace('₱', '').replace(',', '').strip())
        except:
            return 0.0

    revenue = sum(parse_price(b.price) for b in bookings)
    profit = revenue * 0.5  # or your actual formula

    return render(request, 'client/dashboard.html', {
        'booking_count': booking_count,
        'revenue': revenue,
        'profit': profit,
        'pending_count': pending_count,
    })

# Admin Views
@login_required
@admin_only  # Restrict to admin users
def booking(request):
    bookings = Booking.objects.all()  # Fetch all bookings for admin
    return render(request, 'client/booking.html', {'bookings': bookings})

@login_required
@admin_only
def event(request):
    return render(request, 'client/event.html')

@login_required  # ✅ Only this is needed
def booking_events_api(request):
    bookings = Booking.objects.exclude(status__in=['Rejected', 'Cancelled'])

    events = []
    for booking in bookings:
        events.append({
            "date": booking.event_date.strftime("%Y-%m-%d"),
            "type": booking.event_type,
            "time": booking.event_time.strftime("%H:%M")
        })

    grouped = {}
    for booking in bookings:
        date_str = booking.event_date.strftime("%Y-%m-%d")
        time_str = booking.event_time.strftime("%H:%M")

        if date_str not in grouped:
            grouped[date_str] = {
                "count": 0,
                "times": []
            }

        grouped[date_str]["count"] += 1
        grouped[date_str]["times"].append(time_str)

    return JsonResponse({
        "calendar": events,
        "form_logic": grouped
    }, safe=False)

@login_required
@admin_only
def equipment(request):
    return render(request, 'client/equipment.html')

@login_required
@admin_only
def tracking(request):
    return render(request, 'client/tracking.html')

@login_required
@admin_only
def reviews(request):
    return render(request, 'client/reviews.html')

@login_required
@admin_only
def customer(request):
    return render(request, 'client/customer.html')

@login_required
@admin_only
def employee(request):
    return render(request, 'client/employee.html')

@login_required
def view_booking(request, booking_id):
    # Use get_object_or_404 to avoid the 404 error if booking doesn't exist
    booking = get_object_or_404(Booking, id=booking_id)
    
    return render(request, 'client/view_booking.html', {'booking': booking})

# Accept Booking: Marks a booking as accepted
@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Update the status to 'Accepted'
    booking.status = 'Accepted'
    booking.save()

    messages.success(request, f"Booking {booking.id} has been successfully accepted.")
    return redirect('booking')  # Redirect to the booking list page or booking details page


@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Update the status to 'Rejected'
    booking.status = 'Rejected'
    booking.save()

    messages.success(request, f"Booking {booking.id} has been rejected.")
    return redirect('booking')  # Redirect to the booking list page or booking details page

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status == "Processing":
        booking.status = "Cancelled"
        booking.save()
        messages.success(request, f"Booking #{booking.id} has been cancelled.")
    else:
        messages.warning(request, "Only bookings with 'Processing' status can be cancelled.")
    return redirect('mybookings')
