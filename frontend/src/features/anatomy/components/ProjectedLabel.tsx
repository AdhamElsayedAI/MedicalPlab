'use client';

import React from 'react';
import { ProjectedAnchor } from '../scene/AnatomyViewport';

interface ProjectedLabelProps {
  anchor: ProjectedAnchor | null;
  displayName: string;
  isChallengeMode?: boolean;
}

export function ProjectedLabel({
  anchor,
  displayName,
  isChallengeMode = false,
}: ProjectedLabelProps) {
  if (!anchor || !anchor.visible) return null;

  // Clamp within safe canvas boundaries:
  // Margin 30px from left/top, safe margin from right edge
  const safeX = Math.max(30, Math.min(anchor.screenX, window.innerWidth - 420));
  const safeY = Math.max(80, Math.min(anchor.screenY, window.innerHeight - 100));

  // In active challenge mode, do not leak identity of unselected test structures if restricted
  const labelText = isChallengeMode ? 'Selected Structure' : displayName;

  return (
    <div
      style={{
        left: `${safeX}px`,
        top: `${safeY}px`,
        transform: 'translate(-50%, -120%)',
      }}
      className="absolute z-10 pointer-events-none transition-all duration-150 select-none"
    >
      <div className="flex flex-col items-center">
        {/* Label Badge */}
        <div className="px-3 py-1 rounded-full bg-slate-900/90 backdrop-blur-md border border-amber-400/60 text-amber-300 shadow-xl flex items-center gap-1.5 whitespace-nowrap animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          <span className="text-xs font-semibold tracking-wide">
            {labelText}
          </span>
        </div>
        {/* Subtle pointer indicator */}
        <div className="w-1.5 h-1.5 bg-amber-400/80 rounded-full mt-1 ring-2 ring-slate-900 shadow" />
      </div>
    </div>
  );
}
