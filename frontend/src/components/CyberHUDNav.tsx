"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  LayoutDashboard,
  BookOpen,
  Layers3,
  HeartPulse,
  BarChart3,
  User,
  ChevronDown,
  ChevronRight,
  Settings,
  LogOut,
  Crown,
  Rocket,
  Globe,
  TrendingUp,
  Swords,
  Trophy,
  UserCheck,
  ShieldCheck,
  Sparkles,
  Play,
  X,
} from "lucide-react";
import { NavigationMode, UserRole } from "@/lib/types";

interface CyberHUDNavProps {
  currentMode: NavigationMode;
  onSelectMode: (mode: NavigationMode) => void;
  userRole: UserRole;
  onSwitchRole: (role: UserRole) => void;
  onOpenPipelineModal: () => void;
  onStartDemoJourney: () => void;
}

const PRIMARY_NAV: { mode: NavigationMode; label: string; icon: React.ReactNode }[] = [
  { mode: "command_center", label: "Dashboard",   icon: <LayoutDashboard className="w-4 h-4" /> },
  { mode: "tutor",          label: "Learn",        icon: <BookOpen         className="w-4 h-4" /> },
  { mode: "anatomy",        label: "Anatomy",      icon: <Layers3          className="w-4 h-4" /> },
  { mode: "simulation",     label: "Simulation",   icon: <HeartPulse       className="w-4 h-4" /> },
  { mode: "admin",          label: "Analytics",    icon: <BarChart3        className="w-4 h-4" /> },
];

const ADVANCED_MODES: { mode: NavigationMode; label: string; icon: React.ReactNode; description: string }[] = [
  { mode: "championship",       label: "Championship",       icon: <Trophy     className="w-4 h-4" />, description: "Competition hub & scoring" },
  { mode: "battle",             label: "Final Battle",       icon: <Swords     className="w-4 h-4" />, description: "Judge arena & pitch drills" },
  { mode: "founder",            label: "Founder Hub",        icon: <Sparkles   className="w-4 h-4" />, description: "Pitch deck & demo controller" },
  { mode: "investor",           label: "Investor Pitch",     icon: <ShieldCheck className="w-4 h-4" />, description: "Investor readiness view" },
  { mode: "validation",         label: "Impact & Validation",icon: <TrendingUp className="w-4 h-4" />, description: "Real-world outcomes data" },
  { mode: "grand_championship", label: "Grand Championship", icon: <Crown      className="w-4 h-4" />, description: "Grand stage presentation" },
  { mode: "global_intelligence",label: "Global Intelligence",icon: <Globe      className="w-4 h-4" />, description: "Global AI intelligence layer" },
  { mode: "startup_execution",  label: "Startup Launch",     icon: <Rocket     className="w-4 h-4" />, description: "Fundraising & execution mode" },
];

const ROLE_LABELS: Record<UserRole, string> = {
  STUDENT:           "Medical Student",
  DOCTOR:            "Doctor",
  INSTITUTION_ADMIN: "Educator / Admin",
};

const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  STUDENT:           "Access learning modules, quizzes, and progress tracking",
  DOCTOR:            "Clinical reasoning tools and advanced case discussions",
  INSTITUTION_ADMIN: "Analytics dashboard, cohort management, and reporting",
};

