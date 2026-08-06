"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/providers/AuthProvider";

export default function OauthSuccess() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function hydrate() {
      try {
        const user = await refreshUser();
        if (!active) {
          return;
        }

        if (!user) {
          setError("We could not restore your OAuth session.");
          return;
        }

        router.push(user.is_email_verified ? "/" : "/auth/verify-email");
        router.refresh();
      } catch {
        if (active) {
          setError("We could not restore your OAuth session.");
        }
      }
    }

    void hydrate();

    return () => {
      active = false;
    };
  }, [refreshUser, router]);

  return (
    <div className="space-y-4">
      <div>
        <p className="mono-ui text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
          OAuth Success
        </p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Finishing social sign in</h2>
      </div>

      <p className="text-sm leading-7 text-slate-300">
        Your provider authentication succeeded. We are restoring your platform session now.
      </p>

      {error ? (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      ) : null}
    </div>
  );
}
