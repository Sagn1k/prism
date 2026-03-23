"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { worldsApi, type Mission, type World } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

/* ─── World theming ─── */

interface WorldTheme {
  emoji: string;
  bg: string;
  sceneryGradient: string;
  groundGradient: string;
  pathColor: string;
  pathGlow: string;
  accentFrom: string;
  accentTo: string;
  nodeActive: string;
  nodeDone: string;
  decorations: string[];
  mascot: string;
  mascotName: string;
}

const THEMES: Record<string, WorldTheme> = {
  "space-lab": {
    emoji: "🔬",
    bg: "from-slate-900 via-indigo-950 to-purple-950",
    sceneryGradient: "from-indigo-200/30 via-cyan-100/20 to-transparent",
    groundGradient: "from-indigo-100 to-cyan-50",
    pathColor: "#00ACC1",
    pathGlow: "drop-shadow(0 0 8px rgba(0, 172, 193, 0.4))",
    accentFrom: "#00ACC1",
    accentTo: "#0097A7",
    nodeActive: "from-cyan-400 to-teal-500",
    nodeDone: "from-cyan-300 to-teal-400",
    decorations: ["🪐", "🌟", "🚀", "🛸", "✨", "💫"],
    mascot: "🦕",
    mascotName: "Cosmo",
  },
  "creator-studio": {
    emoji: "🎨",
    bg: "from-pink-50 via-fuchsia-50 to-violet-50",
    sceneryGradient: "from-pink-200/40 via-fuchsia-100/30 to-transparent",
    groundGradient: "from-pink-100 to-fuchsia-50",
    pathColor: "#E040FB",
    pathGlow: "drop-shadow(0 0 8px rgba(224, 64, 251, 0.4))",
    accentFrom: "#E040FB",
    accentTo: "#AB47BC",
    nodeActive: "from-pink-400 to-fuchsia-500",
    nodeDone: "from-pink-300 to-fuchsia-400",
    decorations: ["🎭", "🎵", "🖌️", "📸", "🎬", "💜"],
    mascot: "🦄",
    mascotName: "Arty",
  },
  "code-dungeon": {
    emoji: "💻",
    bg: "from-violet-50 via-purple-50 to-indigo-50",
    sceneryGradient: "from-violet-200/40 via-purple-100/30 to-transparent",
    groundGradient: "from-violet-100 to-purple-50",
    pathColor: "#7C4DFF",
    pathGlow: "drop-shadow(0 0 8px rgba(124, 77, 255, 0.4))",
    accentFrom: "#7C4DFF",
    accentTo: "#651FFF",
    nodeActive: "from-violet-400 to-purple-600",
    nodeDone: "from-violet-300 to-purple-400",
    decorations: ["⚙️", "🔮", "💎", "🧩", "🗝️", "⚡"],
    mascot: "🐉",
    mascotName: "Logix",
  },
  "market-arena": {
    emoji: "🚀",
    bg: "from-amber-50 via-orange-50 to-yellow-50",
    sceneryGradient: "from-amber-200/40 via-orange-100/30 to-transparent",
    groundGradient: "from-amber-100 to-orange-50",
    pathColor: "#F59E0B",
    pathGlow: "drop-shadow(0 0 8px rgba(245, 158, 11, 0.4))",
    accentFrom: "#F59E0B",
    accentTo: "#D97706",
    nodeActive: "from-amber-400 to-orange-500",
    nodeDone: "from-amber-300 to-orange-400",
    decorations: ["💰", "📊", "🏦", "💡", "🎯", "🔥"],
    mascot: "🦊",
    mascotName: "Biz",
  },
};

const DEFAULT_THEME = THEMES["space-lab"];

const DIFF_ORDER: Record<string, number> = { easy: 0, medium: 1, hard: 2 };

