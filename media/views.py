from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import MediaItem
from .serializers import MediaItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework import generics
import boto3
from django.conf import settings
import os
from django.utils import timezone
import uuid
from PIL import Image  # Import the Pillow library to handle images






class MediaItemPagination(PageNumberPagination):
    page_size = 5  # Adjust this based on how many items you want per page
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_image(request, media_id):
    media_item = MediaItem.objects.get(id=media_id)

    # Retrieve the uploaded file from the request
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file uploaded"}, status=400)

    # Delete the original file from S3 (optional, but not necessary if overwriting)
    delete_from_s3(media_item.upload_file.url)

    # Upload the new file to S3 with the same file path
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    file_path = media_item.upload_file.name  # Keep the original path

    # Upload the new image to S3 with the same path (overwriting the existing file)
    try:
        s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, file_path)
    except Exception as e:
        return Response({"error": f"Failed to upload file: {str(e)}"}, status=500)

    # Update the media item's timestamp to reflect the new upload
    media_item.timestamp = timezone.now()
    media_item.save()

    # Return the updated media item data
    serializer = MediaItemSerializer(media_item)
    return Response(serializer.data, status=200)



# Function to delete file from S3
def delete_from_s3(file_url):
    s3 = boto3.client('s3', 
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME)

    # Extract the S3 bucket and the file path from the file URL
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    reg_name=settings.AWS_S3_REGION_NAME

    file_key = file_url.replace(f"https://{bucket_name}.s3.{reg_name}.amazonaws.com/", "")

    try:
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        return True
    except Exception as e:
        print(f"Error deleting file from S3: {e}")
        return False

@api_view(['GET'])
def get_available_dates(request):
    available_dates = (
        MediaItem.objects.annotate(
            year=ExtractYear('timestamp'),
            month=ExtractMonth('timestamp')
        )
        .values('year', 'month')
        .annotate(count=Count('id'))
        .order_by('-year', '-month')
    )

    # No need to convert month to string; keep it numeric (e.g., '10' for October)
    formatted_dates = [
        {
            'year': date['year'],       # The year is already an integer
            'month': date['month'],     # Keep the month as a number
            'count': date['count'],     # Count of media items in that month
        }
        for date in available_dates
    ]

    return Response(formatted_dates)


@api_view(['GET'])
def get_media_item(request, media_id):
    try:
        media_item = MediaItem.objects.get(id=media_id)
        serializer = MediaItemSerializer(media_item)
        return Response(serializer.data, status=200)
    except MediaItem.DoesNotExist:
        return Response({"detail": "Media item not found"}, status=404)



@api_view(['GET', 'POST'])
def media_list_create_view(request):
    search_query = request.query_params.get('search', '')
    media_type = request.query_params.get('media_type', 'all')
    date_filter = request.query_params.get('date', 'all')  # The date filter passed from the frontend

    # Start with all media items
    media_items = MediaItem.objects.all()

    # Apply search filter if a search query exists
    if search_query:
        media_items = media_items.filter(
            Q(alternative_text__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(caption__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(upload_file__icontains=search_query)
        )

    # Apply media type filter based on substrings
    if media_type != 'all':
        if media_type == 'image':
            media_items = media_items.filter(media_type__icontains='image')
        elif media_type == 'audio':
            media_items = media_items.filter(media_type__icontains='audio')
        elif media_type == 'video':
            media_items = media_items.filter(media_type__icontains='video')
        elif media_type == 'document':
            media_items = media_items.filter(media_type__in=[
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/pdf',
                'application/vnd.oasis.opendocument.text',
                'application/vnd.apple.pages',
                'application/rtf',
            ])
        elif media_type == 'spreadsheet':
            media_items = media_items.filter(media_type__in=[
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            ])
        elif media_type == 'archive':
            media_items = media_items.filter(media_type__in=[
                'application/x-gzip',
                'application/zip',
                'application/x-7z-compressed',
                'application/x-tar',
            ])

    # Apply date filter if a specific date is selected
    if date_filter != 'all':
        try:
            year, month = map(int, date_filter.split('-'))  # Expecting date in 'YYYY-MM' format
            media_items = media_items.filter(
                timestamp__year=year,
                timestamp__month=month
            )
        except ValueError:
            # Handle invalid date format if needed
            pass

    # Order media items by 'timestamp' in descending order
    media_items = media_items.order_by('-timestamp')

    # Paginate the results
    paginator = MediaItemPagination()
    result_page = paginator.paginate_queryset(media_items, request)
    serializer = MediaItemSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)




@api_view(['GET', 'PUT', 'DELETE'])
def media_detail_view(request, pk):
    media_item = get_object_or_404(MediaItem, pk=pk)

    if request.method == 'DELETE':
        # First, delete the file from S3
        if delete_from_s3(media_item.upload_file.url):  # Assuming upload_file is a FileField
            # If successful, delete the item from the database
            media_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Failed to delete file from S3."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'GET':
        serializer = MediaItemSerializer(media_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Handle PUT requests (for updating media details)
        serializer = MediaItemSerializer(media_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_media(request):
    file = request.FILES.get('file')
    media_type = request.data.get('media_type', 'other')  # Ensure the media type is received

    if not file:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    # Extract the original file name and extension
    original_filename = file.name
    name, extension = os.path.splitext(original_filename)

    # Check if a file with the same name already exists in the database
    existing_file = MediaItem.objects.filter(upload_file__contains=original_filename).exists()

    # Generate a unique file name if a file with the same name already exists
    if existing_file:
        unique_suffix = timezone.now().strftime("%Y%m%d_%H%M%S")  # Or use uuid.uuid4().hex
        new_filename = f"{name}_{unique_suffix}{extension}"
    else:
        new_filename = original_filename

    # Save the file with the new unique name
    file.name = new_filename

    # Initialize default values for image dimensions
    image_dimensions = None

    # Check if the uploaded file is an image by inspecting its extension and using Pillow
    try:
        image = Image.open(file)
        width, height = image.size
        image_dimensions = f"{width}x{height} px"  # Format as "WIDTHxHEIGHT px"
    except Exception as e:
        print(f"Error getting image dimensions: {e}")  # If not an image, no dimensions will be saved

    # Create and save the media item, including the image dimensions if available
    media_item = MediaItem(
        upload_file=file,
        media_type=media_type,
        user=request.user,
        image_dimensions=image_dimensions  # Add dimensions if available
    )
    media_item.save()

    # Serialize the saved media item
    serializer = MediaItemSerializer(media_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class MediaItemUpdateView(generics.UpdateAPIView):
    queryset = MediaItem.objects.all()
    serializer_class = MediaItemSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        # Check if the data is valid
        if not serializer.is_valid():
            # Print out the errors
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_delete_media_items(request):
    ids = request.data.get('ids', [])
    
    if not ids:
        return Response({"error": "No media items selected for deletion."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Filter the media items by their IDs
    media_items_to_delete = MediaItem.objects.filter(id__in=ids)

    if not media_items_to_delete.exists():
        return Response({"error": "No matching media items found."}, status=status.HTTP_404_NOT_FOUND)

    failed_deletions = []

    # Loop through each media item, try deleting from S3, and track failures
    for media_item in media_items_to_delete:
        if not delete_from_s3(media_item.upload_file.url):
            failed_deletions.append(media_item.id)

    # If there are failed deletions, return an error
    if failed_deletions:
        return Response({
            "error": f"Failed to delete the following media items from S3: {failed_deletions}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Delete the media items from the database
    media_items_to_delete.delete()

    return Response({"message": "Media items deleted successfully."}, status=status.HTTP_200_OK)