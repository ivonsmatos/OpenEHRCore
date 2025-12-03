/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta Institucional OpenEHRCore
        primary: {
          dark: "#0339A6",     // Menu/Header
          medium: "#0468BF",   // Botões/Ações principais
          light: "#79ACD9",    // Destaques suaves
        },
        secondary: {
          accent: "#79ACD9",   // Alias para light
        },
        alert: {
          critical: "#D91A1A", // Erros/Alertas médicos
        },
        background: {
          surface: "#F2F2F2",  // Fundo geral - Clean
          default: "#FFFFFF",  // Branco puro
        },
        neutral: {
          dark: "#595959",     // Texto escuro
          darkest: "#0D0D0D",  // Texto muito escuro
        },
      },
      spacing: {
        // Whitespace generoso (escala 8px)
        xs: "0.5rem",    // 8px
        sm: "1rem",      // 16px
        md: "1.5rem",    // 24px
        lg: "2rem",      // 32px
        xl: "3rem",      // 48px
        "2xl": "4rem",   // 64px
      },
      borderRadius: {
        // Bordas suaves
        soft: "0.375rem",  // 6px
        base: "0.5rem",    // 8px
        md: "0.75rem",     // 12px
        lg: "1rem",        // 16px
        full: "9999px",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      fontSize: {
        // Tipografia moderna
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
      },
      boxShadow: {
        // Sombras suaves para profundidade
        soft: "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)",
        base: "0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)",
        md: "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)",
        lg: "0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
}
