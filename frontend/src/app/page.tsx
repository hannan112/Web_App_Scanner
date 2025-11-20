"use client";

import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Script from "next/script";
import ProfileDropdown from "@/components/layout/ProfileDropdown";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";

export default function Home() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  const handleScanClick = () => {
    if (loading) return;
    if (isAuthenticated) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col">
      <Script id="ld-json-home" type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: "Security Scanner",
            url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
            potentialAction: {
              "@type": "SearchAction",
              target: `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/search?q={search_term_string}`,
              "query-input": "required name=search_term_string"
            }
          })
        }}
      />
      {/* World Map Background */}
      <WorldMapAnimation />

      {/* NAVBAR */}
      <nav className="relative z-50 flex items-center justify-between py-5 px-8 shadow bg-white/80 backdrop-blur-md">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-2xl font-bold text-blue-700">Security Scanner</Link>
          <Link href="/" className="text-gray-700 hover:text-blue-700 font-medium">Home</Link>
          <Link href="/pricing" className="text-gray-700 hover:text-blue-700 font-medium">Pricing</Link>
          <Link href="/blog" className="text-gray-700 hover:text-blue-700 font-medium">Blog</Link>
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

      {/* HERO + FEATURES */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 pt-12">
        <section className="mb-10">
          <h1 className="text-5xl font-extrabold mb-6 text-blue-800 drop-shadow">Protect Your Website. Stay Ahead of Hackers.</h1>
          <div className="text-2xl md:text-3xl font-bold mb-3 text-red-600 animate-pulse">~30,000+ websites are hacked every day worldwide!</div>
          <div className="text-gray-700 mb-7 text-lg max-w-xl mx-auto">Our advanced web security scanner helps you spot critical vulnerabilities <strong>before</strong> they are exploited. Get peace of mind by proactively securing your project.</div>
          <button
            className="mt-4 px-8 py-4 bg-blue-700 text-white font-bold text-lg rounded-xl shadow-lg hover:bg-blue-800 transition disabled:opacity-60"
            onClick={handleScanClick}
            disabled={loading}
          >
            Scan Your Site
          </button>
        </section>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center flex-grow text-center px-4 py-12">
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-12 w-full">
          <div className="bg-white/80 backdrop-blur rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold text-blue-800 mb-2">Real-Time Threat Detection</h2>
            <p className="text-gray-700">Scan your site for known vulnerabilities, OWASP Top 10, outdated libraries, and more.</p>
          </div>
          <div className="bg-white/80 backdrop-blur rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold text-blue-800 mb-2">Actionable Reports</h2>
            <p className="text-gray-700">Get a clear breakdown with recommended fixes for each issue detected during scanning.</p>
          </div>
          <div className="bg-white/80 backdrop-blur rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold text-blue-800 mb-2">Built for Developers & Businesses</h2>
            <p className="text-gray-700">Integrate results in your workflow, track scans, and empower your team with better security.</p>
          </div>
        </section>
        <section className="mt-6 bg-white/70 backdrop-blur px-6 py-4 rounded-lg shadow">
          <h3 className="text-2xl font-bold text-blue-800 mb-2">Our Mission</h3>
          <p className="max-w-2xl text-gray-700 text-lg mx-auto">Our agenda is to make advanced web security accessible for everyone. With Security Scanner, empower yourself to protect digital assets, customer trust, and your reputation—without needing a security expert on staff.</p>
        </section>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
