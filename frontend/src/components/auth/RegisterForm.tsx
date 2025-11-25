/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register } from "@/lib/api/auth";

export default function RegisterForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validatePassword = (password: string) => {
    // At least 8 characters, one number, one special character
    // Backend accepts: !@#$%^&*()_+
    if (password.length < 8) {
      return false;
    }
    if (!/[0-9]/.test(password)) {
      return false;
    }
    if (!/[!@#$%^&*()_+]/.test(password)) {
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: { preventDefault: () => void; }) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }

    // Validate password strength
    if (!validatePassword(formData.password)) {
      setError("Password must be at least 8 characters with at least one number and one special character (!@#$%^&*).");
      setLoading(false);
      return;
    }

    try {
      // Change confirmPassword to password_confirm to match backend expectations
      const response = await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        confirmPassword: formData.confirmPassword
      });

      setSuccess("Registration successful! Please check your email to verify your account.");
      // Clear form
      setFormData({
        email: "",
        username: "",
        password: "",
        confirmPassword: "",
      });
    } catch (err: any) {
      console.error("Registration error details:", err);

      // Handle different error formats from backend
      let errorMessage = "Registration failed. Please try again.";

      if (err.response?.data) {
        // Backend returns serializer.errors which is an object
        const errors = err.response.data;

        // Check for field-specific errors
        if (errors.email) {
          errorMessage = Array.isArray(errors.email) ? errors.email[0] : errors.email;
        } else if (errors.username) {
          errorMessage = Array.isArray(errors.username) ? errors.username[0] : errors.username;
        } else if (errors.password) {
          errorMessage = Array.isArray(errors.password) ? errors.password[0] : errors.password;
        } else if (errors.password_confirm) {
          errorMessage = Array.isArray(errors.password_confirm) ? errors.password_confirm[0] : errors.password_confirm;
        } else if (errors.non_field_errors) {
          errorMessage = Array.isArray(errors.non_field_errors) ? errors.non_field_errors[0] : errors.non_field_errors;
        } else if (typeof errors === 'string') {
          errorMessage = errors;
        } else if (errors.detail) {
          errorMessage = errors.detail;
        } else if (errors.message) {
          errorMessage = errors.message;
        } else {
          // Try to extract first error message from object
          const firstError = Object.values(errors)[0];
          if (Array.isArray(firstError) && firstError.length > 0) {
            errorMessage = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMessage = firstError;
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="w-full max-w-lg p-8 mx-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-xl shadow-2xl">
      <h1 className="mb-6 text-3xl font-bold text-center text-slate-900">Create Account</h1>

      {error && (
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 border border-red-200 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 mb-4 text-sm text-green-600 bg-green-100 border border-green-200 rounded">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-3 py-3 mt-1 border border-gray-300 rounded-md text-gray-900 bg-white/80 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label htmlFor="username" className="block text-sm font-medium text-slate-700">
            Username
          </label>
          <input
            id="username"
            name="username"
            type="text"
            value={formData.username}
            onChange={handleChange}
            required
            className="w-full px-3 py-3 mt-1 border border-gray-300 rounded-md text-gray-900 bg-white/80 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-slate-700">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
            className="w-full px-3 py-3 mt-1 border border-gray-300 rounded-md text-gray-900 bg-white/80 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="mt-1 text-xs text-slate-500">
            Must be at least 8 characters with at least one number and one special character (!@#$%^&*()_+).
          </p>
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            className="w-full px-3 py-3 mt-1 border border-gray-300 rounded-md text-gray-900 bg-white/80 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-3 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 transition-colors font-semibold shadow-lg mt-2"
        >
          {loading ? "Creating Account..." : "Create Account"}
        </button>
      </form>

      <p className="mt-8 text-center">
        <span className="text-sm text-slate-700">Already have an account? </span>
        <Link href="/login" className="text-sm text-blue-600 hover:text-blue-800 hover:underline font-medium">
          Log in
        </Link>
      </p>
    </div>
  );
}