from django.contrib import admin
from .models import Category, Chant
from taggit.models import Tag
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse


admin.site.unregister(Tag)  # Unregister the default taggit Tag admin

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('order', 'name_with_parent', 'parent', 'is_active', 'slug')
    list_display_links = ('name_with_parent',)
    # Note: 'order' should NOT be in list_editable when using SortableAdminMixin with drag-and-drop
    # The drag-and-drop handles ordering automatically
    list_editable = ('is_active',)
    parent_field = 'parent'  # Keep this for hierarchical sorting
    list_select_related = ('parent',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    ordering = ['order', 'name']
    
    class Media:
        js = ('admin/js/category_colors.js',)
    
    def name_with_parent(self, obj):
        """Display name as 'Parent > Child' format"""
        # chanting uses '→' separator, convert to '>'
        full_path = obj.get_full_path()
        return full_path.replace(' → ', ' > ')
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


class ChantAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display full hierarchical path for categories
        # Order by parent order, then parent name, then child order, then child name
        self.fields['category'].queryset = Category.objects.select_related('parent').order_by('parent__order', 'parent__name', 'order', 'name')
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_path().replace(' → ', ' > ')
        # Make published_date not required
        self.fields['published_date'].required = False

    class Meta:
        model = Chant
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        is_published = cleaned_data.get('is_published')
        published_date = cleaned_data.get('published_date')
        
        # If is_published is True and published_date is not set, set it to now
        if is_published and not published_date:
            cleaned_data['published_date'] = timezone.now()
        
        return cleaned_data


@admin.register(Chant)
class ChantAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = ChantAdminForm  # Use the custom form
    list_display = ('order', 'title', 'category', 'language', 'recommended_count', 'image_display', 'publish_status_button', 'published_date', 'get_tags')
    list_display_links = ('title',)
    list_editable = ('order',)
    list_filter = ('is_published', 'category', 'tags', 'language')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ['order', '-published_date']
    filter_horizontal = ('tags',)
    readonly_fields = ('image_display', 'audio_player_display', 'publish_button')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'mp3_file', 'audio_player_display', 'image', 'image_display', 'description', 'tags')
        }),
        ('Chant Details', {
            'fields': ('language', 'recommended_count', 'audio_duration'),
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
            path('<int:object_id>/toggle-publish/', self.admin_site.admin_view(self.toggle_publish), name='chanting_chant_toggle_publish'),
        ]
        return custom_urls + urls

    def toggle_publish(self, request, object_id):
        """Toggle the published status of a chant"""
        chant = self.get_object(request, object_id)
        if chant:
            chant.is_published = not chant.is_published
            if chant.is_published and not chant.published_date:
                chant.published_date = timezone.now()
            elif not chant.is_published:
                pass
            chant.save()
            
            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'is_published': chant.is_published,
                    'published_date': chant.published_date.isoformat() if chant.published_date else None,
                    'message': f'Chant "{chant.title}" has been {"published" if chant.is_published else "unpublished"}.'
                })
            
            self.message_user(request, f'Chant "{chant.title}" has been {"published" if chant.is_published else "unpublished"}.')
        return HttpResponseRedirect(reverse('admin:chanting_chant_change', args=[object_id]))

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
            
            toggle_url = reverse('admin:chanting_chant_toggle_publish', args=[obj.pk])
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
        return format_html('<p><em>Save the chant first to enable publishing.</em></p>')
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
        
        toggle_url = reverse('admin:chanting_chant_toggle_publish', args=[obj.pk])
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



