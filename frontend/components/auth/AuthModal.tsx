"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import LoginPanel from "@/components/auth/LoginPanel";
import RegisterPanel from "@/components/auth/RegisterPanel";
import VerifyEmailPanel from "@/components/auth/VerifyEmailPanel";

interface AuthModalProps {
  open: boolean;
  onClose: () => void;
  initialMode?: "login" | "register" | "verify";
}

export default function AuthModal({ open, onClose, initialMode = "login" }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register" | "verify">(initialMode);

  function handleClose() {
    setMode("login");
    onClose();
  }
  // Rendered via portal so the modal escapes any ancestor (e.g. the sticky,
  // backdrop-blurred header) that would otherwise become a containing block
  // for this fixed-position dialog and clip it to that ancestor's box.
  // `open` only ever flips to true from a click handler (after hydration),
  // so `document` is always available by the time we reach createPortal below.

  // Close on Escape, lock background scroll while open.
  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMode("login");
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto px-4 py-6 sm:py-8"
      role="dialog"
      aria-modal="true"
      aria-label={mode === "login" ? "Sign in" : mode === "register" ? "Register" : "Verify email"}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal panel */}
      <div className="relative z-10 my-auto w-full max-w-md rounded-3xl border border-white/10 bg-[#0d0d0d] p-5 shadow-2xl shadow-black/60 sm:p-6">
        <button
          type="button"
          onClick={handleClose}
          aria-label="Close authentication dialog"
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

        {mode === "login" ? (
          <LoginPanel
            onSuccess={handleClose}
            onRegisterClick={() => setMode("register")}
            onNeedsVerification={() => setMode("verify")}
          />
        ) : mode === "register" ? (
          <RegisterPanel
            onBackToLogin={() => setMode("login")}
            onRegistered={() => setMode("verify")}
          />
        ) : (
          <VerifyEmailPanel onSuccess={handleClose} />
        )}
      </div>
    </div>,
    document.body,
  );
}
