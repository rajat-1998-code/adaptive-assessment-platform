"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/providers/AuthProvider";

/** Right-side account area: session status, verify link, sign out. Renders nothing while signed out — the Sign In trigger lives inline in the nav (see SignInNavItem). */
export default function AuthStatus() {
  const router = useRouter();
  const { isAuthenticated, isLoading, logout, user } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    setIsLoggingOut(true);

    try {
      await logout();
      router.push("/");
      router.refresh();
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mono-ui rounded-lg border border-white/10 px-3 py-1.5 text-xs uppercase tracking-[0.18em] text-slate-500">
        Checking session
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex items-center gap-3">
      <div className="hidden text-right md:block">
        <p className="text-sm font-medium text-white">{user.email}</p>
      </div>

      <button
        type="button"
        onClick={() => void handleLogout()}
        disabled={isLoggingOut}
        className="mono-ui rounded-lg border border-white/10 px-3 py-1.5 text-xs uppercase tracking-[0.16em] text-slate-300 transition hover:border-white/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoggingOut ? "Signing out" : "Sign Out"}
      </button>
    </div>
  );
}
