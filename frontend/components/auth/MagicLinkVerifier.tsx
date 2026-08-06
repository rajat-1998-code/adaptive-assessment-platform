"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/providers/AuthProvider";

export default function MagicLinkVerifier() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { error, setUser, verifyMagicLink } = useAuth();
  const missingToken = token === null;
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  useEffect(() => {
    if (missingToken || token === null) {
      return;
    }

    const magicToken = token;
    let active = true;

    async function run() {
      setStatus("loading");

      try {
        const user = await verifyMagicLink(magicToken);
        if (!active) {
          return;
        }
        setUser(user);
        setStatus("success");
        router.push("/");
        router.refresh();
      } catch {
        if (active) {
          setStatus("error");
        }
      }
    }

    void run();

    return () => {
      active = false;
    };
  }, [missingToken, router, setUser, token, verifyMagicLink]);

  return (
    <div className="space-y-6">
      <div>
        <p className="mono-ui text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
          Magic Link
        </p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Completing passwordless sign in</h2>
      </div>

      {status === "loading" || status === "idle" ? (
        <p className="text-sm leading-7 text-slate-300">
          We are verifying your one-time sign-in link and restoring your session.
        </p>
      ) : null}

      {missingToken || status === "error" ? (
        <div className="space-y-4">
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {missingToken
              ? "This sign-in link is missing its token."
              : (error ?? "This sign-in link could not be completed.")}
          </div>
          <div className="flex gap-3">
            <Link
              href="/"
              className="rounded-full bg-[#ff8a2a] px-5 py-2.5 text-sm font-semibold text-black transition hover:brightness-110"
            >
              Back to Sign In
            </Link>
            <Link
              href="/auth/register"
              className="rounded-full border border-white/10 px-5 py-2.5 text-sm text-white transition hover:border-white/20"
            >
              Register
            </Link>
          </div>
        </div>
      ) : null}

      {status === "success" ? (
        <p className="text-sm leading-7 text-emerald-200">
          Sign-in complete. Redirecting you to the platform.
        </p>
      ) : null}
    </div>
  );
}
