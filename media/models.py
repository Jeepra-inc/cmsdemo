from django.db import models
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import mimetypes
import sys
import boto3
import requests
from django.conf import settings



def generate_upload_path(instance, filename):
    client_id = 1
    client_name = 'test'
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%m')
    return f'media/{client_id}_{client_name}/media/{current_year}/{current_month}/{filename}'


def generate_thumbnail_path(instance, filename):
    client_id = 1
    client_name = 'test'
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%m')
    filename = filename.replace(' ', '_')
    return f'media/thumbnails/{client_id}_{client_name}/media/{current_year}/{current_month}/{filename}'


class MediaItem(models.Model):
    MEDIA_TYPE_CHOICES = [
    ('image/jpeg', 'JPEG'),
    ('image/png', 'PNG'),
    ('image/gif', 'GIF'),
    ('image/webp', 'WEBP'),
    ('image/svg', 'SVG+XML'),
    ('audio/mp3', 'MP3'),
    ('video/mp4', 'MP4'),
    ('document/pdf', 'PDF'),
    ('document/docx', 'DOCX'),
    ('document/pptx', 'PPTX'),
    ('document/csv', 'CSV'),
    ('spreadsheet/xlsx', 'XLSX'),
    ('other', 'Other'),
]
    upload_file = models.FileField(upload_to=generate_upload_path, blank=True, null=True)
    thumbnails = models.ImageField(upload_to=generate_thumbnail_path, blank=True, null=True)
    alternative_text = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=255, choices=MEDIA_TYPE_CHOICES, blank=True, null=True)
    image_dimensions = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Define output size and buffer for thumbnail creation
        output_size = (300, 300)
        output_thumb = BytesIO()

        # Get the uploaded file name
        uploaded_file_name = str(self.upload_file)

        # Add custom MIME types
        mimetypes.add_type('image/webp', '.webp')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')

        def check_image(filename):
            content_type, _ = mimetypes.guess_type(filename)
            if content_type and content_type.startswith('image/'):
                return True, content_type
            return False, content_type

        # Check if the file is an image and get content type
        is_image, content_type = check_image(uploaded_file_name)

        # Process the image if applicable
        if is_image:
            try:
                img = Image.open(self.upload_file)
                img.thumbnail(output_size)
                img_name = self.upload_file.name.rsplit('.', 1)[0]

                # Convert RGBA images to RGB before saving as JPEG
                if img.mode == 'RGBA' and content_type == 'image/jpeg':
                    img = img.convert('RGB')

                # Determine the format for thumbnail
                thumb_format = {
                    'image/jpeg': 'JPEG',
                    'image/png': 'PNG',
                    'image/gif': 'GIF',
                    'image/webp': 'WEBP',
                }.get(content_type, 'JPEG')  # Default to JPEG if no match

                # Save the thumbnail
                img.save(output_thumb, format=thumb_format, quality=90)
                output_thumb.seek(0)  # Ensure buffer is reset

                # Prepare the thumbnail for saving to the model
                self.thumbnails = InMemoryUploadedFile(
                    output_thumb, 'ImageField', f"{img_name}_thumb.{thumb_format.lower()}", 
                    content_type, sys.getsizeof(output_thumb), None
                )
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                raise

        # Convert InMemoryUploadedFile to BytesIO for S3
        self.upload_file.open()
        file_obj = BytesIO(self.upload_file.read())
        file_obj.seek(0)  # Ensure the file object is reset for reading

        # Set content type for file in S3 upload
        extra_args = {'ContentType': content_type, 'CacheControl': 'max-age=86400'}

        try:
            # Initialize S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Upload the file to S3
            s3.upload_fileobj(
                file_obj,
                settings.AWS_STORAGE_BUCKET_NAME,
                self.upload_file.name,
                ExtraArgs=extra_args
            )

            # Fetch file size after upload
            response = requests.head(f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.upload_file.name}")
            size_in_bytes = int(response.headers.get('Content-Length', 0))
            size_in_mb = size_in_bytes / (1024 * 1024)
            self.file_size = f'{size_in_mb:.2f} MB'

            # Save the media item
            super().save(*args, **kwargs)

        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            raise

        finally:
            # Close the file
            self.upload_file.close()
