"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { cardApi, spectrumApi, type PrismCardData, type SpectrumData } from "@/lib/api";
import PrismCard from "@/components/PrismCard";
import SpectrumBar from "@/components/SpectrumBar";
import LoginModal from "@/components/LoginModal";

const LEVEL_NAMES = ["", "Spark", "Ray", "Beam", "Spectrum", "Master"];

const DIM_LABELS: Record<string, { label: string; low: string; high: string }> = {
  analytical_creative: { label: "Thinking Style", low: "Analytical", high: "Creative" },
  builder_explorer: { label: "Action Mode", low: "Builder", high: "Explorer" },
  leader_specialist: { label: "Role Preference", low: "Leader", high: "Specialist" },
  entrepreneur_steward: { label: "Risk Style", low: "Entrepreneur", high: "Steward" },
  people_systems: { label: "Focus Area", low: "People", high: "Systems" },
};

export default function ProfilePage() {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const authLoading = useAuth((s) => s.loading);
  const [spectrum, setSpectrum] = useState<SpectrumData | null>(null);
  const [card, setCard] = useState<PrismCardData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [spectrumError, setSpectrumError] = useState(false);

  useEffect(() => {
    if (authLoading || !user) return;
    spectrumApi.get()
      .then((r) => setSpectrum(r.data))
      .catch(() => setSpectrumError(true));
    cardApi.mine()
      .then((r) => { if (r.data.length > 0) setCard(r.data[0]); })
      .catch(() => {});
  }, [user, authLoading]);

  const handleGenerateCard = async () => {
    setGenerating(true);
    try {
      const res = await cardApi.generate();
      const cards = await cardApi.mine();
      if (cards.data.length > 0) setCard(cards.data[0]);
    } catch {
      // handle error silently
    } finally {
      setGenerating(false);
    }
  };

  const shareUrl = card
    ? `${typeof window !== "undefined" ? window.location.origin : ""}/card/${card.share_token}`
    : "";

  const shareText = card
    ? `I'm ${(card.card_data as Record<string, unknown>)?.archetype || "discovering my identity"} on Prism! Check out my identity card:`
    : "";

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShareWhatsApp = () => {
    window.open(`https://wa.me/?text=${encodeURIComponent(shareText + " " + shareUrl)}`, "_blank");
  };

  const handleShareTwitter = () => {
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`, "_blank");
  };

  if (authLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card p-8 h-48 animate-pulse bg-prism-surface-alt" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto px-4 py-20">
        <div className="card p-8 text-center">
          <div className="text-5xl mb-4">🔮</div>
          <p className="text-xl font-bold text-prism-text mb-2">Sign in to see your profile</p>
          <p className="text-prism-text-secondary mb-6">
            Complete quests to discover your archetype and get your Prism Card!
          </p>
          <button onClick={() => setShowLogin(true)} className="btn-primary px-8">
            Sign In
          </button>
        </div>
        <LoginModal open={showLogin} onClose={() => setShowLogin(false)} />
      </div>
    );
  }

  const levelName = LEVEL_NAMES[user.level] || `Lv ${user.level}`;

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Profile header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6 mb-6"
      >
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-prism-gradient flex items-center justify-center text-3xl shadow-glow">
            {user.current_archetype_label ? "🏆" : "🌱"}
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-extrabold text-prism-text">{user.name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className="badge-level">{levelName}</span>
              <span className="badge-xp">⭐ {user.xp_points} XP</span>
              {user.current_archetype_label && (
                <span className="badge bg-violet-50 text-prism-violet border border-violet-200">
                  {user.current_archetype_label}
                </span>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: Spectrum */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          {spectrumError ? (
            <div className="card p-8 text-center">
              <div className="text-4xl mb-3">🗺️</div>
              <p className="font-bold text-prism-text mb-2">No spectrum yet</p>
              <p className="text-sm text-prism-text-secondary mb-4">
                Complete missions in any world to start building your identity spectrum.
              </p>
              <button onClick={() => router.push("/worlds")} className="btn-primary px-6">
                Start Exploring
              </button>
            </div>
          ) : spectrum ? (
            <div className="card p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-extrabold text-prism-text">Your Spectrum</h2>
                <span className="badge bg-prism-surface-alt text-prism-text-secondary border border-prism-border">
                  {spectrum.total_signals} signals
                </span>
              </div>

              {/* Archetype */}
              {spectrum.primary_archetype && (
                <div className="bg-prism-gradient-soft rounded-2xl p-4 border border-prism-border/50">
                  <p className="text-sm font-bold text-prism-text">
                    {spectrum.primary_archetype.emoji_icon} {spectrum.primary_archetype.label}
                  </p>
                  {spectrum.primary_archetype.description && (
                    <p className="text-xs text-prism-text-secondary mt-1 leading-relaxed">
                      {spectrum.primary_archetype.description}
                    </p>
                  )}
                </div>
              )}

              {/* Color spectrum bar */}
              {spectrum.color_ratios && (
                <SpectrumBar spectrum={spectrum.color_ratios} showLabels height="h-5" />
              )}

              {/* Dimension bars */}
              <div className="space-y-3">
                {Object.entries(DIM_LABELS).map(([key, meta]) => {
                  const val = (spectrum as unknown as Record<string, number>)[key] || 0;
                  const pct = ((val + 1) / 2) * 100; // -1..1 -> 0..100
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-semibold text-prism-text-secondary">{meta.low}</span>
                        <span className="text-prism-text-muted">{meta.label}</span>
                        <span className="font-semibold text-prism-text-secondary">{meta.high}</span>
                      </div>
                      <div className="h-2.5 bg-prism-surface-alt rounded-full border border-prism-border/50 relative">
                        <motion.div
                          initial={{ left: "50%" }}
                          animate={{ left: `${pct}%` }}
                          transition={{ duration: 0.8 }}
                          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-prism-violet border-2 border-white shadow-md"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="card p-8 h-64 animate-pulse bg-prism-surface-alt" />
          )}
        </motion.div>

        {/* Right: Card + Share */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-5"
        >
          {card ? (
            <>
              <PrismCard card={card} />

              {/* Share buttons */}
              <div className="card p-5 space-y-4">
                <h3 className="text-sm font-extrabold text-prism-text uppercase tracking-wider">
                  Share your identity
                </h3>

                <div className="grid grid-cols-3 gap-3">
                  {/* WhatsApp */}
                  <button
                    onClick={handleShareWhatsApp}
                    className="flex flex-col items-center gap-2 p-3 rounded-2xl bg-emerald-50 border-2 border-emerald-200
                               hover:bg-emerald-100 transition-colors active:scale-95"
                  >
                    <span className="text-2xl">💬</span>
                    <span className="text-xs font-bold text-emerald-700">WhatsApp</span>
                  </button>

                  {/* Twitter/X */}
                  <button
                    onClick={handleShareTwitter}
                    className="flex flex-col items-center gap-2 p-3 rounded-2xl bg-sky-50 border-2 border-sky-200
                               hover:bg-sky-100 transition-colors active:scale-95"
                  >
                    <span className="text-2xl">𝕏</span>
                    <span className="text-xs font-bold text-sky-700">Twitter</span>
                  </button>

                  {/* Copy Link */}
                  <button
                    onClick={handleCopyLink}
                    className="flex flex-col items-center gap-2 p-3 rounded-2xl bg-violet-50 border-2 border-violet-200
                               hover:bg-violet-100 transition-colors active:scale-95"
                  >
                    <span className="text-2xl">{copied ? "✅" : "🔗"}</span>
                    <span className="text-xs font-bold text-violet-700">
                      {copied ? "Copied!" : "Copy Link"}
                    </span>
                  </button>
                </div>

                {/* Direct link */}
                <div className="flex items-center gap-2 bg-prism-surface-alt rounded-xl p-2.5 border border-prism-border">
                  <input
                    type="text"
                    readOnly
                    value={shareUrl}
                    className="flex-1 bg-transparent text-xs text-prism-text-secondary truncate outline-none"
                  />
                  <button
                    onClick={handleCopyLink}
                    className="text-xs font-bold text-prism-violet px-3 py-1 rounded-lg hover:bg-prism-violet/10 transition-colors shrink-0"
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              </div>
            </>
          ) : spectrumError ? null : (
            <div className="card p-8 text-center">
              <div className="text-5xl mb-4">🃏</div>
              <h3 className="text-lg font-extrabold text-prism-text mb-2">
                Generate your Prism Card
              </h3>
              <p className="text-sm text-prism-text-secondary mb-6">
                Create a shareable card showing your archetype and unique spectrum.
                Share it with friends on social media!
              </p>
              <button
                onClick={handleGenerateCard}
                disabled={generating || spectrumError}
                className="btn-primary px-8 disabled:opacity-40"
              >
                {generating ? "Generating..." : "Generate Card 🎨"}
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
