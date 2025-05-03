// src/lib/auth/AuthProvider.tsx
"use client";

import { SessionProvider } from "next-auth/react";
import { useEffect } from "react";
import { useSession } from "next-auth/react";

function TokenPersistence() {
  const { data: session, status } = useSession();
  
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    if (session?.accessToken) {
      localStorage.setItem('accessToken', session.accessToken);
      if (session.refreshToken) {
        localStorage.setItem('refreshToken', session.refreshToken);
      }
      
      console.log('Token stored in localStorage:', session.accessToken.substring(0, 10) + '...');
    } else if (status === "unauthenticated") {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }, [session, status]);
  
  return null;
}

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <TokenPersistence />
      {children}
    </SessionProvider>
  );
}