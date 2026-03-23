"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function LoginModal({ open, onClose }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const login = useAuth((s) => s.login);
  const register = useAuth((s) => s.register);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      if (mode === "register") {
        await register({ email, password, name });
      } else {
        await login({ email, password });
      }
      onClose();
      setEmail("");
      setPassword("");
      setName("");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined;
      setError(msg || "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError("");
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm px-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 30 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="card p-8 w-full max-w-md shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-center mb-6">
              <div className="text-4xl mb-2">
                {mode === "login" ? "👋" : "🚀"}
              </div>
              <h2 className="text-2xl font-extrabold text-prism-text">
                {mode === "login" ? "Welcome back!" : "Join the quest!"}
              </h2>
              <p className="text-sm text-prism-text-secondary mt-1">
                {mode === "login"
                  ? "Sign in to continue your adventure"
                  : "Create your account and start exploring"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div>
                  <label className="block text-xs font-bold text-prism-text-secondary mb-1.5 uppercase tracking-wider">
                    Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    required
                    className="input-field"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-prism-text-secondary mb-1.5 uppercase tracking-wider">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-prism-text-secondary mb-1.5 uppercase tracking-wider">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  minLength={6}
                  className="input-field"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-prism-red text-sm font-medium bg-red-50 px-4 py-2.5 rounded-xl border border-red-200">
                  <span>⚠️</span> {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting
                  ? "Please wait..."
                  : mode === "login"
                    ? "Sign In"
                    : "Create Account 🎮"}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-prism-text-secondary">
              {mode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}{" "}
              <button
                onClick={switchMode}
                className="text-prism-violet hover:text-prism-magenta transition-colors font-bold"
              >
                {mode === "login" ? "Sign up" : "Sign in"}
              </button>
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
