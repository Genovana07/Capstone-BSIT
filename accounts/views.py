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
from django.core.files.storage import FileSystemStorage
from .models import Equipment

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
        "Cables & Connectors (1 set)"
    ]},
    {"title": "Standard Birthday Sound System", "description": "For medium birthday parties up to 100 guests.", "price": "₱5,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Birthday Sound System", "description": "For large birthday parties up to 150 guests.", "price": "₱8,000", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Wedding Sound System", "description": "For small weddings up to 100 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (1 set)"
    ]},
    {"title": "Standard Wedding Sound System", "description": "For medium weddings up to 200 guests.", "price": "₱10,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "2 Subwoofers",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Wedding Sound System", "description": "For large weddings up to 500 guests.", "price": "₱15,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Corporate Event Sound System", "description": "For corporate events up to 50 guests.", "price": "₱4,000", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Corporate Event Sound System", "description": "For corporate events up to 150 guests.", "price": "₱6,500", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Corporate Event Sound System", "description": "For corporate events up to 300 guests.", "price": "₱10,500", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Concert Sound System", "description": "For small concerts up to 100 guests.", "price": "₱7,500", "equipment": [
        "4 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Standard Concert Sound System", "description": "For medium concerts up to 300 guests.", "price": "₱12,000", "equipment": [
        "6 Speakers (300-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Premium Concert Sound System", "description": "For large concerts up to 1,000 guests.", "price": "₱20,000", "equipment": [
        "8 Speakers (600-800 watts)",
        "6 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (4 sets)"
    ]},
    {"title": "Basic Seminar Sound System", "description": "For seminars up to 50 guests.", "price": "₱3,500", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Seminar Sound System", "description": "For seminars up to 150 guests.", "price": "₱5,500", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Seminar Sound System", "description": "For seminars up to 300 guests.", "price": "₱9,000", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Conference Sound System", "description": "For conferences up to 50 guests.", "price": "₱4,000", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Conference Sound System", "description": "For conferences up to 200 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Conference Sound System", "description": "For conferences up to 500 guests.", "price": "₱12,500", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Graduation Sound System", "description": "For small graduation events up to 100 guests.", "price": "₱6,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Standard Graduation Sound System", "description": "For medium graduation events up to 200 guests.", "price": "₱9,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "2 Subwoofers",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Graduation Sound System", "description": "For large graduation events up to 500 guests.", "price": "₱14,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "4 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Awarding Ceremony Sound System", "description": "For small awarding ceremonies up to 50 guests.", "price": "₱4,500", "equipment": [
        "2 Speakers (50-100 watts)",
        "1 Wired Microphone",
        "Mixer Console (2 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Awarding Ceremony Sound System", "description": "For medium awarding ceremonies up to 150 guests.", "price": "₱7,000", "equipment": [
        "4 Speakers (100-300 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Awarding Ceremony Sound System", "description": "For large awarding ceremonies up to 500 guests.", "price": "₱12,000", "equipment": [
        "6 Speakers (300-500 watts)",
        "3 Wireless Microphones",
        "Mixer Console with Effects (6 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Fundraising Event Sound System", "description": "For small fundraising events up to 100 guests.", "price": "₱6,000", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Fundraising Event Sound System", "description": "For medium fundraising events up to 200 guests.", "price": "₱9,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Fundraising Event Sound System", "description": "For large fundraising events up to 500 guests.", "price": "₱14,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Fashion Show Sound System", "description": "For small fashion shows up to 100 guests.", "price": "₱5,000", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (1 set)"
    ]},
    {"title": "Standard Fashion Show Sound System", "description": "For medium fashion shows up to 200 guests.", "price": "₱8,000", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "Subwoofer",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Fashion Show Sound System", "description": "For large fashion shows up to 500 guests.", "price": "₱12,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Church Service Sound System", "description": "For small church services up to 100 guests.", "price": "₱4,500", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard Church Service Sound System", "description": "For medium church services up to 200 guests.", "price": "₱7,500", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium Church Service Sound System", "description": "For large church services up to 500 guests.", "price": "₱11,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic School Play Sound System", "description": "For small school plays up to 100 guests.", "price": "₱5,000", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing"
    ]},
    {"title": "Standard School Play Sound System", "description": "For medium school plays up to 200 guests.", "price": "₱8,500", "equipment": [
        "6 Speakers (200-400 watts)",
        "3 Wireless Microphones",
        "Mixer Console (6 channels)",
        "Subwoofer",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]},
    {"title": "Premium School Play Sound System", "description": "For large school plays up to 500 guests.", "price": "₱13,000", "equipment": [
        "8 Speakers (400-600 watts)",
        "4 Wireless Microphones",
        "Mixer Console with Effects (8 channels)",
        "2 Subwoofers",
        "Stage Monitors",
        "Sound System Setup & Testing",
        "Cables & Connectors (3 sets)"
    ]},
    {"title": "Basic Charity Event Sound System", "description": "For small charity events up to 100 guests.", "price": "₱5,500", "equipment": [
        "4 Speakers (100-200 watts)",
        "2 Wireless Microphones",
        "Mixer Console (4 channels)",
        "Cables & Connectors (1 set)",
        "Sound System Setup & Testing",
        "Cables & Connectors (2 sets)"
    ]}
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

@login_required
def profile(request):
    if request.method == "POST":
        user = request.user
        
        # Update basic user info
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        # Update profile picture if one is uploaded
        profile = user.profile
        profile.contact_number = request.POST.get('phone')
        profile.province = request.POST.get('province')
        profile.city = request.POST.get('city')
        profile.address = request.POST.get('address')

        if 'profile_picture' in request.FILES:  # Check if the profile picture is part of the request
            profile.profile_picture = request.FILES['profile_picture']

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
            'id': booking.id,  # Make sure booking.id is included here
            'customer_name': booking.full_name,
            'date_booked': booking.created_at.strftime('%B %d, %Y'),
            'package': booking.package.title,
            'event_date': booking.event_date.strftime('%B %d, %Y'),
            'total': booking.price,
            'rating': '⭐ Rate' if booking.status == 'Completed' else 'N/A'  # Placeholder for rating system
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
        fulladdress = request.POST.get("fulladdress")
        audience_size = request.POST.get("audience_size")

        try:
            package = ServicePackage.objects.get(title=selected_package)
        except ServicePackage.DoesNotExist:
            messages.error(request, f"The selected package '{selected_package}' does not exist.")
            return redirect('services')

        # Check bookings count only for ACCEPTED bookings
        accepted_bookings_count = Booking.objects.filter(
            event_date=event_date,
            status='Accepted'  # Only count accepted bookings
        ).count()

        if accepted_bookings_count >= 2:
            messages.error(request, "This date already has two accepted bookings. Please select another date.")
            return redirect('services')

        event_time_obj = datetime.strptime(event_time, "%H:%M")
        end_time_obj = event_time_obj + timedelta(hours=4)
        end_time = end_time_obj.time()

        Booking.objects.create(
            user=request.user,
            package=package,
            full_name=full_name,
            email=email,
            contact_number=contact_number,
            event_date=event_date,
            event_time=event_time,
            end_time=end_time,
            event_type=event_type,
            location=location,
            fulladdress=fulladdress,
            audience_size=audience_size,
            price=package.price,
            status='Processing'  # Default status, not accepted yet
        )

        messages.success(request, f"Your booking for {selected_package} has been successfully created!")
        return redirect("mybookings")

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

@login_required
def booking_events_api(request):
    # Only include accepted bookings to block dates/times
    accepted_statuses = ['Accepted']
    bookings = Booking.objects.filter(status__in=accepted_statuses)

    events = []
    for booking in bookings:
        events.append({
            "date": booking.event_date.strftime("%Y-%m-%d"),
            "type": booking.event_type,
            "time": booking.event_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M") if booking.end_time else None
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
    equipment_list = Equipment.objects.all()
    return render(request, 'client/equipment.html', {'equipment_list': equipment_list})

@login_required
@admin_only
def tracking(request):
    # Filter bookings with 'Approved' status, exclude 'Completed'
    bookings = Booking.objects.filter(status='Accepted')  # Only show approved bookings

    return render(request, 'client/tracking.html', {'bookings': bookings})

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
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'client/view_booking.html', {'booking': booking})

@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Update booking status to 'Accepted'
    booking.status = 'Accepted'
    booking.save()

    # Get the equipment associated with the booked service package
    package = booking.package
    inventory_updated = True  # Flag to check if inventory updates are successful

    # Loop through all the equipment in the package
    for package_equipment in package.packageequipment_set.all():
        equipment = package_equipment.equipment
        quantity_required = package_equipment.quantity_required

        # Check if there is enough stock available
        if equipment.quantity_available < quantity_required:
            messages.error(request, f"Not enough stock for {equipment.name}. Booking cannot be processed.")
            inventory_updated = False
            break  # Stop checking further if one equipment is unavailable

        # Deduct the available stock and update the rented quantity
        equipment.update_quantity(quantity_required)  # This will update the stock

    if inventory_updated:
        # Add the event to the calendar (this part updates the event in the calendar)
        events = {
            "date": booking.event_date.strftime("%Y-%m-%d"),
            "type": booking.event_type,
            "time": booking.event_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M") if booking.end_time else None
        }
        messages.success(request, f"Booking {booking.id} has been successfully accepted and inventory updated.")
    else:
        booking.status = 'Processing'
        booking.save()

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


def complete_booking(request, id):
    # Get the booking object by ID
    booking = get_object_or_404(Booking, id=id)

    # Ensure the booking is either 'Accepted' or 'Processing' before completing it
    if booking.status in ['Accepted', 'Processing']:
        # Mark the booking as 'Completed'
        booking.status = 'Completed'
        booking.save()

        # Loop through the equipment in the booking and restore it to the inventory
        for package_equipment in booking.package.packageequipment_set.all():
            equipment = package_equipment.equipment
            quantity_rented = package_equipment.quantity_required  # Quantity rented for the package

            # Update the equipment inventory
            equipment.quantity_available += quantity_rented
            equipment.quantity_rented -= quantity_rented
            equipment.save()

            print(f"Returned {quantity_rented} of {equipment.name} to inventory. Available: {equipment.quantity_available}, Rented: {equipment.quantity_rented}")

    # Redirect to the bookings page after completing the booking
    return redirect('booking')  # Or another appropriate page