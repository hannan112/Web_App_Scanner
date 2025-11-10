from rest_framework import serializers
from .models import BlogPost, BlogCategory, BlogTag


class BlogPostListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source='author.email', read_only=True)

    def get_author_name(self, obj):
        full_name = obj.author.get_full_name()
        if full_name:
            return full_name
        return obj.author.email.split('@')[0] if obj.author.email else 'Anonymous'

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author_name', 'author_email',
            'status', 'featured_image', 'published_at', 'views_count'
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'published_at']


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source='author.email', read_only=True)

    def get_author_name(self, obj):
        full_name = obj.author.get_full_name()
        if full_name:
            return full_name
        return obj.author.email.split('@')[0] if obj.author.email else 'Anonymous'

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'author_name', 'author_email', 'status', 'featured_image',
            'created_at', 'updated_at', 'published_at', 'views_count',
            'meta_title', 'meta_description'
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'created_at', 'updated_at', 'published_at']


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']


class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']
