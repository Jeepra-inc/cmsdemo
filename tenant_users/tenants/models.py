import time
from django.conf import settings
from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin
from tenant_users.permissions.models import UserTenantPermissions
from django.dispatch import Signal

# Signals for various tenant-related actions
tenant_user_removed = Signal()
tenant_user_added = Signal()
tenant_user_created = Signal()
tenant_user_deleted = Signal()

# Custom Exceptions
class ExistsError(Exception):
    """Exception raised when a user is already added to a tenant."""
    pass

class InactiveError(Exception):
    pass

class DeleteError(Exception):
    pass

class SchemaError(Exception):
    pass

def schema_required(func):
    def inner(self, *args, **options):
        tenant_schema = self.schema_name
        saved_schema = connection.schema_name
        connection.set_schema(tenant_schema)
        try:
            result = func(self, *args, **options)
        finally:
            connection.set_schema(saved_schema)
        return result
    return inner

class TenantBase(TenantMixin):
    """Contains global data and settings for the tenant model."""

    slug = models.SlugField(_("Tenant URL Name"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    auto_create_schema = True
    auto_drop_schema = True

    def add_user(self, user_obj, *, is_superuser: bool = False, is_staff: bool = False):
        """Add user to tenant."""
        if self.user_set.filter(id=user_obj.pk).exists():
            raise ExistsError(f"User already added to tenant: {user_obj}")

        UserTenantPermissions.objects.create(
            profile=user_obj,
            tenant=self,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        user_obj.tenants.add(self)
        tenant_user_added.send(sender=self.__class__, user=user_obj, tenant=self)

    def remove_user(self, user_obj):
        """Remove user from tenant."""
        if user_obj.pk == self.owner.pk:
            raise DeleteError(f"Cannot remove owner from tenant: {self.owner}")

        user_tenant_perms = user_obj.usertenantpermissions
        user_tenant_perms.groups.clear()
        user_obj.tenants.remove(self)
        tenant_user_removed.send(sender=self.__class__, user=user_obj, tenant=self)

    def delete_tenant(self):
        """Mark tenant for deletion."""
        if self.schema_name == "public":
            raise ValueError("Cannot delete public tenant schema")

        for user_obj in self.user_set.all():
            if user_obj.pk == self.owner.pk:
                continue
            self.remove_user(user_obj)

        time_string = str(int(time.time()))
        new_url = f"{time_string}-{self.owner.pk!s}-{self.slug}"
        self.slug = new_url

        public_tenant = TenantBase.objects.get(schema_name="public")
        self.transfer_ownership(public_tenant.owner)

        if self.user_set.filter(pk=self.owner.pk).exists():
            self.remove_user(self.owner)

    @schema_required
    def transfer_ownership(self, new_owner):
        old_owner = self.owner
        old_owner_tenant_permissions = old_owner.usertenantpermissions
        old_owner_tenant_permissions.is_superuser = False
        old_owner_tenant_permissions.save(update_fields=["is_superuser"])

        self.owner = new_owner

        if not old_owner_tenant_permissions.groups.exists():
            self.remove_user(old_owner)

        try:
            user = self.user_set.get(pk=new_owner.pk)
            user_tenant = user.usertenantpermissions
            user_tenant.is_superuser = True
            user_tenant.save(update_fields=["is_superuser"])
        except settings.AUTH_USER_MODEL.DoesNotExist:
            self.add_user(new_owner, is_superuser=True)

        self.save(update_fields=["owner"])

    class Meta:
        abstract = True
