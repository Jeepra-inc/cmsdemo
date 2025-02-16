from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Form
from .serializers import FormSerializer, FormListSerializer

class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use the lightweight FormListSerializer for list action
        if self.action == 'list':
            return FormListSerializer
        # Use the detailed FormSerializer for other actions
        return FormSerializer

    def perform_create(self, serializer):
        # Automatically set `created_by` to the currently authenticated user
        serializer.save(created_by=self.request.user)

    # Custom action for bulk deletion
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform bulk delete and return count of deleted records
        deleted_count = Form.objects.filter(id__in=ids).delete()[0]
        return Response({"message": f"{deleted_count} forms deleted successfully"}, status=status.HTTP_200_OK)
