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
      className="flex h-screen w-screen flex-col bg-[#FFF8F0] text-[#342523] overflow-hidden font-sans"
      data-testid="live-interview-room"
      data-role={session.role}
    >
      {/* Top Session Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-[#EADBCE] bg-[#FFFDFB] px-6 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                connectionStatus === "connected"
                  ? "bg-[#2C6E49] animate-pulse"
                  : connectionStatus === "reconnecting"
                    ? "bg-[#A65E00] animate-ping"
                    : "bg-[#9E2A2B]"
              }`}
            />
            <span className="font-medium text-xs sm:text-sm text-[#342523]">
              LiveKit Room: <span className="font-mono text-[#6E5652]">{session.room_name}</span>
            </span>
          </div>

          <span className="text-[#EADBCE]">|</span>

          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
              isInterviewer
                ? "bg-[#F8DDC9] text-[#9B3B25] border border-[#ECC2A4]"
                : "bg-[#FBF2ED] text-[#9B3B25] border border-[#EADBCE]"
            }`}
          >
            <Shield className="h-3 w-3" />
            {isInterviewer ? "Interviewer" : "Candidate"}
          </span>
        </div>

        {/* Connection status banner */}
        <div className="flex items-center gap-3">
          {connectionStatus === "connected" ? (
            <span className="flex items-center gap-1.5 rounded-full bg-[#E8F4EC] border border-[#C2E0CC] px-2.5 py-0.5 text-xs text-[#2C6E49] font-medium">
              <Wifi className="h-3.5 w-3.5" />
              WebRTC Connected
            </span>
          ) : connectionStatus === "reconnecting" ? (
            <span className="flex items-center gap-1.5 rounded-full bg-[#FEF3E2] border border-[#ECC2A4] px-2.5 py-0.5 text-xs text-[#A65E00] font-medium animate-pulse">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              Reconnecting to media server...
            </span>
          ) : (
            <span className="flex items-center gap-1.5 rounded-full bg-[#FCEBEB] border border-[#F5C2C2] px-2.5 py-0.5 text-xs text-[#9E2A2B] font-medium">
              <WifiOff className="h-3.5 w-3.5" />
              Disconnected
            </span>
          )}

          <button
            onClick={handleSimulateReconnect}
            title="Reconnect LiveKit connection"
            className="rounded-full p-1.5 text-[#6E5652] hover:bg-[#F8DDC9]/50 hover:text-[#342523] transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </header>

      {/* Main Workspace Split */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Column: Video Area */}
        <section
          className={`flex flex-col justify-between p-4 bg-[#1E1715] ${
            isInterviewer ? "w-2/5 border-r border-[#342523]" : "w-full lg:w-3/5"
          }`}
          data-testid="video-area-column"
        >
          {/* Video Grid */}
          <div className="grid flex-1 grid-cols-1 gap-4 overflow-y-auto">
            {/* Remote Participant Tile */}
            <div className="relative flex aspect-video w-full items-center justify-center rounded-[20px] border border-[#3A2D2A] bg-[#140E0C] shadow-inner overflow-hidden">
              <div className="flex flex-col items-center gap-2 text-center text-[#96817D]">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#2A201D] text-[#F8DDC9]">
                  <Users className="h-8 w-8" />
                </div>
                <span className="text-sm font-semibold text-[#FBF2ED]">
                  {isInterviewer ? "Candidate Video Stream" : "Interviewer Video Stream"}
                </span>
                <span className="text-xs text-[#96817D]">Audio/Video Active • 1080p</span>
              </div>

              {/* Remote Badges */}
              <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-full bg-black/70 px-3 py-1 text-xs text-white backdrop-blur-md">
                <span className="h-2 w-2 rounded-full bg-[#2C6E49]" />
                <span>{isInterviewer ? "Candidate" : "Interviewer"}</span>
              </div>
            </div>

            {/* Local Participant Tile */}
            <div className="relative flex h-44 w-full items-center justify-center rounded-[20px] border border-[#3A2D2A] bg-[#140E0C] shadow-inner overflow-hidden">
              {isCamOn ? (
                <div className="flex items-center justify-center h-full w-full bg-[#1A1210]/60 text-[#F8DDC9] text-xs">
                  <span>Local Camera Preview Active</span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-1.5 text-[#96817D]">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#2A201D] text-[#96817D]">
                    <CameraOff className="h-5 w-5" />
                  </div>
                  <span className="text-xs">Camera Off</span>
                </div>
              )}

              {/* Local Badges */}
              <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1.5 rounded-full bg-black/70 px-3 py-0.5 text-xs text-white backdrop-blur-md">
                <span>You ({session.role})</span>
                {!isMicOn && <MicOff className="h-3 w-3 text-[#9E2A2B]" />}
              </div>
            </div>
          </div>

          {/* Bottom Floating Control Bar */}
          <div className="mt-4 flex items-center justify-center gap-4 rounded-full border border-[#44332F] bg-[#2A201D]/90 py-2.5 px-6 shadow-xl backdrop-blur-md">
            <button
              onClick={() => setIsMicOn(!isMicOn)}
              aria-label={isMicOn ? "Mute" : "Unmute"}
              className={`flex h-11 w-11 items-center justify-center rounded-full transition cursor-pointer ${
                isMicOn
                  ? "bg-[#3D2E2A] text-[#F8DDC9] hover:bg-[#4E3B36]"
                  : "bg-[#9E2A2B] text-white hover:bg-[#B33132]"
              }`}
              data-testid="room-toggle-mic"
            >
              {isMicOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
            </button>

            <button
              onClick={() => setIsCamOn(!isCamOn)}
              aria-label={isCamOn ? "Stop Video" : "Start Video"}
              className={`flex h-11 w-11 items-center justify-center rounded-full transition cursor-pointer ${
                isCamOn
                  ? "bg-[#3D2E2A] text-[#F8DDC9] hover:bg-[#4E3B36]"
                  : "bg-[#9E2A2B] text-white hover:bg-[#B33132]"
              }`}
              data-testid="room-toggle-cam"
            >
              {isCamOn ? <Camera className="h-5 w-5" /> : <CameraOff className="h-5 w-5" />}
            </button>

            <button
              onClick={onLeaveRoom}
              aria-label="Leave call"
              className="flex items-center gap-2 rounded-full bg-[#9B3B25] px-5 py-2.5 text-sm font-medium text-white shadow-md hover:bg-[#83321F] active:scale-95 transition cursor-pointer"
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
            className="flex flex-1 flex-col bg-[#FFFDFB] overflow-hidden"
            data-testid="interviewer-workspace"
          >
            {/* Tab Navigation */}
            <div className="flex border-b border-[#EADBCE] bg-[#FFF8F0]/70 px-6 gap-2">
              <button
                onClick={() => setActiveTab("rubric")}
                className={`flex items-center gap-2 px-4 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition cursor-pointer ${
                  activeTab === "rubric"
                    ? "border-[#9B3B25] text-[#9B3B25]"
                    : "border-transparent text-[#6E5652] hover:text-[#342523]"
                }`}
                data-testid="tab-interviewer-rubric"
              >
                <BookOpen className="h-4 w-4" />
                Evaluation Rubric
              </button>

              <button
                onClick={() => setActiveTab("notes")}
                className={`flex items-center gap-2 px-4 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition cursor-pointer ${
                  activeTab === "notes"
                    ? "border-[#9B3B25] text-[#9B3B25]"
                    : "border-transparent text-[#6E5652] hover:text-[#342523]"
                }`}
                data-testid="tab-interviewer-notes"
              >
                <Lock className="h-4 w-4 text-[#A65E00]" />
                Private Notes
              </button>

              <button
                onClick={() => setActiveTab("scratchpad")}
                className={`flex items-center gap-2 px-4 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition cursor-pointer ${
                  activeTab === "scratchpad"
                    ? "border-[#9B3B25] text-[#9B3B25]"
                    : "border-transparent text-[#6E5652] hover:text-[#342523]"
                }`}
                data-testid="tab-interviewer-scratchpad"
              >
                <Code2 className="h-4 w-4" />
                Shared Scratchpad
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-8">
              {activeTab === "rubric" && (
                <div className="space-y-6" data-testid="rubric-panel">
                  <div className="flex items-center justify-between pb-2 border-b border-[#EADBCE]">
                    <div>
                      <h3 className="font-serif text-lg font-normal text-[#342523]">
                        Standardized Evaluation Rubric
                      </h3>
                      <p className="text-xs text-[#6E5652]">
                        Score 1 (Poor) to 5 (Exceptional)
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3.5">
                    {[
                      { id: "problem_solving", label: "Problem Solving & Analytical Thinking" },
                      { id: "system_architecture", label: "System Design & Architecture" },
                      { id: "code_quality", label: "Code Quality, Modularity & Edge Cases" },
                      { id: "communication", label: "Communication, Clarifications & Collaboration" },
                    ].map((criteria) => (
                      <div
                        key={criteria.id}
                        className="rounded-[20px] border border-[#EADBCE] bg-[#FFF8F0]/40 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
                      >
                        <span className="text-sm font-medium text-[#342523]">{criteria.label}</span>
                        <div className="flex items-center gap-1.5">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star}
                              type="button"
                              onClick={() => handleScoreChange(criteria.id, star)}
                              aria-label={`Score ${star} for ${criteria.label}`}
                              className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition cursor-pointer ${
                                (rubricScores[criteria.id] || 0) >= star
                                  ? "bg-[#9B3B25] text-white shadow-xs"
                                  : "bg-[#FBF2ED] text-[#6E5652] hover:bg-[#F8DDC9] hover:text-[#9B3B25]"
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
                    <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-2">
                      Structured Feedback & Recommendations
                    </label>
                    <textarea
                      rows={5}
                      value={rubricFeedback}
                      onChange={(e) => setRubricFeedback(e.target.value)}
                      placeholder="Enter detailed feedback on candidate strengths, areas of improvement, and concrete next steps..."
                      className="w-full rounded-2xl border border-[#EADBCE] bg-[#FFF8F0] p-4 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
                    />
                  </div>
                </div>
              )}

              {activeTab === "notes" && (
                <div className="space-y-4" data-testid="private-notes-panel">
                  <div className="flex items-center gap-2.5 text-[#A65E00] text-xs bg-[#FEF3E2] border border-[#ECC2A4] p-3.5 rounded-2xl">
                    <Lock className="h-4 w-4 shrink-0 text-[#9B3B25]" />
                    <span className="font-medium">
                      Private Notes are confidential to you and are never visible to the candidate.
                    </span>
                  </div>

                  <textarea
                    rows={16}
                    value={interviewerNotes}
                    onChange={(e) => setInterviewerNotes(e.target.value)}
                    placeholder="Type private observations, time milestones, solution efficiency hints..."
                    className="w-full rounded-2xl border border-[#EADBCE] bg-[#FFF8F0] p-4 font-mono text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25] transition"
                    data-testid="private-notes-textarea"
                  />
                </div>
              )}

              {activeTab === "scratchpad" && (
                <div className="h-full flex flex-col space-y-3" data-testid="shared-scratchpad-panel">
                  <div className="flex items-center justify-between text-xs text-[#6E5652]">
                    <span className="font-medium">Collaborative Problem & Code Scratchpad</span>
                    <span className="flex items-center gap-1 rounded-full bg-[#E8F4EC] border border-[#C2E0CC] px-2.5 py-0.5 text-xs text-[#2C6E49] font-medium">
                      <CheckCircle2 className="h-3 w-3" /> Sync Active
                    </span>
                  </div>
                  <textarea
                    rows={18}
                    value={scratchpadContent}
                    onChange={(e) => setScratchpadContent(e.target.value)}
                    className="w-full flex-1 rounded-2xl border border-[#3A2D2A] bg-[#1E1715] p-4 font-mono text-sm text-[#F8DDC9] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none transition"
                    data-testid="scratchpad-textarea"
                  />
                </div>
              )}
            </div>
          </section>
        ) : (
          /* Candidate Right Side: Shared Scratchpad Only (No Rubric or Private Notes!) */
          <section
            className="hidden lg:flex flex-1 flex-col bg-[#FFFDFB] border-l border-[#EADBCE] p-6 sm:p-8 overflow-hidden"
            data-testid="candidate-scratchpad-panel"
          >
            <div className="flex items-center justify-between pb-3.5 border-b border-[#EADBCE] mb-4">
              <div className="flex items-center gap-2">
                <Code2 className="h-5 w-5 text-[#9B3B25]" />
                <h3 className="font-serif text-lg font-normal text-[#342523]">Shared Coding Scratchpad</h3>
              </div>
              <span className="text-xs text-[#6E5652] font-medium rounded-full bg-[#FBF2ED] border border-[#EADBCE] px-2.5 py-0.5">
                Live Sync
              </span>
            </div>

            <textarea
              rows={22}
              value={scratchpadContent}
              onChange={(e) => setScratchpadContent(e.target.value)}
              className="w-full flex-1 rounded-2xl border border-[#3A2D2A] bg-[#1E1715] p-4 font-mono text-sm text-[#F8DDC9] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none transition"
              data-testid="candidate-scratchpad-textarea"
            />
          </section>
        )}
      </main>
    </div>
  );
}
