import django_filters
from .models import AudioFile


class AudioFileFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    tags = django_filters.CharFilter(field_name='tags__slug', lookup_expr='exact')

    class Meta:
        model = AudioFile
        fields = ['category', 'tags', 'is_published']



