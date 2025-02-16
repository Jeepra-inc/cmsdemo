from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, BookedAppointmentViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet)
router.register(r'booked-appointments', BookedAppointmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]