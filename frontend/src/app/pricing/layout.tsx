import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pricing',
  description:
    'Simple, transparent pricing for Security Scanner. Start free and upgrade as you grow.',
  alternates: { canonical: '/pricing' },
  openGraph: {
    type: 'website',
    url: '/pricing',
    title: 'Pricing | Security Scanner',
    description:
      'Compare plans for passive, active, and comprehensive vulnerability scanning.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Pricing | Security Scanner',
    description:
      'Simple, transparent pricing for Security Scanner. Start free and upgrade as you grow.',
  },
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children as React.ReactNode;
}


