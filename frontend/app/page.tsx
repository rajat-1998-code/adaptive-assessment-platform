import Page from "@/components/common/Page";
import { APP_NAME, APP_VERSION } from "@/constants/app";
import { getBackendHealthStatus } from "@/services/health/health.service";

export default async function HomePage() {
  const health = await getBackendHealthStatus();

  return (
    <Page>
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white md:text-5xl">{APP_NAME}</h1>

        <p className="mt-5 text-base text-slate-300 md:text-lg">
          Backend Status
        </p>

        <p className="mt-2 text-sm text-slate-400 md:text-base">
          {health.connected ? "Connected" : "Backend Offline"} | Status {health.statusLabel}
        </p>

        <p className="mt-2 text-sm text-slate-500 md:text-base">
          Version {health.version ?? APP_VERSION} | Next.js 16 | React 19 | TypeScript |
          Tailwind CSS
        </p>
      </div>
    </Page>
  );
}
