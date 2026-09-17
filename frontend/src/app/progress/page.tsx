"use client";

import React, { Suspense } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { UnifiedProgressView } from "@/components/progress/UnifiedProgressView";
import { Loader2 } from "lucide-react";

export default function ProgressPage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="min-h-[60vh] flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-teal-400" />
            <p className="text-sm">Loading Learning Journey Progress...</p>
          </div>
        }
      >
        <UnifiedProgressView />
      </Suspense>
    </AppShell>
  );
}
