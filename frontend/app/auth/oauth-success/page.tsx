import AuthShell from "@/components/auth/AuthShell";
import OauthSuccess from "@/components/auth/OauthSuccess";

export default function OauthSuccessPage() {
  return (
    <AuthShell
      eyebrow="Social Authentication"
      subtitle="Your social provider has redirected back to the frontend. We are now restoring the cookie-based application session issued by the backend callback."
      title="Completing social sign in"
    >
      <OauthSuccess />
    </AuthShell>
  );
}
