# menu/models.py
from django.db import models

class Menu(models.Model):
    menu_name = models.CharField(max_length=100)
    menu_data = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set timestamp on creation

    def __str__(self):
        return self.menu_name
