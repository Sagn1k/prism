"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const FEATURES = [
  {
    icon: "🗺️",
    title: "Explore Worlds",
    desc: "Four unique worlds with missions that reveal who you really are.",
    color: "bg-violet-50 border-violet-200",
    iconBg: "bg-violet-100",
  },
  {
    icon: "⚡",
    title: "Earn XP & Level Up",
    desc: "Complete quests, earn experience points, and unlock new levels.",
    color: "bg-amber-50 border-amber-200",
    iconBg: "bg-amber-100",
  },
  {
    icon: "🤖",
    title: "AI Mentor Ray",
    desc: "Chat with your personal AI guide who understands your spectrum.",
    color: "bg-cyan-50 border-cyan-200",
    iconBg: "bg-cyan-100",
  },
  {
    icon: "🃏",
    title: "Your Prism Card",
    desc: "Get a shareable card showing your archetype and unique spectrum.",
    color: "bg-pink-50 border-pink-200",
    iconBg: "bg-pink-100",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" },
  }),
};

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Soft ambient gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-to-b from-violet-100/60 via-pink-50/40 to-transparent rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-60 -right-20 w-[400px] h-[400px] bg-cyan-100/30 rounded-full blur-[80px] pointer-events-none" />

      {/* Hero */}
      <section className="relative max-w-4xl mx-auto px-4 pt-20 pb-16 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="w-20 h-20 rounded-3xl bg-prism-gradient flex items-center justify-center text-4xl mx-auto mb-6 shadow-glow"
          >
            🌈
          </motion.div>
          <h1 className="text-5xl sm:text-7xl font-extrabold leading-tight text-prism-text">
            Discover Your{" "}
            <span className="text-gradient">Prism</span>
          </h1>
          <p className="mt-5 text-lg sm:text-xl text-prism-text-secondary max-w-2xl mx-auto leading-relaxed">
            You are not one colour &mdash; you are a spectrum. Complete quests,
            level up, and share your unique identity card.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link href="/worlds" className="btn-primary text-lg px-10 py-4">
            Start Your Journey 🚀
          </Link>
          <Link href="/chat" className="btn-secondary text-lg px-10 py-4">
            Talk to Ray 🤖
          </Link>
        </motion.div>

        {/* Stats ribbon */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="mt-12 inline-flex items-center gap-6 px-8 py-4 card rounded-full"
        >
          <div className="text-center">
            <p className="text-2xl font-extrabold text-prism-violet">4</p>
            <p className="text-xs text-prism-text-muted font-semibold">Worlds</p>
          </div>
          <div className="w-px h-8 bg-prism-border" />
          <div className="text-center">
            <p className="text-2xl font-extrabold text-prism-magenta">15+</p>
            <p className="text-xs text-prism-text-muted font-semibold">Missions</p>
          </div>
          <div className="w-px h-8 bg-prism-border" />
          <div className="text-center">
            <p className="text-2xl font-extrabold text-prism-cyan">5</p>
            <p className="text-xs text-prism-text-muted font-semibold">Levels</p>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="relative max-w-5xl mx-auto px-4 pb-28">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-40px" }}
              variants={fadeUp}
              className={`p-5 rounded-2xl border-2 ${f.color} hover:scale-[1.03] transition-transform duration-200`}
            >
              <div
                className={`w-12 h-12 rounded-xl ${f.iconBg}
                            flex items-center justify-center text-2xl mb-3`}
              >
                {f.icon}
              </div>
              <h3 className="font-bold text-prism-text mb-1">{f.title}</h3>
              <p className="text-sm text-prism-text-secondary leading-relaxed">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
