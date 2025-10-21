// src/middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ['/dashboard', '/projects', '/scans'];
const authRoutes = ['/login', '/register', '/password-reset'];

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const isAuthPage = authRoutes.some(route => path.startsWith(route));
  const isProtectedRoute = protectedRoutes.some(route => path.startsWith(route));
  
  // Skip middleware for API routes, static files, and Next.js internals
  if (path.startsWith('/api/') ||
      path.startsWith('/_next/') ||
      path.startsWith('/static/') ||
      path.startsWith('/favicon.ico')) {
    return NextResponse.next();
  }
  
  // For client-side navigation, let the AuthContext handle authentication
  // This middleware only handles initial page loads and prevents infinite redirects
  
  // Skip authentication checks for client-side navigation
  if (request.headers.get('x-next-router-prefetch') || 
      request.headers.get('x-next-router-cache')) {
    return NextResponse.next();
  }
  
  // For auth pages, don't redirect - let the AuthContext handle it
  if (isAuthPage) {
    return NextResponse.next();
  }
  
  // For protected routes and root, let the AuthContext handle authentication
  // The AuthContext will redirect to login if not authenticated
  if (isProtectedRoute || path === '/') {
    return NextResponse.next();
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/login',
    '/register',
    '/password-reset',
    '/password-reset/:path*',
    '/dashboard',
    '/dashboard/:path*',
    '/projects',
    '/projects/:path*',
    '/scans',
    '/scans/:path*',
  ]
};