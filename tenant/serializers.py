from rest_framework import serializers
from .models import Tenant

class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model.
    """
    class Meta:
        model = Tenant
        fields = '__all__'
