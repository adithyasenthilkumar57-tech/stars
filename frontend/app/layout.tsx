import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClearWay AI — Quantum-Enhanced Urban Traffic Optimization",
  description: "AI-first intelligent traffic management platform combining quantum optimization, computer vision, siren detection, and real-time analytics for smart cities.",
  keywords: "traffic management, AI, quantum optimization, smart city, emergency corridor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
