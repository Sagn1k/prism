"use client";

import { motion } from "framer-motion";
import SpectrumBar from "./SpectrumBar";
import type { PrismCardData } from "@/lib/api";

const LEVEL_NAMES = ["", "Spark", "Ray", "Beam", "Spectrum", "Master"];

interface Props {
  card: PrismCardData;
}

export default function PrismCard({ card }: Props) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = card.card_data as any;
  const name: string = data?.name || "Unknown";
  const level: number = data?.level || 1;
  const xp: number = data?.xp_points || 0;
  const archLabel: string = data?.primary_archetype?.label || data?.archetype || "Undiscovered";
  const archEmoji: string = data?.primary_archetype?.emoji_icon || "🔮";
  const archDesc: string = data?.primary_archetype?.description || "";
  const colorRatios: Record<string, number> = data?.color_ratios || {};
  const confidence: number = data?.confidence || 0;
  const totalSignals: number = data?.total_signals || 0;
  const levelName = LEVEL_NAMES[level] || `Lv ${level}`;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="relative w-full max-w-sm mx-auto"
    >
      <div className="bg-white rounded-3xl p-6 space-y-5 relative overflow-hidden border-2 border-prism-border shadow-card-hover">
        {/* Soft gradient background */}
        <div className="absolute -top-16 -right-16 w-48 h-48 bg-violet-100/60 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-pink-100/60 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="relative flex items-center justify-between">
          <div>
            <p className="text-[10px] text-prism-text-muted uppercase tracking-[0.2em] font-bold">
              Prism Card
            </p>
            <h2 className="text-2xl font-extrabold text-prism-text mt-0.5">{name}</h2>
          </div>
          <div className="flex items-center gap-1.5 bg-prism-surface-alt px-3 py-1.5 rounded-full border border-prism-border">
            <span className="text-sm">⭐</span>
            <span className="text-prism-violet font-bold text-xs">{levelName}</span>
            <span className="text-prism-text-muted text-[10px]">({xp} XP)</span>
          </div>
        </div>

        {/* Archetype */}
        <div className="relative bg-prism-gradient-soft rounded-2xl p-4 border border-prism-border/50">
          <p className="text-[10px] text-prism-text-muted uppercase tracking-[0.15em] font-bold mb-1">
            Archetype
          </p>
          <p className="text-xl font-extrabold text-gradient">
            {archEmoji} {archLabel}
          </p>
          {archDesc && (
            <p className="text-xs text-prism-text-secondary mt-1.5 leading-relaxed line-clamp-2">
              {archDesc}
            </p>
          )}
        </div>

        {/* Spectrum */}
        {Object.keys(colorRatios).length > 0 && (
          <div className="relative">
            <p className="text-[10px] text-prism-text-muted uppercase tracking-[0.15em] font-bold mb-2">
              Spectrum
            </p>
            <SpectrumBar spectrum={colorRatios} showLabels height="h-5" />
          </div>
        )}

        {/* Stats */}
        <div className="relative flex items-center gap-4">
          <div className="flex-1 bg-prism-surface-alt rounded-xl p-2.5 text-center border border-prism-border/50">
            <p className="text-lg font-extrabold text-prism-violet">{Math.round(confidence * 100)}%</p>
            <p className="text-[10px] text-prism-text-muted font-bold uppercase">Confidence</p>
          </div>
          <div className="flex-1 bg-prism-surface-alt rounded-xl p-2.5 text-center border border-prism-border/50">
            <p className="text-lg font-extrabold text-prism-cyan">{totalSignals}</p>
            <p className="text-[10px] text-prism-text-muted font-bold uppercase">Signals</p>
          </div>
        </div>

        {/* Footer */}
        <div className="relative pt-3 border-t-2 border-prism-border/50 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-prism-gradient" />
            <span className="text-[10px] text-prism-text-muted tracking-widest uppercase font-bold">
              prism
            </span>
          </div>
          <span className="text-[10px] text-prism-text-muted font-mono">
            #{card.share_token.slice(0, 8)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
