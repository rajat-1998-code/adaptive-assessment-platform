"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import OauthButtons from "@/components/auth/OauthButtons";
import { useAuth } from "@/providers/AuthProvider";

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 6-10 7L2 6" />
    </svg>
  );
}

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a19.5 19.5 0 0 1 5.06-5.94M9.9 4.24A10.6 10.6 0 0 1 12 4c7 0 11 8 11 8a19.6 19.6 0 0 1-2.36 3.44M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <path d="M1 1l22 22" />
    </svg>
  );
}

interface RegisterPanelProps {
  onBackToLogin?: () => void;
  onRegistered?: () => void;
}

export default function RegisterPanel({ onBackToLogin, onRegistered }: RegisterPanelProps = {}) {
  const router = useRouter();
  const { clearError, error, register } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setLocalError(null);

    if (password !== confirmPassword) {
      setLocalError("Passwords do not match.");
      return;
    }

    startTransition(async () => {
      try {
        await register({ email, password });
        if (onRegistered) {
          onRegistered();
        } else {
          router.push("/auth/verify-email");
          router.refresh();
        }
      } catch {}
    });
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="mono-ui text-xl font-bold uppercase tracking-[0.1em] text-white">Register</h2>
        <p className="mt-2 text-sm text-slate-400">Create your account.</p>
      </div>

      <form className="space-y-3" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="sr-only" htmlFor="register-first-name">
              First name
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-5 flex items-center text-slate-400"><UserIcon /></span>
              <input id="register-first-name" type="text" placeholder="First name" value={firstName} onChange={(event) => setFirstName(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#161616] px-5 py-3 pl-12 text-white placeholder:text-slate-400 outline-none transition focus:border-[#ff8a2a]" required />
            </div>
          </div>
          <div>
            <label className="sr-only" htmlFor="register-last-name">
              Last name
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-5 flex items-center text-slate-400"><UserIcon /></span>
              <input id="register-last-name" type="text" placeholder="Last name" value={lastName} onChange={(event) => setLastName(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#161616] px-5 py-3 pl-12 text-white placeholder:text-slate-400 outline-none transition focus:border-[#ff8a2a]" required />
            </div>
          </div>
        </div>

        <div>
          <label className="sr-only" htmlFor="register-email">
            Email
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-5 flex items-center text-slate-400"><MailIcon /></span>
            <input id="register-email" type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#161616] px-5 py-3 pl-12 text-white placeholder:text-slate-400 outline-none transition focus:border-[#ff8a2a]" required />
          </div>
        </div>

        <div>
          <label className="sr-only" htmlFor="register-password">
            Password
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-[#667d9d]">
              <LockIcon />
            </span>
            <input
              id="register-password"
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-2xl border border-white/10 bg-[#161616] px-4 py-3 pl-14 pr-14 text-white placeholder:text-slate-400 outline-none transition focus:border-[#ff8a2a]"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-5 flex items-center text-slate-400 transition hover:text-white"
            >
              <EyeIcon open={showPassword} />
            </button>
          </div>
        </div>

        <div>
          <label className="sr-only" htmlFor="register-confirm-password">
            Confirm Password
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-[#667d9d]"><LockIcon /></span>
            <input id="register-confirm-password" type={showConfirmPassword ? "text" : "password"} placeholder="Confirm password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#161616] px-4 py-3 pl-14 pr-14 text-white placeholder:text-slate-400 outline-none transition focus:border-[#ff8a2a]" required />
            <button type="button" onClick={() => setShowConfirmPassword((value) => !value)} aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"} className="absolute inset-y-0 right-5 flex items-center text-slate-400 transition hover:text-white">
              <EyeIcon open={showConfirmPassword} />
            </button>
          </div>
        </div>

        {localError ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {localError}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={isPending}
          className="w-full rounded-full bg-[#ff8a2a] px-6 py-2.5 text-sm font-semibold text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isPending ? "Creating account..." : "Create Account"}
        </button>
      </form>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-white/5" />
          <span className="mono-ui text-[0.68rem] uppercase tracking-[0.18em] text-slate-500">
            Or register with
          </span>
          <div className="h-px flex-1 bg-white/5" />
        </div>
        <OauthButtons />
      </div>

      <p className="text-center text-sm text-slate-400">
        Already have an account?{" "}
        <button type="button" onClick={onBackToLogin} className="text-[#ffb87a] transition hover:text-[#ff8a2a]">
          Sign in
        </button>
      </p>
    </div>
  );
}
