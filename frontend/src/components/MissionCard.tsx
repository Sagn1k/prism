"use client";

import { motion } from "framer-motion";
import type { Mission } from "@/lib/api";

const TYPE_META: Record<string, { icon: string; label: string; bg: string }> = {
  flash: { icon: "⚡", label: "Quick Fire", bg: "bg-amber-100" },
  scenario_sim: { icon: "🎭", label: "Scenario", bg: "bg-cyan-100" },
  build_quest: { icon: "🔨", label: "Build Quest", bg: "bg-pink-100" },
  ai_debate: { icon: "💬", label: "AI Debate", bg: "bg-violet-100" },
  this_or_that: { icon: "↔️", label: "This or That", bg: "bg-emerald-100" },
};

const DIFF_META: Record<string, { badge: string; xp: string }> = {
  easy: { badge: "badge-easy", xp: "~5 XP" },
  medium: { badge: "badge-medium", xp: "~8 XP" },
  hard: { badge: "badge-hard", xp: "~12 XP" },
};

interface Props {
  mission: Mission;
  index: number;
  onClick?: () => void;
}

export default function MissionCard({ mission, index, onClick }: Props) {
  const type = TYPE_META[mission.type] || TYPE_META.flash;
  const diff = DIFF_META[mission.difficulty] || DIFF_META.easy;
  const minutes = Math.ceil(mission.duration_seconds / 60);
  const done = mission.completed === true;

  return (
    <motion.button
      onClick={done ? undefined : onClick}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      whileHover={done ? {} : { scale: 1.02, y: -2 }}
      whileTap={done ? {} : { scale: 0.98 }}
      className={`card-interactive p-5 text-left w-full group ${done ? "opacity-70 cursor-default" : ""}`}
      disabled={done}
    >
      <div className="flex items-center gap-4">
        {/* Quest icon */}
        <div className="relative">
          <div
            className={`w-12 h-12 rounded-2xl ${type.bg} flex items-center justify-center text-2xl shrink-0
                        ${done ? "grayscale" : ""}`}
          >
            {type.icon}
          </div>
          {done && (
            <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-prism-green flex items-center justify-center">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="white">
                <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
              </svg>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className={`font-bold truncate transition-colors ${done ? "text-prism-text-muted" : "text-prism-text group-hover:text-prism-violet"}`}>
            {mission.title}
          </h3>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {done ? (
              <span className="badge bg-emerald-50 text-emerald-600 border border-emerald-200">
                ✓ +{mission.xp_earned ?? 0} XP earned
              </span>
            ) : (
              <>
                <span className={diff.badge}>{mission.difficulty}</span>
                <span className="text-xs text-prism-text-muted font-medium">~{minutes} min</span>
                <span className="text-xs text-prism-text-muted">•</span>
                <span className="text-xs font-semibold text-prism-amber">{diff.xp}</span>
              </>
            )}
          </div>
        </div>

        {/* Play button or completed check */}
        {done ? (
          <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-prism-green shrink-0 border border-emerald-200">
            ✓
          </div>
        ) : (
          <div className="w-10 h-10 rounded-xl bg-prism-violet/10 flex items-center justify-center
                          group-hover:bg-prism-violet group-hover:text-white text-prism-violet
                          transition-all duration-200 shrink-0">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 2l10 6-10 6V2z" />
            </svg>
          </div>
        )}
      </div>
    </motion.button>
  );
}
