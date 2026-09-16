'use client';

import React, { useState } from 'react';
import { AnatomyStructure } from '@/lib/anatomy/types';
import { adaptStructure, formatRelationshipSummary } from '../adapters/anatomyPresentationAdapter';

interface ExplorePanelProps {
  selectedStructure: AnatomyStructure | null;
  onFocusStructure: (structureId: string) => void;
  onIsolateStructure: (structureId: string) => void;
  onAskTutor: (prompt: string) => void;
  onSelectStructureByName: (structureId: string) => void;
}

export function ExplorePanel({
  selectedStructure,
  onFocusStructure,
  onIsolateStructure,
  onAskTutor,
  onSelectStructureByName,
}: ExplorePanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!selectedStructure) {
    return (
      <div className="flex flex-col gap-4 py-4">
        <div className="p-4 bg-teal-50/60 rounded-xl border border-teal-100 text-slate-700">
          <div className="flex items-center gap-2 mb-1.5 text-teal-800 font-semibold text-xs">
            <svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
            Interactive Exploration
          </div>
          <p className="text-xs leading-relaxed text-slate-600">
            Click any anatomical structure on the 3D model (capsule, renal artery, renal vein, or pelvis) to inspect its anatomical and clinical significance.
          </p>
        </div>

        {/* Quick Structure Shortcuts */}
        <div className="flex flex-col gap-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Key Renal Structures
          </span>
          <div className="grid grid-cols-1 gap-1.5">
            {[
              { id: 'renal_artery_left', label: 'Left Renal Artery', color: 'border-l-rose-500' },
              { id: 'renal_vein_left', label: 'Left Renal Vein', color: 'border-l-blue-500' },
              { id: 'renal_pelvis_left', label: 'Left Renal Pelvis', color: 'border-l-amber-500' },
              { id: 'kidney_capsule_left', label: 'Kidney Capsule', color: 'border-l-emerald-500' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => onSelectStructureByName(item.id)}
                className={`flex items-center justify-between p-2.5 bg-white hover:bg-slate-50 border border-slate-200 border-l-4 ${item.color} rounded-lg text-xs font-medium text-slate-700 transition text-left shadow-xs`}
              >
                <span>{item.label}</span>
                <span className="text-slate-400 text-[10px]">Select &rarr;</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const presented = adaptStructure(selectedStructure);
  const relationshipSummaries = formatRelationshipSummary(presented.relationships);

  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Title & Short Category */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-teal-100 text-teal-800">
            {presented.category}
          </span>
        </div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight" id="selected-structure-display">
          {presented.displayName}
        </h2>
      </div>

      {/* Verified Description */}
      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
        <p className="text-xs text-slate-700 leading-relaxed">
          {presented.shortDescription}
        </p>
      </div>

      {/* Clinical Relevance */}
      <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
          Clinical Relevance
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          {presented.clinicalRelevance}
        </p>
      </div>

      {/* Simple Grounded Relationships */}
      {relationshipSummaries.length > 0 && (
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
            Anatomical Relationships
          </div>
          <ul className="space-y-1">
            {relationshipSummaries.map((summary, idx) => (
              <li key={idx} className="text-xs text-slate-600 flex items-start gap-1.5">
                <span className="text-teal-600 font-bold">&bull;</span>
                <span>{summary}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onFocusStructure(presented.structureId)}
          className="flex-1 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition text-center"
        >
          Focus View
        </button>
        <button
          onClick={() => onIsolateStructure(presented.structureId)}
          className="flex-1 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition text-center"
        >
          Isolate
        </button>
        <button
          onClick={() => onAskTutor(`Explain the clinical significance of ${presented.displayName}`)}
          className="flex-1 py-1.5 px-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg transition text-center shadow-xs"
        >
          Ask Tutor
        </button>
      </div>

      {/* Collapsible Anatomy Details (UBERON, Provenance) */}
      <div className="border-t border-slate-200 pt-3">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-xs font-medium text-slate-500 hover:text-slate-800 transition"
        >
          <span>Anatomy details &amp; citations</span>
          <span>{showAdvanced ? '−' : '+'}</span>
        </button>

        {showAdvanced && (
          <div className="mt-2.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-[11px] space-y-1.5 text-slate-600">
            <div className="flex justify-between">
              <span className="text-slate-400">Ontology ID:</span>
              <span className="font-mono font-medium text-slate-800">{presented.ontologyId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Source:</span>
              <span>{presented.sourceSystem}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Mesh Nodes:</span>
              <span className="font-mono text-[10px] text-slate-500 truncate max-w-[180px]">
                {presented.meshNodeNames.join(', ')}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
