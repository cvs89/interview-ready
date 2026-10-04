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
      <div className="flex min-h-[60vh] items-center justify-center bg-[#FFF8F0]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#9B3B25] border-t-transparent" />
      </div>
    );
  }

  if (!user || apiUser?.role !== "ADMIN") {
    return (
      <div className="min-h-screen bg-[#FFF8F0] flex items-center justify-center px-4 py-16">
        <div className="mx-auto max-w-md w-full rounded-[24px] border border-[#EADBCE] bg-white p-8 sm:p-10 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#FCEBEB] text-[#9E2A2B]">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <h1 className="font-serif text-2xl font-normal text-[#342523]">Access Denied</h1>
          <p className="mt-2 text-sm text-[#6E5652]">
            You must be logged in with an administrator account to view the operations portal.
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex items-center rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow hover:bg-[#83321F] transition"
            >
              Return to Homepage
            </Link>
          </div>
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
    <div className="min-h-screen bg-[#FFF8F0]">
      <div className="border-b border-[#EADBCE] bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25]">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h1 className="font-serif text-lg font-normal text-[#342523]">Operations Control Portal</h1>
                <p className="text-xs text-[#6E5652]">Marketplace Administration & Monitoring</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-[#FDF5EE] border border-[#ECC2A4] px-3 py-0.5 text-xs font-semibold text-[#9B3B25]">
                Admin Role Verified
              </span>
            </div>
          </div>
          <div className="flex space-x-8 border-t border-[#EADBCE] pt-1 overflow-x-auto">
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
                      ? "border-[#9B3B25] text-[#9B3B25]"
                      : "border-transparent text-[#6E5652] hover:border-[#EADBCE] hover:text-[#342523]"
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