const DIFF_META: Record<string, { stars: number; label: string; color: string; tierName: string; tierEmoji: string }> = {
  easy:   { stars: 1, label: "Easy",   color: "#10B981", tierName: "Meadow",    tierEmoji: "🌿" },
  medium: { stars: 2, label: "Medium", color: "#F59E0B", tierName: "Hills",     tierEmoji: "⛰️" },
  hard:   { stars: 3, label: "Hard",   color: "#EF4444", tierName: "Summit",    tierEmoji: "🌋" },
};

const TYPE_ICONS: Record<string, string> = {
  flash: "⚡",
  scenario_sim: "🎭",
  build_quest: "🔨",
  ai_debate: "💬",
  this_or_that: "↔️",
};

/* ─── Floating decorations ─── */

function FloatingDecor({ items }: { items: string[] }) {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {items.map((item, i) => (
        <motion.div
          key={i}
          className="absolute text-2xl opacity-20"
          style={{
            left: `${10 + (i * 17) % 80}%`,
            top: `${5 + (i * 23) % 85}%`,
          }}
          animate={{
            y: [0, -15, 0],
            rotate: [0, i % 2 === 0 ? 10 : -10, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 3 + i * 0.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.4,
          }}
        >
          {item}
        </motion.div>
      ))}
    </div>
  );
}

/* ─── Mascot character ─── */

function Mascot({ emoji, name, message }: { emoji: string; name: string; message: string }) {
  return (
    <motion.div
      className="flex items-end gap-3"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3, type: "spring" }}
    >
      <motion.div
        animate={{ y: [0, -8, 0], rotate: [0, -5, 5, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="text-5xl"
      >
        {emoji}
      </motion.div>
      <motion.div
        initial={{ scale: 0, originX: 0, originY: 1 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.6, type: "spring", stiffness: 300 }}
        className="relative bg-white rounded-2xl rounded-bl-md px-4 py-2.5 shadow-card border border-prism-border max-w-[220px]"
      >
        <p className="text-xs text-prism-text-secondary leading-relaxed">
          <span className="font-bold text-prism-text">{name}:</span> {message}
        </p>
        {/* Speech bubble tail */}
        <div className="absolute -bottom-1.5 left-3 w-3 h-3 bg-white border-b border-l border-prism-border rotate-[-35deg]" />
      </motion.div>
    </motion.div>
  );
}

/* ─── Tier separator ─── */

function TierBanner({ tierName, tierEmoji, color, index }: { tierName: string; tierEmoji: string; color: string; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.2 + index * 0.05 }}
      className="flex items-center gap-3 py-2"
    >
      <div className="flex-1 h-px bg-gradient-to-r from-transparent" style={{ backgroundImage: `linear-gradient(to right, transparent, ${color}40)` }} />
      <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border-2" style={{ borderColor: `${color}30`, backgroundColor: `${color}08` }}>
        <span className="text-lg">{tierEmoji}</span>
        <span className="text-xs font-extrabold uppercase tracking-widest" style={{ color }}>{tierName}</span>
      </div>
      <div className="flex-1 h-px bg-gradient-to-l from-transparent" style={{ backgroundImage: `linear-gradient(to left, transparent, ${color}40)` }} />
    </motion.div>
  );
}

/* ─── Quest node ─── */

