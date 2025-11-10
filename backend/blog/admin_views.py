from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Sum
from .models import BlogPost


def is_staff_user(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_user)
def custom_admin_dashboard(request):
    total_posts = BlogPost.objects.count()
    published_posts = BlogPost.objects.filter(status='published').count()
    draft_posts = BlogPost.objects.filter(status='draft').count()
    total_views = BlogPost.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
    recent_posts = BlogPost.objects.all()[:5]

    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_views': total_views,
        'recent_posts': recent_posts,
    }
    return render(request, 'blog_admin/dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def custom_admin_posts(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'blog_admin/posts_list.html', {'posts': posts})


@login_required
@user_passes_test(is_staff_user)
def custom_admin_post_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug') or slugify(title)
        excerpt = request.POST.get('excerpt')
        content = request.POST.get('content')
        featured_image = request.POST.get('featured_image') or None
        status = request.POST.get('status', 'draft')
        meta_title = request.POST.get('meta_title') or ''
        meta_description = request.POST.get('meta_description') or ''

        # Create the post
        post = BlogPost.objects.create(
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            author=request.user,
            status=status,
            featured_image=featured_image,
            meta_title=meta_title,
            meta_description=meta_description,
            published_at=timezone.now() if status == 'published' else None
        )

        messages.success(request, f'Blog post "{post.title}" created successfully!')
        return redirect('custom_admin_posts')

    return render(request, 'blog_admin/post_form.html', {'post': None})


@login_required
@user_passes_test(is_staff_user)
def custom_admin_post_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.slug = request.POST.get('slug') or slugify(post.title)
        post.excerpt = request.POST.get('excerpt')
        post.content = request.POST.get('content')
        post.featured_image = request.POST.get('featured_image') or None
        post.status = request.POST.get('status', 'draft')
        post.meta_title = request.POST.get('meta_title') or ''
        post.meta_description = request.POST.get('meta_description') or ''

        # Set published_at if publishing for the first time
        if post.status == 'published' and not post.published_at:
            post.published_at = timezone.now()

        post.save()

        messages.success(request, f'Blog post "{post.title}" updated successfully!')
        return redirect('custom_admin_posts')

    return render(request, 'blog_admin/post_form.html', {'post': post})


@login_required
@user_passes_test(is_staff_user)
def custom_admin_post_delete(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)

    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.success(request, f'Blog post "{title}" deleted successfully!')

    return redirect('custom_admin_posts')
