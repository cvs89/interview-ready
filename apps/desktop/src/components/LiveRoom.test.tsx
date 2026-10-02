import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { LiveRoom } from "./LiveRoom";

const mockInterviewerSession: ExchangeDesktopTicketResponse = {
  session_jwt: "mock.jwt.interviewer",
  livekit_url: "wss://livekit.test.com",
  livekit_token: "lk_token_int",
  room_name: "room-abc-123",
  session_id: "session-1",
  booking_id: "booking-1",
  role: "INTERVIEWER",
  expires_in_seconds: 3600,
};

const mockCandidateSession: ExchangeDesktopTicketResponse = {
  session_jwt: "mock.jwt.candidate",
  livekit_url: "wss://livekit.test.com",
  livekit_token: "lk_token_cand",
  room_name: "room-abc-123",
  session_id: "session-1",
  booking_id: "booking-1",
  role: "CANDIDATE",
  expires_in_seconds: 3600,
};

describe("LiveRoom", () => {
  it("renders interviewer layout with 40% video area and 60% evaluation workspace", () => {
    const onLeave = vi.fn();

    render(
      <LiveRoom
        session={mockInterviewerSession}
        initialSettings={{ isMicOn: true, isCamOn: true }}
        onLeaveRoom={onLeave}
      />
    );

    expect(screen.getByTestId("live-interview-room")).toBeInTheDocument();
    expect(screen.getByTestId("video-area-column")).toBeInTheDocument();
    expect(screen.getByTestId("interviewer-workspace")).toBeInTheDocument();

    // Verify interviewer tabs
    expect(screen.getByTestId("tab-interviewer-rubric")).toBeInTheDocument();
    expect(screen.getByTestId("tab-interviewer-notes")).toBeInTheDocument();
    expect(screen.getByTestId("tab-interviewer-scratchpad")).toBeInTheDocument();

    // Verify rubric panel is visible by default
    expect(screen.getByTestId("rubric-panel")).toBeInTheDocument();
  });

  it("switches to private notes tab for interviewer", () => {
    const onLeave = vi.fn();

    render(
      <LiveRoom
        session={mockInterviewerSession}
        initialSettings={{ isMicOn: true, isCamOn: true }}
        onLeaveRoom={onLeave}
      />
    );

    const notesTab = screen.getByTestId("tab-interviewer-notes");
    fireEvent.click(notesTab);

    expect(screen.getByTestId("private-notes-panel")).toBeInTheDocument();
    expect(screen.getByTestId("private-notes-textarea")).toBeInTheDocument();
  });

  it("renders candidate layout without rubric or private notes", () => {
    const onLeave = vi.fn();

    render(
      <LiveRoom
        session={mockCandidateSession}
        initialSettings={{ isMicOn: true, isCamOn: true }}
        onLeaveRoom={onLeave}
      />
    );

    expect(screen.getByTestId("live-interview-room")).toBeInTheDocument();

    // Candidate should NOT have interviewer-private workspace
    expect(screen.queryByTestId("interviewer-workspace")).not.toBeInTheDocument();
    expect(screen.queryByTestId("tab-interviewer-rubric")).not.toBeInTheDocument();
    expect(screen.queryByTestId("tab-interviewer-notes")).not.toBeInTheDocument();
    expect(screen.queryByTestId("rubric-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("private-notes-panel")).not.toBeInTheDocument();

    // Candidate has shared scratchpad
    expect(screen.getByTestId("candidate-scratchpad-panel")).toBeInTheDocument();
  });

  it("toggles mic and camera buttons and leaves call", () => {
    const onLeave = vi.fn();

    render(
      <LiveRoom
        session={mockCandidateSession}
        initialSettings={{ isMicOn: true, isCamOn: true }}
        onLeaveRoom={onLeave}
      />
    );

    const micBtn = screen.getByTestId("room-toggle-mic");
    const camBtn = screen.getByTestId("room-toggle-cam");
    const leaveBtn = screen.getByTestId("room-leave-btn");

    expect(micBtn).toHaveAttribute("aria-label", "Mute");
    expect(camBtn).toHaveAttribute("aria-label", "Stop Video");

    fireEvent.click(micBtn);
    expect(micBtn).toHaveAttribute("aria-label", "Unmute");

    fireEvent.click(camBtn);
    expect(camBtn).toHaveAttribute("aria-label", "Start Video");

    fireEvent.click(leaveBtn);
    expect(onLeave).toHaveBeenCalledTimes(1);
  });
});
