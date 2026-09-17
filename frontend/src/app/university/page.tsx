"use client";

import { AppShell } from "@/components/layout/AppShell";
import { UniversityLearning } from "@/components/UniversityLearning";

export default function UniversityPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <UniversityLearning />
      </div>
    </AppShell>
  );
}
