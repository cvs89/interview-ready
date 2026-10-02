import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../../context/AuthContext";
import AdminLayout from "./layout";
import AdminOverviewPage from "./page";
import AdminUsersPage from "./users/page";
import AdminVerificationsPage from "./verifications/page";
import AdminBookingsPage from "./bookings/page";
import AdminAuditLogsPage from "./audit-logs/page";

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/admin",
}));

describe("Admin Portal Frontend", () => {
  const mockGet = vi.fn();
  const mockPatch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AdminLayout Access Guard", () => {
    it("denies access if user is not ADMIN", () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "cand_uid" },
        apiUser: { role: "CANDIDATE" },
        loading: false,
      });

      render(
        <AdminLayout>
          <div>Protected Content</div>
        </AdminLayout>
      );

      expect(screen.getByText("Access Denied")).toBeInTheDocument();
      expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    });

    it("renders admin navigation and children if user is ADMIN", () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { role: "ADMIN" },
        loading: false,
      });

      render(
        <AdminLayout>
          <div>Protected Content</div>
        </AdminLayout>
      );

      expect(screen.getByText("Operations Control Portal")).toBeInTheDocument();
      expect(screen.getByText("Protected Content")).toBeInTheDocument();
    });
  });

  describe("AdminOverviewPage", () => {
    it("renders operational overview and statistics", async () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { role: "ADMIN" },
        api: {
          get: mockGet,
        },
      });

      mockGet
        .mockResolvedValueOnce({ total: 42 })
        .mockResolvedValueOnce({ total: 5 })
        .mockResolvedValueOnce({ total: 18 });

      render(<AdminOverviewPage />);

      await waitFor(() => {
        expect(screen.getByText("Operations Center")).toBeInTheDocument();
        expect(screen.getByText("42")).toBeInTheDocument();
        expect(screen.getByText("5")).toBeInTheDocument();
        expect(screen.getByText("18")).toBeInTheDocument();
      });
    });
  });

  describe("AdminUsersPage", () => {
    it("fetches and renders user list and opens status change modal", async () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { id: "admin-id", role: "ADMIN" },
        api: {
          get: mockGet,
          patch: mockPatch,
        },
      });

      mockGet.mockResolvedValue({
        items: [
          {
            id: "user-1",
            email: "candidate@test.com",
            full_name: "Candidate Test",
            role: "CANDIDATE",
            status: "ACTIVE",
            email_verified: true,
            created_at: "2026-10-02T12:00:00Z",
            updated_at: "2026-10-02T12:00:00Z",
          },
        ],
        total: 1,
        limit: 10,
        offset: 0,
      });

      render(<AdminUsersPage />);

      await waitFor(() => {
        expect(screen.getByText("Candidate Test")).toBeInTheDocument();
        expect(screen.getByText("candidate@test.com")).toBeInTheDocument();
      });

      const manageBtn = screen.getByRole("button", { name: "Manage Status" });
      fireEvent.click(manageBtn);

      expect(screen.getByText("Manage Account Status")).toBeInTheDocument();
      expect(screen.getByText("Confirm Status Change")).toBeInTheDocument();
    });
  });

  describe("AdminVerificationsPage", () => {
    it("fetches and renders verification queue and opens review modal", async () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { id: "admin-id", role: "ADMIN" },
        api: {
          get: mockGet,
          patch: mockPatch,
        },
      });

      mockGet.mockResolvedValue({
        items: [
          {
            id: "verif-1",
            interviewer_id: "int-1",
            user_id: "user-int-1",
            full_name: "Interviewer Test",
            email: "int@test.com",
            title: "Staff Engineer",
            years_experience: 7,
            status: "PENDING",
            submitted_at: "2026-10-02T10:00:00Z",
          },
        ],
        total: 1,
        limit: 10,
        offset: 0,
      });

      render(<AdminVerificationsPage />);

      await waitFor(() => {
        expect(screen.getByText("Interviewer Test")).toBeInTheDocument();
        expect(screen.getByText("Staff Engineer")).toBeInTheDocument();
      });

      const reviewBtn = screen.getByRole("button", { name: "Review" });
      fireEvent.click(reviewBtn);

      expect(screen.getByText("Review Interviewer Application")).toBeInTheDocument();
      expect(screen.getByText("Approve Interviewer")).toBeInTheDocument();
      expect(screen.getByText("Reject Application")).toBeInTheDocument();
    });
  });

  describe("AdminBookingsPage", () => {
    it("fetches and renders bookings table and opens inspection modal", async () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { id: "admin-id", role: "ADMIN" },
        api: {
          get: mockGet,
          patch: mockPatch,
        },
      });

      mockGet.mockResolvedValue({
        items: [
          {
            id: "booking-1234-5678",
            slot_id: "slot-1",
            candidate_id: "cand-1",
            candidate_name: "Candidate Test",
            candidate_email: "cand@test.com",
            interviewer_id: "int-1",
            interviewer_name: "Interviewer Test",
            interviewer_email: "int@test.com",
            status: "CONFIRMED",
            slot_start_time: "2026-10-05T10:00:00Z",
            slot_end_time: "2026-10-05T11:00:00Z",
            price_minor: 15000,
            currency: "USD",
            payment_status: "PAID",
            created_at: "2026-10-02T12:00:00Z",
          },
        ],
        total: 1,
        limit: 10,
        offset: 0,
      });

      render(<AdminBookingsPage />);

      await waitFor(() => {
        expect(screen.getByText("Candidate Test")).toBeInTheDocument();
        expect(screen.getByText("Interviewer Test")).toBeInTheDocument();
      });

      const inspectBtn = screen.getByTitle("View booking details");
      fireEvent.click(inspectBtn);

      expect(screen.getByText("Booking Inspection")).toBeInTheDocument();
      expect(screen.getByText("Participants")).toBeInTheDocument();
    });
  });

  describe("AdminAuditLogsPage", () => {
    it("fetches and renders audit log entries", async () => {
      (useAuth as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        user: { uid: "admin_uid" },
        apiUser: { id: "admin-id", role: "ADMIN" },
        api: {
          get: mockGet,
        },
      });

      mockGet.mockResolvedValue([
        {
          id: "audit-1",
          event_type: "ADMIN_USER_STATUS_UPDATED",
          resource_type: "USER",
          resource_id: "user-123",
          actor_user_id: "admin-1",
          metadata: { old_status: "ACTIVE", new_status: "SUSPENDED" },
          created_at: "2026-10-02T12:00:00Z",
        },
      ]);

      render(<AdminAuditLogsPage />);

      await waitFor(() => {
        expect(screen.getByText("ADMIN_USER_STATUS_UPDATED")).toBeInTheDocument();
        expect(screen.getByText("USER")).toBeInTheDocument();
      });
    });
  });
});
