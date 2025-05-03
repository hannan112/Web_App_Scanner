// src/app/(dashboard)/layout.tsx
import { ReactNode } from 'react';
import Link from 'next/link';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ProfileDropdown from '@/components/layout/ProfileDropdown';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100 flex flex-col">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-xl font-bold text-gray-800">
                Security Scanner
              </Link>
              <nav className="ml-10 space-x-4 hidden md:flex">
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
    </ProtectedRoute>
  );
}