"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  Sparkles,
  Layers3,
  TrendingUp,
  LayoutDashboard,
  Check,
  Copy,
  RotateCcw,
  ShieldCheck,
  Radio,
  ChevronDown,
} from "lucide-react";
import { api, getAuthoritativeLearnerId, LEARNER_STORAGE_KEY } from "@/lib/api-client";

interface HeaderNavProps {
  learnerId?: string;
  onLearnerIdChange?: (newId: string) => void;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({
  learnerId: propLearnerId,
  onLearnerIdChange,
}) => {
  const pathname = usePathname();
  const [learnerId, setLearnerId] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = propLearnerId || getAuthoritativeLearnerId();
    setLearnerId(id);
  }, [propLearnerId]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCopyId = () => {
    if (navigator?.clipboard && learnerId) {
      navigator.clipboard.writeText(learnerId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleResetProfile = () => {
    const newId = `uni-${crypto.randomUUID().slice(0, 8)}`;
    if (typeof window !== "undefined") {
      localStorage.setItem(LEARNER_STORAGE_KEY, newId);
    }
    api.setUser(newId);
    setLearnerId(newId);
    if (onLearnerIdChange) onLearnerIdChange(newId);
    setProfileDropdownOpen(false);
  };

  const navItems = [
    { href: "/", label: "Learning Hub", icon: <LayoutDashboard className="w-4 h-4" /> },
    { href: "/practice", label: "Practice", icon: <BookOpen className="w-4 h-4" /> },
    { href: "/tutor", label: "AI Tutor", icon: <Sparkles className="w-4 h-4" /> },
    { href: "/anatomy", label: "3D Anatomy", icon: <Layers3 className="w-4 h-4" /> },
    { href: "/progress", label: "Progress", icon: <TrendingUp className="w-4 h-4" /> },
  ];

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href === "/practice") return pathname === "/practice" || pathname.startsWith("/university");
    return pathname.startsWith(href);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-[#090d16]/85 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 p-[1px] shadow-lg shadow-sky-500/20 group-hover:shadow-sky-500/30 transition-all">
            <div className="w-full h-full bg-[#0b1120] rounded-[11px] flex items-center justify-center">
              <Activity className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white font-['Plus_Jakarta_Sans',sans-serif]">
                Medical<span className="text-sky-400">Plab</span>
              </span>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                Pilot v1.1
              </span>
            </div>
            <p className="hidden md:block text-[11px] text-slate-400 tracking-wide">
              Adaptive Medical Learning Platform
            </p>
          </div>
        </Link>

        {/* Primary Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/[0.06]" aria-label="Main Navigation">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  active
                    ? "bg-sky-500/15 text-sky-300 border border-sky-500/30 shadow-sm shadow-sky-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Section: Backend Status & Learner Identity */}
        <div className="flex items-center gap-2.5">
          {/* Educator Portal Link */}
          <Link
            href="/radar"
            title="Educator Cohort Radar"
            className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent hover:border-white/[0.08] transition-all"
          >
            <Radio className="w-3.5 h-3.5 text-indigo-400" />
            <span>Cohort Radar</span>
          </Link>

          {/* Learner Identity Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-medium text-slate-200 transition-all focus:outline-none focus:ring-2 focus:ring-sky-400/50 shrink-0"
              aria-expanded={profileDropdownOpen}
              aria-label="Learner Profile Menu"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
              <span className="text-xs font-medium text-slate-200">
                <span className="hidden sm:inline">Learner Profile</span>
                <span className="sm:hidden">Profile</span>
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            </button>

            {profileDropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-[#0f172a] border border-white/[0.12] p-4 shadow-2xl shadow-black/80 z-50 med-fade-in">
                <div className="flex items-center justify-between mb-3 pb-3 border-b border-white/[0.08]">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-white">Learner Identity</span>
                  </div>
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                    Active
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1 block">
                      Canonical Header (X-User-Id)
                    </label>
                    <div className="flex items-center justify-between bg-black/40 rounded-lg p-2 border border-white/[0.06]">
                      <span className="font-mono text-xs text-sky-300 truncate max-w-[190px]">
                        {learnerId}
                      </span>
                      <button
                        onClick={handleCopyId}
                        title="Copy Learner ID"
                        className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                      >
                        {copied ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Identity persists attempts, adaptive recommendations, and 3D challenge mastery.
                  </p>

                  <button
                    onClick={handleResetProfile}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 border border-white/[0.08] transition-all"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
                    <span>Reset to Fresh Learner Profile</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
