"use client";

import { LogOut, Search, User as UserIcon, Video } from "lucide-react";
import Link from "next/link";
import React from "react";

import { useAuth } from "../context/AuthContext";

export function Navbar() {
  const { user, apiUser, logout, loading } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-blue-600">
            <Video className="h-6 w-6" />
            <span>Interview Ready</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/marketplace"
              className="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-blue-600 transition"
            >
              <Search className="h-4 w-4" />
              Find Interviewers
            </Link>
            {user && (
              <Link
                href="/dashboard"
                className="text-sm font-medium text-gray-700 hover:text-blue-600 transition"
              >
                My Bookings
              </Link>
            )}
            {apiUser?.role === "ADMIN" && (
              <Link
                href="/admin"
                className="text-sm font-semibold text-purple-600 hover:text-purple-700 transition flex items-center gap-1"
              >
                Admin Portal
              </Link>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {loading ? (
            <div className="h-8 w-20 animate-pulse rounded-md bg-gray-200" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-semibold text-gray-900">
                  {apiUser?.full_name || user.displayName || user.email?.split("@")[0]}
                </span>
                <span className="text-xs text-gray-500 capitalize">
                  {apiUser?.role?.toLowerCase() || "Candidate"}
                </span>
              </div>
              <Link
                href="/dashboard"
                className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-semibold hover:ring-2 hover:ring-blue-400"
              >
                <UserIcon className="h-5 w-5" />
              </Link>
              <button
                onClick={() => logout()}
                className="flex items-center gap-1 rounded-md px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
                title="Log out"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                href="/auth/sign-in"
                className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition"
              >
                Sign In
              </Link>
              <Link
                href="/auth/sign-up"
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
