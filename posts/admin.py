from django.contrib import admin
from .models import Category, Tag, Post, PostImage
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.utils.html import format_html, mark_safe
from django.utils.text import slugify
from adminsortable2.admin import SortableAdminMixin
from django.urls import reverse, path
from django.utils.http import urlencode
from .views import delete_category_image
from admin_utils import get_api_endpoint_url
from admin_api_helper import get_api_endpoint_display


# Custom form for PostAdmin to handle comma-separated tags
class CustomPostAdminForm(forms.ModelForm):
    tags_input = forms.CharField(
        label="Tags (comma-separated)",
        required=False,
        help_text="Enter tags separated by commas, e.g., 'python, django, webdev'"
    )

    class Meta:
        model = Post
        # Exclude 'tags' from default fields as we handle it via tags_input
        exclude = ('tags', 'created_at', 'updated_at')
        fields = (
            'category', 'author', 'title', 'slug', 'excerpt', 'content',
            'featured_image', 'featured_image_hash', 'meta_title',
            'meta_description', 'is_published', 'published_date',
            'tags_input' # Include the custom tags_input field here
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display category with parent > child format in dropdown
        self.fields['category'].queryset = Category.objects.select_related('parent').order_by('parent__order', 'parent__name', 'order', 'name')
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_path()
        if self.instance and self.instance.pk:
            # Populate tags_input with existing tags
            self.fields['tags_input'].initial = ", ".join(
                [tag.name for tag in self.instance.tags.all()]
            )

    def save(self, commit=True):
        # Save the Post instance first
        post = super().save(commit=False)

        # Handle tags_input
        tags_string = self.cleaned_data.get('tags_input', '')
        tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]

        if commit:
            post.save()  # Save the post instance to ensure it has a primary key

        # Clear existing tags and set new ones
        if tag_names:
            post.tags.clear()
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name, defaults={'slug': slugify(tag_name)})
                post.tags.add(tag)
        else:
            post.tags.clear()

        return post


class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('order', 'name_with_parent', 'parent', 'is_active', 'slug', 'category_image_display', 'api_url')
    list_display_links = ('name_with_parent',)
    # Note: 'order' should NOT be in list_editable when using SortableAdminMixin with drag-and-drop
    # The drag-and-drop handles ordering automatically
    parent_field = 'parent' # Keep this for hierarchical sorting
    list_select_related = ('parent',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    readonly_fields = ('category_image_display', 'api_endpoint')
    ordering = ['order'] # Re-add explicit ordering

    def name_with_parent(self, obj):
        """Display name as 'Parent > Child' format"""
        return obj.get_full_path()
    name_with_parent.short_description = 'Name'

    def get_queryset(self, request):
        """Order queryset to show parents first, then their children directly below"""
        qs = super().get_queryset(request)
        # Ensure parent is selected for proper ordering
        qs = qs.select_related('parent')
        # Order by: use parent's order for grouping (for parents, use their own order; for children, use parent's order)
        # Then by whether it's a parent (0) or child (1), then by the item's own order, then name

        from django.db.models import Case, When, IntegerField, F, Value
        from django.db.models.functions import Coalesce
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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/delete_image/', self.admin_site.admin_view(delete_category_image), name='posts_category_delete_image'),
        ]
        return custom_urls + urls

    def category_image_display(self, obj):
        html = ""
        if obj.category_image:
            html += format_html('<img src="{}" width="50" height="50" style="object-fit: cover; margin-right: 10px;" />', obj.category_image.url)
            # The URL for deleting the image will be implemented in posts/urls.py and posts/views.py
            # For now, we will use a placeholder name, which we will define later.
            delete_url = reverse('admin:posts_category_delete_image', args=[obj.pk])
            html += format_html('<a href="{}" class="button" onclick="return confirm(\'Are you sure you want to delete this image and all its versions from disk?\');">Delete Image</a>', delete_url)
        else:
            html += "No Image"
        return mark_safe(html)
    category_image_display.short_description = "Image"

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

    def get_fieldsets(self, request, obj=None):
        """Add API endpoint fieldset"""
        fieldsets = list(super().get_fieldsets(request, obj) or [])
        fieldsets.insert(0, ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this category in the API'
        }))
        return fieldsets

    def api_url(self, obj):
        """Display API URL in list view"""
        request = getattr(self, '_request', None)
        return get_api_endpoint_display(obj, request=request, for_list=True)
    api_url.short_description = "API URL"

    class Media:
        js = ('admin/js/category_colors.js',)

    def changelist_view(self, request, *args, **kwargs):
        """Store request for list view"""
        self._request = request
        return super().changelist_view(request, *args, **kwargs)


# class PostAdminForm(forms.ModelForm):
#     content = forms.CharField(widget=CKEditorWidget())

#     class Meta:
#         model = Post
#         fields = '__all__'


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ('image_file', 'caption', 'image_file_thumb_display')
    readonly_fields = ('image_file_thumb_display',)

    def image_thumbnail(self, obj):
        if obj.image_file:
            return format_html('<img src="{}" width="50" height="50" />', obj.image_file.url)
        return ""
    image_thumbnail.short_description = "Image"


class PostAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = CustomPostAdminForm  # Use the custom form
    list_display = ('order', 'title', 'category', 'author', 'is_published', 'published_date', 'featured_image_thumb_display', 'api_url') # Re-add 'order' first for drag handle, remove tree_actions
    list_display_links = ('title',)
    list_editable = ('order', 'is_published') # Make order editable again with SortableAdminMixin
    list_filter = ('is_published', 'category', 'author') # Remove 'tags' from list_filter
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'published_date'
    ordering = ['order', '-published_date'] # Keep existing ordering
    inlines = [PostImageInline]
    readonly_fields = ('featured_image_thumb_display', 'api_endpoint')
    fieldsets = (
        ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this post in the API'
        }),
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'author', 'tags_input', 'featured_image', 'featured_image_thumb_display')
        }),
        ('Images', {
            'fields': ('featured_image_hash',),
            'classes': ('collapse',),
            'description': 'Image sizes (small, thumb, medium, large) are automatically generated and stored in folders.'
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('SEO Information', {
            'fields': ('meta_title', 'meta_description')
        }),
        ('Publication', {
            'fields': ('is_published', 'published_date')
        }),
    )

    def post_thumbnail(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="50" height="50" />', obj.featured_image.url)
        return ""
    post_thumbnail.short_description = "Featured Image"

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


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'api_url')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('api_endpoint',)

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
        """Add API endpoint fieldset"""
        fieldsets = list(super().get_fieldsets(request, obj) or [])
        fieldsets.insert(0, ('API Endpoint', {
            'fields': ('api_endpoint',),
            'description': 'View this tag in the API'
        }))
        return fieldsets


admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Post, PostAdmin)
