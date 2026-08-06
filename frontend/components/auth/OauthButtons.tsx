"use client";

import { authService } from "@/services/auth/auth.service";

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" aria-hidden="true">
      <path
        d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.3h6.47a5.53 5.53 0 0 1-2.4 3.63v3.02h3.88c2.27-2.09 3.54-5.17 3.54-8.68Z"
        fill="#4285F4"
      />
      <path
        d="M12 24c3.24 0 5.95-1.08 7.93-2.92l-3.87-3.02c-1.07.72-2.45 1.15-4.06 1.15-3.13 0-5.78-2.11-6.73-4.96H1.27v3.11A11.99 11.99 0 0 0 12 24Z"
        fill="#34A853"
      />
      <path
        d="M5.27 14.25a7.2 7.2 0 0 1 0-4.5V6.64H1.27a12 12 0 0 0 0 10.72l4-3.11Z"
        fill="#FBBC05"
      />
      <path
        d="M12 4.75c1.76 0 3.35.61 4.6 1.8l3.44-3.44C17.94 1.19 15.24 0 12 0 7.31 0 3.26 2.69 1.27 6.64l4 3.11C6.22 6.86 8.87 4.75 12 4.75Z"
        fill="#EA4335"
      />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 0C5.37 0 0 5.5 0 12.29c0 5.43 3.44 10.03 8.21 11.66.6.11.82-.27.82-.6 0-.29-.01-1.26-.02-2.29-3.34.75-4.04-1.45-4.04-1.45-.55-1.43-1.34-1.81-1.34-1.81-1.09-.77.08-.76.08-.76 1.21.09 1.85 1.27 1.85 1.27 1.07 1.87 2.81 1.33 3.5 1.02.11-.79.42-1.33.76-1.64-2.67-.31-5.47-1.37-5.47-6.1 0-1.35.47-2.45 1.24-3.31-.12-.31-.54-1.57.12-3.28 0 0 1.01-.33 3.3 1.26a11.2 11.2 0 0 1 6.01 0c2.29-1.59 3.3-1.26 3.3-1.26.66 1.71.24 2.97.12 3.28.77.86 1.24 1.96 1.24 3.31 0 4.74-2.81 5.79-5.49 6.09.43.38.81 1.14.81 2.3 0 1.66-.02 2.99-.02 3.4 0 .33.22.72.83.6C20.57 22.31 24 17.71 24 12.29 24 5.5 18.63 0 12 0Z"
      />
    </svg>
  );
}

const PROVIDERS = [
  {
    href: () => authService.getGoogleOauthUrl(),
    label: "Continue with Google",
    icon: GoogleIcon,
  },
  {
    href: () => authService.getGithubOauthUrl(),
    label: "Continue with GitHub",
    icon: GithubIcon,
  },
] as const;

export default function OauthButtons() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {PROVIDERS.map((provider) => {
        const Icon = provider.icon;
        return (
          <a
            key={provider.label}
            href={provider.href()}
            className="flex items-center justify-center gap-1.5 whitespace-nowrap rounded-xl border border-white/10 bg-white/[0.03] px-2 py-3 text-xs font-medium text-slate-200 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-white sm:text-sm"
          >
            <Icon />
            <span>{provider.label}</span>
          </a>
        );
      })}
    </div>
  );
}
