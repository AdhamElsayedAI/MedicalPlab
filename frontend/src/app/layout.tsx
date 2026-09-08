import type { Metadata } from "next";
import React from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedicalPlab — AI-Powered Clinical Learning Platform",
  description:
    "Master clinical reasoning with evidence-grounded AI. MedicalPlab combines 3D anatomy intelligence, AI medical tutoring, and emergency simulation into one premium clinical learning platform. Built for UK PLAB & GMC exams.",
  keywords: "medical education, PLAB exam, clinical AI, 3D anatomy, medical simulation, NICE guidelines, evidence-based medicine",
  openGraph: {
    title: "MedicalPlab — AI-Powered Clinical Learning Platform",
    description: "Evidence-grounded AI medical education combining 3D anatomy, Socratic tutoring, and emergency simulation.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col text-slate-100 font-sans" style={{ background: '#0b1120' }}>
        {children}
      </body>
    </html>
  );
}
