"use client";

import type { ReactNode } from "react";
import { RoleProvider } from "@/providers/RoleProvider";

interface AppProvidersProps {
  children: ReactNode;
}

export default function AppProviders({ children }: AppProvidersProps) {
  return <RoleProvider>{children}</RoleProvider>;
}
