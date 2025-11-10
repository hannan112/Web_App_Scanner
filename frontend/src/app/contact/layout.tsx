import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contact',
  description:
    "Get in touch with Security Scanner. We're here to help with your web security needs.",
  alternates: { canonical: '/contact' },
  openGraph: {
    type: 'website',
    url: '/contact',
    title: 'Contact | Security Scanner',
    description: 'Contact the Security Scanner team for questions, support, or sales.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Contact | Security Scanner',
    description:
      "Get in touch with Security Scanner. We're here to help with your web security needs.",
  },
};

export default function ContactLayout({ children }: { children: React.ReactNode }) {
  return children as React.ReactNode;
}


