from django.utils import timezone
from datetime import timedelta
from .models import Appointment, ArchivedAppointment

def archive_old_appointments(days_old=365):
    cutoff_date = timezone.now() - timedelta(days=days_old)
    old_appointments = Appointment.objects.filter(end__lt=cutoff_date)
    
    for appointment in old_appointments:
        ArchivedAppointment.objects.create(
            title=appointment.title,
            start=appointment.start,
            end=appointment.end,
            type=appointment.type
        )
    
    old_appointments.delete()
    
    return len(old_appointments)