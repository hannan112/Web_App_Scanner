/* eslint-disable react/no-unescaped-entities */
// src/components/auth/LoginForm.tsx
"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { UserCredentials } from "@/types/api";
// import GoogleAuthDebug from "./GoogleAuthDebug";

export default function LoginForm() {
  const { login, loginWithGoogle } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get("returnUrl");
  const [credentials, setCredentials] = useState<UserCredentials>({
    email: "",
    password: ""
  });
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      console.log("Attempting Django JWT login with:", credentials.email);
      const result = await login(credentials.email, credentials.password);

      console.log("Login result:", result);

      if (result.success) {
        if (returnUrl) {
          router.push(decodeURIComponent(returnUrl));
        } else {
          router.push("/dashboard");
        }
      } else {
        setError(result.error || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setLoading(true);

    try {
      // Check if Google Client ID is configured
      const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      if (!googleClientId) {
        throw new Error("Google Client ID not configured. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID in your environment variables.");
      }

      // Wait for Google Identity Services to load
      if (!window.google) {
        // Try to load the script dynamically
        await loadGoogleScript();

        // Wait a bit more for the script to initialize
        await new Promise(resolve => setTimeout(resolve, 1000));

        if (!window.google) {
          throw new Error("Google Identity Services failed to load. Please check your internet connection and try again.");
        }
      }

      console.log("Initializing Google Sign-In with client ID:", googleClientId.substring(0, 20) + "...");

      // Initialize Google Sign-In
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: googleClientId,
        scope: "profile email",
        callback: async (response: { access_token: string }) => {
          try {
            console.log("Google token received, exchanging with backend...");
            const result = await loginWithGoogle(response.access_token);

            if (result.success) {
              if (returnUrl) {
                router.push(decodeURIComponent(returnUrl));
              } else {
                router.push("/dashboard");
              }
            } else {
              setError(result.error || "Google login failed");
            }
          } catch (err) {
            console.error("Google login error:", err);
            setError("Google login failed. Please try again.");
          } finally {
            setLoading(false);
          }
        },
      });

      // Request access token
      client.requestAccessToken();
    } catch (err) {
      console.error("Google login initialization error:", err);
      setError(err instanceof Error ? err.message : "Failed to initialize Google login. Please try again.");
      setLoading(false);
    }
  };

  // Function to dynamically load Google Identity Services
  const loadGoogleScript = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      // Check if script is already loaded
      if (window.google) {
        resolve();
        return;
      }

      // Check if script is already in the DOM
      const existingScript = document.querySelector('script[src*="accounts.google.com/gsi/client"]');
      if (existingScript) {
        // Script exists but google object not available yet, wait for it
        const checkGoogle = () => {
          if (window.google) {
            resolve();
          } else {
            setTimeout(checkGoogle, 100);
          }
        };
        checkGoogle();
        return;
      }

      // Create and load the script
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;

      script.onload = () => {
        console.log("Google Identity Services script loaded");
        // Wait for the google object to be available
        const checkGoogle = () => {
          if (window.google) {
            resolve();
          } else {
            setTimeout(checkGoogle, 100);
          }
        };
        checkGoogle();
      };

      script.onerror = () => {
        reject(new Error("Failed to load Google Identity Services script"));
      };

      document.head.appendChild(script);
    });
  };

  return (
    <div className="w-full max-w-lg p-8 mx-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-xl shadow-2xl">
      <h1 className="mb-6 text-3xl font-bold text-center text-slate-900">Log In</h1>

      {error && (
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 border border-red-200 rounded">
          {error}
        </div>
      )}

      <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
        <div className="rounded-md shadow-sm -space-y-px">
          <div>
            <label htmlFor="email" className="sr-only">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm bg-white/80"
              placeholder="Email address"
              value={credentials.email}
              onChange={handleChange}
            />
          </div>
          <div>
            <label htmlFor="password" className="sr-only">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm bg-white/80"
              placeholder="Password"
              value={credentials.password}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="text-sm">
            <Link href="/password-reset" className="text-blue-600 hover:text-blue-800 hover:underline">
              Forgot your password?
            </Link>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-3 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 transition-colors font-semibold shadow-lg"
        >
          {loading ? "Logging in..." : "Log In"}
        </button>
      </form>

      <div className="mt-8">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 text-gray-500 bg-transparent">Or continue with</span>
          </div>
        </div>

        <div className="mt-6">
          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={loading}
            className="w-full inline-flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm bg-white/50 backdrop-blur-sm text-sm font-medium text-gray-700 hover:bg-white/80 disabled:bg-gray-100 transition-all"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span className="ml-2">Sign in with Google</span>
          </button>
        </div>
      </div>

      <p className="mt-8 text-center">
        <span className="text-sm text-slate-700">Don't have an account? </span>
        <Link href="/register" className="text-sm text-blue-600 hover:text-blue-800 hover:underline font-medium">
          Sign up
        </Link>
      </p>

    </div>
  );
}