import uuid
import random
import string
import logging
from .models import UserAccount, UserSettings
from tenant.models import Tenant, Domain
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django_tenants.utils import schema_context
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .token import email_verification_token
logger = logging.getLogger(__name__)
User = get_user_model()


def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'username','contact_number','gender','profile_picture', 'role', 'is_verified')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        # Ensure username is generated if not provided
        if not attrs.get('username'):
            attrs['username'] = str(uuid.uuid4())  # Generate unique username
        
        # Ensure role is set in validated data
        if 'role' not in attrs:
            attrs['role'] = 'Doctor'  # Default role is 'Doctor'

        return attrs

    def create(self, validated_data):
        # Use the create_user method for proper password hashing
        return UserAccount.objects.create_user(**validated_data)


# class UserListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserAccount
#         fields = ['email']

class UserAccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    last_login_ip = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = UserAccount
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email', 'profile_picture',
            'gender', 'contact_number', 'role', 'is_active','is_verified', 'is_staff', 'is_superuser',
            'last_login_ip', 'login_count', 'last_activity', 'is_high_engagement',
            'average_session_duration'
        ]
        read_only_fields = ['id', 'login_count', 'last_activity', 'is_high_engagement', 'average_session_duration', 'username', 'email']


    def update(self, instance, validated_data):
        # Exclude fields that are causing issues or should not be updated
        validated_data.pop('username', None)
        validated_data.pop('email', None)
        validated_data.pop('last_login_ip', None)  # Exclude the problematic field

        # Update instance with remaining data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# class UserSettingsSerializer(serializers.ModelSerializer):
#     user = UserAccountSerializer()

#     class Meta:
#         model = UserSettings
#         fields = '__all__'

#     def validate(self, data):
#         user_data = data.get('user', {})
#         if 'email' in user_data:
#             user_id = self.instance.user.id if self.instance else None
#             if UserAccount.objects.filter(email=user_data['email']).exclude(id=user_id).exists():
#                 raise serializers.ValidationError({"user": {"email": "This email is already in use."}})
#         return data

#     def update(self, instance, validated_data):
#         user_data = validated_data.pop('user', None)

#         # Update non-empty user fields, excluding username
#         if user_data:
#             user = instance.user
#             user_data.pop('username', None)  # Exclude username from update
#             for attr, value in user_data.items():
#                 if value not in [None, ""]:
#                     setattr(user, attr, value)
#             user.save()

#         # Update other settings fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         return instance

class TenantRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def generate_schema_name(self):
        """
        Generate a unique schema name in the format pradoc000001, pradoc000002, etc.
        """
        next_number = 1
        while True:
            schema_name = f"pradoc{next_number:06d}"
            if not Tenant.objects.filter(schema_name=schema_name).exists():
                return schema_name
            next_number += 1

    def generate_random_domain(self):
        """
        Generate a unique random subdomain for the tenant in the format randomstring.example.com.
        """
        while True:
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            domain_name = f"{random_string}.example.com"
            if not Domain.objects.filter(domain=domain_name).exists():
                return domain_name

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a tenant and associate it with a user. Generate schema, domain, and JWT tokens.
        """
        # Step 1: Create user in the public schema
        user = UserAccount.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )

        # Step 2: Generate schema name and domain
        schema_name = self.generate_schema_name()
        domain_name = self.generate_random_domain()

        # Step 3: Create tenant
        tenant = Tenant.objects.create(
            schema_name=schema_name,
            user=user,
            is_active=True  
        )

        # Step 4: Create domain
        Domain.objects.create(
            domain=domain_name,
            tenant=tenant,
            is_primary=True,
        )

        # Step 5: Copy user to the tenant schema
        with schema_context(tenant.schema_name):
            UserAccount.objects.create_user(
                email=user.email,
                password=validated_data['password'],  # Use original password for the tenant
                is_active=True  
            )

        # Step 6: Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Step 7: Return all required data including tokens
        return {
            "user": user,
            "tenant": tenant,
            "domain": domain_name,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_verified:
                raise serializers.ValidationError("User is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def send_verification_email(self, user):
        from django.core.mail import send_mail

        try:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_verification_token.make_token(user)
            verification_url = f"http://example.com/verify-email/{uid}/{token}/"

            send_mail(
                "Verify your email",
                f"Click the link to verify your email: {verification_url}",
                "no-reply@example.com",
                [user.email],
            )
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send email: {str(e)}")
        

class UserRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = '__all__'


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = '__all__'
        read_only_fields = ["email"]  # Email is read-only

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = '__all__'
        read_only_fields = ['user']

# from .models import DoctorQualification

# class DoctorQualificationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DoctorQualification
#         fields = '__all__'
#         read_only_fields = ['id', 'user']

        
from .models import UserAccount, UserSettings, UserActivity
#Dev user management view
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['first_name', 'last_name', 'email', 'username', 'gender', 'contact_number', 'role']
        read_only_fields = ['email', 'username']

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'specialization', 'license_number', 'medical_board', 'years_of_experience',
            'qualification', 'registration_number', 'bio', 'seo_title', 'seo_description',
            'do_not_index', 'emergency_contact_number', 'is_accepting_patients',
            'consultation_fee', 'offers_telemedicine', 'available_for_emergency',
            'social_profiles', 'languages_spoken', 'consultation_languages', 'system_language', 'doctor_qualifications'       ]

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'ip_address', 'device_info', 'location_data', 'timestamp']
        read_only_fields = ['timestamp']

