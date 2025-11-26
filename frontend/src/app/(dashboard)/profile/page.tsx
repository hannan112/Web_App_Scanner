"use client";

import { useState } from "react";
import { useAuth } from "@/lib/contexts/AuthContext";
import PageTitle from "@/components/PageTitle";

interface FormData {
  username: string;
  email: string;
}

export default function ProfilePage() {
  const { user, checkAuthStatus } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    username: user?.username ?? "",
    email: user?.email ?? "",
  });

  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const token = localStorage.getItem("accessToken");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/user/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(Object.values(errorData).flat().join(", ") || "Failed to update profile");
      }

      await checkAuthStatus(); // Refresh user data
      setMessage({ type: "success", text: "Profile updated successfully" });
      setIsEditing(false);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
      setMessage({ type: "error", text: errorMessage });
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: "error", text: "New passwords do not match" });
      return;
    }

    try {
      const token = localStorage.getItem("accessToken");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/password/change/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(passwordData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(Object.values(errorData).flat().join(", ") || "Failed to change password");
      }

      setMessage({ type: "success", text: "Password changed successfully" });
      setIsChangingPassword(false);
      setPasswordData({ old_password: "", new_password: "", confirm_password: "" });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
      setMessage({ type: "error", text: errorMessage });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value.trim() }));
  };

  const handlePasswordDataChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageTitle
        title="Manage Profile"
        subtitle="Update your account settings and profile information"
      />

      {message && (
        <div className={`mb-6 p-4 rounded-md ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      {/* Account Information Card */}
      <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rounded-lg overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-white/10">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-slate-900">Account Information</h2>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
            >
              {isEditing ? "Cancel" : "Edit Profile"}
            </button>
          </div>
        </div>

        <div className="p-6">
          {isEditing ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-slate-700">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  minLength={2}
                  maxLength={50}
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md text-slate-900 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter username"
                />
              </div>

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
                  className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md text-slate-900 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 shadow-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
                >
                  Save Changes
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-slate-700">Username</h3>
                <p className="mt-1 text-slate-900">{user?.username || "N/A"}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-slate-700">Email</h3>
                <p className="mt-1 text-slate-900">{user?.email}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Security Card */}
      <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-xl font-semibold text-slate-900">Security</h2>
        </div>
        <div className="p-6">
          {!isChangingPassword ? (
            <button
              onClick={() => setIsChangingPassword(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
            >
              Change Password
            </button>
          ) : (
            <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
              <div>
                <label htmlFor="old_password" className="block text-sm font-medium text-slate-700">
                  Current Password
                </label>
                <input
                  id="old_password"
                  name="old_password"
                  type="password"
                  required
                  value={passwordData.old_password}
                  onChange={handlePasswordDataChange}
                  className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md text-slate-900 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-slate-700">
                  New Password
                </label>
                <input
                  id="new_password"
                  name="new_password"
                  type="password"
                  required
                  minLength={8}
                  value={passwordData.new_password}
                  onChange={handlePasswordDataChange}
                  className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md text-slate-900 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-slate-700">
                  Confirm New Password
                </label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  required
                  minLength={8}
                  value={passwordData.confirm_password}
                  onChange={handlePasswordDataChange}
                  className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md text-slate-900 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsChangingPassword(false);
                    setPasswordData({ old_password: "", new_password: "", confirm_password: "" });
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 shadow-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
                >
                  Update Password
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}