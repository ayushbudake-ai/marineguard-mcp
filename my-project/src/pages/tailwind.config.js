/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A1418",       // page background — dark like a sonar display off-state
        surface: "#101C22",   // panel background
        surface2: "#16232B",  // raised panel / hover
        line: "#20343C",      // hairline borders, grid lines
        fg: "#DCE8E8",        // primary text
        muted: "#7C96A0",     // secondary text
        teal: {
          DEFAULT: "#3FB8AF", // accepted detections, primary actions
          dim: "#28524E",
        },
        amber: {
          DEFAULT: "#E8A33D", // flagged / medium confidence
          dim: "#4A3A20",
        },
        coral: {
          DEFAULT: "#E2574C", // rejected / critical
          dim: "#492723",
        },
      },
      fontFamily: {
        sans: ['"Space Grotesk"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};