from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import ( 
    TenantRegistrationView, 
    VerifyTokenView, 
    SendVerificationEmailView, 
    VerifyEmailView, 
    CustomActivationView,
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    UserManagementAPIView
)
router = DefaultRouter()

urlpatterns = [
    # Social authentication via provider (e.g., Google, Facebook)
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),
    
    # JWT Token management
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('auth/verify/', VerifyTokenView.as_view(), name='token-verify'),

    
    # Logout
    path('logout/', LogoutView.as_view(), name='logout'),    

    # Include Djoser's default authentication and user management URLs
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("auth/users/activation/", CustomActivationView.as_view({"post": "activation"}), name="activation"),


    path('tenants/register/', TenantRegistrationView.as_view(), name='tenant-register'),


    path("send-verification-email/", SendVerificationEmailView.as_view(), name="send_verification_email"),
    path("verify-email/<str:uidb64>/<str:token>/", VerifyEmailView.as_view(), name="verify_email"),


    path('user-management/', UserManagementAPIView.as_view(), name='user-management'),

]
