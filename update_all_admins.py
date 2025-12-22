"""
Script to add API endpoint functionality to all admin files.

This script adds the API endpoint field to all model admins that have corresponding viewsets.
Run this script to automatically update all admin files.
"""

import re
from pathlib import Path

# Common API endpoint method code
API_ENDPOINT_METHOD = '''
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
    
    def changeform_view(self, request, *args, **kwargs):
        """Store request in instance for use in api_endpoint method"""
        self._request = request
        return super().changeform_view(request, *args, **kwargs)
'''

# This script would need manual review - for now, let's manually update the files



