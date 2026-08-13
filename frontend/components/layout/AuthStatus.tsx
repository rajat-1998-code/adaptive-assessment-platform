"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createPortal } from "react-dom";

import AuthModal from "@/components/auth/AuthModal";
import { useAuth } from "@/providers/AuthProvider";

function getInitials(firstName: string | null, lastName: string | null, email: string) {
  if (firstName || lastName) {
    return `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`.toUpperCase() || "U";
  }

  const localPart = email.split("@", 1)[0] ?? email;
  const parts = localPart
    .replace(/[^a-zA-Z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length === 0) {
    return "U";
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/** Right-side account area: compact avatar trigger plus profile popup. */
export default function AuthStatus() {
  const router = useRouter();
  const { isAuthenticated, isLoading, logout, user } = useAuth();
  const [isSignInOpen, setIsSignInOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const initials = useMemo(() => {
    if (!user) {
      return "U";
    }

    return getInitials(user.first_name, user.last_name, user.email);
  }, [user]);

  const fullName = user
    ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email
    : "";

  async function handleLogout() {
    setIsLoggingOut(true);

    try {
      await logout();
      setIsProfileOpen(false);
      router.push("/");
      router.refresh();
    } finally {
      setIsLoggingOut(false);
    }
  }

  useEffect(() => {
    if (!isProfileOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsProfileOpen(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [isProfileOpen]);

  if (isLoading) {
    return (
      <div className="mono-ui rounded-lg border border-white/10 px-3 py-1.5 text-xs uppercase tracking-[0.18em] text-slate-500">
        Checking session
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <>
        <button
          type="button"
          onClick={() => setIsSignInOpen(true)}
          className="mono-ui whitespace-nowrap rounded-lg bg-[#ff8a2a] px-3.5 py-2 text-sm font-medium tracking-[0.08em] text-black transition hover:brightness-110"
        >
          Sign In
        </button>

        <AuthModal open={isSignInOpen} onClose={() => setIsSignInOpen(false)} />
      </>
    );
  }

  return (
    <div className="relative">
      <div className="group relative">
        <button
          type="button"
          onClick={() => setIsProfileOpen((prev) => !prev)}
          aria-label="Open user profile"
          className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-[#161616] text-sm font-semibold text-white shadow-sm shadow-black/30 transition hover:border-[#ff8a2a] hover:bg-[#1d1d1d] focus:outline-none focus:ring-2 focus:ring-[#ff8a2a]/50"
        >
          {initials}
        </button>

        <div className="pointer-events-none absolute right-0 top-full z-50 mt-2 w-44 translate-y-1 opacity-0 transition duration-150 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100">
          <div className="rounded-2xl border border-white/10 bg-[#121212] px-4 py-3 text-left shadow-2xl shadow-black/40">
            <p className="mono-ui text-[0.65rem] uppercase tracking-[0.22em] text-slate-500">
              User Menu
            </p>
            <p className="mt-2 text-sm font-medium text-white">Open profile</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              View account details and sign out.
            </p>
          </div>
        </div>
      </div>

      {isProfileOpen
        ? createPortal(
            <div
              className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto px-4 py-6 sm:py-8"
              onClick={() => setIsProfileOpen(false)}
              role="dialog"
              aria-modal="true"
              aria-label="User profile"
            >
              <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

              <div
                className="relative z-10 my-auto w-full max-w-md rounded-3xl border border-white/10 bg-[#0d0d0d] p-5 shadow-2xl shadow-black/60 sm:p-6"
                onClick={(event) => event.stopPropagation()}
              >
                <button
                  type="button"
                  onClick={() => setIsProfileOpen(false)}
                  aria-label="Close profile"
                  className="absolute right-5 top-5 rounded-full border border-white/10 p-1.5 text-slate-400 transition hover:border-red-500/60 hover:bg-red-500/10 hover:text-red-500"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-3.5 w-3.5"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>

                <div className="flex flex-col items-center text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full border border-[#ff8a2a]/40 bg-[#ff8a2a]/10 text-2xl font-semibold text-[#ffb87a]">
                    {initials}
                  </div>

                  <p className="mono-ui mt-4 text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
                    Profile
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">Account details</h2>
                  <p className="mt-2 text-base font-medium text-[#ffb87a]">{fullName}</p>
                  <p className="mt-2 max-w-sm text-sm leading-6 text-slate-400">
                    Here is the signed-in profile currently active in this browser session.
                  </p>
                </div>

                <div className="mt-6 space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Full name</span>
                    <span className="max-w-[16rem] truncate text-sm font-medium text-white">
                      {fullName}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Email</span>
                    <span className="max-w-[16rem] truncate text-sm font-medium text-white">
                      {user.email}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Role</span>
                    <span className="text-sm font-medium capitalize text-white">{user.role}</span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Verified</span>
                    <span
                      className={`text-sm font-medium ${
                        user.is_email_verified ? "text-emerald-300" : "text-amber-300"
                      }`}
                    >
                      {user.is_email_verified ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Active</span>
                    <span className="text-sm font-medium text-white">
                      {user.is_active ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm text-slate-400">Joined</span>
                    <span className="text-sm font-medium text-white">{formatDate(user.created_at)}</span>
                  </div>
                </div>

                <div className="mt-6 flex justify-center">
                  <button
                    type="button"
                    onClick={() => void handleLogout()}
                    disabled={isLoggingOut}
                    className="mono-ui rounded-full bg-[#ff8a2a] px-8 py-3 text-sm font-medium tracking-[0.08em] text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoggingOut ? "Signing out..." : "Sign Out"}
                  </button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
