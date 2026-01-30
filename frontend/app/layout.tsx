import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/components/providers/AppProviders";

export const metadata: Metadata = {
  title: "NExus AI - Multi-Hazard Decision Dashboard",
  description: "Government-grade multi-hazard decision dashboard for flood and landslide risk management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased text-base">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
