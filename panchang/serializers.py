"""
Serializers for Panchang API
"""
from rest_framework import serializers
from .models import Festival, ImportantDay, FestivalGallery, ImportantDayGallery, PanchangData, PanchangDailyFestival


class GalleryImageSerializer(serializers.ModelSerializer):
    """Base serializer for gallery images"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        fields = [
            'id', 'image', 'image_url', 'image_alt', 'caption', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        """Return full URL for original image if it exists"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class FestivalGallerySerializer(GalleryImageSerializer):
    """Serializer for Festival Gallery"""
    class Meta(GalleryImageSerializer.Meta):
        model = FestivalGallery


class ImportantDayGallerySerializer(GalleryImageSerializer):
    """Serializer for Important Day Gallery"""
    class Meta(GalleryImageSerializer.Meta):
        model = ImportantDayGallery


class FestivalSerializer(serializers.ModelSerializer):
    """Serializer for Festival model"""
    image_url = serializers.SerializerMethodField()
    gallery_images = FestivalGallerySerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Festival
        fields = [
            'id', 'festival_name', 'slug', 'type', 'importance', 'description', 'content',
            'image', 'image_url', 'month', 'paksha', 'tithi', 'nakshatra', 'solar_event',
            'calculation_type', 'regions', 'gallery_images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        """Return full URL for original image if it exists"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ImportantDaySerializer(serializers.ModelSerializer):
    """Serializer for ImportantDay model"""
    image_url = serializers.SerializerMethodField()
    gallery_images = ImportantDayGallerySerializer(many=True, read_only=True)

    class Meta:
        model = ImportantDay
        fields = [
            'id', 'sequence_id', 'date', 'day_name', 'slug', 'type_of', 'importance',
            'description', 'content', 'image', 'image_url',
            'is_holiday', 'regions', 'calendar_type', 'gallery_images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        """Return full URL for original image if it exists"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PanchangRequestSerializer(serializers.Serializer):
    """Serializer for Panchang calculation request"""
    date = serializers.DateField(required=True, help_text="Date in YYYY-MM-DD format")
    latitude = serializers.FloatField(required=False, default=13.0827, help_text="Latitude")
    longitude = serializers.FloatField(required=False, default=80.2707, help_text="Longitude")
    timezone = serializers.CharField(required=False, default='Asia/Kolkata', help_text="Timezone")
    profile_code = serializers.CharField(required=False, default='en', help_text="Language code: en, te, hi, ta, kn, bn, gu")
    format_profile = serializers.BooleanField(required=False, default=True, help_text="Return localized format")


class PanchangDailyFestivalSerializer(serializers.ModelSerializer):
    """Serializer for daily festivals linked to panchang data"""
    slug = serializers.CharField(source='festival_reference.slug', read_only=True)
    image_url = serializers.SerializerMethodField()
    festival_reference_id = serializers.IntegerField(source='festival_reference.id', read_only=True)

    class Meta:
        model = PanchangDailyFestival
        fields = ['festival_name', 'festival_reference_id', 'slug', 'image_url']

    def get_image_url(self, obj):
        """Return full URL for original image if it exists in the referenced festival"""
        if obj.festival_reference and obj.festival_reference.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.festival_reference.image.url)
            return obj.festival_reference.image.url
        return None


class PanchangDataSerializer(serializers.ModelSerializer):
    """Serializer for PanchangData model"""
    festivals = PanchangDailyFestivalSerializer(source='daily_festivals', many=True, read_only=True)
    createddate = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = PanchangData
        fields = [
            'id', 'date', 'lunar_month', 'paksha', 
            'thithi', 'thithi_end', 'nakshatram', 'nakshatram_end',
            'sunrise', 'sunset', 'moonrise', 'moonset',
            'varjyam_time', 'durmuhurtham_1', 'durmuhurtham_2',
            'abhijit_muhurtham', 'amrita_kalam', 'brahma_muhurtham', 
            'pratah_sandhya', 'vijaya_muhurtham', 'godhuli_muhurtham', 
            'sayam_sandhya', 'nishita_muhurtham',
            'festivals', 'createddate'
        ]

