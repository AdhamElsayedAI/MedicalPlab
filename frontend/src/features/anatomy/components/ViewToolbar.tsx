'use client';

import React from 'react';
import { CameraPresetName } from '../scene/cameraPresets';
import { SurfacePresentationMode } from '../scene/pickingPolicy';

interface ViewToolbarProps {
  currentPreset: CameraPresetName;
  onSelectPreset: (preset: CameraPresetName) => void;
  surfaceMode: SurfacePresentationMode;
  onSetSurfaceMode: (mode: SurfacePresentationMode) => void;
  hasSelectedStructure: boolean;
  isIsolated: boolean;
  onToggleIsolate: () => void;
  onResetView: () => void;
}

export function ViewToolbar({
  currentPreset,
  onSelectPreset,
  surfaceMode,
  onSetSurfaceMode,
  hasSelectedStructure,
  isIsolated,
  onToggleIsolate,
  onResetView,
}: ViewToolbarProps) {
  return (
    <div className="absolute bottom-6 left-6 z-10 flex flex-wrap items-center gap-2 p-1.5 bg-[#0B1522]/85 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-2xl select-none">
      {/* Camera Presets Segment */}
      <div className="flex items-center gap-1 pr-2 border-r border-slate-800">
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
          Views
        </span>
        <button
          onClick={() => onSelectPreset('KIDNEY_OVERVIEW')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            currentPreset === 'KIDNEY_OVERVIEW'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Optimal 55–65% canvas height view prioritizing kidney body and hilum"
        >
          Kidney Overview
        </button>

        <button
          onClick={() => onSelectPreset('HILUM_FOCUS')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            currentPreset === 'HILUM_FOCUS'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Medial hilum framing showing Vein-Artery-Pelvis relationship"
        >
          Hilum Focus
        </button>

        <button
          onClick={() => onSelectPreset('INTERNAL_CUTAWAY')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            currentPreset === 'INTERNAL_CUTAWAY'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Anatomical cutaway revealing pyramids, columns, and collecting system inside the organ"
        >
          Cutaway View
        </button>

        <button
          onClick={() => onSelectPreset('WHOLE_MODEL')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            currentPreset === 'WHOLE_MODEL'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Complete verified anatomy including descending ureter"
        >
          Whole Model
        </button>
      </div>

      {/* Surface Presentation Modes */}
      <div className="flex items-center gap-1 pr-2 border-r border-slate-800">
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
          Layers
        </span>
        <button
          onClick={() => onSetSurfaceMode('SURFACE')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            surfaceMode === 'SURFACE'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Intact verified outer renal capsule and cortex"
        >
          Surface
        </button>

        <button
          onClick={() => onSetSurfaceMode('CUTAWAY')}
          className={`px-2.5 py-1 text-xs rounded font-medium transition ${
            surfaceMode === 'CUTAWAY' || surfaceMode === 'REVEAL'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title="Didactic medical cutaway exposing internal renal architecture nestled within the organ"
        >
          Cutaway
        </button>
      </div>

      {/* Focus & Reset Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={onToggleIsolate}
          disabled={!hasSelectedStructure}
          className={`px-2.5 py-1 text-xs rounded font-medium transition disabled:opacity-40 disabled:cursor-not-allowed ${
            isIsolated
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
          title={hasSelectedStructure ? 'Dim all other structures to focus on selection' : 'Select a structure first'}
        >
          {isIsolated ? 'Exit Isolation' : 'Isolate Selection'}
        </button>

        <button
          onClick={onResetView}
          className="px-2.5 py-1 text-xs rounded font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition"
          title="Reset camera and surface presentation"
        >
          Reset View
        </button>
      </div>
    </div>
  );
}
