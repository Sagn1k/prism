"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";
import LoginModal from "@/components/LoginModal";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/worlds", label: "Worlds", icon: "🗺️" },
  { href: "/chat", label: "Ray AI", icon: "🤖" },
  { href: "/profile", label: "My Prism", icon: "🔮" },
];

const LEVEL_NAMES = ["", "Spark", "Ray", "Beam", "Spectrum", "Master"];

export default function Navbar() {
  const pathname = usePathname();
  const user = useAuth((s) => s.user);
  const loading = useAuth((s) => s.loading);
  const logout = useAuth((s) => s.logout);
  const [showLogin, setShowLogin] = useState(false);

  const xpInLevel = user ? user.xp_points % 100 : 0;
  const levelName = user ? (LEVEL_NAMES[user.level] || `Lv ${user.level}`) : "";

  return (
    <>
      <nav className="fixed top-0 inset-x-0 z-50 h-16 bg-white/80 backdrop-blur-xl border-b border-prism-border">
        <div className="max-w-6xl mx-auto h-full px-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-prism-gradient flex items-center justify-center shadow-md">
              <span className="text-white font-extrabold text-sm">P</span>
            </div>
            <span className="font-extrabold text-lg tracking-tight text-prism-text">Prism</span>
          </Link>

          <div className="flex items-center gap-1">
            {NAV_ITEMS.map(({ href, label, icon }) => {
              const active =
                href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className="relative px-4 py-2 text-sm font-semibold rounded-xl transition-colors"
                >
                  {active && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 bg-prism-violet/10 rounded-xl"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span
                    className={`relative z-10 flex items-center gap-1.5 ${
                      active ? "text-prism-violet" : "text-prism-text-secondary hover:text-prism-text"
                    }`}
                  >
                    <span className="text-base">{icon}</span>
                    {label}
                  </span>
                </Link>
              );
            })}
          </div>

          <div className="flex items-center gap-3">
            {loading ? (
              <div className="w-32 h-10 bg-prism-surface-alt rounded-xl animate-pulse" />
            ) : user ? (
              <div className="flex items-center gap-2">
                {/* XP + Level pill */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-prism-surface-alt border border-prism-border">
                  <span className="text-base">⭐</span>
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-prism-amber leading-none">
                      {user.xp_points} XP
                    </span>
                    <div className="w-14 h-1.5 bg-prism-border rounded-full mt-0.5 overflow-hidden">
                      <div
                        className="h-full bg-prism-amber rounded-full transition-all duration-500"
                        style={{ width: `${xpInLevel}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-px h-5 bg-prism-border" />
                  <span className="badge-level text-[10px]">
                    {levelName}
                  </span>
                </div>

                <button
                  onClick={logout}
                  className="text-xs font-semibold text-prism-text-muted hover:text-prism-red transition-colors
                             px-3 py-2 rounded-xl hover:bg-red-50"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowLogin(true)}
                className="btn-primary text-sm px-5 py-2.5"
              >
                Start Playing
              </button>
            )}
          </div>
        </div>
      </nav>
      <LoginModal open={showLogin} onClose={() => setShowLogin(false)} />
    </>
  );
}
