import type { ExchangeDesktopTicketResponse } from "@interview-ready/api-types";
import { AlertCircle, Camera, CameraOff, Mic, MicOff, Shield, Video, VideoOff } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";

interface DevicePreviewProps {
  session: ExchangeDesktopTicketResponse;
  onJoinRoom: (settings: { isMicOn: boolean; isCamOn: boolean }) => void;
  onCancel: () => void;
}

export function DevicePreview({ session, onJoinRoom, onCancel }: DevicePreviewProps) {
  const [isMicOn, setIsMicOn] = useState(true);
  const [isCamOn, setIsCamOn] = useState(true);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    let active = true;

    async function setupPreviewStream() {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
          });

          if (!active) {
            stream.getTracks().forEach((track) => track.stop());
            return;
          }

          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        }
      } catch (err: unknown) {
        if (!active) return;
        const e = err as { name?: string; message?: string };
        if (e.name === "NotAllowedError" || e.name === "PermissionDeniedError") {
          setPermissionError("Camera or microphone permission was denied. Please grant access in system settings.");
        } else {
          // Device not found or simulated environment
          setPermissionError(null);
        }
      }
    }

    if (isCamOn) {
      setupPreviewStream();
    }

    return () => {
      active = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    };
  }, [isCamOn]);

  const toggleCamera = () => {
    if (isCamOn) {
      if (streamRef.current) {
        streamRef.current.getVideoTracks().forEach((t) => (t.enabled = false));
      }
      setIsCamOn(false);
    } else {
      setIsCamOn(true);
    }
  };

  const toggleMic = () => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach((t) => (t.enabled = !isMicOn));
    }
    setIsMicOn(!isMicOn);
  };

  const isInterviewer = session.role === "INTERVIEWER" || session.role === "interviewer";

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-[#FFF8F0] p-6 text-[#342523]"
      data-testid="device-preview-screen"
    >
      <div className="w-full max-w-2xl rounded-[28px] border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#EADBCE] pb-5 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-2 w-2 rounded-full bg-[#2C6E49] animate-pulse" />
              <h2 className="font-serif text-2xl font-normal text-[#342523]">Interview Check-in & Setup</h2>
            </div>
            <p className="text-xs text-[#6E5652]">
              Review your camera and audio settings before joining the live session.
            </p>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
              isInterviewer ? "bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4]" : "bg-[#F8DDC9] text-[#342523] border border-[#ECC2A4]"
            }`}
          >
            <Shield className="h-3 w-3" />
            {isInterviewer ? "Interviewer" : "Candidate"}
          </span>
        </div>

        {permissionError && (
          <div className="mb-6 flex items-start gap-2.5 rounded-2xl border border-red-200 bg-[#FCEBEB] p-4 text-xs text-[#9E2A2B]">
            <AlertCircle className="h-4 w-4 shrink-0 text-[#9E2A2B] mt-0.5" />
            <div>
              <span className="font-semibold block mb-0.5">Device Access Notice:</span>
              {permissionError}
            </div>
          </div>
        )}

        {/* Video Preview Box */}
        <div className="relative aspect-video w-full overflow-hidden rounded-[20px] border border-[#342523]/20 bg-[#1e1514] flex items-center justify-center mb-6 shadow-inner">
          {isCamOn ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-full w-full object-cover mirror scale-x-[-1]"
              data-testid="local-video-preview"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-[#96817D]">
              <VideoOff className="h-12 w-12 text-[#96817D]" />
              <span className="text-sm font-medium">Camera is turned off</span>
            </div>
          )}

          {/* Bottom Floating Control Bar */}
          <div className="absolute bottom-4 flex items-center gap-3 rounded-full bg-[#1e1514]/80 px-4 py-2 backdrop-blur-md border border-white/10">
            <button
              onClick={toggleMic}
              aria-label={isMicOn ? "Mute microphone" : "Unmute microphone"}
              className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
                isMicOn
                  ? "bg-white/20 text-white hover:bg-white/30"
                  : "bg-[#9E2A2B] text-white hover:bg-[#802223]"
              }`}
              data-testid="preview-toggle-mic"
            >
              {isMicOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
            </button>

            <button
              onClick={toggleCamera}
              aria-label={isCamOn ? "Turn off camera" : "Turn on camera"}
              className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
                isCamOn
                  ? "bg-white/20 text-white hover:bg-white/30"
                  : "bg-[#9E2A2B] text-white hover:bg-[#802223]"
              }`}
              data-testid="preview-toggle-cam"
            >
              {isCamOn ? <Camera className="h-5 w-5" /> : <CameraOff className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={onCancel}
            className="rounded-full border border-[#EADBCE] bg-white px-6 py-2.5 text-sm font-medium text-[#342523] hover:bg-[#FDF5EE] transition"
            data-testid="preview-cancel-btn"
          >
            Cancel
          </button>

          <button
            onClick={() => onJoinRoom({ isMicOn, isCamOn })}
            className="flex items-center gap-2 rounded-full bg-[#9B3B25] px-6 py-2.5 text-sm font-medium text-white shadow-lg hover:bg-[#83321F] active:scale-95 transition"
            data-testid="enter-room-btn"
          >
            <Video className="h-4 w-4" />
            Enter Live Room
          </button>
        </div>
      </div>
    </div>
  );
}
