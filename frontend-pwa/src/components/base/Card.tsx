import React from "react";
import { colors, spacing, borderRadius, shadows } from "../../theme/colors";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
  elevation?: "none" | "soft" | "base" | "md";
  onClick?: () => void;
}

/**
 * Componente Card - Design System
 *
 * Elemento base para agrupar conteúdo. Segue o padrão:
 * - Fundo branco puro
 * - Bordas suaves
 * - Sombra sutil para profundidade
 * - Whitespace generoso
 */
export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  padding = "md",
  elevation = "base",
  onClick,
}) => {
  const paddingMap = {
    sm: spacing.sm,    // 16px
    md: spacing.md,    // 24px
    lg: spacing.lg,    // 32px
  };

  return (
    <div
      onClick={onClick}
      className={className}
      style={{
        backgroundColor: colors.background.default,
        borderRadius: borderRadius.lg,
        padding: paddingMap[padding],
        boxShadow: shadows[elevation],
        border: `1px solid ${colors.border.light}`,
        transition: `all 250ms ease-in-out`,
        cursor: onClick ? "pointer" : "default",
      }}
    >
      {children}
    </div>
  );
};

export default Card;
