import type { Metadata } from "next";
import { Barlow, Barlow_Condensed, Geist_Mono } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { Nav } from "@/components/nav";
import "./globals.css";

const barlow = Barlow({
  variable: "--font-barlow",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const barlowCondensed = Barlow_Condensed({
  variable: "--font-barlow-condensed",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LeGM - NBA Take Analyzer",
  description:
    "Drop your hottest NBA take. Get fact-checked with real stats and roasted by AI.",
  icons: {
    icon: "/favicon.ico",
    apple: "/logo-400.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${barlow.variable} ${barlowCondensed.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <div className="court-bg" aria-hidden="true" />
        <div className="ambient-glow" aria-hidden="true" />
        <div className="ambient-glow-2" aria-hidden="true" />
        <Nav />
        <main className="relative z-10">{children}</main>
        <Toaster />
      </body>
    </html>
  );
}
