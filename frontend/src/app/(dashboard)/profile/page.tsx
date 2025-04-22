"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import PageTitle from "@/components/PageTitle";
import type { Session } from "next-auth";

interface FormData {
  username: string;
  email: string;
}

interface CustomUser {
  name?: string | null;
  email?: string | null;
  id: string;
}

type CustomSession = Session & {
  user: CustomUser;
};

export default function ProfilePage() {
  const { data: session } = useSession() as { data: CustomSession | null };
  const [isEditing, setIsEditing] = useState(false);
  
  const [formData, setFormData] = useState<FormData>({
    username: session?.user?.name ?? "",
    email: session?.user?.email ?? "",
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
    <div>
      <PageTitle 
        title="Manage Profile" 
        subtitle="Update your account settings and profile information" 
      />
      
      <div className="bg-white shadow rounded-lg p-6 mt-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-700">Account Information</h2>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="px-4 py-2 text-sm font-medium text-gray-100 bg-blue-600 rounded-md hover:bg-blue-700"
          >
            {isEditing ? "Cancel" : "Edit Profile"}
          </button>
        </div>

        {isEditing ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
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
                className="w-full px-3 py-2 mt-1 border rounded-md text-gray-900 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-3 py-2 mt-1 border rounded-md text-black"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-gray-100 bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Username</h3>
              <p className="mt-1 text-gray-700">{session?.user?.name || "N/A"}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Email</h3>
              <p className="mt-1 text-gray-700">{session?.user?.email}</p>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white shadow rounded-lg p-6 mt-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-6">Security</h2>
        <button
          className="px-4 py-2 text-sm font-medium text-gray-100 bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Change Password
        </button>
      </div>
    </div>
  );
}