import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NéoMêtis",
  description: "The Lean, Single-Tenant AI Workbench powered by Hermes Agent & Advanced RAG.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
