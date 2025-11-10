from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from .models import BlogPost, BlogCategory, BlogTag
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogCategorySerializer,
    BlogTagSerializer
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a post to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the author
        return obj.author == request.user


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing blog posts.
    List/Retrieve: Public (only published posts for non-authenticated users)
    Create/Update/Delete: Authenticated users only
    """
    queryset = BlogPost.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'created_at', 'views_count']
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return BlogPostListSerializer
        return BlogPostDetailSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()
        # Non-authenticated users can only see published posts
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published', published_at__lte=timezone.now())
        # Authenticated users can see their own drafts + all published posts
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                models.Q(status='published') | models.Q(author=self.request.user)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def published(self, request):
        """Get only published posts"""
        posts = self.get_queryset().filter(status='published', published_at__lte=timezone.now())
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)


class BlogCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog categories.
    """
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class BlogTagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog tags.
    """
    queryset = BlogTag.objects.all()
    serializer_class = BlogTagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
