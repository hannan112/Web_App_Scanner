// src/lib/auth/AuthProvider.tsx
"use client";

import { SessionProvider } from "next-auth/react";
import { useEffect } from "react";
import { useSession } from "next-auth/react";

function TokenPersistence() {
  const { data: session, status } = useSession();
  
  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    console.log("Session status:", status, {
      hasSession: !!session,
      hasAccessToken: !!session?.accessToken
    });
    
    if (session?.accessToken) {
      console.log("Storing tokens in localStorage");
      localStorage.setItem('accessToken', session.accessToken);
      if (session.refreshToken) {
        localStorage.setItem('refreshToken', session.refreshToken);
      }
    } else if (status === "authenticated" && !session?.accessToken) {
      console.error("Authenticated but no access token in session!");
    } else if (status === "unauthenticated") {
      console.log("Clearing tokens from localStorage");
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