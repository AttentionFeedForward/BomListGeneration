/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 深空蓝主调
        'space-dark': '#0A0E27',
        'space-blue': '#1E3A8A',
        'space-light': '#3B82F6',
        // 霓虹强调色
        'neon-cyan': '#00F5FF',
        'neon-blue': '#0080FF',
        'neon-purple': '#8B5CF6',
        'neon-green': '#00FF88',
        'neon-orange': '#FF8C00',
        'neon-red': '#FF4444',
        // 玻璃态效果
        'glass-white': 'rgba(255, 255, 255, 0.1)',
        'glass-blue': 'rgba(59, 130, 246, 0.1)',
      },
      backgroundImage: {
        'space-gradient': 'radial-gradient(ellipse at center, #1E3A8A 0%, #0A0E27 100%)',
        'neon-gradient': 'linear-gradient(45deg, #00F5FF, #0080FF)',
      },
      boxShadow: {
        'neon-cyan': '0 0 20px rgba(0, 245, 255, 0.5)',
        'neon-blue': '0 0 20px rgba(0, 128, 255, 0.5)',
        'glass': '0 8px 32px rgba(31, 38, 135, 0.37)',
      },
      backdropBlur: {
        'glass': '20px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 245, 255, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 245, 255, 0.8)' },
        },
      },
    },
  },
  plugins: [],
}