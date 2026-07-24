import Logo from "@/components/common/Logo";
import Container from "@/components/ui/Container";

export default function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-950">
      <Container>
        <div className="flex h-20 items-center justify-center">
          <Logo />
        </div>
      </Container>
    </header>
  );
}
