import React from "react";
import { colors, spacing, borderRadius, shadows } from "../../theme/colors";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  elevation?: "none" | "soft" | "base" | "md";
  onClick?: () => void;
  style?: React.CSSProperties;
  onMouseEnter?: (e: React.MouseEvent<HTMLDivElement>) => void;
  onMouseLeave?: (e: React.MouseEvent<HTMLDivElement>) => void;
  title?: string;
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
  style,
  onMouseEnter,
  onMouseLeave,
  title,
}) => {
  const paddingMap = {
    none: "0px",
    sm: spacing.sm,    // 16px
    md: spacing.md,    // 24px
    lg: spacing.lg,    // 32px
  };

  return (
    <div
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className={className}
      style={{
        backgroundColor: colors.background.default,
        borderRadius: borderRadius.lg,
        padding: paddingMap[padding],
        boxShadow: shadows[elevation],
        border: `1px solid ${colors.border.light}`,
        transition: `all 250ms ease-in-out`,
        cursor: onClick ? "pointer" : "default",
        ...style,
      }}
    >
      {title && (
        <h3 style={{
          margin: `0 0 ${spacing.md} 0`,
          fontSize: '1.1rem',
          fontWeight: 600,
          color: colors.text.primary
        }}>
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};

export default Card;