function QuestNode({
  mission,
  index,
  isUnlocked,
  isActive,
  isDone,
  onClick,
  theme,
  position,
}: {
  mission: Mission;
  index: number;
  isUnlocked: boolean;
  isActive: boolean;
  isDone: boolean;
  onClick: () => void;
  theme: WorldTheme;
  position: number;
}) {
  const diff = DIFF_META[mission.difficulty] || DIFF_META.easy;
  const typeIcon = TYPE_ICONS[mission.type] || "⚡";

  // Duolingo-style snake path: nodes sway left/right
  const amplitude = 80;
  const xOffset = Math.sin(position * 0.8) * amplitude;

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 + index * 0.08, type: "spring", stiffness: 150, damping: 20 }}
      className="relative flex flex-col items-center"
      style={{ transform: `translateX(${xOffset}px)` }}
    >
      {/* Active node glow ring */}
      {isActive && (
        <motion.div
          className="absolute inset-0 flex items-start justify-center"
          animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div
            className="w-[88px] h-[88px] rounded-full"
            style={{ background: `radial-gradient(circle, ${theme.accentFrom}30, transparent 70%)` }}
          />
        </motion.div>
      )}

      {/* Node button */}
      <motion.button
        onClick={isUnlocked ? onClick : undefined}
        disabled={!isUnlocked}
        whileHover={isUnlocked && !isDone ? { scale: 1.15, y: -4 } : {}}
        whileTap={isUnlocked ? { scale: 0.92 } : {}}
        className={`relative w-[76px] h-[76px] rounded-full flex items-center justify-center
                    transition-shadow duration-300 ${
          isDone
            ? "shadow-lg cursor-default"
            : isActive
            ? "shadow-xl cursor-pointer"
            : isUnlocked
            ? "shadow-md cursor-pointer hover:shadow-xl"
            : "cursor-not-allowed"
        }`}
        style={
          isDone
            ? { background: `linear-gradient(135deg, ${theme.accentFrom}, ${theme.accentTo})` }
            : isActive
            ? { background: `linear-gradient(135deg, ${theme.accentFrom}, ${theme.accentTo})`, boxShadow: `0 0 24px ${theme.accentFrom}50` }
            : isUnlocked
            ? { background: "white", border: `3px solid ${theme.accentFrom}60` }
            : { background: "#F3F4F6", border: "3px solid #E5E7EB" }
        }
      >
        {/* Inner content */}
        {isDone ? (
          <motion.div
            initial={{ rotate: -30, scale: 0 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <span className="text-3xl drop-shadow-md">⭐</span>
          </motion.div>
        ) : isActive ? (
          <motion.div
            animate={{ scale: [1, 1.15, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            <span className="text-3xl drop-shadow-md">{typeIcon}</span>
          </motion.div>
        ) : isUnlocked ? (
          <span className="text-2xl">{typeIcon}</span>
        ) : (
          <span className="text-2xl grayscale opacity-40">🔒</span>
        )}

        {/* Sparkle on done nodes */}
        {isDone && (
          <motion.div
            className="absolute -top-1 -right-1"
            animate={{ rotate: [0, 20, -20, 0], scale: [1, 1.2, 1] }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            <span className="text-sm">✨</span>
          </motion.div>
        )}
      </motion.button>

      {/* Star rating */}
      <div className="flex gap-0.5 mt-2.5">
        {Array.from({ length: diff.stars }).map((_, i) => (
          <motion.span
            key={i}
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.3 + index * 0.08 + i * 0.1, type: "spring" }}
            className="text-base"
            style={{ color: isDone ? "#FBBF24" : isUnlocked ? `${diff.color}80` : "#D1D5DB" }}
          >
            {isDone ? "★" : "☆"}
          </motion.span>
        ))}
      </div>

      {/* Title */}
      <p className={`text-[11px] font-bold mt-1 max-w-[110px] text-center leading-snug ${
        isDone ? "text-prism-text-secondary" : isUnlocked ? "text-prism-text" : "text-gray-300"
      }`}>
        {mission.title}
      </p>

      {/* XP earned badge */}
      {isDone && mission.xp_earned != null && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", delay: 0.4 + index * 0.08 }}
          className="mt-1 px-2 py-0.5 rounded-full text-[10px] font-extrabold"
          style={{ backgroundColor: `${theme.accentFrom}15`, color: theme.accentFrom }}
        >
          +{mission.xp_earned} XP
        </motion.div>
      )}
    </motion.div>
  );
}

/* ─── Connector path between nodes ─── */

function PathConnector({ from, to, theme, done }: { from: number; to: number; theme: WorldTheme; done: boolean }) {
  return (
    <div className="flex justify-center py-1">
      <motion.div
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ delay: 0.1 + from * 0.08 }}
        className="w-1 h-10 rounded-full origin-top"
        style={{
          backgroundColor: done ? theme.accentFrom : `${theme.accentFrom}25`,
          filter: done ? theme.pathGlow : "none",
        }}
      />
    </div>
  );
}

