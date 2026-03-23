"use client";

import { useEffect, useState } from "react";
import { cardApi, type PrismCardData } from "@/lib/api";
import PrismCard from "@/components/PrismCard";
import { motion } from "framer-motion";
import Link from "next/link";

export default function CardPageClient({ token }: { token: string }) {
  const [card, setCard] = useState<PrismCardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    cardApi
      .byToken(token)
      .then((r) => {
        // Public endpoint returns {card_data, image_url, og_title, og_description}
        // Normalize it to PrismCardData shape for the PrismCard component
        const data = r.data as Record<string, unknown>;
        setCard({
          id: token,
          card_data: (data.card_data || data) as Record<string, unknown>,
          image_url: (data.image_url as string) || null,
          share_token: token,
          is_public: true,
          generated_at: new Date().toISOString(),
        });
      })
      .catch(() => setError(true));
  }, [token]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="card p-12 text-center">
          <div className="text-5xl mb-3">🔍</div>
          <h2 className="text-xl font-bold text-prism-text mb-2">Card Not Found</h2>
          <p className="text-prism-text-secondary">
            This Prism Card doesn&apos;t exist or has been removed.
          </p>
        </div>
      </div>
    );
  }

  if (!card) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-80 h-96 card animate-pulse bg-prism-surface-alt" />
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12">
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-prism-text-muted text-xs font-bold mb-6 uppercase tracking-[0.2em]"
      >
        Shared Prism Card
      </motion.p>
      <PrismCard card={card} />
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-8"
      >
        <Link href="/worlds" className="btn-primary px-8">
          Discover Your Prism 🌈
        </Link>
      </motion.div>
    </div>
  );
}
