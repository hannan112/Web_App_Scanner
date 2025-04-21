/* eslint-disable react/no-unescaped-entities */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import Link from "next/link";
import { requestPasswordReset } from "@/lib/api/auth";

export default function PasswordResetForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await requestPasswordReset(email);
      setSuccess("Password reset email sent! Please check your inbox for further instructions.");
      setEmail("");
    } catch (err: any) {
      setError(err.message || "Failed to send password reset email. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-6 mx-auto bg-white rounded-lg shadow">
      <h1 className="mb-6 text-2xl font-bold text-center text-gray-600">Reset Password</h1>
      
      <p className="mb-6 text-sm text-gray-600">
        Enter your email address and we'll send you a link to reset your password.
      </p>

      {error && (
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 mb-4 text-sm text-green-600 bg-green-100 rounded">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 mt-1 border rounded-md text-black"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
        >
          {loading ? "Sending..." : "Send Reset Link"}
        </button>
      </form>

      <p className="mt-6 text-center">
        <Link href="/login" className="text-sm text-blue-600 hover:underline">
          Back to Log In
        </Link>
      </p>
    </div>
  );
}