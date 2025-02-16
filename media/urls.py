from django.urls import path
from . import views

from .views import MediaItemUpdateView
from .views import get_available_dates,bulk_delete_media_items



urlpatterns = [
    path('media/', views.media_list_create_view, name='media-list-create'),
    path('media/<int:pk>/', views.media_detail_view, name='media-detail'),
    path('media/<int:pk>/update/', MediaItemUpdateView.as_view(), name='media-item-update'),
    path('media/upload/', views.upload_media, name='upload_media'),
    path('media/available-dates/', get_available_dates, name='get_available_dates'),
    path('media/bulk-delete/', bulk_delete_media_items, name='bulk-delete-media'),
    path('media/<int:media_id>/update-image/', views.update_image, name='update_image'),




]
