"use client";

import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Script from "next/script";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";
import Navbar from "@/components/layout/Navbar";

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
      <Navbar />

      {/* HERO + FEATURES */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 pt-20 pb-16">
        {isAuthenticated ? (
          <section className="mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">Welcome Back</h1>
            <p className="text-lg text-slate-600 mb-10 leading-relaxed">
              Ready to secure your projects? Jump right back into your dashboard or start a new scan.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/dashboard"
                className="px-6 py-3 bg-slate-900 text-white font-medium text-base rounded-lg shadow-sm hover:bg-slate-800 transition-all"
              >
                Go to Dashboard
              </Link>
              <Link
                href="/projects/new"
                className="px-6 py-3 bg-white text-slate-900 border border-slate-200 font-medium text-base rounded-lg shadow-sm hover:bg-slate-50 transition-all"
              >
                Start New Scan
              </Link>
              <Link
                href="/projects"
                className="px-6 py-3 text-slate-600 font-medium text-base hover:text-slate-900 transition-all"
              >
                View Projects
              </Link>
            </div>
          </section>
        ) : (
          <section className="mb-16 max-w-4xl">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 text-slate-900 tracking-tight leading-tight">
              Protect Your Website.<br />Stay Ahead of Hackers.
            </h1>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-orange-50 text-orange-700 text-sm font-medium mb-8 border border-orange-100">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
              </span>
              ~30,000+ websites are hacked every day worldwide
            </div>
            <p className="text-lg text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              Our advanced web security scanner helps you spot critical vulnerabilities <strong>before</strong> they are exploited. Get peace of mind by proactively securing your project.
            </p>
            <button
              className="px-8 py-4 bg-blue-600 text-white font-semibold text-lg rounded-lg shadow-md hover:bg-blue-700 transition-all disabled:opacity-60 hover:shadow-lg"
              onClick={handleScanClick}
              disabled={loading}
            >
              Scan Your Site
            </button>
          </section>
        )}
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center flex-grow text-center px-4 py-12 bg-white/50 backdrop-blur-sm w-full">
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-16 w-full px-4">
          <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-100 hover:shadow-md transition-shadow text-left">
            <div className="h-10 w-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Real-Time Detection</h2>
            <p className="text-slate-600 text-sm leading-relaxed">Scan your site for known vulnerabilities, OWASP Top 10, outdated libraries, and more.</p>
          </div>
          <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-100 hover:shadow-md transition-shadow text-left">
            <div className="h-10 w-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            </div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Actionable Reports</h2>
            <p className="text-slate-600 text-sm leading-relaxed">Get a clear breakdown with recommended fixes for each issue detected during scanning.</p>
          </div>
          <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-100 hover:shadow-md transition-shadow text-left">
            <div className="h-10 w-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
            </div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">For Developers</h2>
            <p className="text-slate-600 text-sm leading-relaxed">Integrate results in your workflow, track scans, and empower your team with better security.</p>
          </div>
        </section>

        <section className="max-w-3xl mx-auto">
          <h3 className="text-2xl font-bold text-slate-900 mb-4">Our Mission</h3>
          <p className="text-slate-600 text-lg leading-relaxed">
            We believe advanced web security should be accessible to everyone. Security Scanner empowers you to protect your digital assets without needing a dedicated security team.
          </p>
        </section>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
