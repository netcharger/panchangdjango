from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Tag, Post
from .serializers import CategorySerializer, TagSerializer, PostSerializer, PostListSerializer, PostListNoCategorySerializer
from .filters import PostFilter
from .pagination import PostPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        """
        Return categories ordered by 'order' field first, then by 'name'.
        This ensures the order set in the admin panel is respected.
        """
        queryset = Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('order', 'name').prefetch_related(
            Prefetch('children', queryset=Category.objects.filter(is_active=True).order_by('order', 'name'))
        )
        return queryset


@staff_member_required
def delete_category_image(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.category_image:
        # Call the method to delete files from disk
        category.delete_category_image_files()
        # Set the image field to None and save the model
        category.category_image = None
        category.save()
        messages.success(request, "Category image and all its versions deleted successfully.")
    else:
        messages.warning(request, "No image found for this category.")
    return redirect(reverse('admin:posts_category_change', args=[pk]))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    lookup_field = 'slug'


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(is_published=True).select_related('category', 'author').prefetch_related('tags', 'images').order_by('order', '-published_date')
    serializer_class = PostSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter
    pagination_class = PostPagination

    def get_serializer_class(self):
        """Use simplified serializer for list action, full serializer for detail"""
        if self.action == 'list':
            # If posts are filtered by category, exclude category from response
            if 'category' in self.request.query_params:
                return PostListNoCategorySerializer
            return PostListSerializer
        return PostSerializer

    @action(detail=False, methods=['get'], url_path='by-id/(?P<post_id>[0-9]+)')
    def by_id(self, request, post_id=None):
        """Retrieve a post by its ID"""
        try:
            post = self.queryset.get(id=post_id)
            serializer = self.get_serializer(post)
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
