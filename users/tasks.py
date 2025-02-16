from celery import shared_task
from .models import UserAccount
from tenant.models import Tenant

@shared_task
def delete_unverified_tenants():
    """
    Deletes tenants associated with unverified users.
    """
    unverified_users = UserAccount.objects.filter(is_verified=False, is_active=True)
    for user in unverified_users:
        tenant = Tenant.objects.filter(user=user).first()
        if tenant:
            tenant.delete()
            print(f"Deleted Tenant: {tenant.schema_name}")
