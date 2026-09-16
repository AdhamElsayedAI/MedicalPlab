'use client';

import React from 'react';

interface AnatomyHeaderProps {
  onOpenSources: () => void;
  onResetCamera: () => void;
  isDemoActive: boolean;
  onToggleDemo: () => void;
  debugMode?: boolean;
  perfStats?: {
    fps: number;
    loadTimeMs: number;
    triangleCount: number;
  };
}

export function AnatomyHeader({
  onOpenSources,
  onResetCamera,
  isDemoActive,
  onToggleDemo,
  debugMode = false,
  perfStats,
}: AnatomyHeaderProps) {
  return (
    <header className="h-16 px-6 bg-[#0E1726] border-b border-slate-800/80 flex items-center justify-between select-none shrink-0 z-20">
      {/* Brand & Module Identification */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-teal-400 ring-4 ring-teal-950/60" />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-[15px] font-semibold tracking-tight text-slate-100">
                MedicalPlab Anatomy Lab
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-teal-950/70 text-teal-300 border border-teal-800/50">
                Renal Anatomy
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Verified anatomy · AI-guided learning
            </p>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Debug diagnostics (Only if ?debug=1) */}
        {debugMode && perfStats && (
          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 bg-slate-900/90 rounded border border-slate-700 text-[10px] font-mono text-slate-400">
            <span>FPS: <strong className="text-emerald-400">{perfStats.fps}</strong></span>
            <span>Load: <strong className="text-cyan-400">{perfStats.loadTimeMs}ms</strong></span>
            <span>Tris: <strong className="text-amber-400">{perfStats.triangleCount.toLocaleString()}</strong></span>
          </div>
        )}

        {/* Home Camera Reset */}
        <button
          onClick={onResetCamera}
          title="Reset camera to default overview without altering lesson progress"
          className="px-3 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-700 border border-slate-700/60 transition flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Home View
        </button>

        {/* Demo Mode Toggle */}
        <button
          onClick={onToggleDemo}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 border ${
            isDemoActive
              ? 'bg-teal-500/20 text-teal-300 border-teal-500/50 shadow-sm'
              : 'bg-slate-800/60 text-slate-300 hover:text-white hover:bg-slate-700 border-slate-700/60'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isDemoActive ? 'bg-teal-400 animate-pulse' : 'bg-slate-500'}`} />
          {isDemoActive ? 'Exit Demo' : 'Demo Mode'}
        </button>

        {/* Sources & Provenance */}
        <button
          onClick={onOpenSources}
          className="px-3 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-700 border border-slate-700/60 transition flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Sources &amp; Details
        </button>
      </div>
    </header>
  );
}