/* ─── Main page ─── */

export default function WorldMissionsPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [world, setWorld] = useState<World | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!worldId) return;
    setLoading(true);
    worldsApi
      .list()
      .then((r) => {
        const w = r.data.find((w: World) => w.id === worldId);
        if (w) setWorld(w);
      })
      .catch(() => {});
    worldsApi
      .missions(worldId)
      .then((r) => setMissions(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [worldId, user?.id]);

  const theme = THEMES[world?.slug || ""] || DEFAULT_THEME;

  // Sort: easy → medium → hard
  const sorted = useMemo(
    () => [...missions].sort((a, b) => (DIFF_ORDER[a.difficulty] ?? 0) - (DIFF_ORDER[b.difficulty] ?? 0)),
    [missions]
  );

  const getUnlockState = (index: number) => {
    if (index === 0) return true;
    return sorted.slice(0, index).every((m) => m.completed);
  };

  const activeIndex = sorted.findIndex((m, i) => !m.completed && getUnlockState(i));
  const completedCount = sorted.filter((m) => m.completed).length;
  const allDone = sorted.length > 0 && completedCount === sorted.length;

  // Determine tier boundaries
  const tiers = useMemo(() => {
    const result: { difficulty: string; startIndex: number }[] = [];
    let lastDiff = "";
    sorted.forEach((m, i) => {
      if (m.difficulty !== lastDiff) {
        result.push({ difficulty: m.difficulty, startIndex: i });
        lastDiff = m.difficulty;
      }
    });
    return result;
  }, [sorted]);

  // Build mascot message
  const mascotMessage = allDone
    ? "You did it! All quests complete! 🎉"
    : activeIndex === 0
    ? "Let's start this adventure! Tap the glowing quest!"
    : `${completedCount} down, ${sorted.length - completedCount} to go! Keep it up!`;

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Background scenery gradient */}
      <div className={`absolute inset-0 bg-gradient-to-b ${theme.sceneryGradient} pointer-events-none`} />
      <FloatingDecor items={theme.decorations} />

      <div className="relative max-w-md mx-auto px-4 pt-8 pb-20">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Link
            href="/worlds"
            className="text-sm font-semibold text-prism-violet hover:text-prism-magenta transition-colors mb-5 inline-flex items-center gap-1"
          >
            ← Back to Worlds
          </Link>

          {/* World title card */}
          <div className="card p-5 mb-5 relative overflow-hidden">
            <div
              className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-20 pointer-events-none"
              style={{ backgroundColor: theme.accentFrom }}
            />
            <div className="relative flex items-center gap-4">
              <motion.div
                animate={{ rotate: [0, -10, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-md"
                style={{ background: `linear-gradient(135deg, ${theme.accentFrom}20, ${theme.accentTo}20)` }}
              >
                {theme.emoji}
              </motion.div>
              <div className="flex-1">
                <h1 className="text-xl sm:text-2xl font-extrabold text-prism-text">
                  {world?.name || "Loading..."}
                </h1>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-bold text-prism-text-secondary">{sorted.length} quests</span>
                  <span className="text-prism-text-muted">•</span>
                  <span className="text-xs font-bold" style={{ color: theme.accentFrom }}>
                    {completedCount} done
                  </span>
                </div>
              </div>
            </div>

            {/* XP progress bar */}
            {!loading && sorted.length > 0 && (
              <div className="mt-4">
                <div className="flex justify-between text-[10px] font-bold mb-1.5 uppercase tracking-wider">
                  <span className="text-prism-text-muted">Progress</span>
                  <span style={{ color: theme.accentFrom }}>
                    {Math.round((completedCount / sorted.length) * 100)}%
                  </span>
                </div>
                <div className="h-3 bg-prism-surface-alt rounded-full overflow-hidden border border-prism-border/50">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(completedCount / sorted.length) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: `linear-gradient(90deg, ${theme.accentFrom}, ${theme.accentTo})` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Mascot with speech bubble */}
          {!loading && sorted.length > 0 && (
            <div className="mb-6">
              <Mascot emoji={theme.mascot} name={theme.mascotName} message={mascotMessage} />
            </div>
          )}
        </motion.div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center gap-8 py-8">
            {[...Array(4)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                className="w-[76px] h-[76px] rounded-full bg-prism-surface-alt"
              />
            ))}
          </div>
        ) : sorted.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-12 text-center"
          >
            <div className="text-5xl mb-3">🏗️</div>
            <p className="text-prism-text-secondary font-semibold">
              New quests coming soon! Check back later.
            </p>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center">
            {sorted.map((m, i) => {
              const isDone = m.completed === true;
              const isUnlocked = getUnlockState(i);
              const isActive = i === activeIndex;

              // Check if we need a tier banner
              const tier = tiers.find((t) => t.startIndex === i);
              const tierMeta = tier ? DIFF_META[tier.difficulty] : null;

              return (
                <div key={m.id} className="w-full">
                  {/* Tier separator */}
                  {tierMeta && (
                    <TierBanner
                      tierName={tierMeta.tierName}
                      tierEmoji={tierMeta.tierEmoji}
                      color={tierMeta.color}
                      index={i}
                    />
                  )}

                  {/* Path connector (not before first node) */}
                  {i > 0 && (
                    <PathConnector
                      from={i - 1}
                      to={i}
                      theme={theme}
                      done={sorted[i - 1]?.completed === true}
                    />
                  )}

                  {/* Quest node */}
                  <QuestNode
                    mission={m}
                    index={i}
                    isUnlocked={isUnlocked}
                    isActive={isActive}
                    isDone={isDone}
                    onClick={() => router.push(`/missions/${m.id}`)}
                    theme={theme}
                    position={i}
                  />
                </div>
              );
            })}

            {/* Path to trophy */}
            <PathConnector
              from={sorted.length - 1}
              to={sorted.length}
              theme={theme}
              done={allDone}
            />

            {/* Trophy / finish node */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 + sorted.length * 0.08, type: "spring" }}
              className="flex flex-col items-center pb-8"
            >
              <motion.div
                whileHover={allDone ? { scale: 1.1, rotate: [0, -5, 5, 0] } : {}}
                className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl
                            transition-all duration-500 ${
                  allDone
                    ? "shadow-xl"
                    : "opacity-30 grayscale"
                }`}
                style={
                  allDone
                    ? {
                        background: `linear-gradient(135deg, #FBBF24, #F59E0B)`,
                        boxShadow: "0 0 30px rgba(251, 191, 36, 0.4)",
                      }
                    : { background: "#F3F4F6", border: "3px solid #E5E7EB" }
                }
              >
                🏆
              </motion.div>

              {allDone ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="text-center mt-3"
                >
                  <p className="text-sm font-extrabold text-amber-500">World Complete!</p>
                  <p className="text-xs text-prism-text-secondary mt-1">
                    You&apos;ve mastered all quests!
                  </p>
                  {/* Celebration mascot */}
                  <motion.div
                    className="mt-3 text-4xl"
                    animate={{ y: [0, -10, 0], rotate: [0, -10, 10, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    {theme.mascot}
                  </motion.div>
                </motion.div>
              ) : (
                <p className="text-xs text-gray-300 font-bold mt-2">
                  Complete all quests
                </p>
              )}
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
