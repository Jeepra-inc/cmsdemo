from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('djoser.urls')),
    path('api/', include('users.urls')),
    path('api/', include('tenant.urls')),
    path('api/', include('media.urls')),
    path('api/', include('menu.urls')), 
    path('api/', include('form.urls')), 
    path('api/', include('content.urls')),
    path('api/', include('appointment.urls')),

] + debug_toolbar_urls()
