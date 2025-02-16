# content/urls.py

from django.urls import path
from .views import (
    PageListCreateView, PageDetailView,
    PostListCreateView, PostDetailView,
    ServiceListCreateView, ServiceDetailView,
    ProductListCreateView, ProductDetailView,
)

urlpatterns = [
    # Page URLs
    path('pages/', PageListCreateView.as_view(), name='page-list-create'),
    path('pages/<int:pk>/', PageDetailView.as_view(), name='page-detail'),

    # Post URLs
    path('articles/', PostListCreateView.as_view(), name='post-list-create'),
    path('articles/<int:pk>/', PostDetailView.as_view(), name='post-detail'),

    # Service URLs
    path('services/', ServiceListCreateView.as_view(), name='service-list-create'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),

    # Product URLs
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]

