import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";
import {
  AlertCircle,
  BookOpen,
  Camera,
  CameraOff,
  CheckCircle2,
  Code2,
  FileText,
  Lock,
  Mic,
  MicOff,
  PhoneOff,
  RefreshCw,
  Share2,
  Shield,
  Star,
  Users,
  Video,
  Wifi,
  WifiOff,
} from "lucide-react";
import React, { useState } from "react";

interface LiveRoomProps {
  session: ExchangeDesktopTicketResponse;
  initialSettings: { isMicOn: boolean; isCamOn: boolean };
  onLeaveRoom: () => void;
}

export function LiveRoom({ session, initialSettings, onLeaveRoom }: LiveRoomProps) {
  const [isMicOn, setIsMicOn] = useState(initialSettings.isMicOn);
  const [isCamOn, setIsCamOn] = useState(initialSettings.isCamOn);
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "reconnecting" | "disconnected"
  >("connected");

  // Interviewer Workspace State
  const [activeTab, setActiveTab] = useState<"rubric" | "notes" | "scratchpad">("rubric");
  const [rubricScores, setRubricScores] = useState<Record<string, number>>({
    problem_solving: 4,
    system_architecture: 4,
    code_quality: 4,
    communication: 5,
  });
  const [interviewerNotes, setInterviewerNotes] = useState("");
  const [rubricFeedback, setRubricFeedback] = useState("");
  const [scratchpadContent, setScratchpadContent] = useState(
    "// Shared interview scratchpad\nfunction solution(arr) {\n  // Implementation here\n  return arr;\n}"
  );

  const isInterviewer = session.role === "INTERVIEWER" || session.role === "interviewer";

  const handleScoreChange = (criteria: string, score: number) => {
    setRubricScores((prev) => ({ ...prev, [criteria]: score }));
  };

  const handleSimulateReconnect = () => {
    setConnectionStatus("reconnecting");
    setTimeout(() => {
      setConnectionStatus("connected");
    }, 1500);
  };

  return (
    <div
      className="flex h-screen w-screen flex-col bg-[#060d17] text-white overflow-hidden"
      data-testid="live-interview-room"
      data-role={session.role}
    >
      {/* Top Session Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-800/80 bg-[#091424] px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                connectionStatus === "connected"
                  ? "bg-green-500 animate-pulse"
                  : connectionStatus === "reconnecting"
                    ? "bg-amber-500 animate-ping"
                    : "bg-red-500"
              }`}
            />
            <span className="font-bold text-sm text-gray-200">
              LiveKit Room: <span className="font-mono text-gray-400">{session.room_name}</span>
            </span>
          </div>

          <span className="text-gray-600">|</span>

          <span
            className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-bold uppercase tracking-wider ${
              isInterviewer ? "bg-purple-900/60 text-purple-300" : "bg-blue-900/60 text-blue-300"
            }`}
          >
            <Shield className="h-3 w-3" />
            {isInterviewer ? "Interviewer" : "Candidate"}
          </span>
        </div>

        {/* Connection status banner */}
        <div className="flex items-center gap-3">
          {connectionStatus === "connected" ? (
            <span className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
              <Wifi className="h-3.5 w-3.5" />
              WebRTC Connected
            </span>
          ) : connectionStatus === "reconnecting" ? (
            <span className="flex items-center gap-1.5 text-xs text-amber-400 font-medium animate-pulse">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              Reconnecting to media server...
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs text-red-400 font-medium">
              <WifiOff className="h-3.5 w-3.5" />
              Disconnected
            </span>
          )}

          <button
            onClick={handleSimulateReconnect}
            title="Reconnect LiveKit connection"
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white transition"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </header>

      {/* Main Workspace Split */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Column: Video Area */}
        <section
          className={`flex flex-col justify-between p-4 bg-[#08111f] ${
            isInterviewer ? "w-2/5 border-r border-gray-800/80" : "w-full lg:w-3/5"
          }`}
          data-testid="video-area-column"
        >
          {/* Video Grid */}
          <div className="grid flex-1 grid-cols-1 gap-4 overflow-y-auto">
            {/* Remote Participant Tile */}
            <div className="relative flex aspect-video w-full items-center justify-center rounded-2xl border border-gray-800 bg-gray-950 shadow-inner overflow-hidden">
              <div className="flex flex-col items-center gap-2 text-center text-gray-500">
                <Users className="h-12 w-12 text-gray-600" />
                <span className="text-sm font-semibold text-gray-400">
                  {isInterviewer ? "Candidate Video Stream" : "Interviewer Video Stream"}
                </span>
                <span className="text-xs text-gray-600">Audio/Video Active • 1080p</span>
              </div>

              {/* Remote Badges */}
              <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-lg bg-black/60 px-2.5 py-1 text-xs text-white backdrop-blur-md">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span>{isInterviewer ? "Candidate" : "Interviewer"}</span>
              </div>
            </div>

            {/* Local Participant Tile */}
            <div className="relative flex h-44 w-full items-center justify-center rounded-2xl border border-gray-800 bg-gray-950 shadow-inner overflow-hidden">
              {isCamOn ? (
                <div className="flex items-center justify-center h-full w-full bg-gray-900/60 text-gray-400 text-xs">
                  <span>Local Camera Preview Active</span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-1 text-gray-500">
                  <CameraOff className="h-6 w-6 text-gray-600" />
                  <span className="text-xs">Camera Off</span>
                </div>
              )}

              {/* Local Badges */}
              <div className="absolute bottom-2 left-2 flex items-center gap-1.5 rounded-lg bg-black/60 px-2 py-0.5 text-xs text-white backdrop-blur-md">
                <span>You ({session.role})</span>
                {!isMicOn && <MicOff className="h-3 w-3 text-red-400" />}
              </div>
            </div>
          </div>

          {/* Bottom Floating Control Bar */}
          <div className="mt-4 flex items-center justify-center gap-4 rounded-2xl border border-gray-800/80 bg-[#0d1b2e] py-3 px-6 shadow-xl">
            <button
              onClick={() => setIsMicOn(!isMicOn)}
              aria-label={isMicOn ? "Mute" : "Unmute"}
              className={`flex h-11 w-11 items-center justify-center rounded-xl transition ${
                isMicOn
                  ? "bg-gray-800 text-white hover:bg-gray-700"
                  : "bg-red-600 text-white hover:bg-red-500"
              }`}
              data-testid="room-toggle-mic"
            >
              {isMicOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
            </button>

            <button
              onClick={() => setIsCamOn(!isCamOn)}
              aria-label={isCamOn ? "Stop Video" : "Start Video"}
              className={`flex h-11 w-11 items-center justify-center rounded-xl transition ${
                isCamOn
                  ? "bg-gray-800 text-white hover:bg-gray-700"
                  : "bg-red-600 text-white hover:bg-red-500"
              }`}
              data-testid="room-toggle-cam"
            >
              {isCamOn ? <Camera className="h-5 w-5" /> : <CameraOff className="h-5 w-5" />}
            </button>

            <button
              onClick={onLeaveRoom}
              aria-label="Leave call"
              className="flex items-center gap-2 rounded-xl bg-red-600 px-5 py-2.5 text-sm font-bold text-white shadow hover:bg-red-700 active:scale-95 transition"
              data-testid="room-leave-btn"
            >
              <PhoneOff className="h-4 w-4" />
              Leave Room
            </button>
          </div>
        </section>

        {/* Right Column: Interviewer Workspace (60%) or Candidate Scratchpad */}
        {isInterviewer ? (
          <section
            className="flex flex-1 flex-col bg-[#091424] overflow-hidden"
            data-testid="interviewer-workspace"
          >
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-800 bg-[#0d1b2e] px-4">
              <button
                onClick={() => setActiveTab("rubric")}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
                  activeTab === "rubric"
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-gray-400 hover:text-white"
                }`}
                data-testid="tab-interviewer-rubric"
              >
                <BookOpen className="h-4 w-4" />
                Evaluation Rubric
              </button>

              <button
                onClick={() => setActiveTab("notes")}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
                  activeTab === "notes"
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-gray-400 hover:text-white"
                }`}
                data-testid="tab-interviewer-notes"
              >
                <Lock className="h-4 w-4 text-amber-400" />
                Private Notes
              </button>

              <button
                onClick={() => setActiveTab("scratchpad")}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
                  activeTab === "scratchpad"
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-gray-400 hover:text-white"
                }`}
                data-testid="tab-interviewer-scratchpad"
              >
                <Code2 className="h-4 w-4" />
                Shared Scratchpad
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === "rubric" && (
                <div className="space-y-6" data-testid="rubric-panel">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-base text-gray-100">Standardized Evaluation Rubric</h3>
                    <span className="text-xs text-gray-400">Score 1 (Poor) to 5 (Exceptional)</span>
                  </div>

                  <div className="space-y-4">
                    {[
                      { id: "problem_solving", label: "Problem Solving & Analytical Thinking" },
                      { id: "system_architecture", label: "System Design & Architecture" },
                      { id: "code_quality", label: "Code Quality, Modularity & Edge Cases" },
                      { id: "communication", label: "Communication, Clarifications & Collaboration" },
                    ].map((criteria) => (
                      <div
                        key={criteria.id}
                        className="rounded-xl border border-gray-800 bg-[#0d1b2e] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <span className="text-sm font-medium text-gray-200">{criteria.label}</span>
                        <div className="flex items-center gap-1.5">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star}
                              type="button"
                              onClick={() => handleScoreChange(criteria.id, star)}
                              aria-label={`Score ${star} for ${criteria.label}`}
                              className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold transition ${
                                (rubricScores[criteria.id] || 0) >= star
                                  ? "bg-purple-600 text-white shadow"
                                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                              }`}
                            >
                              {star}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-gray-400 mb-2">
                      Structured Feedback & Recommendations
                    </label>
                    <textarea
                      rows={5}
                      value={rubricFeedback}
                      onChange={(e) => setRubricFeedback(e.target.value)}
                      placeholder="Enter detailed feedback on candidate strengths, areas of improvement, and concrete next steps..."
                      className="w-full rounded-xl border border-gray-800 bg-[#0d1b2e] p-4 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                </div>
              )}

              {activeTab === "notes" && (
                <div className="space-y-4" data-testid="private-notes-panel">
                  <div className="flex items-center gap-2 text-amber-300 text-xs bg-amber-500/10 border border-amber-500/20 p-3 rounded-xl">
                    <Lock className="h-4 w-4 shrink-0" />
                    <span>
                      Private Notes are confidential to you and are never visible to the candidate.
                    </span>
                  </div>

                  <textarea
                    rows={16}
                    value={interviewerNotes}
                    onChange={(e) => setInterviewerNotes(e.target.value)}
                    placeholder="Type private observations, time milestones, solution efficiency hints..."
                    className="w-full rounded-xl border border-gray-800 bg-[#0d1b2e] p-4 font-mono text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    data-testid="private-notes-textarea"
                  />
                </div>
              )}

              {activeTab === "scratchpad" && (
                <div className="h-full flex flex-col space-y-2" data-testid="shared-scratchpad-panel">
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>Collaborative Problem & Code Scratchpad</span>
                    <span className="text-green-400 flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" /> Sync Active
                    </span>
                  </div>
                  <textarea
                    rows={18}
                    value={scratchpadContent}
                    onChange={(e) => setScratchpadContent(e.target.value)}
                    className="w-full flex-1 rounded-xl border border-gray-800 bg-[#08111f] p-4 font-mono text-sm text-green-400 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                    data-testid="scratchpad-textarea"
                  />
                </div>
              )}
            </div>
          </section>
        ) : (
          /* Candidate Right Side: Shared Scratchpad Only (No Rubric or Private Notes!) */
          <section
            className="hidden lg:flex flex-1 flex-col bg-[#091424] border-l border-gray-800/80 p-6 overflow-hidden"
            data-testid="candidate-scratchpad-panel"
          >
            <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-4">
              <div className="flex items-center gap-2">
                <Code2 className="h-5 w-5 text-blue-400" />
                <h3 className="font-bold text-sm text-gray-200">Shared Coding Scratchpad</h3>
              </div>
              <span className="text-xs text-gray-500 font-mono">Live Sync</span>
            </div>

            <textarea
              rows={22}
              value={scratchpadContent}
              onChange={(e) => setScratchpadContent(e.target.value)}
              className="w-full flex-1 rounded-xl border border-gray-800 bg-[#08111f] p-4 font-mono text-sm text-blue-300 placeholder-gray-600 focus:border-blue-500 focus:outline-none"
              data-testid="candidate-scratchpad-textarea"
            />
          </section>
        )}
      </main>
    </div>
  );
}
