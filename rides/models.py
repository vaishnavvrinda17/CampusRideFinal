
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.conf import settings



class Ride(models.Model):
    student_name = models.CharField(max_length=100)
    pickup_location = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    travel_date = models.DateField()
    travel_time = models.TimeField()
    available_seats = models.PositiveIntegerField(default=1)

    pickup_point = gis_models.PointField(
        srid=4326, null=True, blank=True
    )
    destination_point = gis_models.PointField(
        srid=4326, null=True, blank=True
    )

    offered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offered_rides'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name}: {self.pickup_location} to {self.destination}"


class Errand(models.Model):
    student_name = models.CharField(max_length=100)
    task_description = models.CharField(max_length=300)
    pickup_location = models.CharField(max_length=200)
    delivery_location = models.CharField(max_length=200)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)

    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=[
            ('shopping', 'Shopping'),
            ('documents', 'Document Pickup'),
            ('food', 'Food Pickup'),
            ('other', 'Other'),
        ],
        default='other'
    )
    required_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('accepted', 'Accepted'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='available'
    )

    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_errands'
    )


    def __str__(self):
        return f"{self.student_name}: {self.task_description}"

   
class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='ride_requests'
    )

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_ride_requests'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ride', 'requester'],
                name='unique_request_per_student_ride'
            )
        ]

    def __str__(self):
        return f"{self.requester} - {self.ride} ({self.status})"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    enrollment_number = models.CharField(
        max_length=30,
        unique=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.enrollment_number}"
