"""
Helper functions for displaying API endpoints in Django Admin
"""
from django.utils.html import format_html
from admin_utils import get_api_endpoint_url


def get_api_endpoint_display(obj, request=None, for_list=False):
    """
    Get API endpoint display HTML for detail or list view
    
    Args:
        obj: Model instance
        request: Django request object
        for_list: If True, return compact version for list view
    
    Returns:
        HTML string for API endpoint display
    """
    if not obj or not hasattr(obj, 'pk') or not obj.pk:
        return format_html('<span style="color: #888;">API available after saving.</span>') if not for_list else "-"
    
    api_url = get_api_endpoint_url(obj, request=None)  # Don't pass request here, we'll build it ourselves
    
    if not api_url:
        return format_html('<span style="color: #888;">No API endpoint configured.</span>') if not for_list else "-"
    
    # Ensure the path starts with / to make it absolute from root
    if not api_url.startswith('http'):
        if not api_url.startswith('/'):
            api_url = '/' + api_url
    
    # Build full URL for display
    if request:
        # Get the scheme and host from request
        scheme = request.scheme
        host = request.get_host()
        full_url = f"{scheme}://{host}{api_url}"
    else:
        full_url = api_url if api_url.startswith('http') else f'http://localhost:8000{api_url}'
    
    if for_list:
        # Compact version for list view
        return format_html(
            '<code style="font-size: 11px; word-break: break-all;">{}</code>',
            full_url
        )
    else:
        # Full version for detail view
        return format_html(
            '<div style="padding: 10px; background-color: #e8f4f8; border: 1px solid #417690; border-radius: 4px; margin-bottom: 10px;">'
            '<strong style="color: #417690; display: block; margin-bottom: 5px;">API Endpoint URL:</strong>'
            '<code style="display: block; padding: 5px; background-color: white; border: 1px solid #ddd; border-radius: 3px; word-break: break-all; font-size: 13px; margin-bottom: 8px;">{}</code>'
            '<a href="{}" target="_blank" style="font-weight: bold; color: #417690; text-decoration: none;">📌 Open API Endpoint →</a>'
            '</div>',
            full_url,
            full_url
        )


def add_api_endpoint_to_admin_class(admin_class, list_display_field_name='api_url'):
    """
    Add API endpoint methods to an admin class
    
    Args:
        admin_class: Django ModelAdmin class
        list_display_field_name: Name of the method to add to list_display
    """
    
    def api_endpoint(self, obj):
        """Display API endpoint in detail view"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=False)
    api_endpoint.short_description = "API Endpoint"
    
    def api_url(self, obj):
        """Display API URL in list view"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=True)
    api_url.short_description = "API URL"
    
    # Store original changeform_view and changelist_view
    original_changeform_view = getattr(admin_class, 'changeform_view', None)
    original_changelist_view = getattr(admin_class, 'changelist_view', None)
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request for detail view"""
        self._request = request
        if original_changeform_view:
            return original_changeform_view(self, request, *args, **kwargs)
        return super(admin_class, self).changeform_view(request, *args, **kwargs)
    
    def changelist_view(self, request, *args, **kwargs):
        """Store request for list view"""
        self._request = request
        if original_changelist_view:
            return original_changelist_view(self, request, *args, **kwargs)
        return super(admin_class, self).changelist_view(request, *args, **kwargs)
    
    # Add methods to class
    admin_class.api_endpoint = api_endpoint
    admin_class.api_url = api_url
    admin_class.changeform_view = changeform_view
    admin_class.changelist_view = changelist_view
    
    return admin_class

