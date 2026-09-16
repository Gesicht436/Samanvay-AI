import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f4f6f8",
        surface: "#ffffff",
        card: "#ffffff",
        cardBorder: "#d5d9d9",
        textPrimary: "#0f1111",
        textSecondary: "#565959",
        amazon: {
          dark: "#131921",
          navy: "#232f3e",
          blue: "#007185",
          blueHover: "#004854",
          amber: "#ff9900",
          yellow: "#ffd814",
          yellowHover: "#f7ca00",
          orange: "#ffa41c",
          orangeHover: "#fa8900",
          border: "#d5d9d9",
          borderDark: "#888c8c",
          bgLight: "#f4f6f8",
        },
        brand: {
          50: "#f0f4f8",
          100: "#d9e2ec",
          500: "#007185",
          600: "#005c6d",
          700: "#004854",
        },
        tier1: {
          bg: "#e6f4ea",
          border: "#34a853",
          text: "#137333",
          badge: "#067d62",
        },
        tier2: {
          bg: "#fef7e0",
          border: "#f9ab00",
          text: "#b06000",
          badge: "#b12704",
        },
        tier3: {
          bg: "#fce8e6",
          border: "#ea4335",
          text: "#c5221f",
          badge: "#c40000",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
        mono: ["Consolas", '"Liberation Mono"', "Menlo", "Courier", "monospace"],
      },
      boxShadow: {
        amazon: "0 1px 2px 0 rgba(0,0,0,0.05)",
        amazonCard: "0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.08)",
        amazonHover: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
