from django.shortcuts import render
from rest_framework import viewsets
from .models import Category, AudioFile
from .serializers import CategorySerializer, CategoryListSerializer, AudioFileSerializer
from .filters import AudioFileFilter
from .pagination import AudioFilePagination
from django_filters.rest_framework import DjangoFilterBackend


# Create your views here.


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(
        is_active=True,
        parent__isnull=True  # Only return main categories for list
    ).order_by('order')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Return main categories for list, all categories for retrieve"""
        if self.action == 'list':
            # For list, return only main categories
            return Category.objects.filter(
                is_active=True,
                parent__isnull=True
            ).order_by('order')
        else:
            # For retrieve (detail view), allow both main and subcategories
            return Category.objects.filter(is_active=True).order_by('order')
    
    def get_serializer_class(self):
        """Use simple list serializer for list action, full serializer for detail"""
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer


class AudioFileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AudioFile.objects.filter(is_published=True).select_related('category').prefetch_related('tags').order_by('-published_date')
    serializer_class = AudioFileSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_class = AudioFileFilter
    pagination_class = AudioFilePagination
