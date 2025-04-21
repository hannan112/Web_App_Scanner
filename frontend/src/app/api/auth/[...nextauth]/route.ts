/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/api/auth/[...nextauth]/route.ts
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const authOptions = {
  providers: [
    CredentialsProvider({
      id: "django-credentials",
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          // Call your Django login endpoint
          const response = await fetch(`${API_URL}/auth/login/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials?.email,
              password: credentials?.password,
            }),
          });
          
          const data = await response.json();
          
          if (response.ok && data.access) {
            return {
              id: data.user.id.toString(),
              email: data.user.email,
              name: data.user.username,
              accessToken: data.access,
              refreshToken: data.refresh,
            };
          }
          return null;
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      },
    }),
    
    // Optional Google provider
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
  ],
  
  callbacks: {
    async jwt({ token, user, account }: { token: any; user?: any; account?: any }) {
      // Initial sign in
      if (account && user) {
        if (account.provider === "google") {
          try {
            // Exchange Google token for your backend JWT
            const response = await fetch(`${API_URL}/auth/google/`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ 
                access_token: account.access_token,
                id_token: account.id_token 
              }),
            });
            
            const data = await response.json();
            
            if (!response.ok) {
              throw new Error(data.message || 'Google authentication failed');
            }

            return {
              ...token,
              accessToken: data.access,
              refreshToken: data.refresh,
              user: data.user,
              provider: "google"
            };
          } catch (error) {
            console.error("Google auth error:", error);
            return { ...token, error: "GoogleAuthError" };
          }
        } else {
          return {
            ...token,
            accessToken: user.accessToken,
            refreshToken: user.refreshToken,
            user,
            provider: "credentials"
          };
        }
      }

      // Check if token needs refresh
      if (token.accessToken) {
        // Here you would implement your token refresh logic
        try {
          // Example refresh token logic (implement according to your backend)
          if (isTokenExpired(token.accessToken)) {
            const response = await fetch(`${API_URL}/auth/token/refresh/`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh: token.refreshToken }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
              return {
                ...token,
                accessToken: data.access,
                refreshToken: data.refresh,
              };
            }
          }
        } catch (error) {
          console.error("Token refresh error:", error);
          // Return token as is if refresh fails
          return token;
        }
      }
      
      return token;
    },

    async session({ session, token }: { session: any; token: any }) {
      if (token) {
        // Pass provider information to the client
        session.user = {
          ...token.user,
          provider: token.provider
        };
        session.accessToken = token.accessToken;
        session.refreshToken = token.refreshToken;
        session.error = token.error;
      }
      return session;
    },
  },
  
  pages: {
    signIn: "/login",
    error: "/login",
  },
  
  session: {
    strategy: "jwt" as const,
  },
};

// Helper function to check if token is expired
function isTokenExpired(token: string): boolean {
  try {
    const tokenData = JSON.parse(atob(token.split('.')[1]));
    const expires = tokenData.exp * 1000; // Convert to milliseconds
    return Date.now() >= expires;
  } catch {
    return true;
  }
}

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };