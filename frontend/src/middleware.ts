// src/middleware.ts
import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ['/dashboard', '/projects', '/scans'];
const authRoutes = ['/login', '/register', '/password-reset'];

export async function middleware(request: NextRequest) {
  // Get token and verify authentication status
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET
  });
  
  const path = request.nextUrl.pathname;
  const isAuthPage = authRoutes.some(route => path.startsWith(route));
  const isProtectedRoute = protectedRoutes.some(route => path.startsWith(route));
  
  // Debug logging
  console.log(`Middleware: Path=${path}, HasToken=${!!token}, IsAuthPage=${isAuthPage}, IsProtectedRoute=${isProtectedRoute}`);
  
  // No token means not authenticated
  if (!token) {
    // If trying to access protected route, redirect to login
    if (isProtectedRoute || path === '/') {
      console.log('Redirecting unauthenticated user to login');
      const loginUrl = new URL('/login', request.url);
      loginUrl.searchParams.set('callbackUrl', encodeURI(request.url));
      return NextResponse.redirect(loginUrl);
    }
    
    // Let unauthenticated users access auth pages
    if (isAuthPage) {
      return NextResponse.next();
    }
  }
  
  // User is authenticated
  if (token) {
    // Prevent authenticated users from accessing login/register pages
    if (isAuthPage) {
      console.log('Redirecting authenticated user from auth page to dashboard');
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    
    // Redirect root to dashboard for authenticated users
    if (path === '/') {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }
  
  // For all other cases, proceed normally
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