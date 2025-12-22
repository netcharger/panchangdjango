from rest_framework import serializers
from .models import Category, Tag, Post, PostImage


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CategorySerializer(serializers.ModelSerializer):
    children = RecursiveField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'description', 'meta_title',
            'meta_description', 'category_image', 'is_active', 'get_absolute_url', 'children'
        ]
        read_only_fields = ('get_absolute_url', 'children')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified category serializer for list views - only name and slug"""
    class Meta:
        model = Category
        fields = ['name', 'slug']


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image_file', 'caption', 'uploaded_at']


class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    author = serializers.StringRelatedField()  # Displays the username of the author

    class Meta:
        model = Post
        fields = [
            'id', 'category', 'tags', 'author', 'title', 'slug', 'excerpt',
            'content', 'featured_image', 'images', 'meta_title', 'meta_description',
            'is_published', 'published_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at',)


class PostListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view - includes title, slug, image, and category"""
    category = CategoryListSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = ['title', 'id', 'slug', 'featured_image', 'category']


class PostListNoCategorySerializer(serializers.ModelSerializer):
    """Simplified serializer for list view when filtered by category - excludes category"""
    
    class Meta:
        model = Post
        fields = ['title', 'id', 'slug', 'featured_image']



