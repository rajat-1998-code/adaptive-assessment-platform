import Container from "@/components/ui/Container";
import { APP_NAME } from "@/constants/app";

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950">
      <Container>
        <div className="flex h-14 items-center justify-center text-sm text-slate-400">
          {"(c) 2026 "}
          {APP_NAME}
        </div>
      </Container>
    </footer>
  );
}
