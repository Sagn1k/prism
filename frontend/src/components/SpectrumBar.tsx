"use client";

import { motion } from "framer-motion";

const COLORS = [
  { keys: ["Violet", "violet"], hex: "#7C4DFF", label: "Analytical" },
  { keys: ["Magenta", "magenta"], hex: "#E040FB", label: "Creative" },
  { keys: ["Cyan", "cyan"], hex: "#00ACC1", label: "Explorer" },
  { keys: ["Amber", "amber"], hex: "#F59E0B", label: "Builder" },
  { keys: ["Green", "green"], hex: "#10B981", label: "People" },
];

interface Props {
  spectrum: Record<string, number>;
  showLabels?: boolean;
  height?: string;
}

export default function SpectrumBar({
  spectrum,
  showLabels = false,
  height = "h-4",
}: Props) {
  const getValue = (keys: string[]) => {
    for (const k of keys) {
      if (spectrum[k] != null) return spectrum[k];
    }
    return 0;
  };

  const total = COLORS.reduce((s, c) => s + getValue(c.keys), 0) || 1;

  return (
    <div>
      <div className={`flex ${height} rounded-full overflow-hidden bg-prism-surface-alt border border-prism-border/50`}>
        {COLORS.map(({ keys, hex }, i) => {
          const pct = (getValue(keys) / total) * 100;
          return (
            <motion.div
              key={keys[0]}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.8, delay: i * 0.1, ease: "easeOut" }}
              style={{ backgroundColor: hex }}
              className="min-w-[2px]"
            />
          );
        })}
      </div>
      {showLabels && (
        <div className="flex justify-between mt-2.5">
          {COLORS.map(({ keys, hex, label }) => {
            const pct = Math.round((getValue(keys) / total) * 100);
            return (
              <div key={keys[0]} className="flex flex-col items-center text-xs gap-1">
                <div
                  className="w-3 h-3 rounded-full border-2 border-white shadow-sm"
                  style={{ backgroundColor: hex }}
                />
                <span className="text-prism-text-muted font-medium">{label}</span>
                <span className="font-bold" style={{ color: hex }}>
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
