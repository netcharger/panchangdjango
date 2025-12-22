from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CarouselImage, SiteSetting
from .serializers import CarouselImageSerializer, SiteSettingSerializer

# Create your views here.

class CarouselImageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CarouselImage.objects.filter(is_active=True).order_by('order')
    serializer_class = CarouselImageSerializer
    lookup_field = 'pk'  # Using primary key for retrieval as slug might not be unique


class SiteSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for SiteSetting model.
    Provides read-only access to site settings.
    """
    queryset = SiteSetting.objects.filter(is_active=True).order_by('key')
    serializer_class = SiteSettingSerializer
    lookup_field = 'key'  # Use key instead of pk for lookups
    
    @action(detail=False, methods=['get'])
    def as_dict(self, request):
        """
        Return all active settings as a dictionary.
        Useful for frontend to get all settings at once.
        """
        serializer = self.get_serializer(self.queryset, many=True)
        settings_dict = {}
        for item in serializer.data:
            settings_dict[item['key']] = {
                'value': item['value'],
                'value_type': item['value_type'],
                'description': item.get('description', '')
            }
        return Response(settings_dict)
