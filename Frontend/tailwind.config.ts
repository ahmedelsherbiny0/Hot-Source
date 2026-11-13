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
        nasa: {
          blue: "#0B3D91",
          red: "#FC3D21",
        },
        slate: {
          950: "#070b14",
          900: "#0b1220",
          850: "#0f172a",
          800: "#1e293b",
        },
        cyan: {
          400: "#22d3ee",
          500: "#06b6d4",
        },
        amber: {
          400: "#fbbf24",
          500: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
