import { Loader2 } from 'lucide-react'

/**
 * 버튼 컴포넌트
 * @param {string} variant - 'primary' | 'secondary' | 'outline' | 'ghost'
 * @param {string} size - 'sm' | 'md' | 'lg'
 * @param {boolean} loading - 로딩 상태
 * @param {boolean} disabled - 비활성화 상태
 * @param {ReactNode} icon - 왼쪽 아이콘
 */
function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-bg'

  const variantStyles = {
    primary: 'bg-primary hover:bg-primary-hover text-white focus:ring-primary disabled:bg-primary/50',
    secondary: 'bg-dark-card hover:bg-dark-hover text-white border border-dark-border focus:ring-gray-500',
    outline: 'border border-dark-border hover:bg-dark-hover text-gray-300 focus:ring-gray-500',
    ghost: 'hover:bg-dark-hover text-gray-400 hover:text-white focus:ring-gray-500',
  }

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-6 py-3 gap-2',
  }

  const isDisabled = disabled || loading

  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${isDisabled ? 'cursor-not-allowed opacity-50' : ''}
        ${className}
      `}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : Icon ? (
        <Icon className="w-4 h-4" />
      ) : null}
      {children}
    </button>
  )
}

export default Button
