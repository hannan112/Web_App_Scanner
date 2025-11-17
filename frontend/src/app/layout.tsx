// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/contexts/AuthContext";

const inter = Inter({ subsets: ["latin"] });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Security Scanner",
    template: "%s | Security Scanner",
  },
  description: "Scan your website for vulnerabilities and get actionable security insights.",
  keywords: [
    "web security",
    "vulnerability scanner",
    "OWASP",
    "penetration testing",
    "security testing",
  ],
  authors: [{ name: "Security Scanner" }],
  creator: "Security Scanner",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    url: "/",
    title: "Security Scanner",
    description:
      "Scan your website for vulnerabilities and get actionable security insights.",
    siteName: "Security Scanner",
    images: [
      {
        url: "/world-map.png",
        width: 1200,
        height: 630,
        alt: "Security Scanner",
      },
    ],
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Security Scanner",
    description:
      "Scan your website for vulnerabilities and get actionable security insights.",
    images: ["/world-map.png"],
    creator: "@securityscanner",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      maxVideoPreview: -1,
      maxImagePreview: "large",
      maxSnippet: -1,
    },
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          src="https://accounts.google.com/gsi/client"
          async
          defer
        ></script>
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}