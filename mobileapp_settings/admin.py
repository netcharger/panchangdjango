from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from .models import CarouselImage, SiteSetting
from django.utils.html import format_html
from admin_utils import get_api_endpoint_url
from admin_api_helper import get_api_endpoint_display

# Register your models here.

@admin.register(CarouselImage)
class CarouselImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('order', 'heading', 'is_active', 'link', 'image_display', 'created_at', 'api_url')
    list_display_links = ('heading',)
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('heading', 'description')
    ordering = ['order', '-created_at']
    readonly_fields = ('image_display', 'api_endpoint')

    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this carousel image in the API'
        }),
        (None, {
            'fields': ('heading', 'description', 'image', 'image_display', 'link', 'order', 'is_active')
        }),
    )

    def image_display(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "No Image"
    image_display.short_description = "Image"
    
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

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'site_setting_value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('key', 'text_value', 'description')
    readonly_fields = ('api_endpoint',)
    list_display = ('key', 'site_setting_value', 'is_active', 'updated_at', 'api_url')
    ordering = ['key']
    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this site setting in the API'
        }),
        (None, {
            'fields': ('key', 'text_value', 'image_value', 'number_value', 'boolean_value', 'url_value', 'description', 'is_active')
        }),
    )

    def site_setting_value(self, obj):
        return obj.get_value()
    site_setting_value.short_description = "Value"

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
        """Store request in instance for use in api_endpoint methods"""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)

    def changelist_view(self, request, *args, **kwargs):
        """Store request for list view"""
        self._request = request
        return super().changelist_view(request, *args, **kwargs)
