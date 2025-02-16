from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameAuthenticationBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print("Authenticating with username or email:", username)  # Debug print
        try:
            # Check if the username is an email or a standard username
            user = User.objects.get(Q(email=username) | Q(username=username))
            print("User found:", user)  # Debug print
        except User.DoesNotExist:
            print("User not found")  # Debug print
            return None

        # Verify the password
        if user.check_password(password):
            print("Password is correct")  # Debug print
            return user
        print("Password is incorrect")  # Debug print
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
