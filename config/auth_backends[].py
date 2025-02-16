# myapp/auth_backends.py

from django.contrib.auth.backends import ModelBackend
from django_tenants.utils import get_tenant_model, schema_context

class TenantBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        Tenant = get_tenant_model()
        domain = request.get_host().split(':')[0]  # Get the domain part from the request
        try:
            # Use the correct related name for the domain lookup
            tenant = Tenant.objects.get(domains__domain=domain)
            with schema_context(tenant.schema_name):
                user = super().authenticate(request, username=username, password=password, **kwargs)
                return user
        except Tenant.DoesNotExist:
            return None
