"use client";

import type { AuditLogResponse } from "@interview-ready/api-types";
import { AlertCircle, ChevronDown, ChevronRight, RefreshCw, ShieldCheck } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../../context/AuthContext";
import { ApiError } from "../../../lib/api-client";

export default function AdminAuditLogsPage() {
  const { api } = useAuth();
  const [logs, setLogs] = useState<AuditLogResponse[]>([]);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("");
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };
      if (eventTypeFilter.trim()) params.event_type = eventTypeFilter.trim();
      if (resourceTypeFilter.trim()) params.resource_type = resourceTypeFilter.trim();

      const data = await api.get<AuditLogResponse[]>("/admin/audit-logs", { params });
      setLogs(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load audit logs");
      }
    } finally {
      setLoading(false);
    }
  }, [api, limit, offset, eventTypeFilter, resourceTypeFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Audit Trail & Security Logs</h2>
          <p className="text-sm text-gray-500">
            Immutable log of system events, administrative mutations, and verification state transitions.
          </p>
        </div>
        <button
          onClick={() => fetchLogs()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 border border-red-200 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Filter by Event Type</label>
          <input
            type="text"
            placeholder="e.g. ADMIN_USER_STATUS_UPDATED, BOOKING_CONFIRMED"
            value={eventTypeFilter}
            onChange={(e) => {
              setEventTypeFilter(e.target.value);
              setOffset(0);
            }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Filter by Resource Type</label>
          <input
            type="text"
            placeholder="e.g. USER, BOOKING, INTERVIEWER_PROFILE"
            value={resourceTypeFilter}
            onChange={(e) => {
              setResourceTypeFilter(e.target.value);
              setOffset(0);
            }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
          />
        </div>
      </div>

      {/* Logs Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Event Type</th>
                <th className="px-6 py-3">Resource</th>
                <th className="px-6 py-3">Resource ID</th>
                <th className="px-6 py-3">Actor ID</th>
                <th className="px-6 py-3">Timestamp (UTC)</th>
                <th className="px-6 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                    <p className="mt-2 text-xs">Loading audit logs...</p>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    No audit records matching filter criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isExpanded = expandedId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr className="hover:bg-gray-50/50 transition cursor-pointer" onClick={() => toggleExpand(log.id)}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700 ring-1 ring-inset ring-purple-600/20">
                            <ShieldCheck className="h-3 w-3" />
                            {log.event_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs font-medium text-gray-700">
                          {log.resource_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                          {log.resource_id.length > 12 ? `${log.resource_id.substring(0, 12)}...` : log.resource_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                          {log.actor_user_id ? `${log.actor_user_id.substring(0, 8)}...` : "SYSTEM"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                          {new Date(log.created_at).toISOString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-xs text-gray-400">
                          {isExpanded ? <ChevronDown className="inline h-4 w-4" /> : <ChevronRight className="inline h-4 w-4" />}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-gray-50/80">
                          <td colSpan={6} className="px-6 py-4">
                            <div className="rounded-lg border border-gray-200 bg-gray-900 p-3 text-xs text-emerald-400 font-mono overflow-x-auto">
                              <div className="text-gray-400 mb-1">Metadata Payload (Sanitized)</div>
                              <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3">
          <span className="text-xs text-gray-500">
            Showing <span className="font-semibold">{logs.length}</span> audit log entries
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
              disabled={logs.length < limit || loading}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
