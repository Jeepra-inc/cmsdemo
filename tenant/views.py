import logging
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django_tenants.utils import schema_context
from .models import Domain, Tenant
from .serializers import TenantSerializer

# Set up logging
logger = logging.getLogger(__name__)

class TenantDetailView(RetrieveUpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = TenantSerializer

    def get_object(self):
        # Attempt to get tenant using tenant_id from URL kwargs
        tenant_id = self.kwargs.get("tenant_id", None)
        if tenant_id:
            try:
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                logger.info(f"Tenant found by tenant_id: {tenant}")
                return tenant
            except Tenant.DoesNotExist:
                logger.error(f"Tenant with tenant_id {tenant_id} not found.")
                raise NotFound("Tenant with the specified ID not found.")

        # Fallback to retrieving tenant using domain name
        domain_name = self.request.get_host().split(':')[0]
        logger.info(f"Processed domain: {domain_name}")

        with schema_context('public'):  # Ensure context is set to 'public'
            try:
                domain = Domain.objects.get(domain=domain_name)
                logger.info(f"Domain found: {domain}. Associated tenant: {domain.tenant}")
                return domain.tenant
            except Domain.DoesNotExist:
                logger.error(f"Domain with name {domain_name} not found.")
                raise NotFound("Domain with the specified name not found.")

    def update(self, request, *args, **kwargs):
        logger.info(f"Update request received. Data: {request.data}")
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Tenant updated successfully. Updated data: {serializer.data}")
            return Response(serializer.data)
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"detail": "An error occurred while updating the tenant."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
