import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        prism: {
          violet: "#7C4DFF",
          magenta: "#E040FB",
          cyan: "#00ACC1",
          amber: "#F59E0B",
          green: "#10B981",
          red: "#EF4444",
          bg: "#F8F6FF",
          surface: "#FFFFFF",
          "surface-alt": "#F0ECFB",
          border: "#E8E0F5",
          text: "#1E1433",
          "text-secondary": "#6B5B8A",
          "text-muted": "#9B8FB8",
        },
      },
      backgroundImage: {
        "prism-gradient":
          "linear-gradient(135deg, #7C4DFF 0%, #E040FB 50%, #00ACC1 100%)",
        "prism-gradient-warm":
          "linear-gradient(135deg, #E040FB 0%, #F59E0B 100%)",
        "prism-gradient-cool":
          "linear-gradient(135deg, #7C4DFF 0%, #00ACC1 100%)",
        "prism-gradient-soft":
          "linear-gradient(135deg, #F0ECFB 0%, #FDF2F8 50%, #ECFDF5 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s linear infinite",
        float: "float 6s ease-in-out infinite",
        "bounce-in": "bounceIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)",
        "slide-up": "slideUp 0.4s ease-out",
        "pop": "pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
        "confetti": "confetti 0.8s ease-out",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        bounceIn: {
          "0%": { transform: "scale(0.3)", opacity: "0" },
          "50%": { transform: "scale(1.05)" },
          "70%": { transform: "scale(0.9)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        pop: {
          "0%": { transform: "scale(0.8)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        confetti: {
          "0%": { transform: "scale(0) rotate(0deg)", opacity: "1" },
          "100%": { transform: "scale(1.5) rotate(45deg)", opacity: "0" },
        },
      },
      boxShadow: {
        "card": "0 2px 12px rgba(124, 77, 255, 0.06), 0 1px 3px rgba(0,0,0,0.04)",
        "card-hover": "0 8px 30px rgba(124, 77, 255, 0.12), 0 2px 8px rgba(0,0,0,0.06)",
        "glow": "0 0 20px rgba(124, 77, 255, 0.15)",
      },
    },
  },
  plugins: [],
};
export default config;
