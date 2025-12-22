from django.contrib import admin
from django.utils.html import format_html
from .models import Festival, ImportantDay, FestivalGallery, ImportantDayGallery
from admin_utils import get_api_endpoint_url
from admin_api_helper import get_api_endpoint_display


class FestivalGalleryInline(admin.TabularInline):
    """Inline admin for Festival Gallery"""
    model = FestivalGallery
    extra = 1
    fields = ('image_thumb_display', 'image', 'image_alt', 'caption', 'display_order')
    readonly_fields = ('image_thumb_display',)

    def image_thumb_display(self, obj):
        """Display thumbnail in inline"""
        if obj and obj.pk:
            return obj.image_thumb_display()
        return "Upload image to see thumbnail"
    image_thumb_display.short_description = "Thumbnail"


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ['image_thumb_display', 'festival_name', 'slug', 'type', 'importance', 'month', 'tithi', 'paksha', 'calculation_type', 'festival_dates_summary', 'api_url']
    list_filter = ['type', 'importance', 'calculation_type', 'month', 'paksha']
    search_fields = ['festival_name', 'slug', 'description', 'month', 'observation']
    readonly_fields = ['created_at', 'updated_at', 'image_thumb_display', 'festival_dates_display', 'api_endpoint']
    prepopulated_fields = {'slug': ('festival_name',)}
    inlines = [FestivalGalleryInline]
    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this festival in the API'
        }),
        ('Basic Information', {
            'fields': ('festival_name', 'slug', 'type', 'importance', 'image', 'image_thumb_display')
        }),
        ('Image Information', {
            'fields': (),
            'classes': ('collapse',),
            'description': 'Image sizes (tiny, thumb, medium, large) are automatically generated and stored in folders.'
        }),
        ('Content', {
            'fields': ('description', 'content')
        }),
        ('Lunar Calendar Details', {
            'fields': ('month', 'paksha', 'tithi', 'nakshatra', 'solar_event', 'calculation_type')
        }),
        ('Regions', {
            'fields': ('regions',)
        }),
        ('Festival Dates', {
            'fields': ('festival_dates_display', 'festival_dates'),
            'description': 'Generated festival dates (4 years before, current year, next 5 years). Use "generate_festival_dates" command to populate.'
        }),
        ('Admin Notes', {
            'fields': ('observation',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def festival_dates_summary(self, obj):
        """Display summary of festival dates in list view"""
        if obj.festival_dates and len(obj.festival_dates) > 0:
            # Just check if any dates are present in the dictionary
            if any(len(dates) > 0 for dates in obj.festival_dates.values()):
                return format_html('<span style="color: green; font-weight: bold;">Generated</span>')
        return format_html('<span style="color: orange;">Not generated</span>')
    festival_dates_summary.short_description = "Dates Summary"
    
    def festival_dates_display(self, obj):
        """Display formatted festival dates in detail view"""
        if not obj.festival_dates or obj.festival_dates == {}:
            return format_html(
                '<div style="padding: 10px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">'
                '<strong>No dates generated yet.</strong><br>'
                'Run the management command: <code>python manage.py generate_festival_dates --festival-id {}</code>'
                '</div>',
                obj.pk
            )
        
        html = '<div style="max-height: 400px; overflow-y: auto; padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;">'
        html += '<h4>Festival Dates (4 years before, current year, next 5 years)</h4>'
        
        # Sort years
        sorted_years = sorted(obj.festival_dates.keys(), key=int)
        total_dates = 0
        
        for year in sorted_years:
            dates = obj.festival_dates[year]
            total_dates += len(dates)
            html += f'<div style="margin-bottom: 15px;">'
            html += f'<strong style="color: #007bff;">{year}</strong> ({len(dates)} occurrence(s)):<br>'
            html += '<ul style="margin: 5px 0; padding-left: 20px;">'
            for date_info in dates:
                date_str = date_info.get('date', 'N/A')
                time_str = date_info.get('time', 'N/A')
                html += f'<li>{date_str} at {time_str}</li>'
            html += '</ul>'
            html += '</div>'
        
        html += f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #dee2e6;">'
        html += f'<strong>Total: {total_dates} dates across {len(sorted_years)} years</strong>'
        html += '</div>'
        html += '</div>'
        
        return format_html(html)
    festival_dates_display.short_description = "Generated Festival Dates"
    
    def next_occurrence_display(self, obj):
        """Display next occurrence dates for this festival"""
        if not obj.pk:
            return "Save festival first"
        
        # Only calculate for lunar festivals with tithi and paksha
        if obj.calculation_type not in ['lunar', 'unspecified'] or not obj.tithi or not obj.paksha:
            return "N/A (requires lunar calculation with tithi and paksha)"
        
        try:
            from .utils import calculate_future_festival_dates
            from datetime import date
            today = date.today()
            next_dates = calculate_future_festival_dates(
                tithi=obj.tithi,
                paksha=obj.paksha,
                month=obj.month if obj.month else None,
                nakshatra=obj.nakshatra if obj.nakshatra else None,
                start_date=today,
                years_ahead=2,
                max_results=3
            )
            
            if next_dates:
                dates_str = ", ".join([f"{d['date']} ({d.get('time', 'N/A')})" for d in next_dates[:3]])
                return format_html('<span style="color: green; font-weight: bold;">{}</span>', dates_str)
            else:
                return "No dates found in next 2 years"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    
    next_occurrence_display.short_description = "Next Occurrences"
    
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


class ImportantDayGalleryInline(admin.TabularInline):
    """Inline admin for Important Day Gallery"""
    model = ImportantDayGallery
    extra = 1
    fields = ('image_thumb_display', 'image', 'image_alt', 'caption', 'display_order')
    readonly_fields = ('image_thumb_display',)

    def image_thumb_display(self, obj):
        """Display thumbnail in inline"""
        if obj and obj.pk:
            return obj.image_thumb_display()
        return "Upload image to see thumbnail"
    image_thumb_display.short_description = "Thumbnail"


@admin.register(ImportantDay)
class ImportantDayAdmin(admin.ModelAdmin):
    list_display = ['image_thumb_display', 'sequence_id', 'day_name', 'slug', 'date', 'type_of', 'importance', 'is_holiday', 'api_url']
    list_filter = ['type_of', 'importance', 'is_holiday', 'calendar_type']
    search_fields = ['day_name', 'slug', 'description', 'date']
    readonly_fields = ['created_at', 'updated_at', 'image_thumb_display', 'api_endpoint']
    prepopulated_fields = {'slug': ('day_name', 'date')}
    inlines = [ImportantDayGalleryInline]
    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this important day in the API'
        }),
        ('Basic Information', {
            'fields': ('sequence_id', 'day_name', 'slug', 'date', 'type_of', 'importance', 'image', 'image_thumb_display')
        }),
        ('Image Information', {
            'fields': (),
            'classes': ('collapse',),
            'description': 'Image sizes (tiny, thumb, medium, large) are automatically generated and stored in folders.'
        }),
        ('Content', {
            'fields': ('description', 'content')
        }),
        ('Holiday Information', {
            'fields': ('is_holiday', 'regions', 'calendar_type')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
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


@admin.register(FestivalGallery)
class FestivalGalleryAdmin(admin.ModelAdmin):
    list_display = ['image_thumb_display', 'festival', 'image_alt', 'caption', 'display_order', 'created_at']
    list_filter = ['festival', 'created_at']
    search_fields = ['festival__festival_name', 'image_alt', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'image_thumb_display']
    fieldsets = (
        ('Image Information', {
            'fields': ('festival', 'image', 'image_thumb_display', 'image_alt', 'caption', 'display_order')
        }),
        ('Image Information', {
            'fields': (),
            'classes': ('collapse',),
            'description': 'Image sizes (tiny, thumb, medium, large) are automatically generated and stored in folders.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ImportantDayGallery)
class ImportantDayGalleryAdmin(admin.ModelAdmin):
    list_display = ['image_thumb_display', 'important_day', 'image_alt', 'caption', 'display_order', 'created_at']
    list_filter = ['important_day', 'created_at']
    search_fields = ['important_day__day_name', 'image_alt', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'image_thumb_display']
    fieldsets = (
        ('Image Information', {
            'fields': ('important_day', 'image', 'image_thumb_display', 'image_alt', 'caption', 'display_order')
        }),
        ('Image Information', {
            'fields': (),
            'classes': ('collapse',),
            'description': 'Image sizes (tiny, thumb, medium, large) are automatically generated and stored in folders.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )