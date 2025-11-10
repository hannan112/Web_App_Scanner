import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

  const routes = [
    '',
    'pricing',
    'blog',
    'contact',
    'login',
    'register',
    'dashboard',
    'projects',
    'scans',
  ];

  return routes.map((route) => ({
    url: `${siteUrl}/${route}`.replace(/\/$/, '/'),
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: route === '' ? 1 : 0.7,
  }));
}


