"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { worldsApi, type Mission, type World } from "@/lib/api";
import MissionCard from "@/components/MissionCard";

const WORLD_EMOJI: Record<string, string> = {
  "space-lab": "🔬",
  "creator-studio": "🎨",
  "code-dungeon": "💻",
  "market-arena": "🚀",
};

export default function WorldMissionsPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const router = useRouter();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [world, setWorld] = useState<World | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!worldId) return;
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
  }, [worldId]);

  const emoji = world?.slug ? (WORLD_EMOJI[world.slug] || "🌍") : "🌍";

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Link
          href="/worlds"
          className="text-sm font-semibold text-prism-violet hover:text-prism-magenta transition-colors mb-6 inline-flex items-center gap-1"
        >
          ← Back to Worlds
        </Link>

        <div className="flex items-center gap-4 mb-2">
          <div className="w-14 h-14 rounded-2xl bg-prism-surface-alt flex items-center justify-center text-3xl shadow-sm border border-prism-border">
            {emoji}
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-prism-text">
              {world?.name || "Loading..."} Quests
            </h1>
            <p className="text-prism-text-secondary text-sm mt-0.5">
              Complete quests to earn XP and shift your spectrum
            </p>
          </div>
        </div>

        {/* Mission count badge */}
        {!loading && missions.length > 0 && (
          <div className="mt-4 mb-6 flex items-center gap-3">
            <span className="badge bg-prism-surface-alt text-prism-text-secondary border border-prism-border">
              {missions.length} quests available
            </span>
          </div>
        )}
      </motion.div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card p-5 h-20 animate-pulse bg-prism-surface-alt" />
          ))}
        </div>
      ) : missions.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-5xl mb-3">🏗️</div>
          <p className="text-prism-text-secondary font-semibold">
            New quests coming soon! Check back later.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {missions.map((m, i) => (
            <MissionCard key={m.id} mission={m} index={i} onClick={() => router.push(`/missions/${m.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}
