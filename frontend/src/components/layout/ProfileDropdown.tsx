"use client";

import { useState, useRef, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Session } from "next-auth";

interface CustomUser {
  name?: string | null;
  email?: string | null;
  id: string;
}

type CustomSession = Session & {
  user: CustomUser;
};

export default function ProfileDropdown() {
  const { data: session } = useSession() as { data: CustomSession | null };
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Handle logout
  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push("/login");
  };

  if (!session) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Profile button that toggles dropdown */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 p-2 rounded-full hover:bg-gray-100 transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
          {session?.user?.name?.[0]?.toUpperCase() ?? "U"}
        </div>
        <span className="hidden md:inline text-sm font-medium">
          {session?.user?.name ?? session?.user?.email ?? "User"}
        </span>
        {/* Dropdown arrow */}
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-gray-200">
          <div className="px-4 py-2 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-700">{session?.user?.name ?? "User"}</p>
            <p className="text-xs text-gray-500 truncate">{session?.user?.email}</p>
          </div>
          
          <Link
            href="/profile"
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => setIsOpen(false)}
          >
            Manage Profile
          </Link>
          
          <button
            onClick={handleLogout}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}