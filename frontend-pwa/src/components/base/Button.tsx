import React from "react";
import { colors, borderRadius, transitions } from "../../theme/colors";

interface ButtonProps {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  isLoading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
  type?: "button" | "submit" | "reset";
}

/**
 * Componente Button - Design System
 *
 * Variantes:
 * - primary: Ações principais (azul medium)
 * - secondary: Ações secundárias (cinza)
 * - danger: Ações destrutivas (vermelho)
 * - ghost: Botões sem fundo (texto + ícone)
 */
export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  disabled = false,
  isLoading = false,
  children,
  onClick,
  className = "",
  style = {},
  type = "button",
}) => {
  const baseStyles = `
    font-sans font-medium rounded-${borderRadius.md}
    transition-all ${transitions.base}
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    inline-flex items-center justify-center gap-2
  `;

  const sizeStyles = {
    sm: `px-3 py-1.5 text-sm`,
    md: `px-4 py-2 text-base`,
    lg: `px-6 py-3 text-lg`,
  };

  const variantStyles = {
    primary: `
      bg-[${colors.primary.medium}] text-white
      hover:bg-[${colors.primary.dark}]
      focus:ring-[${colors.primary.light}]
    `,
    secondary: `
      bg-[${colors.neutral.lighter}] text-[${colors.text.primary}]
      hover:bg-[${colors.neutral.base}]
      focus:ring-[${colors.neutral.base}]
    `,
    danger: `
      bg-[${colors.alert.critical}] text-white
      hover:opacity-90
      focus:ring-[${colors.alert.critical}]
    `,
    ghost: `
      bg-transparent text-[${colors.text.primary}]
      hover:bg-[${colors.background.muted}]
      focus:ring-[${colors.background.surface}]
    `,
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      className={`
        ${baseStyles}
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${className}
      `}
      style={{
        backgroundColor:
          variant === "primary"
            ? colors.primary.medium
            : variant === "secondary"
              ? colors.neutral.lighter
              : variant === "danger"
                ? colors.alert.critical
                : "transparent",
        color:
          variant === "primary" || variant === "danger"
            ? "#FFFFFF"
            : colors.text.primary,
        padding: size === "sm" ? "6px 12px" : size === "lg" ? "12px 24px" : "8px 16px",
        borderRadius: "8px",
        border: "none",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: `all ${transitions.base}`,
        ...style,
      }}
    >
      {isLoading ? (
        <>
          <span className="animate-spin">⟳</span>
          {children}
        </>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;
