"use client";

import React, { useState, useEffect } from "react";
import { HeaderNav } from "./HeaderNav";
import { MobileNav } from "./MobileNav";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";

interface AppShellProps {
  children: React.ReactNode;
  activeLearnerId?: string;
  onLearnerIdChange?: (id: string) => void;
  noPadding?: boolean;
  fullHeight?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeLearnerId: propLearnerId,
  onLearnerIdChange,
  noPadding = false,
  fullHeight = false,
}) => {
  const [learnerId, setLearnerId] = useState<string>("");

  useEffect(() => {
    const id = propLearnerId || getAuthoritativeLearnerId();
    setLearnerId(id);
    api.setUser(id);
  }, [propLearnerId]);

  const handleLearnerIdChange = (newId: string) => {
    setLearnerId(newId);
    api.setUser(newId);
    if (onLearnerIdChange) onLearnerIdChange(newId);
  };

  return (
    <div className={`min-h-screen flex flex-col bg-[#090d16] text-slate-100 selection:bg-sky-500/30 selection:text-sky-200 ${fullHeight ? "h-screen overflow-hidden" : ""}`}>
      {/* Top Header Navigation */}
      <HeaderNav learnerId={learnerId} onLearnerIdChange={handleLearnerIdChange} />

      {/* Main Page Content */}
      <main className={`flex-1 w-full ${noPadding ? "" : "pb-24 md:pb-12"} ${fullHeight ? "overflow-hidden flex flex-col" : ""}`}>
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </div>
  );
};
