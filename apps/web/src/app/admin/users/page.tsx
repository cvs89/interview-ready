"use client";

import type { AdminUserListResponse, AdminUserResponse, UserRole, UserStatus } from "@interview-ready/api-types";
import { AlertCircle, CheckCircle2, Filter, RefreshCw, Search, Shield, UserX } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../../context/AuthContext";
import { ApiError } from "../../../lib/api-client";

export default function AdminUsersPage() {
  const { api, apiUser } = useAuth();
  const [users, setUsers] = useState<AdminUserResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status Change Modal State
  const [selectedUser, setSelectedUser] = useState<AdminUserResponse | null>(null);
  const [targetStatus, setTargetStatus] = useState<UserStatus>("ACTIVE");
  const [statusReason, setStatusReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };
      if (search.trim()) params.search = search.trim();
      if (roleFilter !== "ALL") params.role = roleFilter;
      if (statusFilter !== "ALL") params.status = statusFilter;

      const data = await api.get<AdminUserListResponse>("/admin/users", { params });
      setUsers(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to fetch users");
      }
    } finally {
      setLoading(false);
    }
  }, [api, limit, offset, search, roleFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchUsers();
  };

  const openStatusModal = (user: AdminUserResponse) => {
    setSelectedUser(user);
    setTargetStatus(user.status);
    setStatusReason("");
    setActionError(null);
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setSubmitting(true);
    setActionError(null);

    try {
      await api.patch<AdminUserResponse>(`/admin/users/${selectedUser.id}/status`, {
        status: targetStatus,
        reason: statusReason.trim() || undefined,
      });
      setSelectedUser(null);
      await fetchUsers();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to update user status");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: UserStatus) => {
    switch (status) {
      case "ACTIVE":
        return "bg-[#E8F4EC] text-[#2C6E49] border border-[#C5E1D0]";
      case "SUSPENDED":
        return "bg-[#FEF3E2] text-[#A65E00] border border-[#FADBB0]";
      case "DISABLED":
        return "bg-[#FCEBEB] text-[#9E2A2B] border border-[#F5C2B8]";
      default:
        return "bg-[#FDF5EE] text-[#6E5652] border border-[#EADBCE]";
    }
  };

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case "ADMIN":
        return "bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4]";
      case "INTERVIEWER":
        return "bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4]";
      case "CANDIDATE":
        return "bg-[#FFFDFB] text-[#6E5652] border border-[#EADBCE]";
      default:
        return "bg-[#FFFDFB] text-[#6E5652] border border-[#EADBCE]";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="font-serif text-2xl sm:text-3xl font-normal text-[#342523]">User Management</h2>
          <p className="text-sm text-[#6E5652] mt-1">
            Inspect registered accounts, filter by role/status, and manage account state safely.
          </p>
        </div>
        <button
          onClick={() => fetchUsers()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] shadow-sm transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-[#6E5652] ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-2xl bg-[#FCEBEB] p-4 border border-red-200">
          <div className="flex items-center gap-2 text-sm text-[#9E2A2B] font-medium">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="rounded-[24px] border border-[#EADBCE] bg-white p-4 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="sm:col-span-2 relative">
            <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-[#96817D]" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] pl-10 pr-4 py-2 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-[#96817D]" />
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full rounded-xl border border-[#EADBCE] px-3 py-2 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25] bg-[#FFFDFB]"
              >
                <option value="ALL">All Roles</option>
                <option value="CANDIDATE">Candidate</option>
                <option value="INTERVIEWER">Interviewer</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setOffset(0);
              }}
              className="w-full rounded-xl border border-[#EADBCE] px-3 py-2 text-sm text-[#342523] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25] bg-[#FFFDFB]"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="DISABLED">Disabled</option>
            </select>
          </div>
        </form>
      </div>

      {/* Users Table */}
      <div className="overflow-hidden rounded-[24px] border border-[#EADBCE] bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#EADBCE] text-left text-sm">
            <thead className="bg-[#FFFDFB] text-xs font-semibold text-[#6E5652] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">User</th>
                <th className="px-6 py-3.5">Role</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Email Verified</th>
                <th className="px-6 py-3.5">Joined</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EADBCE] bg-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-[#6E5652]">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[#9B3B25] border-t-transparent" />
                    <p className="mt-2 text-xs">Loading users...</p>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-[#6E5652]">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-[#FFF8F0]/60 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="font-medium text-[#342523]">{u.full_name}</div>
                        <div className="text-xs text-[#6E5652]">{u.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getRoleBadge(
                          u.role
                        )}`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getStatusBadge(
                          u.status
                        )}`}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.email_verified ? (
                        <span className="flex items-center gap-1 text-xs text-[#2C6E49] font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                        </span>
                      ) : (
                        <span className="text-xs text-[#96817D]">Unverified</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-[#6E5652]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <button
                        onClick={() => openStatusModal(u)}
                        className="rounded-full border border-[#EADBCE] bg-white px-3.5 py-1 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] shadow-sm transition"
                      >
                        Manage Status
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between border-t border-[#EADBCE] px-6 py-3.5 bg-[#FFFDFB]">
          <span className="text-xs text-[#6E5652]">
            Showing <span className="font-semibold text-[#342523]">{users.length > 0 ? offset + 1 : 0}</span> to{" "}
            <span className="font-semibold text-[#342523]">{Math.min(offset + limit, total)}</span> of{" "}
            <span className="font-semibold text-[#342523]">{total}</span> users
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || loading}
              className="rounded-full border border-[#EADBCE] bg-white px-3.5 py-1 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total || loading}
              className="rounded-full border border-[#EADBCE] bg-white px-3.5 py-1 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Account Status Modal Dialog */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-[24px] bg-white p-6 sm:p-8 shadow-xl border border-[#EADBCE]">
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#FEF3E2] text-[#A65E00]">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-serif text-lg font-normal text-[#342523]">Manage Account Status</h3>
                <p className="text-xs text-[#6E5652]">{selectedUser.email}</p>
              </div>
            </div>

            {actionError && (
              <div className="mt-4 rounded-2xl bg-[#FCEBEB] p-3 border border-red-200 text-xs text-[#9E2A2B] flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateStatus} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">Target Account Status</label>
                <div className="space-y-2">
                  {(["ACTIVE", "SUSPENDED", "DISABLED"] as UserStatus[]).map((st) => (
                    <label
                      key={st}
                      className={`flex items-center justify-between rounded-xl border p-3 text-xs cursor-pointer transition ${
                        targetStatus === st ? "border-[#9B3B25] bg-[#FDF5EE]" : "border-[#EADBCE] bg-[#FFFDFB] hover:bg-white"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="status"
                          value={st}
                          checked={targetStatus === st}
                          onChange={() => setTargetStatus(st)}
                          className="accent-[#9B3B25]"
                        />
                        <span className="font-medium text-[#342523]">{st}</span>
                      </div>
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${getStatusBadge(
                          st
                        )}`}
                      >
                        {st}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                  Reason for Status Change {targetStatus !== "ACTIVE" && <span className="text-[#9E2A2B]">*</span>}
                </label>
                <textarea
                  rows={3}
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder="Provide audit justification (e.g., terms violation, abusive behaviour, user request)..."
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] p-3 text-xs text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  required={targetStatus !== "ACTIVE"}
                />
              </div>

              {selectedUser.id === apiUser?.id && targetStatus !== "ACTIVE" && (
                <p className="text-xs text-[#9E2A2B] font-medium flex items-center gap-1">
                  <UserX className="h-3.5 w-3.5" />
                  You cannot suspend or disable your own active administrator account.
                </p>
              )}

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setSelectedUser(null)}
                  disabled={submitting}
                  className="rounded-full border border-[#EADBCE] bg-white px-4 py-2 text-xs font-medium text-[#342523] hover:bg-[#FDF5EE] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || (selectedUser.id === apiUser?.id && targetStatus !== "ACTIVE")}
                  className="rounded-full bg-[#9B3B25] px-5 py-2 text-xs font-medium text-white shadow-sm hover:bg-[#83321F] disabled:opacity-50 transition"
                >
                  {submitting ? "Updating..." : "Confirm Status Change"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
