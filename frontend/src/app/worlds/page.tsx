"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, animate, PanInfo } from "framer-motion";
import { useRouter } from "next/navigation";
import { worldsApi, type World } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

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

const WORLD_META: Record<string, { emoji: string; bg: string; border: string; gradient: string }> = {
  "space-lab":      { emoji: "🔬", bg: "bg-cyan-50",   border: "border-cyan-200",   gradient: "from-cyan-400 to-cyan-600" },
  "creator-studio": { emoji: "🎨", bg: "bg-pink-50",   border: "border-pink-200",   gradient: "from-pink-400 to-fuchsia-600" },
  "code-dungeon":   { emoji: "💻", bg: "bg-violet-50", border: "border-violet-200", gradient: "from-violet-400 to-violet-600" },
  "market-arena":   { emoji: "🚀", bg: "bg-amber-50",  border: "border-amber-200",  gradient: "from-amber-400 to-orange-600" },
};

const SWIPE_THRESHOLD = 120;

function SwipeableCard({
  world,
  onSwipe,
  isTop,
}: {
  world: World;
  onSwipe: (direction: "left" | "right") => void;
  isTop: boolean;
}) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-300, 0, 300], [-18, 0, 18]);
  const leftOpacity = useTransform(x, [-150, -40, 0], [1, 0.5, 0]);
  const rightOpacity = useTransform(x, [0, 40, 150], [0, 0.5, 1]);
  const meta = WORLD_META[world.slug] || {
    emoji: "🌍", bg: "bg-gray-50", border: "border-gray-200", gradient: "from-gray-400 to-gray-600",
  };
  const pct = world.user_progress != null ? Math.round(world.user_progress * 100) : 0;
  const completed = world.user_progress != null ? Math.round(world.user_progress * world.mission_count) : 0;

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (info.offset.x > SWIPE_THRESHOLD) {
      animate(x, 500, { duration: 0.3 });
      setTimeout(() => onSwipe("right"), 250);
    } else if (info.offset.x < -SWIPE_THRESHOLD) {
      animate(x, -500, { duration: 0.3 });
      setTimeout(() => onSwipe("left"), 250);
    } else {
      animate(x, 0, { type: "spring", stiffness: 500, damping: 30 });
    }
  };

  return (
    <motion.div
      className="absolute inset-0 touch-none"
      style={{ x, rotate, zIndex: isTop ? 10 : 1 }}
      drag={isTop ? "x" : false}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.9}
      onDragEnd={handleDragEnd}
      initial={{ scale: isTop ? 1 : 0.92, y: isTop ? 0 : 24, opacity: 1 }}
      animate={{ scale: isTop ? 1 : 0.92, y: isTop ? 0 : 24, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      <div
        className={`relative w-full h-full rounded-3xl border-2 ${meta.border} overflow-hidden
                     shadow-xl ${isTop ? "cursor-grab active:cursor-grabbing" : ""}`}
        style={{ backgroundColor: "#FFFFFF" }}
      >
        {/* Swipe indicators */}
        {isTop && (
          <>
            <motion.div
              className="absolute top-8 left-6 z-20 px-5 py-2.5 rounded-2xl bg-red-500 text-white
                         font-extrabold text-lg -rotate-12 border-4 border-red-300 shadow-lg"
              style={{ opacity: leftOpacity }}
            >
              SKIP
            </motion.div>
            <motion.div
              className="absolute top-8 right-6 z-20 px-5 py-2.5 rounded-2xl bg-emerald-500 text-white
                         font-extrabold text-lg rotate-12 border-4 border-emerald-300 shadow-lg"
              style={{ opacity: rightOpacity }}
            >
              INTERESTED
            </motion.div>
          </>
        )}

        {/* Top gradient accent */}
        <div className={`h-2 w-full bg-gradient-to-r ${meta.gradient}`} />

        {/* Content */}
        <div className="flex flex-col items-center justify-center h-full px-8 pb-8 pt-4">
          {/* Emoji */}
          <div
            className="w-24 h-24 rounded-3xl flex items-center justify-center text-6xl mb-6 shadow-md"
            style={{ backgroundColor: `${world.color_hex}20` }}
          >
            {meta.emoji}
          </div>

          {/* Title */}
          <h2 className="text-3xl font-extrabold text-prism-text text-center mb-3">
            {world.name}
          </h2>

          {/* Description */}
          <p className="text-base text-prism-text-secondary text-center leading-relaxed max-w-sm mb-8">
            {world.description}
          </p>

          {/* Stats */}
          <div className="w-full max-w-xs space-y-4">
            <div className="flex items-center justify-between text-sm font-bold">
              <span className="text-prism-text-secondary">
                {completed}/{world.mission_count} quests
              </span>
              <span style={{ color: world.color_hex }}>{pct}%</span>
            </div>
            <div className="progress-bar">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="progress-fill"
                style={{ backgroundColor: world.color_hex }}
              />
            </div>
            <div className="flex justify-center">
              <span className="badge bg-white/80 text-prism-text-secondary border border-prism-border">
                {world.mission_count} missions
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function WorldsPage() {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const [worlds, setWorlds] = useState<World[]>(FALLBACK_WORLDS);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipedWorlds, setSwipedWorlds] = useState<{ world: World; direction: "left" | "right" }[]>([]);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    // Reset swipe state when user changes
    setCurrentIndex(0);
    setSwipedWorlds([]);
    setFinished(false);
    worldsApi
      .list()
      .then((r) => setWorlds(r.data))
      .catch(() => {});
  }, [user?.id]);

  const handleSwipe = useCallback(
    (direction: "left" | "right") => {
      const world = worlds[currentIndex];
      if (!world) return;

      // Fire-and-forget swipe signal to backend (ignore auth errors silently)
      const token = typeof window !== "undefined" ? localStorage.getItem("prism_token") : null;
      if (token) {
        worldsApi.swipe(world.id, direction).catch(() => {});
      }

      // Right swipe → navigate directly to that world's quests
      if (direction === "right") {
        router.push(`/worlds/${world.id}`);
        return;
      }

      // Left swipe → advance to next card
      const nextIndex = currentIndex + 1;
      if (nextIndex >= worlds.length) {
        setFinished(true);
      } else {
        setCurrentIndex(nextIndex);
      }
    },
    [currentIndex, worlds, router]
  );

  if (finished) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          <div className="text-6xl mb-6">🤔</div>
          <h2 className="text-2xl font-extrabold text-prism-text mb-3">
            No worlds selected
          </h2>
          <p className="text-prism-text-secondary mb-8">
            Swipe right on a world that interests you to explore its quests!
          </p>
          <button
            onClick={() => {
              setCurrentIndex(0);
              setFinished(false);
            }}
            className="btn-secondary"
          >
            Swipe Again
          </button>
        </motion.div>
      </div>
    );
  }

  const topWorld = worlds[currentIndex];
  const nextWorld = worlds[currentIndex + 1];

  return (
    <div className="max-w-md mx-auto px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="text-5xl mb-3">🗺️</div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-prism-text">
          Explore <span className="text-gradient">Worlds</span>
        </h1>
        <p className="text-prism-text-secondary mt-2">
          Swipe right if interested, left to skip
        </p>
      </motion.div>

      {/* Card counter */}
      <div className="flex justify-center gap-2 mb-6">
        {worlds.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i < currentIndex
                ? "w-6 bg-prism-violet"
                : i === currentIndex
                ? "w-8 bg-prism-violet"
                : "w-6 bg-prism-border"
            }`}
          />
        ))}
      </div>

      {/* Card stack */}
      <div className="relative w-full" style={{ height: 480 }}>
        {nextWorld && (
          <SwipeableCard
            key={nextWorld.id}
            world={nextWorld}
            onSwipe={() => {}}
            isTop={false}
          />
        )}
        {topWorld && (
          <SwipeableCard
            key={topWorld.id}
            world={topWorld}
            onSwipe={handleSwipe}
            isTop={true}
          />
        )}
      </div>

      {/* Manual buttons */}
      <div className="flex justify-center gap-6 mt-8">
        <button
          onClick={() => handleSwipe("left")}
          className="w-16 h-16 rounded-full bg-red-50 border-2 border-red-200
                     flex items-center justify-center text-2xl
                     hover:bg-red-100 hover:scale-110 active:scale-95 transition-all"
          aria-label="Skip"
        >
          ✕
        </button>
        <button
          onClick={() => handleSwipe("right")}
          className="w-16 h-16 rounded-full bg-emerald-50 border-2 border-emerald-200
                     flex items-center justify-center text-2xl
                     hover:bg-emerald-100 hover:scale-110 active:scale-95 transition-all"
          aria-label="Interested"
        >
          ♥
        </button>
      </div>
    </div>
  );
}
