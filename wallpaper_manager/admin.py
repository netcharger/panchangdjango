"""
Admin configuration for Wallpaper Manager
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.contrib.admin import SimpleListFilter
from adminsortable2.admin import SortableAdminMixin
from .models import Category, Wallpaper
from admin_utils import get_api_endpoint_url
from admin_api_helper import get_api_endpoint_display


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'order', 'name_with_parent', 'parent', 'is_active', 'slug', 'image_preview', 'wallpaper_count', 'api_url']
    list_display_links = ['name_with_parent']
    # Note: 'order' should NOT be in list_editable when using SortableAdminMixin with drag-and-drop
    # The drag-and-drop handles ordering automatically
    list_editable = ['is_active']
    parent_field = 'parent'  # For hierarchical sorting
    list_select_related = ['parent']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug', 'description']
    ordering = ['order', 'name']
    readonly_fields = ['api_endpoint']
    
    class Media:
        js = ('admin/js/category_colors.js',)
    
    def name_with_parent(self, obj):
        """Display name as 'Parent > Child' format"""
        # wallpaper_manager uses '-->' separator, convert to '>'
        full_path = obj.get_full_path()
        return full_path.replace(' --> ', ' > ')
    name_with_parent.short_description = 'Name'
    
    def get_queryset(self, request):
        """Order queryset to show parents first, then their children directly below"""
        qs = super().get_queryset(request)
        # Ensure parent is selected for proper ordering
        qs = qs.select_related('parent')
        # Order by: use parent's order for grouping (for parents, use their own order; for children, use parent's order)
        # Then by whether it's a parent (0) or child (1), then by the item's own order, then name
        from django.db.models import Case, When, IntegerField, F, Value
        from django.db.models.functions import Coalesce
        return qs.annotate(
            parent_order_value=Case(
                When(parent__isnull=True, then=Coalesce(F('order'), Value(999999))),
                default=Coalesce(F('parent__order'), Value(999999)),
                output_field=IntegerField()
            ),
            is_parent=Case(
                When(parent__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('parent_order_value', 'is_parent', 'order', 'name')
    
    def api_endpoint(self, obj):
        """Display API endpoint link and URL"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=False)
    api_endpoint.short_description = "API Endpoint"
    
    def api_url(self, obj):
        """Display API URL in list view"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=True)
    api_url.short_description = "API URL"
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request in instance for use in api_endpoint method"""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)
    
    def changelist_view(self, request, *args, **kwargs):
        """Store request for list view"""
        self._request = request
        return super().changelist_view(request, *args, **kwargs)
    
    def get_fieldsets(self, request, obj=None):
        """Add API endpoint fieldset at top"""
        fieldsets = list(super().get_fieldsets(request, obj) or [])
        fieldsets.insert(0, ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this category in the API'
        }))
        return fieldsets

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Image"

    def wallpaper_count(self, obj):
        # Count wallpapers for this category (only if it's a subcategory - has parent)
        if obj.parent:
            count = obj.wallpapers.filter(is_active=True).count()
        else:
            # For main categories, count wallpapers in all child categories
            count = Wallpaper.objects.filter(category__parent=obj, is_active=True).count()
        return count
    wallpaper_count.short_description = "Wallpapers"


class MainCategoryFilter(SimpleListFilter):
    """Filter wallpapers by main category (parent category)"""
    title = 'Main Category'
    parameter_name = 'main_category'

    def lookups(self, request, model_admin):
        """Get all main categories (categories with no parent)"""
        main_categories = Category.objects.filter(parent__isnull=True, is_active=True).order_by('order', 'name')
        return [(cat.id, cat.name) for cat in main_categories]

    def queryset(self, request, queryset):
        """Filter wallpapers by main category"""
        if self.value():
            # Filter wallpapers where category's parent matches the selected main category
            return queryset.filter(category__parent_id=self.value())
        return queryset


class SubCategoryFilter(SimpleListFilter):
    """Filter wallpapers by subcategory (category with parent)"""
    title = 'Sub Category'
    parameter_name = 'sub_category'

    def lookups(self, request, model_admin):
        """Get all subcategories (categories with parent)"""
        # If main_category filter is applied, only show subcategories for that main category
        main_category_id = request.GET.get('main_category', None)
        if main_category_id:
            subcategories = Category.objects.filter(
                parent_id=main_category_id,
                is_active=True
            ).order_by('order', 'name')
        else:
            subcategories = Category.objects.filter(
                parent__isnull=False,
                is_active=True
            ).order_by('parent__name', 'order', 'name')

        return [(cat.id, f"{cat.parent.name} → {cat.name}" if cat.parent else cat.name) for cat in subcategories]

    def queryset(self, request, queryset):
        """Filter wallpapers by subcategory"""
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


class WallpaperAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display full hierarchical path for categories
        # Only show subcategories (categories with parent) since wallpapers must use subcategories
        # Order by parent order, then parent name, then child order, then child name
        self.fields['category'].queryset = Category.objects.filter(
            parent__isnull=False, 
            is_active=True
        ).select_related('parent').order_by('parent__order', 'parent__name', 'order', 'name')
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_path().replace(' --> ', ' > ')

    class Meta:
        model = Wallpaper
        fields = '__all__'


@admin.register(Wallpaper)
class WallpaperAdmin(admin.ModelAdmin):
    form = WallpaperAdminForm
    list_display = ['id', 'title', 'image_preview', 'category', 'is_active', 'views_count', 'download_count', 'created_at', 'api_url']
    list_filter = [MainCategoryFilter, SubCategoryFilter, 'is_active', 'created_at']
    search_fields = ['title', 'image']

    class Media:
        js = ('admin/js/dependent_dropdown.js',)
    readonly_fields = ['image_hash', 'views_count', 'download_count', 'created_at', 'updated_at', 'image_preview', 'api_endpoint']
    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this wallpaper in the API'
        }),
        ('Basic Information', {
            'fields': ('title', 'image', 'image_preview', 'category', 'is_active'),
            'description': 'Category must be a subcategory (category with parent).'
        }),
        ('Statistics', {
            'fields': ('views_count', 'download_count', 'image_hash')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make category required in admin
        form.base_fields['category'].required = True
        return form

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.image.url.replace('wallpapers/', 'wallpapers/thumb/').replace(".jpg", ".webp"))
        return "No image"
    image_preview.short_description = "Preview"
    
    def api_endpoint(self, obj):
        """Display API endpoint link and URL"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=False)
    api_endpoint.short_description = "API Endpoint"
    
    def api_url(self, obj):
        """Display API URL in list view"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=True)
    api_url.short_description = "API URL"
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request in instance for use in api_endpoint method"""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)
    
    def changelist_view(self, request, *args, **kwargs):
        """Store request for list view"""
        self._request = request
        return super().changelist_view(request, *args, **kwargs)
