const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content?: string;
  author_name: string;
  author_email: string;
  status: string;
  featured_image?: string;
  published_at: string;
  views_count: number;
  created_at?: string;
  updated_at?: string;
  meta_title?: string;
  meta_description?: string;
}

export async function getBlogPosts(): Promise<BlogPost[]> {
  try {
    const response = await fetch(`${API_URL}/blog/posts/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API Error:", response.status, errorText);
      throw new Error(`Failed to fetch blog posts: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}

export async function getBlogPost(slug: string): Promise<BlogPost> {
  try {
    const response = await fetch(`${API_URL}/blog/posts/${slug}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API Error:", response.status, errorText);
      throw new Error(`Failed to fetch blog post: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}

export async function getPublishedBlogPosts(): Promise<BlogPost[]> {
  try {
    const response = await fetch(`${API_URL}/blog/posts/published/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API Error:", response.status, errorText);
      throw new Error(`Failed to fetch published blog posts: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}
