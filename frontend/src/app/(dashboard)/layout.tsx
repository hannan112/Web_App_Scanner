// src/app/(dashboard)/layout.tsx
'use client';

import { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Navbar from '@/components/layout/Navbar';
import WorldMapAnimation from '@/components/visuals/WorldMapAnimation';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // Hide map background on scan results pages only
  const hideMapBackground = pathname?.includes('/results');

  return (
    <ProtectedRoute>
      <div className="relative min-h-screen flex flex-col">
        {!hideMapBackground && <WorldMapAnimation />}
        <div className="relative z-10 min-h-screen flex flex-col">
          <Navbar />
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