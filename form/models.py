from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings


class Form(models.Model):
    form_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    form_structure = models.JSONField(default=dict, blank=True, null=True)
    form_setting = models.JSONField(default=dict, blank=True, null=True)
    form_confirmation = models.JSONField(default=dict, blank=True, null=True)
    form_notification = models.JSONField(default=dict, blank=True, null=True)
    additional_setting = models.JSONField(default=dict, blank=True, null=True)
    
    def __str__(self):
        return self.name
