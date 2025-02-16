import os
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from django.apps import apps
from users.models import UserAccount
from tenant.models import Tenant, Domain
from tenant_users.permissions.models import UserTenantPermissions

class Command(BaseCommand):
    help = "Create a user in the public schema, then create a tenant and copy the user to that tenant with specific permissions."

    def handle(self, *args, **kwargs):
        # Step 1: Create the user in the public schema
        email = os.getenv("USER_EMAIL", "newuser@example.com")  # Replace or set in env
        password = os.getenv("USER_PASSWORD", "newpassword123")  # Replace or set in env

        # Create user in the public schema
        user, created = UserAccount.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "New",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": False,
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"User created in public schema: {user.email}"))
        else:
            self.stdout.write(self.style.WARNING(f"User already exists in public schema: {user.email}"))

        # Step 2: Create the tenant
        tenant_name = os.getenv("TENANT_NAME", "MyTenant")  # Replace or set in env
        tenant_domain = os.getenv("TENANT_DOMAIN", "mytenant.example.com")  # Replace or set in env
        tenant_schema_name = tenant_name.lower()

        # Create Tenant
        tenant, tenant_created = Tenant.objects.get_or_create(
            schema_name=tenant_schema_name,
            defaults={
                "name": tenant_name,
                "clinic_name": tenant_name,
            }
        )

        if tenant_created:
            self.stdout.write(self.style.SUCCESS(f"Tenant created with schema name: {tenant_schema_name}"))

            # Create Domain for the tenant
            Domain.objects.get_or_create(
                domain=tenant_domain,
                tenant=tenant,
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS(f"Domain '{tenant_domain}' created for tenant '{tenant_name}'"))
        else:
            self.stdout.write(self.style.WARNING(f"Tenant '{tenant_name}' already exists."))

        # Step 3: Copy the user to the tenant schema with permissions
        with schema_context(tenant_schema_name):
            user_exists_in_tenant = UserAccount.objects.filter(email=email).exists()

            if not user_exists_in_tenant:
                tenant_user, created_in_tenant = UserAccount.objects.get_or_create(
                    email=user.email,
                    defaults={
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "password": user.password,  # Copy hashed password
                    }
                )

                if created_in_tenant:
                    self.stdout.write(self.style.SUCCESS(f"User created in '{tenant_schema_name}' schema: {tenant_user.email}"))
                else:
                    self.stdout.write(self.style.WARNING(f"User already exists in '{tenant_schema_name}' schema."))

                # Assign tenant-specific permissions
                UserTenantPermissions.objects.create(
                    profile=tenant_user,
                    tenant=tenant,
                    is_staff=True,
                    is_superuser=False  # Adjust as needed
                )
                self.stdout.write(self.style.SUCCESS(f"Tenant-specific permissions added for user in '{tenant_schema_name}' schema."))
            else:
                self.stdout.write(self.style.WARNING(f"User already exists in '{tenant_schema_name}' schema and no action was needed."))
