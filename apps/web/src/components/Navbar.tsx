"use client";

import {
  Briefcase,
  LogOut,
  Menu,
  Search,
  Shield,
  User as UserIcon,
  X,
} from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";

import { useAuth } from "../context/AuthContext";

export function Navbar() {
  const { user, apiUser, logout, loading } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[#EADBCE] bg-[#FFF8F0]/90 backdrop-blur-md">
      <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="font-editorial text-2xl font-bold tracking-tight text-[#342523]">
              interview ready<span className="text-[#9B3B25]">.</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/marketplace"
              className="flex items-center gap-1.5 text-sm font-medium text-[#342523] hover:text-[#9B3B25] transition"
            >
              <Search className="h-4 w-4 text-[#9B3B25]" />
              Find Interviewers
            </Link>
            {user && (
              <Link
                href="/dashboard"
                className="text-sm font-medium text-[#342523] hover:text-[#9B3B25] transition"
              >
                My Bookings
              </Link>
            )}
            {user ? (
              <Link
                href="/interviewer"
                className="flex items-center gap-1.5 text-sm font-medium text-[#342523] hover:text-[#9B3B25] transition"
              >
                <Briefcase className="h-4 w-4 text-[#9B3B25]" />
                {apiUser?.role === "INTERVIEWER" ? "Interviewer Portal" : "Become an Interviewer"}
              </Link>
            ) : (
              <Link
                href="/auth/interviewer"
                className="flex items-center gap-1.5 text-sm font-medium text-[#342523] hover:text-[#9B3B25] transition"
              >
                <Briefcase className="h-4 w-4 text-[#9B3B25]" />
                For Interviewers
              </Link>
            )}
            {apiUser?.role === "ADMIN" && (
              <Link
                href="/admin"
                className="flex items-center gap-1 text-xs font-bold uppercase tracking-wider rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-3 py-1 text-[#9B3B25] hover:bg-[#F8DDC9] transition"
              >
                <Shield className="h-3.5 w-3.5" />
                Admin
              </Link>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {loading ? (
            <div className="h-9 w-24 animate-pulse rounded-full bg-[#EADBCE]" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-semibold text-[#342523]">
                  {apiUser?.full_name || user.displayName || user.email?.split("@")[0]}
                </span>
                <span className="text-xs text-[#6E5652] capitalize">
                  {apiUser?.role?.toLowerCase() || "Candidate"}
                </span>
              </div>
              <Link
                href="/dashboard"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] font-semibold border border-[#ECC2A4] hover:shadow-sm transition"
                title="Account Dashboard"
              >
                <UserIcon className="h-5 w-5" />
              </Link>
              <button
                onClick={() => logout()}
                className="flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold text-[#6E5652] hover:bg-[#FDF5EE] hover:text-[#9B3B25] border border-transparent hover:border-[#ECC2A4] transition cursor-pointer"
                title="Log out"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-2.5">
              <Link
                href="/auth/sign-in"
                className="btn-pill-secondary px-5 py-2 text-sm"
              >
                Sign In
              </Link>
              <Link
                href="/auth/sign-up"
                className="btn-pill-primary px-5 py-2 text-sm"
              >
                Get Started
              </Link>
            </div>
          )}

          {/* Mobile hamburger toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex h-10 w-10 items-center justify-center rounded-full border border-[#ECC2A4] bg-white text-[#342523] hover:bg-[#FDF5EE]"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#EADBCE] bg-[#FFF8F0] px-4 pt-3 pb-6 space-y-3">
          <Link
            href="/marketplace"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-[#342523] hover:bg-[#FDF5EE]"
          >
            <Search className="h-4 w-4 text-[#9B3B25]" />
            Find Interviewers
          </Link>
          {user && (
            <Link
              href="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-[#342523] hover:bg-[#FDF5EE]"
            >
              <UserIcon className="h-4 w-4 text-[#9B3B25]" />
              My Bookings
            </Link>
          )}
          <Link
            href={user ? "/interviewer" : "/auth/interviewer"}
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-[#342523] hover:bg-[#FDF5EE]"
          >
            <Briefcase className="h-4 w-4 text-[#9B3B25]" />
            {user && apiUser?.role === "INTERVIEWER" ? "Interviewer Portal" : "For Interviewers"}
          </Link>
          {apiUser?.role === "ADMIN" && (
            <Link
              href="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-[#9B3B25] hover:bg-[#FDF5EE]"
            >
              <Shield className="h-4 w-4" />
              Admin Portal
            </Link>
          )}

          {!user && (
            <div className="pt-2 flex flex-col gap-2">
              <Link
                href="/auth/sign-in"
                onClick={() => setMobileMenuOpen(false)}
                className="btn-pill-secondary w-full text-center py-2"
              >
                Sign In
              </Link>
              <Link
                href="/auth/sign-up"
                onClick={() => setMobileMenuOpen(false)}
                className="btn-pill-primary w-full text-center py-2"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
