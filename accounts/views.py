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
from django.utils import timezone, dateformat
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
from .models import ContactMessage, PackageEquipment
from .forms import ServicePackageForm
from collections import defaultdict
from datetime import timezone as dt_timezone
import calendar
import random
from .forms import ServicePackageForm,EquipmentQuantityForm
from django.forms import inlineformset_factory

# Temporary storage for OTP (use session)
OTP_EXPIRY = 300  # 5 minutes


def send_otp_email(request, email):
    otp = random.randint(100000, 999999)
    request.session['otp'] = str(otp)
    request.session['otp_email'] = email
    request.session['otp_time'] = request.timestamp if hasattr(request, 'timestamp') else None

    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP code is: {otp}",
        from_email=None,  # uses DEFAULT_FROM_EMAIL from settings
        recipient_list=[email],
        fail_silently=False,
    )


def register_view(request):
    if request.method == "POST":
        step = request.POST.get("step", "email")  # default first step: enter email

        if step == "email":
            email = request.POST.get("email")
            if not email:
                messages.error(request, "Please enter your email to receive OTP.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already in use.")
            else:
                send_otp_email(request, email)
                messages.success(request, f"OTP sent to {email}. Please check your inbox.")
                request.session["otp_email"] = email
                return render(request, "accounts/register.html", {
                    "step": "otp",
                    "email": email,
                    "hide_footer": True
                })

        elif step == "otp":
            email = request.POST.get("email")
            entered_otp = request.POST.get("otp")
            session_otp = request.session.get("otp")
            session_email = request.session.get("otp_email")

            if entered_otp == session_otp and email == session_email:
                messages.success(request, "OTP verified! Continue registration.")
                return render(request, "accounts/register.html", {
                    "step": "register",
                    "email": email,
                    "hide_footer": True
                })
            else:
                messages.error(request, "Invalid OTP. Try again.")
                return render(request, "accounts/register.html", {
                    "step": "otp",
                    "email": email,
                    "hide_footer": True
                })

        elif step == "register":
            # Proceed with full registration
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
            barangay = request.POST.get("barangay")

            # Validation
            if not username:
                messages.error(request, "Username is required.")
            elif not password or not confirm_password:
                messages.error(request, "Password and confirmation are required.")
            elif password != confirm_password:
                messages.error(request, "Passwords do not match.")
            elif User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
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
                    city=city,
                    barangay=barangay
                )

                # Clear OTP from session
                request.session.pop("otp", None)
                request.session.pop("otp_email", None)

                messages.success(request, "Registration successful. You can now log in.")
                return redirect("login")

    else:
        step = "email"

    return render(request, "accounts/register.html", {
        "step": step,
        "hide_footer": True
    })


# Temporary storage for OTPs (use DB or cache in production)
otp_storage = {}

