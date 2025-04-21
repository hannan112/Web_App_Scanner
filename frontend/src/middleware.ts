// src/middleware.ts
import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ['/dashboard', '/projects'];
const authRoutes = ['/login', '/register'];

export async function middleware(request: NextRequest) {
  // Enhanced logging
  console.log('Middleware executing for path:', request.nextUrl.pathname);
  
  // Get token with more debug info
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET
  });
  
  console.log('Auth token details:', token ? 'Token exists' : 'No token found');
  
  const path = request.nextUrl.pathname;
  const isAuthPage = authRoutes.some(route => path.startsWith(route));
  const isProtectedRoute = protectedRoutes.some(route => path.startsWith(route));
  
  // No token means not authenticated
  if (!token) {
    console.log('No authentication token found');
    
    // If trying to access protected route, redirect to login
    if (isProtectedRoute || path === '/') {
      const loginUrl = new URL('/login', request.url);
      // Pass the original URL as a parameter for redirect after login
      loginUrl.searchParams.set('callbackUrl', request.url);
      console.log('Redirecting unauthenticated user to login:', loginUrl.toString());
      return NextResponse.redirect(loginUrl);
    }
    
    // Let unauthenticated users access auth pages
    if (isAuthPage) {
      console.log('Unauthenticated user accessing auth page, allowing');
      return NextResponse.next();
    }
  }
  
  // User is authenticated
  if (token) {
    console.log('User is authenticated');
    
    // Prevent authenticated users from accessing login/register pages
    if (isAuthPage) {
      console.log('Authenticated user redirected from auth page to dashboard');
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    
    // Redirect root to dashboard for authenticated users
    if (path === '/') {
      console.log('Redirecting authenticated user from root to dashboard');
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
    '/dashboard',
    '/dashboard/:path*',
    '/projects',
    '/projects/:path*',
  ]
};