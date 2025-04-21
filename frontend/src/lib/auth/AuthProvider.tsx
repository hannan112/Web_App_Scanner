// src/lib/auth/AuthProvider.tsx
"use client";

import { SessionProvider } from "next-auth/react";
//mport "../../types/next-auth"; // Ensure the extended types are imported
import { useEffect } from "react";
import { useSession } from "next-auth/react";
import "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
    }
    accessToken?: string
    refreshToken?: string
  }
}

function TokenPersistence() {
  const { data: session } = useSession();
  useEffect(() => {
    if (session?.accessToken) {
      // Store the token for API calls
      localStorage.setItem('accessToken', session.accessToken as string);
      if (session.refreshToken) {
        localStorage.setItem('refreshToken', session.refreshToken as string);
      }
    } else {
      // Clear tokens when session is invalid
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }, [session]);
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