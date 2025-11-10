// src/app/(dashboard)/layout.tsx
'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ProfileDropdown from '@/components/layout/ProfileDropdown';
import RunningScanIndicator from '@/components/layout/RunningScanIndicator';
import WorldMapAnimation from '@/components/visuals/WorldMapAnimation';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // Hide map background on scan results and specific project detail pages (but not on /projects list page)
  const hideMapBackground =
    pathname?.includes('/results') ||
    (pathname?.startsWith('/projects/') && pathname !== '/projects');

  return (
    <ProtectedRoute>
      <div className="relative min-h-screen flex flex-col">
        {!hideMapBackground && <WorldMapAnimation />}
        <div className="relative z-10 min-h-screen flex flex-col">
        <header className="bg-white/80 backdrop-blur-md shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-xl font-bold text-gray-800">
                Security Scanner
              </Link>
              <nav className="ml-10 space-x-4 hidden md:flex">
                <Link href="/" className="text-gray-600 hover:text-gray-900">
                  Home
                </Link>
                <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                  Dashboard
                </Link>
                <Link href="/projects" className="text-gray-600 hover:text-gray-900">
                  Projects
                </Link>
                <Link href="/scans" className="text-gray-600 hover:text-gray-900">
                  Scans
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              {/* Running scan indicator */}
              <RunningScanIndicator />
              {/* You can add more icons or links here */}
              {/* Replace the simple Profile link with the ProfileDropdown component */}
              <ProfileDropdown />
            </div>
          </div>
        </header>
        <main className="flex-grow">
          {children}
        </main>
        <footer className="bg-white border-t">
          <div className="max-w-7xl mx-auto px-4 py-4 text-sm text-gray-500">
            <p>Security Scanner &copy; {new Date().getFullYear()}</p>
          </div>
        </footer>
        </div>
      </div>
    </ProtectedRoute>
  );
}