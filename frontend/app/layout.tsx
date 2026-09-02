import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "METFI — Autonomous Finance Operations Console",
  description:
    "Deterministic financial reconciliation, verifier-gated AI investigation, policy authorization, and tamper-evident audit ledger.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#030712] text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
