/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",   // 扫描所有模板
    "./app.py",                // 如有内联 class，也可加上
    "./services.py",
    "./main.py"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
