from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, BlogCategoryViewSet, BlogTagViewSet
from .admin_views import (
    custom_admin_dashboard,
    custom_admin_posts,
    custom_admin_post_create,
    custom_admin_post_edit,
    custom_admin_post_delete,
)

router = DefaultRouter()
router.register(r'posts', BlogPostViewSet, basename='blogpost')
router.register(r'categories', BlogCategoryViewSet, basename='blogcategory')
router.register(r'tags', BlogTagViewSet, basename='blogtag')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),

    # Custom Admin URLs
    path('admin-panel/', custom_admin_dashboard, name='custom_admin_dashboard'),
    path('admin-panel/posts/', custom_admin_posts, name='custom_admin_posts'),
    path('admin-panel/posts/create/', custom_admin_post_create, name='custom_admin_post_create'),
    path('admin-panel/posts/<int:post_id>/edit/', custom_admin_post_edit, name='custom_admin_post_edit'),
    path('admin-panel/posts/<int:post_id>/delete/', custom_admin_post_delete, name='custom_admin_post_delete'),
]
