from django.urls import path
from .views import TenantDetailView

urlpatterns = [
    path('tenant-detail/', TenantDetailView.as_view(), name='tenant-detail'),
    path('tenants/<str:tenant_id>/', TenantDetailView.as_view(), name='tenant-detail-id'),
]
