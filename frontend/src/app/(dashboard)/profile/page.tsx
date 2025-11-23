"use client";

import { useState } from "react";
import { useAuth } from "@/lib/contexts/AuthContext";
import PageTitle from "@/components/PageTitle";

interface FormData {
  username: string;
  email: string;
}

export default function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    username: user?.username ?? "",
    email: user?.email ?? "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Update profile with:", formData);
    setIsEditing(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value.trim() }));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageTitle
        title="Manage Profile"
        subtitle="Update your account settings and profile information"
      />

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
          <button
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
          >
            Change Password
          </button>
        </div>
      </div>
    </div>
  );
}