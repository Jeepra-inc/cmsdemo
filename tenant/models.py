import random
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


def generate_unique_tenant_id():
    """Generate a unique 8-digit numeric tenant_id."""
    while True:
        tenant_id = ''.join(random.choices("0123456789", k=8))  # Only digits
        if not Tenant.objects.filter(tenant_id=tenant_id).exists():
            return tenant_id


class Tenant(TenantMixin):
    user = models.ForeignKey('users.UserAccount', on_delete=models.CASCADE, null=True, blank=True)
    schema_name = models.CharField(max_length=63, unique=True)  # Schema Name (pradoc000001, etc.)
    tenant_id = models.CharField(
        max_length=8, unique=True, editable=False, blank=True, null=True, default=generate_unique_tenant_id
    )  # Unique Tenant ID (digits only)
    domain_type = models.CharField(
        max_length=50,
        choices=[('custom', 'Custom Domain'), ('subdomain', 'Platform Subdomain')],
        default='subdomain',
    )
    is_active = models.BooleanField(default=False, blank=True)  # Account Status
    wizard = models.BooleanField(default=True, blank=True)  # Account Status

    # Subscription Plan
    SUBSCRIPTION_PLANS = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_plan = models.CharField(
        max_length=20, choices=SUBSCRIPTION_PLANS, default='free'
    )

    # Schema settings for tenants
    auto_create_schema = True  # Automatically create schema when saved
    auto_drop_schema = True  # Automatically drop schema when deleted

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant_id = generate_unique_tenant_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.schema_name}"



class Domain(DomainMixin):
    """
    Extend this if additional fields are needed in the Domain model.
    """
    pass



class TenantInfo(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="info")

    # Tenant/Clinic Information
    clinic_name = models.CharField(max_length=150, blank=True, null=True)  # Clinic/Hospital Name
    logo = models.ImageField(upload_to="tenant_logos/", blank=True, null=True)  # Logo
    established_year = models.PositiveIntegerField(blank=True, null=True)  # Year of establishment
    registration_number = models.CharField(max_length=100, blank=True, null=True)  # Medical registration/license number
    specialization = models.CharField(max_length=255, blank=True, null=True)  # Specialization for individual doctors/hospitals
    description = models.TextField(blank=True, null=True)  # Overview/Description of the hospital or doctor
    website = models.URLField(blank=True, null=True)  # Clinic/Hospital/Doctor's Website URL

    # Address Fields
    clinic_address_line1 = models.CharField(max_length=255, blank=True, null=True)  # Address Line 1
    clinic_address_line2 = models.CharField(max_length=255, blank=True, null=True)  # Address Line 2 (optional)
    city = models.CharField(max_length=100, blank=True, null=True)  # City
    state = models.CharField(max_length=100, blank=True, null=True)  # State/Province/Region
    postal_code = models.CharField(max_length=20, blank=True, null=True)  # Postal/ZIP Code
    country = models.CharField(max_length=100, blank=True, null=True)  # Country

    # Contact Information
    clinic_phone = models.CharField(max_length=20, blank=True, null=True)  # Clinic Phone Number
    clinic_email = models.EmailField(blank=True, null=True)  # Clinic Email Address
    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)  # Emergency Contact Number

    # Preferences
    time_zone = models.CharField(max_length=100, blank=True, null=True)  # Time Zone
    default_language = models.CharField(max_length=10, blank=True, null=True)  # Default Language (e.g., 'en', 'es')
    week_starts_from = models.CharField(
        max_length=10,
        choices=[('monday', 'Monday'), ('sunday', 'Sunday')],
        default='monday',
    )

    # Hospital/Doctor-Specific Fields
    total_beds = models.PositiveIntegerField(blank=True, null=True)  # For hospitals
    departments = models.JSONField(blank=True, null=True)  # List of departments (e.g., {"departments": ["Cardiology", "Orthopedics"]})
    services_offered = models.JSONField(blank=True, null=True)  # Services (e.g., {"services": ["X-Ray", "MRI", "Consultation"]})
    awards = models.JSONField(blank=True, null=True)  # Awards/Recognitions (e.g., {"awards": ["Best Hospital 2023"]})
    affiliations = models.JSONField(blank=True, null=True)  # Medical board affiliations
    insurance_accepted = models.JSONField(blank=True, null=True)  # Insurance providers accepted
    available_timings = models.JSONField(blank=True, null=True)  # Working hours (e.g., {"monday": "9 AM - 5 PM"})

    # Social Media Links
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)

    # Additional Features
    parking_availability = models.BooleanField(default=False)  # Parking availability
    ambulance_services = models.BooleanField(default=False)  # Ambulance availability
    pharmacy = models.BooleanField(default=False)  # On-premise pharmacy

    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)  # Record Creation Timestamp
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True)  # Record Last Updated Timestamp

    system_language = models.CharField(max_length=2, blank=True, null=True)


    def __str__(self):
        return f"Info for Tenant {self.tenant.schema_name}"

