"use client";

import { AlertTriangle, CheckSquare, FileText, LayoutDashboard, Shield, Users, Video } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";

import { useAuth } from "../../context/AuthContext";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, apiUser, loading } = useAuth();
  const pathname = usePathname();

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
      </div>
    );
  }

  if (!user || apiUser?.role !== "ADMIN") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600">
          <AlertTriangle className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
        <p className="mt-2 text-sm text-gray-600">
          You must be logged in with an administrator account to view the operations portal.
        </p>
        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex items-center rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Return to Homepage
          </Link>
        </div>
      </div>
    );
  }

  const navItems = [
    { label: "Overview", href: "/admin", icon: LayoutDashboard, exact: true },
    { label: "User Management", href: "/admin/users", icon: Users },
    { label: "Verification Queue", href: "/admin/verifications", icon: CheckSquare },
    { label: "Bookings", href: "/admin/bookings", icon: Video },
    { label: "Audit Logs", href: "/admin/audit-logs", icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-700">
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Operations Control Portal</h1>
                <p className="text-xs text-gray-500">Marketplace Administration & Monitoring</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700 ring-1 ring-inset ring-purple-600/20">
                Admin Role Verified
              </span>
            </div>
          </div>
          <div className="flex space-x-8 border-t border-gray-100 pt-2 overflow-x-auto">
            {navItems.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname === item.href || pathname?.startsWith(item.href + "/");
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 border-b-2 py-3 text-sm font-medium transition whitespace-nowrap ${
                    active
                      ? "border-purple-600 text-purple-600"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
