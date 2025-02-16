# tenant_users/permissions/custom_auth_backend.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from tenant_users.permissions.models import UserTenantPermissions

class TenantBackend(ModelBackend):
    """Custom authentication backend for tenant-aware user authentication."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Use default authentication from ModelBackend
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            # Add any tenant-specific authentication logic here if needed
            return user
        return None

    def _get_group_permissions(self, user_obj):
        """Retrieve group permissions associated with the user's tenant."""
        if user_obj.is_anonymous:
            return set()

        user_groups_field = UserTenantPermissions._meta.get_field("groups")
        user_groups_query = f"group__{user_groups_field.related_query_name()}"
        return Permission.objects.filter(**{user_groups_query: user_obj})

    def get_user_permissions(self, user_obj, obj=None):
        """Retrieve user-specific permissions associated with the tenant context."""
        if user_obj.is_anonymous:
            return set()

        tenant_permissions = UserTenantPermissions.objects.filter(profile=user_obj)
        return Permission.objects.filter(usertenantpermissions__in=tenant_permissions)
