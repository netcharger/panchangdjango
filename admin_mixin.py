"""
Django Admin Mixin to add API endpoint links to admin detail pages
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from admin_utils import get_api_endpoint_url, get_api_endpoint_with_examples


class APIEndpointMixin:
    """Mixin to add API endpoint field to Django Admin"""
    
    api_endpoint_field_name = 'api_endpoint'
    
    def get_readonly_fields(self, request, obj=None):
        """Add API endpoint to readonly fields"""
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.append(self.api_endpoint_field_name)
        return readonly
    
    def api_endpoint(self, obj):
        """Display API endpoint link"""
        if not obj or not hasattr(obj, 'pk') or not obj.pk:
            return format_html('<span style="color: #888;">API available after saving.</span>')
        
        # Try to get request from admin instance if available
        request = getattr(self, '_request', None)
        
        # Get the base API URL
        api_url = get_api_endpoint_url(obj, request=request)
        
        if not api_url:
            return format_html('<span style="color: #888;">No API endpoint configured for this model.</span>')
        
        # Build absolute URL - ensure it starts with / for relative URLs
        if not api_url.startswith('http'):
            if not api_url.startswith('/'):
                api_url = '/' + api_url
        
        return format_html(
            '<a href="{}" target="_blank" style="font-weight: bold; color: #417690;">📌 View API</a>',
            api_url
        )
    api_endpoint.short_description = "API Endpoint"
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request in instance for use in api_endpoint method"""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)


def add_api_endpoint_to_admin(model_admin_class):
    """Decorator/helper to add API endpoint field to an existing admin class"""
    # Add the method
    def api_endpoint(self, obj):
        """Display API endpoint link"""
        if not obj or not hasattr(obj, 'pk') or not obj.pk:
            return format_html('<span style="color: #888;">API available after saving.</span>')
        
        request = getattr(self, '_request', None)
        api_url = get_api_endpoint_url(obj, request=request)
        
        if not api_url:
            return format_html('<span style="color: #888;">No API endpoint configured for this model.</span>')
        
        if not api_url.startswith('http'):
            if not api_url.startswith('/'):
                api_url = '/' + api_url
        
        return format_html(
            '<a href="{}" target="_blank" style="font-weight: bold; color: #417690;">📌 View API</a>',
            api_url
        )
    api_endpoint.short_description = "API Endpoint"
    
    # Add the method to the class
    model_admin_class.api_endpoint = api_endpoint
    
    # Store request for use in api_endpoint
    original_changeform_view = model_admin_class.changeform_view
    
    def changeform_view(self, request, *args, **kwargs):
        self._request = request
        return original_changeform_view(self, request, *args, **kwargs)
    
    model_admin_class.changeform_view = changeform_view
    
    # Modify get_readonly_fields to include api_endpoint
    original_get_readonly_fields = model_admin_class.get_readonly_fields
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(original_get_readonly_fields(request, obj))
        readonly.append('api_endpoint')
        return readonly
    
    model_admin_class.get_readonly_fields = get_readonly_fields
    
    return model_admin_class

