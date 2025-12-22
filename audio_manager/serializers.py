from rest_framework import serializers
from .models import Category, AudioFile
from taggit.serializers import TagListSerializerField


class RecursiveField(serializers.Serializer):
    """Recursive field for nested children"""
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CategoryListSerializer(serializers.ModelSerializer):
    """Simple serializer for listing main categories only"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'order']
        read_only_fields = ['id', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    children = RecursiveField(many=True, read_only=True)
    audio_file_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent',  'children',   'audio_file_count'
        ]
        read_only_fields = ['id', 'slug', 'parent', 'children', 'audio_file_count']

    def get_audio_file_count(self, obj):
        """Count audio files in this category and its children"""
        if obj.parent:
            # If it's a subcategory, count its audio files
            return obj.audio_files.filter(is_published=True).count()
        else:
            # If it's a main category, count audio files in all child categories
            return AudioFile.objects.filter(category__parent=obj, is_published=True).count()


class AudioFileSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagListSerializerField(read_only=True)

    class Meta:
        model = AudioFile
        fields = [
            'id', 'category', 'tags', 'title', 'slug', 'description',
            'mp3_file', 'image',

        ]
        read_only_fields = ('created_at', 'updated_at',)



