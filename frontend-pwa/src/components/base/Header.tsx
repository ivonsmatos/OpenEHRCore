import React from "react";
import { colors, typography, spacing } from "../../theme/colors";

interface HeaderProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  className?: string;
}

/**
 * Componente Header - Design System
 *
 * Cabeçalho fixo da aplicação
 * - Fundo azul escuro (#0339A6)
 * - Texto branco para máximo contraste
 * - Whitespace generoso
 */
export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  children,
  className = "",
}) => {
  return (
    <header
      className={className}
      style={{
        backgroundColor: colors.primary.dark,
        color: "#FFFFFF",
        padding: `${spacing.lg} ${spacing.xl}`,
        boxShadow: "0 2px 8px rgba(3, 57, 166, 0.15)",
        borderBottom: `1px solid ${colors.primary.medium}`,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        <div>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              margin: "0 0 4px 0",
              lineHeight: "2rem",
            }}
          >
            {title}
          </h1>
          {subtitle && (
            <p
              style={{
                fontSize: "0.875rem",
                margin: 0,
                opacity: 0.9,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
        {children && (
          <div
            style={{
              display: "flex",
              gap: spacing.md,
              alignItems: "center",
            }}
          >
            {children}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
