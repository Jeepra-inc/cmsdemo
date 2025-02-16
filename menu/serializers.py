# serializers.py
from rest_framework import serializers
from .models import Menu

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'menu_name', 'menu_data', 'created_at']  # Include created_at field
