'use client';

import React from 'react';

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SourcesModal({ isOpen, onClose }: SourcesModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs select-none">
      <div className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-2xl overflow-hidden animate-fade-in flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-500" />
            <h3 className="text-sm font-bold text-slate-900">
              Anatomy Sources &amp; Provenance
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs text-slate-600 overflow-y-auto max-h-[70vh]">
          {/* Primary Source */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
            <div className="font-bold text-slate-800 text-xs flex items-center justify-between">
              <span>HuBMAP Human Reference Atlas (HRA)</span>
              <span className="px-2 py-0.5 rounded bg-teal-100 text-teal-800 font-mono text-[10px]">
                CC BY 4.0
              </span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Curated 3D Reference Organ Objects from the NIH Human BioMolecular Atlas Program (HuBMAP) CCF 3D Reference Object Library.
            </p>
            <div className="pt-1">
              <a
                href="https://humanatlas.io/3d-reference-library"
                target="_blank"
                rel="noreferrer"
                className="text-teal-600 hover:underline font-medium inline-flex items-center gap-1"
              >
                <span>Visit HuBMAP 3D Reference Object Library</span>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>

          {/* Coordinate Framework */}
          <div className="space-y-1">
            <div className="font-semibold text-slate-800">
              Common Coordinate Framework (CCF)
            </div>
            <p className="text-slate-600 leading-relaxed">
              All models are rendered strictly in canonical CCF anatomical coordinate space without independent scaling or artificial fabrication, preserving true spatial relationships between the kidney capsule, renal vasculature, and collecting system.
            </p>
          </div>

          {/* Ontologies */}
          <div className="space-y-1">
            <div className="font-semibold text-slate-800">
              Authoritative Ontologies
            </div>
            <ul className="list-disc pl-4 space-y-1 text-slate-600">
              <li><strong>UBERON:</strong> Cross-species anatomy ontology (e.g. Left Renal Artery: UBERON:0001186, Left Renal Vein: UBERON:0001142, Hilum: UBERON:0008716).</li>
              <li><strong>FMA:</strong> Foundational Model of Anatomy ontology for human clinical alignment.</li>
            </ul>
          </div>

          {/* AI Tutoring Attribution */}
          <div className="p-3 bg-teal-50/60 rounded-xl border border-teal-100 text-teal-900 text-xs">
            <strong>Educational AI Grounding:</strong> AI tutoring recommendations and deterministic scoring are anchored directly to verified anatomical coordinates and expert-reviewed medical curricula. Geometry is never generated or fabricated.
          </div>

          {/* Display Presentation Disclosure */}
          <div className="p-2.5 bg-slate-100 rounded-lg text-slate-500 text-[11px] leading-relaxed space-y-1.5">
            <div>
              <strong>Display Note:</strong> In Kidney Overview and Hilum Focus teaching perspectives, contralateral bilateral vessels from the source HRA asset are filtered so learners focus strictly on the left renal hilum and collecting system. The original verified full extent remains accessible in Whole Model.
            </div>
            <div>
              <strong>Cutaway Note:</strong> Cutaway is a didactic presentation view derived from verified HRA geometry. Anatomical structures retain their original HRA positions and proportions.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs rounded-xl transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
