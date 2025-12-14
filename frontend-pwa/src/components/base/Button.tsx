/**
 * Button Component - REFATORADO (Design System Compliant)
 * 
 * ✅ Usa classes Tailwind + inline styles para compatibilidade
 * ✅ Totalmente acessível (WCAG 2.1 AA)
 * ✅ Variants consistentes com Design System
 * ✅ Loading states com aria-busy
 * ✅ Focus rings com contraste adequado
 * 
 * @author Product Designer Sênior
 * @date 14/12/2024
 */

import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import { colors, transitions } from '../../theme/colors';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Variante visual do botão */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  
  /** Tamanho do botão */
  size?: 'sm' | 'md' | 'lg';
  
  /** Estado de carregamento (desabilita e mostra spinner) */
  isLoading?: boolean;
  
  /** Ícone à esquerda do texto */
  leftIcon?: React.ReactNode;
  
  /** Ícone à direita do texto */
  rightIcon?: React.ReactNode;
  
  /** Se true, botão ocupa 100% da largura */
  fullWidth?: boolean;
  
  /** Label acessível (obrigatório se children for apenas ícone) */
  'aria-label'?: string;
}

/**
 * Button Component - Design System Compliant
 * 
 * @example
 * <Button variant="primary" leftIcon={<Save />}>
 *   Salvar Prontuário
 * </Button>
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      children,
      disabled,
      style,
      ...props
    },
    ref
  ) => {
    // Validação de acessibilidade
    const hasOnlyIcon = !children && (leftIcon || rightIcon);
    if (hasOnlyIcon && !props['aria-label'] && process.env.NODE_ENV === 'development') {
      console.warn('⚠️ Button com apenas ícone precisa de aria-label para acessibilidade!');
    }

    // Estilos baseados em variant usando inline styles para compatibilidade
    const variantStyles: React.CSSProperties = 
      variant === 'primary' ? {
        backgroundColor: colors.primary.medium,
        color: '#FFFFFF',
      } :
      variant === 'secondary' ? {
        backgroundColor: colors.neutral?.lighter || '#e5e7eb',
        color: colors.text.primary,
        border: `2px solid ${colors.neutral?.base || '#9ca3af'}`,
      } :
      variant === 'danger' ? {
        backgroundColor: colors.alert.critical,
        color: '#FFFFFF',
      } :
      variant === 'success' ? {
        backgroundColor: '#10b981',
        color: '#FFFFFF',
      } :
      { // ghost
        backgroundColor: 'transparent',
        color: colors.text.primary,
      };

    const sizeStyles: React.CSSProperties =
      size === 'sm' ? { padding: '6px 12px', fontSize: '0.875rem' } :
      size === 'lg' ? { padding: '12px 24px', fontSize: '1.125rem' } :
      { padding: '8px 16px', fontSize: '1rem' };

    return (
      <button
        ref={ref}
        type={props.type || "button"}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        aria-disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center gap-2',
          'font-medium rounded-lg',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-60',
          fullWidth && 'w-full',
          className
        )}
        style={{
          ...variantStyles,
          ...sizeStyles,
          cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: `all ${transitions.base}`,
          ...style,
        }}
        onClick={!disabled && !isLoading ? props.onClick : undefined}
        {...props}
      >
        {/* Loading Spinner Acessível */}
        {isLoading && (
          <>
            <Loader2 
              className={cn(
                'animate-spin',
                size === 'sm' && 'w-3 h-3',
                size === 'md' && 'w-4 h-4',
                size === 'lg' && 'w-5 h-5'
              )}
              aria-hidden="true"
            />
            <span className="sr-only">Carregando...</span>
          </>
        )}

        {/* Ícone esquerdo */}
        {!isLoading && leftIcon && (
          <span aria-hidden="true">{leftIcon}</span>
        )}

        {/* Texto/Children */}
        {children && <span>{children}</span>}

        {/* Ícone direito */}
        {!isLoading && rightIcon && (
          <span aria-hidden="true">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
