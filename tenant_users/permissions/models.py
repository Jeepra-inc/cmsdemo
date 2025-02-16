from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from tenant_users.permissions.functional import tenant_cached_property
from tenant.models import Tenant  # Import Tenant model for ForeignKey


class PermissionsMixinFacade(PermissionsMixin):
    """A facade for Django's PermissionMixin to handle multi-tenant permissions."""

    class Meta:
        abstract = True

    @tenant_cached_property
    def tenant_perms(self):
        """Retrieve tenant-specific permissions."""
        return UserTenantPermissions.objects.get(profile_id=self.pk)

    def has_tenant_permissions(self) -> bool:
        try:
            _ = self.tenant_perms
        except UserTenantPermissions.DoesNotExist:
            return False
        return True

    @tenant_cached_property
    def is_staff(self):
        try:
            return self.tenant_perms.is_staff
        except UserTenantPermissions.DoesNotExist:
            return False

    @tenant_cached_property
    def is_superuser(self):
        try:
            return self.tenant_perms.is_superuser
        except UserTenantPermissions.DoesNotExist:
            return False

    def get_group_permissions(self, obj=None):
        try:
            return self.tenant_perms.get_group_permissions(obj)
        except UserTenantPermissions.DoesNotExist:
            return set()

    def get_all_permissions(self, obj=None):
        try:
            return self.tenant_perms.get_all_permissions(obj)
        except UserTenantPermissions.DoesNotExist:
            return set()

    def has_perm(self, perm, obj=None):
        try:
            return self.tenant_perms.has_perm(perm, obj)
        except UserTenantPermissions.DoesNotExist:
            return False

    def has_perms(self, perm_list, obj=None):
        try:
            return self.tenant_perms.has_perms(perm_list, obj)
        except UserTenantPermissions.DoesNotExist:
            return False

    def has_module_perms(self, app_label):
        try:
            return self.tenant_perms.has_module_perms(app_label)
        except UserTenantPermissions.DoesNotExist:
            return False


class TenantUserMixin(models.Model):
    """Provides multi-tenant user functionality."""

    class Meta:
        abstract = True

    def add_to_tenant(self, tenant, is_superuser=False, is_staff=False):
        UserTenantPermissions.objects.create(
            profile=self,
            tenant=tenant,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )

    def remove_from_tenant(self, tenant):
        UserTenantPermissions.objects.filter(
            profile=self,
            tenant=tenant
        ).delete()

    def get_tenant_permissions(self, tenant):
        try:
            return UserTenantPermissions.objects.get(profile=self, tenant=tenant)
        except UserTenantPermissions.DoesNotExist:
            return None


class AbstractBaseUserFacade:
    """A facade class bridging authorization and authentication models in a multi-tenant setup."""

    class Meta:
        abstract = True

    @property
    def is_active(self):
        return self.profile.is_active

    @property
    def is_anonymous(self):
        return False


class UserTenantPermissions(PermissionsMixin, AbstractBaseUserFacade):
    """Authorization model for managing per-tenant permissions in Django-tenant-users."""

    id = models.AutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name="ID",
    )

    profile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    tenant = models.ForeignKey(  # Add tenant field here
        Tenant,
        on_delete=models.CASCADE,
        related_name="user_permissions",
        help_text="The tenant to which these permissions apply.",
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='tenant_user_permissions_groups',  # Unique related name
        blank=True,
        help_text=_("The groups this user belongs to."),
        verbose_name=_("groups"),
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='tenant_user_permissions_user_permissions',  # Unique related name
        blank=True,
        help_text=_("Specific permissions for this user."),
        verbose_name=_("user permissions"),
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this tenant's admin site."),
    )

    def __str__(self):
        return str(self.profile)
