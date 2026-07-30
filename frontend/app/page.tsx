"use client";

import { useRole } from "@/providers/RoleProvider";

export default function HomePage() {
  const { role } = useRole();

  const content =
    role === "students"
      ? {
          audience: "Students",
          description:
            "Build knowledge, develop understanding, and practice confidently with AI-powered document learning, adaptive quizzes, knowledge gap analysis, and personalized exam preparation.",
        }
      : {
          audience: "Professionals",
          description:
            "Build expertise, develop career-ready skills, and practice confidently with AI-powered document learning, interview preparation, resume analysis, and personalized knowledge refresh.",
        };

  return (
    <section className="relative flex flex-1 px-6 py-10 md:py-16">
      {/* Background Glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(255,138,42,0.08),transparent_45%)]" />

      <div className="relative z-10 mx-auto flex w-full max-w-4xl flex-col items-center text-center">
        <p className="mono-ui text-[0.8rem] uppercase tracking-[0.30em] text-slate-500">
          Adaptive Assessment Platform
        </p>

        <h1 className="mt-10 text-5xl font-bold leading-[1.02] text-white md:text-7xl">
          <span className="text-[#ff8a2a]">Open Source</span>{" "}
          <span>AI</span>

          <span className="mt-8 block text-3xl font-semibold text-slate-500 md:text-6xl">
            Assessment for{" "}
            <span className="text-white">{content.audience}</span>
          </span>
        </h1>

        <p className="mt-12 max-w-2xl text-lg leading-8 text-slate-300">
          {content.description}
        </p>

        <div className="mt-14 flex flex-col gap-4 sm:flex-row">
          <button className="rounded-full bg-[#ff8a2a] px-7 py-3 font-medium text-black transition hover:brightness-110">
            Get Started
          </button>
        </div>
      </div>
    </section>
  );
}