import { Award, ChevronRight, ShieldCheck, Video, Zap } from "lucide-react";
import Link from "next/link";
import React from "react";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50/50 via-white to-gray-50 py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50/80 px-4 py-1.5 text-xs font-semibold text-blue-700">
            <Video className="h-4 w-4" />
            <span>Interview Ready Marketplace</span>
          </div>

          <h1 className="mx-auto max-w-4xl font-extrabold text-4xl sm:text-6xl text-gray-900 tracking-tight leading-tight">
            Practice real technical mock interviews with vetted tech leaders.
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600 leading-relaxed">
            Boost your interview performance. Book 1-on-1 system design, coding, and behavioral mock interviews with principal engineers and hiring managers.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/marketplace"
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition"
            >
              Explore Interviewers
              <ChevronRight className="h-5 w-5" />
            </Link>
            <Link
              href="/auth/sign-up"
              className="rounded-xl border border-gray-300 bg-white px-8 py-3.5 text-base font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-white border-t border-gray-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">Why Interview Ready?</h2>
            <p className="text-gray-600 mt-2">Real-world interview simulations built for engineers.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="rounded-2xl border border-gray-200 bg-gray-50/50 p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 mb-6">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-xl text-gray-900 mb-2">Vetted Industry Experts</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                All interviewers are rigorously verified with documented years of experience at top technology companies.
              </p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-gray-50/50 p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 mb-6">
                <Zap className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-xl text-gray-900 mb-2">Instant Slot Reservations</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Lock in your session with transaction-safe 10-minute temporary slot holds and transparent real-money pricing.
              </p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-gray-50/50 p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 mb-6">
                <Award className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-xl text-gray-900 mb-2">Actionable Rubric & Feedback</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Receive structured evaluations, coding rubric breakdowns, and personalized improvement roadmaps after each call.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
