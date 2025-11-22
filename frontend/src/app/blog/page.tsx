"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";
import { getBlogPosts, BlogPost } from "@/lib/api/blog";

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPosts() {
      try {
        setLoading(true);
        const data = await getBlogPosts();
        setPosts(data);
      } catch (err) {
        setError("Failed to load blog posts");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchPosts();
  }, []);

  return (
    <main className="relative min-h-screen flex flex-col">
      {/* World Map Background */}
      <WorldMapAnimation />

      {/* NAVBAR */}
      <Navbar />

      <div className="relative z-10 flex-grow py-10 px-4 flex flex-col items-center">
        <section className="max-w-3xl w-full">
          <h1 className="text-4xl font-bold text-blue-800 mb-8 text-center">Our Blog</h1>

          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
              <p className="mt-4 text-gray-600">Loading blog posts...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg text-center">
              {error}
            </div>
          )}

          {!loading && !error && posts.length === 0 && (
            <div className="bg-blue-50 border border-blue-200 text-blue-700 px-6 py-8 rounded-lg text-center">
              <p className="text-lg">No blog posts available yet. Check back soon!</p>
            </div>
          )}

          {!loading && !error && posts.length > 0 && (
            <div className="space-y-8">
              {posts.map((post) => (
                <article key={post.slug} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition group">
                  <h2 className="text-2xl font-bold text-blue-700 mb-1 group-hover:text-blue-900 transition">
                    <Link href={`/blog/${post.slug}`}>{post.title}</Link>
                  </h2>
                  <div className="flex items-center gap-3 text-sm text-gray-500 mb-2">
                    <span>By {post.author_name}</span>
                    <span>•</span>
                    <time>{new Date(post.published_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</time>
                    <span>•</span>
                    <span>{post.views_count} views</span>
                  </div>
                  <p className="text-gray-700 mb-4">{post.excerpt}</p>
                  <Link href={`/blog/${post.slug}`} className="text-blue-600 hover:underline font-semibold">Read More →</Link>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
