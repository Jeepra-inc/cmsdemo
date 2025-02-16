from django.db import models
from django.utils import timezone
from django.conf import settings


class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('checkup', 'Check-up'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
    ]

    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()
    type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)

    def __str__(self):
        return self.title

class ArchivedAppointment(models.Model):
    APPOINTMENT_TYPES = [
        ('checkup', 'Check-up'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
    ]

    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()
    type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)
    archived_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Archived: {self.title}"

class BookedAppointment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Prevent cascading deletes
        null=True,
        related_name='booked_appointments'
    )  
    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField()
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=[
        ('checkup', 'Check-up'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.appointment_date} {self.appointment_time}"