export const CyberHUDNav: React.FC<CyberHUDNavProps> = ({
  currentMode,
  onSelectMode,
  userRole,
  onSwitchRole,
  onOpenPipelineModal: _onOpenPipelineModal,
  onStartDemoJourney,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const isAdvancedActive = ADVANCED_MODES.some((m) => m.mode === currentMode);
  const isDashboardArea = ["command_center","tutor","anatomy","simulation","admin"].includes(currentMode);

  return (
    <header className="sticky top-0 z-50 w-full" style={{ background: 'rgba(11,17,32,0.92)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* ── Logo ── */}
          <button
            onClick={() => onSelectMode("landing")}
            className="flex items-center gap-3 focus:outline-none flex-shrink-0"
            aria-label="Go to homepage"
          >
            <div className="flex items-center justify-center w-9 h-9 rounded-xl" style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)' }}>
              <HeartPulse className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <div className="flex items-center gap-2">
                <span className="font-bold text-[15px] tracking-tight text-white" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
                  Medical<span style={{ color: '#38bdf8' }}>Plab</span>
                </span>
                <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ background: 'rgba(34,197,94,0.12)', color: '#86efac', border: '1px solid rgba(34,197,94,0.22)' }}>
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" style={{ boxShadow: '0 0 4px rgba(34,197,94,0.8)' }} />
                  Evidence Verified
                </span>
              </div>
            </div>
          </button>

          {/* ── Primary Navigation (desktop) ── */}
          <nav className="hidden lg:flex items-center gap-1" role="navigation" aria-label="Primary navigation">
            {PRIMARY_NAV.map((item) => {
              const isActive = currentMode === item.mode ||
                (item.mode === "command_center" && currentMode === "landing");
              return (
                <button
                  key={item.mode}
                  onClick={() => onSelectMode(item.mode)}
                  className={`nav-pill${isActive ? " active" : ""}`}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}

            {/* MCQ / Quiz under Learn — accessible via tab */}
            <button
              onClick={() => onSelectMode("quiz")}
              className={`nav-pill${currentMode === "quiz" ? " active" : ""}`}
            >
              <BookOpen className="w-4 h-4" />
              Quiz
            </button>
          </nav>

          {/* ── Right Actions ── */}
          <div className="flex items-center gap-2">

            {/* Demo CTA — prominent 3-minute guided tour */}
            <button
              onClick={onStartDemoJourney}
              className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-semibold transition-all"
              style={{ background: 'rgba(14,165,233,0.12)', color: '#7dd3fc', border: '1px solid rgba(14,165,233,0.28)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(14,165,233,0.2)';
                e.currentTarget.style.borderColor = 'rgba(14,165,233,0.45)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(14,165,233,0.12)';
                e.currentTarget.style.borderColor = 'rgba(14,165,233,0.28)';
              }}
              id="nav-demo-btn"
            >
              <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
              <span>3-Min Demo</span>
            </button>

            {/* Profile / Menu */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all"
                style={{ background: profileOpen ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
                aria-expanded={profileOpen}
                aria-haspopup="true"
                id="profile-menu-button"
              >
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0" style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)' }}>
                  {userRole === "STUDENT" ? "S" : userRole === "DOCTOR" ? "D" : "A"}
                </div>
                <span className="hidden sm:inline text-slate-300">{ROLE_LABELS[userRole].split(" ")[0]}</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${profileOpen ? "rotate-180" : ""}`} />
              </button>

              {/* Profile Dropdown */}
              {profileOpen && (
                <div
                  className="absolute right-0 mt-2 w-[300px] rounded-2xl shadow-2xl overflow-hidden med-fade-in"
                  style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', zIndex: 100 }}
                  role="menu"
                  aria-labelledby="profile-menu-button"
                >
                  {/* User info header */}
                  <div className="px-5 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0" style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)' }}>
                        {userRole === "STUDENT" ? "S" : userRole === "DOCTOR" ? "D" : "A"}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-white">
                          {userRole === "STUDENT" ? "Dr. Alice Vance" : userRole === "DOCTOR" ? "Dr. James Chen" : "Dean Administrator"}
                        </div>
                        <div className="text-xs text-slate-400">{ROLE_LABELS[userRole]}</div>
                      </div>
                    </div>
                  </div>

                  {/* Role switcher */}
                  <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Switch Role</div>
                    <div className="space-y-1">
                      {(["STUDENT", "DOCTOR", "INSTITUTION_ADMIN"] as UserRole[]).map((role) => (
                        <button
                          key={role}
                          onClick={() => {
                            onSwitchRole(role);
                            if (role === "INSTITUTION_ADMIN") onSelectMode("admin");
                            else if (role === "STUDENT") onSelectMode("command_center");
                            setProfileOpen(false);
                          }}
                          className="w-full flex items-start gap-3 p-2.5 rounded-lg text-left transition-colors"
                          style={{
                            background: userRole === role ? 'rgba(14,165,233,0.1)' : 'transparent',
                            border: userRole === role ? '1px solid rgba(14,165,233,0.2)' : '1px solid transparent',
                          }}
                          role="menuitem"
                        >
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0 ${userRole === role ? "bg-sky-500" : "bg-slate-700"}`}>
                            <User className="w-3 h-3 text-white" />
                          </div>
                          <div>
                            <div className={`text-xs font-semibold ${userRole === role ? "text-sky-300" : "text-slate-300"}`}>
                              {ROLE_LABELS[role]}
                            </div>
                            <div className="text-[11px] text-slate-500">{ROLE_DESCRIPTIONS[role]}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Advanced Workspace */}
                  <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                    <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
                      <span>Advanced Workspace</span>
                    </div>

                    {/* Featured Investor / Pitch Card */}
                    <button
                      onClick={() => { onSelectMode("investor"); setProfileOpen(false); }}
                      className="w-full p-2.5 rounded-xl text-left transition-all mb-2.5 flex items-center justify-between"
                      style={{
                        background: currentMode === "investor" ? 'rgba(14,165,233,0.18)' : 'rgba(14,165,233,0.08)',
                        border: '1px solid rgba(14,165,233,0.25)',
                      }}
                      role="menuitem"
                    >
                      <div>
                        <div className="text-xs font-bold text-sky-300 flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
                          <span>Investor Pitch &amp; Memo</span>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">TAM ($4.8B), Unit Economics &amp; Moats</div>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 text-sky-400" />
                    </button>

                    {/* Grid for other advanced workspaces */}
                    <div className="grid grid-cols-2 gap-1">
                      {ADVANCED_MODES.filter((m) => m.mode !== "investor").map((item) => (
                        <button
                          key={item.mode}
                          onClick={() => { onSelectMode(item.mode); setProfileOpen(false); }}
                          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left transition-colors"
                          style={{ background: currentMode === item.mode ? 'rgba(14,165,233,0.1)' : 'rgba(255,255,255,0.03)' }}
                          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.background = currentMode === item.mode ? 'rgba(14,165,233,0.1)' : 'rgba(255,255,255,0.03)'; }}
                          role="menuitem"
                        >
                          <span className="text-slate-400 flex-shrink-0">{item.icon}</span>
                          <span className="text-xs font-medium text-slate-300 leading-tight">{item.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Footer actions */}
                  <div className="px-5 py-3 flex items-center justify-between">
                    <button
                      onClick={() => { setProfileOpen(false); }}
                      className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                      role="menuitem"
                    >
                      <Settings className="w-3.5 h-3.5" />
                      Settings
                    </button>
                    <div className="flex items-center gap-1.5 text-[11px]" style={{ color: '#86efac' }}>
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
                      AI Core Online
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle mobile menu"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : (
                <div className="flex flex-col gap-1">
                  <div className="w-4 h-0.5 bg-current rounded" />
                  <div className="w-4 h-0.5 bg-current rounded" />
                  <div className="w-4 h-0.5 bg-current rounded" />
                </div>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden med-fade-in" style={{ background: '#111827', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          <div className="max-w-7xl mx-auto px-4 py-4 space-y-1">
            {PRIMARY_NAV.map((item) => {
              const isActive = currentMode === item.mode;
              return (
                <button
                  key={item.mode}
                  onClick={() => { onSelectMode(item.mode); setMobileMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors text-left"
                  style={{
                    background: isActive ? 'rgba(14,165,233,0.1)' : 'transparent',
                    color: isActive ? '#7dd3fc' : '#94a3b8',
                    border: isActive ? '1px solid rgba(14,165,233,0.2)' : '1px solid transparent',
                  }}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
            <button
              onClick={() => { onSelectMode("quiz"); setMobileMenuOpen(false); }}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors text-left"
              style={{ color: '#94a3b8', border: '1px solid transparent' }}
            >
              <BookOpen className="w-4 h-4" />
              Quiz
            </button>
            <div className="pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}>
              <button
                onClick={() => { onStartDemoJourney(); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium"
                style={{ background: 'rgba(14,165,233,0.1)', color: '#7dd3fc', border: '1px solid rgba(14,165,233,0.22)' }}
              >
                <Play className="w-4 h-4 fill-current" />
                Launch Guided Demo
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
