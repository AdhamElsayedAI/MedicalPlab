"use client";

import React, { Suspense } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { GroundedTutorView } from "@/components/tutor/GroundedTutorView";
import { Loader2 } from "lucide-react";

export default function TutorPage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="min-h-[60vh] flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-sky-400" />
            <p className="text-sm">Connecting to Evidence-Grounded Tutor...</p>
          </div>
        }
      >
        <GroundedTutorView />
      </Suspense>
    </AppShell>
  );
}
