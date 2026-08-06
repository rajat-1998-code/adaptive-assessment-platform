import AuthShell from "@/components/auth/AuthShell";
import MagicLinkVerifier from "@/components/auth/MagicLinkVerifier";

export default function MagicLinkPage() {
  return (
    <AuthShell
      eyebrow="Magic Link"
      subtitle="This page completes one-time passwordless sign-in after you click the secure email link sent by the backend."
      title="Restoring your passwordless session"
    >
      <MagicLinkVerifier />
    </AuthShell>
  );
}
