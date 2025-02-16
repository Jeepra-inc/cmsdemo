import logging
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, BookedAppointment, ArchivedAppointment
from .serializers import (
    AppointmentSerializer,
    ArchivedAppointmentSerializer,
    AvailableDateSerializer,
    BookAppointmentSerializer,
    BookedAppointmentSerializer
)

logger = logging.getLogger(__name__)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def available_dates(self, request):
        try:
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=30)  # Get available dates for the next 30 days

            business_hours = {
                'start': time(9, 0),
                'end': time(17, 0),
                'slot_duration': timedelta(minutes=30)
            }

            available_dates = []
            for date in (start_date + timedelta(n) for n in range((end_date - start_date).days)):
                day_start = timezone.make_aware(datetime.combine(date, business_hours['start']))
                day_end = timezone.make_aware(datetime.combine(date, business_hours['end']))

                day_appointments = self.queryset.filter(
                    Q(start__date=date) | Q(end__date=date)
                ).order_by('start')
                
                booked_appointments = BookedAppointment.objects.filter(appointment_date=date)

                available_slots = []
                current_slot = day_start

                while current_slot < day_end:
                    slot_end = current_slot + business_hours['slot_duration']
                    is_available = True

                    # Check if the slot overlaps with any existing appointment
                    for appointment in day_appointments:
                        if current_slot < appointment.end and slot_end > appointment.start:
                            is_available = False
                            break

                    # Check if the slot is already booked
                    if booked_appointments.filter(appointment_time=current_slot.time()).exists():
                        is_available = False

                    if is_available:
                        available_slots.append(current_slot.time())

                    current_slot += business_hours['slot_duration']

                if available_slots:
                    available_dates.append({
                        'date': date.isoformat(),
                        'availableSlots': [slot.strftime('%H:%M') for slot in available_slots]
                    })

            serializer = AvailableDateSerializer(available_dates, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"Error in available_dates: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def book_appointment(self, request):
        try:
            serializer = BookAppointmentSerializer(data=request.data)
            if serializer.is_valid():
                appointment_date = serializer.validated_data['appointment_date']
                appointment_time = serializer.validated_data['appointment_time']

                # Check if the slot is still available
                available_dates = self.available_dates(request).data
                available_date = next((d for d in available_dates if d['date'] == appointment_date.isoformat()), None)
                if not available_date or appointment_time.strftime('%H:%M') not in available_date['availableSlots']:
                    return Response({'error': 'This appointment slot is no longer available'}, status=status.HTTP_400_BAD_REQUEST)

                booked_appointment = BookedAppointment.objects.create(
                    user=request.user,
                    patient_name=serializer.validated_data['patient_name'],
                    patient_email=serializer.validated_data['patient_email'],
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    appointment_type=serializer.validated_data['appointment_type']
                )

                return Response(BookedAppointmentSerializer(booked_appointment).data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error in book_appointment: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BookedAppointmentViewSet(viewsets.ModelViewSet):
    queryset = BookedAppointment.objects.all()
    serializer_class = BookedAppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        try:
            appointment = self.get_object()
            appointment.delete()
            return Response({'message': 'Appointment cancelled successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error in cancel appointment: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)