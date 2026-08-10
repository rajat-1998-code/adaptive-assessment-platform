import Link from "next/link";

import Logo from "@/components/common/Logo";
import AuthStatus from "@/components/layout/AuthStatus";
import Container from "@/components/ui/Container";
import RoleSwitcher from "@/components/layout/RoleSwitcher";

const NAV_ITEMS = [
  { label: "Home", href: "/" },
  { label: "Dashboard", href: "#" },
  { label: "Features", href: "#" },
  { label: "Assessment", href: "#" },
  { label: "Docs", href: "#" },
  { label: "About", href: "#" },
];

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
      <Container>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center py-1.5">
          {/* Logo */}
          <div className="justify-self-start">
            <Logo />
          </div>

          {/* Center Navigation */}
          <nav className="flex items-center gap-1 rounded-xl bg-white/10 p-1.5 shadow-sm shadow-black/20 backdrop-blur-sm">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="mono-ui whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-medium tracking-[0.08em] text-slate-100 transition-all duration-300 hover:bg-white/10 hover:text-[#ffb87a]"
              >
                {item.label}
              </Link>
            ))}

            <AuthStatus />
          </nav>

          <div className="flex items-center justify-self-end gap-3">
            <RoleSwitcher />
          </div>
        </div>
      </Container>
    </header>
  );
}
