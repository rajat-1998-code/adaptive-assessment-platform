import type { Metadata } from "next";
import "./globals.css";

import { AppLayout } from "@/components/layout";
import { APP_DESCRIPTION, APP_NAME } from "@/constants/app";
import AppProviders from "@/providers/AppProviders";

export const metadata: Metadata = {
  title: APP_NAME,
  description: APP_DESCRIPTION,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppProviders>
          <AppLayout>{children}</AppLayout>
        </AppProviders>
      </body>
    </html>
  );
}
