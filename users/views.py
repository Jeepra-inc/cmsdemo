import logging
import requests

from django.conf import settings
from djoser.conf import settings as djoser_settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authtoken.models import Token
from djoser.views import UserViewSet
from djoser.social.views import ProviderAuthView
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .serializers import ( TenantRegistrationSerializer, EmailVerificationSerializer, AccountSerializer, SettingsSerializer )
from .models import UserAccount, UserSettings
from .token import email_verification_token
UserAccount = get_user_model()

User = get_user_model()
logger = logging.getLogger(__name__)

# Utility function for setting cookies
def set_cookie(response, key, value):
    response.set_cookie(
        key,
        value,
        max_age=settings.AUTH_COOKIE_MAX_AGE,
        path=settings.AUTH_COOKIE_PATH,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        domain='.example.com',  # Share cookies across all subdomains
    )


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 201:
            set_cookie(response, 'access', response.data.get('access'))
            set_cookie(response, 'refresh', response.data.get('refresh'))
        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            # Set cookies for access and refresh tokens
            set_cookie(response, 'access', access_token)
            set_cookie(response, 'refresh', refresh_token)
        return response

    def get_user_from_token(self, token):
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            user_id = AccessToken(token)['user_id']
            return UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            return None


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            set_cookie(response, 'access', response.data.get('access'))
        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        request.data['token'] = request.COOKIES.get('access', request.data.get('token'))
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access', domain='.example.com', path='/')
        response.delete_cookie('refresh', domain='.example.com', path='/')
        return response

class CustomActivationView(UserViewSet):
    permission_classes = [AllowAny]
    def activation(self, request, *args, **kwargs):
        serializer = djoser_settings.SERIALIZERS.activation(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.is_active = True
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"auth_token": token.key}, status=status.HTTP_200_OK)
    
class VerifyTokenView(APIView):
    def post(self, request, *args, **kwargs):
        auth = JWTAuthentication()
        try:
            token = request.headers.get('Authorization').split()[1]
            validated_token = auth.get_validated_token(token)
            return Response({"message": "Token is valid"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        

class SendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                serializer.send_verification_email(user)
                return Response({"message": "Verification email sent."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                return Response({"error": "Failed to send verification email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST)

        if email_verification_token.check_token(user, token):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            return Response({"message": "Email successfully verified."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)



class TenantRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        logger.info("Tenant registration started with data: %s", request.data)
        serializer = TenantRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.create(serializer.validated_data)
            logger.info("Tenant created successfully. Tenant: %s, User: %s", data['tenant'], data['user'])

            # Send verification email via /api/send-verification-email/
            user = data["user"]
            if not user:
                raise ValidationError("User creation failed.")

            email_payload = {"email": user.email}
            api_url = f"{settings.BASE_BACKEND_URL}/api/send-verification-email/"
            
            response = requests.post(api_url, json=email_payload)
            if response.status_code != 200:
                logger.error("Failed to send verification email. Response: %s", response.json())
                return Response({
                    "message": "Tenant created, but failed to send verification email.",
                    "error": response.json()
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            clean_domain = data['domain'].replace("http://", "").replace("https://", "")
            full_domain_url = f"http://{clean_domain}:3000"

            return Response({
                "message": "Tenant created successfully! Verification email sent.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "tenant": {
                    "schema_name": data["tenant"].schema_name,
                },
                "domain_name": full_domain_url,
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Error during tenant creation: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#Dev user api view
class UserManagementAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object_or_none(self, model, **filters):
        """Fetch object if it exists, else return None."""
        try:
            return model.objects.get(**filters)
        except model.DoesNotExist:
            return None

    def get_user(self, user_id=None):
        """Retrieve user by ID or return the logged-in user if no ID is provided."""
        if user_id is not None:
            return self.get_object_or_none(UserAccount, id=user_id)
        # If no user_id given, rely on request.user
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def get(self, request, *args, **kwargs):
        """
        Retrieve details for a specific user.
        - If `?user_id=<id>` is provided, fetch that user.
        - If not provided, fetch the currently logged-in user.
        """
        user_id = request.query_params.get('user_id')
        user = self.get_user(user_id)

        if not user:
            return Response({"error": "User not found or not authenticated."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize user data
        user_data = AccountSerializer(user).data

        # Serialize user settings if available
        user_settings = self.get_object_or_none(UserSettings, user=user)
        settings_data = SettingsSerializer(user_settings).data if user_settings else None

        response_data = {
            "user_account": user_data,
            "user_settings": settings_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        user = self.get_user(user_id)

        if not user:
            return Response({"error": "User not found or not authenticated."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            response_data = {}

            # Update UserAccount
            user_data = request.data.get('user_account')
            if user_data:
                user_serializer = AccountSerializer(user, data=user_data, partial=True)
                if user_serializer.is_valid():
                    user_serializer.save()
                    response_data['user_account'] = user_serializer.data
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Update UserSettings
            settings_data = request.data.get('user_settings')
            if settings_data:
                user_settings = self.get_object_or_none(UserSettings, user=user)
                if user_settings:
                    settings_serializer = SettingsSerializer(user_settings, data=settings_data, partial=True)
                    if settings_serializer.is_valid():
                        settings_serializer.save()
                        response_data['user_settings'] = settings_serializer.data
                    else:
                        return Response(settings_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "User settings not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        user = self.get_user(user_id)

        if not user:
            return Response({"error": "User not found or not authenticated."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            model_to_delete = request.data.get('model')

            if model_to_delete == "user_account":
                user.delete()
                return Response({"message": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

            if model_to_delete == "user_settings":
                user_settings = self.get_object_or_none(UserSettings, user=user)
                if user_settings:
                    user_settings.delete()
                    return Response({"message": "User settings deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({"error": "User settings not found."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"error": "Invalid model or ID provided."}, status=status.HTTP_400_BAD_REQUEST)