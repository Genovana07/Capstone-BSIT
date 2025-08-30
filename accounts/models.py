from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import datetime

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    requested_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    quantity_available = models.IntegerField(default=0)
    quantity_rented = models.IntegerField(default=0)
    qty_maintenance = models.PositiveIntegerField(default=0)
    qty_repair = models.PositiveIntegerField(default=0)

    condition = models.CharField(
        max_length=100,
        choices=[
            ('Good', 'Good'),
            ('Needs Repair', 'Needs Repair'),
            ('Excellent', 'Excellent'),
        ],
        default='Good'
    )

    status = models.CharField(
        max_length=50,
        choices=[
            ('Available', 'Available'),
            ('Rented', 'Rented'),
            ('Under Maintenance', 'Under Maintenance'),
            ('Under Repair', 'Under Repair'),   # 🔥 Added
            ('Decommissioned', 'Decommissioned'),  # optional
        ],
        default='Available'
    )

    last_checked_out_date = models.DateField(null=True, blank=True)
    current_location = models.CharField(max_length=255, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)  # 🔥 New field

    def __str__(self):
        return self.name

    # --- STOCK MANAGEMENT METHODS ---

    def update_quantity(self, quantity_rented: int):
        """Rent equipment and update stock safely."""
        if quantity_rented > self.quantity_available:
            raise ValueError(
                f"Not enough stock available for {self.name}. Only {self.quantity_available} available."
            )
        self.quantity_available -= quantity_rented
        self.quantity_rented += quantity_rented
        self.status = "Rented" if self.quantity_rented > 0 else "Available"
        self.save()

    def return_stock(self, quantity_rented: int):
        """Return rented equipment back to inventory."""
        if quantity_rented > self.quantity_rented:
            raise ValueError(
                f"Cannot return {quantity_rented}. Only {self.quantity_rented} rented out."
            )
        self.quantity_available += quantity_rented
        self.quantity_rented -= quantity_rented
        self.status = "Available"
        self.save()

    def move_to_maintenance(self, qty=1):
        """Send available stock to maintenance."""
        if qty > self.quantity_available:
            raise ValueError("Not enough available stock to move to maintenance.")
        self.quantity_available -= qty
        self.qty_maintenance += qty
        self.status = "Under Maintenance"
        self.save()

    def return_from_maintenance(self, qty=1):
        """Return stock from maintenance back to available."""
        if qty > self.qty_maintenance:
            raise ValueError("Not enough stock in maintenance to return.")
        self.qty_maintenance -= qty
        self.quantity_available += qty
        self.status = "Available"
        self.save()

    def move_to_repair(self, qty=1):
        """Send available stock to repair."""
        if qty > self.quantity_available:
            raise ValueError("Not enough available stock to move to repair.")
        self.quantity_available -= qty
        self.qty_repair += qty
        self.status = "Under Repair"
        self.save()

    def return_from_repair(self, qty=1):
        """Return stock from repair back to available."""
        if qty > self.qty_repair:
            raise ValueError("Not enough stock in repair to return.")
        self.qty_repair -= qty
        self.quantity_available += qty
        self.status = "Available"
        self.save()

    # --- PROPERTIES ---

    @property
    def total_stock(self):
        """Total stock across all categories."""
        return (
            self.quantity_available +
            self.quantity_rented +
            self.qty_maintenance +
            self.qty_repair
        )

    @property
    def is_available(self):
        """Check if equipment can be rented."""
        return self.quantity_available > 0


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
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey('ServicePackage', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    event_date = models.DateField()
    event_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    fulladdress = models.CharField(max_length=255, blank=True, null=True)
    audience_size = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    price = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    cancel_reason = models.TextField(blank=True, null=True) 
    reject_reason = models.TextField(null=True, blank=True)

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

    def return_equipment(self):
        """Restores rented equipment back to inventory."""
        if self.status != 'Approved':
            raise ValueError("Booking is not approved yet.")
        
        for package_equipment in self.package.packageequipment_set.all():
            equipment = package_equipment.equipment
            quantity_rented = package_equipment.quantity_required  

            equipment.return_stock(quantity_rented)
    
    def mark_as_completed(self):
        """Mark the booking as completed and return the equipment to inventory."""
        self.status = 'Completed'
        self.save()
        
        self.return_equipment()

        print(f"Booking {self.id} is marked as completed and equipment has been returned to inventory.")
    
    def cancel_booking(self):
        """Handles booking cancellation and restores equipment to inventory."""
        if self.status == 'Approved':
            self.return_equipment()
        
        self.status = 'Rejected'
        self.save()

        print(f"Booking {self.id} has been canceled and equipment restored to inventory.")

class InventoryLog(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=[('rented', 'Rented'), ('returned', 'Returned')])
    quantity = models.IntegerField()
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} {self.quantity} of {self.equipment.name} for Booking {self.booking.id}."


class Review(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=255, default='Anonymous')
    booking_date = models.DateField()
    event_type = models.CharField(max_length=255, default='Unknown')

    # Overall rating
    rating = models.IntegerField(default=5)

    # Metrics ratings (1–5 scale)
    quality = models.IntegerField(default=0)
    timeliness = models.IntegerField(default=0)
    professionalism = models.IntegerField(default=0)
    value_for_money = models.IntegerField(default=0)

    comment = models.TextField(default='No comment.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer_name} on {self.booking_date}"
    
class BookingChecklist(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="checklist")
    is_confirmed = models.BooleanField(default=False)  # Kung na-confirm na lahat ng equipment

    def __str__(self):
        return f"Checklist for Booking {self.booking.id}"


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(BookingChecklist, on_delete=models.CASCADE, related_name="items")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity_required = models.IntegerField()
    quantity_received = models.IntegerField(default=0)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.equipment.name} - {self.quantity_received}/{self.quantity_required}"
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"