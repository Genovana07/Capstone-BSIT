from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class ServicePackage(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.CharField(max_length=20)

    def __str__(self):
        return self.title


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey('ServicePackage', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    event_date = models.DateField()
    event_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)  # Keep end_time field
    event_type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    audience_size = models.IntegerField()
    status = models.CharField(max_length=50, default='Processing')
    price = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking {self.id} by {self.full_name}"
    
    # Function to calculate end time based on event time (assuming 4 hours event duration)
    def calculate_end_time(self):
        start_time = timezone.make_aware(datetime.combine(self.event_date, self.event_time))
        end_time = start_time + timedelta(hours=4)
        return end_time.time()


class BookingStatus(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Processing')

    def __str__(self):
        return f"Booking Status for {self.booking.full_name}: {self.status}"
