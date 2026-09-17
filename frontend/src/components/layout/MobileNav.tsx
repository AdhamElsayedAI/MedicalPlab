"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Sparkles,
  Layers3,
  TrendingUp,
} from "lucide-react";

export const MobileNav: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Hub", icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: "/practice", label: "Practice", icon: <BookOpen className="w-5 h-5" /> },
    { href: "/tutor", label: "Tutor", icon: <Sparkles className="w-5 h-5" /> },
    { href: "/anatomy", label: "Anatomy", icon: <Layers3 className="w-5 h-5" /> },
    { href: "/progress", label: "Progress", icon: <TrendingUp className="w-5 h-5" /> },
  ];

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href === "/practice") return pathname === "/practice" || pathname.startsWith("/university");
    return pathname.startsWith(href);
  };

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#090d16]/95 backdrop-blur-2xl border-t border-white/[0.08] px-2 py-1.5 shadow-2xl shadow-black"
      aria-label="Mobile Bottom Navigation"
    >
      <div className="grid grid-cols-5 gap-1 items-center">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center py-2 px-1 rounded-xl transition-all min-h-[52px] ${
                active
                  ? "text-sky-400 font-semibold bg-sky-500/10"
                  : "text-slate-400 hover:text-slate-200 active:scale-95"
              }`}
            >
              <div className={`transition-transform ${active ? "scale-110" : ""}`}>
                {item.icon}
              </div>
              <span className="text-[10px] mt-1 tracking-tight truncate max-w-full">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
