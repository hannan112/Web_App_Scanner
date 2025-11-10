import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Blog',
  description:
    'Insights on web application security, vulnerability scanning, and best practices.',
  alternates: { canonical: '/blog' },
  openGraph: {
    type: 'website',
    url: '/blog',
    title: 'Blog | Security Scanner',
    description:
      'Latest posts on OWASP, scanning techniques, and secure development.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Blog | Security Scanner',
    description:
      'Insights on web application security, vulnerability scanning, and best practices.',
  },
};

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return children as React.ReactNode;
}


