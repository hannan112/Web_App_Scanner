from django.contrib import admin
from django.utils import timezone
from .models import BlogPost, BlogCategory, BlogTag


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'views_count', 'created_at']
    list_filter = ['status', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ['-published_at', '-created_at']
    readonly_fields = ['views_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'status', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image',),
        }),
        ('Publishing', {
            'fields': ('published_at',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Metrics', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['publish_posts', 'unpublish_posts']

    def publish_posts(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} post(s) published successfully.')
    publish_posts.short_description = 'Publish selected posts'

    def unpublish_posts(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished successfully.')
    unpublish_posts.short_description = 'Unpublish selected posts'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new post
            obj.author = request.user
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
