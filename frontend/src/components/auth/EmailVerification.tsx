/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api/auth";

interface EmailVerificationProps {
  token: string;
}

export default function EmailVerification({ token }: EmailVerificationProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      try {
        await verifyEmail(token);
        setSuccess(true);
      } catch (err: any) {
        setError(err.message || "Email verification failed. The token may be invalid or expired.");
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  return (
    <div className="w-full max-w-md p-6 mx-auto bg-white rounded-lg shadow">
      <h1 className="mb-6 text-2xl font-bold text-center">Email Verification</h1>

      {loading ? (
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="mt-4">Verifying your email...</p>
        </div>
      ) : success ? (
        <div className="space-y-4">
          <div className="p-3 text-sm text-green-600 bg-green-100 rounded">
            Your email has been successfully verified! You can now log in to your account.
          </div>
          <button
            onClick={() => router.push("/login")}
            className="w-full px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Go to Login
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-3 text-sm text-red-600 bg-red-100 rounded">
            {error}
          </div>
          <div className="flex justify-center space-x-4">
            <Link 
              href="/login" 
              className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Go to Login
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}