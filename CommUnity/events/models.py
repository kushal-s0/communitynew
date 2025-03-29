from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from Login.models import UserProfile
from members.models import CoreMember
from faculty.models import Faculty
from committees.models import Associations


class Location(models.Model):
    LOCATION_CHOICES = [
        ('online', 'Online'),
        ('auditorium', 'Auditorium'),
        ('open canteen', 'Open Canteen'),
        ('turf', 'Turf'),
        ('vidya vihar', 'Vidya Vihar')
    ]

    id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255, choices=LOCATION_CHOICES, default='online')
    # custom_location = models.CharField(max_length=255, blank=True, null=True)  # Only for 'Other' selection

    def __str__(self):
        # return self.custom_location if self.location == 'other' else self.location
        return self.location


# Faculty Lock Date Model (For Exams & College Fest)
class FacultyLockDate(models.Model):
    locked_date = models.DateField(unique=True)  # Ensures no duplicate locked dates
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.locked_date} - {self.reason if self.reason else 'Locked'}"

# Event Model

# Event Model
class Event(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255)  # Directly storing location name
    assosiation = models.ForeignKey(Associations, on_delete=models.CASCADE)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='created_events')
    approved_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        """
        Prevents double booking if event is approved.
        Also prevents scheduling on locked dates.
        """
        if FacultyLockDate.objects.filter(locked_date=self.date_time.date()).exists():
            raise ValidationError("This date is locked by faculty and cannot have events.")

        if Event.objects.filter(
            location=self.location,
            date_time=self.date_time,
            status="approved"
        ).exists():
            raise ValidationError("This location and time are already booked for another event.")

    def __str__(self):
        return f"{self.title} - {self.date_time} - {self.club}"
