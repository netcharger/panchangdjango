"""
Utility functions for dynamically detecting and generating API endpoints for Django Admin.

This module automatically discovers:
- Router registrations (DefaultRouter, SimpleRouter)
- ViewSet to Model mappings
- Filter backends, search fields, ordering fields
- Query parameters supported by each endpoint
"""
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import importlib
import inspect


class APIEndpointBuilder:
    """Builds API endpoints by discovering routers and viewsets"""
    
    def __init__(self):
        self._router_cache = {}
        self._viewset_cache = {}
        self._endpoint_map = {}
        self._load_all_routers()
    
    def _load_all_routers(self):
        """Load all routers from all apps"""
        # Map of URL module paths to their API prefixes from main urls.py
        url_configs = [
            ('panchang.urls', 'api/'),
            ('posts.urls', 'api/posts/'),
            ('audio_manager.urls', 'api/audio-manager/'),
            ('mobileapp_settings.urls', 'api/mobile-settings/'),
            ('wallpaper_manager.urls', 'api/wallpapers/'),
        ]
        
        for module_path, prefix in url_configs:
            try:
                module = importlib.import_module(module_path)
                # Look for router instances
                if hasattr(module, 'router'):
                    router = module.router
                    self._register_router(router, prefix)
            except ImportError as e:
                # Silently skip if module doesn't exist
                pass
    
    def _register_router(self, router, url_prefix):
        """Register a router and its viewsets"""
        if not isinstance(router, (DefaultRouter, SimpleRouter)):
            return
        
        # Extract registrations from router
        for prefix_name, viewset, basename in router.registry:
            viewset_class = viewset if inspect.isclass(viewset) else viewset.__class__
            
            # Get model from viewset
            model = self._get_model_from_viewset(viewset_class)
            
            if model:
                self._endpoint_map[model] = {
                    'viewset': viewset_class,
                    'route_name': basename or prefix_name.replace('-', ''),
                    'url_prefix': url_prefix,
                    'router_prefix': prefix_name,
                }
                self._viewset_cache[model] = viewset_class
    
    def _get_model_from_viewset(self, viewset_class):
        """Extract the model from a viewset class"""
        # Try to get model from queryset attribute
        if hasattr(viewset_class, 'queryset') and viewset_class.queryset:
            queryset = viewset_class.queryset
            if hasattr(queryset, 'model'):
                return queryset.model
        
        # Try to get model from serializer
        if hasattr(viewset_class, 'serializer_class') and viewset_class.serializer_class:
            serializer_class = viewset_class.serializer_class
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'model'):
                return serializer_class.Meta.model
        
        # Try to get model by instantiating viewset (with minimal setup)
        try:
            # Create a minimal request-like object to avoid errors
            class MinimalRequest:
                pass
            
            viewset_instance = viewset_class()
            queryset = viewset_instance.get_queryset()
            if hasattr(queryset, 'model'):
                return queryset.model
        except:
            pass
        
        return None
    
    def get_api_endpoint_for_model(self, model, instance=None, request=None):
        """Get the API endpoint URL for a model instance"""
        if model not in self._endpoint_map:
            return None
        
        endpoint_info = self._endpoint_map[model]
        viewset_class = endpoint_info['viewset']
        url_prefix = endpoint_info['url_prefix']
        router_prefix = endpoint_info['router_prefix']
        
        # Get lookup field from viewset
        lookup_field = getattr(viewset_class, 'lookup_field', 'pk')
        
        # Build base URL path - ensure it starts with /
        base_path = url_prefix.rstrip('/')
        if not base_path.startswith('/'):
            base_path = '/' + base_path
        
        if instance and hasattr(instance, 'pk') and instance.pk:
            # Detail view
            if lookup_field == 'pk':
                lookup_value = instance.pk
            elif lookup_field == 'slug' and hasattr(instance, 'slug'):
                lookup_value = instance.slug
            else:
                lookup_value = getattr(instance, lookup_field, instance.pk)
            
            detail_path = f"{base_path}/{router_prefix}/{lookup_value}/"
        else:
            # List view (no instance or unsaved)
            detail_path = f"{base_path}/{router_prefix}/"
        
        # Return path only (absolute path starting with /)
        # Don't build absolute URL here - let the helper do it
        return detail_path
    
    def get_query_params_for_model(self, model):
        """Get all supported query parameters for a model's API endpoint"""
        if model not in self._viewset_cache:
            return {}
        
        viewset_class = self._viewset_cache[model]
        params = {
            'filters': [],
            'search_fields': [],
            'ordering_fields': [],
            'pagination': None,
        }
        
        # Get filter backends
        filter_backends = getattr(viewset_class, 'filter_backends', [])
        
        # Detect DjangoFilterBackend
        if DjangoFilterBackend in filter_backends:
            # Get filterset fields
            filterset_fields = getattr(viewset_class, 'filterset_fields', [])
            params['filters'].extend(filterset_fields)
            
            # Check for filterset_class
            if hasattr(viewset_class, 'filterset_class'):
                filterset_class = viewset_class.filterset_class
                if filterset_class:
                    # Get filter fields from Meta
                    if hasattr(filterset_class, 'Meta'):
                        meta = filterset_class.Meta
                        if hasattr(meta, 'fields'):
                            meta_fields = meta.fields
                            if isinstance(meta_fields, dict):
                                params['filters'].extend(meta_fields.keys())
                            elif isinstance(meta_fields, (list, tuple)):
                                params['filters'].extend(meta_fields)
                    
                    # Get declared filter fields
                    if hasattr(filterset_class, 'declared_filters'):
                        params['filters'].extend(filterset_class.declared_filters.keys())
        
        # Detect SearchFilter
        if SearchFilter in filter_backends:
            search_fields = getattr(viewset_class, 'search_fields', [])
            # Remove lookup expressions (like ^name, =name, etc.)
            clean_search_fields = []
            for field in search_fields:
                # Remove lookup prefixes/suffixes
                clean_field = field.split('^')[0].split('=')[0].split('$')[0].split('@')[0]
                clean_search_fields.append(clean_field)
            params['search_fields'] = clean_search_fields
        
        # Detect OrderingFilter
        if OrderingFilter in filter_backends:
            ordering_fields = getattr(viewset_class, 'ordering_fields', [])
            if ordering_fields == '__all__':
                # Special case - all fields can be ordered
                params['ordering_fields'] = ['any_field']
            else:
                params['ordering_fields'] = list(ordering_fields) if ordering_fields else []
        
        # Check for pagination
        pagination_class = getattr(viewset_class, 'pagination_class', None)
        if pagination_class:
            params['pagination'] = True
        
        return params
    
    def build_api_url_with_params(self, model, instance=None, base_url_override=None, request=None):
        """Build complete API URL with query parameters example"""
        if base_url_override:
            base_url = base_url_override
        else:
            base_url = self.get_api_endpoint_for_model(model, instance, request)
        
        if not base_url:
            return None
        
        params = self.get_query_params_for_model(model)
        query_parts = []
        
        # Add filter examples (limited)
        if params['filters']:
            for filter_field in params['filters'][:3]:  # Limit to 3 examples
                if filter_field not in ['is_published', 'is_active']:  # Skip boolean filters for examples
                    query_parts.append(f"{filter_field}=value")
        
        # Add search example
        if params['search_fields']:
            query_parts.append(f"search=term")
        
        # Add ordering example
        if params['ordering_fields']:
            first_field = params['ordering_fields'][0]
            query_parts.append(f"ordering=-{first_field}")
        
        # Add pagination example
        if params['pagination']:
            query_parts.append("limit=20")
        
        if query_parts:
            return f"{base_url}?{'&'.join(query_parts)}"
        
        return base_url


# Global instance
_endpoint_builder = None


def get_endpoint_builder():
    """Get or create the global endpoint builder instance"""
    global _endpoint_builder
    if _endpoint_builder is None:
        _endpoint_builder = APIEndpointBuilder()
    return _endpoint_builder


def get_api_endpoint_url(instance, request=None):
    """Get API endpoint URL for a model instance"""
    if not instance or not hasattr(instance, 'pk') or not instance.pk:
        return None
    
    builder = get_endpoint_builder()
    model = instance.__class__
    return builder.get_api_endpoint_for_model(model, instance, request)


def get_api_endpoint_with_examples(instance, request=None):
    """Get API endpoint URL with example query parameters"""
    if not instance or not hasattr(instance, 'pk') or not instance.pk:
        return None
    
    builder = get_endpoint_builder()
    model = instance.__class__
    base_url = builder.get_api_endpoint_for_model(model, instance, request)
    
    if not base_url:
        return None
    
    return builder.build_api_url_with_params(model, instance, base_url, request)

