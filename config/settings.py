import os
import dotenv
from os import getenv, path
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from datetime import timedelta


# BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

# LOAD ENV VARIABLES
dotenv_file = BASE_DIR / '.env'
if path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

# ENVIRONMENT CONFIGURATION
DEVELOPMENT_MODE = getenv('DEVELOPMENT_MODE', 'False') == 'True'
DEBUG = getenv('DEBUG', 'False') == 'True'
SECRET_KEY = getenv('DJANGO_SECRET_KEY', get_random_secret_key())
ALLOWED_HOSTS = getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,jeepra.com.np,localhost,example.com,*').split(',')

# APPS
SHARED_APPS = [
    'django_tenants', 'tenant', 'tenant_users.permissions',
    'social_django', 'storages', 'djoser', 'rest_framework', 'corsheaders',
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles','appointment',
    'users', 'media', 'menu', 'form', 'content', 'taggit', 'axes','debug_toolbar','django_celery_beat','graphene_django',
]
TENANT_APPS = [
    'django.contrib.contenttypes', 'django.contrib.auth', 'django.contrib.admin', 
    'django.contrib.sessions', 'django.contrib.messages', 'users', 
    'social_django', 'djoser', 'storages', 'media', 'menu', 'form', 
    'content', 'taggit', 'appointment', 'axes',
]
INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

GRAPHENE = {
    "SCHEMA": "menu.schema.schema",  # Replace 'menu_app' with your app name
}

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'axes.middleware.AxesMiddleware',
    'corsheaders.middleware.CorsMiddleware', 
    'django_tenants.middleware.main.TenantMainMiddleware', 
    'config.middleware.TenantMiddleware', 
    'django.middleware.common.CommonMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# URLS AND WSGI
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'ebdb', 
        'USER': 'jeepra', 
        'PASSWORD': 'Jeepra123', 
        'HOST': 'awseb-e-6mbmzqxmpa-stack-awsebrdsdatabase-ue8ivfwm2uju.cb8miimwiusn.us-west-2.rds.amazonaws.com', 
        'PORT': '5432',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django_tenants.postgresql_backend',
#         'NAME': 'jeepra', 
#         'USER': 'postgres', 
#         'PASSWORD': 'Jeepra123', 
#         'HOST': 'jeepra.cb8miimwiusn.us-west-2.rds.amazonaws.com', 
#         'PORT': '5432',
#     }
# }


DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

# TEMPLATE CONFIGURATION
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', 
                'django.template.context_processors.request', 
                'django.contrib.auth.context_processors.auth', 
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# AUTHENTICATION
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',  # Add Axes Backend

    'tenant_users.permissions.backend.TenantBackend', 
    'social_core.backends.google.GoogleOAuth2', 
    'social_core.backends.facebook.FacebookOAuth2', 
    'django.contrib.auth.backends.ModelBackend',
]
AUTH_USER_MODEL = 'users.UserAccount'
TENANT_MODEL = "tenant.Tenant"
TENANT_DOMAIN_MODEL = "tenant.Domain"

# DJOSER SETTINGS
DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset?uid={uid}&token={token}', 
    'SEND_ACTIVATION_EMAIL': True, 
    'ACTIVATION_URL': 'activation/{uid}/{token}', 
    'USER_CREATE_PASSWORD_RETYPE': True, 
    'PASSWORD_RESET_CONFIRM_RETYPE': True, 
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
    "USERNAME_RESET_CONFIRM_URL": "confirm-reset-email?uid={uid}&token={token}",
    'TOKEN_MODEL': None, 
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': getenv('REDIRECT_URLS').split(','), 
    'LOGIN_FIELD': 'email', 
    'USER_ID_FIELD': 'id', 
    'EMAIL': {
        'password_reset': 'users.emails.CustomPasswordResetEmail', 
        'activation': 'users.emails.CustomActivationEmail',
    },
    'SERIALIZERS': {
        'user': 'users.serializers.CustomUserSerializer', 
        'current_user': 'users.serializers.CustomUserSerializer',

    },
    'ACTIVATION_TOKEN_LIFESPAN': timedelta(days=7),

}

# DJANGO-AXES CONFIGURATION
AXES_FAILURE_LIMIT = 3  # Number of failed attempts before lockout
AXES_COOLOFF_TIME = timedelta(seconds=30)
# AXES_ONLY_USER_FAILURES = True  # Only lock out based on user failures, not IP
AXES_IPWARE_META_PRECEDENCE_ORDER = ('HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR')

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# EMAIL CONFIGURATION
# EMAIL_BACKEND = 'django_ses.SESBackend'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = getenv('AWS_SES_FROM_EMAIL')

# AWS SES CONFIGURATION
AWS_SES_ACCESS_KEY_ID = getenv('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = getenv('AWS_SES_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = getenv('AWS_SES_REGION_NAME')
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
AWS_SES_FROM_EMAIL = getenv('AWS_SES_FROM_EMAIL')
USE_SES_V2 = True

# AWS S3 STORAGE SETTINGS
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = getenv('AWS_S3_REGION_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = getenv('AWS_S3_FILE_OVERWRITE', 'False')
AWS_S3_VERITY = getenv('AWS_S3_VERITY', 'True')
AWS_S3_ENDPOINT_URL = f'https://s3.{AWS_S3_REGION_NAME}.amazonaws.com'

# STATIC & MEDIA URLS
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# STORAGE BACKENDS
STORAGES = {
    'default': {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'},
    'staticfiles': {'BACKEND': 'storages.backends.s3boto3.S3StaticStorage'},
}

# SOCIAL AUTH SETTINGS
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv('GOOGLE_AUTH_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv('GOOGLE_AUTH_SECRET_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile', 'openid',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']

SOCIAL_AUTH_FACEBOOK_KEY = getenv('FACEBOOK_AUTH_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = getenv('FACEBOOK_AUTH_SECRET_KEY')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'email, first_name, last_name'}

# CORS SETTINGS
# Allow all subdomains of example.com
CORS_ORIGIN_REGEX_WHITELIST = [
    r"^https?:\/\/(\w+\.)?example\.com(:3000)?$"
]

# Allow localhost and 127.0.0.1 for local development
CORS_ALLOWED_ORIGINS = getenv(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:3000,http://127.0.0.1:3000',
).split(',')

CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ['http://example.com', 'http://*.example.com']


# JWT COOKIE SETTINGS
AUTH_COOKIE = 'access'
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24  # 1 day in seconds
AUTH_COOKIE_SECURE = False  # Set to False for local development if not using HTTPS
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = '/'
AUTH_COOKIE_SAMESITE = 'None'  # Required for cross-site cookies

# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['users.authentication.CustomJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',  # Limit anonymous users to 5 requests per minute
        'user': '100/minute', # Limit authenticated users to 10 requests per minute
    }
}

# DEFAULT PRIMARY KEY FIELD TYPE
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TURNSTILE_SECRET_KEY = "0x4AAAAAAA0fu2NoPZyi0mUVMjeuT8bGJwY"  # Replace with your secret key

DOMAIN = "example.com:3000"
BASE_BACKEND_URL = "http://example.com:8000"



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Change from DEBUG to INFO or WARNING
        },
    },
}


# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Using Redis as the message broker
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
