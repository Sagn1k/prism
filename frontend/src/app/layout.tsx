import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Navbar from "@/components/Navbar";
import AuthProvider from "@/components/AuthProvider";

const inter = localFont({
  src: "../fonts/InterVariable.woff2",
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Prism — Discover Your Spectrum",
  description:
    "A gamified identity-discovery platform for students. Explore missions, uncover your strengths, and share your unique Prism Card.",
  openGraph: {
    title: "Prism — Discover Your Spectrum",
    description:
      "A gamified identity-discovery platform for students.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`min-h-screen ${inter.variable} font-sans`}>
        <AuthProvider>
          <Navbar />
          <main className="pt-16">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
