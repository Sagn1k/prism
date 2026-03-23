"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { dashboardApi, type DashboardStats } from "@/lib/api";

const STAT_CARDS = [
  { key: "total_students" as const, label: "Total Students", format: (v: number) => v.toLocaleString() },
  { key: "active_students" as const, label: "Active Students", format: (v: number) => v.toLocaleString() },
  { key: "avg_engagement" as const, label: "Avg Engagement", format: (v: number) => `${Math.round(v * 100)}%` },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi
      .stats()
      .then((r) => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="grid sm:grid-cols-3 gap-6 mb-8">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card-glass p-6 h-28 animate-pulse" />
          ))}
        </div>
        <div className="card-glass p-8 h-64 animate-pulse" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center">
        <div className="card-glass p-12">
          <h2 className="text-xl font-bold mb-2">Dashboard Unavailable</h2>
          <p className="text-prism-muted">
            Could not load school statistics. Please ensure you have admin access.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold mb-2">
          School <span className="text-gradient">Dashboard</span>
        </h1>
        <p className="text-prism-muted mb-8">Overview of student engagement and identity insights.</p>
      </motion.div>

      {/* Stat cards */}
      <div className="grid sm:grid-cols-3 gap-6 mb-8">
        {STAT_CARDS.map(({ key, label, format }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card-glass p-6"
          >
            <p className="text-sm text-prism-muted uppercase tracking-wider mb-1">{label}</p>
            <p className="text-3xl font-bold">{format(stats[key])}</p>
          </motion.div>
        ))}
      </div>

      {/* Archetype distribution */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-glass p-8 mb-8"
      >
        <h2 className="font-semibold text-lg mb-4">Archetype Distribution</h2>
        <div className="space-y-3">
          {Object.entries(stats.archetype_distribution)
            .sort(([, a], [, b]) => b - a)
            .map(([archetype, count]) => {
              const pct = stats.total_students > 0 ? Math.round((count / stats.total_students) * 100) : 0;
              return (
                <div key={archetype}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{archetype}</span>
                    <span className="text-prism-muted">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 bg-prism-dark-surface rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8 }}
                      className="h-full rounded-full bg-prism-gradient"
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </motion.div>

      {/* Stream readiness */}
      {stats.stream_readiness && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card-glass p-8"
        >
          <h2 className="font-semibold text-lg mb-4">Stream Readiness</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {Object.entries(stats.stream_readiness).map(([stream, count]) => (
              <div key={stream} className="bg-prism-dark-surface rounded-xl p-4 text-center">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-prism-muted capitalize mt-1">{stream}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
