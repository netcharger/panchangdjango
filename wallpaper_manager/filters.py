"""
Filters for Wallpaper Manager API
"""
import django_filters
from .models import Category, Wallpaper


class WallpaperFilter(django_filters.FilterSet):
    """
    Custom filter for wallpapers that supports filtering by main_category/sub_category slug or ID.
    - Use 'main_category' parameter with slug (e.g., main_category=shiva-god-wallpapers)
    - Use 'main_category_id' parameter with ID (e.g., main_category_id=1)
    - Use 'sub_category' parameter with slug (e.g., sub_category=mountains)
    - Use 'sub_category_id' parameter with ID (e.g., sub_category_id=5)
    """
    main_category = django_filters.CharFilter(field_name='category__parent__slug', lookup_expr='exact', help_text='Filter by main category slug')
    main_category_id = django_filters.NumberFilter(field_name='category__parent', lookup_expr='exact', help_text='Filter by main category ID')
    sub_category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact', help_text='Filter by sub category slug')
    sub_category_id = django_filters.NumberFilter(field_name='category', lookup_expr='exact', help_text='Filter by sub category ID')
    
    class Meta:
        model = Wallpaper
        fields = ['main_category', 'main_category_id', 'sub_category', 'sub_category_id', 'is_active']

