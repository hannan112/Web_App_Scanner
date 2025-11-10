import type { Metadata } from 'next';
import { getBlogPost } from '@/lib/api/blog';

export async function generateMetadata(
  { params }: { params: { slug: string } }
): Promise<Metadata> {
  try {
    const post = await getBlogPost(params.slug);
    const title = post.meta_title || `${post.title} | Security Scanner`;
    const description = post.meta_description || post.excerpt || 'Blog post';

    return {
      title,
      description,
      alternates: { canonical: `/blog/${post.slug}` },
      openGraph: {
        type: 'article',
        url: `/blog/${post.slug}`,
        title,
        description,
        images: post.featured_image ? [{ url: post.featured_image }] : undefined,
        publishedTime: post.published_at,
      },
      twitter: {
        card: 'summary_large_image',
        title,
        description,
        images: post.featured_image ? [post.featured_image] : undefined,
      },
    };
  } catch {
    return {
      title: 'Blog Post | Security Scanner',
      description: 'Read our latest insights on web application security.',
    };
  }
}

export default function BlogPostLayout({ children }: { children: React.ReactNode }) {
  return children as React.ReactNode;
}


