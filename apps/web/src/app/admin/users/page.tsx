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
        return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
      case "SUSPENDED":
        return "bg-amber-50 text-amber-700 ring-amber-600/20";
      case "DISABLED":
        return "bg-red-50 text-red-700 ring-red-600/20";
      default:
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
    }
  };

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-50 text-purple-700 ring-purple-600/20";
      case "INTERVIEWER":
        return "bg-blue-50 text-blue-700 ring-blue-600/20";
      case "CANDIDATE":
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
      default:
        return "bg-gray-50 text-gray-700 ring-gray-600/20";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">User Management</h2>
          <p className="text-sm text-gray-500">
            Inspect registered accounts, filter by role/status, and manage account state safely.
          </p>
        </div>
        <button
          onClick={() => fetchUsers()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 border border-red-200">
          <div className="flex items-center gap-2 text-sm text-red-700 font-medium">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="sm:col-span-2 relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-gray-300 pl-9 pr-4 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
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
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
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
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">User</th>
                <th className="px-6 py-3">Role</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Email Verified</th>
                <th className="px-6 py-3">Joined</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                    <p className="mt-2 text-xs">Loading users...</p>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50/50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="font-medium text-gray-900">{u.full_name}</div>
                        <div className="text-xs text-gray-500">{u.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getRoleBadge(
                          u.role
                        )}`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getStatusBadge(
                          u.status
                        )}`}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.email_verified ? (
                        <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">Unverified</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <button
                        onClick={() => openStatusModal(u)}
                        className="rounded border border-gray-300 bg-white px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
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
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3">
          <span className="text-xs text-gray-500">
            Showing <span className="font-semibold">{users.length > 0 ? offset + 1 : 0}</span> to{" "}
            <span className="font-semibold">{Math.min(offset + limit, total)}</span> of{" "}
            <span className="font-semibold">{total}</span> users
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || loading}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total || loading}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Account Status Modal Dialog */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">Manage Account Status</h3>
                <p className="text-xs text-gray-500">{selectedUser.email}</p>
              </div>
            </div>

            {actionError && (
              <div className="mt-4 rounded-lg bg-red-50 p-3 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateStatus} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Target Account Status</label>
                <div className="space-y-2">
                  {(["ACTIVE", "SUSPENDED", "DISABLED"] as UserStatus[]).map((st) => (
                    <label
                      key={st}
                      className={`flex items-center justify-between rounded-lg border p-3 text-xs cursor-pointer transition ${
                        targetStatus === st ? "border-purple-600 bg-purple-50/50" : "border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="status"
                          value={st}
                          checked={targetStatus === st}
                          onChange={() => setTargetStatus(st)}
                          className="text-purple-600 focus:ring-purple-500"
                        />
                        <span className="font-medium text-gray-900">{st}</span>
                      </div>
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${getStatusBadge(
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
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Reason for Status Change {targetStatus !== "ACTIVE" && <span className="text-red-500">*</span>}
                </label>
                <textarea
                  rows={3}
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder="Provide audit justification (e.g., terms violation, abusive behaviour, user request)..."
                  className="w-full rounded-lg border border-gray-300 p-2.5 text-xs focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  required={targetStatus !== "ACTIVE"}
                />
              </div>

              {selectedUser.id === apiUser?.id && targetStatus !== "ACTIVE" && (
                <p className="text-xs text-red-600 font-medium flex items-center gap-1">
                  <UserX className="h-3.5 w-3.5" />
                  You cannot suspend or disable your own active administrator account.
                </p>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedUser(null)}
                  disabled={submitting}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || (selectedUser.id === apiUser?.id && targetStatus !== "ACTIVE")}
                  className="rounded-lg bg-purple-600 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-purple-700 disabled:opacity-50"
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
