"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ACADEMY_PROGRAMS, AcademyProgram } from "@/lib/stage-x-data";

export default function MedicalPlabAcademy() {
  const [selectedCertificate, setSelectedCertificate] = useState<string>("all");

  const certificates = ["all", "Clinical Reasoning", "Emergency Medicine", "AI Assisted Medicine"];

  const filteredPrograms = ACADEMY_PROGRAMS.filter((prog) => {
    if (selectedCertificate !== "all" && prog.certificateType !== selectedCertificate) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Global Academic Credentialing & Medical Education
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                Royal Colleges & WHO Partner Network
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Global Medical Academy
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Empowering the next generation of physicians, clinicians, and medical leaders with verified clinical AI credentials.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {certificates.map((cert) => (
              <button
                key={cert}
                onClick={() => setSelectedCertificate(cert)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  selectedCertificate === cert
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {cert === "all" ? "All Certificates" : cert}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Program Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPrograms.map((prog) => (
          <motion.div
            key={prog.id}
            whileHover={{ y: -3 }}
            className="bg-slate-900/70 backdrop-blur-md border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-6 shadow-xl flex flex-col justify-between transition-all group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 uppercase">
                  {prog.certificateType}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {prog.partnerType}
                </span>
              </div>

              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                {prog.title}
              </h3>

              <p className="text-xs text-cyan-400 font-mono mt-1">
                Partner: {prog.partnerName}
              </p>

              <div className="mt-3 p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] font-mono text-slate-400">
                Accreditation: {prog.accreditationBody}
              </div>

              {/* Curriculum Modules */}
              <div className="mt-4 space-y-1.5">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Curriculum Modules:
                </span>
                {prog.curriculumModules.map((mod, i) => (
                  <div key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <span className="text-cyan-400 text-xs mt-0.5">✦</span>
                    <span className="leading-tight">{mod}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Card Footer: Metrics & Enrollment CTA */}
            <div className="mt-6 pt-4 border-t border-slate-800">
              <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono mb-4">
                <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Duration</span>
                  <span className="text-white font-bold">{prog.durationWeeks} wks</span>
                </div>
                <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">ECTS</span>
                  <span className="text-cyan-400 font-bold">{prog.creditsEcts} pts</span>
                </div>
                <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Pass Rate</span>
                  <span className="text-emerald-400 font-bold">{prog.alumniPassRate}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">{prog.enrolledScholars.toLocaleString()} Scholars Enrolled</span>
                <button
                  onClick={() => alert(`Enrolled into ${prog.title}`)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold transition-colors"
                >
                  Enroll Now
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
