import { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-950">
      <Header />

      <main className="flex flex-1">
        {children}
      </main>

      <Footer />
    </div>
  );
}
