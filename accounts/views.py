from django.contrib.auth.decorators import login_required, user_passes_test
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
from .models import Review
from django.db.models import Avg
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db.models.functions import TruncMonth
from django.utils.dateformat import DateFormat
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import re
from accounts.models import Profile
from django.db.models import Q
from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from .models import Booking, Notification
from .models import BookingChecklist, ChecklistItem
from .models import ContactMessage
from .forms import ServicePackageForm

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
    from .models import ServicePackage, Profile

    # Kunin lahat ng packages sa database
    packages = ServicePackage.objects.all()

    # Kunin user profile para ma-auto populate
    profile = None
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None

    return render(request, 'accounts/services.html', {
        'packages': packages,
        'profile': profile
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
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Save to DB
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Send email to admin
        send_mail(
            subject=f"New Inquiry: {subject}",
            message=f"From: {name} <{email}>\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # admin email
            fail_silently=False,
        )

        # Flash message
        messages.success(request, "✅ Your message has been sent successfully!")
        return redirect("contactus")  # dapat tugma ito sa urls.py name="contactus"

    # GET request → render template
    return render(request, "accounts/contactus.html")
@login_required
def profile(request):
    user = request.user

    # Try to get or create Profile for this user, avoid RelatedObjectDoesNotExist
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        # update user and profile as usual, for example:
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.contact_number = request.POST.get('phone', profile.contact_number)
        profile.province = request.POST.get('province', profile.province)
        profile.city = request.POST.get('city', profile.city)
        profile.address = request.POST.get('address', profile.address)

        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    context = {
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)

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
    bookings = Booking.objects.filter(user=request.user).exclude(status='Processing').order_by('-created_at')

    history_list = []
    for booking in bookings:
        history_list.append({
            'id': booking.id,
            'customer_name': booking.full_name,
            'date_booked': booking.created_at.strftime('%B %d, %Y'),
            'package': booking.package.title,
            'event_date': booking.event_date.strftime('%B %d, %Y'),
            'total': booking.price,
            'rating': booking.rating if hasattr(booking, 'rating') else '',  # Assume you have rating field or adjust accordingly
            'status': booking.status,
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
        end_time = request.POST.get("end_time")  # ✅ now we take it from the form
        event_type = request.POST.get("event_type")
        location = request.POST.get("location")
        fulladdress = request.POST.get("fulladdress")
        audience_size = request.POST.get("audience_size")

        try:
            package = ServicePackage.objects.get(title=selected_package)
        except ServicePackage.DoesNotExist:
            messages.error(request, f"The selected package '{selected_package}' does not exist.")
            return redirect('services')

        accepted_bookings_count = Booking.objects.filter(
            event_date=event_date,
            status='Accepted'
        ).count()

        if accepted_bookings_count >= 2:
            messages.error(request, "This date already has two accepted bookings. Please select another date.")
            return redirect('services')

        # Parse event_time and end_time as time objects
        event_time_obj = datetime.strptime(event_time, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M").time()

        Booking.objects.create(
            user=request.user,
            package=package,
            full_name=full_name,
            email=email,
            contact_number=contact_number,
            event_date=event_date,
            event_time=event_time_obj,
            end_time=end_time_obj,
            event_type=event_type,
            location=location,
            fulladdress=fulladdress,
            audience_size=audience_size,
            price=package.price,
            status='Processing'
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
    profit = revenue * 0.5  # Adjust this formula if needed

    # Chart.js monthly data
    raw_monthly = bookings.annotate(
        month=TruncMonth('event_date')
    ).values('month').annotate(count=Count('id')).order_by('month')

    bookings_per_month = [
        {
            "month": DateFormat(entry["month"]).format("Y-m"),
            "count": entry["count"]
        }
        for entry in raw_monthly
    ]

    # Notifications
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    event_type_data = bookings.values('event_type').annotate(count=Count('id'))
    package_popularity = bookings.values('package__title').annotate(count=Count('id')).order_by('-count')
    status_data = bookings.values('status').annotate(count=Count('id'))

    # === Feedback Aggregation ===
    reviews = Review.objects.all()
    avg_quality = reviews.aggregate(avg=Avg('quality'))['avg'] or 0
    avg_timeliness = reviews.aggregate(avg=Avg('timeliness'))['avg'] or 0
    avg_professionalism = reviews.aggregate(avg=Avg('professionalism'))['avg'] or 0
    avg_value_for_money = reviews.aggregate(avg=Avg('value_for_money'))['avg'] or 0
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0  # <- use 'rating' field

    return render(request, 'client/dashboard.html', {
        'booking_count': booking_count,
        'revenue': revenue,
        'profit': profit,
        'pending_count': pending_count,

        'bookings_per_month': bookings_per_month,
        'event_type_data': list(event_type_data),
        'package_popularity': list(package_popularity),
        'status_data': list(status_data),

        'notifications': notifications,

        # Feedback context
        'reviews': reviews,
        'avg_quality': round(avg_quality, 1),
        'avg_timeliness': round(avg_timeliness, 1),
        'avg_professionalism': round(avg_professionalism, 1),
        'avg_value_for_money': round(avg_value_for_money, 1),
        'average_rating': round(average_rating, 1),
    })
@login_required
@admin_only
def booking(request):
    current_year = datetime.now().year

    # Dropdown options
    months = [
        ("1", "January"), ("2", "February"), ("3", "March"), ("4", "April"),
        ("5", "May"), ("6", "June"), ("7", "July"), ("8", "August"),
        ("9", "September"), ("10", "October"), ("11", "November"), ("12", "December"),
    ]
    years = list(range(2000, current_year + 1))
    days = list(range(1, 32))  # 1 to 31

    # Get filters
    filter_day = request.GET.get('filter_day')
    filter_month = request.GET.get('filter_month')
    filter_year = request.GET.get('filter_year')

    filter_conditions = Q()

    # If filter is "today"
    if filter_day == "today":
        filter_conditions &= Q(event_date=datetime.now().date())
    else:
        # Try converting day to int if it's numeric
        day_number = int(filter_day) if filter_day and filter_day.isdigit() else None
        month_number = int(filter_month) if filter_month and filter_month.isdigit() else None
        year_number = int(filter_year) if filter_year and filter_year.isdigit() else None

        # If full date (day + month + year) is selected
        if day_number and month_number and year_number:
            filter_conditions &= Q(
                event_date__day=day_number,
                event_date__month=month_number,
                event_date__year=year_number
            )
        elif month_number and year_number:
            filter_conditions &= Q(
                event_date__month=month_number,
                event_date__year=year_number
            )
        elif month_number:
            filter_conditions &= Q(event_date__month=month_number)
        elif year_number:
            filter_conditions &= Q(event_date__year=year_number)

    bookings = Booking.objects.filter(filter_conditions).order_by('-created_at')

    # Notifications (show up to 5 newest "Processing" bookings)
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    context = {
        'bookings': bookings,
        'months': months,
        'years': years,
        'days': days,
        'current_year': current_year,
        'notifications': notifications,  # Pass notifications to the template
    }

    return render(request, 'client/booking.html', context)

@login_required
@admin_only
def event(request):
    # Get all bookings with "Processing" status
    bookings = Booking.objects.all()

    # Notifications (show up to 5 newest "Processing" bookings)
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    return render(request, 'client/event.html', {
        'notifications': notifications,  # Pass notifications to the template
    })

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

@csrf_exempt
def chatbot_api(request):
    if request.method == "GET":
        message = request.GET.get("message", "").lower()

        # Regex para mahanap ang date (YYYY-MM-DD)
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", message)

        if date_match:
            try:
                # Kunin yung date mula sa message
                event_date = datetime.strptime(date_match.group(), "%Y-%m-%d").date()

                # Bilangin ilan na yung accepted bookings sa araw na yun
                bookings_count = Booking.objects.filter(
                    event_date=event_date, 
                    status="Accepted"
                ).count()

                if bookings_count >= 2:
                    response = f"Pasensya na, puno na ang {event_date} para sa booking."
                else:
                    response = f"Oo, available pa ang {event_date} para sa booking."

            except ValueError:
                response = "Pakispecify ng tamang date (format: YYYY-MM-DD)."
        else:
            response = "Pakiulit, anong date po ang gusto ninyong i-check? (format: YYYY-MM-DD)"

        return JsonResponse({"response": response})

    return JsonResponse({"response": "Only GET method is allowed"})


@login_required
@admin_only
def equipment(request):
    show = request.GET.get('show', 'all')
    q = request.GET.get('q', '').strip()

    # base queryset
    qs = Equipment.objects.all()

    # Search filter
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(condition__icontains=q) |
            Q(current_location__icontains=q)
        )

    # Tabs filter
    if show == 'maintenance':
        qs = qs.filter(qty_maintenance__gt=0)
    elif show == 'repair':
        qs = qs.filter(qty_repair__gt=0)
    elif show == 'available':
        qs = qs.filter(quantity_available__gt=0)
    elif show == 'rented':
        qs = qs.filter(quantity_rented__gt=0)
    # else 'all' → no extra filter

    # Notifications (up to 5 newest "Processing")
    bookings = Booking.objects.all()
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    # Badge counts (total inventory, not affected by search)
    counts = {
        'all': Equipment.objects.count(),
        'available': Equipment.objects.filter(quantity_available__gt=0).count(),
        'rented': Equipment.objects.filter(quantity_rented__gt=0).count(),
        'maintenance': Equipment.objects.filter(qty_maintenance__gt=0).count(),
        'repair': Equipment.objects.filter(qty_repair__gt=0).count(),
    }

    return render(request, 'client/equipment.html', {
        'equipment_list': qs,
        'notifications': notifications,
        'show': show,      # for active tab in template
        'counts': counts,  # for badges
    })
@login_required
@admin_only
def tracking(request):
    # Filter bookings with 'Approved' status, exclude 'Completed'
    bookings = Booking.objects.filter(status='Accepted')

    # Notifications (show up to 5 newest "Processing" bookings)
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    return render(request, 'client/tracking.html', {
        'bookings': bookings,
        'notifications': notifications,  # Pass notifications to the template
    })

@login_required
@admin_only
def reviews(request):
    current_year = datetime.now().year  # Get the current year

    # List of days (1-31), months (1-12), and years (2000-current year)
    days = list(range(1, 32))
    months = [
        ("1", "January"), ("2", "February"), ("3", "March"), ("4", "April"),
        ("5", "May"), ("6", "June"), ("7", "July"), ("8", "August"),
        ("9", "September"), ("10", "October"), ("11", "November"), ("12", "December"),
    ]
    years = list(range(2000, current_year + 1))

    # Get the filter values from the GET request
    filter_day = request.GET.get('filter_day')
    filter_month = request.GET.get('filter_month')
    filter_year = request.GET.get('filter_year')

    filter_conditions = Q()

    # Apply filters based on selected day, month, and year
    if filter_day and filter_month and filter_year:
        filter_date = datetime.strptime(f'{filter_year}-{filter_month}-{filter_day}', '%Y-%m-%d')
        filter_conditions &= Q(booking_date=filter_date.date())

    elif filter_month and not filter_day:
        filter_conditions &= Q(booking_date__month=int(filter_month))

    elif filter_year and not filter_month:
        filter_conditions &= Q(booking_date__year=int(filter_year))

    reviews = Review.objects.filter(filter_conditions).order_by('-created_at')

    # Calculate average ratings for reviews
    averages = reviews.aggregate(
        average_rating=Avg('rating'),
        avg_quality=Avg(Coalesce('quality', 0)),
        avg_timeliness=Avg(Coalesce('timeliness', 0)),
        avg_professionalism=Avg(Coalesce('professionalism', 0)),
        avg_value_for_money=Avg(Coalesce('value_for_money', 0))
    )

    # Notifications (show up to 5 newest "Processing" bookings)
    bookings = Booking.objects.all()
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    # Rating distribution
    rating_distribution = {
        'quality': {i: reviews.filter(quality=i).count() for i in range(1, 6)},
        'timeliness': {i: reviews.filter(timeliness=i).count() for i in range(1, 6)},
        'professionalism': {i: reviews.filter(professionalism=i).count() for i in range(1, 6)},
        'value_for_money': {i: reviews.filter(value_for_money=i).count() for i in range(1, 6)}
    }

    context = {
        'reviews': reviews,
        'average_rating': round(averages['average_rating'] if averages['average_rating'] is not None else 0, 1),
        'avg_quality': round(averages['avg_quality'] if averages['avg_quality'] is not None else 0, 1),
        'avg_timeliness': round(averages['avg_timeliness'] if averages['avg_timeliness'] is not None else 0, 1),
        'avg_professionalism': round(averages['avg_professionalism'] if averages['avg_professionalism'] is not None else 0, 1),
        'avg_value_for_money': round(averages['avg_value_for_money'] if averages['avg_value_for_money'] is not None else 0, 1),
        'rating_distribution': rating_distribution,
        'current_year': current_year,
        'days': days,
        'months': months,
        'years': years,
        'notifications': notifications,  # Pass notifications to the template
    }

    return render(request, 'client/reviews.html', context)
@login_required
@admin_only
def customer(request):
    # Retrieve all users and their associated profile data
    users = User.objects.filter(is_staff=False)  # Exclude admin users (is_staff=False)
    customer_data = []

    for user in users:
        try:
            profile = Profile.objects.get(user=user)  # One-to-One relation with Profile
            customer_data.append({
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": profile.contact_number,
                "address": profile.address,
                "province": profile.province,
                "city": profile.city,
                "profile_picture": profile.profile_picture.url if profile.profile_picture else None,  # Handle profile picture if exists
            })
        except Profile.DoesNotExist:
            # If the profile is missing (for any reason), handle it gracefully
            customer_data.append({
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": None,
                "address": None,
                "province": None,
                "city": None,
                "profile_picture": None,
            })

    # Notifications (show up to 5 newest "Processing" bookings)
    bookings = Booking.objects.all()
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    return render(request, 'client/customer.html', {
        'customer_data': customer_data,
        'notifications': notifications,  # Pass notifications to the template
    })

@login_required
@admin_only
def employee(request):
    # Get only users who are current admins (is_staff=True)
    employees = Profile.objects.filter(user__is_staff=True)  # Only current admins

    # Notifications (show up to 5 newest "Processing" bookings)
    bookings = Booking.objects.all()
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    return render(request, 'client/employee.html', {
        'employees': employees,
        'notifications': notifications,  # Pass notifications to the template
    })

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
        # ✅ Create checklist for the booking if it doesn’t exist
        from .models import BookingChecklist, ChecklistItem  # import inside to avoid circular issues
        checklist, created = BookingChecklist.objects.get_or_create(booking=booking)

        if created:
            for pkg_eq in booking.package.packageequipment_set.all():
                ChecklistItem.objects.create(
                    checklist=checklist,
                    equipment=pkg_eq.equipment,
                    quantity_required=pkg_eq.quantity_required
                )

        # Add the event to the calendar (this part updates the event in the calendar)
        events = {
            "date": booking.event_date.strftime("%Y-%m-%d"),
            "type": booking.event_type,
            "time": booking.event_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M") if booking.end_time else None
        }

        # ✅ Create notification for customer
        Notification.objects.create(
            user=booking.user,
            message=f"Your booking #{booking.id} has been accepted!"
        )

        messages.success(request, f"Booking {booking.id} has been successfully accepted, inventory updated, and checklist created.")
    else:
        booking.status = 'Processing'
        booking.save()

    return redirect('booking')


@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    reason = request.POST.get("reason") or request.GET.get("reason") or "No reason provided"
    
    # Update status to rejected
    booking.status = 'Rejected'
    booking.reject_reason = reason
    booking.save()

    # ✅ Create notification for the customer
    Notification.objects.create(
        user=booking.user,
        message=f"Your booking #{booking.id} has been rejected. Reason: {reason}"
    )

    messages.success(request, f"Booking {booking.id} has been rejected.")
    return redirect('booking') 

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

@login_required
def complete_booking(request, id):
    booking = get_object_or_404(Booking, id=id)

    if booking.status in ['Accepted', 'Processing']:
        booking.status = 'Completed'
        booking.save()

        for package_equipment in booking.package.packageequipment_set.all():
            equipment = package_equipment.equipment
            quantity_rented = package_equipment.quantity_required  

            equipment.quantity_available += quantity_rented
            equipment.quantity_rented -= quantity_rented
            equipment.save()

            print(f"Returned {quantity_rented} of {equipment.name} to inventory. Available: {equipment.quantity_available}, Rented: {equipment.quantity_rented}")
    return redirect('booking')  

@login_required
@csrf_protect
def submit_review(request):
    if request.method == 'POST':
        booking_id = request.POST.get('bookingId')
        rating = request.POST.get('rating')
        quality = request.POST.get('quality')
        timeliness = request.POST.get('timeliness')
        professionalism = request.POST.get('professionalism')
        value_for_money = request.POST.get('value_for_money')
        comment = request.POST.get('comment', '').strip()

        # ✅ Check required fields
        if not booking_id or not rating or not quality or not timeliness or not professionalism or not value_for_money or not comment:
            messages.error(request, "All fields are required!")
            return redirect('history')

        # ✅ Get booking, must belong to current user
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        # ✅ Only completed bookings can be reviewed
        if booking.status != 'Completed':
            messages.error(request, "You can only review completed bookings.")
            return redirect('history')

        # ✅ Validate numeric inputs (1–5)
        try:
            rating = int(rating)
            quality = int(quality)
            timeliness = int(timeliness)
            professionalism = int(professionalism)
            value_for_money = int(value_for_money)

            for score in [rating, quality, timeliness, professionalism, value_for_money]:
                if score < 1 or score > 5:
                    raise ValueError
        except ValueError:
            messages.error(request, "All ratings must be numbers between 1 and 5.")
            return redirect('history')

        # ✅ Prevent duplicate review
        if Review.objects.filter(booking=booking).exists():
            messages.error(request, "You have already submitted a review for this booking.")
            return redirect('history')

        # ✅ Create review
        Review.objects.create(
            booking=booking,
            customer_name=booking.full_name if hasattr(booking, "full_name") else request.user.username,
            booking_date=booking.event_date,   # adjust kung ibang field
            event_type=booking.event_type,
            rating=rating,
            quality=quality,
            timeliness=timeliness,
            professionalism=professionalism,
            value_for_money=value_for_money,
            comment=comment
        )

        messages.success(request, "Thank you for your detailed review!")
        return redirect('history')

    return redirect('home')
@login_required
@admin_only
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    review.delete()
    
    return redirect('reviews')  

def delete_booking(request, id):
    booking = get_object_or_404(Booking, id=id)
    booking.delete()
    return redirect('booking')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_requests_view(request):
    # Lahat ng users na may "staff" sa username pero hindi pa admin
    requested_profiles = Profile.objects.filter(
        user__username__icontains="staff",
        user__is_staff=False
    )

    return render(request, 'client/admin_request.html', {
        'requested_profiles': requested_profiles
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        # Gawing admin/staff
        user.is_staff = True
        user.save()

        # Optional: linisin yung requested_admin flag kung meron
        if hasattr(user, "profile"):
            user.profile.requested_admin = False
            user.profile.save()

        messages.success(request, f"✅ {user.username} has been approved as an admin.")

    return redirect('admin_requests_view')
@login_required
def update_profile(request):
    user = request.user
    profile = user.profile  # may OneToOne relation ka kaya safe ito

    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)

        # Update profile fields
        profile.contact_number = request.POST.get('phone', profile.contact_number)
        profile.address = request.POST.get('address', profile.address)

        # Upload new profile picture (kung meron)
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        # Save both
        user.save()
        profile.save()

        messages.success(request, "✅ Profile updated successfully!")
        return redirect('profile')  # redirect to profile page

    # render profile update page
    return render(request, 'accounts/profile.html', {
        'user': user,
        'profile': profile
    })


@login_required
def dashboard_redirect(request):
    # Check if the logged-in user is an admin or regular user
    profile = Profile.objects.get(user=request.user)
    
    if profile.requested_admin:  # If requested_admin is True
        return redirect('employee')  # Redirect to the employee dashboard
    else:
        return redirect('customer')  # Redirect to the customer dashboard
    

@login_required
def update_inventory(request, equipment_id):
    if request.method != 'POST':
        return HttpResponse("Invalid request.", status=400)

    equipment = get_object_or_404(Equipment, id=equipment_id)
    action = request.POST.get('action', '').strip()
    qty_str = request.POST.get('qty', '1')

    try:
        qty = max(1, int(qty_str))
    except ValueError:
        qty = 1

    try:
        if action == 'add_stock':
            # simple add to available
            equipment.quantity_available += qty
            equipment.status = 'Available'
            equipment.save()
            messages.success(request, f"Added {qty} to {equipment.name} stock.")

        elif action == 'subtract_stock':
            if equipment.quantity_available < qty:
                return HttpResponse("Insufficient stock to subtract.", status=400)
            equipment.quantity_available -= qty
            # huwag gawing negative ang available
            if equipment.quantity_available <= 0 and equipment.quantity_rented <= 0:
                equipment.status = 'Under Maintenance' if equipment.qty_maintenance > 0 else 'Available'
            equipment.save()
            messages.success(request, f"Subtracted {qty} from {equipment.name} stock.")

        elif action == 'to_maintenance':
            equipment.move_to_maintenance(qty)
            messages.success(request, f"Moved {qty} of {equipment.name} to maintenance.")

        elif action == 'back_from_maintenance':
            equipment.return_from_maintenance(qty)
            messages.success(request, f"Returned {qty} of {equipment.name} from maintenance to available.")

        elif action == 'to_repair':
            equipment.move_to_repair(qty)
            messages.success(request, f"Moved {qty} of {equipment.name} to repair.")

        elif action == 'back_from_repair':
            equipment.return_from_repair(qty)
            messages.success(request, f"Returned {qty} of {equipment.name} from repair to available.")

        elif action == 'rent_out':
            # optional kung gusto mong may rent button sa table
            equipment.update_quantity(qty)
            messages.success(request, f"Rented out {qty} of {equipment.name}.")

        elif action == 'return_rental':
            equipment.return_stock(qty)
            messages.success(request, f"Returned {qty} of {equipment.name} (rental).")

        else:
            return HttpResponse("Unknown action.", status=400)

    except ValueError as e:
        # galing sa helper methods mo kapag kulang stock
        return HttpResponse(str(e), status=400)

    return redirect('inventory_list')

from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404

@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    reason = request.POST.get("reason", "").strip()
    booking.status = "Cancelled"
    booking.cancel_reason = reason
    booking.save()

    # Add Django success message
    messages.success(request, f"Booking #{booking.id} has been cancelled successfully.")
    return redirect("mybookings")

@login_required
@admin_only
def checklist_view(request):
    bookings = Booking.objects.filter(status="Accepted").select_related("checklist")
    return render(request, "client/checklist.html", {"bookings": bookings})


@login_required
@admin_only
def checklist_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    checklist, created = BookingChecklist.objects.get_or_create(booking=booking)

    # kung bagong gawa yung checklist, kailangan din natin i-populate ng equipment
    if created:
        for pkg_eq in booking.package.packageequipment_set.all():
            ChecklistItem.objects.create(
                checklist=checklist,
                equipment=pkg_eq.equipment,
                quantity_required=pkg_eq.quantity_required
            )

    if request.method == "POST":
        all_confirmed = True
        for item in checklist.items.all():
            received_qty = int(request.POST.get(f"received_{item.id}", item.quantity_received))
            confirmed = f"confirm_{item.id}" in request.POST

            item.quantity_received = received_qty
            item.confirmed = confirmed
            item.save()

            if not confirmed or received_qty < item.quantity_required:
                all_confirmed = False

        checklist.is_confirmed = all_confirmed
        checklist.save()

        messages.success(request, "Checklist updated successfully!")
        return redirect("checklist_detail", booking_id=booking.id)

    return render(request, "client/checklist_detail.html", {"booking": booking, "checklist": checklist})

import csv
def download_employees(request):
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    # CSV header
    writer.writerow(['Username', 'First Name', 'Last Name', 'Email', 'Phone', 'Address', 'Province', 'City'])

    employees = Profile.objects.all()  # Or filter if needed
    for emp in employees:
        writer.writerow([
            emp.user.username,
            emp.user.first_name,
            emp.user.last_name,
            emp.user.email,
            emp.contact_number,
            emp.address,
            emp.province,
            emp.city
        ])

    return response

def mark_notifications_as_read(request):
    if request.user.is_authenticated:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "unauthorized"}, status=401)

# READ - List of packages in dashboard
def package_list_view(request):
    packages = ServicePackage.objects.all()
    return render(request, 'client/package_list.html', {'packages': packages})

# CREATE - Add new package
def package_add_view(request):
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "New package added successfully!")
            return redirect('package_list')
    else:
        form = ServicePackageForm()
    return render(request, 'client/package_add.html', {'form': form})

# UPDATE - Edit package
def package_edit_view(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, "Package updated successfully!")
            return redirect('package_list')
    else:
        form = ServicePackageForm(instance=package)
    return render(request, 'client/package_edit.html', {'form': form, 'package': package})

# DELETE - Delete package
def package_delete_view(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id)
    if request.method == 'POST':
        package.delete()
        messages.success(request, "Package deleted successfully!")
        return redirect('package_list')
    return render(request, 'client/package_delete.html', {'package': package})

