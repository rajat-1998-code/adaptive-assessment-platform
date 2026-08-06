"use client";

import Link from "next/link";
import type { ReactNode } from "react";

interface AuthShellProps {
  children: ReactNode;
  eyebrow: string;
  subtitle: string;
  title: string;
}

export default function AuthShell({ children, eyebrow, subtitle, title }: AuthShellProps) {
  return (
    <section className="flex flex-1 px-6 py-10 md:py-16">
      <div className="mx-auto grid w-full max-w-6xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[2rem] border border-white/10 bg-white/[0.02] p-8">
          <p className="mono-ui text-[0.72rem] uppercase tracking-[0.24em] text-slate-500">
            {eyebrow}
          </p>
          <h1 className="mt-4 text-4xl font-semibold leading-tight text-white md:text-5xl">
            {title}
          </h1>
          <p className="mt-5 max-w-xl text-base leading-8 text-slate-300">{subtitle}</p>

          <div className="mt-8 space-y-4 rounded-[1.5rem] border border-white/10 bg-black/30 p-6">
            <div>
              <p className="mono-ui text-[0.68rem] uppercase tracking-[0.22em] text-slate-500">
                Included
              </p>
              <ul className="mt-3 space-y-3 text-sm leading-7 text-slate-300">
                <li>Email and password authentication</li>
                <li>Magic-link sign in</li>
                <li>Google and GitHub OAuth entry points</li>
                <li>Cookie-based session continuity</li>
              </ul>
            </div>

            <div className="h-px bg-white/10" />

            <div className="flex flex-wrap gap-3 text-sm text-slate-400">
              <Link href="/" className="transition hover:text-white">
                Back Home
              </Link>
            </div>
          </div>
        </div>

        <div className="tech-frame rounded-[2rem] border border-white/10 bg-black/40 p-6 md:p-8">
          {children}
        </div>
      </div>
    </section>
  );
}
