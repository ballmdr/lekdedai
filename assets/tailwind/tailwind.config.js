const path = require("path");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [path.join(__dirname, "../../app/**/*.html").replace(/\\/g, "/")],
  theme: {
    extend: {
      colors: {
        primary: "#f59e0b",
        secondary: "#ea580c",
        accent: "#dc2626",
      },
    },
  },
  plugins: [],
};
