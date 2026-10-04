"use client";

import { ArrowRight, CheckSquare, FileText, ShieldAlert, Users, Video } from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";

interface AdminOverviewStats {
  usersCount: number;
  pendingVerifications: number;
  bookingsCount: number;
}

export default function AdminOverviewPage() {
  const { api } = useAuth();
  const [stats, setStats] = useState<AdminOverviewStats>({
    usersCount: 0,
    pendingVerifications: 0,
    bookingsCount: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [usersRes, verifRes, bookingsRes] = await Promise.all([
          api.get<{ total: number }>("/admin/users", { params: { limit: 1 } }),
          api.get<{ total: number }>("/admin/verifications", { params: { status: "PENDING", limit: 1 } }),
          api.get<{ total: number }>("/admin/bookings", { params: { limit: 1 } }),
        ]);
        setStats({
          usersCount: usersRes.total,
          pendingVerifications: verifRes.total,
          bookingsCount: bookingsRes.total,
        });
      } catch (err) {
        console.error("Failed to load admin stats", err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [api]);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523]">Operations Center</h2>
        <p className="text-sm text-[#6E5652] mt-1">
          Monitor marketplace users, interviewer approvals, bookings, and audit records.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#6E5652]">Registered Users</span>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25]">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded-lg bg-[#FDF5EE]" />
            ) : (
              <span className="font-serif text-3xl font-normal text-[#342523]">{stats.usersCount}</span>
            )}
          </div>
          <Link
            href="/admin/users"
            className="mt-4 flex items-center gap-1 text-xs font-medium text-[#9B3B25] hover:text-[#83321F]"
          >
            Manage users <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#6E5652]">Pending Verifications</span>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#FEF3E2] text-[#A65E00]">
              <CheckSquare className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded-lg bg-[#FDF5EE]" />
            ) : (
              <span className="font-serif text-3xl font-normal text-[#342523]">{stats.pendingVerifications}</span>
            )}
          </div>
          <Link
            href="/admin/verifications"
            className="mt-4 flex items-center gap-1 text-xs font-medium text-[#A65E00] hover:text-[#8E4F00]"
          >
            Review queue <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#6E5652]">Total Bookings</span>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E8F4EC] text-[#2C6E49]">
              <Video className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded-lg bg-[#FDF5EE]" />
            ) : (
              <span className="font-serif text-3xl font-normal text-[#342523]">{stats.bookingsCount}</span>
            )}
          </div>
          <Link
            href="/admin/bookings"
            className="mt-4 flex items-center gap-1 text-xs font-medium text-[#2C6E49] hover:text-[#215236]"
          >
            Inspect bookings <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#FDF5EE] text-[#9B3B25]">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-medium text-[#342523] text-base">Safety & Security Rules</h3>
              <p className="text-xs text-[#6E5652]">Administrative operational constraints</p>
            </div>
          </div>
          <ul className="mt-4 space-y-2 text-xs text-[#6E5652]">
            <li className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#9B3B25] mt-1.5 shrink-0" />
              <span>All administrative mutations (user status changes, verification reviews) are strictly audited.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#9B3B25] mt-1.5 shrink-0" />
              <span>Credentials, secrets, and raw authentication tokens are excluded from all responses.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#9B3B25] mt-1.5 shrink-0" />
              <span>Self-suspension and destructive operations require explicit confirmations.</span>
            </li>
          </ul>
        </div>

        <div className="rounded-[24px] border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25]">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-medium text-[#342523] text-base">Audit Trail</h3>
              <p className="text-xs text-[#6E5652]">System mutations and verification history</p>
            </div>
          </div>
          <p className="mt-4 text-xs text-[#6E5652] leading-relaxed">
            Every critical lifecycle event and administrative action is logged with actor identification, request context, and change metadata.
          </p>
          <div className="mt-6">
            <Link
              href="/admin/audit-logs"
              className="inline-flex items-center gap-1.5 rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] shadow-sm transition"
            >
              View System Audit Logs <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
