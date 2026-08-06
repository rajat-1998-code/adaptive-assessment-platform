"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { useAuth } from "@/providers/AuthProvider";

interface VerifyEmailPanelProps {
  onSuccess?: () => void;
}

export default function VerifyEmailPanel({ onSuccess }: VerifyEmailPanelProps = {}) {
  const router = useRouter();
  const { clearError, error, isAuthenticated, resendOtp, user, verifyEmail } = useAuth();
  const [code, setCode] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isResending, startResendTransition] = useTransition();

  const helperText = useMemo(() => {
    if (!isAuthenticated || !user) {
      return "Sign in or register first, then come back here to verify your email.";
    }

    if (user.is_email_verified) {
      return "Your email is already verified. You can return to the platform.";
    }

    return `Enter the verification code sent to ${user.email}.`;
  }, [isAuthenticated, user]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setMessage(null);

    startTransition(async () => {
      try {
        await verifyEmail({ code });
        if (onSuccess) {
          onSuccess();
        } else {
          router.push("/");
          router.refresh();
        }
      } catch {}
    });
  }

  function handleResend() {
    clearError();
    setMessage(null);

    startResendTransition(async () => {
      try {
        const responseMessage = await resendOtp();
        setMessage(responseMessage);
      } catch {}
    });
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="mono-ui text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
          Verify Email
        </p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Confirm your email address</h2>
        <p className="mt-4 text-sm leading-7 text-slate-300">{helperText}</p>
      </div>

      {!isAuthenticated || !user ? (
        <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.02] p-6 text-sm text-slate-300">
          <p>You need an active session to verify email.</p>
          <div className="mt-4 flex gap-3">
            <Link
              href="/"
              className="rounded-full border border-white/10 px-4 py-2 text-white transition hover:border-white/20"
            >
              Sign In
            </Link>
            <Link
              href="/auth/register"
              className="rounded-full bg-[#ff8a2a] px-4 py-2 font-medium text-black transition hover:brightness-110"
            >
              Register
            </Link>
          </div>
        </div>
      ) : user.is_email_verified ? (
        <div className="rounded-[1.5rem] border border-emerald-500/20 bg-emerald-500/10 p-6 text-sm text-emerald-100">
          Your account is already verified.
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-2 block text-sm text-slate-300" htmlFor="verification-code">
              Verification Code
            </label>
            <input
              id="verification-code"
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className="mono-ui w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-white outline-none transition focus:border-[#ff8a2a]"
              placeholder="Enter the 6-digit code"
              required
            />
          </div>

          {message ? (
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {message}
            </div>
          ) : null}

          {error ? (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="submit"
              disabled={isPending}
              className="rounded-full bg-[#ff8a2a] px-6 py-3 text-sm font-semibold text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isPending ? "Verifying..." : "Verify Email"}
            </button>
            <button
              type="button"
              disabled={isResending}
              onClick={() => handleResend()}
              className="mono-ui rounded-full border border-white/10 px-6 py-3 text-xs uppercase tracking-[0.18em] text-slate-200 transition hover:border-white/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isResending ? "Sending..." : "Resend Code"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
