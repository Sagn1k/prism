"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { worldsApi, type World } from "@/lib/api";

const FALLBACK_WORLDS: World[] = [
  {
    id: "1",
    name: "Space Lab",
    slug: "space-lab",
    description: "Explore the unknown and test your curiosity.",
    color_hex: "#00ACC1",
    icon_url: null,
    sort_order: 1,
    mission_count: 4,
    user_progress: null,
  },
  {
    id: "2",
    name: "Creator Studio",
    slug: "creator-studio",
    description: "Unleash your imagination and creative superpower.",
    color_hex: "#E040FB",
    icon_url: null,
    sort_order: 2,
    mission_count: 4,
    user_progress: null,
  },
  {
    id: "3",
    name: "Code Dungeon",
    slug: "code-dungeon",
    description: "Solve puzzles, crack logic, and sharpen your mind.",
    color_hex: "#7C4DFF",
    icon_url: null,
    sort_order: 3,
    mission_count: 3,
    user_progress: null,
  },
  {
    id: "4",
    name: "Market Arena",
    slug: "market-arena",
    description: "Build, trade, and discover your entrepreneurial edge.",
    color_hex: "#F59E0B",
    icon_url: null,
    sort_order: 4,
    mission_count: 3,
    user_progress: null,
  },
];

const WORLD_META: Record<string, { emoji: string; bg: string; border: string }> = {
  "space-lab": { emoji: "🔬", bg: "bg-cyan-50", border: "border-cyan-200" },
  "creator-studio": { emoji: "🎨", bg: "bg-pink-50", border: "border-pink-200" },
  "code-dungeon": { emoji: "💻", bg: "bg-violet-50", border: "border-violet-200" },
  "market-arena": { emoji: "🚀", bg: "bg-amber-50", border: "border-amber-200" },
};

export default function WorldsPage() {
  const [worlds, setWorlds] = useState<World[]>(FALLBACK_WORLDS);

  useEffect(() => {
    worldsApi
      .list()
      .then((r) => setWorlds(r.data))
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <div className="text-5xl mb-3">🗺️</div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-prism-text">
          Choose Your <span className="text-gradient">World</span>
        </h1>
        <p className="text-prism-text-secondary mt-2 text-lg">
          Each world has quests that reveal a different part of your spectrum
        </p>
      </motion.div>

      <div className="grid sm:grid-cols-2 gap-5">
        {worlds.map((w, i) => {
          const meta = WORLD_META[w.slug] || { emoji: "🌍", bg: "bg-gray-50", border: "border-gray-200" };
          const pct = w.user_progress != null ? Math.round(w.user_progress * 100) : 0;
          const completed = w.user_progress != null ? Math.round(w.user_progress * w.mission_count) : 0;
          return (
            <motion.div
              key={w.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
            >
              <Link
                href={`/worlds/${w.id}`}
                className={`block p-6 rounded-2xl border-2 ${meta.bg} ${meta.border}
                           hover:shadow-card-hover hover:scale-[1.02] transition-all duration-200 group`}
              >
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-white/80 flex items-center justify-center text-4xl shrink-0 shadow-sm">
                    {meta.emoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h2 className="font-extrabold text-lg text-prism-text group-hover:text-prism-violet transition-colors">
                      {w.name}
                    </h2>
                    <p className="text-sm text-prism-text-secondary mt-1 leading-relaxed">
                      {w.description}
                    </p>
                  </div>
                </div>

                {/* Quest progress */}
                <div className="mt-5">
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span className="text-prism-text-secondary">
                      {completed}/{w.mission_count} quests
                    </span>
                    <span style={{ color: w.color_hex }}>{pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8, delay: 0.3 + i * 0.1 }}
                      className="progress-fill"
                      style={{ backgroundColor: w.color_hex }}
                    />
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <span className="badge bg-white/80 text-prism-text-secondary border border-prism-border">
                    {w.mission_count} missions
                  </span>
                  <span className="text-prism-violet font-bold text-sm group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                    Play →
                  </span>
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