def login_view(request):
    step = request.POST.get("step", "initial")
    email = request.POST.get("email", "")
    password = request.POST.get("password", "")

    if request.method == "POST":
        action = request.POST.get("action")

        # ---------- STEP 1: SEND OTP ----------
        if action == "send_otp":
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

            if user:
                # Generate OTP for ALL users (admin, staff, normal)
                otp = str(random.randint(100000, 999999))
                otp_storage[email] = otp

                send_mail(
                    subject="Your Login OTP",
                    message=f"Your OTP is: {otp}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )

                messages.success(request, f"✅ OTP sent to {email}. Please enter it below.")
                return render(request, "accounts/login.html", {
                    "step": "otp",
                    "email": email,
                    "password": password,
                    "hide_footer": True
                })

            else:
                messages.error(request, "❌ Invalid email or password.")

        # ---------- STEP 2: VERIFY OTP ----------
        elif action == "verify_otp":
            otp_input = request.POST.get("otp")

            if otp_input == otp_storage.get(email):
                # OTP correct
                try:
                    user_obj = User.objects.get(email=email)
                    user = authenticate(request, username=user_obj.username, password=password)

                    if user:
                        login(request, user)

                        # Remove OTP after success
                        otp_storage.pop(email, None)

                        messages.success(request, f"✅ Login successful. Welcome, {user.username}!")

                        # Redirect admin/staff to dashboard
                        if user.is_superuser or user.is_staff:
                            return redirect("dashboard")

                        # Redirect normal user to home
                        return redirect("home")

                    else:
                        messages.error(request, "❌ Authentication failed.")
                except User.DoesNotExist:
                    messages.error(request, "❌ User not found.")
            else:
                messages.error(request, "❌ Invalid OTP.")
                return render(request, "accounts/login.html", {
                    "step": "otp",
                    "email": email,
                    "password": password,
                    "hide_footer": True
                })

    # ---------- DEFAULT: SHOW INITIAL FORM ----------
    return render(request, "accounts/login.html", {
        "step": "initial",
        "email": email,
        "password": password,
        "hide_footer": True
    })

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# Home Page
def home(request):
    return render(request, "accounts/home.html")

def services_view(request):
    selected_event = request.GET.get('event_type')

    packages = ServicePackage.objects.annotate(
        avg_rating=Avg('booking__review__rating'),
        review_count=Count('booking__review')
    )

    # Filter based on keyword matching inside package.title
    if selected_event and selected_event != "":
        packages = packages.filter(title__icontains=selected_event)

    profile = None
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None

    event_choices = [
        "Wedding", "Birthday", "Corporate", "Concert", "Seminar",
        "Graduation", "Awarding Ceremony", "Fundraising", "Fashion Show",
        "Church", "Conference", "School Play", "School", "Charity Event"
    ]

    return render(request, 'accounts/services.html', {
        'packages': packages,
        'profile': profile,
        'selected_event': selected_event,
        'event_choices': event_choices,
    })

# About Us Page
def aboutus(request):
    team_members = [
        {'name': 'Alice Reyes', 'img': 'images/speaker1.png'},
        {'name': 'Bob Santos', 'img': 'images/speaker1.png'},
        {'name': 'Charlie Cruz', 'img': 'images/speaker1.png'},
    ]
    return render(request, "accounts/aboutus.html", {'team_members': team_members})

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages

def contactus(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Combine info for email body
        full_message = f"Message from {name} <{email}>:\n\n{message}"

        try:
            send_mail(
                subject,
                full_message,
                'christiangeno0107@gmail.com',  # Your Gmail (App Password) sender
                ['christiangeno0107@gmail.com'],  # Receiver email (can be same)
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
        except Exception as e:
            messages.error(request, f'Error sending message: {e}')

        # Redirect to prevent re-submitting the form on refresh
        return redirect('contactus')

    return render(request, 'accounts/contactus.html')

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
        profile.barangay = request.POST.get("barangay")

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
        barangay = request.POST.get("barangay")

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
            barangay=barangay,
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



import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone, dateformat
from datetime import datetime
from collections import defaultdict
from .models import Booking, Review  # Siguraduhing tama ang import path ng models mo
# Kung gumagamit ka ng admin_only decorator, siguraduhing naka-import din ito

@login_required
def dashboard(request):
    # ====== 1. FILTERS & DROPDOWNS ======
    selected_month = request.GET.get("month")
    selected_year = request.GET.get("year")

    months_list = [
        {"value": "01", "label": "January"}, {"value": "02", "label": "February"},
        {"value": "03", "label": "March"}, {"value": "04", "label": "April"},
        {"value": "05", "label": "May"}, {"value": "06", "label": "June"},
        {"value": "07", "label": "July"}, {"value": "08", "label": "August"},
        {"value": "09", "label": "September"}, {"value": "10", "label": "October"},
        {"value": "11", "label": "November"}, {"value": "12", "label": "December"},
    ]
    current_year = datetime.now().year
    years_list = list(range(current_year - 5, current_year + 1))

    # ====== 2. BASE QUERIES & HELPER ======
    all_bookings = Booking.objects.all()
    all_reviews = Review.objects.all()

    def parse_price(price):
        if not price: return 0.0
        try:
            return float(str(price).replace('₱', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return 0.0

    # ====== 3. BELL NOTIFICATION LOGIC (REAL-TIME FIX) ======
    notification_count = all_bookings.filter(is_seen=False).count()
    all_bookings.filter(is_seen=False).update(is_seen=True)

    # ====== 4. SUMMARY CARDS (FILTERED) ======
    filtered_bookings = all_bookings
    filtered_reviews = all_reviews

    if selected_year:
        filtered_bookings = filtered_bookings.filter(event_date__year=int(selected_year))
        filtered_reviews = filtered_reviews.filter(created_at__year=int(selected_year))
    if selected_month:
        filtered_bookings = filtered_bookings.filter(event_date__month=int(selected_month))
        filtered_reviews = filtered_reviews.filter(created_at__month=int(selected_month))

    # Bilangin ang lahat ng filtered bookings (Total Bookings card)
    booking_count = filtered_bookings.count()
    pending_count = filtered_bookings.filter(status="Processing").count()

    # ✅ UPDATE: Revenue at Profit computation (Filtered by status)
    # Dito natin sinasala na 'Accepted' at 'Completed' lang ang may presyo
    money_generating_bookings = filtered_bookings.filter(status__in=["Accepted", "Completed"])
    revenue = sum(parse_price(b.price) for b in money_generating_bookings)
    profit = revenue * 0.5 
    
    average_rating = filtered_reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # ====== 5. CHART DATA (UNFILTERED / MONTHLY BREAKDOWN) ======
    raw_monthly = (
        all_bookings.annotate(month_trunc=TruncMonth('event_date'))
        .values('month_trunc')
        .annotate(count=Count('id'))
        .order_by('month_trunc')
    )

    bookings_per_month = []
    package_popularity_by_month = defaultdict(list)
    status_data_by_month = defaultdict(list)
    revenue_data_by_month = {}

    for entry in raw_monthly:
        month_date = entry["month_trunc"]
        if not month_date: continue
        
        key = dateformat.DateFormat(month_date).format("Y-m")
        bookings_per_month.append({"month": key, "count": entry["count"]})

        monthly_b_objs = all_bookings.filter(event_date__year=month_date.year, event_date__month=month_date.month)
        
        # ✅ UPDATE: Monthly Revenue Chart (Filtered by status)
        # Para sa chart, 'Accepted'/'Completed' lang din ang iku-compute na revenue
        chart_money_objs = monthly_b_objs.filter(status__in=["Accepted", "Completed"])
        monthly_revenue = sum(parse_price(b.price) for b in chart_money_objs)
        
        revenue_data_by_month[key] = {
            "total_revenue": monthly_revenue,
            "booking_count": entry["count"]
        }

        package_popularity_by_month[key] = list(monthly_b_objs.values('package__title').annotate(count=Count('id')).order_by('-count'))
        status_data_by_month[key] = list(monthly_b_objs.values('status').annotate(count=Count('id')).order_by('-count'))

    # ====== 6. FEEDBACK ANALYTICS ======
    feedback_by_month = {}
    raw_review_months = all_reviews.annotate(month_trunc=TruncMonth('created_at')).values('month_trunc').distinct()

    for entry in raw_review_months:
        m_date = entry["month_trunc"]
        if not m_date: continue
        key = dateformat.DateFormat(m_date).format("Y-m")
        
        m_reviews = all_reviews.filter(created_at__year=m_date.year, created_at__month=m_date.month)
        feedback_by_month[key] = {
            "avg_quality": round(m_reviews.aggregate(avg=Avg('quality'))['avg'] or 0, 1),
            "avg_timeliness": round(m_reviews.aggregate(avg=Avg('timeliness'))['avg'] or 0, 1),
            "avg_professionalism": round(m_reviews.aggregate(avg=Avg('professionalism'))['avg'] or 0, 1),
            "avg_value_for_money": round(m_reviews.aggregate(avg=Avg('value_for_money'))['avg'] or 0, 1),
        }

    # ====== 7. OTHER DATA ======
    status_data = list(all_bookings.values("status").annotate(count=Count("id")).order_by('-count'))
    upcoming_events = all_bookings.filter(event_date__gte=timezone.now()).exclude(
        status__in=["Completed", "Cancelled", "Rejected"]
    ).order_by('event_date')[:1]

    # ====== 8. CONTEXT CONSTRUCTION ======
    context = {
        'booking_count': booking_count,
        'pending_count': pending_count, 
        'notification_count': notification_count,
        'revenue': revenue,
        'profit': profit,
        'average_rating': round(average_rating, 1),
        
        'bookings_per_month': json.dumps(bookings_per_month),
        'revenue_data_by_month': json.dumps(revenue_data_by_month),
        'package_popularity_by_month': json.dumps(dict(package_popularity_by_month)),
        'status_data_by_month': json.dumps(dict(status_data_by_month)),
        'feedback_by_month': json.dumps(feedback_by_month),
        
        'latest_feedback': all_reviews.order_by('-created_at').first(),
        'upcoming_events': upcoming_events,
        'months': months_list,
        'years': years_list,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }

    return render(request, 'client/dashboard.html', context)
# ============================================================
# ✅ NEW ENDPOINT: fetch Booking Status per Month (for JS filter)
# ============================================================

@login_required
@admin_only
def booking_status_data(request):
    """Return booking status counts filtered by month/year (for JS chart updates)."""
    month = request.GET.get("month")
    year = request.GET.get("year")

    queryset = Booking.objects.all()
    if year:
        queryset = queryset.filter(event_date__year=int(year))
    if month:
        queryset = queryset.filter(event_date__month=int(month))

    data = list(
        queryset.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return JsonResponse({"status_data": data})
@login_required
@admin_only
def booking(request):
    current_year = datetime.now().year

    # ... (retain your months, years, days list) ...
    months = [("1", "January"), ("2", "February"), ("3", "March"), ("4", "April"), ("5", "May"), ("6", "June"), ("7", "July"), ("8", "August"), ("9", "September"), ("10", "October"), ("11", "November"), ("12", "December")]
    years = list(range(2000, current_year + 1))
    days = list(range(1, 32))

    # Get filters
    filter_day = request.GET.get('filter_day')
    filter_month = request.GET.get('filter_month')
    filter_year = request.GET.get('filter_year')
    filter_conditions = Q()

    if filter_day == "today":
        filter_conditions &= Q(event_date=datetime.now().date())
    else:
        day_number = int(filter_day) if filter_day and filter_day.isdigit() else None
        month_number = int(filter_month) if filter_month and filter_month.isdigit() else None
        year_number = int(filter_year) if filter_year and filter_year.isdigit() else None

        if day_number and month_number and year_number:
            filter_conditions &= Q(event_date__day=day_number, event_date__month=month_number, event_date__year=year_number)
        elif month_number and year_number:
            filter_conditions &= Q(event_date__month=month_number, event_date__year=year_number)
        elif month_number:
            filter_conditions &= Q(event_date__month=month_number)
        elif year_number:
            filter_conditions &= Q(event_date__year=year_number)

    # Kunin ang bookings kasama ang checklists
    bookings = Booking.objects.filter(filter_conditions).order_by('-created_at').prefetch_related('checklists__checked_by')

    for b in bookings:
        # Kunin ang specific checklists
        before_cl = b.checklists.filter(checklist_type='BEFORE').first()
        after_cl = b.checklists.filter(checklist_type='AFTER').first()
        
        b.equipment_status = "No Checklist"
        b.checker_name = "N/A"
        b.is_ready_for_complete = False # Default: Hindi pa pwedeng i-complete
        
        if before_cl:
            b.checker_name = before_cl.checked_by.username if before_cl.checked_by else "System"
            
            if not before_cl.is_confirmed:
                b.equipment_status = "Kulang (Outbound)"
            elif after_cl:
                if after_cl.checked_by:
                    b.checker_name = after_cl.checked_by.username
                
                if not after_cl.is_confirmed:
                    b.equipment_status = "Kulang (Inbound)"
                else:
                    b.equipment_status = "✅ Complete (All Returned)"
                    b.is_ready_for_complete = True # ETO ANG MAG-EENABLE NG BUTTON
            else:
                b.equipment_status = "📦 Out for Event"

    # Notifications logic
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    context = {
        'bookings': bookings, 'months': months, 'years': years, 'days': days,
        'current_year': current_year, 'notifications': notifications,
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
    # Table data: only Accepted bookings
    bookings = Booking.objects.filter(status='Accepted')

    # Notifications: newest 5 Processing bookings
    notifications_qs = Booking.objects.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    return render(request, 'client/tracking.html', {
        'bookings': bookings,
        'notifications': notifications,
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

from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .models import Booking, Notification, BookingChecklist, ChecklistItem

@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    package = booking.package
    package_items = package.packageequipment_set.all()

    # --- PHASE 1: VALIDATE STOCK ---
    for item in package_items:
        if item.equipment.quantity_available < item.quantity_required:
            messages.error(
                request,
                f"Not enough stock for {item.equipment.name}. Booking cannot be processed."
            )
            return redirect("booking")

    # --- PHASE 2: APPLY DEDUCTIONS ATOMICALLY ---
    try:
        with transaction.atomic():
            booking.status = "Accepted"
            booking.save()

            for item in package_items:
                equipment = item.equipment
                equipment.quantity_available -= item.quantity_required
                equipment.quantity_rented += item.quantity_required
                equipment.status = "Rented" if equipment.quantity_rented > 0 else "Available"
                equipment.save()

            # Create checklist if not exists
            checklist, created = BookingChecklist.objects.get_or_create(booking=booking)
            if created:
                for item in package_items:
                    ChecklistItem.objects.create(
                        checklist=checklist,
                        equipment=item.equipment,
                        quantity_required=item.quantity_required
                    )

            # Send Notification
            Notification.objects.create(
                user=booking.user,
                message=f"Your booking #{booking.id} has been accepted!"
            )

            messages.success(request, f"Booking #{booking.id} accepted and inventory updated!")

    except Exception as e:
        messages.error(request, f"Error processing booking: {str(e)}")

    return redirect("booking")



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
    # Kunin ang booking
    booking = get_object_or_404(Booking, id=id)

    # Check kung pwede i-complete
    if booking.status in ['Accepted', 'Processing']:
        # 1️⃣ Mark as Completed
        booking.status = 'Completed'
        booking.save()

        # 2️⃣ Return equipment sa inventory
        for package_equipment in booking.package.packageequipment_set.all():
            equipment = package_equipment.equipment
            quantity_rented = package_equipment.quantity_required  

            equipment.quantity_available += quantity_rented
            equipment.quantity_rented -= quantity_rented
            equipment.save()

        # 3️⃣ Flash message sa page
        messages.success(request, f"✅ Booking #{booking.id} has been completed successfully!")

        # 4️⃣ Optional: Create notification sa bell
        Notification.objects.create(
            user=booking.user,
            message=f"✅ Your booking #{booking.id} is done! You can now leave a review."
        )

    else:
        messages.warning(request, f"Booking #{booking.id} cannot be completed because its status is '{booking.status}'.")

    # 5️⃣ Redirect sa bookings page (palitan kung needed)
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
    # Users na may "staff" sa username pero hindi pa admin
    requested_profiles = Profile.objects.filter(
        user__username__icontains="staff",
        user__is_staff=False
    )

    # 🔔 Fetch notifications
    notif_qs = Booking.objects.filter(status="Processing").order_by("-created_at")[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notif_qs
    ]

    return render(request, 'client/admin_request.html', {
        'requested_profiles': requested_profiles,
        'notifications': notifications  # 👈 Added to context
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)

        # 🔔 Notifications
    notif_qs = Booking.objects.filter(status="Processing").order_by("-created_at")[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notif_qs
    ]

    if request.method == "POST":
        # Gawing admin/staff
        user.is_staff = True
        user.save()

        # Optional: linisin yung requested_admin flag kung meron
        if hasattr(user, "profile"):
            user.profile.requested_admin = False
            user.profile.save()

        # ✅ Create a notification for the user
        Notification.objects.create(
            user=user,
            message="🎉 Congratulations! You are now an admin."
        )

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
    
from .models import Equipment, InventoryLog, Booking

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

    booking = None
    booking_id = request.POST.get("booking_id")
    if booking_id:
        booking = Booking.objects.filter(id=booking_id).first()

    try:
        if action == "add_stock":
            equipment.quantity_available += qty
            equipment.save()
            messages.success(request, f"Added {qty} to {equipment.name}.")
        
        elif action == "subtract_stock":
            if equipment.quantity_available < qty:
                messages.error(request, "Not enough available stock.")
                return redirect("inventory_list")
            equipment.quantity_available -= qty
            equipment.save()
            messages.success(request, f"Subtracted {qty} from {equipment.name}.")

        elif action == "to_maintenance":
            # Siguraduhin na may available stock bago ilipat
            if equipment.quantity_available >= qty:
                equipment.quantity_available -= qty
                equipment.qty_maintenance += qty
                equipment.save()
            messages.success(request, f"Moved {qty} to maintenance.")

        elif action == "back_from_maintenance":
            if equipment.qty_maintenance >= qty:
                equipment.qty_maintenance -= qty
                equipment.quantity_available += qty
                equipment.save()
            messages.success(request, f"Returned {qty} from maintenance.")

        elif action == "to_repair":
            if equipment.quantity_available >= qty:
                equipment.quantity_available -= qty
                equipment.qty_repair += qty
                equipment.save()
            messages.success(request, f"Moved {qty} to repair.")

        elif action == "back_from_repair":
            if equipment.qty_repair >= qty:
                equipment.qty_repair -= qty
                equipment.quantity_available += qty
                equipment.save()
            messages.success(request, f"Returned {qty} from repair.")

        # --- DITO NALILIKHA ANG HISTORY/LOG ---
        InventoryLog.objects.create(
            equipment=equipment,
            action=action,
            quantity=qty,
            booking=booking
        )

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect("inventory_list")


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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateformat import DateFormat
from .models import Booking, BookingChecklist, ChecklistItem, Notification
from django.contrib import messages
from django.contrib.auth.models import User

@login_required
@admin_only
def checklist_view(request):
    # FIX: Pinalitan ang select_related("checklist") ng prefetch_related("checklists")
    # Dahil ang ForeignKey ay nagbabalik ng listahan, hindi isang object lang.
    bookings = Booking.objects.filter(status="Accepted").prefetch_related("checklists")

    notif_qs = Booking.objects.filter(status="Processing").order_by("-created_at")[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notif_qs
    ]

    return render(request, "client/checklist.html", {
        "bookings": bookings,
        "notifications": notifications,
    })

@login_required
@admin_only
def checklist_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    ctype = request.GET.get('type', 'BEFORE')
    
    checklist, created = BookingChecklist.objects.get_or_create(
        booking=booking, 
        checklist_type=ctype
    )

    # Populate items (>0 qty only)
    if created:
        package_items = booking.package.packageequipment_set.filter(quantity_required__gt=0)
        for pkg_eq in package_items:
            ChecklistItem.objects.create(
                checklist=checklist,
                equipment=pkg_eq.equipment,
                quantity_required=pkg_eq.quantity_required
            )

    # Check kung confirmed na ang BEFORE step
    before_cl = booking.checklists.filter(checklist_type='BEFORE').first()
    before_is_confirmed = before_cl.is_confirmed if before_cl else False

    # Block access sa Step 2 kung di pa tapos ang Step 1
    if ctype == 'AFTER' and not before_is_confirmed:
        messages.error(request, "⚠️ Tapusin muna ang Step 1.")
        return redirect(f"/accounts/checklist/{booking_id}/?type=BEFORE")

    if request.method == "POST":
        # Security: Bawal mag-save kung confirmed na
        if checklist.is_confirmed:
            messages.error(request, "⚠️ Naka-lock na ang audit na ito.")
            return redirect(f"/accounts/checklist/{booking_id}/?type={ctype}")

        all_ok = True
        missing_items = []
        current_items = checklist.items.filter(quantity_required__gt=0)
        
        for item in current_items:
            qty = int(request.POST.get(f"received_{item.id}", 0) or 0)
            conf = f"confirm_{item.id}" in request.POST
            
            item.quantity_received = qty
            item.confirmed = conf
            item.save()
            
            if qty < item.quantity_required or not conf:
                all_ok = False
                missing_items.append(item.equipment.name)
        
        checklist.is_confirmed = all_ok
        checklist.checked_by = request.user # Sine-save ang auditor
        checklist.save()
        
        if all_ok:
            messages.success(request, f"✅ {ctype}: COMPLETE")
        else:
            messages.warning(request, f"⚠️ INCOMPLETE: {', '.join(missing_items)}")
            
        return redirect(f"/accounts/checklist/{booking_id}/?type={ctype}")

    display_items = checklist.items.filter(quantity_required__gt=0)

    return render(request, "client/checklist_detail.html", {
        "booking": booking, 
        "checklist": checklist, 
        "items": display_items, 
        "checklist_type": ctype,
        "before_is_confirmed": before_is_confirmed
    })
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
@login_required
@admin_only
def package_list_view(request):
    packages = ServicePackage.objects.all()

    # 🔔 Notifications logic
    notif_qs = Booking.objects.filter(status="Processing").order_by("-created_at")[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notif_qs
    ]

    return render(request, 'client/package_list.html', {
        'packages': packages,
        'notifications': notifications,
    })



def package_add_view(request):
    equipments = Equipment.objects.all()

    if request.method == "POST":
        form = ServicePackageForm(request.POST, request.FILES)
        qty_form = EquipmentQuantityForm(request.POST, equipments=equipments)

        if form.is_valid() and qty_form.is_valid():
            package = form.save()

            for equipment in equipments:
                field_name = f"equipment_{equipment.id}"
                qty = int(qty_form.cleaned_data.get(field_name, 0))
                if qty > 0:
                    PackageEquipment.objects.create(
                        package=package,
                        equipment=equipment,
                        quantity_required=qty
                    )
            
            messages.success(request, "Package created successfully!")
            return redirect("package_list")
    else:
        form = ServicePackageForm()
        qty_form = EquipmentQuantityForm(equipments=equipments)

    equipment_fields = [(eq, qty_form[f"equipment_{eq.id}"]) for eq in equipments]

    return render(request, "client/package_add.html", {
        "form": form,
        "qty_form": qty_form,
        "equipment_fields": equipment_fields,
        "package": None,
    })


def package_edit_view(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id)
    # ✅ Only get equipment linked to this package
    equipments = Equipment.objects.all()
    
    if request.method == "POST":
        form = ServicePackageForm(request.POST, request.FILES, instance=package)
        qty_form = EquipmentQuantityForm(request.POST, equipments=equipments)

        if form.is_valid() and qty_form.is_valid():
            form.save()

            # Update existing PackageEquipment or create new ones
            for equipment in equipments:
                field_name = f"equipment_{equipment.id}"
                qty = qty_form.cleaned_data.get(field_name, 0)

                pe, created = PackageEquipment.objects.get_or_create(
                    package=package,
                    equipment=equipment,
                    defaults={"quantity_required": qty}
                )
                if not created:
                    pe.quantity_required = qty
                    pe.save()

            messages.success(request, "Package updated successfully!")
            return redirect("package_list")
    else:
        form = ServicePackageForm(instance=package)

        # Pre-fill quantities from existing PackageEquipment
        initial_data = {}
        for equipment in equipments:
            try:
                pe = PackageEquipment.objects.get(package=package, equipment=equipment)
                initial_data[f"equipment_{equipment.id}"] = pe.quantity_required
            except PackageEquipment.DoesNotExist:
                initial_data[f"equipment_{equipment.id}"] = 0

        qty_form = EquipmentQuantityForm(initial=initial_data, equipments=equipments)

    equipment_fields = [
        (equipment, qty_form[f"equipment_{equipment.id}"])
        for equipment in equipments
    ]

    return render(request, "client/package_add.html", {
        "form": form,
        "qty_form": qty_form,
        "equipment_fields": equipment_fields,
        "package": package,
    })
# DELETE - Delete package
def package_delete_view(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id)
    if request.method == 'POST':
        package.delete()
        messages.success(request, "Package deleted successfully!")
        return redirect('package_list')
    return render(request, 'client/package_delete.html', {'package': package})

@login_required
@admin_only
def add_employee_view(request):
    # --- Sidebar Notifications (Para mag-match sa ibang pages mo) ---
    bookings = Booking.objects.all()
    notifications_qs = bookings.filter(status="Processing").order_by('-created_at')[:5]
    notifications = [
        f"📌 New booking from {b.full_name} on {DateFormat(b.event_date).format('M d, Y')}"
        for b in notifications_qs
    ]

    if request.method == "POST":
        # Kunin ang data mula sa form
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        province = request.POST.get("province")
        city = request.POST.get("city")
        barangay = request.POST.get("barangay")

        # Validation: Check kung existing na ang username/email
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            # 1. Create User as Staff (is_staff=True)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True # Ito ang magseset sa kanila bilang Staff/Employee
            )

            # 2. Create Profile associated with the user
            Profile.objects.create(
                user=user,
                contact_number=phone,
                address=address,
                province=province,
                city=city,
                barangay=barangay
            )

            messages.success(request, f"✅ Employee account for {username} successfully created!")
            return redirect('employee') # Redirect pabalik sa table ng employees

    return render(request, 'client/add_employee.html', {
        'notifications': notifications
    })
import csv
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, FloatField, Value
from django.db.models.functions import Cast, ExtractMonth, Replace
from django.utils import timezone
from .models import Booking

@login_required
def reports_page(request):
    # Kunin ang Year at Month mula sa URL filters
    y = request.GET.get('year', str(timezone.now().year))
    m = request.GET.get('month', 'All')

    # Data Cleaning: Tanggalin ang symbols para maging Float ang CharField
    clean_price = Replace(Replace('price', Value('₱'), Value('')), Value(','), Value(''))

    # 1. Base Filters
    filters = Q(event_date__year=y)
    if m != 'All':
        filters &= Q(event_date__month=m)

    # 2. Revenue Calculation (Lahat ng hindi Rejected)
    revenue_query = Booking.objects.filter(filters).exclude(status__icontains='Reject').annotate(
        price_num=Cast(clean_price, output_field=FloatField())
    )
    total_rev = revenue_query.aggregate(total=Sum('price_num'))['total'] or 0

    # 3. Monthly Kita para sa Graph (Trend)
    monthly_rev = [0] * 12
    graph_query = Booking.objects.filter(event_date__year=y).exclude(status__icontains='Reject').annotate(
        price_num=Cast(clean_price, output_field=FloatField())
    ).annotate(month=ExtractMonth('event_date')).values('month').annotate(total=Sum('price_num'))
    
    for item in graph_query:
        monthly_rev[item['month']-1] = float(item['total'] or 0)

    # 4. Growth Logic (Current Year vs Previous Year)
    last_y_rev = Booking.objects.filter(event_date__year=int(y)-1).exclude(status__icontains='Reject').annotate(
        price_num=Cast(clean_price, output_field=FloatField())
    ).aggregate(total=Sum('price_num'))['total'] or 0
    
    growth = 0
    if last_y_rev > 0:
        growth = ((total_rev - last_y_rev) / last_y_rev) * 100

    # 5. History at Insights
    all_bookings = Booking.objects.filter(filters).order_by('-event_date')
    recent_bookings = all_bookings[:5] # Limit sa 5 para sa table
    has_more = all_bookings.count() > 5

    top_loc = all_bookings.values('location').annotate(c=Count('id')).order_by('-c').first()
    top_area = top_loc['location'] if top_loc else "N/A"
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    max_val = max(monthly_rev) if any(monthly_rev) else 0
    peak_month = month_names[monthly_rev.index(max_val)] if max_val > 0 else "N/A"

    # Insight Message Construction
    monthly_summary = ", ".join([f"{month_names[i]}: ₱{val:,.0f}" for i, val in enumerate(monthly_rev) if val > 0])
    
    if total_rev > 0:
        insight_msg = f"Noong {y}, ang pinakamalakas mong buwan ay {peak_month}. Breakdown ng kita: {monthly_summary}. Pinaka-active na location ang {top_area}."
    else:
        insight_msg = "Wala pang sapat na revenue data para sa period na ito. Siguraduhin na ang bookings ay may 'Price' at hindi Rejected."

    context = {
        'bookings': recent_bookings,
        'all_bookings_count': all_bookings.count(),
        'has_more': has_more,
        'revenue_data': json.dumps(monthly_rev),
        'total_rev': total_rev,
        'growth': round(growth, 2),
        'top_area': top_area,
        'peak_month': peak_month,
        'insight_msg': insight_msg,
        'selected_y': y,
        'selected_m': m,
        'years': range(2024, 2028),
    }
    return render(request, 'client/reports.html', context)
@login_required
def export_bookings_csv(request):
    y = request.GET.get('year', str(timezone.now().year))
    m = request.GET.get('month', 'All')
    
    clean_price = Replace(Replace('price', Value('₱'), Value('')), Value(','), Value(''))
    filters = Q(event_date__year=y)
    if m != 'All': filters &= Q(event_date__month=m)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Report_{y}_{m}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['BUSINESS REPORT', f'Year: {y}', f'Month: {m}'])
    writer.writerow([]) # Blank line
    writer.writerow(['Date', 'Customer', 'Location', 'Price', 'Status'])
    
    bookings = Booking.objects.filter(filters).order_by('-event_date')
    total = 0
    for b in bookings:
        writer.writerow([b.event_date, b.full_name, b.location, b.price, b.status])
        # Simple cleaning for total in CSV
        try:
            p = float(b.price.replace('₱', '').replace(',', ''))
            if 'Reject' not in b.status: total += p
        except: pass

    writer.writerow([])
    writer.writerow(['', '', 'TOTAL REVENUE:', f'PHP {total:,.2f}'])
    return response

def bookings_list(request):
    # Dito natin kukunin lahat ng bookings sa database
    all_bookings = Booking.objects.all().order_by('-event_date') 
    
    context = {
        'bookings': all_bookings,
    }
    return render(request, 'client/bookings_list.html', context)