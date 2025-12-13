// src/lib/auth.ts
import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_URL = `${BASE_URL}/api`;

export const authOptions: NextAuthOptions = {
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
          if (!credentials?.email || !credentials?.password) {
            console.log("Missing email or password");
            throw new Error("Missing email or password");
          }

          // Log the auth attempt (remove in production)
          console.log("Attempting login for:", credentials.email);

          const response = await fetch(`${API_URL}/auth/login/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          // Log the response status
          console.log("Auth response status:", response.status);

          // Improved error handling
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("Auth error response:", errorData);
            throw new Error(errorData.detail || "Invalid credentials");
          }

          const data = await response.json();
          console.log("Auth success, token received:", !!data.access);

          if (data.access) {
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
          throw error;
        }
      },
    }),

    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
      // Explicitly set redirect URI if needed
      // redirectUri: "http://localhost:3000/api/auth/callback/google",
    }),
  ],

  callbacks: {
    async jwt({ token, user, account }) {
      // Initial sign in
      if (account && user) {
        console.log("JWT callback - initial sign in:", {
          provider: account.provider,
          hasUser: !!user,
        });

        if (account.provider === "google") {
          try {
            console.log("Google auth - attempting token exchange with backend");
            console.log("Google tokens:", {
              accessTokenAvailable: !!account.access_token,
              idTokenAvailable: !!account.id_token
            });

            // Exchange Google token for backend token
            const response = await fetch(`${API_URL}/auth/google/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                // Send only access_token to avoid backend id_token audience validation issues
                access_token: account.access_token
              }),
            });

            console.log(`Google token exchange response: ${response.status}`);

            if (!response.ok) {
              const errorData = await response.text();
              console.error('Google auth backend error:', errorData);
              throw new Error('Failed to authenticate with backend');
            }

            const data = await response.json();
            console.log("Response data:", data);

            // Make sure tokens and user info exist
            if (!data.access || !data.refresh) {
              console.error("Missing tokens in backend response", data);
              throw new Error('Invalid response from backend - missing tokens');
            }

            return {
              ...token,
              accessToken: data.access,
              refreshToken: data.refresh,
              userId: data.user?.id ?? token.sub,
            };
          } catch (error) {
            console.error('Error exchanging Google token:', error);
            return { ...token, error: 'GoogleTokenExchangeError' };
          }
        } else {
          // For credentials login
          return {
            ...token,
            accessToken: user.accessToken,
            refreshToken: user.refreshToken,
            userId: user.id
          };
        }
      }
      return token;
    },

    async session({ session, token }) {
      if (token) {
        console.log("Session callback - token available:", {
          hasAccessToken: !!token.accessToken,
          hasUserId: !!token.userId
        });

        session.user = {
          ...session.user,
          id: (token.userId as string) || (token.sub as string),
        };

        session.accessToken = token.accessToken as string;
        session.refreshToken = token.refreshToken as string;
        session.error = token.error as string | undefined;
      } else {
        console.warn("Session callback - no token available");
      }

      return session;
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },

  session: {
    strategy: "jwt",
  },

  // Add debug option to see detailed logs in development
  debug: process.env.NODE_ENV === 'development',
}; 