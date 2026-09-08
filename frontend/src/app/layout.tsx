import type { Metadata } from "next";
import React from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedicalPlab // Digital Anatomy Lab & Clinical Intelligence OS",
  description:
    "Startup-grade evidence-grounded medical AI learning platform for UK PLAB & GMC exams. Features 3D interactive anatomy, Socratic AI mentor, and emergency ward simulation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#050811] text-slate-100 font-sans">
        {children}
      </body>
    </html>
  );
}
