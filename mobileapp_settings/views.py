import json
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


class VersionCheckViewSet(viewsets.ViewSet):
    """
    ViewSet for version checking of different content types.
    Provides endpoints to check if splash screens and panchang files need updates.
    """

    @action(detail=False, methods=['get'])
    def content_versions(self, request):
        """
        Return version information for splash screens and panchang files.
        Used by mobile app to check if content needs to be updated.
        """
        version_data = {}

        # Get splash screen images version info
        splash_images = CarouselImage.objects.filter(is_active=True)
        if splash_images.exists():
            # Get the latest updated timestamp for splash images
            latest_splash_update = splash_images.order_by('-updated_at').first().updated_at
            version_data['splash_screens'] = {
                'last_updated': latest_splash_update.isoformat(),
                'count': splash_images.count()
            }

        # Get panchang generation info
        panchang_setting = SiteSetting.objects.filter(
            key='panchang_generation_info',
            is_active=True
        ).first()

        if panchang_setting and panchang_setting.text_value:
            try:
                panchang_info = json.loads(panchang_setting.text_value)
                version_data['panchang'] = {
                    'last_updated': panchang_info.get('generated_at'),
                    'date_generated': panchang_info.get('date_generated'),
                    'from_date': panchang_info.get('from_date'),
                    'to_date': panchang_info.get('to_date')
                }
            except (json.JSONDecodeError, KeyError):
                version_data['panchang'] = {'last_updated': None}

        return Response(version_data)
