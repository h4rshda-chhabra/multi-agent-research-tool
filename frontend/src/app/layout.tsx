import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { NEXTAUTH_URL } from "@/lib/config";

export const metadata: Metadata = {
  title: "AI Research Assistant",
  description: "Generate citation-backed research reports from trusted sources in minutes.",
  metadataBase: new URL(NEXTAUTH_URL),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
