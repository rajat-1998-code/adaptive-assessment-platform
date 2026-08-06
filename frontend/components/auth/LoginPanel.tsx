"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import OauthButtons from "@/components/auth/OauthButtons";
import { useAuth } from "@/providers/AuthProvider";

interface LoginPanelProps {
  /** Called after a successful password login or magic-link request (e.g. to close a modal). */
  onSuccess?: () => void;
  /** Hides the "New here? Create an account" footer link (used when a Register CTA is rendered by a parent, e.g. a modal). */
  hideRegisterLink?: boolean;
  /** Switches the current auth surface to the inline registration form. */
  onRegisterClick?: () => void;
  /** Switches the current auth surface to email verification for unverified users. */
  onNeedsVerification?: () => void;
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 6-10 7L2 6" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a19.5 19.5 0 0 1 5.06-5.94M9.9 4.24A10.6 10.6 0 0 1 12 4c7 0 11 8 11 8a19.6 19.6 0 0 1-2.36 3.44M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <path d="M1 1l22 22" />
    </svg>
  );
}

export default function LoginPanel({ onSuccess, hideRegisterLink, onRegisterClick, onNeedsVerification }: LoginPanelProps = {}) {
  const router = useRouter();
  const { clearError, error, login, requestMagicLink } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [magicLinkEmail, setMagicLinkEmail] = useState("");
  const [magicLinkMessage, setMagicLinkMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isMagicPending, startMagicTransition] = useTransition();

  function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setMagicLinkMessage(null);

    startTransition(async () => {
      try {
        const user = await login({ email, password });
        if (!user.is_email_verified && onNeedsVerification) {
          onNeedsVerification();
          return;
        }

        onSuccess?.();
        router.push(user.is_email_verified ? "/" : "/auth/verify-email");
        router.refresh();
      } catch {}
    });
  }

  function handleMagicLink() {
    clearError();

    startMagicTransition(async () => {
      try {
        const message = await requestMagicLink({ email: magicLinkEmail });
        setMagicLinkMessage(message);
      } catch {}
    });
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="mono-ui text-xl font-bold uppercase tracking-[0.1em] text-white">Sign In</h2>
        <p className="mt-2 text-sm text-slate-400">Welcome back! Please sign in to your account.</p>
      </div>

      <OauthButtons />

      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-white/10" />
        <span className="text-xs uppercase tracking-[0.18em] text-slate-500">Or</span>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <form className="space-y-4" onSubmit={handleLogin}>
        <div>
          <label className="mb-2 block text-sm text-slate-300" htmlFor="login-email">
            Email address
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center">
              <MailIcon />
            </span>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email"
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] py-3 pl-11 pr-4 text-white placeholder:text-slate-500 outline-none transition focus:border-[#ff8a2a]"
              required
            />
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm text-slate-300" htmlFor="login-password">
            Password
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center">
              <LockIcon />
            </span>
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] py-3 pl-11 pr-11 text-white placeholder:text-slate-500 outline-none transition focus:border-[#ff8a2a]"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-4 flex items-center text-slate-500 transition hover:text-slate-300"
            >
              <EyeIcon open={showPassword} />
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => setShowForgot((value) => !value)}
            className="text-sm text-[#ffb87a] transition hover:text-[#ff8a2a]"
          >
            Forgot password?
          </button>
        </div>

        {showForgot ? (
          <div className="space-y-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <p className="text-sm text-slate-400">
              We don&apos;t use password resets — enter your email and we&apos;ll send a one-time sign-in link instead.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="email"
                value={magicLinkEmail}
                onChange={(event) => setMagicLinkEmail(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    handleMagicLink();
                  }
                }}
                placeholder="you@example.com"
                className="w-full flex-1 rounded-xl border border-white/10 bg-black/40 px-4 py-2.5 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-[#ff8a2a]"
                required
              />
              <button
                type="button"
                onClick={handleMagicLink}
                disabled={isMagicPending}
                className="mono-ui shrink-0 rounded-xl border border-white/10 px-4 py-2.5 text-xs uppercase tracking-[0.14em] text-slate-200 transition hover:border-white/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isMagicPending ? "Sending..." : "Send link"}
              </button>
            </div>
            {magicLinkMessage ? (
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5 text-sm text-emerald-200">
                {magicLinkMessage}
              </div>
            ) : null}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={isPending}
          className="w-full rounded-xl bg-[#ff8a2a] px-6 py-3 text-sm font-semibold text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isPending ? "Signing in..." : "Sign In"}
        </button>
      </form>

      {hideRegisterLink ? null : (
        <p className="text-center text-sm text-slate-400">
          Don&apos;t have an account?{" "}
          <button
            type="button"
            onClick={onRegisterClick ?? onSuccess}
            className="text-[#ffb87a] transition hover:text-[#ff8a2a]"
          >
            Sign up
          </button>
        </p>
      )}
    </div>
  );
}
