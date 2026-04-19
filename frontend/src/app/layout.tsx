import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Job Match CV",
  description: "Paste a LinkedIn profile, get matching jobs, and generate a tailored CV guide.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
