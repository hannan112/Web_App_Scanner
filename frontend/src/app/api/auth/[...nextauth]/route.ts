// src/app/api/auth/[...nextauth]/route.ts
import NextAuth, { NextAuthOptions } from "next-auth";
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
            throw new Error("Missing email or password");
          }

          const response = await fetch(`${API_URL}/auth/login/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            throw new Error("Invalid credentials");
          }

          const data = await response.json();

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
          return null;
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
    }),
  ],

  callbacks: {
    async jwt({ token, user, account }) {
      // Initial sign in
      if (account && user) {
        if (account.provider === "google") {
          try {
            // Exchange Google token for backend token
            const response = await fetch(`${API_URL}/auth/google/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                access_token: account.access_token,
                id_token: account.id_token
              }),
            });
            
            if (!response.ok) {
              throw new Error('Failed to authenticate with backend');
            }
            
            const data = await response.json();
            
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
        session.user = {
          ...session.user,
          id: (token.userId as string) || (token.sub as string),
        };
        
        session.accessToken = token.accessToken as string;
        session.refreshToken = token.refreshToken as string;
        session.error = token.error as string | undefined;
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
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };