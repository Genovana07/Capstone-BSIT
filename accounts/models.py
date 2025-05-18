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

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    quantity_available = models.IntegerField(default=0)  # Total quantity available
    quantity_rented = models.IntegerField(default=0)  # Total quantity rented out
    condition = models.CharField(max_length=100, choices=[  # Condition field
        ('Good', 'Good'),
        ('Needs Repair', 'Needs Repair'),
        ('Excellent', 'Excellent'),
    ], default='Good')

    def __str__(self):
        return self.name

    def update_quantity(self, quantity_rented):
        """Update the available and rented quantities for the equipment."""
        
        # Check if there is enough stock available
        if quantity_rented > self.quantity_available:
            raise ValueError(f"Not enough stock available for {self.name}. Only {self.quantity_available} available.")
        
        # Deduct the rented quantity from available stock
        self.quantity_available -= quantity_rented
        
        # Add to the rented quantity
        self.quantity_rented += quantity_rented
        
        # Save the changes in the database
        self.save()

        print(f"Updated {self.name}: {self.quantity_available} available, {self.quantity_rented} rented.")

class ServicePackage(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.CharField(max_length=20)
    equipment = models.ManyToManyField(Equipment, through='PackageEquipment')

    def __str__(self):
        return self.title

class PackageEquipment(models.Model):
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity_required = models.IntegerField()  # The quantity needed for the package

    def __str__(self):
        return f'{self.package.title} - {self.equipment.name}'

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    event_date = models.DateField()
    event_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    audience_size = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    price = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking {self.id} by {self.full_name}"

    def calculate_end_time(self):
        start_time = timezone.make_aware(datetime.combine(self.event_date, self.event_time))
        end_time = start_time + timedelta(hours=4)
        return end_time.time()

    @staticmethod
    def is_day_full(date, max_bookings=2):
        approved_count = Booking.objects.filter(event_date=date, status='Approved').count()
        return approved_count >= max_bookings
