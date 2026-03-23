"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { AnimatePresence } from "framer-motion";
import { worldsApi, cardApi, type Mission, type MissionResult, type PrismCardData } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import LoginModal from "@/components/LoginModal";
import PrismCard from "@/components/PrismCard";

const TYPE_META: Record<string, { icon: string; label: string }> = {
  flash: { icon: "⚡", label: "Quick Fire" },
  scenario_sim: { icon: "🎭", label: "Scenario" },
  build_quest: { icon: "🔨", label: "Build Quest" },
  ai_debate: { icon: "💬", label: "AI Debate" },
  this_or_that: { icon: "↔️", label: "This or That" },
};

export default function MissionPage() {
  const { missionId } = useParams<{ missionId: string }>();
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const authLoading = useAuth((s) => s.loading);
  const hydrate = useAuth((s) => s.hydrate);
  const [mission, setMission] = useState<Mission | null>(null);
  const [missionLoading, setMissionLoading] = useState(true);
  const [response, setResponse] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<MissionResult | null>(null);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [worldComplete, setWorldComplete] = useState(false);
  const [generatedCard, setGeneratedCard] = useState<PrismCardData | null>(null);
  const [showCardPopup, setShowCardPopup] = useState(false);

  // Timer
  useEffect(() => {
    if (result || !mission) return;
    const interval = setInterval(() => {
      setElapsed(Math.round((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [mission, result, startTime]);

  // Wait for auth, then start mission — only re-run if user identity changes, not on XP/level updates
  const userId = user?.id;
  useEffect(() => {
    if (authLoading || !missionId) return;
    if (!userId) {
      setMissionLoading(false);
      setShowLogin(true);
      return;
    }
    worldsApi
      .startMission(missionId)
      .then((r) => {
        const d = r.data;
        setMission({
          id: d.id,
          world_id: d.world_id,
          title: d.title,
          type: d.type,
          difficulty: d.difficulty,
          duration_seconds: d.duration_seconds,
          content_payload: d.content_payload,
        });
      })
      .catch((err) => {
        const detail = err.response?.data?.detail || "Failed to load mission.";
        if (err.response?.status === 409) {
          setError("already_completed");
        } else {
          setError(detail);
        }
      })
      .finally(() => setMissionLoading(false));
  }, [missionId, userId, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!missionId || submitting || !response.trim()) return;

    setSubmitting(true);
    try {
      const timeSpent = Math.round((Date.now() - startTime) / 1000);
      const res = await worldsApi.submitMission(missionId, {
        responses: { answer: response },
        time_spent: timeSpent,
      });
      setResult(res.data);
      hydrate();

      // Check if all missions in this world are now completed
      if (mission?.world_id) {
        try {
          const worldMissions = await worldsApi.missions(mission.world_id);
          const allDone = worldMissions.data.every((m: Mission) => m.completed || m.id === missionId);
          if (allDone) {
            setWorldComplete(true);
            // Auto-generate a fresh Prism Card
            try {
              await cardApi.generate();
              const cards = await cardApi.mine();
              if (cards.data.length > 0) {
                setGeneratedCard(cards.data[0]);
              }
            } catch {
              // Card generation failed silently — don't block the result screen
            }
          }
        } catch {
          // World check failed silently
        }
      }
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError(msg || "Failed to submit mission.");
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  // --- Loading ---
  if (authLoading || missionLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card p-8 space-y-4">
          <div className="h-6 w-48 bg-prism-surface-alt rounded-lg animate-pulse" />
          <div className="h-4 w-full bg-prism-surface-alt rounded-lg animate-pulse" />
          <div className="h-32 w-full bg-prism-surface-alt rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  // --- Not logged in ---
  if (!user) {
    return (
      <div className="max-w-md mx-auto px-4 py-20">
        <div className="card p-8 text-center">
          <div className="text-5xl mb-4">🔒</div>
          <p className="text-xl font-bold text-prism-text mb-2">Sign in to play</p>
          <p className="text-prism-text-secondary mb-6">
            Create a free account to start completing quests and earning XP!
          </p>
          <button onClick={() => setShowLogin(true)} className="btn-primary px-8">
            Sign In to Play
          </button>
        </div>
        <LoginModal open={showLogin} onClose={() => setShowLogin(false)} />
      </div>
    );
  }

  // --- Already completed ---
  if (error === "already_completed") {
    return (
      <div className="max-w-md mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card p-8 text-center"
        >
          <div className="text-5xl mb-4">✅</div>
          <p className="text-xl font-bold text-prism-text mb-2">Already completed!</p>
          <p className="text-prism-text-secondary mb-6">
            You&apos;ve already finished this quest. Try another one to keep earning XP!
          </p>
          <button onClick={() => router.back()} className="btn-primary px-8">
            Back to Quests 🗺️
          </button>
        </motion.div>
      </div>
    );
  }

  // --- Error ---
  if (error && !mission) {
    return (
      <div className="max-w-md mx-auto px-4 py-20">
        <div className="card p-8 text-center">
          <div className="text-5xl mb-4">😵</div>
          <p className="text-prism-red font-bold mb-2">Oops!</p>
          <p className="text-prism-text-secondary mb-6">{error}</p>
          <button onClick={() => router.back()} className="btn-secondary px-6">
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  // --- Result screen (gamified!) ---
  if (result) {
    const totalScore = Math.round(
      (result.accuracy_score * 40 + result.speed_score * 30 + result.creativity_score * 30)
    );
    const stars = totalScore >= 70 ? 3 : totalScore >= 40 ? 2 : 1;

    return (
      <div className="max-w-md mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="card p-8 text-center"
        >
          {/* Stars */}
          <div className="flex justify-center gap-2 mb-4">
            {[1, 2, 3].map((s) => (
              <motion.div
                key={s}
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.2 + s * 0.15, type: "spring", stiffness: 300 }}
                className="text-4xl"
              >
                {s <= stars ? "⭐" : "☆"}
              </motion.div>
            ))}
          </div>

          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="text-2xl font-extrabold text-prism-text mb-1"
          >
            Quest Complete!
          </motion.h1>
          <p className="text-prism-text-secondary text-sm mb-6">Great job, adventurer!</p>

          {/* XP earned - big highlight */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 1, type: "spring", stiffness: 200 }}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-amber-50 border-2 border-amber-200 mb-6"
          >
            <span className="text-2xl">⚡</span>
            <span className="text-2xl font-extrabold text-prism-amber">+{result.xp_earned} XP</span>
          </motion.div>

          {/* Score breakdown */}
          <div className="space-y-3 mb-6">
            {[
              { label: "Accuracy", score: result.accuracy_score, icon: "🎯", color: "bg-emerald-400" },
              { label: "Speed", score: result.speed_score, icon: "⏱️", color: "bg-cyan-400" },
              { label: "Creativity", score: result.creativity_score, icon: "💡", color: "bg-pink-400" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <span className="text-lg">{item.icon}</span>
                <span className="text-sm font-semibold text-prism-text-secondary w-20 text-left">{item.label}</span>
                <div className="flex-1 progress-bar">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.round(item.score * 100)}%` }}
                    transition={{ delay: 1.2, duration: 0.6 }}
                    className={`progress-fill ${item.color}`}
                  />
                </div>
                <span className="text-sm font-bold text-prism-text w-10 text-right">
                  {Math.round(item.score * 100)}%
                </span>
              </div>
            ))}
          </div>

          {/* Spectrum shifts */}
          {result.spectrum_update && Object.keys(result.spectrum_update).length > 0 && (
            <div className="border-t-2 border-prism-border pt-4 mb-6">
              <p className="text-xs font-bold text-prism-text-muted uppercase tracking-wider mb-3">Spectrum Shifts</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {Object.entries(result.spectrum_update).map(([dim, val]) => (
                  <span
                    key={dim}
                    className={`badge ${val > 0 ? "bg-emerald-50 text-emerald-600 border border-emerald-200" : "bg-red-50 text-red-600 border border-red-200"}`}
                  >
                    {dim.replace("_", " ")} {val > 0 ? "+" : ""}{val.toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* World complete celebration */}
          {worldComplete && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.5, type: "spring" }}
              className="border-t-2 border-prism-border pt-5 mb-6"
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <motion.span
                  animate={{ rotate: [0, -15, 15, 0], scale: [1, 1.2, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="text-3xl"
                >
                  🏆
                </motion.span>
              </div>
              <p className="text-lg font-extrabold text-gradient mb-1">World Complete!</p>
              <p className="text-xs text-prism-text-secondary mb-4">
                You&apos;ve conquered every quest! Your Prism Card has been updated.
              </p>
              {generatedCard && (
                <button
                  onClick={() => setShowCardPopup(true)}
                  className="btn-primary w-full mb-3"
                >
                  View Your Prism Card 🃏
                </button>
              )}
            </motion.div>
          )}

          <button onClick={() => router.back()} className={`w-full ${worldComplete ? "btn-secondary" : "btn-primary"}`}>
            {worldComplete ? "Back to Quests" : "Continue 🎮"}
          </button>
        </motion.div>

        {/* Prism Card popup */}
        <AnimatePresence>
          {showCardPopup && generatedCard && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
              onClick={() => setShowCardPopup(false)}
            >
              <motion.div
                initial={{ scale: 0.7, y: 40 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.7, y: 40 }}
                transition={{ type: "spring", stiffness: 250, damping: 22 }}
                className="relative max-w-sm w-full"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Floating celebration emojis */}
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex gap-3">
                  {["🎉", "⭐", "🎉"].map((e, i) => (
                    <motion.span
                      key={i}
                      className="text-2xl"
                      animate={{ y: [0, -10, 0], rotate: [0, i % 2 === 0 ? 15 : -15, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                    >
                      {e}
                    </motion.span>
                  ))}
                </div>

                <PrismCard card={generatedCard} />

                <div className="flex gap-3 mt-5">
                  <button
                    onClick={() => router.push("/profile")}
                    className="btn-primary flex-1"
                  >
                    My Profile
                  </button>
                  <button
                    onClick={() => setShowCardPopup(false)}
                    className="btn-secondary flex-1"
                  >
                    Close
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // --- Active mission ---
  const meta = TYPE_META[mission?.type || ""] || TYPE_META.flash;
  const maxTime = mission?.duration_seconds || 300;
  const timeRemaining = Math.max(0, maxTime - elapsed);
  const timeWarning = timeRemaining < 30;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header bar */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="#"
            onClick={(e) => { e.preventDefault(); router.back(); }}
            className="text-sm font-semibold text-prism-violet hover:text-prism-magenta transition-colors inline-flex items-center gap-1"
          >
            ← Back
          </Link>

          {/* Timer */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full font-mono text-sm font-bold
                          ${timeWarning ? "bg-red-50 text-prism-red border-2 border-red-200 animate-pulse" : "bg-prism-surface-alt text-prism-text-secondary border-2 border-prism-border"}`}>
            <span>⏱️</span>
            <span>{formatTime(timeRemaining)}</span>
          </div>
        </div>

        {/* Quest card */}
        <div className="card p-6 mb-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-prism-surface-alt flex items-center justify-center text-xl">
              {meta.icon}
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-prism-text">{mission?.title}</h1>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`badge-${mission?.difficulty || "easy"}`}>{mission?.difficulty}</span>
                <span className="text-xs text-prism-text-muted font-medium">{meta.label}</span>
              </div>
            </div>
          </div>

          {/* Mission content */}
          {mission?.content_payload && (() => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const cp = mission.content_payload as any;
            const mainText: string = cp.instructions || cp.prompt || cp.scenario || "";
            return (
              <div className="bg-prism-surface-alt rounded-xl p-5 text-sm leading-relaxed space-y-4">
                {mainText && (
                  <p className="text-prism-text font-medium">{mainText}</p>
                )}

                {cp.description && (
                  <p className="text-prism-text-secondary">{String(cp.description)}</p>
                )}

                {cp.question && (
                  <p className="font-bold text-prism-text">{String(cp.question)}</p>
                )}

                {Array.isArray(cp.options) && (
                  <ul className="space-y-2">
                    {cp.options.map((opt: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-prism-text-secondary">
                        <span className="w-6 h-6 rounded-lg bg-prism-violet/10 text-prism-violet text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {String.fromCharCode(65 + i)}
                        </span>
                        {String(opt)}
                      </li>
                    ))}
                  </ul>
                )}

                {Array.isArray(cp.items) && (
                  <div>
                    <p className="text-xs font-bold text-prism-text-muted uppercase tracking-wider mb-2">Samples</p>
                    <div className="grid grid-cols-2 gap-2">
                      {cp.items.map((item: Record<string, unknown>, i: number) => (
                        <div key={i} className="bg-white rounded-lg p-2.5 border border-prism-border text-xs">
                          <span className="font-bold text-prism-violet">#{String(item.id || i + 1)}</span>
                          {Object.entries(item).filter(([k]) => k !== "id").map(([k, v]) => (
                            <span key={k} className="text-prism-text-secondary ml-2">
                              {k}: <span className="font-semibold text-prism-text">{String(v)}</span>
                            </span>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {Array.isArray(cp.categories) && (
                  <div>
                    <p className="text-xs font-bold text-prism-text-muted uppercase tracking-wider mb-2">Categories</p>
                    <div className="flex flex-wrap gap-2">
                      {cp.categories.map((cat: string, i: number) => (
                        <span key={i} className="badge bg-white text-prism-text border border-prism-border">
                          {cat}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {Array.isArray(cp.decisions) && (
                  <div className="space-y-3">
                    <p className="text-xs font-bold text-prism-text-muted uppercase tracking-wider">Decisions to make</p>
                    {cp.decisions.map((d: { question: string; options?: string[] }, i: number) => (
                      <div key={i} className="bg-white rounded-lg p-3 border border-prism-border">
                        <p className="font-semibold text-prism-text text-sm">{d.question}</p>
                        {Array.isArray(d.options) && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {d.options.map((opt: string, j: number) => (
                              <span key={j} className="badge bg-prism-surface-alt text-prism-text-secondary border border-prism-border text-[11px]">
                                {opt}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {cp.resources && typeof cp.resources === "object" && !Array.isArray(cp.resources) && (
                  <div>
                    <p className="text-xs font-bold text-prism-text-muted uppercase tracking-wider mb-2">Resources</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(cp.resources as Record<string, number>).map(([k, v]) => (
                        <div key={k} className="bg-white rounded-lg p-2 border border-prism-border text-xs">
                          <span className="text-prism-text-secondary">{k.replace(/_/g, " ")}: </span>
                          <span className="font-bold text-prism-text">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>

        {/* Response form */}
        <form onSubmit={handleSubmit} className="card p-5 space-y-4">
          <label className="text-sm font-bold text-prism-text">Your Response</label>
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Type your answer here..."
            rows={5}
            className="input-field resize-none"
          />
          {error && (
            <div className="flex items-center gap-2 text-prism-red text-sm font-medium">
              <span>⚠️</span> {error}
            </div>
          )}
          <button
            type="submit"
            disabled={submitting || !response.trim()}
            className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed text-base"
          >
            {submitting ? "Submitting..." : "Submit Response 🚀"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
