"use client";

import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import ProfileDropdown from "@/components/layout/ProfileDropdown";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";

export default function PricingPage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  const handleGetStarted = () => {
    if (loading) return;
    if (isAuthenticated) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col">
      {/* World Map Background */}
      <WorldMapAnimation />

      {/* NAVBAR */}
      <nav className="relative z-10 flex items-center justify-between py-5 px-8 shadow bg-white/80 backdrop-blur-md">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-2xl font-bold text-blue-700">Security Scanner</Link>
          <Link href="/" className="text-gray-700 hover:text-blue-700 font-medium">Home</Link>
          <Link href="/pricing" className="text-blue-700 font-medium">Pricing</Link>
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

      {/* PRICING CONTENT */}
      <div className="relative z-10 flex-grow py-12 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-extrabold text-blue-800 mb-4">Simple, Transparent Pricing</h1>
            <p className="text-xl text-gray-700 max-w-2xl mx-auto">
              Choose the scanning plan that fits your security needs. Start with our free passive scan and upgrade as you grow.
            </p>
          </div>

          {/* Pricing Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* FREE - Passive Scan */}
            <div className="bg-white/90 backdrop-blur rounded-2xl shadow-xl p-8 border-2 border-gray-200 hover:shadow-2xl transition transform hover:-translate-y-1">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Passive Scan</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-5xl font-extrabold text-green-600">Free</span>
                </div>
                <p className="text-gray-600">Perfect for getting started with web security</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">DNS & SSL/TLS Analysis</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">Security Headers Check</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">Technology Detection (Wappalyzer)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">CORS & Cookie Analysis</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">Form Detection</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-600 text-xl">✓</span>
                  <span className="text-gray-700">Basic Reconnaissance</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-gray-400 text-xl">✗</span>
                  <span className="text-gray-400">No intrusive testing</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-gray-400 text-xl">✗</span>
                  <span className="text-gray-400">30-120 seconds scan time</span>
                </li>
              </ul>

              <button
                onClick={() => handleGetStarted()}
                className="w-full py-3 px-6 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition shadow-md"
                disabled={loading}
              >
                Get Started Free
              </button>

              <p className="text-center text-sm text-gray-500 mt-4">No credit card required</p>
            </div>

            {/* PAID - Active Scan */}
            <div className="bg-white/90 backdrop-blur rounded-2xl shadow-xl p-8 border-4 border-blue-600 hover:shadow-2xl transition transform hover:-translate-y-1 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                POPULAR
              </div>

              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Active Scan</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-5xl font-extrabold text-blue-600">$29</span>
                  <span className="text-gray-600">/scan</span>
                </div>
                <p className="text-gray-600">Comprehensive vulnerability testing with OWASP ZAP</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700 font-semibold">All Passive Scan Features</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">OWASP ZAP Active Scanning</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">Spider & AJAX Crawling</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">SQL Injection Detection</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">XSS & CSRF Testing</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">Authentication Testing</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 text-xl">✓</span>
                  <span className="text-gray-700">Detailed Vulnerability Reports</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-gray-600 text-xl">⏱</span>
                  <span className="text-gray-600">5-30 minutes scan time</span>
                </li>
              </ul>

              <button
                onClick={() => handleGetStarted()}
                className="w-full py-3 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition shadow-md"
                disabled={loading}
              >
                Start Active Scan
              </button>

              <p className="text-center text-sm text-gray-500 mt-4">Pay per scan</p>
            </div>

            {/* PREMIUM - Comprehensive Scan */}
            <div className="bg-white/90 backdrop-blur rounded-2xl shadow-xl p-8 border-2 border-purple-600 hover:shadow-2xl transition transform hover:-translate-y-1">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Comprehensive Scan</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-5xl font-extrabold text-purple-600">$99</span>
                  <span className="text-gray-600">/scan</span>
                </div>
                <p className="text-gray-600">Full-spectrum security testing with all tools</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700 font-semibold">All Active Scan Features</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Nuclei Vulnerability Scanning</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Subdomain Enumeration (Subfinder)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Directory Brute-forcing (Feroxbuster)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Historical URL Discovery (Waybackurls)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Advanced SQLMap Integration</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Priority Support</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl">✓</span>
                  <span className="text-gray-700">Executive Summary Report</span>
                </li>
              </ul>

              <button
                onClick={() => handleGetStarted()}
                className="w-full py-3 px-6 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition shadow-md"
                disabled={loading}
              >
                Start Comprehensive Scan
              </button>

              <p className="text-center text-sm text-gray-500 mt-4">Best value for enterprises</p>
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-16 text-center max-w-4xl mx-auto">
            <div className="bg-blue-50/80 backdrop-blur rounded-xl p-8 border border-blue-200">
              <h3 className="text-2xl font-bold text-blue-800 mb-4">Not Sure Which Plan to Choose?</h3>
              <p className="text-gray-700 mb-6">
                Start with our <strong>free Passive Scan</strong> to understand your security posture.
                Upgrade to <strong>Active Scan</strong> when you need vulnerability testing, or go
                <strong> Comprehensive</strong> for complete security coverage with advanced tools.
              </p>
              <div className="flex gap-4 justify-center">
                <Link href="/contact" className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition">
                  Contact Sales
                </Link>
                <Link href="/blog" className="px-6 py-3 border-2 border-blue-600 text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition">
                  Learn More
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
