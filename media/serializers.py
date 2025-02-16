from rest_framework import serializers
from .models import MediaItem
import mimetypes

class MediaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItem
        fields = '__all__'

    def update(self, instance, validated_data):
        file = validated_data.get('upload_file', None)
        
        # If file exists, we determine the media type from the file
        if file:
            # Use MIME type to media type conversion
            mime_type, _ = mimetypes.guess_type(file.name)
            instance.media_type = self.map_mime_to_media_type(mime_type)
        
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.alternative_text = validated_data.get('alternative_text', instance.alternative_text)
        instance.caption = validated_data.get('caption', instance.caption)
        instance.save()
        return instance

    def create(self, validated_data):
        file = validated_data.get('upload_file')
        # Assign media type based on file MIME type
        mime_type, _ = mimetypes.guess_type(file.name)
        validated_data['media_type'] = self.map_mime_to_media_type(mime_type)
        return super().create(validated_data)

    def map_mime_to_media_type(self, mime_type: str) -> str:
        # Map MIME types to the defined media type choices
        if mime_type.startswith('image/jpeg'):
            return 'jpeg'
        elif mime_type.startswith('image/png'):
            return 'png'
        elif mime_type.startswith('image/gif'):
            return 'gif'
        elif mime_type.startswith('image/webp'):
            return 'webp'
        elif mime_type.startswith('image/svg+xml'):
            return 'svg+xml'
        elif mime_type == 'audio/mpeg':
            return 'mp3'
        elif mime_type == 'video/mp4':
            return 'mp4'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            return 'xlsx'
        elif mime_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
            return 'pptx'
        elif mime_type == 'text/csv':
            return 'csv'
        else:
            return 'other'

