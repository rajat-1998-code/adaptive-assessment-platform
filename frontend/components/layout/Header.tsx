import Logo from "@/components/common/Logo";
import Container from "@/components/ui/Container";
import RoleSwitcher from "@/components/layout/RoleSwitcher";

const NAV_ITEMS = [
  "Dashboard",
  "Features",
  "Assessment",
  "Docs",
  "About",
];

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
      <Container>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center py-4">
          {/* Logo */}
          <div className="justify-self-start">
            <Logo />
          </div>

          {/* Center Navigation */}
          <nav className="flex items-center gap-1 rounded-full bg-white/10 p-2 shadow-sm shadow-black/20 backdrop-blur-sm">
            {NAV_ITEMS.map((item) => (
              <a
                key={item}
                href="#"
                className="mono-ui rounded-full px-4 py-2.5 text-sm font-medium tracking-[0.08em] text-slate-100 transition-all duration-300 hover:bg-white/10 hover:text-[#ffb87a]"
              >
                {item}
              </a>
            ))}

            <a
              href="#signin"
              className="mono-ui rounded-full bg-[#ff8a2a] px-5 py-2.5 text-sm font-semibold tracking-[0.08em] text-black transition-all duration-300 hover:brightness-110"
            >
              Sign In
            </a>
          </nav>

          {/* Role Switcher */}
          <div className="justify-self-end">
            <RoleSwitcher />
          </div>
        </div>
      </Container>
    </header>
  );
}