import { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-transparent">
      <Header />

      <main id="main-content" className="flex flex-1">
        {children}
      </main>

      <Footer />
    </div>
  );
}
