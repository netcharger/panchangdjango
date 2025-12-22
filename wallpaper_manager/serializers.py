"""
Serializers for Wallpaper Manager API
"""
from rest_framework import serializers
from .models import Category, Wallpaper


class RecursiveField(serializers.Serializer):
    """Recursive field for nested children"""
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CategorySerializer(serializers.ModelSerializer):
    children = RecursiveField(many=True, read_only=True)
    wallpaper_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'description', 'image', 'is_active', 'order', 'wallpaper_count', 'children', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_wallpaper_count(self, obj):
        # If it's a subcategory (has parent), count its wallpapers
        if obj.parent:
            return obj.wallpapers.filter(is_active=True).count()
        # If it's a main category, count wallpapers in all child categories
        return Wallpaper.objects.filter(category__parent=obj, is_active=True).count()


class WallpaperSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    main_category_name = serializers.CharField(source='category.parent.name', read_only=True, allow_null=True)
    main_category_slug = serializers.CharField(source='category.parent.slug', read_only=True, allow_null=True)
    
    class Meta:
        model = Wallpaper
        fields = ['id', 'title', 'image', 'category', 'category_name', 'category_slug', 
                  'main_category_name', 'main_category_slug', 'is_active', 
                  'views_count', 'download_count', 'created_at']
        read_only_fields = ['id', 'views_count', 'download_count', 'created_at']
    
    def validate(self, data):
        """Validate that category is provided and is a subcategory (has parent)"""
        category = data.get('category')
        
        if not category:
            raise serializers.ValidationError({"category": "Category is required"})
        
        if not category.parent:
            raise serializers.ValidationError(
                {"category": f"Category '{category.name}' must be a subcategory (must have a parent category)"}
            )
        
        return data


class WallpaperListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_category_name = serializers.CharField(source='category.parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Wallpaper
        fields = ['id', 'title', 'image', 'category_name', 'main_category_name', 'views_count', 'download_count']

