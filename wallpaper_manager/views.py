"""
Views for Wallpaper Manager
"""
import os
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from PIL import Image
from django.core.files import File
from io import BytesIO

from .models import Category, Wallpaper
from .serializers import CategorySerializer, WallpaperSerializer, WallpaperListSerializer
from .utils import convert_and_optimize_uploaded_image, create_image_sizes, calculate_image_hash
from .pagination import WallpaperPagination
from .filters import WallpaperFilter


def bulk_upload_page(request):
    """Render the bulk upload page"""
    # Get only main categories (parent is null)
    categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('order', 'name')
    return render(request, 'wallpaper_manager/bulk_upload.html', {'categories': categories})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing categories (hierarchical like audio_manager).
    Returns only main categories (parent is null) with their children.
    """
    queryset = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).order_by('order', 'name').prefetch_related(
        'children'
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']


class WallpaperViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing wallpapers.
    Returns 10 items per page with pagination.
    Supports filtering by main_category/sub_category ID or slug.
    If main_category_id is provided without sub_category_id, returns subcategories instead of wallpapers.
    """
    queryset = Wallpaper.objects.filter(is_active=True)
    serializer_class = WallpaperSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WallpaperFilter
    search_fields = ['title']
    ordering_fields = ['created_at', 'views_count', 'download_count']
    ordering = ['-created_at']
    pagination_class = WallpaperPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WallpaperListSerializer
        return WallpaperSerializer
    
    def list(self, request, *args, **kwargs):
        """Override list to return subcategories if main_category_id is provided without sub_category_id"""
        main_category_id = request.query_params.get('main_category_id', None)
        main_category = request.query_params.get('main_category', None)
        sub_category_id = request.query_params.get('sub_category_id', None)
        sub_category = request.query_params.get('sub_category', None)
        
        # If main_category_id/main_category is provided but no sub_category filter, return subcategories
        if (main_category_id or main_category) and not (sub_category_id or sub_category):
            if main_category_id:
                try:
                    main_category_obj = Category.objects.get(id=main_category_id, is_active=True, parent__isnull=True)
                except Category.DoesNotExist:
                    return Response({'error': 'Main category not found'}, status=status.HTTP_404_NOT_FOUND)
            elif main_category:
                try:
                    main_category_obj = Category.objects.get(slug=main_category, is_active=True, parent__isnull=True)
                except Category.DoesNotExist:
                    return Response({'error': 'Main category not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get all subcategories (children) of the main category
            subcategories = Category.objects.filter(parent=main_category_obj, is_active=True).order_by('order', 'name')
            serializer = CategorySerializer(subcategories, many=True)
            return Response(serializer.data)
        
        # Otherwise, return wallpapers as normal
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """Increment view count for a wallpaper"""
        wallpaper = self.get_object()
        wallpaper.views_count += 1
        wallpaper.save(update_fields=['views_count'])
        return Response({'views_count': wallpaper.views_count})
    
    @action(detail=True, methods=['post'])
    def increment_download(self, request, pk=None):
        """Increment download count for a wallpaper"""
        wallpaper = self.get_object()
        wallpaper.download_count += 1
        wallpaper.save(update_fields=['download_count'])
        return Response({'download_count': wallpaper.download_count})


@csrf_exempt
@require_http_methods(["POST"])
def bulk_upload_wallpapers(request):
    """
    Bulk upload wallpapers using Dropzone.js
    Expects: subcategory_id (required - must be a category with parent), and image file
    Dropzone sends files one at a time, so we handle single file uploads
    """
    import traceback
    
    try:
        subcategory_id = request.POST.get('subcategory_id')
        
        if not subcategory_id:
            return JsonResponse({
                'success': False,
                'error': 'subcategory_id is required',
                'error_detail': 'Please select a subcategory before uploading'
            }, status=400)
        
        try:
            # Get subcategory (category with parent)
            subcategory = Category.objects.get(id=subcategory_id, parent__isnull=False, is_active=True)
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Subcategory with id {subcategory_id} does not exist or is not a valid subcategory',
                'error_detail': 'Invalid subcategory selected. Subcategory must have a parent category.'
            }, status=404)
        
        # Get the uploaded file (Dropzone sends it as 'file')
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided',
                'error_detail': 'Please select an image file to upload'
            }, status=400)
        
        file = request.FILES['file']
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': f'Invalid file type: {file.content_type}',
                'error_detail': f'{file.name} is not a valid image file'
            }, status=400)
        
        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': f'File too large: {file.size} bytes',
                'error_detail': f'{file.name} exceeds the 10MB size limit'
            }, status=400)
        
        try:
            # Create wallpaper instance (category must be a subcategory - has parent)
            wallpaper = Wallpaper(
                category=subcategory,
                image=file
            )
            
            # Save to trigger image processing
            wallpaper.save()
            
            return JsonResponse({
                'success': True,
                'uploaded_count': 1,
                'uploaded_files': [{
                    'id': wallpaper.id,
                    'image_url': wallpaper.image.url,
                    'title': str(wallpaper),
                    'filename': file.name
                }]
            })
            
        except ValueError as e:
            error_msg = str(e)
            return JsonResponse({
                'success': False,
                'error': 'Validation error',
                'error_detail': error_msg,
                'filename': file.name
            }, status=400)
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Error uploading {file.name}: {error_msg}")
            print(error_trace)
            return JsonResponse({
                'success': False,
                'error': f'Error uploading {file.name}',
                'error_detail': error_msg,
                'filename': file.name
            }, status=500)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Unexpected error: {error_msg}")
        print(error_trace)
        return JsonResponse({
            'success': False,
            'error': 'Unexpected error occurred',
            'error_detail': error_msg
        }, status=500)
