from django.db import models
from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from tenant_users.permissions.models import TenantUserMixin, PermissionsMixinFacade
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import random

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError(_('Users must have an email address'))
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(email, password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class UserAccount(TenantUserMixin, AbstractBaseUser, PermissionsMixinFacade, PermissionsMixin):
    # Basic personal info
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True, max_length=255, db_index=True)
    profile_picture = models.CharField(max_length=5000, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
        null=True
    )
    contact_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', _('Invalid phone number'))]
    )

    # User role
    ROLE_CHOICES = [
        (1, 'Admin'),
        (2, 'Staff'),
        (3, 'Doctor'),
        (4, 'Patient'),
        (5, 'Subscriber'),
    ]
    role = models.IntegerField(choices=ROLE_CHOICES, default=2, db_index=True)

    # Account management
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Manager
    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['email']
        verbose_name = _('User Account')
        verbose_name_plural = _('User Accounts')

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Check if username is missing, and generate one
        if not self.username:
            self.username = self.generate_unique_username()           
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_username():
        while True:
            # Generate a random 8-digit number
            username = str(random.randint(10000000, 99999999))
            # Check if the username already exists
            if not UserAccount.objects.filter(username=username).exists():
                return username


class UserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings')

    # Professional Details
    specialization = models.JSONField(null=True, blank=True, default=list)
    license_number = models.CharField(
        max_length=50,
        unique=True,
        validators=[RegexValidator(r'^[A-Za-z0-9]+$', _('Invalid license number'))]
    )
    medical_board = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    qualification = models.JSONField(null=True, blank=True, default=list)
    registration_number = models.CharField(max_length=100, blank=True, null=True)

    # Biographical Info
    bio = models.CharField(max_length=2000, blank=True, null=True)

    # SEO Settings
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.CharField(max_length=500, blank=True, null=True)
    do_not_index = models.BooleanField(default=False)

    # Contact and availability
    emergency_contact_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', _('Invalid phone number'))]
    )
    is_accepting_patients = models.BooleanField(default=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    offers_telemedicine = models.BooleanField(default=False)
    available_for_emergency = models.BooleanField(default=False)

    # Social Profiles
    social_profiles = models.JSONField(blank=True, null=True, default=dict)

    # Languages
    languages_spoken = models.JSONField(blank=True, null=True, default=list)
    consultation_languages = models.JSONField(blank=True, null=True, default=list)
    system_language = models.CharField(max_length=2, blank=True, null=True)
    doctor_qualifications = models.JSONField(blank=True, null=True, default=list)

    class Meta:
        verbose_name = _('User Settings')
        verbose_name_plural = _('User Settings')

    def __str__(self):
        return f"Settings for {self.user.email}"


class UserActivity(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='activities')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.JSONField(default=dict, blank=True, null=True)  # Stores OS, browser, etc.
    location_data = models.JSONField(blank=True, null=True)  # Stores city, country, latitude, longitude
    timestamp = models.DateTimeField(auto_now_add=True)  # Records the login time

    class Meta:
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"Activity for {self.user.email} at {self.timestamp}"
