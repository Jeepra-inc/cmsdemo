# views.py
from rest_framework import viewsets
from .models import Menu
from .serializers import MenuSerializer
from rest_framework.permissions import IsAuthenticated

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticated]
