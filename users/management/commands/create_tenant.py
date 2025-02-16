import os
from django.core.management.base import BaseCommand
from django.apps import apps  # Import the apps utility for dynamic model loading
from users.models import UserAccount  # Only import UserAccount directly

class Command(BaseCommand):
    help = 'Create a tenant and assign a global user'

    def handle(self, *args, **options):
        # Dynamically get Tenant and Domain models to avoid circular imports
        Tenant = apps.get_model('tenant', 'Tenant')
        Domain = apps.get_model('tenant', 'Domain')

        # Read arguments from environment variables
        email = os.getenv('USER_EMAIL')
        tenant_name = os.getenv('TENANT_TITLE')
        domain_name = os.getenv('TENANT_DOMAIN')

        if not email or not tenant_name or not domain_name:
            self.stdout.write(self.style.ERROR("Please set USER_EMAIL, TENANT_TITLE, and TENANT_DOMAIN environment variables."))
            return

        # Ensure global user exists
        try:
            user = UserAccount.objects.get(email=email)
        except UserAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {email} does not exist."))
            return

        # Create Tenant
        tenant = Tenant(
            schema_name=tenant_name.lower(),
            name=tenant_name,
            clinic_name=tenant_name
        )
        tenant.save()

        # Create Domain
        domain = Domain(
            domain=domain_name,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        # Add user to tenant with access
        user.add_to_tenant(tenant, is_superuser=True)
        self.stdout.write(self.style.SUCCESS(f'Tenant "{tenant_name}" created with domain "{domain_name}" and user "{email}" assigned.'))
