from rest_framework import serializers
from .models import Appointment, ArchivedAppointment, BookedAppointment
from datetime import datetime, time

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'title', 'start', 'end', 'type']

class ArchivedAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivedAppointment
        fields = ['id', 'title', 'start', 'end', 'type', 'archived_date']

from rest_framework import serializers
from .models import BookedAppointment
from django.contrib.auth import get_user_model
from datetime import datetime, time

User = get_user_model()

class AvailableDateSerializer(serializers.Serializer):
    date = serializers.DateField()
    availableSlots = serializers.ListField(child=serializers.TimeField(format='%H:%M'))

class BookAppointmentSerializer(serializers.Serializer):
    patient_name = serializers.CharField(max_length=100)
    patient_email = serializers.EmailField()
    appointment_date = serializers.DateField(input_formats=['%Y-%m-%d'])
    appointment_time = serializers.TimeField(input_formats=['%H:%M'])
    appointment_type = serializers.ChoiceField(choices=['checkup', 'followup', 'emergency'])

    def validate_appointment_date(self, value):
        if value < datetime.now().date():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value

    def validate_appointment_time(self, value):
        if not isinstance(value, time):
            try:
                value = datetime.strptime(value, '%H:%M').time()
            except ValueError:
                raise serializers.ValidationError("Time has wrong format. Use HH:MM format.")
        return value

class BookedAppointmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = BookedAppointment
        fields = ['id', 'user', 'patient_name', 'patient_email', 'appointment_date', 'appointment_time', 'appointment_type', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)