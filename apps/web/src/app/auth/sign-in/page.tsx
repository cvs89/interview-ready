"use client";

import { AlertCircle, ArrowRight, Loader2, LogIn } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import React, { Suspense, useState } from "react";

import { useAuth } from "../../../context/AuthContext";

function SignInContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const { signInWithEmail, signInWithGoogle, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) {
    router.push(redirect);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signInWithEmail(email, password);
      router.push(redirect);
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setError(eObj.message || "Failed to sign in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setLoading(true);
    try {
      await signInWithGoogle();
      router.push(redirect);
    } catch (err: unknown) {
      const eObj = err as { message?: string };
      setError(eObj.message || "Google sign-in failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-[#FFF8F0]">
      <div className="w-full max-w-md space-y-8 rounded-[24px] border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-sm">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8DDC9] text-[#9B3B25] mb-4">
            <LogIn className="h-6 w-6" />
          </div>
          <h2 className="font-serif text-3xl font-normal tracking-tight text-[#342523]">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-[#6E5652]">
            Or{" "}
            <Link href="/auth/sign-up" className="font-medium text-[#9B3B25] hover:text-[#83321F] underline-offset-4 hover:underline">
              create a new account
            </Link>
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-2xl border border-red-200 bg-[#FCEBEB] p-3.5 text-sm text-[#9E2A2B]" role="alert">
            <AlertCircle className="h-4 w-4 shrink-0 text-[#9E2A2B]" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-semibold uppercase tracking-wider text-[#6E5652] mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-[#EADBCE] bg-[#FFFDFB] px-3.5 py-2.5 text-sm text-[#342523] placeholder-[#96817D] focus:border-[#9B3B25] focus:outline-none focus:ring-1 focus:ring-[#9B3B25]"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-[#9B3B25] px-6 py-3 text-sm font-medium text-white shadow hover:bg-[#83321F] active:bg-[#6D2919] transition disabled:opacity-50 mt-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Sign In <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#EADBCE]" />
          </div>
          <div className="relative flex justify-center text-xs uppercase tracking-wider">
            <span className="bg-white px-3 text-[#96817D] font-medium">Or continue with</span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="flex w-full items-center justify-center gap-3 rounded-full border border-[#EADBCE] bg-white px-4 py-2.5 text-sm font-medium text-[#342523] shadow-sm hover:bg-[#FDF5EE] transition disabled:opacity-50"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              fill="#EA4335"
            />
          </svg>
          Google
        </button>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-[#FFF8F0]">
          <Loader2 className="h-8 w-8 animate-spin text-[#9B3B25]" />
        </div>
      }
    >
      <SignInContent />
    </Suspense>
  );
}

