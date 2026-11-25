import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sovela AI — Universal AI Life Operating System",
  description: "Define goals, create actionable plans, track progress, and learn with an AI Socratic mentor.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-sovela-navy text-sovela-text-primary antialiased selection:bg-sovela-teal selection:text-white">
        {children}
      </body>
    </html>
  );
}
