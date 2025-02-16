from rest_framework import serializers
from .models import Page, Post, Service, Category, Product

class PageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Make user read-only

    class Meta:
        model = Page
        fields = [
            'id', 'name', 'slug', 'seo_title', 'meta_description', 
            'content', 'featured_image', 'image_id', 'status', 
            'visibility', 'page_password', 'published_at', 'last_updated_at',
            'view_count', 'user'
        ]


class PostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Make user read-only
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True
    )

    class Meta:
        model = Post
        fields = [
            'id', 'name', 'slug', 'seo_title', 'meta_description', 
            'content', 'featured_image', 'image_id', 'status', 
            'visibility', 'page_password', 'published_at', 'last_updated_at',
            'excerpt', 'allow_comments', 'categories', 'view_count', 'user'
        ]


class ServiceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Make user read-only
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True
    )

    class Meta:
        model = Service
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Make user read-only
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'seo_title', 'meta_description', 
            'description_url', 'featured_image', 'image_id', 'status', 
            'visibility', 'page_password', 'published_at', 'last_updated_at',
            'price', 'duration', 'categories', 'view_count', 'user'
        ]
