"use client";

import { AlertCircle, ArrowRight, Briefcase, CheckCircle2, DollarSign, Loader2, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

import { useAuth } from "../../../context/AuthContext";

export default function InterviewerAuthPage() {
  const router = useRouter();
  const { user, signInWithGoogle, signInWithEmail, signUpWithEmail } = useAuth();

  const [mode, setMode] = useState<"register" | "login">("register");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) {
    router.push("/interviewer");
  }

  const handleGoogleAuth = async () => {
    setError(null);
    setLoading(true);
    try {
      await signInWithGoogle();
      router.push("/interviewer");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setError(eObj.message || "Google authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await signUpWithEmail(email, password, fullName);
      } else {
        await signInWithEmail(email, password);
      }
      router.push("/interviewer");
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setError(eObj.message || "Authentication failed. Please check your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#FFF8F0] py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Value Proposition */}
          <div className="lg:col-span-7 space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-3.5 py-1 text-xs font-semibold text-[#9B3B25]">
              <Briefcase className="h-4 w-4" />
              <span>Interviewer Network</span>
            </div>

            <h1 className="font-serif text-3xl sm:text-5xl font-normal text-[#342523] tracking-tight leading-tight">
              Conduct mock interviews. <br />
              <span className="text-[#9B3B25]">Mentor the next generation & earn.</span>
            </h1>

            <p className="text-base sm:text-lg text-[#6E5652] leading-relaxed">
              Join our curated network of senior engineers, tech leads, and hiring managers.
              Help ambitious candidates crack their dream tech interviews while setting your own rates and schedule.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="flex items-start gap-3.5 rounded-[20px] border border-[#EADBCE] bg-white p-4 shadow-sm">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25]">
                  <DollarSign className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-medium text-[#342523] text-sm">Set Your Own Rates</h4>
                  <p className="text-xs text-[#6E5652] mt-0.5">Keep 100% control over your slot pricing in your local currency.</p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 rounded-[20px] border border-[#EADBCE] bg-white p-4 shadow-sm">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#FDF5EE] text-[#9B3B25]">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-medium text-[#342523] text-sm">Flexible Calendar</h4>
                  <p className="text-xs text-[#6E5652] mt-0.5">Publish availability slots when you have free time.</p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 rounded-[20px] border border-[#EADBCE] bg-white p-4 shadow-sm">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#E8F4EC] text-[#2C6E49]">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-medium text-[#342523] text-sm">Verified Expert Badge</h4>
                  <p className="text-xs text-[#6E5652] mt-0.5">Stand out on the marketplace after peer credentials verification.</p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 rounded-[20px] border border-[#EADBCE] bg-white p-4 shadow-sm">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#FEF3E2] text-[#A65E00]">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-medium text-[#342523] text-sm">Built-in WebRTC & IDE</h4>
                  <p className="text-xs text-[#6E5652] mt-0.5">Seamless live video and collaborative workspace ready to go.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Auth Card */}
          <div className="lg:col-span-5">
            <div className="rounded-[24px] border border-[#EADBCE] bg-white p-8 shadow-sm">
              <div className="flex border-b border-[#EADBCE] pb-3 mb-6">
                <button
                  type="button"
                  onClick={() => setMode("register")}
                  className={`flex-1 text-center pb-2 text-sm font-semibold transition border-b-2 ${
                    mode === "register"
                      ? "border-[#9B3B25] text-[#9B3B25]"
                      : "border-transparent text-[#6E5652] hover:text-[#342523]"
                  }`}
                >
                  Apply as Interviewer
                </button>
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  className={`flex-1 text-center pb-2 text-sm font-semibold transition border-b-2 ${
                    mode === "login"
                      ? "border-[#9B3B25] text-[#9B3B25]"
                      : "border-transparent text-[#6E5652] hover:text-[#342523]"
                  }`}
                >
                  Interviewer Sign In
                </button>
              </div>

              {error && (
                <div className="mb-6 flex items-center gap-2 rounded-2xl border border-red-200 bg-[#FCEBEB] p-3 text-sm text-[#9E2A2B]" role="alert">
                  <AlertCircle className="h-4 w-4 shrink-0 text-[#9E2A2B]" />
                  <span>{error}</span>
                </div>
              )}

              {/* Google Button */}
              <button
                type="button"
                onClick={handleGoogleAuth}
                disabled={loading}
                className="flex w-full items-center justify-center gap-3 rounded-full border border-[#EADBCE] bg-white px-4 py-2.5 text-sm font-medium text-[#342523] shadow-sm hover:bg-[#FDF5EE] transition disabled:opacity-50"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Continue with Google</span>
              </button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[#EADBCE]" />
                </div>
                <div className="relative flex justify-center text-xs uppercase tracking-wider">
                  <span className="bg-white px-3 text-[#96817D]">Or with work email</span>
                </div>
              </div>

              {/* Email/Password Form */}
              <form onSubmit={handleEmailAuth} className="space-y-4">
                {mode === "register" && (
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Work Email
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-[#9B3B25] px-6 py-3 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : mode === "register" ? (
                    <>
                      <span>Continue to Profile Setup</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  ) : (
                    <span>Sign In to Portal</span>
                  )}
                </button>
              </form>

              <div className="mt-6 border-t border-[#EADBCE] pt-4 text-center">
                <p className="text-xs text-[#6E5652]">
                  Looking for mock interviews as a candidate?{" "}
                  <Link href="/auth/sign-in" className="text-[#9B3B25] font-medium hover:underline">
                    Candidate Sign In
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
