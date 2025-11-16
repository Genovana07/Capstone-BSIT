from .models import Notification
from .models import Booking

def notifications_context(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'notifications_unread_count': unread_count
        }
    return {}

def global_notifications(request):
    if request.user.is_authenticated:
        # Example: unread or pending bookings only
        notifications = Booking.objects.filter(status="Pending")
    else:
        notifications = []

    return {
        'notifications': notifications
    }


def user_notifications(request):
    if request.user.is_authenticated:
        # Step 1: Kunin lahat ng notifications ng user, newest first
        notifications_qs = Notification.objects.filter(user=request.user).order_by('-created_at')

        # Step 2: Bilangin yung unread notifications
        notifications_unread_count = notifications_qs.filter(is_read=False).count()

        # Step 3: Kunin ang latest 5 notifications
        latest_notifications = notifications_qs[:5]

        return {
            'notifications': latest_notifications,
            'notifications_unread_count': notifications_unread_count,
        }

    return {
        'notifications': [],
        'notifications_unread_count': 0,
    }