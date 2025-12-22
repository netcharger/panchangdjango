"""
Helper function to add API endpoint functionality to admin classes.

This can be imported and used in admin.py files to add API endpoint links.
"""

from django.utils.html import format_html
from admin_utils import get_api_endpoint_url


def add_api_endpoint_method(admin_class):
    """Add API endpoint method to an admin class"""
    
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
    
    # Store original changeform_view if it exists
    original_changeform_view = getattr(admin_class, 'changeform_view', None)
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request in instance for use in api_endpoint method"""
        self._request = request
        if original_changeform_view:
            return original_changeform_view(self, request, *args, **kwargs)
        return super(admin_class, self).changeform_view(request, *args, **kwargs)
    
    # Add methods to class
    admin_class.api_endpoint = api_endpoint
    admin_class.changeform_view = changeform_view
    
    return admin_class



