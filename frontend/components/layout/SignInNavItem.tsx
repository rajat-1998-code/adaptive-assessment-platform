"use client";

import { useState } from "react";

import AuthModal from "@/components/auth/AuthModal";
import { useAuth } from "@/providers/AuthProvider";

/** Sign In trigger rendered inline in the nav row, right after the last nav link. Hidden once signed in or while the session check is in flight. */
export default function SignInNavItem() {
  const { isAuthenticated, isLoading } = useAuth();
  const [isSignInOpen, setIsSignInOpen] = useState(false);

  if (isLoading) {
    return null;
  }

  return (
    <>
      {!isAuthenticated ? (
        <button
          type="button"
          onClick={() => setIsSignInOpen(true)}
          className="mono-ui whitespace-nowrap rounded-lg bg-[#ff8a2a] px-3.5 py-2 text-sm font-medium tracking-[0.08em] text-black transition hover:brightness-110"
        >
          Sign In
        </button>
      ) : null}

      <AuthModal open={isSignInOpen} onClose={() => setIsSignInOpen(false)} />
    </>
  );
}
