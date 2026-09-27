import type { Metadata } from "next";
import type { ReactNode } from "react";
import { connection } from "next/server";
import { SITE_DESCRIPTION } from "../components/site-copy";
import "./globals.css";

export const metadata: Metadata = {
  title: "Augmentr — Linear system solver",
  description: SITE_DESCRIPTION,
  openGraph: { title: "Augmentr", description: SITE_DESCRIPTION },
};

export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  // A cached static document cannot share a per-request script nonce.
  await connection();
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">Skip to content</a>
        {children}
      </body>
    </html>
  );
}
