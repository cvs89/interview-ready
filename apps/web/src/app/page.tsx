import {
  Award,
  Briefcase,
  ChevronRight,
  Clock,
  Laptop,
  ShieldCheck,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React from "react";

export default function HomePage() {
  return (
    <div className="flex flex-col bg-[#FFF8F0] min-h-screen text-[#342523]">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-16 sm:py-28 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl text-center">
          {/* Eyebrow */}
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-[#ECC2A4] bg-[#FDF5EE] px-4 py-1.5 text-xs font-semibold text-[#9B3B25] shadow-xs">
            <span className="flex h-2 w-2 rounded-full bg-[#9B3B25]" />
            <span>Real people. Useful practice.</span>
          </div>

          <h1 className="font-editorial text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-[#342523] leading-[1.12]">
            Big ambitions. A little more practice.
          </h1>

          <h2 className="font-editorial text-xl sm:text-2xl lg:text-3xl font-medium text-[#9B3B25] mt-4 max-w-3xl mx-auto leading-snug">
            Practice real technical mock interviews with vetted engineering leaders.
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-base sm:text-lg text-[#6E5652] leading-relaxed font-sans">
            Real interview practice. Specific feedback. A clearer next step. Book 1-on-1 system design, coding, and behavioral sessions with principal engineers and hiring managers.
          </p>

          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/marketplace"
              className="btn-pill-primary px-8 py-3.5 text-base shadow-md w-full sm:w-auto"
            >
              <span>Find an Interviewer</span>
              <ChevronRight className="h-5 w-5 ml-1" />
            </Link>
            <Link
              href="/auth/interviewer"
              className="btn-pill-secondary px-8 py-3.5 text-base w-full sm:w-auto"
            >
              Become an Interviewer
            </Link>
          </div>

          <p className="mt-4 text-xs font-medium text-[#96817D]">
            Choose a specific time · See the session price upfront · Real-money booking without subscription locks
          </p>
        </div>
      </section>

      {/* 4-Step Journey Section */}
      <section className="py-16 sm:py-24 bg-white border-y border-[#EADBCE]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-widest text-[#9B3B25]">
              How It Works
            </span>
            <h2 className="font-editorial text-3xl sm:text-4xl font-bold text-[#342523] mt-2">
              Four steps from booking to breakthrough.
            </h2>
            <p className="text-[#6E5652] text-sm sm:text-base mt-3">
              Clear expectations, zero guesswork. Everything you need to prepare under realistic conditions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card-confidence p-6 sm:p-7 bg-[#FFFDFB]">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] font-editorial font-bold text-lg mb-5 border border-[#ECC2A4]">
                1
              </div>
              <h3 className="font-editorial font-bold text-xl text-[#342523] mb-2">Choose an Expert</h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Browse verified technical leaders by primary domain, engineering seniority, hourly pricing, and availability.
              </p>
            </div>

            <div className="card-confidence p-6 sm:p-7 bg-[#FFFDFB]">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] font-editorial font-bold text-lg mb-5 border border-[#ECC2A4]">
                2
              </div>
              <h3 className="font-editorial font-bold text-xl text-[#342523] mb-2">Reserve Your Slot</h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Hold your preferred time with an atomic 10-minute reservation and checkout securely via Stripe with clear pricing.
              </p>
            </div>

            <div className="card-confidence p-6 sm:p-7 bg-[#FFFDFB]">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] font-editorial font-bold text-lg mb-5 border border-[#ECC2A4]">
                3
              </div>
              <h3 className="font-editorial font-bold text-xl text-[#342523] mb-2">Practise Live</h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Join through our focused desktop client featuring WebRTC video and real-time coding with zero browser distractions.
              </p>
            </div>

            <div className="card-confidence p-6 sm:p-7 bg-[#FFFDFB]">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#F8DDC9] text-[#9B3B25] font-editorial font-bold text-lg mb-5 border border-[#ECC2A4]">
                4
              </div>
              <h3 className="font-editorial font-bold text-xl text-[#342523] mb-2">Specific Feedback</h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Receive granular rubric evaluations, concrete problem-framing scores, and prioritized next steps to improve.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why Interview Ready Section */}
      <section className="py-16 sm:py-24 bg-[#FFF8F0]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-widest text-[#9B3B25]">
              Core Pillars
            </span>
            <h2 className="font-editorial text-3xl sm:text-4xl font-bold text-[#342523] mt-2">
              Why engineers practise with Interview Ready.
            </h2>
            <p className="text-[#6E5652] text-sm sm:text-base mt-3">
              We focus on human mentorship, authentic company standards, and transparent logistics.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card-confidence p-8 bg-white">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4] mb-6">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="font-editorial font-bold text-2xl text-[#342523] mb-2.5">
                Vetted Leaders
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                All interviewers complete manual credential review, LinkedIn profile verification, and background audits before opening public slots.
              </p>
            </div>

            <div className="card-confidence p-8 bg-white">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4] mb-6">
                <Zap className="h-6 w-6" />
              </div>
              <h3 className="font-editorial font-bold text-2xl text-[#342523] mb-2.5">
                Guaranteed Slots
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Never worry about double bookings or calendar collisions. Database concurrency locks ensure you only pay for confirmed, available time.
              </p>
            </div>

            <div className="card-confidence p-8 bg-white">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FDF5EE] text-[#9B3B25] border border-[#ECC2A4] mb-6">
                <Award className="h-6 w-6" />
              </div>
              <h3 className="font-editorial font-bold text-2xl text-[#342523] mb-2.5">
                Actionable Rubrics
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Get more than a generic thumbs-up. Detailed assessments cover system architecture, trade-off analysis, code cleanliness, and clarity.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* For Interviewers Section */}
      <section className="py-16 sm:py-20 bg-[#9B3B25] text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#83321F] px-3.5 py-1 text-xs font-semibold text-[#F8DDC9] mb-3 border border-[#ECC2A4]/30">
              <Briefcase className="h-3.5 w-3.5" /> For Experienced Staff & Principal Engineers
            </span>
            <h2 className="font-editorial text-3xl sm:text-4xl font-bold leading-tight">
              Are you an experienced technical interviewer?
            </h2>
            <p className="mt-3 text-[#F8DDC9] text-sm sm:text-base leading-relaxed font-sans">
              Monetize your mentorship on your terms. Set your hourly rate, publish your calendar, and guide ambitious engineers through realistic mock evaluations.
            </p>
          </div>
          <Link
            href="/auth/interviewer"
            className="shrink-0 btn-pill-secondary bg-white text-[#9B3B25] border-transparent hover:bg-[#FDF5EE] px-8 py-3.5 text-base font-bold shadow-lg"
          >
            Apply as an Interviewer →
          </Link>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 sm:py-24 bg-[#FFF8F0]">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <span className="text-xs font-bold uppercase tracking-widest text-[#9B3B25]">
              Common Questions
            </span>
            <h2 className="font-editorial text-3xl sm:text-4xl font-bold text-[#342523] mt-2">
              Everything you need to know.
            </h2>
          </div>

          <div className="space-y-4">
            <div className="card-confidence p-6 bg-white">
              <h3 className="font-editorial font-bold text-lg text-[#342523] mb-2 flex items-center gap-2">
                <Laptop className="h-4 w-4 text-[#9B3B25]" />
                Why does the live interview require a desktop application?
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                The desktop client provides high-fidelity low-latency audio/video, a native code editor scratchpad, and hardware isolation that prevents browser tab slowdowns during intense practice sessions.
              </p>
            </div>

            <div className="card-confidence p-6 bg-white">
              <h3 className="font-editorial font-bold text-lg text-[#342523] mb-2 flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#9B3B25]" />
                When does the interview room open?
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                The join room button opens 10 minutes prior to your scheduled session so you can test your camera and microphone. It remains active with a 30-minute grace window.
              </p>
            </div>

            <div className="card-confidence p-6 bg-white">
              <h3 className="font-editorial font-bold text-lg text-[#342523] mb-2 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#9B3B25]" />
                Who can see the interviewer’s private notes?
              </h3>
              <p className="text-sm text-[#6E5652] leading-relaxed font-sans">
                Only the interviewer has access to their raw scratchpad notes during the session. After the interview, candidates receive the finalized structured rubric breakdown and actionable feedback summary.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
