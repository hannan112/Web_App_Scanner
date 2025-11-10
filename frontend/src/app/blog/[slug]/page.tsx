"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import ProfileDropdown from "@/components/layout/ProfileDropdown";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";
import { getBlogPost, BlogPost } from "@/lib/api/blog";
import Script from "next/script";

export default function BlogPostPage() {
  const { isAuthenticated } = useAuth();
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPost() {
      try {
        setLoading(true);
        const data = await getBlogPost(slug);
        setPost(data);
      } catch (err) {
        setError("Failed to load blog post");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    if (slug) {
      fetchPost();
    }
  }, [slug]);

  return (
    <main className="relative min-h-screen flex flex-col">
      {/* World Map Background */}
      <WorldMapAnimation />

      {/* NAVBAR */}
      <nav className="relative z-10 flex items-center justify-between py-5 px-8 shadow bg-white/80 backdrop-blur-md">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-2xl font-bold text-blue-700">Security Scanner</Link>
          <Link href="/" className="text-gray-700 hover:text-blue-700 font-medium">Home</Link>
          <Link href="/pricing" className="text-gray-700 hover:text-blue-700 font-medium">Pricing</Link>
          <Link href="/blog" className="text-blue-700 font-medium">Blog</Link>
          <Link href="/contact" className="text-gray-700 hover:text-blue-700 font-medium">Contact</Link>
        </div>
        <div>
          {isAuthenticated ? (
            <ProfileDropdown />
          ) : (
            <Link href="/login" className="px-5 py-2 border border-blue-700 text-blue-700 font-semibold rounded hover:bg-blue-50 transition">Sign In</Link>
          )}
        </div>
      </nav>

      <div className="relative z-10 flex-grow py-10 px-4 flex flex-col items-center">
        <article className="max-w-4xl w-full">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
              <p className="mt-4 text-gray-600">Loading post...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg text-center">
              {error}
              <div className="mt-4">
                <Link href="/blog" className="text-blue-600 hover:underline font-semibold">
                  ← Back to Blog
                </Link>
              </div>
            </div>
          )}

          {!loading && !error && post && (
            <>
              <Script id="ld-json-article" type="application/ld+json"
                dangerouslySetInnerHTML={{
                  __html: JSON.stringify({
                    "@context": "https://schema.org",
                    "@type": "Article",
                    headline: post.title,
                    description: post.meta_description || post.excerpt,
                    author: { "@type": "Person", name: post.author_name },
                    datePublished: post.published_at,
                    image: post.featured_image ? [post.featured_image] : undefined,
                    mainEntityOfPage: {
                      "@type": "WebPage",
                      "@id": `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/blog/${post.slug}`,
                    },
                  })
                }}
              />
              <div className="mb-6">
                <Link href="/blog" className="text-blue-600 hover:underline font-semibold">
                  ← Back to Blog
                </Link>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-8 md:p-12">
                <h1 className="text-4xl md:text-5xl font-bold text-blue-800 mb-4">{post.title}</h1>

                <div className="flex items-center gap-4 text-gray-600 mb-6 pb-6 border-b">
                  <span>By {post.author_name}</span>
                  <span>•</span>
                  <time>{new Date(post.published_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</time>
                  <span>•</span>
                  <span>{post.views_count} views</span>
                </div>

                {post.featured_image && (
                  <div className="mb-8">
                    <img
                      src={post.featured_image}
                      alt={post.title}
                      className="w-full h-auto rounded-lg shadow-md"
                    />
                  </div>
                )}

                <div
                  className="prose prose-lg max-w-none prose-headings:text-blue-800 prose-a:text-blue-600 prose-a:hover:text-blue-800"
                  dangerouslySetInnerHTML={{ __html: post.content || '' }}
                />

                <div className="mt-12 pt-8 border-t">
                  <Link href="/blog" className="inline-block text-blue-600 hover:underline font-semibold">
                    ← Back to Blog
                  </Link>
                </div>
              </div>
            </>
          )}
        </article>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
