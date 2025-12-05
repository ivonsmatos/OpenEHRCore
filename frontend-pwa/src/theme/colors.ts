/**
 * Design System - Paleta de Cores Institucional
 *
 * Estas cores foram cuidadosamente selecionadas para:
 * - Transmitir confiança e profissionalismo
 * - Garantir acessibilidade (WCAG AA+)
 * - Criar ambiente limpo e minimalista
 * - Respeitar conformidade de saúde digital
 */

export const colors = {
  // Primary - Para header, menu, ações principais
  primary: {
    dark: "#1E40AF",     // Menu/Header - Azul escuro mais suave (Blue-800)
    medium: "#3B82F6",   // Botões/Ações principais - Azul amigável (Blue-500)
    light: "#93C5FD",    // Destaques suaves (Blue-300)
  },

  // Secondary/Accent - Destaques e elementos secundários
  accent: {
    primary: "#60A5FA",  // Destaque suave (Blue-400)
  },

  // Alert/Status - Para erros e alertas críticos
  alert: {
    critical: "#EF4444", // Erros/Alertas médicos - Vermelho suave (Red-500)
    warning: "#F59E0B",  // Avisos (Amber-500)
    success: "#10B981",  // Sucesso (Emerald-500)
    info: "#3B82F6",     // Info (Blue-500)
  },

  // Background - Fundo geral (clean design)
  background: {
    surface: "#F2F2F2",  // Fundo geral - Cinza bem claro
    default: "#FFFFFF",  // Branco puro para cards
    muted: "#F9FAFB",    // Muito sutilmente cinza
  },

  // Neutral - Textos e elementos neutros
  neutral: {
    light: "#EBEFF2",    // Fundo muito claro (praticamente branco)
    lighter: "#C5D0D9",  // Cinza bem claro para bordas/dividers
    base: "#A3B2BF",     // Cinza médio para textos secundários
    dark: "#595959",     // Texto escuro padrão
    darkest: "#0D0D0D",  // Texto muito escuro (quase preto)
  },

  // Semantic aliases
  text: {
    primary: "#0D0D0D",    // neutral.darkest
    secondary: "#595959",  // neutral.dark
    tertiary: "#A3B2BF",   // neutral.base
    muted: "#C5D0D9",      // neutral.lighter
  },

  border: {
    light: "#EBEFF2",    // Bordas muito sutis
    default: "#C5D0D9",  // Bordas padrão
    strong: "#A3B2BF",   // Bordas mais visíveis
  },

  // Divider
  divider: "#EBEFF2",

  // Backdrop (modal, overlay)
  backdrop: "rgba(13, 13, 13, 0.4)", // darkest com 40% opacidade
} as const;

/**
 * Typografia - Escalas e tamanhos
 */
export const typography = {
  // Títulos
  h1: {
    fontSize: "1.875rem", // 30px
    lineHeight: "2.25rem",
    fontWeight: 700,
  },
  h2: {
    fontSize: "1.5rem", // 24px
    lineHeight: "2rem",
    fontWeight: 700,
  },
  h3: {
    fontSize: "1.25rem", // 20px
    lineHeight: "1.75rem",
    fontWeight: 600,
  },

  // Body
  body: {
    lg: {
      fontSize: "1.125rem",
      lineHeight: "1.75rem",
      fontWeight: 400,
    },
    base: {
      fontSize: "1rem",
      lineHeight: "1.5rem",
      fontWeight: 400,
    },
    sm: {
      fontSize: "0.875rem",
      lineHeight: "1.25rem",
      fontWeight: 400,
    },
  },

  // Labels e hints
  label: {
    fontSize: "0.875rem",
    lineHeight: "1.25rem",
    fontWeight: 500,
  },
  hint: {
    fontSize: "0.75rem",
    lineHeight: "1rem",
    fontWeight: 400,
  },
} as const;

/**
 * Espaçamento - Escala 8px (whitespace generoso)
 */
export const spacing = {
  xs: "0.5rem",    // 8px
  sm: "1rem",      // 16px
  md: "1.5rem",    // 24px
  lg: "2rem",      // 32px
  xl: "3rem",      // 48px
  "2xl": "4rem",   // 64px
} as const;

/**
 * Border Radius - Bordas suaves
 */
export const borderRadius = {
  none: "0",
  soft: "0.375rem",  // 6px
  base: "0.5rem",    // 8px
  md: "0.75rem",     // 12px
  lg: "1rem",        // 16px
  full: "9999px",
} as const;

/**
 * Sombras - Profundidade visual
 */
export const shadows = {
  none: "none",
  soft: "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)",
  base: "0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)",
  md: "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)",
  lg: "0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)",
  xl: "0 25px 50px rgba(0, 0, 0, 0.15), 0 25px 50px rgba(0, 0, 0, 0.1)",
} as const;

/**
 * Transitions - Animações suaves
 */
export const transitions = {
  fast: "150ms ease-in-out",
  base: "250ms ease-in-out",
  slow: "350ms ease-in-out",
} as const;

// Export como um objeto único para fácil acesso
export const theme = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
} as const;
