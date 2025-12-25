from django.contrib import admin
from .models import Category, AudioFile
from taggit.models import Tag
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from admin_utils import get_api_endpoint_url
from admin_api_helper import get_api_endpoint_display


admin.site.unregister(Tag) # Unregister the default taggit Tag admin

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('order', 'name_with_parent', 'parent', 'is_active', 'slug', 'api_url')
    list_display_links = ('name_with_parent',)
    # Note: 'order' should NOT be in list_editable when using SortableAdminMixin with drag-and-drop
    # The drag-and-drop handles ordering automatically
    list_editable = ('is_active',)
    parent_field = 'parent' # Keep this for hierarchical sorting
    list_select_related = ('parent',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    ordering = ['order', 'name']
    readonly_fields = ('api_endpoint',)
    
    class Media:
        js = ('admin/js/category_colors.js',)
    
    def name_with_parent(self, obj):
        """Display name as 'Parent > Child' format"""
        # audio_manager uses '-->' separator, convert to '>'
        full_path = obj.get_full_path()
        return full_path.replace(' --> ', ' > ')
    name_with_parent.short_description = 'Name'
    
    def get_queryset(self, request):
        """Order queryset to show parents first, then their children directly below"""
        qs = super().get_queryset(request)
        # Ensure parent is selected for proper ordering
        qs = qs.select_related('parent')
        # Order by: use parent's order for grouping (for parents, use their own order; for children, use parent's order)
        # Then by whether it's a parent (0) or child (1), then by the item's own order, then name
        from django.db.models import Case, When, IntegerField, F, Value, Coalesce
        return qs.annotate(
            parent_order_value=Case(
                When(parent__isnull=True, then=Coalesce(F('order'), Value(999999))),
                default=Coalesce(F('parent__order'), Value(999999)),
                output_field=IntegerField()
            ),
            is_parent=Case(
                When(parent__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('parent_order_value', 'is_parent', 'order', 'name')
    
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
    
    def get_fieldsets(self, request, obj=None):
        """Add API endpoint fieldset at top"""
        fieldsets = list(super().get_fieldsets(request, obj) or [])
        fieldsets.insert(0, ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this category in the API'
        }))
        return fieldsets

class AudioFileAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display full hierarchical path for categories
        # Order by parent order, then parent name, then child order, then child name
        self.fields['category'].queryset = Category.objects.select_related('parent').order_by('parent__order', 'parent__name', 'order', 'name')
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_path().replace(' --> ', ' > ')
        # Make published_date not required
        self.fields['published_date'].required = False

    class Meta:
        model = AudioFile
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        is_published = cleaned_data.get('is_published')
        published_date = cleaned_data.get('published_date')
        
        # If is_published is True and published_date is not set, set it to now
        if is_published and not published_date:
            cleaned_data['published_date'] = timezone.now()
        
        return cleaned_data

@admin.register(AudioFile)
class AudioFileAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = AudioFileAdminForm # Use the custom form
    list_display = ('order', 'title', 'category', 'image_display', 'publish_status_button', 'published_date', 'get_tags', 'api_url')
    list_display_links = ('title',)
    list_editable = ('order',)
    list_filter = ('is_published', 'category', 'tags')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ['order', '-published_date']
    filter_horizontal = ('tags',)
    readonly_fields = ('image_display', 'audio_player_display', 'publish_button', 'api_endpoint')
    
    class Media:
        js = ('admin/js/audio_file_publish.js',)

    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this audio file in the API'
        }),
        (None, {
            'fields': ('title', 'slug', 'category', 'mp3_file', 'audio_player_display', 'image', 'image_display', 'description', 'tags')
        }),
        ('SEO Information', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('publish_button', 'published_date', 'order'),
            'description': 'Use the "Publish/Unpublish" button to toggle publication status. Published date will be set automatically when publishing.'
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('<int:object_id>/toggle-publish/', self.admin_site.admin_view(self.toggle_publish), name='audio_manager_audiofile_toggle_publish'),
        ]
        return custom_urls + urls

    def toggle_publish(self, request, object_id):
        """Toggle the published status of an audio file"""
        audio_file = self.get_object(request, object_id)
        if audio_file:
            audio_file.is_published = not audio_file.is_published
            if audio_file.is_published and not audio_file.published_date:
                audio_file.published_date = timezone.now()
            elif not audio_file.is_published:
                # Optionally clear published_date when unpublishing
                # audio_file.published_date = None
                pass
            audio_file.save()
            
            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'is_published': audio_file.is_published,
                    'published_date': audio_file.published_date.isoformat() if audio_file.published_date else None,
                    'message': f'Audio file "{audio_file.title}" has been {"published" if audio_file.is_published else "unpublished"}.'
                })
            
            self.message_user(request, f'Audio file "{audio_file.title}" has been {"published" if audio_file.is_published else "unpublished"}.')
        return HttpResponseRedirect(reverse('admin:audio_manager_audiofile_change', args=[object_id]))

    def publish_button(self, obj):
        """Display a button to toggle publish status"""
        if obj and obj.pk:
            if obj.is_published:
                button_text = "Unpublish"
                button_class = "default unpublish-btn"
                status_text = format_html('<span style="color: green;">Currently Published</span>')
            else:
                button_text = "Publish"
                button_class = "default publish-btn"
                status_text = format_html('<span style="color: red;">Currently Unpublished</span>')
            
            toggle_url = reverse('admin:audio_manager_audiofile_toggle_publish', args=[obj.pk])
            return format_html(
                '<div class="publish-button-container">'
                '<p class="publish-status-text"><strong>Status:</strong> {}</p>'
                '<a href="{}" class="button {} publish-toggle-btn" style="margin-top: 10px;">{}</a>'
                '</div>',
                status_text,
                toggle_url,
                button_class,
                button_text
            )
        return format_html('<p><em>Save the audio file first to enable publishing.</em></p>')
    publish_button.short_description = "Publication Status"

    def publish_status_button(self, obj):
        """Display publish status with button in list view"""
        if obj.is_published:
            status = format_html('<span class="publish-status" style="color: green; font-weight: bold;">✓ Published</span>')
            button_text = "Unpublish"
            button_class = "default unpublish-btn"
        else:
            status = format_html('<span class="publish-status" style="color: red; font-weight: bold;">✗ Unpublished</span>')
            button_text = "Publish"
            button_class = "default publish-btn"
        
        toggle_url = reverse('admin:audio_manager_audiofile_toggle_publish', args=[obj.pk])
        return format_html(
            '{}<br><a href="{}" class="button {} publish-toggle-list-btn" style="margin-top: 5px; font-size: 11px;">{}</a>',
            status,
            toggle_url,
            button_class,
            button_text
        )
    publish_status_button.short_description = "Publish Status"

    def save_model(self, request, obj, form, change):
        """Override save to automatically set published_date when is_published is True"""
        if obj.is_published and not obj.published_date:
            obj.published_date = timezone.now()
        super().save_model(request, obj, form, change)

    def get_tags(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    get_tags.short_description = "Tags"

    def image_display(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "No Image"
    image_display.short_description = "Image"

    def audio_player_display(self, obj):
        if obj.mp3_file:
            return format_html('<audio controls src="{}">Your browser does not support the audio element.</audio>', obj.mp3_file.url)
        return "No Audio File"
    audio_player_display.short_description = "Audio Player"
    
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
