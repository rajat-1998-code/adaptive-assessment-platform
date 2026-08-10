import { Suspense } from "react";

import AuthShell from "@/components/auth/AuthShell";
import MagicLinkVerifier from "@/components/auth/MagicLinkVerifier";

export default function MagicLinkPage() {
  return (
    <AuthShell
      eyebrow="Magic Link"
      subtitle="This page completes one-time passwordless sign-in after you click the secure email link sent by the backend."
      title="Restoring your passwordless session"
    >
      <Suspense
        fallback={
          <div className="space-y-4">
            <div>
              <p className="mono-ui text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
                Magic Link
              </p>
              <h2 className="mt-3 text-3xl font-semibold text-white">
                Completing passwordless sign in
              </h2>
            </div>
            <p className="text-sm leading-7 text-slate-300">
              We are verifying your one-time sign-in link and restoring your session.
            </p>
          </div>
        }
      >
        <MagicLinkVerifier />
      </Suspense>
    </AuthShell>
  );
}
