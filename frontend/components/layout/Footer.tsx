import Container from "@/components/ui/Container";
import { APP_NAME } from "@/constants/app";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/45 backdrop-blur-sm">
      <Container>
        <div className="mono-ui flex flex-col items-center justify-between gap-3 py-4 text-center text-[0.68rem] uppercase tracking-[0.18em] text-slate-500 md:flex-row md:gap-4">
          <span>{"(c) 2026 "}{APP_NAME}</span>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <a className="transition hover:text-white" href="https://github.com/rajat-1998-code/adaptive-assessment-platform/">GitHub</a>
            <a className="transition hover:text-white" href="#docs">Docs</a>
            <a className="transition hover:text-white" href="#contact">Contact</a>
          </div>
        </div>
      </Container>
    </footer>
  );
}
