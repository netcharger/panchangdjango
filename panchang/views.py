"""
API Views for Panchang
"""
import sys
import os
import datetime
from pathlib import Path

# Add parent directory to path to import panchang_calculator
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Festival, ImportantDay
from .serializers import FestivalSerializer, ImportantDaySerializer, PanchangRequestSerializer

# Import panchang calculation functions from calculations module
try:
    from .calculations.panchangam_calculation_v2 import (
        compute_panchang_for_date,
        find_amavasya_dates_in_year,
        LOCATION as DEFAULT_LOCATION,
        TITHI_NAMES,
        PAKSHA_NAMES,
    )
except ImportError as e:
    # Fallback if import fails
    compute_panchang_for_date = None
    find_amavasya_dates_in_year = None
    DEFAULT_LOCATION = {
        "name": "Chennai",
        "region": "India",
        "tz": "Asia/Kolkata",
        "lat": 13.0827,
        "lon": 80.2707
    }
    TITHI_NAMES = []
    PAKSHA_NAMES = []
    print(f"Warning: Could not import panchang calculations: {e}")


class FestivalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing festivals.

    list: Get all festivals with filtering options
    retrieve: Get a specific festival by ID
    by_slug: Get a specific festival by slug
    """
    queryset = Festival.objects.all()
    serializer_class = FestivalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'importance', 'month', 'paksha', 'tithi', 'calculation_type']
    search_fields = ['festival_name', 'slug', 'description', 'month']
    ordering_fields = ['festival_name', 'importance', 'month']
    ordering = ['festival_name']

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def by_slug(self, request, slug=None):
        """Get a festival by slug"""
        try:
            festival = self.queryset.get(slug=slug)
            serializer = self.get_serializer(festival)
            return Response(serializer.data)
        except Festival.DoesNotExist:
            return Response({'error': 'Festival not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """Get festivals filtered by month"""
        month = request.query_params.get('month', None)
        if month:
            festivals = self.queryset.filter(month__iexact=month)
            serializer = self.get_serializer(festivals, many=True)
            return Response(serializer.data)
        return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_tithi(self, request):
        """Get festivals filtered by tithi and paksha"""
        tithi = request.query_params.get('tithi', None)
        paksha = request.query_params.get('paksha', None)

        queryset = self.queryset
        if tithi:
            queryset = queryset.filter(tithi__iexact=tithi)
        if paksha:
            queryset = queryset.filter(paksha__iexact=paksha)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ImportantDayViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing important days.

    list: Get all important days with filtering options
    retrieve: Get a specific important day by ID
    by_slug: Get a specific important day by slug
    """
    queryset = ImportantDay.objects.all()
    serializer_class = ImportantDaySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_of', 'importance', 'is_holiday', 'calendar_type']
    search_fields = ['day_name', 'slug', 'description', 'date']
    ordering_fields = ['date', 'day_name', 'importance', 'sequence_id']
    ordering = ['sequence_id', 'date', 'day_name']

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def by_slug(self, request, slug=None):
        """Get an important day by slug"""
        try:
            important_day = self.queryset.get(slug=slug)
            serializer = self.get_serializer(important_day)
            return Response(serializer.data)
        except ImportantDay.DoesNotExist:
            return Response({'error': 'Important day not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get important days for a specific date (format: DD Month, e.g., '25 December')"""
        date_str = request.query_params.get('date', None)
        if date_str:
            days = self.queryset.filter(date__iexact=date_str)
            serializer = self.get_serializer(days, many=True)
            return Response(serializer.data)
        return Response({'error': 'date parameter required (format: DD Month)'}, status=status.HTTP_400_BAD_REQUEST)


class PanchangAPIView(APIView):
    """
    API endpoint to calculate Panchang for a given date with festivals from database.

    GET /api/panchang/?date=2025-12-25&language=en
    or
    POST /api/panchang/calculate/
    {
        "date": "2025-12-25",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "timezone": "Asia/Kolkata",
        "profile_code": "te",
        "format_profile": true
    }
    """

    def _normalize_text(self, value):
        """Normalize text for matching"""
        if not value:
            return None
        return "".join(ch for ch in str(value).lower() if ch.isalpha()) or None

    def _normalize_month_name(self, month_name):
        """Normalize month name for comparison (handles variations like Phalguna/Phalgun)"""
        if not month_name:
            return None
        month_lower = month_name.lower().strip()
        # Common month name variations
        month_variations = {
            'phalguna': ['phalguna', 'phalgun'],
            'chaitra': ['chaitra', 'chaitr'],
            'vaisakha': ['vaisakha', 'vaishakha', 'vaishakh', 'vaisakh'],
            'jyaistha': ['jyaistha', 'jyestha', 'jyeshtha', 'jestha'],
            'asadha': ['asadha', 'aasadha', 'ashadha'],
            'sravana': ['sravana', 'shravana', 'shravan'],
            'bhadra': ['bhadra', 'bhadrapada', 'bhadrapad'],
            'asvina': ['asvina', 'ashvina', 'ashwin'],
            'kartika': ['kartika', 'kartik', 'karthika', 'karthigai'],
            'agrahayana': ['agrahayana', 'margashirsha', 'margasira', 'margashirsh'],
            'pausa': ['pausa', 'pausha', 'paush'],
            'magha': ['magha', 'magh'],
        }
        # Check if month matches any variation
        for standard, variations in month_variations.items():
            if month_lower in variations or month_lower == standard:
                return standard
        return month_lower

    def _fetch_festivals_from_db(self, tithi_names, paksha_name, nakshatra_names, month_names, date_obj, request):
        """Fetch festivals from database based on panchang data

        Matches festivals like SQL: WHERE (tithi IS NULL OR tithi = ?) AND (paksha IS NULL OR paksha = ?)
        AND (month IS NULL OR month IN (?)) AND (nakshatra IS NULL OR nakshatra IN (?))

        Args:
            tithi_names: List of tithi names that occur during the day
            paksha_name: Paksha name (Shukla or Krishna)
            nakshatra_names: List of nakshatra names that occur during the day
            month_names: List of month names (both Amanta and Purnimanta)
            date_obj: Date object
            request: Request object for serializer context
        """
        from django.db.models import Q
        import json

        date_str = date_obj.strftime('%Y-%m-%d')
        year = date_obj.year

        # Get all lunar/unspecified festivals first
        base_query = Q(calculation_type__in=['lunar', 'unspecified'])
        all_festivals = Festival.objects.filter(base_query)

        # Normalize paksha name for comparison
        paksha_normalized = None
        if paksha_name:
            paksha_normalized = paksha_name.replace('Paksha', '').strip().lower()

        # Use primary tithi (first one) for matching - this is the main tithi for the day
        primary_tithi = tithi_names[0] if tithi_names else None

        filtered_festivals = []
        for fest in all_festivals:
            matches = False

            # First priority: Check if festival has calculated dates for this specific date
            # This is the most accurate method
            if fest.festival_dates:
                try:
                    dates_dict = fest.festival_dates if isinstance(fest.festival_dates, dict) else json.loads(fest.festival_dates)
                    year_dates = dates_dict.get(str(year), [])
                    for date_entry in year_dates:
                        if isinstance(date_entry, dict):
                            entry_date = date_entry.get('date', '')
                        else:
                            entry_date = str(date_entry)

                        if entry_date == date_str:
                            matches = True
                            break
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

            # Second priority: Match by tithi/paksha/month/nakshatra like SQL query
            # Logic: If field is empty/null in DB, don't require it. If field exists, it must match.
            if not matches:
                matches = True

                # Match tithi: If festival has tithi, it must match primary tithi
                fest_tithi = fest.tithi.strip() if fest.tithi else None
                if fest_tithi:
                    if not primary_tithi or fest_tithi.strip() != primary_tithi.strip():
                        matches = False

                # Match paksha: If festival has paksha, it must match (if empty, don't require)
                fest_paksha = fest.paksha.strip() if fest.paksha else None
                if fest_paksha:
                    if not paksha_name:
                        matches = False
                    else:
                        fest_paksha_lower = fest_paksha.lower()
                        paksha_to_match = paksha_name.lower()
                        if paksha_normalized:
                            paksha_to_match = paksha_normalized

                        # Check both full name and normalized
                        if fest_paksha_lower != paksha_to_match and fest_paksha_lower != paksha_name.lower():
                            matches = False

                # Match month: If festival has month, it must match one of the months (with normalization)
                fest_month = fest.month.strip() if fest.month else None
                if fest_month:
                    if not month_names:
                        matches = False
                    else:
                        # Normalize festival month
                        fest_month_normalized = self._normalize_month_name(fest_month)
                        # Check against normalized month names
                        month_matches = False
                        for m in month_names:
                            if m:
                                month_normalized = self._normalize_month_name(m)
                                if fest_month_normalized == month_normalized:
                                    month_matches = True
                                    break
                        if not month_matches:
                            matches = False

                # Match nakshatra: If festival has nakshatra, it must match (optional field)
                fest_nakshatra = fest.nakshatra.strip() if fest.nakshatra else None
                if fest_nakshatra:
                    if not nakshatra_names:
                        matches = False
                    else:
                        if fest_nakshatra.strip() not in [n.strip() for n in nakshatra_names if n]:
                            matches = False

            # Verify: Even if festival_dates matched, verify tithi/month match for accuracy
            # This prevents incorrect festival_dates from matching wrong dates
            if matches and fest.festival_dates:
                # Double-check that tithi and month also match
                fest_tithi = fest.tithi.strip() if fest.tithi else None
                if fest_tithi and primary_tithi:
                    if fest_tithi.strip() != primary_tithi.strip():
                        matches = False

                fest_month = fest.month.strip() if fest.month else None
                if matches and fest_month and month_names:
                    fest_month_normalized = self._normalize_month_name(fest_month)
                    month_matches = False
                    for m in month_names:
                        if m:
                            month_normalized = self._normalize_month_name(m)
                            if fest_month_normalized == month_normalized:
                                month_matches = True
                                break
                    if not month_matches:
                        matches = False

            # Only add festival if it matches
            if matches:
                filtered_festivals.append(fest)

        # Sort festivals by importance (Major > Moderate > Minor)
        importance_order = {'Major': 0, 'Moderate': 1, 'Minor': 2}
        filtered_festivals.sort(key=lambda x: importance_order.get(x.importance, 3))

        # Serialize festivals (without gallery) - exclude gallery_images
        serializer = FestivalSerializer(filtered_festivals, many=True, context={'request': request})
        festival_data = []
        for fest in serializer.data:
            # Remove gallery_images from response
            fest_dict = {k: v for k, v in fest.items() if k != 'gallery_images'}
            if fest_dict.get('festival_name'):
                festival_data.append(fest_dict)
        return festival_data

    def _fetch_important_days_from_db(self, date_obj, request):
        """Fetch important days from database based on date"""
        date_str = date_obj.strftime("%d %B")  # Format: "25 December"
        important_days = ImportantDay.objects.filter(date__iexact=date_str)

        # Serialize important days (without gallery) - exclude gallery_images
        serializer = ImportantDaySerializer(important_days, many=True, context={'request': request})
        day_data = []
        for day in serializer.data:
            # Remove gallery_images from response
            day_dict = {k: v for k, v in day.items() if k != 'gallery_images'}
            day_data.append(day_dict)
        return day_data

    def get(self, request):
        """GET endpoint: /api/panchang/?date=2025-12-25&language=en"""
        date_str = request.query_params.get('date', None)
        language = request.query_params.get('language', 'en')

        if not date_str:
            return Response(
                {'error': 'date parameter required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if compute_panchang_for_date is None:
            return Response(
                {'error': 'Panchang calculation module not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Get location from query params or use default
        location = {
            "name": "Custom Location",
            "region": "India",
            "tz": request.query_params.get('timezone', DEFAULT_LOCATION['tz']),
            "lat": float(request.query_params.get('latitude', DEFAULT_LOCATION['lat'])),
            "lon": float(request.query_params.get('longitude', DEFAULT_LOCATION['lon'])),
        }

        try:
            # First get raw panchang data (English) for festival matching
            raw_panchang = compute_panchang_for_date(
                date_str,
                location=location,
                profile_code='en',
                format_profile=False,
                include_raw=False,
            )

            # Extract panchang data for festival matching from raw English result
            tithi_names = []  # Collect all tithis that occur during the day
            paksha_name = None
            nakshatra_names = []  # Collect all nakshatras that occur during the day
            month_names = []  # Collect both Amanta and Purnimanta months

            if isinstance(raw_panchang, dict):
                core_panchang = raw_panchang.get('core_panchang', {})
                if core_panchang:
                    # Get all tithi events for the day (not just the first one)
                    tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                    if tithi_events:
                        tithi_names = [t.get('name') for t in tithi_events if t.get('name')]
                        # Also get unique tithi names
                        tithi_names = list(set(tithi_names))

                    # Get all nakshatra events for the day
                    nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                    if nakshatra_events:
                        nakshatra_names = [n.get('name') for n in nakshatra_events if n.get('name')]
                        nakshatra_names = list(set(nakshatra_names))

                paksha_info = raw_panchang.get('Paksha', {})
                if paksha_info:
                    paksha_name = paksha_info.get('name')
                    # Normalize paksha name (remove "Paksha" suffix if present)
                    if paksha_name and 'Paksha' in paksha_name:
                        paksha_name = paksha_name.replace(' Paksha', '').strip()

                # Get both Amanta and Purnimanta months
                amanta_month = raw_panchang.get('Amanta Month', {})
                if amanta_month and amanta_month.get('name'):
                    month_names.append(amanta_month.get('name'))

                purnimanta_month = raw_panchang.get('Purnimanta Month', {})
                if purnimanta_month and purnimanta_month.get('name'):
                    month_names.append(purnimanta_month.get('name'))

                month_names = list(set(month_names))  # Remove duplicates

            # Now get localized panchang result for response
            panchang_result = compute_panchang_for_date(
                date_str,
                location=location,
                profile_code=language,
                format_profile=True,
                include_raw=False,
            )

            # Fetch festivals by default (can be disabled with festivals=false)
            festivals_param = request.query_params.get('festivals', 'true').lower()
            include_festivals = festivals_param != 'false'

            if include_festivals:
                # Fetch festivals from database using English names
                festivals = self._fetch_festivals_from_db(tithi_names, paksha_name, nakshatra_names, month_names, date_obj, request)

                # Fetch important days from database
                important_days = self._fetch_important_days_from_db(date_obj, request)

                # Combine festivals and important days
                all_festivals = festivals + important_days

                # Add festivals to panchang result
                panchang_result['festivals'] = all_festivals
            else:
                # Don't include festivals in response
                panchang_result['festivals'] = []

            return Response(panchang_result, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """POST endpoint: /api/panchang/calculate/"""
        serializer = PanchangRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if compute_panchang_for_date is None:
            return Response(
                {'error': 'Panchang calculation module not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        data = serializer.validated_data
        date_str = data['date'].strftime('%Y-%m-%d')
        date_obj = data['date']

        location = {
            "name": "Custom Location",
            "region": "India",
            "tz": data.get('timezone', DEFAULT_LOCATION['tz']),
            "lat": data.get('latitude', DEFAULT_LOCATION['lat']),
            "lon": data.get('longitude', DEFAULT_LOCATION['lon']),
        }

        try:
            profile_code = data.get('profile_code', 'en')

            # First get raw panchang data (English) for festival matching
            raw_panchang = compute_panchang_for_date(
                date_str,
                location=location,
                profile_code='en',
                format_profile=False,
                include_raw=False,
            )

            # Extract panchang data for festival matching from raw English result
            tithi_names = []  # Collect all tithis that occur during the day
            paksha_name = None
            nakshatra_names = []  # Collect all nakshatras that occur during the day
            month_names = []  # Collect both Amanta and Purnimanta months

            if isinstance(raw_panchang, dict):
                core_panchang = raw_panchang.get('core_panchang', {})
                if core_panchang:
                    # Get all tithi events for the day (not just the first one)
                    tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                    if tithi_events:
                        tithi_names = [t.get('name') for t in tithi_events if t.get('name')]
                        # Also get unique tithi names
                        tithi_names = list(set(tithi_names))

                    # Get all nakshatra events for the day
                    nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                    if nakshatra_events:
                        nakshatra_names = [n.get('name') for n in nakshatra_events if n.get('name')]
                        nakshatra_names = list(set(nakshatra_names))

                paksha_info = raw_panchang.get('Paksha', {})
                if paksha_info:
                    paksha_name = paksha_info.get('name')
                    # Normalize paksha name (remove "Paksha" suffix if present)
                    if paksha_name and 'Paksha' in paksha_name:
                        paksha_name = paksha_name.replace(' Paksha', '').strip()

                # Get both Amanta and Purnimanta months
                amanta_month = raw_panchang.get('Amanta Month', {})
                if amanta_month and amanta_month.get('name'):
                    month_names.append(amanta_month.get('name'))

                purnimanta_month = raw_panchang.get('Purnimanta Month', {})
                if purnimanta_month and purnimanta_month.get('name'):
                    month_names.append(purnimanta_month.get('name'))

                month_names = list(set(month_names))  # Remove duplicates

            # Now get localized panchang result for response
            panchang_result = compute_panchang_for_date(
                date_str,
                location=location,
                profile_code=profile_code,
                format_profile=data.get('format_profile', True),
                include_raw=False,
            )

            # Fetch festivals by default (can be disabled with festivals=false)
            festivals_param = str(data.get('festivals', 'true')).lower()
            include_festivals = festivals_param != 'false'

            if include_festivals:
                # Fetch festivals from database using English names
                festivals = self._fetch_festivals_from_db(tithi_names, paksha_name, nakshatra_names, month_names, date_obj, request)

                # Fetch important days from database
                important_days = self._fetch_important_days_from_db(date_obj, request)

                # Combine festivals and important days
                all_festivals = festivals + important_days

                # Add festivals to panchang result
                panchang_result['festivals'] = all_festivals
            else:
                # Don't include festivals in response
                panchang_result['festivals'] = []

            return Response(panchang_result, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AmavasyaAPIView(APIView):
    """
    API endpoint to get all Amavasya dates in a year.

    GET /api/panchang/amavasya/?year=2025
    """

    def get(self, request):
        year = request.query_params.get('year', None)
        if not year:
            return Response(
                {'error': 'year parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': 'year must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if find_amavasya_dates_in_year is None:
            return Response(
                {'error': 'Amavasya calculation module not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            latitude = float(request.query_params.get('latitude', DEFAULT_LOCATION['lat']))
            longitude = float(request.query_params.get('longitude', DEFAULT_LOCATION['lon']))
            timezone = request.query_params.get('timezone', DEFAULT_LOCATION['tz'])

            location = {
                "name": "Custom Location",
                "region": "India",
                "tz": timezone,
                "lat": latitude,
                "lon": longitude,
            }

            amavasya_dates = find_amavasya_dates_in_year(year, location=location, optimized=True)
            return Response({
                'year': year,
                'count': len(amavasya_dates),
                'amavasya_dates': amavasya_dates
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

