from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission

from tenant_users.permissions.models import UserTenantPermissions


class UserBackend(ModelBackend):
    """Custom authentication backend for UserProfile.

    This backend authenticates users against the UserProfile and authorizes them
    based on UserTenantPermissions. It utilizes Facade classes to direct requests
    appropriately.

    Overrides:
        _get_group_permissions: Modified to refer to 'groups' attribute in
        UserTenantPermissions instead of the default user model's groups.

    Methods:
        _get_group_permissions: Retrieves group permissions associated with a given user.
    """

    def _get_group_permissions(self, user_obj):
        user_groups_field = UserTenantPermissions._meta.get_field(  # noqa: SLF001
            "groups"
        )
        user_groups_query = f"group__{user_groups_field.related_query_name()}"
        return Permission.objects.filter(**{user_groups_query: user_obj})


import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from tenant_users.permissions.models import UserTenantPermissions

logger = logging.getLogger(__name__)

class TenantBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"Attempting to authenticate user: {username}")
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user:
            logger.debug(f"Authenticated user: {username}")
        else:
            logger.debug(f"Failed to authenticate user: {username}")
        return user

    def _get_group_permissions(self, user_obj):
        if user_obj.is_anonymous:
            return set()

        logger.debug(f"Fetching group permissions for user: {user_obj}")
        user_groups_field = UserTenantPermissions._meta.get_field("groups")
        user_groups_query = f"group__{user_groups_field.related_query_name()}"
        
        permissions = Permission.objects.filter(**{user_groups_query: user_obj})
        logger.debug(f"Permissions fetched: {permissions}")
        
        return permissions

    def get_user_permissions(self, user_obj, obj=None):
        if user_obj.is_anonymous:
            return set()

        logger.debug(f"Fetching user-specific permissions for user: {user_obj}")
        tenant_permissions = UserTenantPermissions.objects.filter(profile=user_obj)
        
        permissions = Permission.objects.filter(usertenantpermissions__in=tenant_permissions)
        logger.debug(f"User-specific permissions fetched: {permissions}")
        
        return permissions
