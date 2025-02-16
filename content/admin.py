from django.contrib import admin
from .models import Page

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'published_at', 'last_updated_at', 'user')
    search_fields = ('name',)
    list_filter = ('status', 'published_at')
    exclude = ('slug',)  # Exclude slug since it's non-editable and auto-generated
