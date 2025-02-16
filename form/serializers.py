from rest_framework import serializers
from .models import Form

# Detailed serializer with all fields for detailed view
class FormSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()  # Custom field

    class Meta:
        model = Form
        fields = [
            'id', 'form_name', 'description', 'is_active', 'form_structure', 
            'form_setting', 'form_confirmation', 'form_notification', 
            'additional_setting', 'created_by'
        ]

    def get_created_by(self, obj):
        # Returns essential fields from the created_by user
        return {
            "id": obj.created_by.id,
            "email": obj.created_by.email,
            "first_name": obj.created_by.first_name,
            "last_name": obj.created_by.last_name
        }

# Lightweight serializer for list views (excludes detailed fields)
class FormListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ['id', 'form_name', 'description', 'is_active']
