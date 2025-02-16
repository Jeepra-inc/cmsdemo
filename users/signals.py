from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserActivity
import geoip2.database
import os
from django.conf import settings

@receiver(user_logged_in)
def record_user_activity(sender, request, user, **kwargs):
    # Capture device and IP information
    device_info = {
        "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
    }
    ip_address = request.META.get("REMOTE_ADDR")

    # Initialize location data with a default error message
    location_data = {"error": "Location not available"}

    # Check if IP address is local and set a message accordingly
    local_ips = ["127.0.0.1", "localhost"]
    if ip_address in local_ips:
        location_data = {"error": "Local IP address - location not available"}
    else:
        # Path to GeoLite2 database file
        geoip_db_path = os.path.join(settings.BASE_DIR, 'users', 'files', 'GeoLite2-City.mmdb')
        
        # Attempt to get location data from the GeoLite2 database
        try:
            with geoip2.database.Reader(geoip_db_path) as reader:
                response = reader.city(ip_address)
                location_data = {
                    "city": response.city.name,
                    "country": response.country.name,
                    "latitude": response.location.latitude,
                    "longitude": response.location.longitude,
                }
        except geoip2.errors.AddressNotFoundError:
            location_data = {"error": "Location not found"}
        except Exception as e:
            print(f"GeoIP2 error: {e}")
            location_data = {"error": "Location not found"}

    # Create a UserActivity record
    UserActivity.objects.create(
        user=user,
        ip_address=ip_address,
        device_info=device_info,
        location_data=location_data
    )
