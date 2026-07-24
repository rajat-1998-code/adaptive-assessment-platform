import type { ReactNode } from "react";

interface PageProps {
  children: ReactNode;
}

export default function Page({ children }: PageProps) {
  return <main className="flex flex-1 items-center justify-center px-6">{children}</main>;
}
