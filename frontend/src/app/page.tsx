"use client";

import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { LearningHub } from "@/components/home/LearningHub";

export default function Home() {
  return (
    <AppShell>
      <LearningHub />
    </AppShell>
  );
}
