/**
 * Utility para concatenar classNames condicionalmente
 * Similar ao clsx/classnames mas sem dependências externas
 * 
 * @example
 * cn('base-class', isActive && 'active-class', 'another-class')
 * // => 'base-class active-class another-class'
 */
export function cn(...inputs: (string | boolean | undefined | null)[]): string {
  return inputs
    .filter(Boolean)
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
}
